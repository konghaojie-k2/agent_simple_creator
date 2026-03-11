#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datasets API - 数据集市场 API

提供数据集的 CRUD 接口：
- 创建/更新/删除数据集
- 列出数据集
- 上传数据集文件
"""

import os
import json
import uuid
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.pydantic import (
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
)
from agent_builder.services.market.data.market_service import MarketService

router = APIRouter(prefix="/api/market/datasets", tags=["datasets"])

# 上传目录 - 保存在 backend/market/data/private/{user_id}/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
MARKET_DIR = os.path.join(BASE_DIR, "market", "data", "private")


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


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(..., description="Dataset file (json, csv, txt, parquet)"),
    name: str = Form(..., description="Dataset name"),
    description: str = Form("", description="Dataset description"),
    category: str = Form("", description="Dataset category"),
    tags: str = Form("", description="Comma-separated tags"),
    is_public: bool = Form(False, description="Make dataset public"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """上传数据集文件并自动创建记录"""
    # 验证文件类型
    allowed_extensions = {'.json', '.csv', '.txt', '.parquet'}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # 保存文件到用户的私有目录
    user_dir = os.path.join(MARKET_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)

    # 安全处理文件名，防止目录遍历攻击
    safe_filename = os.path.basename(file.filename)
    if not safe_filename:
        safe_filename = f"dataset_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(user_dir, safe_filename)

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # 解析文件内容获取行数和schema
    row_count = 0
    data_schema = {}

    try:
        if file_ext == '.json':
            data = json.loads(content.decode('utf-8'))
            if isinstance(data, list) and len(data) > 0:
                row_count = len(data)
                # 从第一条记录提取schema
                if isinstance(data[0], dict):
                    data_schema = {k: type(v).__name__ for k, v in data[0].items()}
        elif file_ext == '.csv':
            lines = content.decode('utf-8').strip().split('\n')
            row_count = max(0, len(lines) - 1)  # 减去header
            if row_count > 0:
                headers = lines[0].split(',')
                data_schema = {h.strip(): "string" for h in headers}
        elif file_ext == '.txt':
            lines = content.decode('utf-8').strip().split('\n')
            row_count = len([l for l in lines if l.strip()])
    except Exception as e:
        # 解析失败，使用默认值
        pass

    # 解析tags
    tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else None

    # 创建数据集记录
    service = MarketService(db)
    dataset = await service.create_dataset(
        user_id=user_id,
        name=name,
        dataset_type=file_ext[1:],  # 去掉点号
        description=description or None,
        schema=data_schema or None,
        file_path=file_path,
        row_count=row_count,
        tags=tag_list,
        extra_metadata={"original_filename": file.filename},
        category=category or None,
        is_public=is_public,
    )

    return dataset


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    dataset_type: Optional[str] = Query(None, description="Filter by dataset type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    is_public: Optional[bool] = Query(None, description="Filter by visibility (true=public, false=private)"),
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

    # 如果指定了 is_public，使用新的按可见性过滤方法
    if is_public is not None:
        datasets = await service.list_datasets_by_visibility(
            user_id=user_id,
            is_public=is_public,
            dataset_type=dataset_type,
            category=category,
            tags=tag_list,
            limit=limit,
            offset=offset,
        )
    else:
        datasets = await service.list_datasets(
            user_id=user_id,
            dataset_type=dataset_type,
            category=category,
            tags=tag_list,
            limit=limit,
            offset=offset,
        )
    return datasets


@router.patch("/{dataset_id}/visibility", response_model=DatasetResponse)
async def update_dataset_visibility(
    dataset_id: str,
    visibility_data: dict,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """更新数据集可见性（私有<->公共转换）"""
    service = MarketService(db)
    is_public = visibility_data.get("is_public")
    if is_public is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="is_public field is required"
        )

    dataset = await service.update_dataset_visibility(dataset_id, user_id, is_public)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or you don't have permission to modify it"
        )
    return dataset


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


# ========== Analysis Endpoints ==========

@router.get("/{dataset_id}/analyze")
async def analyze_dataset(
    dataset_id: str,
    sample_size: int = Query(1000, ge=100, le=10000),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Analyze dataset and generate comprehensive metadata"""
    from agent_builder.services.market.data.analysis.metadata_service import enhanced_metadata_service
    
    service = MarketService(db)
    dataset = await service.get_dataset(dataset_id, user_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Load data file
    if not dataset.file_path:
        raise HTTPException(status_code=400, detail="Dataset has no file")
    
    # Use the stored file_path directly (it's stored as absolute path from upload)
    file_path = dataset.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    
    # Load data based on type
    if dataset.dataset_type == 'csv':
        df = pd.read_csv(file_path)
    elif dataset.dataset_type == 'json':
        df = pd.read_json(file_path)
    elif dataset.dataset_type == 'parquet':
        df = pd.read_parquet(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Analyze
    result = await enhanced_metadata_service.analyze_dataset(
        dataset_id=dataset_id,
        dataframe=df,
        sample_size=sample_size
    )
    
    return result


@router.get("/{dataset_id}/quality")
async def get_dataset_quality(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get data quality report"""
    from agent_builder.services.market.data.analysis.metadata_service import enhanced_metadata_service
    
    service = MarketService(db)
    dataset = await service.get_dataset(dataset_id, user_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not dataset.file_path:
        raise HTTPException(status_code=400, detail="Dataset has no file")
    
    # Use the stored file_path directly (it's stored as absolute path from upload)
    file_path = dataset.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    
    if dataset.dataset_type == 'csv':
        df = pd.read_csv(file_path)
    elif dataset.dataset_type == 'json':
        df = pd.read_json(file_path)
    elif dataset.dataset_type == 'parquet':
        df = pd.read_parquet(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    quality = enhanced_metadata_service._calculate_quality_score(df)
    
    return {
        "dataset_id": dataset_id,
        "quality": quality
    }


@router.get("/{dataset_id}/schema")
async def get_dataset_schema(
    dataset_id: str,
    include_semantics: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get dataset schema"""
    from agent_builder.services.market.data.analysis.metadata_service import enhanced_metadata_service
    
    service = MarketService(db)
    dataset = await service.get_dataset(dataset_id, user_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    result = {
        "dataset_id": dataset_id,
        "name": dataset.name,
        "columns": []
    }
    
    if dataset.schema:
        for col_name, col_type in dataset.schema.items():
            col_info = {"name": col_name, "type": col_type}
            
            if include_semantics:
                col_info["semantic_type"] = enhanced_metadata_service._infer_semantic_type(col_name)
                col_info["business_description"] = enhanced_metadata_service._generate_business_description(col_name)
            
            result["columns"].append(col_info)
    
    return result


@router.get("/{dataset_id}/insights")
async def get_dataset_insights(
    dataset_id: str,
    sample_size: int = Query(1000, ge=100, le=10000),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get AI-generated insights"""
    from agent_builder.services.market.data.analysis.metadata_service import enhanced_metadata_service
    
    service = MarketService(db)
    dataset = await service.get_dataset(dataset_id, user_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not dataset.file_path:
        raise HTTPException(status_code=400, detail="Dataset has no file")
    
    # Use the stored file_path directly (it's stored as absolute path from upload)
    file_path = dataset.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    
    if dataset.dataset_type == 'csv':
        df = pd.read_csv(file_path)
    elif dataset.dataset_type == 'json':
        df = pd.read_json(file_path)
    elif dataset.dataset_type == 'parquet':
        df = pd.read_parquet(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    result = await enhanced_metadata_service.analyze_dataset(
        dataset_id=dataset_id,
        dataframe=df,
        sample_size=sample_size
    )
    
    return {
        "dataset_id": dataset_id,
        "insights": result.get("data_understanding", {}).get("suggested_uses", []),
        "issues": result.get("data_understanding", {}).get("potential_issues", []),
        "summary": result.get("data_understanding", {}).get("summary", ""),
        "key_fields": result.get("agent_queryable", {}).get("key_fields", [])
    }
