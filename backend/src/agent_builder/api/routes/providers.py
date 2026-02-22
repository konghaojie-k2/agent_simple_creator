# -*- coding: utf-8 -*-
"""API routes for LLM providers."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.core.database import get_db
from agent_builder.db.models import LLMProvider
from agent_builder.myauth_integration.auth import get_current_user
from agent_builder.schemas.pydantic import (
    LLMProviderCreate,
    LLMProviderResponse,
    LLMProviderUpdate,
)
from agent_builder.services.agent_service import AgentService


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("", response_model=LLMProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: LLMProviderCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create a new LLM provider."""
    service = AgentService(db)
    provider = await service.create_provider(user_id, provider_data)
    return provider


@router.get("", response_model=List[LLMProviderResponse])
async def get_providers(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get all LLM providers for the current user."""
    service = AgentService(db)
    providers = await service.get_providers(user_id)

    # Return without exposing encrypted API key
    result = []
    for p in providers:
        result.append(LLMProviderResponse(
            id=p.id,
            user_id=p.user_id,
            name=p.name,
            provider_type=p.provider_type,
            api_base=p.api_base,
            api_key="********",  # Mask API key
            default_model=p.default_model,
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))
    return result


@router.get("/{provider_id}", response_model=LLMProviderResponse)
async def get_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Get a specific LLM provider."""
    service = AgentService(db)
    provider = await service.get_provider(provider_id, user_id)

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )

    return LLMProviderResponse(
        id=provider.id,
        user_id=provider.user_id,
        name=provider.name,
        provider_type=provider.provider_type,
        api_base=provider.api_base,
        api_key="********",
        default_model=provider.default_model,
        is_active=provider.is_active,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


@router.put("/{provider_id}", response_model=LLMProviderResponse)
async def update_provider(
    provider_id: str,
    provider_data: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Update a LLM provider."""
    service = AgentService(db)
    provider = await service.update_provider(provider_id, user_id, provider_data)

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )

    return LLMProviderResponse(
        id=provider.id,
        user_id=provider.user_id,
        name=provider.name,
        provider_type=provider.provider_type,
        api_base=provider.api_base,
        api_key="********",
        default_model=provider.default_model,
        is_active=provider.is_active,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Delete a LLM provider."""
    service = AgentService(db)
    success = await service.delete_provider(provider_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )
