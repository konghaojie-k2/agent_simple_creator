#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datasets API - 数据集市场 API

提供数据集的 CRUD 接口：
- 创建/更新/删除数据集
- 列出数据集
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.pydantic import (
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
)
from agent_builder.services.market_service import MarketService

router = APIRouter(prefix="/api/market/datasets", tags=["datasets"])


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_data: DatasetCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """创建数据集"""
    service = MarketService(db)
    dataset = await service.create_dataset(
        user_id=user_id,
        name=dataset_data.name,
        dataset_type=dataset_data.dataset_type,
        description=dataset_data.description,
        schema=dataset_data.data_schema,
        file_path=dataset_data.file_path,
        row_count=dataset_data.row_count,
        tags=dataset_data.tags,
        extra_metadata=dataset_data.extra_metadata,
        category=dataset_data.category,
        is_public=dataset_data.is_public,
    )
    return dataset


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    dataset_type: Optional[str] = Query(None, description="Filter by dataset type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """列出用户数据集"""
    service = MarketService(db)

    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]

    datasets = await service.list_datasets(
        user_id=user_id,
        dataset_type=dataset_type,
        category=category,
        tags=tag_list,
        limit=limit,
        offset=offset,
    )
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """获取数据集详情"""
    service = MarketService(db)
    dataset = await service.get_dataset(dataset_id, user_id)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    return dataset


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str,
    dataset_data: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """更新数据集"""
    service = MarketService(db)
    dataset = await service.update_dataset(
        dataset_id=dataset_id,
        user_id=user_id,
        name=dataset_data.name,
        description=dataset_data.description,
        dataset_type=dataset_data.dataset_type,
        schema=dataset_data.data_schema,
        file_path=dataset_data.file_path,
        row_count=dataset_data.row_count,
        tags=dataset_data.tags,
        extra_metadata=dataset_data.extra_metadata,
        category=dataset_data.category,
        is_public=dataset_data.is_public,
    )

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """删除数据集"""
    service = MarketService(db)
    success = await service.delete_dataset(dataset_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    return None
