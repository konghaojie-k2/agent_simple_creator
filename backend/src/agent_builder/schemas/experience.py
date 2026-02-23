# -*- coding: utf-8 -*-
"""Pydantic schemas for experience system."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== Experience Schemas ====================

class ExperienceBase(BaseModel):
    """Base experience schema."""
    type: str = Field(..., description="Experience type: success | failure")
    situation: str = Field(..., description="情境描述")
    action: str = Field(..., description="采取的行动")
    result: str = Field(..., description="结果")
    lesson: str = Field(..., description="教训/经验")
    solution: str = Field(..., description="解决方案")
    skills_used: List[str] = Field(default_factory=list, description="使用的技能")
    skills_discovered: List[str] = Field(default_factory=list, description="发现的技能")


class ExperienceCreate(BaseModel):
    """Schema for creating an experience."""
    source_agent_id: str = Field(..., description="Source agent ID")
    source_experiment_id: Optional[str] = Field(None, description="Source experiment ID")
    type: str = Field(..., description="Experience type: success | failure")
    situation: str = Field(..., description="情境描述")
    action: str = Field(..., description="采取的行动")
    result: str = Field(..., description="结果")
    lesson: str = Field(..., description="教训/经验")
    solution: str = Field(..., description="解决方案")
    skills_used: List[str] = Field(default_factory=list, description="使用的技能")
    skills_discovered: List[str] = Field(default_factory=list, description="发现的技能")
    embedding: Optional[str] = Field(None, description="向量嵌入（可选）")


class ExperienceUpdate(BaseModel):
    """Schema for updating an experience."""
    situation: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    lesson: Optional[str] = None
    solution: Optional[str] = None
    skills_used: Optional[List[str]] = None
    skills_discovered: Optional[List[str]] = None
    embedding: Optional[str] = None


class ExperienceResponse(BaseModel):
    """Schema for experience response."""
    id: str
    user_id: str
    source_agent_id: str
    source_experiment_id: Optional[str]
    parent_id: Optional[str]
    evolution_chain: List[str]
    generation: int
    type: str
    situation: str
    action: str
    result: str
    lesson: str
    solution: str
    skills_used: List[str]
    skills_discovered: List[str]
    status: str
    applied_count: int
    success_count: int
    is_auto_variant: bool
    variant_reason: Optional[str]
    embedding: Optional[str]
    created_at: datetime
    last_applied_at: Optional[datetime]

    class Config:
        from_attributes = True


class ExperienceListResponse(BaseModel):
    """Schema for experience list response."""
    items: List[ExperienceResponse]
    total: int


# ==================== Experience Apply Schema ====================

class ExperienceApplyRequest(BaseModel):
    """Schema for applying an experience."""
    success: bool = Field(..., description="Whether the application was successful")


class ExperienceApplyResponse(BaseModel):
    """Schema for experience apply response."""
    id: str
    status: str
    applied_count: int
    success_count: int
    message: str


# ==================== Experience Mutate Schema ====================

class ExperienceMutateRequest(BaseModel):
    """Schema for mutating an experience."""
    improved_solution: str = Field(..., description="改进后的解决方案")
    variant_reason: str = Field(..., description="变异原因")


class ExperienceMutateResponse(BaseModel):
    """Schema for experience mutate response."""
    original_id: str
    new_experience: ExperienceResponse
    message: str


# ==================== Experience Search Schema ====================

class ExperienceSearchRequest(BaseModel):
    """Schema for searching experiences."""
    query: str = Field(..., description="搜索关键词")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")


class ExperienceSearchResponse(BaseModel):
    """Schema for experience search response."""
    results: List[ExperienceResponse]
    query: str


# ==================== Agent Experience Absorption Schemas ====================

class AgentAbsorbExperienceRequest(BaseModel):
    """Schema for agent absorbing an experience."""
    experience_id: str = Field(..., description="经验ID")
    absorption_type: str = Field("referenced", description="吸收类型: injected | referenced")
    helpful_rating: Optional[int] = Field(None, ge=1, le=5, description="有用程度评分 1-5")
    applied_experiment_id: Optional[str] = Field(None, description="应用该经验的实验ID")


class AgentExperienceAbsorptionResponse(BaseModel):
    """Schema for agent experience absorption response."""
    id: str
    agent_id: str
    experience_id: str
    absorption_type: str
    helpful_rating: Optional[int]
    applied_experiment_id: Optional[str]
    absorbed_at: datetime

    class Config:
        from_attributes = True


class AgentAbsorbedExperiencesResponse(BaseModel):
    """Schema for agent absorbed experiences list."""
    agent_id: str
    absorptions: List[AgentExperienceAbsorptionResponse]
    total: int
