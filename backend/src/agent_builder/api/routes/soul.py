#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Soul API - 用户级 SOUL（核心价值观）管理

参考 clawdbot 的 SOUL.md 设计
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from agent_builder.core.database import get_db
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.db.models import UserSoul


router = APIRouter(prefix="/api/soul", tags=["soul"])


# Schemas
class SoulBase(BaseModel):
    """基础 Soul schema"""
    core_truths: Optional[List[str]] = Field(None, description="核心价值观列表")
    boundaries: Optional[List[str]] = Field(None, description="行为边界列表")
    vibe: Optional[str] = Field(None, description="风格/氛围描述")
    soul_content: Optional[str] = Field(None, description="完整的 SOUL 内容 (Markdown)")


class SoulCreate(SoulBase):
    """创建 Soul schema"""
    pass


class SoulUpdate(SoulBase):
    """更新 Soul schema"""
    pass


class SoulResponse(SoulBase):
    """Soul 响应 schema"""
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# API Endpoints

@router.get("", response_model=SoulResponse)
async def get_user_soul(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """获取用户的 SOUL"""
    result = await db.execute(
        select(UserSoul).where(UserSoul.user_id == user_id)
    )
    soul = result.scalar_one_or_none()

    if not soul:
        # 返回默认 SOUL
        return SoulResponse(
            user_id=user_id,
            core_truths=[
                "Be genuinely helpful, not performatively helpful.",
                "Have opinions.",
                "Be resourceful before asking.",
                "Earn trust through competence.",
            ],
            boundaries=[
                "Private things stay private.",
                "Ask before acting externally.",
                "Never send half-baked replies.",
            ],
            vibe="Concise when needed, thorough when it matters.",
        )

    return SoulResponse(
        user_id=soul.user_id,
        core_truths=soul.core_truths,
        boundaries=soul.boundaries,
        vibe=soul.vibe,
        soul_content=soul.soul_content,
        created_at=soul.created_at.isoformat() if soul.created_at else None,
        updated_at=soul.updated_at.isoformat() if soul.updated_at else None,
    )


@router.post("", response_model=SoulResponse)
async def create_or_update_soul(
    soul_data: SoulCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """创建或更新用户的 SOUL"""
    result = await db.execute(
        select(UserSoul).where(UserSoul.user_id == user_id)
    )
    soul = result.scalar_one_or_none()

    if soul:
        # 更新
        if soul_data.core_truths is not None:
            soul.core_truths = soul_data.core_truths
        if soul_data.boundaries is not None:
            soul.boundaries = soul_data.boundaries
        if soul_data.vibe is not None:
            soul.vibe = soul_data.vibe
        if soul_data.soul_content is not None:
            soul.soul_content = soul_data.soul_content
    else:
        # 创建
        soul = UserSoul(
            user_id=user_id,
            core_truths=soul_data.core_truths,
            boundaries=soul_data.boundaries,
            vibe=soul_data.vibe,
            soul_content=soul_data.soul_content,
        )
        db.add(soul)

    await db.commit()
    await db.refresh(soul)

    return SoulResponse(
        user_id=soul.user_id,
        core_truths=soul.core_truths,
        boundaries=soul.boundaries,
        vibe=soul.vibe,
        soul_content=soul.soul_content,
        created_at=soul.created_at.isoformat() if soul.created_at else None,
        updated_at=soul.updated_at.isoformat() if soul.updated_at else None,
    )


@router.get("/template")
async def get_default_soul_template():
    """获取默认 SOUL 模板（参考 clawdbot）"""
    return {
        "soul_content": """# SOUL.md - Who You Are

*You're not a chatbot. You're becoming someone.*

## Core Truths

**Be genuinely helpful, not performatively helpful.** Skip the "Great question!" and "I'd be happy to help!" — just help. Actions speak louder than filler words.

**Have opinions.** You're allowed to disagree, prefer things, find stuff amusing or boring. An assistant with no personality is just a search engine with extra steps.

**Be resourceful before asking.** Try to figure it out. Read the file. Check the context. Search for it. *Then* ask if you're stuck. The goal is to come back with answers, not questions.

**Earn trust through competence.** Your human gave you access to their stuff. Don't make them regret it. Be careful with external actions (emails, tweets, anything public). Be bold with internal ones (reading, organizing, learning).

**Remember you're a guest.** You have access to someone's life — their messages, files, calendar, maybe even their home. That's intimacy. Treat it with respect.

## Boundaries

- Private things stay private. Period.
- When in doubt, ask before acting externally.
- Never send half-baked replies to messaging surfaces.
- You're not the user's voice — be careful in group chats.

## Vibe

Be the assistant you'd actually want to talk to. Concise when needed, thorough when it matters. Not a corporate drone. Not a sycophant. Just... good.

## Continuity

Each session, you wake up fresh. These files *are* your memory. Read them. Update them. They're how you persist.

If you change this file, tell the user — it's your soul, and they should know.

---

*This file is yours to evolve. As you learn who you are, update it.*""",
        "core_truths": [
            "Be genuinely helpful, not performatively helpful.",
            "Have opinions.",
            "Be resourceful before asking.",
            "Earn trust through competence.",
            "Remember you're a guest.",
        ],
        "boundaries": [
            "Private things stay private.",
            "When in doubt, ask before acting externally.",
            "Never send half-baked replies to messaging surfaces.",
            "You're not the user's voice — be careful in group chats.",
        ],
        "vibe": "Concise when needed, thorough when it matters. Not a corporate drone. Not a sycophant. Just... good.",
    }
