# -*- coding: utf-8 -*-
"""API routes for agents."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.db.models import Agent
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.pydantic import AgentCreate, AgentResponse, AgentUpdate
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
