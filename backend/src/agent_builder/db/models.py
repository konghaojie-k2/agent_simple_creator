# -*- coding: utf-8 -*-
"""Database models."""

import json
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agent_builder.core.database import Base

# Import for type hints only - avoid circular imports
if TYPE_CHECKING:
    from agent_builder.db.models import LLMProvider, Agent, ChatSession, Experiment


class ExperimentType(PyEnum):
    """Experiment type enumeration."""
    SKILL_CREATION = "skill_creation"
    DOCUMENT = "document"
    PROBLEM_SOLVING = "problem_solving"
    DATA_ANALYSIS = "data_analysis"
    CUSTOM = "custom"


class ExperimentStatus(PyEnum):
    """Experiment status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


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

    # Relationships - using primaryjoin since no FK constraint exists
    agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        back_populates="provider",
        primaryjoin="LLMProvider.id == Agent.provider_id",
        foreign_keys="Agent.provider_id",
    )

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

    # Relationships - using primaryjoin since no FK constraint exists
    provider: Mapped[Optional["LLMProvider"]] = relationship(
        "LLMProvider",
        back_populates="agents",
        primaryjoin="Agent.provider_id == LLMProvider.id",
        foreign_keys=[provider_id],
        viewonly=True,
    )
    sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="agent",
        primaryjoin="ChatSession.agent_id == Agent.id",
        foreign_keys="ChatSession.agent_id",
        cascade="all, delete-orphan",
    )
    experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment",
        back_populates="agent",
        primaryjoin="Experiment.agent_id == Agent.id",
        foreign_keys="Experiment.agent_id",
        cascade="all, delete-orphan",
    )

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

    # Relationships - using primaryjoin since no FK constraint exists
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="sessions",
        primaryjoin="ChatSession.agent_id == Agent.id",
        foreign_keys=[agent_id],
        viewonly=True,
    )

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


class Experiment(Base):
    """Experiment model for running agent experiments."""

    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    experiment_type: Mapped[str] = mapped_column(String(50), nullable=False, default=ExperimentType.DOCUMENT.value)
    template_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    input_data: Mapped[dict] = mapped_column(JSON, default=dict)
    output_data: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ExperimentStatus.PENDING.value)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, onupdate=datetime.utcnow)

    # Relationships - using primaryjoin since no FK constraint exists
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="experiments",
        primaryjoin="Experiment.agent_id == Agent.id",
        foreign_keys=[agent_id],
        viewonly=True,
    )

    def __repr__(self):
        return f"<Experiment {self.name} ({self.status})>"


class ExperimentTemplate(Base):
    """Experiment template model."""

    __tablename__ = "experiment_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    experiment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    template_config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ExperimentTemplate {self.name} ({self.experiment_type})>"


class ExperimentExperience(Base):
    """Experiment experience model for storing lessons learned."""

    __tablename__ = "experiment_experiences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    improvements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_experiments: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ExperimentExperience {self.id}>"
