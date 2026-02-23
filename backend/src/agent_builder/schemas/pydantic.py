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
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Experiment input data")


class ExperimentCreate(ExperimentBase):
    """Schema for creating an experiment."""
    agent_id: str = Field(..., description="Agent ID to run experiment with")


class ExperimentUpdate(BaseModel):
    """Schema for updating an experiment."""
    name: Optional[str] = None
    description: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class ExperimentResponse(ExperimentBase):
    """Schema for experiment response."""
    id: str
    agent_id: str
    user_id: str
    output_data: Dict[str, Any]
    status: str
    error_message: Optional[str]
    metrics: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExperimentRunRequest(BaseModel):
    """Schema for running an experiment."""
    input_data: Optional[Dict[str, Any]] = Field(None, description="Optional override input data")


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
