"""Organization routes — schemas moved out, update/delete/member management added."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_user, get_current_membership, require_role
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.common import Paging
from app.schemas.organizations import (
    MemberInvite,
    MemberList,
    MemberOut,
    OrganizationCreate,
    OrganizationList,
    OrganizationOut,
    OrganizationUpdate,
)
from app.services.audit_service import AuditService
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    session: AsyncSession = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> OrganizationOut:
    service = OrganizationService(session)
    organization = await service.create(current_user.id, payload.name)

    audit = AuditService(session)
    await audit.log(
        action="organization.created",
        resource_type="organization",
        resource_id=organization.id,
        organization_id=organization.id,
        actor_user_id=current_user.id,
    )
    await session.commit()
    return OrganizationOut.model_validate(organization)


@router.get("", response_model=list[OrganizationOut])
async def list_organizations(
    session: AsyncSession = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> list[OrganizationOut]:
    service = OrganizationService(session)
    organizations = await service.list_for_user(current_user.id)
    return [OrganizationOut.model_validate(org) for org in organizations]


@router.get("/{organization_id}", response_model=OrganizationOut)
async def get_organization(
    organization_id: UUID,
    session: AsyncSession = Depends(db_session),
    current_user: User = Depends(get_current_user),
) -> OrganizationOut:
    service = OrganizationService(session)
    organization = await service.get_for_user(current_user.id, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return OrganizationOut.model_validate(organization)


@router.patch("/{organization_id}", response_model=OrganizationOut)
async def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin")),
) -> OrganizationOut:
    if str(membership.organization_id) != str(organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")

    stmt = select(Organization).where(
        Organization.id == organization_id, Organization.deleted_at.is_(None)
    )
    result = await session.execute(stmt)
    org = result.scalars().first()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if payload.name is not None:
        org.name = payload.name.strip()

    audit = AuditService(session)
    await audit.log(
        action="organization.updated",
        resource_type="organization",
        resource_id=organization_id,
        organization_id=organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()
    await session.refresh(org)
    return OrganizationOut.model_validate(org)


@router.delete("/{organization_id}", status_code=status.HTTP_200_OK)
async def delete_organization(
    organization_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner")),
) -> dict[str, str]:
    if str(membership.organization_id) != str(organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")

    stmt = select(Organization).where(
        Organization.id == organization_id, Organization.deleted_at.is_(None)
    )
    result = await session.execute(stmt)
    org = result.scalars().first()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    org.deleted_at = datetime.now(UTC)
    org.is_active = False

    audit = AuditService(session)
    await audit.log(
        action="organization.deleted",
        resource_type="organization",
        resource_id=organization_id,
        organization_id=organization_id,
        actor_user_id=membership.user_id,
    )
    await session.commit()

    return {"message": "Organization deleted", "organization_id": str(organization_id)}


# --- Member management ---


@router.get("/{organization_id}/members", response_model=MemberList)
async def list_members(
    organization_id: UUID,
    paging: Paging = Depends(),
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(get_current_membership),
) -> MemberList:
    if str(membership.organization_id) != str(organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")

    stmt = (
        select(Membership, User)
        .join(User, Membership.user_id == User.id)
        .where(
            Membership.organization_id == organization_id,
            Membership.is_active.is_(True),
            Membership.deleted_at.is_(None),
        )
        .order_by(Membership.created_at)
        .limit(paging.limit)
        .offset(paging.offset)
    )
    result = await session.execute(stmt)
    rows = result.all()

    members = []
    for m, u in rows:
        members.append(
            MemberOut(
                id=m.id,
                user_id=m.user_id,
                organization_id=m.organization_id,
                role=m.role,
                is_active=m.is_active,
                email=u.email,
                full_name=u.full_name,
                created_at=m.created_at,
            )
        )

    return MemberList(items=members, total=len(members))


@router.post("/{organization_id}/members", status_code=status.HTTP_201_CREATED)
async def invite_member(
    organization_id: UUID,
    payload: MemberInvite,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin")),
) -> dict[str, str]:
    if str(membership.organization_id) != str(organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")

    # Find user by email
    user_result = await session.execute(
        select(User).where(User.email == payload.email, User.deleted_at.is_(None))
    )
    user = user_result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check existing membership
    existing = await session.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == organization_id,
            Membership.deleted_at.is_(None),
        )
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User is already a member"
        )

    new_membership = Membership(
        user_id=user.id,
        organization_id=organization_id,
        role=payload.role,
    )
    session.add(new_membership)

    audit = AuditService(session)
    await audit.log(
        action="member.invited",
        resource_type="membership",
        resource_id=new_membership.id,
        organization_id=organization_id,
        actor_user_id=membership.user_id,
        metadata={"invited_email": payload.email, "role": payload.role},
    )
    await session.commit()

    return {"message": "Member invited", "user_id": str(user.id), "role": payload.role}


@router.delete("/{organization_id}/members/{user_id}", status_code=status.HTTP_200_OK)
async def remove_member(
    organization_id: UUID,
    user_id: UUID,
    session: AsyncSession = Depends(db_session),
    membership: Membership = Depends(require_role("owner", "admin")),
) -> dict[str, str]:
    if str(membership.organization_id) != str(organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization mismatch")

    stmt = select(Membership).where(
        Membership.user_id == user_id,
        Membership.organization_id == organization_id,
        Membership.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    target = result.scalars().first()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if target.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the owner"
        )

    target.is_active = False
    target.deleted_at = datetime.now(UTC)

    audit = AuditService(session)
    await audit.log(
        action="member.removed",
        resource_type="membership",
        resource_id=target.id,
        organization_id=organization_id,
        actor_user_id=membership.user_id,
        metadata={"removed_user_id": str(user_id)},
    )
    await session.commit()

    return {"message": "Member removed", "user_id": str(user_id)}
