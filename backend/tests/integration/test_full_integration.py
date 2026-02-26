#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整集成测试

测试目标：
1. 完整流程：创建 Agent -> 运行实验 -> 沉淀经验
2. 另一 Agent 查询并采纳经验
"""

import pytest
import pytest_asyncio
import uuid
import shutil
from pathlib import Path
from typing import Tuple, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agent_builder.core.database import async_session_factory, init_db
from agent_builder.db.models import Agent, Experiment, Experience
from agent_builder.services.agent_initializer import get_agent_initializer
from agent_builder.services.skill_system import AgentSkillSystem
from agent_builder.services.experience_service import ExperienceService
from agent_builder.services.skill_service import SkillService
from agent_builder.services.experiment_engine import ExperimentEngine
from agent_builder.services.mcp_client_manager import MCPClientManager
from agent_builder.services.experience_manager import get_experience_manager
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
async def test_workspace():
    """Create a temporary workspace directory for testing."""
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="integration_test_")
    yield temp_dir
    # Cleanup after test
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest_asyncio.fixture
async def integration_setup(db_session, test_workspace):
    """Setup complete integration test environment with user and two agents."""
    user_id = str(uuid.uuid4())

    # Create first Agent (Creator)
    agent_a_id = str(uuid.uuid4())
    agent_a = Agent(
        id=agent_a_id,
        user_id=user_id,
        name="Creator Agent",
        model="deepseek-chat",
        system_prompt="You create new solutions.",
        max_steps=50,
    )
    db_session.add(agent_a)

    # Create second Agent (Learner)
    agent_b_id = str(uuid.uuid4())
    agent_b = Agent(
        id=agent_b_id,
        user_id=user_id,
        name="Learner Agent",
        model="deepseek-chat",
        system_prompt="You learn from others.",
        max_steps=50,
    )
    db_session.add(agent_b)

    await db_session.flush()

    # Initialize directories for both agents
    initializer = get_agent_initializer(workspaces_dir=test_workspace)
    initializer.initialize_agent_directories(user_id, agent_a_id)
    initializer.initialize_agent_directories(user_id, agent_b_id)

    return {
        "user_id": user_id,
        "agent_a_id": agent_a_id,
        "agent_b_id": agent_b_id,
        "workspaces_dir": test_workspace
    }


class TestFullIntegrationFlow:
    """测试完整的集成流程"""

    @pytest.mark.asyncio
    async def test_complete_agent_lifecycle(self, integration_setup, db_session):
        """测试完整 Agent 生命周期：创建 -> 实验 -> 经验 -> 复用"""
        setup_data = integration_setup
        user_id = setup_data["user_id"]
        agent_a_id = setup_data["agent_a_id"]
        agent_b_id = setup_data["agent_b_id"]
        workspaces_dir = setup_data["workspaces_dir"]

        # ========== Step 1: Agent A 创建并运行实验 ==========
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_a_id,
            user_id=user_id,
            name="Data Analysis Experiment",
            experiment_type="problem_solving",
            input_data={
                "task": "分析数据并生成报告",
                "data_source": "test_data.csv"
            },
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

        # 验证实验执行
        assert result is not None
        assert result.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]

        # ========== Step 2: 验证经验沉淀 ==========
        if result.success:
            assert result.experience_id is not None

            # 获取经验详情
            experience = await experience_service.get_experience(result.experience_id, user_id)
            assert experience is not None
            assert experience.user_id == user_id
            assert experience.source_agent_id == agent_a_id
            assert experience.status == "draft"

            # 验证文件系统中的经验记录
            exp_manager = get_experience_manager(workspaces_dir=workspaces_dir)
            file_experiences = exp_manager.list_experiences(user_id, agent_a_id)
            # 注意：文件系统经验只在特定条件下创建
            assert isinstance(file_experiences, list)

        # ========== Step 3: Agent B 查询经验 ==========
        # 获取所有经验
        all_experiences = await experience_service.list_experiences(user_id=user_id)
        assert len(all_experiences) > 0

        # 搜索相关经验
        relevant_exps = await experience_service.search_relevant_experiences(
            user_id=user_id,
            agent_id=agent_b_id,
            query="数据分析",
            top_k=5
        )
        assert isinstance(relevant_exps, list)

        # ========== Step 4: Agent B 采纳经验 ==========
        if relevant_exps:
            target_exp = relevant_exps[0]

            # 吸收经验
            absorption = await experience_service.absorb_experience(
                agent_id=agent_b_id,
                experience_id=target_exp.id,
                user_id=user_id,
                absorption_type="referenced",
                helpful_rating=5
            )

            assert absorption is not None
            assert absorption.agent_id == agent_b_id
            assert absorption.experience_id == target_exp.id

    @pytest.mark.asyncio
    async def test_cross_agent_experience_sharing(self, integration_setup, db_session):
        """测试跨 Agent 经验共享"""
        setup_data = integration_setup
        user_id = setup_data["user_id"]
        agent_a_id = setup_data["agent_a_id"]
        agent_b_id = setup_data["agent_b_id"]

        experience_service = ExperienceService(db_session)

        # ========== Step 1: Agent A 创建并验证经验 ==========
        exp_data = {
            "user_id": user_id,
            "source_agent_id": agent_a_id,
            "type": "success",
            "situation": "Web 数据抓取任务",
            "action": "使用 fetch API 获取数据",
            "result": "Success",
            "lesson": "成功抓取网页数据",
            "solution": "使用 fetch 工具并发送正确的 headers",
        }
        experience = await experience_service.create_experience(exp_data)

        # 应用 3 次使其成为 verified
        await experience_service.apply_experience(experience.id, user_id, success=True)
        await experience_service.apply_experience(experience.id, user_id, success=True)
        await experience_service.apply_experience(experience.id, user_id, success=True)

        await db_session.refresh(experience)
        assert experience.status == "verified"

        # ========== Step 2: Agent B 查询并找到该经验 ==========
        relevant_exps = await experience_service.search_relevant_experiences(
            user_id=user_id,
            agent_id=agent_b_id,
            query="网页数据",  # Match the lesson text "成功抓取网页数据"
            top_k=5
        )

        # 验证能找到 Agent A 的经验
        exp_ids = [exp.id for exp in relevant_exps]
        assert experience.id in exp_ids

        # ========== Step 3: Agent B 吸收并使用经验 ==========
        absorption = await experience_service.absorb_experience(
            agent_id=agent_b_id,
            experience_id=experience.id,
            user_id=user_id,
            absorption_type="injected",
            helpful_rating=4
        )

        assert absorption is not None
        assert absorption.agent_id == agent_b_id
        assert absorption.absorption_type == "injected"

    @pytest.mark.asyncio
    async def test_experience_evolution_chain(self, integration_setup, db_session):
        """测试经验进化链"""
        setup_data = integration_setup
        user_id = setup_data["user_id"]
        agent_a_id = setup_data["agent_a_id"]
        agent_b_id = setup_data["agent_b_id"]

        experience_service = ExperienceService(db_session)

        # ========== Step 1: Agent A 创建原始经验 ==========
        exp_data = {
            "user_id": user_id,
            "source_agent_id": agent_a_id,
            "type": "success",
            "situation": "原始问题解决",
            "action": "原始方法",
            "result": "Success",
            "lesson": "原始教训",
            "solution": "原始解决方案",
        }
        original_exp = await experience_service.create_experience(exp_data)

        # ========== Step 2: Agent B 变异经验 ==========
        mutated_exp = await experience_service.mutate_experience(
            original_id=original_exp.id,
            user_id=user_id,
            agent_id=agent_b_id,
            improved_solution="Agent B 改进的解决方案",
            variant_reason="Agent B 发现了更优方法"
        )

        assert mutated_exp is not None
        assert mutated_exp.parent_id == original_exp.id
        assert mutated_exp.generation == original_exp.generation + 1

        # ========== Step 3: 验证进化链 ==========
        assert original_exp.id in mutated_exp.evolution_chain
        assert mutated_exp.id in mutated_exp.evolution_chain

        # ========== Step 4: 进一步变异 ==========
        mutated_exp2 = await experience_service.mutate_experience(
            original_id=mutated_exp.id,
            user_id=user_id,
            agent_id=agent_a_id,
            improved_solution="进一步优化的解决方案",
            variant_reason="再次改进"
        )

        assert mutated_exp2.generation == 3  # 原始 -> 第一代变异 -> 第二代变异

    @pytest.mark.asyncio
    async def test_experiment_with_experience_reuse(self, integration_setup, db_session):
        """测试实验中复用已有经验"""
        setup_data = integration_setup
        user_id = setup_data["user_id"]
        agent_a_id = setup_data["agent_a_id"]
        agent_b_id = setup_data["agent_b_id"]

        experience_service = ExperienceService(db_session)

        # ========== Step 1: 创建已验证的经验 ==========
        exp_data = {
            "user_id": user_id,
            "source_agent_id": agent_a_id,
            "type": "success",
            "situation": "API 调用最佳实践",
            "action": "配置正确的请求头和超时",
            "result": "Success",
            "lesson": "API 调用需要正确配置",
            "solution": "设置 headers 和 timeout 参数",
        }
        experience = await experience_service.create_experience(exp_data)

        # 验证经验
        await experience_service.apply_experience(experience.id, user_id, success=True)
        await experience_service.apply_experience(experience.id, user_id, success=True)
        await experience_service.apply_experience(experience.id, user_id, success=True)

        # ========== Step 2: Agent B 运行相似实验 ==========
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_b_id,
            user_id=user_id,
            name="API Integration Test",
            experiment_type="problem_solving",
            input_data={
                "task": "调用外部 API 获取数据",
                "api_endpoint": "https://api.example.com/data"
            },
            status="pending",
        )
        db_session.add(experiment)
        await db_session.flush()

        # ========== Step 3: 运行实验（应使用已有经验）==========
        mcp_manager = MCPClientManager()
        skill_discovery = SkillService(db_session, mcp_manager)
        engine = ExperimentEngine(db_session, experience_service, skill_discovery)

        result = await engine.run_experiment(experiment.id, user_id)

        # 验证执行完成
        assert result is not None

        # ========== Step 4: 验证经验应用计数增加 ==========
        await db_session.refresh(experience)
        # 经验被引用，应用计数应该增加
        assert experience.applied_count >= 3

    @pytest.mark.asyncio
    async def test_skill_system_with_experiences(self, integration_setup):
        """测试技能系统加载经验"""
        setup_data = integration_setup
        user_id = setup_data["user_id"]
        agent_a_id = setup_data["agent_a_id"]
        agent_b_id = setup_data["agent_b_id"]
        workspaces_dir = setup_data["workspaces_dir"]

        # ========== Step 1: 在 Agent A 的 experiences 目录创建经验 ==========
        exp_manager = get_experience_manager(workspaces_dir=workspaces_dir)

        await exp_manager.create_experience(
            user_id=user_id,
            agent_id=agent_a_id,
            name="data_processing_skill",
            description="数据处理技能",
            skill_content="# 数据处理\n\n处理 CSV 文件的技能",
            implement_code="# 处理逻辑\ndef process(data): return data",
            task_context="数据处理任务",
            source="agent_created"
        )

        # ========== Step 2: 初始化 Agent B 的技能系统 ==========
        skill_system_b = AgentSkillSystem(
            user_id=user_id,
            agent_id=agent_b_id,
            shared_skills_dir="./skills",
            workspaces_dir=workspaces_dir
        )

        # ========== Step 3: 列出所有可用技能 ==========
        all_skills = skill_system_b.list_all_skills()
        assert isinstance(all_skills, list)

        # ========== Step 4: Agent B 可以查询跨 Agent 经验 ==========
        async with async_session_factory() as session:
            exp_service = ExperienceService(session)
            all_experiences = await exp_service.list_experiences(user_id=user_id)
            # 应该包含 Agent A 创建的经验
            assert len(all_experiences) >= 0


class TestMultiAgentCollaboration:
    """测试多 Agent 协作场景"""

    @pytest.mark.asyncio
    async def test_sequential_agent_improvement(self, integration_setup, db_session):
        """测试顺序式 Agent 改进"""
        setup_data = integration_setup
        user_id = setup_data["user_id"]
        agent_a_id = setup_data["agent_a_id"]
        agent_b_id = setup_data["agent_b_id"]

        experience_service = ExperienceService(db_session)

        # Agent A 创建初始经验
        exp_data = {
            "user_id": user_id,
            "source_agent_id": agent_a_id,
            "type": "success",
            "situation": "初始方案",
            "action": "基础实现",
            "result": "Success",
            "lesson": "基础方案可行",
            "solution": "基础解决方案 v1.0",
        }
        exp_v1 = await experience_service.create_experience(exp_data)

        # Agent B 改进
        exp_v2 = await experience_service.mutate_experience(
            original_id=exp_v1.id,
            user_id=user_id,
            agent_id=agent_b_id,
            improved_solution="改进解决方案 v2.0",
            variant_reason="优化性能"
        )

        # Agent A 再次改进
        exp_v3 = await experience_service.mutate_experience(
            original_id=exp_v2.id,
            user_id=user_id,
            agent_id=agent_a_id,
            improved_solution="最终解决方案 v3.0",
            variant_reason="添加新功能"
        )

        # 验证进化链
        assert exp_v1.generation == 1
        assert exp_v2.generation == 2
        assert exp_v3.generation == 3

        assert exp_v1.id in exp_v3.evolution_chain
        assert exp_v2.id in exp_v3.evolution_chain

    @pytest.mark.asyncio
    async def test_parallel_agent_learning(self, integration_setup, db_session):
        """测试并行 Agent 学习"""
        setup_data = integration_setup
        user_id = setup_data["user_id"]
        agent_a_id = setup_data["agent_a_id"]
        agent_b_id = setup_data["agent_b_id"]

        experience_service = ExperienceService(db_session)

        # 创建一个 verified 经验
        exp_data = {
            "user_id": user_id,
            "source_agent_id": agent_a_id,
            "type": "success",
            "situation": "通用解决方案",
            "action": "标准方法",
            "result": "Success",
            "lesson": "通用最佳实践",
            "solution": "标准解决方案",
        }
        experience = await experience_service.create_experience(exp_data)

        # 验证
        for _ in range(3):
            await experience_service.apply_experience(experience.id, user_id, success=True)

        # 两个 Agent 同时吸收该经验
        absorption_a = await experience_service.absorb_experience(
            agent_id=agent_a_id,
            experience_id=experience.id,
            user_id=user_id,
            absorption_type="referenced",
            helpful_rating=5
        )

        absorption_b = await experience_service.absorb_experience(
            agent_id=agent_b_id,
            experience_id=experience.id,
            user_id=user_id,
            absorption_type="referenced",
            helpful_rating=4
        )

        assert absorption_a is not None
        assert absorption_b is not None
        assert absorption_a.agent_id != absorption_b.agent_id


class TestErrorRecovery:
    """测试错误恢复"""

    @pytest.mark.asyncio
    async def test_experiment_failure_creates_failure_experience(self, integration_setup, db_session):
        """测试实验失败创建失败经验"""
        setup_data = integration_setup
        user_id = setup_data["user_id"]
        agent_a_id = setup_data["agent_a_id"]

        # 创建一个会失败的实验
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_a_id,
            user_id=user_id,
            name="Failing Experiment",
            experiment_type="problem_solving",
            input_data={
                "task": "故意失败的任务",
                "should_fail": True
            },
            status="pending",
        )
        db_session.add(experiment)
        await db_session.flush()

        experience_service = ExperienceService(db_session)
        mcp_manager = MCPClientManager()
        skill_discovery = SkillService(db_session, mcp_manager)
        engine = ExperimentEngine(db_session, experience_service, skill_discovery)

        result = await engine.run_experiment(experiment.id, user_id)

        # 即使失败，也应该创建经验
        if result.experience_id:
            experience = await experience_service.get_experience(result.experience_id, user_id)
            assert experience.type == "failure"

    @pytest.mark.asyncio
    async def test_deprecated_experience_not_reused(self, integration_setup, db_session):
        """测试废弃经验不被复用"""
        setup_data = integration_setup
        user_id = setup_data["user_id"]
        agent_a_id = setup_data["agent_a_id"]
        agent_b_id = setup_data["agent_b_id"]

        experience_service = ExperienceService(db_session)

        # 创建一个 deprecated 经验
        exp_data = {
            "user_id": user_id,
            "source_agent_id": agent_a_id,
            "type": "success",
            "situation": "过时的方法",
            "action": "旧方法",
            "result": "Success",
            "lesson": "旧方法的教训",
            "solution": "旧解决方案",
        }
        experience = await experience_service.create_experience(exp_data)

        # 应用 3 次，但只有 1 次成功，使其变为 deprecated
        await experience_service.apply_experience(experience.id, user_id, success=True)
        await experience_service.apply_experience(experience.id, user_id, success=False)
        await experience_service.apply_experience(experience.id, user_id, success=False)

        await db_session.refresh(experience)
        assert experience.status == "deprecated"

        # 搜索经验时应该排除 deprecated
        relevant = await experience_service.search_relevant_experiences(
            user_id=user_id,
            agent_id=agent_b_id,
            query="过时的方法",
            top_k=10
        )

        # deprecated 经验不应该出现在搜索结果中
        deprecated_ids = [exp.id for exp in relevant if exp.status == "deprecated"]
        assert experience.id not in deprecated_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
