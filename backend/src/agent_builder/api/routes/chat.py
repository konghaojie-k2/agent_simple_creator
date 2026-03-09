# -*- coding: utf-8 -*-
"""API routes for chat."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.db.models import Agent, LLMProvider
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.pydantic import ChatSessionResponse
from agent_builder.services.agent.agent_service import AgentService, ChatService


router = APIRouter(prefix="/api/chat", tags=["chat"])


async def get_agent_with_provider(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[str] = None,
) -> tuple[Agent, LLMProvider]:
    """Get agent with its provider."""
    agent_service = AgentService(db)
    agent = await agent_service.get_agent(agent_id, user_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    if not agent.provider_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent has no provider configured",
        )

    provider = await agent_service.get_provider(agent.provider_id, user_id)

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider not found",
        )

    if not provider.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider is not active",
        )

    return agent, provider


@router.post("/{agent_id}")
async def chat(
    agent_id: str,
    request: dict,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Chat with an agent (streaming response)."""
    message = request.get("message", "")
    session_id = request.get("session_id")
    
    agent, provider = await get_agent_with_provider(agent_id, db, user_id)

    # Get or create session
    chat_service = ChatService(db)
    session = await chat_service.get_or_create_session(agent_id, session_id)

    async def generate_response():
        """Generate streaming response."""
        try:
            async for chunk in chat_service.chat(agent, provider, message, session):
                # Format as SSE
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # Send final message
            yield f"data: {json.dumps({'done': True, 'session_id': session.id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{agent_id}/sessions", response_model=list[ChatSessionResponse])
async def get_chat_sessions(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get all chat sessions for an agent."""
    # Verify agent exists and belongs to user
    agent_service = AgentService(db)
    agent = await agent_service.get_agent(agent_id, user_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    chat_service = ChatService(db)
    sessions = await chat_service.get_sessions(agent_id)

    return sessions


@router.get("/{agent_id}/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    agent_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get a specific chat session."""
    # Verify agent exists and belongs to user
    agent_service = AgentService(db)
    agent = await agent_service.get_agent(agent_id, user_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    chat_service = ChatService(db)
    session = await chat_service.get_or_create_session(agent_id, session_id)

    return session
