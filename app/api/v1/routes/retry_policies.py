"""Retry policy CRUD routes."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_membership, require_role
from app.models.membership import Membership
from app.models.retry_policy import RetryPolicy
from app.schemas.common import Paging
from app.schemas.retry_policies import (
    RetryPolicyCreate,
    RetryPolicyList,
    RetryPolicyOut,
    RetryPolicyUpdate,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/retry-policies", tags=["retry-policies"])


@router.post("", response_model=RetryPolicyOut, status_code=status.HTTP_201_CREATED)
async def create_retry_policy(
    payload: RetryPolicyCreate,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin", "developer")),
) -> RetryPolicyOut:
    policy = RetryPolicy(
        organization_id=membership.organization_id,
        name=payload.name.strip(),
        max_attempts=payload.max_attempts,
        base_delay_seconds=payload.base_delay_seconds,
        max_delay_seconds=payload.max_delay_seconds,
    )
    session.add(policy)

    audit = AuditService(session)
    await audit.log(
        action="retry_policy.created",
        resource_type="retry_policy",
        resource_id=policy.id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()
    await session.refresh(policy)
    return RetryPolicyOut.model_validate(policy)


@router.get("", response_model=RetryPolicyList)
async def list_retry_policies(
    paging: Paging = Depends(),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> RetryPolicyList:
    base = select(RetryPolicy).where(
        RetryPolicy.organization_id == membership.organization_id,
        RetryPolicy.deleted_at.is_(None),
    )
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = base.order_by(RetryPolicy.created_at.desc()).limit(paging.limit).offset(paging.offset)
    result = await session.execute(stmt)
    items = result.scalars().all()

    return RetryPolicyList(
        items=[RetryPolicyOut.model_validate(p) for p in items],
        total=int(total),
    )


@router.get("/{policy_id}", response_model=RetryPolicyOut)
async def get_retry_policy(
    policy_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> RetryPolicyOut:
    stmt = select(RetryPolicy).where(
        RetryPolicy.id == policy_id,
        RetryPolicy.organization_id == membership.organization_id,
        RetryPolicy.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    policy = result.scalars().first()
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retry policy not found")
    return RetryPolicyOut.model_validate(policy)


@router.patch("/{policy_id}", response_model=RetryPolicyOut)
async def update_retry_policy(
    policy_id: UUID,
    payload: RetryPolicyUpdate,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin", "developer")),
) -> RetryPolicyOut:
    stmt = select(RetryPolicy).where(
        RetryPolicy.id == policy_id,
        RetryPolicy.organization_id == membership.organization_id,
        RetryPolicy.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    policy = result.scalars().first()
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retry policy not found")

    for field in ("name", "max_attempts", "base_delay_seconds", "max_delay_seconds"):
        value = getattr(payload, field, None)
        if value is not None:
            setattr(policy, field, value.strip() if isinstance(value, str) else value)

    audit = AuditService(session)
    await audit.log(
        action="retry_policy.updated",
        resource_type="retry_policy",
        resource_id=policy_id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()
    await session.refresh(policy)
    return RetryPolicyOut.model_validate(policy)


@router.delete("/{policy_id}", status_code=status.HTTP_200_OK)
async def delete_retry_policy(
    policy_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin")),
) -> dict[str, str]:
    stmt = select(RetryPolicy).where(
        RetryPolicy.id == policy_id,
        RetryPolicy.organization_id == membership.organization_id,
        RetryPolicy.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    policy = result.scalars().first()
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retry policy not found")

    policy.deleted_at = datetime.now(UTC)

    audit = AuditService(session)
    await audit.log(
        action="retry_policy.deleted",
        resource_type="retry_policy",
        resource_id=policy_id,
        organization_id=membership.organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()

    return {"message": "Retry policy deleted", "policy_id": str(policy_id)}
