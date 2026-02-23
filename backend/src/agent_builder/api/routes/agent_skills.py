# -*- coding: utf-8 -*-
"""API routes for agent skills."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.skill import (
    SkillDiscoverRequest,
    SkillDiscoverResponse,
    SkillMatchInfo,
    SkillLoadRequest,
    SkillLoadResponse,
    SkillExecuteRequest,
    SkillExecuteResponse,
    AgentSkillResponse,
)
from agent_builder.services.skill_service import SkillService
from agent_builder.services.mcp_client_manager import MCPClientManager


router = APIRouter(prefix="/api/agents/{agent_id}/skills", tags=["agent-skills"])


def _get_skill_service(db: AsyncSession) -> SkillService:
    """Get skill service instance."""
    mcp_manager = MCPClientManager()
    return SkillService(db, mcp_manager)


@router.get("/discover", response_model=SkillDiscoverResponse)
async def discover_skills(
    agent_id: str,
    capability: str,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    发现技能 - 在用户的 MCP Servers 中搜索匹配的工具

    Args:
        agent_id: Agent ID
        capability: 需要的能力描述（如 "获取网页内容"）
        top_k: 返回最多几个结果（默认 5）

    Returns:
        匹配的技能列表
    """
    service = _get_skill_service(db)
    matches = await service.discover_skills(user_id, agent_id, capability, top_k)

    return SkillDiscoverResponse(
        matches=[
            SkillMatchInfo(
                server_name=m.server_name,
                tool_name=m.tool_name,
                description=m.description,
                match_score=m.match_score,
                input_schema=m.input_schema,
            )
            for m in matches
        ]
    )


@router.post("", response_model=SkillLoadResponse, status_code=status.HTTP_201_CREATED)
async def load_skill(
    agent_id: str,
    request: SkillLoadRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    加载技能 - 将 MCP 工具安装到 Agent 技能库

    Args:
        agent_id: Agent ID
        request:
            - source_server: MCP Server 名称
            - source_tool: 原始工具名
            - custom_name: 自定义技能名（可选）
            - description: 自定义描述（可选）
            - wrapper_config: 封装配置（可选）

    Returns:
        加载成功的技能信息
    """
    service = _get_skill_service(db)
    skill = await service.load_skill(
        agent_id=agent_id,
        user_id=user_id,
        source_server=request.source_server,
        source_tool=request.source_tool,
        custom_name=request.custom_name,
        description=request.description,
        wrapper_config=request.wrapper_config,
    )

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to load skill. Please check server and tool names.",
        )

    return SkillLoadResponse(
        skill_id=skill.id,
        name=skill.name,
        description=skill.description,
        source_server=skill.source_server,
        source_tool=skill.source_tool,
        loaded_at=skill.loaded_at,
    )


@router.get("", response_model=List[AgentSkillResponse])
async def list_agent_skills(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    列出技能 - 获取 Agent 技能库中的所有技能

    Returns:
        Agent 已加载的技能列表（按调用次数排序）
    """
    service = _get_skill_service(db)
    skills = await service.list_agent_skills(agent_id, user_id)

    return [
        AgentSkillResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            source_type=s.source_type,
            source_server=s.source_server,
            source_tool=s.source_tool,
            call_count=s.call_count,
            success_count=s.success_count,
            loaded_at=s.loaded_at,
            last_used_at=s.last_used_at,
        )
        for s in skills
    ]


@router.post("/{skill_name}/execute", response_model=SkillExecuteResponse)
async def execute_skill(
    agent_id: str,
    skill_name: str,
    request: SkillExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    执行技能 - 从 Agent 技能库中调用技能

    Args:
        agent_id: Agent ID
        skill_name: 技能名称
        request:
            - parameters: 调用参数

    Returns:
        执行结果
    """
    service = _get_skill_service(db)
    result = await service.execute_skill(
        agent_id=agent_id,
        user_id=user_id,
        skill_name=skill_name,
        parameters=request.parameters,
    )

    if not result.get("success", False) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    return SkillExecuteResponse(
        success=result.get("success", False),
        result=result.get("result"),
        skill_used=result.get("skill_used", skill_name),
        call_count=result.get("call_count", 0),
    )


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unload_skill(
    agent_id: str,
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    卸载技能 - 从 Agent 技能库中移除技能

    Args:
        agent_id: Agent ID
        skill_id: 技能 ID

    Returns:
        204 No Content on success
    """
    service = _get_skill_service(db)
    success = await service.unload_skill(agent_id, user_id, skill_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )
