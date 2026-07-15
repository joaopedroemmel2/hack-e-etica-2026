from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDep, require_admin, require_manager_or_admin
from app.core.security import hash_password
from app.models.entities import RefreshToken, Role, TeamMember, TeamMemberRole, User
from app.schemas.common import Page, UserPublic
from app.schemas.domain import ProfileUpdate, UserCreate, UserUpdate
from app.services.domain_service import DomainService, apply_values, page

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.post("", response_model=UserPublic, status_code=201)
async def create(
    data: UserCreate, session: SessionDep, actor: Annotated[User, Depends(require_admin)]
) -> User:
    user = User(**data.model_dump(exclude={"password"}), password_hash=hash_password(data.password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(409, "Não foi possível criar o usuário") from error
    await session.refresh(user)
    return user


@router.get("", response_model=Page[UserPublic])
async def list_users(
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
    page_number: int = Query(1, alias="page", ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    role: Role | None = None,
    is_active: bool | None = Query(None, alias="isActive"),
) -> dict[str, object]:
    conditions = []
    if actor.role == Role.GESTOR:
        managed_team_ids = select(TeamMember.team_id).where(
            TeamMember.user_id == actor.id,
            TeamMember.role.in_([TeamMemberRole.OWNER, TeamMemberRole.MANAGER]),
        )
        permitted_users = select(TeamMember.user_id).where(TeamMember.team_id.in_(managed_team_ids))
        conditions.append(User.id.in_(permitted_users))
    conditions += (
        [or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"))] if search else []
    )
    conditions += [User.role == role] if role else []
    conditions += [User.is_active == is_active] if is_active is not None else []
    total = (await session.exec(select(func.count()).select_from(User).where(*conditions))).one()
    rows = (
        await session.exec(
            select(User).where(*conditions).offset((page_number - 1) * limit).limit(limit)
        )
    ).all()
    public_rows = [UserPublic.model_validate(user).model_dump(by_alias=True) for user in rows]
    return page(public_rows, page_number, limit, total)


@router.get("/me", response_model=UserPublic)
async def own_profile(actor: CurrentUser) -> User:
    return actor


@router.patch("/me", response_model=UserPublic)
async def update_profile(data: ProfileUpdate, actor: CurrentUser, session: SessionDep) -> User:
    actor.name = data.name
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(409, "Não foi possível atualizar o usuário") from error
    await session.refresh(actor)
    return actor


@router.get("/{user_id}", response_model=UserPublic)
async def detail(
    user_id: UUID, session: SessionDep, actor: Annotated[User, Depends(require_manager_or_admin)]
) -> User:
    service = DomainService(session)
    await service.assert_user_access(user_id, actor)
    return await service.get(User, user_id, "Usuário")


@router.patch("/{user_id}", response_model=UserPublic)
async def update(
    user_id: UUID,
    data: UserUpdate,
    session: SessionDep,
    actor: Annotated[User, Depends(require_admin)],
) -> User:
    user = await DomainService(session).get(User, user_id, "Usuário")
    values = data.model_dump(exclude_unset=True)
    password = values.pop("password", None)
    apply_values(user, values)
    user.password_hash = hash_password(password) if password else user.password_hash
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise HTTPException(409, "Não foi possível atualizar o usuário") from error
    await session.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
async def deactivate(
    user_id: UUID, session: SessionDep, actor: Annotated[User, Depends(require_admin)]
) -> Response:
    user = await DomainService(session).get(User, user_id, "Usuário")
    user.is_active = False
    tokens = (
        await session.exec(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
            )
        )
    ).all()
    for token in tokens:
        token.revoked_at = datetime.now(UTC)
    await session.commit()
    return Response(status_code=204)
