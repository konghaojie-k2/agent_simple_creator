#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skills API - 技能市场 API

提供技能的 CRUD 接口：
- 创建/更新/删除技能
- 列出技能
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.pydantic import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
)
from agent_builder.services.skill_market_service import SkillService

router = APIRouter(prefix="/api/market/skills", tags=["skills"])


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """创建技能"""
    service = SkillService(db)
    skill = await service.create_skill(
        user_id=user_id,
        name=skill_data.name,
        category=skill_data.category,
        description=skill_data.description,
        content=skill_data.content,
        content_type=skill_data.content_type,
        parameters_schema=skill_data.parameters_schema,
        tags=skill_data.tags,
        extra_metadata=skill_data.extra_metadata,
        is_public=skill_data.is_public,
    )
    return skill


@router.get("", response_model=List[SkillResponse])
async def list_skills(
    category: Optional[str] = Query(None, description="Filter by skill category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """列出用户技能"""
    service = SkillService(db)

    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]

    skills = await service.list_skills(
        user_id=user_id,
        category=category,
        tags=tag_list,
        limit=limit,
        offset=offset,
    )
    return skills


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """获取技能详情"""
    service = SkillService(db)
    skill = await service.get_skill(skill_id, user_id)

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    skill_data: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """更新技能"""
    service = SkillService(db)
    skill = await service.update_skill(
        skill_id=skill_id,
        user_id=user_id,
        name=skill_data.name,
        description=skill_data.description,
        category=skill_data.category,
        content=skill_data.content,
        content_type=skill_data.content_type,
        parameters_schema=skill_data.parameters_schema,
        tags=skill_data.tags,
        extra_metadata=skill_data.extra_metadata,
        is_public=skill_data.is_public,
    )

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """删除技能"""
    service = SkillService(db)
    success = await service.delete_skill(skill_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    return None
