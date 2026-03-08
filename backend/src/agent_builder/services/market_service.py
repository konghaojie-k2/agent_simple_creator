#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Service - 素材市场服务

用于 Data Market（数据集市场）的数据集管理。
支持：
- 创建/更新/删除数据集
- 数据集文件存储
- 数据集分类和标签
"""

import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.db.models import Dataset, DatasetType


class MarketService:
    """数据集市场服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.workspaces_dir = Path("./workspaces")

    def _get_dataset_storage_path(self, user_id: str, dataset_id: str) -> Path:
        """获取数据集存储路径"""
        return self.workspaces_dir / user_id / "data" / dataset_id

    async def create_dataset(
        self,
        user_id: str,
        name: str,
        dataset_type: str = "json",
        description: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        row_count: int = 0,
        tags: Optional[List[str]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        is_public: bool = False,
    ) -> Dataset:
        """创建数据集"""
        dataset = Dataset(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            dataset_type=dataset_type,
            schema=schema or {},
            file_path=file_path,
            row_count=row_count,
            tags=tags or [],
            extra_metadata=extra_metadata or {},
            category=category,
            is_public=is_public,
        )
        self.db.add(dataset)
        await self.db.commit()
        await self.db.refresh(dataset)
        return dataset

    async def get_dataset(self, dataset_id: str, user_id: str) -> Optional[Dataset]:
        """获取数据集详情"""
        result = await self.db.execute(
            select(Dataset).where(
                Dataset.id == dataset_id,
                (Dataset.user_id == user_id) | (Dataset.is_public == True)
            )
        )
        return result.scalar_one_or_none()

    async def list_datasets(
        self,
        user_id: str,
        dataset_type: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dataset]:
        """列出用户数据集"""
        query = select(Dataset).where(
            (Dataset.user_id == user_id) | (Dataset.is_public == True)
        )

        if dataset_type:
            query = query.where(Dataset.dataset_type == dataset_type)

        if category:
            query = query.where(Dataset.category == category)

        if tags:
            for tag in tags:
                query = query.where(Dataset.tags.contains([tag]))

        query = query.order_by(Dataset.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_datasets(
        self,
        user_id: str,
        dataset_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """统计数据集数量"""
        query = select(func.count(Dataset.id)).where(
            (Dataset.user_id == user_id) | (Dataset.is_public == True)
        )

        if dataset_type:
            query = query.where(Dataset.dataset_type == dataset_type)

        if category:
            query = query.where(Dataset.category == category)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def update_dataset(
        self,
        dataset_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        dataset_type: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        row_count: Optional[int] = None,
        tags: Optional[List[str]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> Optional[Dataset]:
        """更新数据集"""
        dataset = await self.get_dataset(dataset_id, user_id)
        if not dataset:
            return None

        if name is not None:
            dataset.name = name
        if description is not None:
            dataset.description = description
        if dataset_type is not None:
            dataset.dataset_type = dataset_type
        if schema is not None:
            dataset.schema = schema
        if file_path is not None:
            dataset.file_path = file_path
        if row_count is not None:
            dataset.row_count = row_count
        if tags is not None:
            dataset.tags = tags
        if extra_metadata is not None:
            dataset.extra_metadata = extra_metadata
        if category is not None:
            dataset.category = category
        if is_public is not None:
            dataset.is_public = is_public

        await self.db.commit()
        await self.db.refresh(dataset)
        return dataset

    async def delete_dataset(self, dataset_id: str, user_id: str) -> bool:
        """删除数据集"""
        dataset = await self.get_dataset(dataset_id, user_id)
        if not dataset:
            return False

        # 删除存储的文件
        storage_path = self._get_dataset_storage_path(user_id, dataset_id)
        if storage_path.exists():
            import shutil
            shutil.rmtree(storage_path)

        await self.db.delete(dataset)
        await self.db.commit()
        return True
