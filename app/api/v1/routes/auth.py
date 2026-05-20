from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest
from app.schemas.common import SuccessResponse, TokenPair
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest, session: AsyncSession = Depends(db_session)
) -> TokenPair:
    service = AuthService(session)
    try:
        user = await service.register(
            payload.email, payload.full_name, payload.password, payload.organization_name
        )
        tokens = await service.issue_tokens(user)
        await session.commit()
        return TokenPair(**tokens)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, session: AsyncSession = Depends(db_session)) -> TokenPair:
    service = AuthService(session)
    user = await service.authenticate(payload.email, payload.password)
    if user is None:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    tokens = await service.issue_tokens(user)
    await session.commit()
    return TokenPair(**tokens)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest, session: AsyncSession = Depends(db_session)
) -> TokenPair:
    service = AuthService(session)
    try:
        tokens = await service.rotate_refresh_token(payload.refresh_token)
        await session.commit()
        return TokenPair(**tokens)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    payload: LogoutRequest, session: AsyncSession = Depends(db_session)
) -> SuccessResponse:
    service = AuthService(session)
    await service.revoke_refresh_token(payload.refresh_token)
    await session.commit()
    return SuccessResponse(success=True)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
