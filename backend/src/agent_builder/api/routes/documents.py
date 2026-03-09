#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document API - 文档市场 API

提供文档的 CRUD 接口：
- 创建/更新/删除文档
- 列出/搜索文档
- 上传文档文件
"""

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.pydantic import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)
from agent_builder.services.market.documents.document_service import DocumentService

router = APIRouter(prefix="/api/market/documents", tags=["documents"])

# 上传目录 - 保存在 backend/market/documents/private/{user_id}/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
MARKET_DIR = os.path.join(BASE_DIR, "market", "documents", "private")


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


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="Document file (md, txt, html, json)"),
    name: str = Form(..., description="Document name"),
    doc_type: str = Form("markdown", description="Document type"),
    category: str = Form("documentation", description="Document category"),
    description: str = Form("", description="Document description"),
    tags: str = Form("", description="Comma-separated tags"),
    is_public: bool = Form(False, description="Make document public"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """上传文档文件并自动创建记录"""
    # 验证文件类型
    allowed_extensions = {'.md', '.txt', '.html', '.json'}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # 保存文件到用户的私有目录
    user_dir = os.path.join(MARKET_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    safe_filename = f"{file.filename}"
    file_path = os.path.join(user_dir, safe_filename)

    content = await file.read()
    content_str = content.decode('utf-8')

    # 根据文件类型确定doc_type
    doc_type_map = {
        '.md': 'markdown',
        '.txt': 'text',
        '.html': 'html',
        '.json': 'json',
    }
    final_doc_type = doc_type_map.get(file_ext, doc_type)

    # 解析tags
    tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else None

    # 创建文档记录
    service = DocumentService(db)
    doc = await service.create_document(
        user_id=user_id,
        name=name,
        doc_type=final_doc_type,
        description=description or None,
        content=content_str,
        file_path=file_path,
        tags=tag_list,
        metadata={"original_filename": file.filename},
        category=category or None,
        is_public=is_public,
    )

    return doc


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    is_public: Optional[bool] = Query(None, description="Filter by visibility (true=public, false=private)"),
    include_public: bool = Query(True, description="Include public documents"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """列出文档"""
    service = DocumentService(db)

    tag_list = tags.split(",") if tags else None

    # 如果指定了 is_public，使用新的按可见性过滤方法
    if is_public is not None:
        docs = await service.list_documents_by_visibility(
            user_id=user_id,
            is_public=is_public,
            doc_type=doc_type,
            category=category,
            tags=tag_list,
            limit=limit,
            offset=offset,
        )
    else:
        docs = await service.list_documents(
            user_id=user_id,
            doc_type=doc_type,
            category=category,
            tags=tag_list,
            include_public=include_public,
            limit=limit,
        )
    return docs


@router.patch("/{doc_id}/visibility", response_model=DocumentResponse)
async def update_document_visibility(
    doc_id: str,
    visibility_data: dict,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """更新文档可见性（私有<->公共转换）"""
    service = DocumentService(db)
    is_public = visibility_data.get("is_public")
    if is_public is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="is_public field is required"
        )

    doc = await service.update_document_visibility(doc_id, user_id, is_public)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you don't have permission to modify it"
        )
    return doc


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
