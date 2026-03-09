# -*- coding: utf-8 -*-
"""API routes for experience system."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from agent_builder.core.database import get_db
from agent_builder.db.models import Agent
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.experience import (
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
    ExperienceApplyRequest,
    ExperienceApplyResponse,
    ExperienceMutateRequest,
    ExperienceMutateResponse,
    ExperienceSearchRequest,
    ExperienceSearchResponse,
    AgentAbsorbExperienceRequest,
    AgentExperienceAbsorptionResponse,
    AgentAbsorbedExperiencesResponse,
)
from agent_builder.services.core.experience_service import ExperienceService


router = APIRouter(prefix="/api/experiences", tags=["experiences"])
agents_router = APIRouter(prefix="/api/agents", tags=["agents"])


# ==================== Experience Routes ====================

@router.post("", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
async def create_experience(
    experience_data: ExperienceCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """创建新经验（初始状态为 draft）"""
    # 验证 source_agent_id 属于当前用户
    agent_result = await db.execute(
        select(Agent).where(
            Agent.id == experience_data.source_agent_id,
            Agent.user_id == user_id,
        )
    )
    if not agent_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent not found or access denied",
        )

    service = ExperienceService(db)

    # 添加 user_id 到数据
    data = experience_data.model_dump()
    data["user_id"] = user_id

    experience = await service.create_experience(data)
    return experience


@router.get("", response_model=List[ExperienceResponse])
async def get_experiences(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by status: draft | verified | deprecated"),
    exp_type: Optional[str] = Query(None, description="Filter by type: success | failure"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """获取经验列表"""
    service = ExperienceService(db)
    experiences = await service.list_experiences(
        user_id=user_id,
        agent_id=agent_id,
        status=status,
        exp_type=exp_type,
    )
    return experiences


@router.get("/{experience_id}", response_model=ExperienceResponse)
async def get_experience(
    experience_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """获取经验详情"""
    service = ExperienceService(db)
    experience = await service.get_experience(experience_id, user_id)

    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found",
        )

    return experience


@router.put("/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    experience_id: str,
    experience_data: ExperienceUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """更新经验"""
    service = ExperienceService(db)
    experience = await service.update_experience(
        exp_id=experience_id,
        user_id=user_id,
        data=experience_data.model_dump(exclude_unset=True),
    )

    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found",
        )

    return experience


@router.delete("/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(
    experience_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """删除经验"""
    service = ExperienceService(db)
    success = await service.delete_experience(experience_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found",
        )


@router.post("/{experience_id}/apply", response_model=ExperienceApplyResponse)
async def apply_experience(
    experience_id: str,
    apply_data: ExperienceApplyRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    应用经验后更新统计
    验证期检查：3次应用，2次成功 → verified
    """
    service = ExperienceService(db)

    # 验证经验存在且属于当前用户
    experience = await service.get_experience(experience_id, user_id)
    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found",
        )

    # 应用经验
    updated = await service.apply_experience(experience_id, user_id, apply_data.success)

    # 生成状态变更消息
    message = f"Applied successfully. Current status: {updated.status}"
    if updated.status == "verified":
        message = "Experience has been verified after 3 applications with 2+ successes!"
    elif updated.status == "deprecated":
        message = "Experience has been deprecated after 3 applications with less than 2 successes."

    return ExperienceApplyResponse(
        id=updated.id,
        status=updated.status,
        applied_count=updated.applied_count,
        success_count=updated.success_count,
        message=message,
    )


@router.post("/{experience_id}/mutate", response_model=ExperienceMutateResponse)
async def mutate_experience(
    experience_id: str,
    mutate_data: ExperienceMutateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """自动变异产生新经验"""
    service = ExperienceService(db)

    # 验证经验存在且属于当前用户
    experience = await service.get_experience(experience_id, user_id)
    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found",
        )

    # 创建变异经验
    new_experience = await service.mutate_experience(
        original_id=experience_id,
        user_id=user_id,
        agent_id=experience.source_agent_id,
        improved_solution=mutate_data.improved_solution,
        variant_reason=mutate_data.variant_reason,
    )

    return ExperienceMutateResponse(
        original_id=experience_id,
        new_experience=new_experience,
        message=f"New variant created from generation {experience.generation} to generation {new_experience.generation}",
    )


@router.post("/search", response_model=ExperienceSearchResponse)
async def search_experiences(
    search_data: ExperienceSearchRequest,
    agent_id: str = Query(..., description="Agent ID to search for"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """
    相似性搜索经验：
    - 同用户的 verified 经验
    - 当前 Agent 自己的 draft 经验
    """
    service = ExperienceService(db)
    results = await service.search_relevant_experiences(
        user_id=user_id,
        agent_id=agent_id,
        query=search_data.query,
        top_k=search_data.top_k,
    )

    return ExperienceSearchResponse(
        results=results,
        query=search_data.query,
    )


# ==================== Agent Experience Absorption Routes ====================

@agents_router.post("/{agent_id}/absorb-experience", response_model=AgentExperienceAbsorptionResponse)
async def agent_absorb_experience(
    agent_id: str,
    absorb_data: AgentAbsorbExperienceRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Agent 吸收经验"""
    service = ExperienceService(db)

    # 验证经验存在且当前用户有权限访问
    experience = await service.get_experience(absorb_data.experience_id, user_id)
    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found",
        )

    # 创建吸收记录
    absorption = await service.absorb_experience(
        agent_id=agent_id,
        experience_id=absorb_data.experience_id,
        user_id=user_id,
        absorption_type=absorb_data.absorption_type,
        helpful_rating=absorb_data.helpful_rating,
        applied_experiment_id=absorb_data.applied_experiment_id,
    )

    if not absorption:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent or experience not found or access denied",
        )

    return absorption


@agents_router.get("/{agent_id}/absorbed-experiences", response_model=AgentAbsorbedExperiencesResponse)
async def get_agent_absorbed_experiences(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """获取 Agent 吸收的所有经验"""
    service = ExperienceService(db)
    absorptions = await service.get_agent_absorptions(agent_id, user_id)

    return AgentAbsorbedExperiencesResponse(
        agent_id=agent_id,
        absorptions=absorptions,
        total=len(absorptions),
    )
