from collections.abc import Callable
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.core.security import decode_token
from app.models.entities import Role, User

bearer = HTTPBearer(auto_error=False)
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Não autenticado", headers={"WWW-Authenticate": "Bearer"}
    )
    if not credentials:
        raise unauthorized
    try:
        payload = decode_token(credentials.credentials, "access")
        user = await session.get(User, UUID(str(payload["sub"])))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized from None
    if not user or not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[CurrentUser], User]:
    async def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado")
        return user

    return dependency


require_admin = require_roles(Role.ADMIN)
require_manager_or_admin = require_roles(Role.ADMIN, Role.GESTOR)
