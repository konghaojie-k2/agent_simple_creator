# -*- coding: utf-8 -*-
"""Experiment service for managing experiments."""

import json
import uuid
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.db.models import Experiment, ExperimentTemplate, ExperimentExperience, ExperimentStatus
from agent_builder.schemas.pydantic import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentTemplateCreate,
    ExperimentTemplateUpdate,
    ExperimentExperienceCreate,
)


class ExperimentService:
    """Service for managing experiments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str,
        experiment_data: ExperimentCreate,
    ) -> Experiment:
        """Create a new experiment."""
        experiment = Experiment(
            id=str(uuid.uuid4()),
            user_id=user_id,
            agent_id=experiment_data.agent_id,
            name=experiment_data.name,
            description=experiment_data.description,
            experiment_type=experiment_data.experiment_type,
            template_id=experiment_data.template_id,
            input_data=experiment_data.input_data,
            output_data={},
            status=ExperimentStatus.PENDING.value,
            metrics={},
        )

        self.db.add(experiment)
        await self.db.flush()
        await self.db.refresh(experiment)

        return experiment

    async def get_list(
        self,
        user_id: str,
        agent_id: Optional[str] = None,
        experiment_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Experiment]:
        """Get experiments for a user with optional filters."""
        query = select(Experiment).where(Experiment.user_id == user_id)

        if agent_id:
            query = query.where(Experiment.agent_id == agent_id)
        if experiment_type:
            query = query.where(Experiment.experiment_type == experiment_type)
        if status:
            query = query.where(Experiment.status == status)

        query = query.order_by(Experiment.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, experiment_id: str, user_id: str) -> Optional[Experiment]:
        """Get a specific experiment."""
        result = await self.db.execute(
            select(Experiment).where(
                Experiment.id == experiment_id,
                Experiment.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        experiment_id: str,
        user_id: str,
        experiment_data: ExperimentUpdate,
    ) -> Optional[Experiment]:
        """Update an experiment."""
        experiment = await self.get(experiment_id, user_id)
        if not experiment:
            return None

        update_data = experiment_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(experiment, key, value)

        await self.db.flush()
        await self.db.refresh(experiment)

        return experiment

    async def delete(self, experiment_id: str, user_id: str) -> bool:
        """Delete an experiment."""
        experiment = await self.get(experiment_id, user_id)
        if not experiment:
            return False

        await self.db.delete(experiment)
        await self.db.flush()

        return True

    async def update_status(
        self,
        experiment_id: str,
        user_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> Optional[Experiment]:
        """Update experiment status and results."""
        experiment = await self.get(experiment_id, user_id)
        if not experiment:
            return None

        experiment.status = status
        if output_data is not None:
            experiment.output_data = output_data
        if error_message is not None:
            experiment.error_message = error_message
        if metrics is not None:
            experiment.metrics = metrics

        await self.db.flush()
        await self.db.refresh(experiment)

        return experiment


class ExperimentTemplateService:
    """Service for managing experiment templates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str,
        template_data: ExperimentTemplateCreate,
    ) -> ExperimentTemplate:
        """Create a new experiment template."""
        template = ExperimentTemplate(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=template_data.name,
            description=template_data.description,
            experiment_type=template_data.experiment_type,
            template_config=template_data.template_config,
            is_public=template_data.is_public,
        )

        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)

        return template

    async def get_list(
        self,
        user_id: Optional[str] = None,
        experiment_type: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> List[ExperimentTemplate]:
        """Get templates with optional filters."""
        conditions = []

        # Get public templates or user's own templates
        if user_id:
            conditions.append(
                (ExperimentTemplate.is_public == True) | (ExperimentTemplate.user_id == user_id)
            )
        elif is_public is not None:
            conditions.append(ExperimentTemplate.is_public == is_public)

        if experiment_type:
            conditions.append(ExperimentTemplate.experiment_type == experiment_type)

        query = select(ExperimentTemplate)
        for condition in conditions:
            query = query.where(condition)

        query = query.order_by(ExperimentTemplate.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, template_id: str) -> Optional[ExperimentTemplate]:
        """Get a specific template."""
        result = await self.db.execute(
            select(ExperimentTemplate).where(ExperimentTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        template_id: str,
        user_id: str,
        template_data: ExperimentTemplateUpdate,
    ) -> Optional[ExperimentTemplate]:
        """Update a template."""
        template = await self.get(template_id)
        if not template or template.user_id != user_id:
            return None

        update_data = template_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(template, key, value)

        await self.db.flush()
        await self.db.refresh(template)

        return template

    async def delete(self, template_id: str, user_id: str) -> bool:
        """Delete a template."""
        template = await self.get(template_id)
        if not template or template.user_id != user_id:
            return False

        await self.db.delete(template)
        await self.db.flush()

        return True


class ExperimentExperienceService:
    """Service for managing experiment experiences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str,
        experience_data: ExperimentExperienceCreate,
    ) -> ExperimentExperience:
        """Create a new experiment experience."""
        experience = ExperimentExperience(
            id=str(uuid.uuid4()),
            user_id=user_id,
            experiment_id=experience_data.experiment_id,
            summary=experience_data.summary,
            lessons_learned=experience_data.lessons_learned,
            improvements=experience_data.improvements,
            related_experiments=experience_data.related_experiments,
        )

        self.db.add(experience)
        await self.db.flush()
        await self.db.refresh(experience)

        return experience

    async def get_list(
        self,
        user_id: str,
        experiment_id: Optional[str] = None,
    ) -> List[ExperimentExperience]:
        """Get experiences for a user."""
        query = select(ExperimentExperience).where(ExperimentExperience.user_id == user_id)

        if experiment_id:
            query = query.where(ExperimentExperience.experiment_id == experiment_id)

        query = query.order_by(ExperimentExperience.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get(self, experience_id: str, user_id: str) -> Optional[ExperimentExperience]:
        """Get a specific experience."""
        result = await self.db.execute(
            select(ExperimentExperience).where(
                ExperimentExperience.id == experience_id,
                ExperimentExperience.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        user_id: str,
        keyword: str,
    ) -> List[ExperimentExperience]:
        """Search experiences by keyword."""
        query = select(ExperimentExperience).where(
            ExperimentExperience.user_id == user_id,
        )
        # Simple keyword search in summary and lessons_learned
        query = query.where(
            (ExperimentExperience.summary.contains(keyword)) |
            (ExperimentExperience.lessons_learned.contains(keyword)) |
            (ExperimentExperience.improvements.contains(keyword))
        )
        query = query.order_by(ExperimentExperience.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())
