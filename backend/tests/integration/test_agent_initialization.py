# -*- coding: utf-8 -*-
"""Tests for Agent initialization and shared skills loading."""

import pytest
import pytest_asyncio
import uuid
import shutil
from pathlib import Path

from agent_builder.services.agent_initializer import get_agent_initializer
from agent_builder.services.skill_system import AgentSkillSystem
from agent_builder.db.models import Agent
from agent_builder.core.database import async_session_factory


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    async with async_session_factory() as session:
        yield session
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


class TestAgentInitialization:
    """Test cases for Agent initialization."""

    @pytest.mark.asyncio
    async def test_directory_structure_creation(self, test_user_and_agent):
        """Test that agent directories are created correctly."""
        user_id, agent_id = test_user_and_agent
        initializer = get_agent_initializer()

        # Initialize directories
        dirs = initializer.initialize_agent_directories(user_id, agent_id)

        # Verify all directories exist (正确的路径是 workspaces/{user_id}/agents/{agent_id})
        workspaces = Path("./workspaces")
        agent_dir = workspaces / user_id / "agents" / agent_id

        assert agent_dir.exists(), "Agent directory should exist"
        assert (agent_dir / "skills").exists(), "Skills directory should exist"
        assert (agent_dir / "experiences").exists(), "Experiences directory should exist"
        assert (agent_dir / "workspace").exists(), "Workspace directory should exist"

        print(f"✓ Directory structure created for agent {agent_id}")

    @pytest.mark.asyncio
    async def test_shared_skills_copy_to_agent(self, test_user_and_agent):
        """Test that shared skills are copied to agent's skills directory."""
        user_id, agent_id = test_user_and_agent
        initializer = get_agent_initializer()

        # Initialize directories
        initializer.initialize_agent_directories(user_id, agent_id)

        # Copy shared skills (新路径: market/skills/public)
        copied_skills = initializer.copy_shared_skills_to_agent(
            user_id=user_id,
            agent_id=agent_id,
            shared_skills_dir="./market/skills/public"
        )

        # Verify skills were copied (正确的路径是 workspaces/{user_id}/agents/{agent_id}/skills)
        agent_skills_dir = Path("./workspaces") / user_id / "agents" / agent_id / "skills"
        shared_skills_dir = Path("./market/skills/public")

        # Count shared skills with SKILL.md
        shared_skill_count = sum(
            1 for d in shared_skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").exists()
        )

        assert len(copied_skills) > 0, "At least one shared skill should be copied"

        # Verify each copied skill has SKILL.md
        for skill_name in copied_skills:
            skill_path = agent_skills_dir / skill_name
            assert skill_path.exists(), f"Skill {skill_name} should exist"
            assert (skill_path / "SKILL.md").exists(), f"Skill {skill_name} should have SKILL.md"

        print(f"✓ Copied {len(copied_skills)} shared skills: {copied_skills}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
