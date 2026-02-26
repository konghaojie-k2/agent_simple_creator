#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试跨Agent经验查询功能"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from sqlalchemy import select

from agent_builder.services.experience_service import ExperienceService
from agent_builder.db.models import Experience, Agent
from agent_builder.core.database import async_session_factory


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    async with async_session_factory() as session:
        yield session
        # Rollback after test
        await session.rollback()


@pytest_asyncio.fixture
async def test_user_and_agent(db_session):
    """Create test user and agent IDs."""
    user_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())

    # Create agent in database
    agent = Agent(
        id=agent_id,
        user_id=user_id,
        name="Test Agent",
        model="gpt-4",
    )
    db_session.add(agent)
    await db_session.flush()

    return user_id, agent_id


@pytest.mark.asyncio
class TestCrossAgentExperienceQueries:
    """测试跨Agent经验查询"""

    async def test_list_user_experiences_default_verified_only(
        self,
        db_session,
        test_user_and_agent
    ):
        """测试默认返回verified经验"""
        user_id, agent_id = test_user_and_agent
        service = ExperienceService(db_session)

        # 创建不同状态的经验
        verified_exp = await service.create_experience({
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "problem_solving",
            "situation": "测试情况",
            "action": "测试行动",
            "result": "测试结果",
            "lesson": "测试教训",
            "solution": "verified方案"
        })
        verified_exp.status = "verified"
        await db_session.flush()

        draft_exp = await service.create_experience({
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "problem_solving",
            "situation": "草稿情况",
            "action": "草稿行动",
            "result": "草稿结果",
            "lesson": "草稿教训",
            "solution": "draft方案"
        })
        # draft_exp.status 默认为 "draft"

        await db_session.flush()

        # 查询 - 默认返回verified
        experiences = await service.list_user_experiences(
            user_id=user_id,
            limit=10
        )

        assert len(experiences) == 1
        assert experiences[0].status == "verified"
        assert experiences[0].solution == "verified方案"

    async def test_list_user_experiences_with_status_filter(
        self,
        db_session,
        test_user_and_agent
    ):
        """测试按状态过滤"""
        user_id, agent_id = test_user_and_agent
        service = ExperienceService(db_session)

        # 创建不同状态的经验
        await service.create_experience({
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "problem_solving",
            "situation": "verified情况",
            "action": "verified行动",
            "result": "verified结果",
            "lesson": "verified教训",
            "solution": "verified方案"
        })
        # 修改为verified
        result = await db_session.execute(
            select(Experience).where(Experience.solution == "verified方案")
        )
        exp = result.scalar_one_or_none()
        if exp:
            exp.status = "verified"

        draft_exp = await service.create_experience({
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "problem_solving",
            "situation": "draft情况",
            "action": "draft行动",
            "result": "draft结果",
            "lesson": "draft教训",
            "solution": "draft方案"
        })
        # draft_exp.status 默认为 "draft"

        deprecated_exp = await service.create_experience({
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "problem_solving",
            "situation": "deprecated情况",
            "action": "deprecated行动",
            "result": "deprecated结果",
            "lesson": "deprecated教训",
            "solution": "deprecated方案"
        })
        # 修改为deprecated
        result = await db_session.execute(
            select(Experience).where(Experience.solution == "deprecated方案")
        )
        exp = result.scalar_one_or_none()
        if exp:
            exp.status = "deprecated"

        await db_session.flush()

        # 查询draft状态
        draft_experiences = await service.list_user_experiences(
            user_id=user_id,
            status="draft",
            limit=10
        )
        assert len(draft_experiences) == 1
        assert draft_experiences[0].status == "draft"

        # 查询deprecated状态
        deprecated_experiences = await service.list_user_experiences(
            user_id=user_id,
            status="deprecated",
            limit=10
        )
        assert len(deprecated_experiences) == 1
        assert deprecated_experiences[0].status == "deprecated"

    async def test_list_user_experiences_limit(
        self,
        db_session,
        test_user_and_agent
    ):
        """测试限制返回数量"""
        user_id, agent_id = test_user_and_agent
        service = ExperienceService(db_session)

        # 创建多个verified经验
        for i in range(5):
            exp = await service.create_experience({
                "user_id": user_id,
                "source_agent_id": agent_id,
                "type": "problem_solving",
                "situation": f"情况{i}",
                "action": f"行动{i}",
                "result": f"结果{i}",
                "lesson": f"教训{i}",
                "solution": f"方案{i}"
            })
            exp.status = "verified"
            if i > 0:
                exp.last_applied_at = datetime.utcnow()

        await db_session.flush()

        # 查询限制为3
        experiences = await service.list_user_experiences(
            user_id=user_id,
            limit=3
        )

        assert len(experiences) == 3

    async def test_list_user_experiences_ordering(
        self,
        db_session,
        test_user_and_agent
    ):
        """测试返回顺序（按last_applied_at降序）"""
        user_id, agent_id = test_user_and_agent
        service = ExperienceService(db_session)

        # 创建多个verified经验，不同的last_applied_at
        exp1 = await service.create_experience({
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "problem_solving",
            "situation": "情况1",
            "action": "行动1",
            "result": "结果1",
            "lesson": "教训1",
            "solution": "方案1"
        })
        exp1.status = "verified"
        exp1.last_applied_at = datetime(2025, 1, 1, 10, 0, 0)

        exp2 = await service.create_experience({
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "problem_solving",
            "situation": "情况2",
            "action": "行动2",
            "result": "结果2",
            "lesson": "教训2",
            "solution": "方案2"
        })
        exp2.status = "verified"
        exp2.last_applied_at = datetime(2025, 1, 2, 10, 0, 0)

        exp3 = await service.create_experience({
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "problem_solving",
            "situation": "情况3",
            "action": "行动3",
            "result": "结果3",
            "lesson": "教训3",
            "solution": "方案3"
        })
        exp3.status = "verified"
        # exp3 没有last_applied_at

        await db_session.flush()

        experiences = await service.list_user_experiences(
            user_id=user_id,
            limit=10
        )

        assert len(experiences) == 3
        # exp2应该排在最前面（最新的last_applied_at）
        assert experiences[0].solution == "方案2"
        assert experiences[1].solution == "方案1"
        assert experiences[2].solution == "方案3"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
