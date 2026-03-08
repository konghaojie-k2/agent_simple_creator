#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Service - 技能市场服务

用于 Skill Market（技能市场）的技能管理。
支持：
- 创建/更新/删除技能
- 技能分类和标签
- 技能复用统计
"""

import uuid
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.db.models import Skill, SkillCategory


class SkillService:
    """技能市场服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_skill(
        self,
        user_id: str,
        name: str,
        category: str = "custom",
        description: Optional[str] = None,
        content: Optional[str] = None,
        content_type: str = "text",
        parameters_schema: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        is_public: bool = False,
    ) -> Skill:
        """创建技能"""
        skill = Skill(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            category=category,
            content=content,
            content_type=content_type,
            parameters_schema=parameters_schema or {},
            tags=tags or [],
            extra_metadata=extra_metadata or {},
            is_public=is_public,
        )
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def get_skill(self, skill_id: str, user_id: str) -> Optional[Skill]:
        """获取技能详情"""
        result = await self.db.execute(
            select(Skill).where(
                Skill.id == skill_id,
                (Skill.user_id == user_id) | (Skill.is_public == True)
            )
        )
        return result.scalar_one_or_none()

    async def list_skills(
        self,
        user_id: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Skill]:
        """列出用户技能"""
        query = select(Skill).where(
            (Skill.user_id == user_id) | (Skill.is_public == True)
        )

        if category:
            query = query.where(Skill.category == category)

        if tags:
            for tag in tags:
                query = query.where(Skill.tags.contains([tag]))

        query = query.order_by(Skill.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_skills(
        self,
        user_id: str,
        category: Optional[str] = None,
    ) -> int:
        """统计技能数量"""
        query = select(func.count(Skill.id)).where(
            (Skill.user_id == user_id) | (Skill.is_public == True)
        )

        if category:
            query = query.where(Skill.category == category)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def update_skill(
        self,
        skill_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        content: Optional[str] = None,
        content_type: Optional[str] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        is_public: Optional[bool] = None,
    ) -> Optional[Skill]:
        """更新技能"""
        skill = await self.get_skill(skill_id, user_id)
        if not skill:
            return None

        if name is not None:
            skill.name = name
        if description is not None:
            skill.description = description
        if category is not None:
            skill.category = category
        if content is not None:
            skill.content = content
        if content_type is not None:
            skill.content_type = content_type
        if parameters_schema is not None:
            skill.parameters_schema = parameters_schema
        if tags is not None:
            skill.tags = tags
        if extra_metadata is not None:
            skill.extra_metadata = extra_metadata
        if is_public is not None:
            skill.is_public = is_public

        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def delete_skill(self, skill_id: str, user_id: str) -> bool:
        """删除技能"""
        skill = await self.get_skill(skill_id, user_id)
        if not skill:
            return False

        await self.db.delete(skill)
        await self.db.commit()
        return True

    async def increment_usage(self, skill_id: str, user_id: str) -> bool:
        """增加技能使用次数"""
        skill = await self.get_skill(skill_id, user_id)
        if not skill:
            return False

        skill.usage_count += 1
        await self.db.commit()
        return True
