# -*- coding: utf-8 -*-
"""API routes for experiments, templates, and experiences."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.myauth_integration.auth import get_current_user
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
    """Run an experiment."""
    service = ExperimentService(db)
    experiment = await service.get(experiment_id, user_id)

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    # Update input data if provided
    if run_request and run_request.input_data:
        experiment.input_data = run_request.input_data
        await db.flush()

    # Mark as running
    experiment.status = "running"
    await db.flush()
    await db.refresh(experiment)

    # TODO: Implement actual experiment execution
    # For now, return the experiment with running status
    # The actual execution would be handled by the experiment engine

    return experiment


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
