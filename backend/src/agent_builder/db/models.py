# -*- coding: utf-8 -*-
"""Database models."""

import json
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agent_builder.core.database import Base


class LLMProvider(Base):
    """LLM Provider configuration model."""

    __tablename__ = "llm_providers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)  # Reference to myauth user
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)  # deepseek, qwen, openai, custom
    api_base: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key: Mapped[str] = mapped_column(String(500), nullable=False)  # Encrypted
    default_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)

    # Relationships
    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="provider")

    def __repr__(self):
        return f"<LLMProvider {self.name} ({self.provider_type})>"


class Agent(Base):
    """Agent configuration model."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)  # Reference to myauth user
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # No FK constraint
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    max_steps: Mapped[int] = mapped_column(Integer, default=50)
    workspace_dir: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, onupdate=datetime.utcnow)

    # Relationships
    provider: Mapped[Optional["LLMProvider"]] = relationship("LLMProvider", back_populates="agents")
    sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Agent {self.name}>"


class ChatSession(Base):
    """Chat session model."""

    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), nullable=False)  # No FK constraint
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    messages: Mapped[list] = mapped_column(JSON, default=list)  # [{"role": "user", "content": "..."}]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, onupdate=datetime.utcnow)

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="sessions")

    def __repr__(self):
        return f"<ChatSession {self.id}>"

    def get_messages(self) -> list[dict]:
        """Get messages as list."""
        if isinstance(self.messages, str):
            return json.loads(self.messages)
        return self.messages or []

    def add_message(self, role: str, content: str):
        """Add a message to the session."""
        messages = self.get_messages()
        messages.append({"role": role, "content": content})
        self.messages = messages
