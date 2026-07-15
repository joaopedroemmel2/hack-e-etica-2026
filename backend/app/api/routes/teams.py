from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDep, require_manager_or_admin
from app.models.entities import Team, TeamMember, TeamMemberRole, User
from app.schemas.domain import MemberInput, MemberUpdate, TeamCreate, TeamUpdate
from app.services.domain_service import DomainService, apply_values, page

router = APIRouter(prefix="/teams", tags=["Equipes"])


@router.post("", status_code=201)
async def create(
    data: TeamCreate, session: SessionDep, actor: Annotated[User, Depends(require_manager_or_admin)]
) -> dict[str, object]:
    service = DomainService(session)
    manager = None
    if data.manager_id is not None:
        manager = await service.get(User, data.manager_id, "Usuário")
        if not manager.is_active:
            raise HTTPException(409, "Usuário inativo")
    team = Team(**data.model_dump(), created_by_id=actor.id)
    session.add(team)
    await session.flush()
    session.add(TeamMember(team_id=team.id, user_id=actor.id, role=TeamMemberRole.OWNER))
    if manager is not None and manager.id != actor.id:
        session.add(TeamMember(team_id=team.id, user_id=manager.id, role=TeamMemberRole.MANAGER))
    await session.commit()
    await session.refresh(team)
    return await DomainService(session).team_view(team)


@router.get("")
async def list_teams(
    session: SessionDep,
    actor: CurrentUser,
    page_number: int = Query(1, alias="page", ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
) -> dict[str, object]:
    service = DomainService(session)
    ids = await service.accessible_team_ids(actor)
    conditions = [Team.is_active.is_(True)]
    conditions += [Team.id.in_(ids)] if ids is not None else []
    conditions += [Team.name.ilike(f"%{search}%")] if search else []
    total = (await session.exec(select(func.count()).select_from(Team).where(*conditions))).one()
    teams = (
        await session.exec(
            select(Team).where(*conditions).offset((page_number - 1) * limit).limit(limit)
        )
    ).all()
    return page([await service.team_view(t) for t in teams], page_number, limit, total)


@router.get("/{team_id}")
async def detail(team_id: UUID, session: SessionDep, actor: CurrentUser) -> dict[str, object]:
    service = DomainService(session)
    team = await service.get(Team, team_id, "Equipe")
    ids = await service.accessible_team_ids(actor)
    if ids is not None and team.id not in ids:
        from fastapi import HTTPException

        raise HTTPException(403, "Acesso negado")
    return await service.team_view(team)


@router.patch("/{team_id}")
async def update(
    team_id: UUID,
    data: TeamUpdate,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> dict[str, object]:
    service = DomainService(session)
    await service.assert_manage_team(team_id, actor)
    team = await service.get(Team, team_id, "Equipe")
    values = data.model_dump(exclude_unset=True)
    if "manager_id" in values and values["manager_id"] is not None:
        manager = await service.get(User, values["manager_id"], "Usuário")
        if not manager.is_active:
            raise HTTPException(409, "Usuário inativo")
        membership = await session.get(TeamMember, (team_id, manager.id))
        if membership is None:
            session.add(
                TeamMember(team_id=team_id, user_id=manager.id, role=TeamMemberRole.MANAGER)
            )
        elif membership.role != TeamMemberRole.OWNER:
            membership.role = TeamMemberRole.MANAGER
    apply_values(team, values)
    await service.commit()
    return await service.team_view(team)


@router.delete("/{team_id}", status_code=204)
async def remove(
    team_id: UUID, session: SessionDep, actor: Annotated[User, Depends(require_manager_or_admin)]
) -> Response:
    service = DomainService(session)
    await service.assert_manage_team(team_id, actor)
    team = await service.get(Team, team_id, "Equipe")
    team.is_active = False
    await service.commit()
    return Response(status_code=204)


@router.post("/{team_id}/members", status_code=201)
async def add_member(
    team_id: UUID,
    data: MemberInput,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> dict[str, object]:
    service = DomainService(session)
    await service.assert_manage_team(team_id, actor)
    user = await service.get(User, data.user_id, "Usuário")
    if not user.is_active:
        raise HTTPException(409, "Usuário inativo")
    if await session.get(TeamMember, (team_id, user.id)) is not None:
        raise HTTPException(409, "Usuário já pertence à equipe")
    member = TeamMember(team_id=team_id, user_id=user.id, role=TeamMemberRole(data.role))
    session.add(member)
    await service.commit()
    return {
        "userId": user.id,
        "role": member.role,
        "joinedAt": member.joined_at,
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }


@router.patch("/{team_id}/members/{user_id}")
async def update_member(
    team_id: UUID,
    user_id: UUID,
    data: MemberUpdate,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> dict[str, object]:
    service = DomainService(session)
    await service.assert_manage_team(team_id, actor)
    member = await session.get(TeamMember, (team_id, user_id))
    if not member:
        from app.services.domain_service import not_found

        raise not_found("Membro")
    if member.role == TeamMemberRole.OWNER:
        raise HTTPException(409, "O proprietário da equipe não pode ter o papel alterado")
    member.role = TeamMemberRole(data.role)
    await service.commit()
    user = await service.get(User, user_id, "Usuário")
    return {
        "userId": user.id,
        "role": member.role,
        "joinedAt": member.joined_at,
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }


@router.delete("/{team_id}/members/{user_id}", status_code=204)
async def remove_member(
    team_id: UUID,
    user_id: UUID,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> Response:
    service = DomainService(session)
    await service.assert_manage_team(team_id, actor)
    member = await session.get(TeamMember, (team_id, user_id))
    if member and member.role == TeamMemberRole.OWNER:
        raise HTTPException(409, "O proprietário da equipe não pode ser removido")
    if member:
        await session.delete(member)
        await service.commit()
    return Response(status_code=204)
