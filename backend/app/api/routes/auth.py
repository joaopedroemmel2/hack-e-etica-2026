import jwt
from fastapi import APIRouter, HTTPException, Request, Response
from uuid import UUID

from app.api.dependencies import CurrentUser, SessionDep
from app.core.security import decode_token
from app.core.rate_limit import limiter
from app.models.entities import User
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.common import UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=AuthResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterRequest, session: SessionDep) -> AuthResponse:
    user, access, refresh = await AuthService(session).register(
        data.name, data.email, data.password
    )
    return AuthResponse(
        user=UserPublic.model_validate(user), access_token=access, refresh_token=refresh
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, session: SessionDep) -> AuthResponse:
    user, access, refresh = await AuthService(session).login(data.email, data.password)
    return AuthResponse(
        user=UserPublic.model_validate(user), access_token=access, refresh_token=refresh
    )


async def refresh_identity(data: RefreshRequest, session: SessionDep) -> tuple[User, str]:
    try:
        payload = decode_token(data.refresh_token, "refresh")
        user = await session.get(User, UUID(str(payload["sub"])))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Refresh token inválido") from None
    if not user or not user.is_active:
        raise HTTPException(401, "Refresh token inválido")
    return user, str(payload["jti"])


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("20/minute")
async def refresh(request: Request, data: RefreshRequest, session: SessionDep) -> TokenPair:
    user, token_id = await refresh_identity(data, session)
    access, replacement = await AuthService(session).rotate(data.refresh_token, user, token_id)
    return TokenPair(access_token=access, refresh_token=replacement)


@router.post("/logout", status_code=204)
async def logout(data: RefreshRequest, session: SessionDep) -> Response:
    try:
        payload = decode_token(data.refresh_token, "refresh")
        await AuthService(session).logout(data.refresh_token, str(payload["jti"]))
    except (jwt.PyJWTError, KeyError):
        pass
    return Response(status_code=204)


@router.get("/me", response_model=UserPublic)
async def me(user: CurrentUser) -> User:
    return user


@router.patch("/change-password", status_code=204)
@limiter.limit("5/minute")
async def change_password(
    request: Request, data: ChangePasswordRequest, user: CurrentUser, session: SessionDep
) -> Response:
    await AuthService(session).change_password(user, data.current_password, data.new_password)
    return Response(status_code=204)
