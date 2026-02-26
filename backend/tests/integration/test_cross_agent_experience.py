# -*- coding: utf-8 -*-
"""Tests for cross-agent experience query functionality."""

import pytest
import pytest_asyncio
import uuid

from agent_builder.services.experience_service import ExperienceService
from agent_builder.db.models import Agent, Experience
from agent_builder.core.database import async_session_factory


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_data(db_session):
    """Create test data with multiple agents and experiences."""
    user_id = str(uuid.uuid4())
    agent1_id = str(uuid.uuid4())
    agent2_id = str(uuid.uuid4())

    # Create agents
    agent1 = Agent(id=agent1_id, user_id=user_id, name="Agent 1", model="gpt-4")
    agent2 = Agent(id=agent2_id, user_id=user_id, name="Agent 2", model="gpt-4")
    db_session.add(agent1)
    db_session.add(agent2)
    await db_session.commit()  # Commit agents first

    # Create experiences for agent1
    exp1 = Experience(
        id=str(uuid.uuid4()),
        user_id=user_id,
        source_agent_id=agent1_id,
        type="success",
        situation="Task A",
        action="Action A",
        result="Success",
        lesson="Lesson A from agent1",
        solution="Solution A",
        status="verified",
        applied_count=3,
        success_count=3,
    )
    exp2 = Experience(
        id=str(uuid.uuid4()),
        user_id=user_id,
        source_agent_id=agent1_id,
        type="failure",
        situation="Task B",
        action="Action B",
        result="Failed",
        lesson="Lesson B from agent1",
        solution="Solution B",
        status="draft",
    )

    # Create experiences for agent2
    exp3 = Experience(
        id=str(uuid.uuid4()),
        user_id=user_id,
        source_agent_id=agent2_id,
        type="success",
        situation="Task C",
        action="Action C",
        result="Success",
        lesson="Lesson C from agent2",
        solution="Solution C",
        status="verified",
        applied_count=5,
        success_count=4,
    )

    db_session.add(exp1)
    db_session.add(exp2)
    db_session.add(exp3)
    await db_session.commit()  # Commit so data is visible to other sessions

    return {
        "user_id": user_id,
        "agent1_id": agent1_id,
        "agent2_id": agent2_id,
        "exp1_id": exp1.id,
        "exp2_id": exp2.id,
        "exp3_id": exp3.id,
    }


class TestCrossAgentExperienceQuery:
    """Test cases for cross-agent experience queries."""

    @pytest.mark.asyncio
    async def test_list_user_experiences_all_verified(self, test_data):
        """Test listing all verified experiences for a user."""
        user_id = test_data["user_id"]

        async with async_session_factory() as db:
            service = ExperienceService(db)
            experiences = await service.list_user_experiences(
                user_id=user_id,
                status="verified",
                limit=10
            )

            # Should return 2 verified experiences (exp1 and exp3)
            assert len(experiences) == 2, f"Expected 2 verified experiences, got {len(experiences)}"

            # Verify they're from different agents
            agent_ids = {exp.source_agent_id for exp in experiences}
            assert len(agent_ids) == 2, "Should have experiences from both agents"

            print(f"✓ Found {len(experiences)} verified experiences from {len(agent_ids)} agents")

    @pytest.mark.asyncio
    async def test_list_user_experiences_filter_by_status(self, test_data):
        """Test filtering experiences by status."""
        user_id = test_data["user_id"]
        
        async with async_session_factory() as db:
            service = ExperienceService(db)

            # Test draft status
            draft_exps = await service.list_user_experiences(
                user_id=user_id,
                status="draft",
                limit=10
            )
            assert len(draft_exps) == 1, "Should have 1 draft experience"
            assert draft_exps[0].status == "draft"

            # Test deprecated status
            deprecated_exps = await service.list_user_experiences(
                user_id=user_id,
                status="deprecated",
                limit=10
            )
            assert len(deprecated_exps) == 0, "Should have 0 deprecated experiences"

            print(f"✓ Status filter works: draft={len(draft_exps)}, deprecated={len(deprecated_exps)}")

    @pytest.mark.asyncio
    async def test_list_user_experiences_default_verified(self, test_data):
        """Test that default status is verified."""
        user_id = test_data["user_id"]
        
        async with async_session_factory() as db:
            service = ExperienceService(db)

            # Call without status parameter
            experiences = await service.list_user_experiences(
                user_id=user_id,
                limit=10
            )

            # Should default to verified
            assert len(experiences) == 2, "Default should return verified experiences"
            for exp in experiences:
                assert exp.status == "verified", "All returned experiences should be verified"

            print(f"✓ Default status is 'verified': {len(experiences)} experiences")

    @pytest.mark.asyncio
    async def test_list_user_experiences_limit(self, test_data):
        """Test limit parameter."""
        user_id = test_data["user_id"]
        
        async with async_session_factory() as db:
            service = ExperienceService(db)

            # Test with limit=1
            experiences = await service.list_user_experiences(
                user_id=user_id,
                status="verified",
                limit=1
            )
            assert len(experiences) == 1, "Should return only 1 experience with limit=1"

            print(f"✓ Limit parameter works correctly")

    @pytest.mark.asyncio
    async def test_cross_agent_experience_sharing(self, test_data):
        """Test that verified experiences are shared across agents."""
        user_id = test_data["user_id"]
        agent1_id = test_data["agent1_id"]
        agent2_id = test_data["agent2_id"]
        
        async with async_session_factory() as db:
            service = ExperienceService(db)

            # Agent2 should be able to see Agent1's verified experiences
            agent1_verified = await service.list_user_experiences(
                user_id=user_id,
                status="verified",
                limit=10
            )

            # Should include exp1 from agent1
            agent1_exp_ids = {exp.id for exp in agent1_verified if exp.source_agent_id == agent1_id}
            assert len(agent1_exp_ids) > 0, "Agent2 should see Agent1's verified experiences"

            print(f"✓ Cross-agent experience sharing works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
