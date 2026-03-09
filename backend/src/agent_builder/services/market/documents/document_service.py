#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document Service - 文档服务

用于 Doc Market（文档模板市场）的文档管理。
支持：
- 创建/更新/删除文档
- 文档内容存储（数据库或文件系统）
- 文档分类和标签
"""

import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agent_builder.db.models import Document


class DocumentService:
    """文档服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        # market 目录：存放共享的文档/数据集/技能
        self.market_root = Path(__file__).parent.parent.parent.parent / "market" / "documents"

    def _get_doc_dir(self, user_id: str, doc_id: str, is_public: bool = False) -> Path:
        """获取文档存储目录（根据是否公开选择public或private）"""
        visibility = "public" if is_public else "private"
        doc_dir = self.market_root / visibility / user_id / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        return doc_dir

    async def create_document(
        self,
        user_id: str,
        name: str,
        doc_type: str = "general",
        description: Optional[str] = None,
        content: Optional[str] = None,
        file_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        is_public: bool = False,
    ) -> Document:
        """创建文档"""
        doc = Document(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            doc_type=doc_type,
            content=content,
            file_path=file_path,
            tags=tags or [],
            metadata=metadata or {},
            category=category,
            is_public=is_public,
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return doc

    async def get_document(self, doc_id: str, user_id: str) -> Optional[Document]:
        """获取文档"""
        result = await self.db.execute(
            select(Document).where(
                Document.id == doc_id,
                (Document.user_id == user_id) | (Document.is_public == True)
            )
        )
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        user_id: str,
        doc_type: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_public: bool = True,
        limit: int = 50,
    ) -> List[Document]:
        """列出文档"""
        query = select(Document)

        # 过滤条件
        if include_public:
            query = query.where(
                (Document.user_id == user_id) | (Document.is_public == True)
            )
        else:
            query = query.where(Document.user_id == user_id)

        if doc_type:
            query = query.where(Document.doc_type == doc_type)

        if category:
            query = query.where(Document.category == category)

        if tags:
            for tag in tags:
                query = query.where(Document.tags.contains([tag]))

        query = query.order_by(Document.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_document(
        self,
        doc_id: str,
        user_id: str,
        **kwargs,
    ) -> Optional[Document]:
        """更新文档"""
        doc = await self.get_document(doc_id, user_id)
        if not doc:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(doc, key):
                setattr(doc, key, value)

        await self.db.flush()
        await self.db.refresh(doc)
        return doc

    async def delete_document(self, doc_id: str, user_id: str) -> bool:
        """删除文档"""
        doc = await self.get_document(doc_id, user_id)
        if not doc:
            return False

        await self.db.delete(doc)
        await self.db.flush()
        return True

    async def search_documents(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
    ) -> List[Document]:
        """搜索文档"""
        # 简单实现：按名称和描述搜索
        result = await self.db.execute(
            select(Document).where(
                ((Document.user_id == user_id) | (Document.is_public == True)),
                (Document.name.contains(query)) | (Document.description.contains(query))
            ).limit(limit)
        )
        return list(result.scalars().all())

    async def list_documents_by_visibility(
        self,
        user_id: str,
        is_public: Optional[bool] = None,
        doc_type: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Document]:
        """按可见性列出文档"""
        from sqlalchemy import and_, or_

        conditions = [
            or_(
                Document.user_id == user_id,
                Document.is_public == True
            )
        ]

        if is_public is not None:
            conditions.append(Document.is_public == is_public)

        if doc_type:
            conditions.append(Document.doc_type == doc_type)

        if category:
            conditions.append(Document.category == category)

        if tags:
            for tag in tags:
                conditions.append(Document.tags.contains([tag]))

        query = select(Document).where(and_(*conditions)).order_by(
            Document.created_at.desc()
        ).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_document_visibility(
        self,
        doc_id: str,
        user_id: str,
        is_public: bool
    ) -> Optional[Document]:
        """更新文档可见性（私有<->公共转换）"""
        doc = await self.get_document(doc_id, user_id)
        if not doc:
            return None

        # 只有文档所有者可以修改可见性
        if doc.user_id != user_id and doc.source != "filesystem":
            return None

        doc.is_public = is_public
        await self.db.commit()
        await self.db.refresh(doc)
        return doc
        return list(result.scalars().all())

    # ==================== 文件存储辅助方法 ====================

    def get_document_file_path(self, user_id: str, doc_id: str, is_public: bool = False) -> Path:
        """获取文档文件存储路径（根据是否公开选择public或private目录）"""
        return self._get_doc_dir(user_id, doc_id, is_public)

    async def save_document_file(
        self,
        user_id: str,
        doc_id: str,
        filename: str,
        content: bytes,
    ) -> str:
        """保存文档文件"""
        doc_dir = self.get_document_file_path(user_id, doc_id)
        file_path = doc_dir / filename
        file_path.write_bytes(content)
        return str(file_path)

    async def read_document_file(
        self,
        user_id: str,
        doc_id: str,
        filename: str,
    ) -> Optional[bytes]:
        """读取文档文件"""
        # 先获取文档的公开状态
        doc = await self.get_document(doc_id, user_id)
        if not doc:
            return None
        doc_dir = self._get_doc_dir(user_id, doc_id, doc.is_public)
        file_path = doc_dir / filename
        if file_path.exists():
            return file_path.read_bytes()
        return None
        return None


# ==================== 全局实例 ====================

_document_service_instance = None


def get_document_service(db: AsyncSession) -> DocumentService:
    """获取 DocumentService 实例"""
    return DocumentService(db)
