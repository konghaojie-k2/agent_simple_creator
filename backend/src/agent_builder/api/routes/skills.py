#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skills API - 技能市场 API

提供技能的 CRUD 接口：
- 创建/更新/删除技能
- 列出技能
- 上传技能文件
"""

import os
import json
import yaml
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.pydantic import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
)
from agent_builder.services.market.skills.skill_market_service import SkillService

router = APIRouter(prefix="/api/market/skills", tags=["skills"])

# 上传目录 - 保存在 backend/market/skills/private/{user_id}/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
MARKET_DIR = os.path.join(BASE_DIR, "market", "skills", "private")


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """创建技能"""
    service = SkillService(db)
    skill = await service.create_skill(
        user_id=user_id,
        name=skill_data.name,
        category=skill_data.category,
        description=skill_data.description,
        content=skill_data.content,
        content_type=skill_data.content_type,
        parameters_schema=skill_data.parameters_schema,
        tags=skill_data.tags,
        extra_metadata=skill_data.extra_metadata,
        is_public=skill_data.is_public,
    )
    return skill


@router.post("/upload", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def upload_skill(
    file: UploadFile = File(..., description="Skill file (json, yaml, yml, txt, md)"),
    name: str = Form(..., description="Skill name"),
    description: str = Form("", description="Skill description"),
    category: str = Form("custom", description="Skill category"),
    tags: str = Form("", description="Comma-separated tags"),
    is_public: bool = Form(False, description="Make skill public"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """上传技能文件并自动创建记录"""
    # 验证文件类型
    allowed_extensions = {'.json', '.yaml', '.yml', '.txt', '.md'}
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

    # 根据文件类型解析内容
    content_str = content.decode('utf-8')
    content_type = 'text'
    parsed_content = content_str
    parameters_schema = None

    try:
        if file_ext == '.json':
            content_type = 'json'
            data = json.loads(content_str)
            # 检查是否有skill格式
            if isinstance(data, dict):
                if 'parameters' in data or 'parameters_schema' in data:
                    parameters_schema = data.get('parameters_schema') or data.get('parameters')
                parsed_content = data.get('content') or data.get('prompt') or json.dumps(data, indent=2)
        elif file_ext in {'.yaml', '.yml'}:
            content_type = 'yaml'
            data = yaml.safe_load(content_str)
            if isinstance(data, dict):
                if 'parameters' in data or 'parameters_schema' in data:
                    parameters_schema = data.get('parameters_schema') or data.get('parameters')
                parsed_content = data.get('content') or data.get('prompt') or yaml.dump(data)
        elif file_ext == '.md':
            content_type = 'text'
            # Markdown文件，提取文件名作为名称
            if not name:
                name = os.path.splitext(file.filename)[0]
    except Exception as e:
        # 解析失败，使用原始内容
        parsed_content = content_str

    # 解析tags
    tag_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else None

    # 创建技能记录
    service = SkillService(db)
    skill = await service.create_skill(
        user_id=user_id,
        name=name,
        category=category,
        description=description or None,
        content=parsed_content,
        content_type=content_type,
        parameters_schema=parameters_schema,
        tags=tag_list,
        extra_metadata={"original_filename": file.filename},
        is_public=is_public,
    )

    return skill


@router.get("", response_model=List[SkillResponse])
async def list_skills(
    category: Optional[str] = Query(None, description="Filter by skill category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    is_public: Optional[bool] = Query(None, description="Filter by visibility (true=public, false=private)"),
    include_all: bool = Query(False, description="Include all skills (public + private)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """列出用户技能"""
    service = SkillService(db)

    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]

    # 如果指定了 is_public，使用新的按可见性过滤方法
    if is_public is not None or include_all:
        skills = await service.list_skills_by_visibility(
            user_id=user_id,
            is_public=is_public,
            category=category,
            tags=tag_list,
            limit=limit,
            offset=offset,
        )
    else:
        # 默认行为：用户自己的 + 公开的
        skills = await service.list_skills(
            user_id=user_id,
            category=category,
            tags=tag_list,
            limit=limit,
            offset=offset,
        )
    return skills


@router.get("/filesystem", response_model=List[dict])
async def list_filesystem_skills():
    """列出文件系统中的公共技能（无需同步到数据库）"""
    from pathlib import Path

    public_dir = os.path.join(BASE_DIR, "market", "skills", "public")
    public_path = Path(public_dir)

    if not public_path.exists():
        return []

    skills = []
    for skill_dir in public_path.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        try:
            content = skill_md.read_text(encoding="utf-8")

            # 解析 YAML frontmatter
            import re
            frontmatter_match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
            if not frontmatter_match:
                continue

            frontmatter = yaml.safe_load(frontmatter_match.group(1))

            skills.append({
                "name": frontmatter.get("name", skill_dir.name),
                "description": frontmatter.get("description", ""),
                "category": frontmatter.get("category", "custom"),
                "tags": frontmatter.get("tags", []),
                "allowed_tools": frontmatter.get("allowed-tools", []),
                "folder_name": skill_dir.name,
            })
        except Exception as e:
            print(f"Error parsing skill {skill_dir.name}: {e}")
            continue

    return skills


@router.post("/sync-filesystem", response_model=dict)
async def sync_filesystem_skills(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """同步文件系统中的公共技能到数据库"""
    service = SkillService(db)
    count = await service.sync_filesystem_skills()
    return {"synced_count": count}


@router.patch("/{skill_id}/visibility", response_model=SkillResponse)
async def update_skill_visibility(
    skill_id: str,
    visibility_data: dict,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """更新技能可见性（私有<->公共转换）"""
    service = SkillService(db)
    is_public = visibility_data.get("is_public")
    if is_public is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="is_public field is required"
        )

    skill = await service.update_skill_visibility(skill_id, user_id, is_public)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found or you don't have permission to modify it"
        )
    return skill


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """获取技能详情"""
    service = SkillService(db)
    skill = await service.get_skill(skill_id, user_id)

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    skill_data: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """更新技能"""
    service = SkillService(db)
    skill = await service.update_skill(
        skill_id=skill_id,
        user_id=user_id,
        name=skill_data.name,
        description=skill_data.description,
        category=skill_data.category,
        content=skill_data.content,
        content_type=skill_data.content_type,
        parameters_schema=skill_data.parameters_schema,
        tags=skill_data.tags,
        extra_metadata=skill_data.extra_metadata,
        is_public=skill_data.is_public,
    )

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """删除技能"""
    service = SkillService(db)
    success = await service.delete_skill(skill_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )
    return None
