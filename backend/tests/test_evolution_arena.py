#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Evolution Arena 端到端测试

测试目标：
1. 经验闭环：执行 -> 沉淀 -> 复用
2. 技能发现闭环：能力不足 -> 搜索 -> 调用 -> 记录
3. 权限隔离验证：用户 A 的 Agent 不能访问用户 B 的数据
"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agent_builder.core.database import async_session_factory, init_db
from agent_builder.db.models import (
    Agent, Experiment, Experience, MCPServerConfig,
    AgentExperienceAbsorption
)
from agent_builder.services.experience_service import ExperienceService
from agent_builder.services.experiment_engine import ExperimentEngine
from agent_builder.services.skill_service import SkillService
from agent_builder.services.mcp_client_manager import MCPClientManager
from agent_builder.schemas.execution import ExecutionStatus


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Setup database for tests."""
    await init_db()
    yield


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user_a(db_session) -> Tuple[str, str]:
    """Create test user A and agent."""
    user_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())

    agent = Agent(
        id=agent_id,
        user_id=user_id,
        name="Test Agent A",
        model="deepseek-chat",
        system_prompt="You are a helpful assistant.",
        max_steps=50,
    )
    db_session.add(agent)
    await db_session.flush()

    return user_id, agent_id


@pytest_asyncio.fixture
async def test_user_b(db_session) -> Tuple[str, str]:
    """Create test user B and agent."""
    user_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())

    agent = Agent(
        id=agent_id,
        user_id=user_id,
        name="Test Agent B",
        model="deepseek-chat",
        system_prompt="You are a helpful assistant.",
        max_steps=50,
    )
    db_session.add(agent)
    await db_session.flush()

    return user_id, agent_id


class TestExperienceLifecycle:
    """测试经验完整生命周期：创建 -> 沉淀 -> 复用"""

    @pytest.mark.asyncio
    async def test_experience_precipitation(self, db_session, test_user_a):
        """测试实验执行后经验被正确沉淀"""
        user_id, agent_id = test_user_a

        # 1. 创建实验
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="First Document Analysis",
            experiment_type="document",
            input_data={"task": "搜索并分析关于 AI 的文档"},
            status="pending",
        )
        db_session.add(experiment)
        await db_session.flush()

        # 2. 运行实验（使用 ExperimentEngine）
        experience_service = ExperienceService(db_session)
        mcp_manager = MCPClientManager()
        skill_discovery = SkillService(db_session, mcp_manager)
        engine = ExperimentEngine(db_session, experience_service, skill_discovery)

        result = await engine.run_experiment(experiment.id, user_id)

        # 3. 验证实验执行成功
        assert result.success is True
        assert result.status == ExecutionStatus.SUCCESS
        assert result.experience_id is not None

        # 4. 验证经验被沉淀
        await db_session.refresh(experiment)
        assert experiment.output_data.get("experience_id") == result.experience_id

        # 5. 验证经验详情
        experience = await experience_service.get_experience(result.experience_id, user_id)
        assert experience is not None
        assert experience.user_id == user_id
        assert experience.source_agent_id == agent_id
        assert experience.source_experiment_id == experiment.id
        assert experience.type == "success"
        assert experience.status == "draft"
        assert experience.situation == "搜索并分析关于 AI 的文档"
        print(f"经验已沉淀: {experience.id}, 类型: {experience.type}, 状态: {experience.status}")

    @pytest.mark.asyncio
    async def test_experience_reuse(self, db_session, test_user_a):
        """测试相似实验能检索并应用已有经验"""
        user_id, agent_id = test_user_a
        experience_service = ExperienceService(db_session)

        # 1. 先创建一个已验证的经验
        experience_data = {
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "success",
            "situation": "分析机器学习文档",
            "action": "search_documents; analyze_content; generate_response",
            "result": "Success",
            "lesson": "成功完成文档分析任务",
            "solution": "使用标准文档分析流程",
            "skills_used": [],
            "skills_discovered": [],
        }
        experience = await experience_service.create_experience(experience_data)

        # 2. 将经验状态改为 verified（模拟已经过验证期）
        # 应用 3 次，2 次成功
        await experience_service.apply_experience(experience.id, user_id, success=True)
        await experience_service.apply_experience(experience.id, user_id, success=True)
        await experience_service.apply_experience(experience.id, user_id, success=False)

        await db_session.refresh(experience)
        assert experience.status == "verified"
        print(f"经验已验证: {experience.id}, 应用次数: {experience.applied_count}")

        # 3. 创建新实验（相似任务）
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Second Document Analysis",
            experiment_type="document",
            input_data={"task": "搜索并分析关于机器学习的文档"},  # 相似任务
            status="pending",
        )
        db_session.add(experiment)
        await db_session.flush()

        # 4. 运行新实验
        mcp_manager = MCPClientManager()
        skill_discovery = SkillService(db_session, mcp_manager)
        engine = ExperimentEngine(db_session, experience_service, skill_discovery)

        result = await engine.run_experiment(experiment.id, user_id)

        # 5. 验证实验成功，并且使用了已有经验
        assert result.success is True

        # 6. 验证原经验的应用统计增加了
        await db_session.refresh(experience)
        # 注意：由于经验复用逻辑在 reflect_phase 中，应用统计应该已经更新
        print(f"经验应用后: 应用次数={experience.applied_count}, 成功次数={experience.success_count}")

    @pytest.mark.asyncio
    async def test_experience_verification_flow(self, db_session, test_user_a):
        """测试经验验证期机制：draft -> verified/deprecated"""
        user_id, agent_id = test_user_a
        service = ExperienceService(db_session)

        # 1. 创建经验
        experience_data = {
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "success",
            "situation": "测试情境",
            "action": "测试行动",
            "result": "测试结果",
            "lesson": "测试教训",
            "solution": "测试解决方案",
        }
        experience = await service.create_experience(experience_data)
        assert experience.status == "draft"

        # 2. 应用 2 次成功，状态仍为 draft
        await service.apply_experience(experience.id, user_id, success=True)
        await service.apply_experience(experience.id, user_id, success=True)
        await db_session.refresh(experience)
        assert experience.status == "draft"
        assert experience.applied_count == 2

        # 3. 第 3 次应用成功，达到 verified 条件
        await service.apply_experience(experience.id, user_id, success=True)
        await db_session.refresh(experience)
        assert experience.status == "verified"
        assert experience.applied_count == 3
        assert experience.success_count == 3
        print(f"经验已验证通过: {experience.id}")


class TestSkillDiscovery:
    """测试技能发现：能力不足 -> 搜索 -> 调用 -> 记录"""

    @pytest.mark.asyncio
    async def test_mcp_server_config(self, db_session, test_user_a):
        """测试 MCP Server 配置管理"""
        user_id, agent_id = test_user_a

        # 1. 创建 MCP Server 配置
        config = MCPServerConfig(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name="test_fetch",
            transport="stdio",
            command="uvx",
            args=["mcp-server-fetch"],
            allowed_agents=[],  # 空列表表示所有 Agent 可用
            is_active=True,
        )
        db_session.add(config)
        await db_session.flush()

        # 2. 验证配置已保存
        result = await db_session.execute(
            select(MCPServerConfig).where(MCPServerConfig.id == config.id)
        )
        saved_config = result.scalar_one_or_none()
        assert saved_config is not None
        assert saved_config.user_id == user_id
        assert saved_config.name == "test_fetch"
        print(f"MCP Server 配置已创建: {saved_config.name}")

    @pytest.mark.asyncio
    async def test_skill_discovery_service(self, db_session, test_user_a):
        """测试技能发现服务的基本功能"""
        user_id, agent_id = test_user_a

        # 创建服务实例
        mcp_manager = MCPClientManager()
        service = SkillService(db_session, mcp_manager)

        # 验证服务可以实例化
        assert service is not None
        assert service.db == db_session
        assert service.mcp_manager == mcp_manager
        print("技能发现服务实例化成功")


class TestPermissionIsolation:
    """测试权限隔离：用户 A 不能访问用户 B 的数据"""

    @pytest.mark.asyncio
    async def test_experience_isolation(self, db_session, test_user_a, test_user_b):
        """测试经验数据隔离"""
        user_a_id, agent_a_id = test_user_a
        user_b_id, agent_b_id = test_user_b

        service = ExperienceService(db_session)

        # 1. 用户 A 创建经验
        experience_data = {
            "user_id": user_a_id,
            "source_agent_id": agent_a_id,
            "type": "success",
            "situation": "用户 A 的情境",
            "action": "用户 A 的行动",
            "result": "用户 A 的结果",
            "lesson": "用户 A 的教训",
            "solution": "用户 A 的解决方案",
        }
        experience_a = await service.create_experience(experience_data)

        # 2. 用户 B 尝试访问用户 A 的经验
        experience_from_b = await service.get_experience(experience_a.id, user_b_id)
        assert experience_from_b is None, "用户 B 不应该能访问用户 A 的经验"

        # 3. 用户 B 获取经验列表，应该为空
        experiences_b = await service.list_experiences(user_id=user_b_id)
        assert len(experiences_b) == 0, "用户 B 不应该看到用户 A 的经验"

        # 4. 用户 A 可以正常访问自己的经验
        experience_from_a = await service.get_experience(experience_a.id, user_a_id)
        assert experience_from_a is not None
        assert experience_from_a.user_id == user_a_id
        print("经验数据隔离验证通过")

    @pytest.mark.asyncio
    async def test_experiment_isolation(self, db_session, test_user_a, test_user_b):
        """测试实验数据隔离"""
        user_a_id, agent_a_id = test_user_a
        user_b_id, agent_b_id = test_user_b

        # 1. 用户 A 创建实验
        experiment_a = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_a_id,
            user_id=user_a_id,
            name="User A Experiment",
            experiment_type="document",
            input_data={"task": "test"},
            status="pending",
        )
        db_session.add(experiment_a)
        await db_session.flush()

        # 2. 用户 B 尝试查询用户 A 的实验
        result = await db_session.execute(
            select(Experiment).where(
                Experiment.id == experiment_a.id,
                Experiment.user_id == user_b_id
            )
        )
        experiment_from_b = result.scalar_one_or_none()
        assert experiment_from_b is None, "用户 B 不应该能访问用户 A 的实验"

        # 3. 用户 A 可以正常访问自己的实验
        result = await db_session.execute(
            select(Experiment).where(
                Experiment.id == experiment_a.id,
                Experiment.user_id == user_a_id
            )
        )
        experiment_from_a = result.scalar_one_or_none()
        assert experiment_from_a is not None
        print("实验数据隔离验证通过")

    @pytest.mark.asyncio
    async def test_agent_isolation(self, db_session, test_user_a, test_user_b):
        """测试 Agent 数据隔离"""
        user_a_id, agent_a_id = test_user_a
        user_b_id, agent_b_id = test_user_b

        # 用户 B 尝试访问用户 A 的 Agent
        result = await db_session.execute(
            select(Agent).where(
                Agent.id == agent_a_id,
                Agent.user_id == user_b_id
            )
        )
        agent_from_b = result.scalar_one_or_none()
        assert agent_from_b is None, "用户 B 不应该能访问用户 A 的 Agent"

        # 用户 A 可以访问自己的 Agent
        result = await db_session.execute(
            select(Agent).where(
                Agent.id == agent_a_id,
                Agent.user_id == user_a_id
            )
        )
        agent_from_a = result.scalar_one_or_none()
        assert agent_from_a is not None
        print("Agent 数据隔离验证通过")


class TestExperimentEngine:
    """测试 Experiment 执行引擎"""

    @pytest.mark.asyncio
    async def test_experiment_execution_flow(self, db_session, test_user_a):
        """测试完整的实验执行流程"""
        user_id, agent_id = test_user_a

        # 创建实验
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Test Execution Flow",
            experiment_type="document",
            input_data={"task": "分析测试文档"},
            status="pending",
        )
        db_session.add(experiment)
        await db_session.flush()

        # 运行实验
        experience_service = ExperienceService(db_session)
        mcp_manager = MCPClientManager()
        skill_discovery = SkillService(db_session, mcp_manager)
        engine = ExperimentEngine(db_session, experience_service, skill_discovery)

        result = await engine.run_experiment(experiment.id, user_id)

        # 验证执行结果
        assert result is not None
        assert result.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]
        assert result.duration_ms >= 0
        assert result.steps_executed >= 0

        # 验证实验状态已更新
        await db_session.refresh(experiment)
        assert experiment.status in ["success", "failed"]
        assert experiment.output_data is not None
        print(f"实验执行完成: 状态={experiment.status}, 耗时={result.duration_ms}ms, 步骤={result.steps_executed}")

    @pytest.mark.asyncio
    async def test_experiment_status_transitions(self, db_session, test_user_a):
        """测试实验状态转换"""
        user_id, agent_id = test_user_a

        # 创建实验
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Test Status Transition",
            experiment_type="document",
            input_data={"task": "测试状态转换"},
            status="pending",
        )
        db_session.add(experiment)
        await db_session.flush()

        assert experiment.status == "pending"

        # 运行实验
        experience_service = ExperienceService(db_session)
        mcp_manager = MCPClientManager()
        skill_discovery = SkillService(db_session, mcp_manager)
        engine = ExperimentEngine(db_session, experience_service, skill_discovery)

        await engine.run_experiment(experiment.id, user_id)

        # 验证最终状态
        await db_session.refresh(experiment)
        assert experiment.status in ["success", "failed"]
        print(f"实验状态转换: pending -> {experiment.status}")


class TestExperienceMutation:
    """测试经验变异功能"""

    @pytest.mark.asyncio
    async def test_experience_mutation_flow(self, db_session, test_user_a):
        """测试经验变异流程"""
        user_id, agent_id = test_user_a
        service = ExperienceService(db_session)

        # 1. 创建原始经验
        experience_data = {
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "success",
            "situation": "原始情境",
            "action": "原始行动",
            "result": "原始结果",
            "lesson": "原始教训",
            "solution": "原始解决方案",
        }
        original = await service.create_experience(experience_data)
        assert original.generation == 1

        # 2. 变异经验
        new_experience = await service.mutate_experience(
            original_id=original.id,
            user_id=user_id,
            agent_id=agent_id,
            improved_solution="改进后的解决方案",
            variant_reason="发现更好的方法",
        )

        # 3. 验证变异结果
        assert new_experience is not None
        assert new_experience.parent_id == original.id
        assert new_experience.generation == original.generation + 1
        assert new_experience.solution == "改进后的解决方案"
        assert new_experience.is_auto_variant is True
        assert new_experience.status == "draft"  # 变异后的经验重新进入验证期

        # 4. 验证族谱链
        assert original.id in new_experience.evolution_chain
        assert new_experience.id in new_experience.evolution_chain
        print(f"经验变异成功: gen {original.generation} -> gen {new_experience.generation}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
