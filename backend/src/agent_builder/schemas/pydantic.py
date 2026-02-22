# -*- coding: utf-8 -*-
"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
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
