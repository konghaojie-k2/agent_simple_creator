# -*- coding: utf-8 -*-
"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# LLM Provider Schemas
class LLMProviderBase(BaseModel):
    """Base LLM Provider schema."""
    name: str = Field(..., description="Provider name")
    provider_type: str = Field(..., description="Provider type: deepseek, qwen, openai, custom")
    api_base: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key (will be encrypted)")
    default_model: Optional[str] = Field(None, description="Default model name")
    is_active: bool = Field(True, description="Whether provider is active")


class LLMProviderCreate(LLMProviderBase):
    """Schema for creating a LLM provider."""
    pass


class LLMProviderUpdate(BaseModel):
    """Schema for updating a LLM provider."""
    name: Optional[str] = None
    provider_type: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    is_active: Optional[bool] = None


class LLMProviderResponse(LLMProviderBase):
    """Schema for LLM provider response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Agent Schemas
class AgentBase(BaseModel):
    """Base Agent schema."""
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    provider_id: Optional[str] = Field(None, description="LLM provider ID")
    model: str = Field(..., description="Model name")
    max_steps: int = Field(50, description="Max execution steps")
    workspace_dir: Optional[str] = Field(None, description="Workspace directory")


class AgentCreate(AgentBase):
    """Schema for creating an agent."""
    pass


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    provider_id: Optional[str] = None
    model: Optional[str] = None
    max_steps: Optional[int] = None
    workspace_dir: Optional[str] = None


class AgentResponse(AgentBase):
    """Schema for agent response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ToolInfo(BaseModel):
    """Tool information schema."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")


class SkillInfo(BaseModel):
    """Skill information schema."""
    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="Skill description")
    source: str = Field(..., description="Skill source: shared, agent, experience")


class AgentDirectoryInfo(BaseModel):
    """Agent directory structure schema."""
    agent_dir: str = Field(..., description="Agent root directory")
    skills_dir: str = Field(..., description="Agent skills directory")
    experiences_dir: str = Field(..., description="Agent experiences directory")
    workspace_dir: Optional[str] = Field(None, description="Agent workspace directory (无独立工作空间，工作空间在实验中)")


class AgentDetailResponse(BaseModel):
    """Schema for detailed agent information including tools and skills."""
    # Basic info
    id: str
    name: str
    description: Optional[str]
    system_prompt: Optional[str]
    model: str
    max_steps: int
    created_at: datetime
    updated_at: Optional[datetime]

    # Tools and skills
    tools: List[ToolInfo] = Field(default_factory=list, description="Available tools")
    skills: List[SkillInfo] = Field(default_factory=list, description="Available skills")

    # Directory structure
    directories: AgentDirectoryInfo = Field(..., description="Agent directory structure")

    class Config:
        from_attributes = True


# Chat Schemas
class ChatMessage(BaseModel):
    """Chat message schema."""
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for continuing conversation")


class ChatResponse(BaseModel):
    """Schema for chat response."""
    session_id: str
    message: str
    thinking: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """Schema for chat session response."""
    id: str
    agent_id: str
    title: Optional[str]
    messages: list
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Experiment Schemas
class ExperimentBase(BaseModel):
    """Base experiment schema."""
    name: str = Field(..., description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    experiment_type: str = Field(..., description="Experiment type: skill_creation, document, problem_solving, data_analysis, custom")
    template_id: Optional[str] = Field(None, description="Template ID to use")

    # ==================== Background Info (Hybrid Mode) ====================
    # Mode 1: Lightweight - fill directly
    requirements: Optional[str] = Field(None, description="Specific requirements")
    background: Optional[str] = Field(None, description="Background information")

    # Mode 2: Reference documents/datasets/skills
    doc_ids: List[str] = Field(default_factory=list, description="Referenced document IDs")
    data_ids: List[str] = Field(default_factory=list, description="Referenced dataset IDs")
    skill_ids: List[str] = Field(default_factory=list, description="Required skill IDs")

    # ==================== Input/Output ====================
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Experiment input data")


class ExperimentCreate(ExperimentBase):
    """Schema for creating an experiment."""
    agent_id: str = Field(..., description="Agent ID to run experiment with (primary agent for collaboration)")
    collaboration_type: Optional[str] = Field(None, description="Collaboration type: sequential, parallel, debate")
    workflow_config: Dict[str, Any] = Field(default_factory=dict, description="Workflow configuration")


class ExperimentUpdate(BaseModel):
    """Schema for updating an experiment."""
    name: Optional[str] = None
    description: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class ExperimentRunRequest(BaseModel):
    """Schema for running an experiment."""
    input_data: Optional[Dict[str, Any]] = Field(None, description="Optional override input data")


# Collaboration Schemas (must be defined before ExperimentResponse)
class ExperimentParticipantBase(BaseModel):
    """Base experiment participant schema."""
    agent_id: str = Field(..., description="Agent ID")
    role: str = Field("worker", description="Participant role: leader, worker, reviewer, observer")
    join_order: int = Field(0, description="Execution order (for sequential mode)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional config")


class ExperimentParticipantCreate(ExperimentParticipantBase):
    """Schema for creating a participant."""
    pass


class ExperimentParticipantResponse(ExperimentParticipantBase):
    """Schema for participant response."""
    id: str
    experiment_id: str
    user_id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CollaborationConfig(BaseModel):
    """Collaboration experiment configuration."""
    collaboration_type: str = Field(..., description="Collaboration type: sequential, parallel, debate")
    participants: List[ExperimentParticipantCreate] = Field(..., description="List of participants")
    workflow_config: Dict[str, Any] = Field(default_factory=dict, description="Workflow configuration")
    shared_materials: List[Dict[str, Any]] = Field(default_factory=list, description="Shared materials")


class ExperimentCreateCollaboration(ExperimentBase):
    """Schema for creating a collaboration experiment."""
    participants: List[ExperimentParticipantCreate] = Field(..., description="List of participants")
    collaboration_type: str = Field("sequential", description="Collaboration type")
    workflow_config: Dict[str, Any] = Field(default_factory=dict, description="Workflow config")


class ExperimentResponse(ExperimentBase):
    """Schema for experiment response."""
    id: str
    agent_id: str
    user_id: str
    output_data: Dict[str, Any]
    status: str
    error_message: Optional[str]
    metrics: Dict[str, Any]
    collaboration_type: Optional[str] = None
    workflow_config: Dict[str, Any] = Field(default_factory=dict)
    participants: List[ExperimentParticipantResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Experiment Template Schemas
class ExperimentTemplateBase(BaseModel):
    """Base experiment template schema."""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    experiment_type: str = Field(..., description="Experiment type")
    template_config: Dict[str, Any] = Field(default_factory=dict, description="Template configuration")
    is_public: bool = Field(False, description="Whether template is public")


class ExperimentTemplateCreate(ExperimentTemplateBase):
    """Schema for creating a template."""
    pass


class ExperimentTemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = None
    description: Optional[str] = None
    template_config: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class ExperimentTemplateResponse(ExperimentTemplateBase):
    """Schema for template response."""
    id: str
    user_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Experiment Experience Schemas
class ExperimentExperienceBase(BaseModel):
    """Base experiment experience schema."""
    summary: str = Field(..., description="Experience summary")
    lessons_learned: Optional[str] = Field(None, description="Lessons learned")
    improvements: Optional[str] = Field(None, description="Improvement suggestions")
    related_experiments: List[str] = Field(default_factory=list, description="Related experiment IDs")


class ExperimentExperienceCreate(ExperimentExperienceBase):
    """Schema for creating an experience."""
    experiment_id: str = Field(..., description="Original experiment ID")


class ExperimentExperienceResponse(ExperimentExperienceBase):
    """Schema for experience response."""
    id: str
    experiment_id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Document Schemas ====================

class DocumentBase(BaseModel):
    """Base document schema."""
    name: str = Field(..., description="Document name")
    description: Optional[str] = Field(None, description="Document description")
    doc_type: str = Field("general", description="Document type: general, requirement, reference, template")
    content: Optional[str] = Field(None, description="Document content (for small content)")
    file_path: Optional[str] = Field(None, description="File path (for large content)")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    category: Optional[str] = Field(None, description="Document category")
    is_public: bool = Field(False, description="Is public")


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    name: Optional[str] = None
    description: Optional[str] = None
    doc_type: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Dataset Schemas
class DatasetBase(BaseModel):
    """Base dataset schema."""
    name: str = Field(..., description="Dataset name")
    description: Optional[str] = Field(None, description="Dataset description")
    dataset_type: str = Field("json", description="Dataset type: json, csv, text, parquet")
    data_schema: Dict[str, Any] = Field(default_factory=dict, description="Data schema (JSON Schema)", alias="schema")
    file_path: Optional[str] = Field(None, description="File path (for large datasets)")
    row_count: int = Field(0, description="Number of rows")
    tags: List[str] = Field(default_factory=list, description="Dataset tags")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    category: Optional[str] = Field(None, description="Dataset category")
    is_public: bool = Field(False, description="Is public")

    class Config:
        populate_by_name = True


class DatasetCreate(DatasetBase):
    """Schema for creating a dataset."""
    pass


class DatasetUpdate(BaseModel):
    """Schema for updating a dataset."""
    name: Optional[str] = None
    description: Optional[str] = None
    dataset_type: Optional[str] = None
    data_schema: Optional[Dict[str, Any]] = Field(None, alias="schema")
    file_path: Optional[str] = None
    row_count: Optional[int] = None
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None

    class Config:
        populate_by_name = True


class DatasetResponse(DatasetBase):
    """Schema for dataset response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Skill Schemas
class SkillBase(BaseModel):
    """Base skill schema."""
    name: str = Field(..., description="Skill name")
    description: Optional[str] = Field(None, description="Skill description")
    category: str = Field("custom", description="Skill category: tool, template, prompt, custom")
    content: Optional[str] = Field(None, description="Skill content (prompt, template, etc.)")
    content_type: str = Field("text", description="Content type: text, json, yaml")
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, description="Parameters schema (JSON Schema)")
    tags: List[str] = Field(default_factory=list, description="Skill tags")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    is_public: bool = Field(False, description="Is public")


class SkillCreate(SkillBase):
    """Schema for creating a skill."""
    pass


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class SkillResponse(SkillBase):
    """Schema for skill response."""
    id: str
    user_id: str
    usage_count: int = Field(0, description="Usage count")
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
