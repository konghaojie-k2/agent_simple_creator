# -*- coding: utf-8 -*-
"""API routes for experiments, templates, and experiences."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agent_builder.core.database import get_db
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.db.models import Experiment
from agent_builder.schemas.pydantic import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentUpdate,
    ExperimentRunRequest,
    ExperimentTemplateCreate,
    ExperimentTemplateResponse,
    ExperimentTemplateUpdate,
    ExperimentExperienceCreate,
    ExperimentExperienceResponse,
)
from agent_builder.schemas.execution import ExecutionResult
from agent_builder.services.experiment_service import (
    ExperimentService,
    ExperimentTemplateService,
    ExperimentExperienceService,
)


router = APIRouter(prefix="/api/experiments", tags=["experiments"])


# ==================== Experiment Routes ====================

@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    experiment_data: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create a new experiment."""
    service = ExperimentService(db)
    experiment = await service.create(user_id, experiment_data)
    return experiment


@router.get("", response_model=List[ExperimentResponse])
async def get_experiments(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    experiment_type: Optional[str] = Query(None, description="Filter by experiment type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get experiments for the current user."""
    service = ExperimentService(db)
    experiments = await service.get_list(user_id, agent_id, experiment_type, status)
    return experiments


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get a specific experiment."""
    service = ExperimentService(db)
    experiment = await service.get(experiment_id, user_id)

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    return experiment


@router.put("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: str,
    experiment_data: ExperimentUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Update an experiment."""
    service = ExperimentService(db)
    experiment = await service.update(experiment_id, user_id, experiment_data)

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    return experiment


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Delete an experiment."""
    service = ExperimentService(db)
    success = await service.delete(experiment_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )


@router.post("/{experiment_id}/run", response_model=ExperimentResponse)
async def run_experiment(
    experiment_id: str,
    run_request: ExperimentRunRequest = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """运行实验（执行完整的 Sense-Plan-Act-Reflect 循环）"""
    from agent_builder.services.experiment_engine import ExperimentEngine
    from agent_builder.services.experience_service import ExperienceService
    from agent_builder.services.skill_service import SkillService
    from agent_builder.services.mcp_client_manager import MCPClientManager

    # 获取实验
    result = await db.execute(
        select(Experiment).where(
            Experiment.id == experiment_id,
            Experiment.user_id == user_id
        )
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.status == "running":
        raise HTTPException(status_code=400, detail="Experiment is already running")

    # 更新输入数据（如果提供）
    if run_request and run_request.input_data:
        experiment.input_data = run_request.input_data
        await db.flush()

    # 初始化服务
    experience_service = ExperienceService(db)
    mcp_manager = MCPClientManager()
    skill_discovery = SkillService(db, mcp_manager)

    # 创建执行引擎（传入 mcp_manager 用于技能管理）
    engine = ExperimentEngine(db, experience_service, skill_discovery, mcp_manager)

    # 运行实验
    execution_result = await engine.run_experiment(experiment_id, user_id)

    # 刷新实验数据
    await db.refresh(experiment)

    return experiment


@router.get("/{experiment_id}/execution", response_model=ExecutionResult)
async def get_execution_result(
    experiment_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """获取实验执行结果"""
    result = await db.execute(
        select(Experiment).where(
            Experiment.id == experiment_id,
            Experiment.user_id == user_id
        )
    )
    experiment = result.scalar_one_or_none()

    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return ExecutionResult(
        success=experiment.status == "success",
        status=experiment.status,
        output=experiment.output_data.get("result", {}).get("content") if experiment.output_data else None,
        error_message=experiment.error_message,
        duration_ms=0,  # 可以从 output_data 中计算
        steps_executed=len(experiment.output_data.get("steps", [])) if experiment.output_data else 0,
        experience_id=experiment.output_data.get("experience_id") if experiment.output_data else None
    )


# ==================== Template Routes ====================

templates_router = APIRouter(prefix="/api/templates", tags=["templates"])


@templates_router.post("", response_model=ExperimentTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: ExperimentTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create a new experiment template."""
    service = ExperimentTemplateService(db)
    template = await service.create(user_id, template_data)
    return template


@templates_router.get("", response_model=List[ExperimentTemplateResponse])
async def get_templates(
    experiment_type: Optional[str] = Query(None, description="Filter by experiment type"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get templates."""
    service = ExperimentTemplateService(db)
    templates = await service.get_list(user_id, experiment_type, is_public)
    return templates


@templates_router.get("/{template_id}", response_model=ExperimentTemplateResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific template."""
    service = ExperimentTemplateService(db)
    template = await service.get(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return template


@templates_router.put("/{template_id}", response_model=ExperimentTemplateResponse)
async def update_template(
    template_id: str,
    template_data: ExperimentTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Update a template."""
    service = ExperimentTemplateService(db)
    template = await service.update(template_id, user_id, template_data)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or not authorized",
        )

    return template


@templates_router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Delete a template."""
    service = ExperimentTemplateService(db)
    success = await service.delete(template_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or not authorized",
        )


# ==================== Experience Routes ====================

experiences_router = APIRouter(prefix="/api/experiences", tags=["experiences"])


@experiences_router.post("", response_model=ExperimentExperienceResponse, status_code=status.HTTP_201_CREATED)
async def create_experience(
    experience_data: ExperimentExperienceCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create a new experiment experience."""
    service = ExperimentExperienceService(db)
    experience = await service.create(user_id, experience_data)
    return experience


@experiences_router.get("", response_model=List[ExperimentExperienceResponse])
async def get_experiences(
    experiment_id: Optional[str] = Query(None, description="Filter by experiment ID"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get experiences for the current user."""
    service = ExperimentExperienceService(db)
    experiences = await service.get_list(user_id, experiment_id)
    return experiences


@experiences_router.get("/search", response_model=List[ExperimentExperienceResponse])
async def search_experiences(
    keyword: str = Query(..., description="Search keyword"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Search experiences by keyword."""
    service = ExperimentExperienceService(db)
    experiences = await service.search(user_id, keyword)
    return experiences


@experiences_router.get("/{experience_id}", response_model=ExperimentExperienceResponse)
async def get_experience(
    experience_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get a specific experience."""
    service = ExperimentExperienceService(db)
    experience = await service.get(experience_id, user_id)

    if not experience:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experience not found",
        )

    return experience


@experiences_router.get("/user/{user_id}", response_model=List[ExperimentExperienceResponse])
async def list_user_experiences(
    user_id: str,
    status: Optional[str] = Query(None, description="Filter by status: verified, draft, deprecated"),
    limit: Optional[int] = Query(10, description="Maximum number of experiences to return"),
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user),
):
    """
    获取用户所有Agent的verified经验（跨Agent经验查询）

    支持的查询参数:
    - status: 过滤经验状态 (verified, draft, deprecated)
    - limit: 返回结果的最大数量 (默认10)
    """
    # 验证权限：只能查询自己的经验
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access other users' experiences",
        )

    from agent_builder.services.experience_service import ExperienceService

    service = ExperienceService(db)
    experiences = await service.list_user_experiences(
        user_id=user_id,
        status=status,
        limit=limit
    )

    return experiences
