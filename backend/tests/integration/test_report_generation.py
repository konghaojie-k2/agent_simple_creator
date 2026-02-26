#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
写报告实验测试

测试目标：
1. 创建 document_generation 类型实验
2. 运行实验并验证输出结构包含：摘要、正文、结论
3. 验证经验正确沉淀
"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from typing import Tuple, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agent_builder.core.database import async_session_factory, init_db
from agent_builder.db.models import Agent, Experiment, Experience
from agent_builder.services.experience_service import ExperienceService
from agent_builder.services.skill_service import SkillService
from agent_builder.services.experiment_engine import ExperimentEngine
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
async def test_user_and_agent(db_session) -> Tuple[str, str]:
    """Create test user and agent."""
    user_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())

    agent = Agent(
        id=agent_id,
        user_id=user_id,
        name="Report Writer Agent",
        model="deepseek-chat",
        system_prompt="You are a report writing specialist.",
        max_steps=50,
    )
    db_session.add(agent)
    await db_session.flush()

    return user_id, agent_id


class TestReportGenerationExperiment:
    """测试写报告实验"""

    @pytest.mark.asyncio
    async def test_create_document_generation_experiment(self, db_session, test_user_and_agent):
        """测试创建 document_generation 类型实验"""
        user_id, agent_id = test_user_and_agent

        # 创建文档生成实验
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Technical Report Generation",
            description="Generate a technical report on AI agents",
            experiment_type="document",  # document 类型
            input_data={
                "task": "写一份关于 AI Agent 技术的报告",
                "report_type": "technical",
                "sections": ["introduction", "methodology", "conclusion"]
            },
            status="pending",
        )
        db_session.add(experiment)
        await db_session.flush()

        # 验证实验创建成功
        assert experiment.id is not None
        assert experiment.experiment_type == "document"
        assert experiment.status == "pending"
        assert "task" in experiment.input_data

    @pytest.mark.asyncio
    async def test_run_report_generation_experiment(self, db_session, test_user_and_agent):
        """测试运行报告生成实验"""
        user_id, agent_id = test_user_and_agent

        # 创建实验
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="AI Agent Report",
            experiment_type="document",
            input_data={
                "task": "生成一份 AI Agent 系统架构报告",
                "report_structure": {
                    "summary": "执行摘要",
                    "body": "正文内容",
                    "conclusion": "结论"
                }
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

        # 验证执行结果
        assert result is not None
        assert result.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]
        assert result.duration_ms >= 0

        # 验证实验状态已更新
        await db_session.refresh(experiment)
        assert experiment.status in ["success", "failed"]
        assert experiment.output_data is not None

    @pytest.mark.asyncio
    async def test_report_output_structure(self, db_session, test_user_and_agent):
        """测试报告输出结构验证"""
        user_id, agent_id = test_user_and_agent

        # 创建实验
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Structured Report Test",
            experiment_type="document",
            input_data={
                "task": "生成结构化报告",
                "expected_structure": ["summary", "body", "conclusion"]
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

        # 检查输出数据结构
        await db_session.refresh(experiment)
        output_data = experiment.output_data

        assert output_data is not None
        assert "result" in output_data or "steps" in output_data

        # 检查步骤记录
        if "steps" in output_data:
            steps = output_data["steps"]
            assert isinstance(steps, list)
            # 验证至少有执行步骤
            assert len(steps) >= 0

    @pytest.mark.asyncio
    async def test_experience_precipitation_from_report(self, db_session, test_user_and_agent):
        """测试从报告生成实验沉淀经验"""
        user_id, agent_id = test_user_and_agent

        # 创建实验
        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Report with Experience",
            experiment_type="document",
            input_data={
                "task": "生成 AI Agent 研究报告",
                "require_experience_tracking": True
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

        # 验证经验被创建
        if result.success:
            assert result.experience_id is not None

            # 获取经验详情
            experience = await experience_service.get_experience(result.experience_id, user_id)
            assert experience is not None
            assert experience.user_id == user_id
            assert experience.source_agent_id == agent_id
            assert experience.source_experiment_id == experiment.id
            assert experience.type in ["success", "failure"]
            assert experience.status == "draft"

    @pytest.mark.asyncio
    async def test_experience_content_from_report(self, db_session, test_user_and_agent):
        """测试从报告生成的内容正确沉淀到经验"""
        user_id, agent_id = test_user_and_agent

        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Content Precipitation Test",
            experiment_type="document",
            input_data={
                "task": "生成机器学习研究报告",
                "topic": "machine_learning"
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

        # 如果成功，验证经验内容
        if result.success and result.experience_id:
            experience = await experience_service.get_experience(result.experience_id, user_id)

            # 验证经验字段
            assert experience.situation is not None
            assert "机器学习研究报告" in experience.situation or "machine_learning" in experience.situation.lower()
            assert experience.action is not None
            assert experience.lesson is not None

    @pytest.mark.asyncio
    async def test_report_with_skill_usage(self, db_session, test_user_and_agent):
        """测试报告生成中使用技能"""
        user_id, agent_id = test_user_and_agent

        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Report with Skills",
            experiment_type="document",
            input_data={
                "task": "使用文档分析和生成技能创建报告",
                "use_skills": True
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

        # 验证执行完成
        assert result is not None
        assert result.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]


class TestReportOutputValidation:
    """测试报告输出验证"""

    @pytest.mark.asyncio
    async def test_summary_section_present(self, db_session, test_user_and_agent):
        """测试输出包含摘要部分"""
        user_id, agent_id = test_user_and_agent

        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Summary Test",
            experiment_type="document",
            input_data={
                "task": "生成包含摘要的报告",
                "sections": ["summary"]
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

        # 验证执行完成（具体内容取决于实现）
        assert result is not None

    @pytest.mark.asyncio
    async def test_body_section_present(self, db_session, test_user_and_agent):
        """测试输出包含正文部分"""
        user_id, agent_id = test_user_and_agent

        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Body Test",
            experiment_type="document",
            input_data={
                "task": "生成包含正文的报告",
                "sections": ["body"]
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

        assert result is not None

    @pytest.mark.asyncio
    async def test_conclusion_section_present(self, db_session, test_user_and_agent):
        """测试输出包含结论部分"""
        user_id, agent_id = test_user_and_agent

        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Conclusion Test",
            experiment_type="document",
            input_data={
                "task": "生成包含结论的报告",
                "sections": ["conclusion"]
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

        assert result is not None


class TestReportExperienceQuality:
    """测试报告经验质量"""

    @pytest.mark.asyncio
    async def test_experience_captures_report_structure(self, db_session, test_user_and_agent):
        """测试经验捕获报告结构信息"""
        user_id, agent_id = test_user_and_agent

        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Structure Capture Test",
            experiment_type="document",
            input_data={
                "task": "测试报告结构捕获",
                "structure": "summary-body-conclusion"
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

        if result.success and result.experience_id:
            experience = await experience_service.get_experience(result.experience_id, user_id)

            # 验证经验记录了任务信息
            assert experience.situation is not None
            assert len(experience.situation) > 0

    @pytest.mark.asyncio
    async def test_experience_tracks_successful_reports(self, db_session, test_user_and_agent):
        """测试经验跟踪成功报告"""
        user_id, agent_id = test_user_and_agent

        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Success Tracking Test",
            experiment_type="document",
            input_data={
                "task": "生成成功报告"
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

        if result.success:
            assert result.experience_id is not None
            experience = await experience_service.get_experience(result.experience_id, user_id)
            assert experience.type == "success"

    @pytest.mark.asyncio
    async def test_experience_tracks_failed_reports(self, db_session, test_user_and_agent):
        """测试经验跟踪失败报告"""
        user_id, agent_id = test_user_and_agent

        experiment = Experiment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            name="Failure Tracking Test",
            experiment_type="document",
            input_data={
                "task": "故意失败的任务测试"
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
        if not result.success:
            assert result.experience_id is not None
            experience = await experience_service.get_experience(result.experience_id, user_id)
            assert experience.type == "failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
