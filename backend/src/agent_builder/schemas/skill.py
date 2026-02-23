#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Skill schemas for agent skill management."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class SkillDiscoverRequest(BaseModel):
    """技能发现请求"""
    capability: str
    top_k: int = 5


class SkillMatchInfo(BaseModel):
    """技能匹配信息"""
    server_name: str
    tool_name: str
    description: str
    match_score: float
    input_schema: Dict[str, Any]


class SkillDiscoverResponse(BaseModel):
    """技能发现响应"""
    matches: List[SkillMatchInfo]


class SkillLoadRequest(BaseModel):
    """技能加载请求"""
    source_server: str
    source_tool: str
    custom_name: Optional[str] = None
    description: Optional[str] = None
    wrapper_config: Optional[Dict[str, Any]] = None


class SkillLoadResponse(BaseModel):
    """技能加载响应"""
    skill_id: str
    name: str
    description: Optional[str]
    source_server: Optional[str]
    source_tool: str
    loaded_at: datetime


class SkillExecuteRequest(BaseModel):
    """技能执行请求"""
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SkillExecuteResponse(BaseModel):
    """技能执行响应"""
    success: bool
    result: Optional[Dict[str, Any]]
    skill_used: str
    call_count: int


class AgentSkillResponse(BaseModel):
    """Agent 技能响应"""
    id: str
    name: str
    description: Optional[str]
    source_type: str
    source_server: Optional[str]
    source_tool: str
    call_count: int
    success_count: int
    loaded_at: datetime
    last_used_at: Optional[datetime]
