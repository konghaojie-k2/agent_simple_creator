#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Service - 技能市场服务

用于 Skill Market（技能市场）的技能管理。
支持：
- 创建/更新/删除技能
- 技能分类和标签
- 技能复用统计
- 文件系统技能同步
"""

import uuid
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func, and_, or_
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

    async def sync_filesystem_skills(self, public_dir: str = "./market/skills/public") -> int:
        """
        同步文件系统中的公共技能到数据库

        Args:
            public_dir: 公共技能目录路径

        Returns:
            同步的技能数量
        """
        import yaml

        public_path = Path(public_dir)
        if not public_path.exists():
            return 0

        synced_count = 0

        # 遍历公共技能目录
        for skill_dir in public_path.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                # 读取并解析 SKILL.md
                content = skill_md.read_text(encoding="utf-8")
                frontmatter_match = re.match(r"---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
                if not frontmatter_match:
                    continue

                frontmatter = yaml.safe_load(frontmatter_match.group(1))
                skill_content = frontmatter_match.group(2).strip()

                # 检查是否已存在（根据名称和来源）
                existing = await self.db.execute(
                    select(Skill).where(
                        and_(
                            Skill.name == frontmatter.get("name", skill_dir.name),
                            Skill.source == "filesystem"
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    continue  # 已存在，跳过

                # 创建技能记录
                skill = Skill(
                    id=str(uuid.uuid4()),
                    user_id="system",  # 系统预置
                    name=frontmatter.get("name", skill_dir.name),
                    description=frontmatter.get("description", ""),
                    category=frontmatter.get("category", "custom"),
                    content=skill_content,
                    content_type="text",
                    parameters_schema=frontmatter.get("parameters", {}),
                    tags=frontmatter.get("tags", []),
                    is_public=True,
                    source="filesystem",
                    extra_metadata={
                        "skill_dir": str(skill_dir),
                        "original_name": skill_dir.name
                    }
                )
                self.db.add(skill)
                synced_count += 1

            except Exception as e:
                print(f"Failed to sync skill {skill_dir.name}: {e}")
                continue

        if synced_count > 0:
            await self.db.commit()

        return synced_count

    async def list_skills_by_visibility(
        self,
        user_id: str,
        is_public: Optional[bool] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Skill]:
        """按可见性列出技能"""
        # 构建条件：用户自己的 + 公开的
        conditions = [
            or_(
                Skill.user_id == user_id,
                Skill.is_public == True
            )
        ]

        if is_public is not None:
            conditions.append(Skill.is_public == is_public)

        if category:
            conditions.append(Skill.category == category)

        if tags:
            for tag in tags:
                conditions.append(Skill.tags.contains([tag]))

        query = select(Skill).where(and_(*conditions)).order_by(
            Skill.created_at.desc()
        ).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_skill_visibility(
        self,
        skill_id: str,
        user_id: str,
        is_public: bool
    ) -> Optional[Skill]:
        """更新技能可见性（私有<->公共转换）"""
        skill = await self.get_skill(skill_id, user_id)
        if not skill:
            return None

        # 只有技能所有者可以修改可见性
        if skill.user_id != user_id and skill.source != "filesystem":
            return None

        skill.is_public = is_public
        await self.db.commit()
        await self.db.refresh(skill)
        return skill
