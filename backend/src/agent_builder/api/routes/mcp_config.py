#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Server 配置管理 API
用户管理自己的 MCP Server 配置
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agent_builder.core.database import get_db
from agent_builder.db.models import MCPServerConfig
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.services.core.mcp_client_manager import MCPClientManager
from agent_builder.services.market.skills.skill_service import SkillService


router = APIRouter(prefix="/api/mcp-servers", tags=["mcp"])


# Schema 定义
class MCPServerConfigCreate(BaseModel):
    """Schema for creating MCP server config."""
    name: str = Field(..., description="Server name, e.g., 'fetch', 'filesystem'")
    transport: str = Field(default="stdio", description="Transport type: 'stdio' | 'sse'")
    command: Optional[str] = Field(None, description="Command for stdio transport, e.g., 'uvx', 'npx'")
    args: Optional[List[str]] = Field(None, description="Arguments list for stdio transport")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    url: Optional[str] = Field(None, description="SSE endpoint URL")
    allowed_agents: Optional[List[str]] = Field(default_factory=list, description="Allowed agent IDs, empty list means all agents")


class MCPServerConfigUpdate(BaseModel):
    """Schema for updating MCP server config."""
    name: Optional[str] = None
    transport: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    url: Optional[str] = None
    allowed_agents: Optional[List[str]] = None
    is_active: Optional[bool] = None


class MCPServerConfigResponse(BaseModel):
    """Schema for MCP server config response."""
    id: str
    name: str
    transport: str
    command: Optional[str]
    args: Optional[List[str]]
    env: Optional[Dict[str, str]]
    url: Optional[str]
    allowed_agents: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MCPServerTestResponse(BaseModel):
    """Schema for MCP server test response."""
    success: bool
    message: str
    tools_count: Optional[int] = None
    tools: Optional[List[Dict[str, str]]] = None


class SkillMatchResponse(BaseModel):
    """Schema for skill match response."""
    server_name: str
    tool_name: str
    description: str
    match_score: float
    input_schema: Dict[str, Any]


class SkillExecuteRequest(BaseModel):
    """Schema for skill execution request."""
    server_name: str
    tool_name: str
    arguments: Dict[str, Any]


class SkillExecuteResponse(BaseModel):
    """Schema for skill execution response."""
    content: List[str]
    is_error: bool


# API 端点
@router.get("", response_model=List[MCPServerConfigResponse])
async def list_mcp_servers(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """列出用户的所有 MCP Server 配置"""
    result = await db.execute(
        select(MCPServerConfig).where(MCPServerConfig.user_id == user_id)
    )
    configs = result.scalars().all()
    return configs


@router.post("", response_model=MCPServerConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    config: MCPServerConfigCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """创建 MCP Server 配置"""
    # 检查名称是否已存在
    result = await db.execute(
        select(MCPServerConfig).where(
            MCPServerConfig.user_id == user_id,
            MCPServerConfig.name == config.name
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MCP server with name '{config.name}' already exists"
        )

    db_config = MCPServerConfig(
        user_id=user_id,
        name=config.name,
        transport=config.transport,
        command=config.command,
        args=config.args,
        env=config.env,
        url=config.url,
        allowed_agents=config.allowed_agents or [],
        is_active=True,
    )

    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)

    return db_config


@router.get("/{server_id}", response_model=MCPServerConfigResponse)
async def get_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """获取 MCP Server 配置详情"""
    result = await db.execute(
        select(MCPServerConfig).where(
            MCPServerConfig.id == server_id,
            MCPServerConfig.user_id == user_id
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server config not found"
        )

    return config


@router.put("/{server_id}", response_model=MCPServerConfigResponse)
async def update_mcp_server(
    server_id: str,
    config_update: MCPServerConfigUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """更新 MCP Server 配置"""
    result = await db.execute(
        select(MCPServerConfig).where(
            MCPServerConfig.id == server_id,
            MCPServerConfig.user_id == user_id
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server config not found"
        )

    # 更新字段
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return config


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """删除 MCP Server 配置"""
    result = await db.execute(
        select(MCPServerConfig).where(
            MCPServerConfig.id == server_id,
            MCPServerConfig.user_id == user_id
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server config not found"
        )

    await db.delete(config)
    await db.commit()


@router.post("/{server_id}/test", response_model=MCPServerTestResponse)
async def test_mcp_server(
    server_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """测试 MCP Server 连接"""
    result = await db.execute(
        select(MCPServerConfig).where(
            MCPServerConfig.id == server_id,
            MCPServerConfig.user_id == user_id
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server config not found"
        )

    mcp_manager = MCPClientManager()
    service = SkillDiscoveryService(db, mcp_manager)

    test_result = await service.test_server_connection(user_id, config)

    return MCPServerTestResponse(**test_result)


# 技能发现相关端点
@router.get("/discover/skills", response_model=List[SkillMatchResponse])
async def discover_skills(
    agent_id: str,
    capability_need: str,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    为指定 Agent 发现合适的技能

    - **agent_id**: Agent ID
    - **capability_need**: 能力需求描述，如 "fetch web page", "parse pdf"
    - **top_k**: 返回的最大结果数
    """
    mcp_manager = MCPClientManager()
    service = SkillDiscoveryService(db, mcp_manager)

    matches = await service.discover_skills(
        user_id=user_id,
        agent_id=agent_id,
        capability_need=capability_need,
        top_k=top_k
    )

    return [
        SkillMatchResponse(
            server_name=m.server_name,
            tool_name=m.tool_name,
            description=m.description,
            match_score=m.match_score,
            input_schema=m.input_schema
        )
        for m in matches
    ]


@router.post("/execute/skill", response_model=SkillExecuteResponse)
async def execute_skill(
    request: SkillExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """执行指定的技能"""
    from agent_builder.services.skill_service import SkillMatch

    mcp_manager = MCPClientManager()
    service = SkillService(db, mcp_manager)

    # 创建 SkillMatch 对象
    match = SkillMatch(
        server_name=request.server_name,
        tool_name=request.tool_name,
        description="",  # 不需要描述来执行
        match_score=1.0,
        input_schema={}
    )

    result = await service.execute_skill(
        user_id=user_id,
        agent_id="",  # 执行时不需要 agent_id
        match=match,
        arguments=request.arguments
    )

    return SkillExecuteResponse(**result)
