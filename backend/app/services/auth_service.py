from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    new_token_id,
    token_digest,
    verify_password,
)
from app.models.entities import RefreshToken, Role, User, utcnow

DUMMY_PASSWORD_HASH = hash_password("invalid-credentials-placeholder")


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, name: str, email: str, password: str) -> tuple[User, str, str]:
        user = User(
            name=name,
            email=email.lower(),
            password_hash=hash_password(password),
            role=Role.COLABORADOR,
        )
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError as error:
            await self.session.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Não foi possível concluir o cadastro"
            ) from error
        tokens = await self._issue(user)
        await self.session.commit()
        return user, *tokens

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        user = (await self.session.exec(select(User).where(User.email == email.lower()))).first()
        valid_password = verify_password(
            password,
            user.password_hash if user else DUMMY_PASSWORD_HASH,
        )
        if not user or not user.is_active or not valid_password:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas")
        tokens = await self._issue(user)
        await self.session.commit()
        return user, *tokens

    async def _issue(self, user: User) -> tuple[str, str]:
        token_id = new_token_id()
        refresh = create_refresh_token(str(user.id), user.role.value, token_id)
        self.session.add(
            RefreshToken(
                token_id=token_id,
                token_hash=token_digest(refresh),
                user_id=user.id,
                expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
            )
        )
        return create_access_token(str(user.id), user.role.value), refresh

    async def rotate(self, token: str, user: User, token_id: str) -> tuple[str, str]:
        stored = (
            await self.session.exec(
                select(RefreshToken)
                .where(RefreshToken.token_id == token_id, RefreshToken.user_id == user.id)
                .with_for_update()
            )
        ).first()
        expires_at = stored.expires_at if stored else datetime.now(UTC)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if (
            not stored
            or stored.revoked_at
            or expires_at <= datetime.now(UTC)
            or stored.token_hash != token_digest(token)
        ):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token inválido")
        stored.revoked_at = datetime.now(UTC)
        pair = await self._issue(user)
        await self.session.commit()
        return pair

    async def logout(self, token: str, token_id: str) -> None:
        stored = (
            await self.session.exec(select(RefreshToken).where(RefreshToken.token_id == token_id))
        ).first()
        if stored and stored.token_hash == token_digest(token):
            stored.revoked_at = datetime.now(UTC)
            await self.session.commit()

    async def change_password(self, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas")
        user.password_hash = hash_password(new)
        user.updated_at = utcnow()
        rows = (
            await self.session.exec(
                select(RefreshToken).where(
                    RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
                )
            )
        ).all()
        for row in rows:
            row.revoked_at = datetime.now(UTC)
        await self.session.commit()
