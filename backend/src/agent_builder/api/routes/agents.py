# -*- coding: utf-8 -*-
"""API routes for agents."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.db.models import Agent
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.pydantic import AgentCreate, AgentResponse, AgentUpdate, AgentDetailResponse, ToolInfo, SkillInfo, AgentDirectoryInfo
from agent_builder.services.agent_service import AgentService


router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create a new agent."""
    service = AgentService(db)
    agent = await service.create_agent(user_id, agent_data)

    # 初始化Agent目录结构
    from agent_builder.services.agent_initializer import get_agent_initializer
    initializer = get_agent_initializer()
    dirs = initializer.initialize_agent_directories(user_id, agent.id)

    # 自动加载全量共享技能到Agent的skills目录
    copied_skills = initializer.copy_shared_skills_to_agent(
        user_id=user_id,
        agent_id=agent.id,
        shared_skills_dir="./skills"
    )

    return agent


@router.get("", response_model=List[AgentResponse])
async def get_agents(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get all agents for the current user."""
    service = AgentService(db)
    agents = await service.get_agents(user_id)
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get a specific agent."""
    service = AgentService(db)
    agent = await service.get_agent(agent_id, user_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Update an agent."""
    service = AgentService(db)
    agent = await service.update_agent(agent_id, user_id, agent_data)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Delete an agent."""
    service = AgentService(db)
    success = await service.delete_agent(agent_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )


@router.get("/{agent_id}/detail", response_model=AgentDetailResponse)
async def get_agent_detail(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get detailed agent information including tools and skills."""
    # 1. Get agent basic info
    service = AgentService(db)
    agent = await service.get_agent(agent_id, user_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # 2. Get directory structure
    from agent_builder.services.agent_initializer import get_agent_initializer
    initializer = get_agent_initializer()
    dirs = initializer.get_agent_directories(user_id, agent_id)

    # 3. Get available tools
    from agent_builder.services.tool_registry import get_tool_registry
    tool_registry = get_tool_registry()
    tool_names = tool_registry.list_tools()
    tools = [ToolInfo(name=name, description=f"Built-in tool: {name}") for name in tool_names]

    # 4. Get available skills
    from agent_builder.services.skill_system import AgentSkillSystem
    skill_system = AgentSkillSystem(
        user_id=user_id,
        agent_id=agent_id,
        shared_skills_dir="./skills",
        workspaces_dir="./workspaces"
    )
    skill_names = skill_system.list_all_skills()
    skills = []
    for name in skill_names:
        skill = skill_system.get_skill(name)
        if skill:
            # Determine source
            if skill_system.experience_loader.get_skill(name):
                source = "experience"
            elif skill_system.agent_loader.get_skill(name):
                source = "agent"
            else:
                source = "shared"
            skills.append(SkillInfo(
                name=name,
                description=skill.description,
                source=source
            ))

    # 5. Build response
    return AgentDetailResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        model=agent.model,
        max_steps=agent.max_steps,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        tools=tools,
        skills=skills,
        directories=AgentDirectoryInfo(
            agent_dir=dirs["agent_dir"],
            skills_dir=dirs["skills_dir"],
            experiences_dir=dirs["experiences_dir"],
            workspace_dir=dirs["workspace_dir"]
        )
    )
