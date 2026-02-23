# -*- coding: utf-8 -*-
"""Tests for experience system."""

import pytest
import pytest_asyncio
import uuid
import asyncio
from datetime import datetime

from agent_builder.services.experience_service import ExperienceService
from agent_builder.db.models import Experience, AgentExperienceAbsorption, Agent
from agent_builder.core.database import async_session_factory, init_db


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


class TestExperienceService:
    """Test cases for ExperienceService."""

    @pytest.mark.asyncio
    async def test_create_experience(self, db_session, test_user_and_agent):
        """Test creating a new experience."""
        user_id, agent_id = test_user_and_agent
        service = ExperienceService(db_session)

        data = {
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "success",
            "situation": "Test situation",
            "action": "Test action",
            "result": "Test result",
            "lesson": "Test lesson",
            "solution": "Test solution",
        }

        experience = await service.create_experience(data)

        assert experience is not None
        assert experience.user_id == user_id
        assert experience.source_agent_id == agent_id
        assert experience.type == "success"
        assert experience.status == "draft"
        assert experience.applied_count == 0
        assert experience.success_count == 0
        assert experience.generation == 1
        print(f"Created experience: {experience.id} with status {experience.status}")

    @pytest.mark.asyncio
    async def test_apply_experience_verification(self, db_session, test_user_and_agent):
        """Test experience verification logic."""
        user_id, agent_id = test_user_and_agent
        service = ExperienceService(db_session)

        # Create experience
        data = {
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "success",
            "situation": "Test situation",
            "action": "Test action",
            "result": "Test result",
            "lesson": "Test lesson",
            "solution": "Test solution",
        }
        experience = await service.create_experience(data)

        # Apply 3 times with 2 successes
        await service.apply_experience(experience.id, user_id, success=True)
        await service.apply_experience(experience.id, user_id, success=True)
        await service.apply_experience(experience.id, user_id, success=False)

        # Refresh experience
        updated = await service.get_experience(experience.id, user_id)

        assert updated.status == "verified"
        assert updated.applied_count == 3
        assert updated.success_count == 2
        print(f"Experience verified: {updated.id}, applied={updated.applied_count}, success={updated.success_count}")

    @pytest.mark.asyncio
    async def test_apply_experience_deprecated(self, db_session, test_user_and_agent):
        """Test experience deprecation logic."""
        user_id, agent_id = test_user_and_agent
        service = ExperienceService(db_session)

        # Create experience
        data = {
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "failure",
            "situation": "Test situation",
            "action": "Test action",
            "result": "Test result",
            "lesson": "Test lesson",
            "solution": "Test solution",
        }
        experience = await service.create_experience(data)

        # Apply 3 times with only 1 success
        await service.apply_experience(experience.id, user_id, success=True)
        await service.apply_experience(experience.id, user_id, success=False)
        await service.apply_experience(experience.id, user_id, success=False)

        # Refresh experience
        updated = await service.get_experience(experience.id, user_id)

        assert updated.status == "deprecated"
        assert updated.applied_count == 3
        assert updated.success_count == 1
        print(f"Experience deprecated: {updated.id}, applied={updated.applied_count}, success={updated.success_count}")

    @pytest.mark.asyncio
    async def test_mutate_experience(self, db_session, test_user_and_agent):
        """Test experience mutation."""
        user_id, agent_id = test_user_and_agent
        service = ExperienceService(db_session)

        # Create original experience
        data = {
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "success",
            "situation": "Original situation",
            "action": "Original action",
            "result": "Original result",
            "lesson": "Original lesson",
            "solution": "Original solution",
        }
        original = await service.create_experience(data)

        # Mutate experience
        new_experience = await service.mutate_experience(
            original_id=original.id,
            user_id=user_id,
            agent_id=agent_id,
            improved_solution="Improved solution",
            variant_reason="Better approach found",
        )

        assert new_experience is not None
        assert new_experience.parent_id == original.id
        assert new_experience.generation == original.generation + 1
        assert new_experience.solution == "Improved solution"
        assert new_experience.is_auto_variant is True
        assert new_experience.variant_reason == "Better approach found"
        assert original.id in new_experience.evolution_chain
        print(f"Mutated experience: gen {original.generation} -> gen {new_experience.generation}")

    @pytest.mark.asyncio
    async def test_absorb_experience(self, db_session, test_user_and_agent):
        """Test agent absorbing experience."""
        user_id, agent_id = test_user_and_agent
        service = ExperienceService(db_session)

        # Create experience
        data = {
            "user_id": user_id,
            "source_agent_id": agent_id,
            "type": "success",
            "situation": "Test situation",
            "action": "Test action",
            "result": "Test result",
            "lesson": "Test lesson",
            "solution": "Test solution",
        }
        experience = await service.create_experience(data)

        # Absorb experience
        absorption = await service.absorb_experience(
            agent_id=agent_id,
            experience_id=experience.id,
            user_id=user_id,
            absorption_type="referenced",
            helpful_rating=5,
        )

        assert absorption is not None
        assert absorption.agent_id == agent_id
        assert absorption.experience_id == experience.id
        assert absorption.absorption_type == "referenced"
        assert absorption.helpful_rating == 5
        print(f"Experience absorbed: {absorption.id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
