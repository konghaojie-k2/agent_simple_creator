# -*- coding: utf-8 -*-
"""Agent service for managing agents and chat sessions."""

import json
import os
import uuid
from pathlib import Path
from typing import AsyncGenerator, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.config import settings
from agent_builder.core.security import decrypt_api_key, encrypt_api_key
from agent_builder.db.models import Agent, ChatSession, LLMProvider
from agent_builder.schemas.pydantic import AgentCreate, AgentUpdate, ChatMessage, LLMProviderCreate, LLMProviderUpdate
from agent_builder.services.llm_service import LLMClient


class AgentService:
    """Service for managing agents."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_provider(
        self,
        user_id: str,
        provider_data: LLMProviderCreate,
    ) -> LLMProvider:
        """Create a new LLM provider."""
        # Encrypt API key
        encrypted_key = encrypt_api_key(provider_data.api_key)

        provider = LLMProvider(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=provider_data.name,
            provider_type=provider_data.provider_type,
            api_base=provider_data.api_base,
            api_key=encrypted_key,
            default_model=provider_data.default_model,
            is_active=provider_data.is_active,
        )

        self.db.add(provider)
        await self.db.flush()
        await self.db.refresh(provider)

        return provider

    async def get_providers(self, user_id: str) -> list[LLMProvider]:
        """Get all providers for a user."""
        result = await self.db.execute(
            select(LLMProvider).where(LLMProvider.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_provider(self, provider_id: str, user_id: str) -> Optional[LLMProvider]:
        """Get a specific provider."""
        result = await self.db.execute(
            select(LLMProvider).where(
                LLMProvider.id == provider_id,
                LLMProvider.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_provider(
        self,
        provider_id: str,
        user_id: str,
        provider_data: LLMProviderUpdate,
    ) -> Optional[LLMProvider]:
        """Update a provider."""
        provider = await self.get_provider(provider_id, user_id)
        if not provider:
            return None

        update_data = provider_data.model_dump(exclude_unset=True)

        # Encrypt new API key if provided
        if "api_key" in update_data:
            update_data["api_key"] = encrypt_api_key(update_data["api_key"])

        for key, value in update_data.items():
            setattr(provider, key, value)

        await self.db.flush()
        await self.db.refresh(provider)

        return provider

    async def delete_provider(self, provider_id: str, user_id: str) -> bool:
        """Delete a provider."""
        provider = await self.get_provider(provider_id, user_id)
        if not provider:
            return False

        await self.db.delete(provider)
        await self.db.flush()

        return True

    async def create_agent(
        self,
        user_id: str,
        agent_data: AgentCreate,
    ) -> Agent:
        """Create a new agent."""
        # Generate workspace directory
        workspace_dir = os.path.join(
            settings.WORKSPACES_DIR,
            user_id,
            str(uuid.uuid4()),
        )

        # Ensure workspace directory exists
        Path(workspace_dir).mkdir(parents=True, exist_ok=True)

        agent = Agent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=agent_data.name,
            description=agent_data.description,
            system_prompt=agent_data.system_prompt,
            provider_id=agent_data.provider_id,
            model=agent_data.model,
            max_steps=agent_data.max_steps,
            workspace_dir=workspace_dir,
        )

        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)

        return agent

    async def get_agents(self, user_id: str) -> list[Agent]:
        """Get all agents for a user."""
        result = await self.db.execute(
            select(Agent).where(Agent.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_agent(self, agent_id: str, user_id: str) -> Optional[Agent]:
        """Get a specific agent."""
        result = await self.db.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_agent(
        self,
        agent_id: str,
        user_id: str,
        agent_data: AgentUpdate,
    ) -> Optional[Agent]:
        """Update an agent."""
        agent = await self.get_agent(agent_id, user_id)
        if not agent:
            return None

        update_data = agent_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(agent, key, value)

        await self.db.flush()
        await self.db.refresh(agent)

        return agent

    async def delete_agent(self, agent_id: str, user_id: str) -> bool:
        """Delete an agent."""
        agent = await self.get_agent(agent_id, user_id)
        if not agent:
            return False

        # Delete workspace directory
        if agent.workspace_dir and os.path.exists(agent.workspace_dir):
            import shutil
            shutil.rmtree(agent.workspace_dir)

        await self.db.delete(agent)
        await self.db.flush()

        return True


class ChatService:
    """Service for managing chat sessions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_session(
        self,
        agent_id: str,
        session_id: Optional[str] = None,
    ) -> ChatSession:
        """Get or create a chat session."""
        if session_id:
            result = await self.db.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.agent_id == agent_id,
                )
            )
            session = result.scalar_one_or_none()
            if session:
                return session

        # Create new session
        session = ChatSession(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            messages=[],
        )

        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def get_sessions(self, agent_id: str) -> list[ChatSession]:
        """Get all sessions for an agent."""
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.agent_id == agent_id)
            .order_by(ChatSession.updated_at.desc())
        )
        return list(result.scalars().all())

    async def chat(
        self,
        agent: Agent,
        provider: LLMProvider,
        message: str,
        session: ChatSession,
    ) -> AsyncGenerator[str, None]:
        """Process a chat message and stream the response.

        Args:
            agent: The agent
            provider: The LLM provider
            message: User message
            session: Chat session

        Yields:
            Streamed response chunks
        """
        # Decrypt API key
        api_key = decrypt_api_key(provider.api_key)

        # Create LLM client
        llm_client = LLMClient(
            api_key=api_key,
            api_base=provider.api_base,
            model=agent.model,
        )

        try:
            # Build messages
            messages = session.get_messages() if session.messages else []

            # Add system prompt
            system_prompt = agent.system_prompt or "You are a helpful AI assistant."
            messages.insert(0, {"role": "system", "content": system_prompt})

            # Add user message
            messages.append({"role": "user", "content": message})

            # Stream response
            async for chunk in llm_client.generate_stream(messages):
                yield chunk

            # Save messages to session
            messages.append({"role": "assistant", "content": "[Response saved]"})

            session.messages = messages

            # Update session title if first message
            if not session.title:
                session.title = message[:50] + ("..." if len(message) > 50 else "")

            await self.db.flush()

        finally:
            await llm_client.close()
