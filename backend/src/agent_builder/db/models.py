# -*- coding: utf-8 -*-
"""Database models."""

import json
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agent_builder.core.database import Base

# Import for type hints only - avoid circular imports
if TYPE_CHECKING:
    from agent_builder.db.models import LLMProvider, Agent, ChatSession, Experiment, AgentSkill


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
    experiences: Mapped[list["Experience"]] = relationship(
        "Experience",
        back_populates="source_agent",
        primaryjoin="Experience.source_agent_id == Agent.id",
        foreign_keys="Experience.source_agent_id",
        cascade="all, delete-orphan",
    )
    absorbed_experiences: Mapped[list["AgentExperienceAbsorption"]] = relationship(
        "AgentExperienceAbsorption",
        back_populates="agent",
        primaryjoin="AgentExperienceAbsorption.agent_id == Agent.id",
        foreign_keys="AgentExperienceAbsorption.agent_id",
        cascade="all, delete-orphan",
    )
    skills: Mapped[list["AgentSkill"]] = relationship(
        "AgentSkill",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Agent {self.name}>"


class AgentSkill(Base):
    """Agent 已加载的技能库"""
    __tablename__ = "agent_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # 技能来源
    source_type: Mapped[str] = mapped_column(String(20), default="mcp")  # "mcp" | "native" | "custom"
    source_server: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # MCP Server 名
    source_tool: Mapped[str] = mapped_column(String(100), nullable=False)  # 原始工具名

    # 技能定义（加载时快照）
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # Agent 给的名字（可自定义）
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # 封装配置
    wrapper_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 参数模板
    default_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # 统计
    call_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)

    loaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关系
    agent: Mapped["Agent"] = relationship("Agent", back_populates="skills")

    def __repr__(self):
        return f"<AgentSkill {self.name} ({self.source_type})>"


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


class Experience(Base):
    """经验记录 - 沉淀在本地数据库"""
    __tablename__ = "experiences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 归属（同用户所有 Agent 共享）
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    source_experiment_id: Mapped[Optional[str]] = mapped_column(ForeignKey("experiments.id"), nullable=True)

    # 族谱关系
    parent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("experiences.id"), nullable=True)
    evolution_chain: Mapped[list] = mapped_column(JSON, default=list)  # [root, ..., parent, self]
    generation: Mapped[int] = mapped_column(Integer, default=1)

    # 内容
    type: Mapped[str] = mapped_column(String(20))  # "success" | "failure"
    situation: Mapped[str] = mapped_column(Text)      # 情境描述
    action: Mapped[str] = mapped_column(Text)         # 采取的行动
    result: Mapped[str] = mapped_column(Text)         # 结果
    lesson: Mapped[str] = mapped_column(Text)         # 教训/经验
    solution: Mapped[str] = mapped_column(Text)       # 解决方案

    # 技能关联
    skills_used: Mapped[list] = mapped_column(JSON, default=list)
    skills_discovered: Mapped[list] = mapped_column(JSON, default=list)

    # 验证期机制
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | verified | deprecated
    applied_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)

    # 自动变异标记
    is_auto_variant: Mapped[bool] = mapped_column(Boolean, default=False)
    variant_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 向量嵌入（用于相似搜索）- 先用 JSON 存储，后续集成 sqlite-vec
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    source_agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="experiences",
        primaryjoin="Experience.source_agent_id == Agent.id",
        foreign_keys=[source_agent_id],
        viewonly=True,
    )
    source_experiment: Mapped[Optional["Experiment"]] = relationship(
        "Experiment",
        primaryjoin="Experience.source_experiment_id == Experiment.id",
        foreign_keys=[source_experiment_id],
        viewonly=True,
    )
    parent: Mapped[Optional["Experience"]] = relationship(
        "Experience",
        remote_side="Experience.id",
        foreign_keys=[parent_id],
    )

    def __repr__(self):
        return f"<Experience {self.id} ({self.type}, {self.status})>"


class AgentExperienceAbsorption(Base):
    """Agent 吸收经验的记录"""
    __tablename__ = "agent_experience_absorptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    experience_id: Mapped[str] = mapped_column(ForeignKey("experiences.id"), nullable=False)

    absorption_type: Mapped[str] = mapped_column(String(20))  # "injected" | "referenced"
    helpful_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    applied_experiment_id: Mapped[Optional[str]] = mapped_column(ForeignKey("experiments.id"), nullable=True)

    absorbed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="absorbed_experiences",
        primaryjoin="AgentExperienceAbsorption.agent_id == Agent.id",
        foreign_keys=[agent_id],
        viewonly=True,
    )
    experience: Mapped["Experience"] = relationship(
        "Experience",
        primaryjoin="AgentExperienceAbsorption.experience_id == Experience.id",
        foreign_keys=[experience_id],
        viewonly=True,
    )

    def __repr__(self):
        return f"<AgentExperienceAbsorption {self.id}>"


class MCPServerConfig(Base):
    """用户级 MCP Server 配置"""
    __tablename__ = "mcp_server_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 如 "fetch", "filesystem"
    transport: Mapped[str] = mapped_column(String(20), default="stdio")  # "stdio" | "sse"

    # stdio 配置
    command: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # 如 "uvx", "npx"
    args: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # 参数列表
    env: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)  # 环境变量

    # sse 配置
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # SSE 端点

    # 权限控制
    allowed_agents: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)  # 空列表表示所有 Agent 可用

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MCPServerConfig {self.name} ({self.transport})>"
