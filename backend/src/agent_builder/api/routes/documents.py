#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document API - 文档市场 API

提供文档的 CRUD 接口：
- 创建/更新/删除文档
- 列出/搜索文档
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.pydantic import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)
from agent_builder.services.document_service import DocumentService

router = APIRouter(prefix="/api/market/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    doc_data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """创建文档"""
    service = DocumentService(db)
    doc = await service.create_document(
        user_id=user_id,
        name=doc_data.name,
        doc_type=doc_data.doc_type,
        description=doc_data.description,
        content=doc_data.content,
        file_path=doc_data.file_path,
        tags=doc_data.tags,
        metadata=doc_data.metadata,
        category=doc_data.category,
        is_public=doc_data.is_public,
    )
    return doc


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    include_public: bool = Query(True, description="Include public documents"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """列出文档"""
    service = DocumentService(db)

    tag_list = tags.split(",") if tags else None

    docs = await service.list_documents(
        user_id=user_id,
        doc_type=doc_type,
        category=category,
        tags=tag_list,
        include_public=include_public,
        limit=limit,
    )
    return docs


@router.get("/search", response_model=List[DocumentResponse])
async def search_documents(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """搜索文档"""
    service = DocumentService(db)
    docs = await service.search_documents(user_id=user_id, query=q, limit=limit)
    return docs


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """获取文档详情"""
    service = DocumentService(db)
    doc = await service.get_document(doc_id, user_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@router.put("/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: str,
    doc_data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """更新文档"""
    service = DocumentService(db)

    # 构建更新参数
    update_kwargs = doc_data.model_dump(exclude_unset=True)

    doc = await service.update_document(doc_id, user_id, **update_kwargs)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """删除文档"""
    service = DocumentService(db)
    success = await service.delete_document(doc_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
