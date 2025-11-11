"""Transition API endpoints for Advanced Editor."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_current_user, get_db
from app.models import Transition, TransitionType, User
from app.schemas.advanced_editor import TransitionCreate, TransitionRead

router = APIRouter()


@router.get("", response_model=list[TransitionRead])
async def list_transitions(
    transition_type: TransitionType | None = Query(None),
    is_public: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List available transitions."""
    query = select(Transition).where(Transition.is_public == is_public)

    if transition_type:
        query = query.where(Transition.transition_type == transition_type)

    query = query.order_by(Transition.is_builtin.desc(), Transition.name)

    result = await db.execute(query)
    transitions = result.scalars().all()

    return transitions


@router.get("/{transition_id}", response_model=TransitionRead)
async def get_transition(
    transition_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get transition details."""
    result = await db.execute(select(Transition).where(Transition.id == transition_id))
    transition = result.scalar_one_or_none()

    if not transition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transition not found",
        )

    return transition


@router.post("", response_model=TransitionRead, status_code=status.HTTP_201_CREATED)
async def create_transition(
    transition_data: TransitionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create custom transition (future feature)."""
    # For now, only allow built-in transitions
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Custom transitions not yet supported",
    )
