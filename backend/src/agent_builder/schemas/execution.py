#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验执行相关的 Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SENSE = "sense"      # 感知阶段
    PLAN = "plan"        # 决策阶段
    ACT = "act"          # 执行阶段
    REFLECT = "reflect"  # 反思阶段
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStep(BaseModel):
    """执行步骤"""
    step_number: int
    action: str           # 动作类型
    status: str           # "success" | "failed" | "skipped"
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    timestamp: datetime


class ExecutionContext(BaseModel):
    """执行上下文"""
    experiment_id: str
    agent_id: str
    user_id: str

    # 相关经验
    relevant_experiences: List[Dict[str, Any]] = []

    # 执行计划
    plan: Optional[Dict[str, Any]] = None

    # 执行历史
    steps: List[ExecutionStep] = []

    # 发现的技能
    discovered_skills: List[Dict[str, Any]] = []


class ExecutionResult(BaseModel):
    """执行结果"""
    success: bool
    status: ExecutionStatus
    output: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: int
    steps_executed: int
    experience_id: Optional[str] = None  # 沉淀的经验ID


class PlanStep(BaseModel):
    """计划中的单个步骤"""
    step_id: str
    description: str
    action_type: str  # "use_tool", "call_llm", "search_skill"
    parameters: Dict[str, Any]
    expected_outcome: Optional[str] = None
