from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDep, require_manager_or_admin
from app.models.entities import Project, ProjectMember, ProjectMemberRole, ProjectStatus, User
from app.schemas.domain import MemberInput, MemberUpdate, ProjectCreate, ProjectUpdate
from app.services.domain_service import DomainService, apply_values, page

router = APIRouter(prefix="/projects", tags=["Projetos"])


@router.post("", status_code=201)
async def create(
    data: ProjectCreate,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> dict[str, object]:
    service = DomainService(session)
    await service.assert_manage_team(data.team_id, actor)
    if data.manager_id is not None:
        await service.assert_active_team_member(data.team_id, data.manager_id)
    project = Project(**data.model_dump())
    session.add(project)
    await session.flush()
    session.add(
        ProjectMember(project_id=project.id, user_id=actor.id, role=ProjectMemberRole.MANAGER)
    )
    await session.commit()
    await session.refresh(project)
    return await service.project_view(project)


@router.get("")
async def list_projects(
    session: SessionDep,
    actor: CurrentUser,
    page_number: int = Query(1, alias="page", ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    status: ProjectStatus | None = None,
    team_id: UUID | None = Query(None, alias="teamId"),
    manager_id: UUID | None = Query(None, alias="managerId"),
) -> dict[str, object]:
    service = DomainService(session)
    ids = await service.accessible_team_ids(actor)
    c = [Project.is_archived.is_(False)]
    c += [Project.team_id.in_(ids)] if ids is not None else []
    c += [Project.name.ilike(f"%{search}%")] if search else []
    c += [Project.status == status] if status else []
    c += [Project.team_id == team_id] if team_id else []
    c += [Project.manager_id == manager_id] if manager_id else []
    total = (await session.exec(select(func.count()).select_from(Project).where(*c))).one()
    rows = (
        await session.exec(select(Project).where(*c).offset((page_number - 1) * limit).limit(limit))
    ).all()
    return page(await service.project_views(list(rows)), page_number, limit, total)


@router.get("/{project_id}")
async def detail(project_id: UUID, session: SessionDep, actor: CurrentUser) -> dict[str, object]:
    service = DomainService(session)
    obj = await service.get(Project, project_id, "Projeto")
    await service.assert_project_access(obj, actor)
    return await service.project_view(obj)


@router.patch("/{project_id}")
async def update(
    project_id: UUID,
    data: ProjectUpdate,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> dict[str, object]:
    service = DomainService(session)
    obj = await service.get(Project, project_id, "Projeto")
    await service.assert_project_access(obj, actor, True)
    values = data.model_dump(exclude_unset=True)
    if "manager_id" in values and values["manager_id"] is not None:
        await service.assert_active_team_member(obj.team_id, values["manager_id"])
    next_start = values.get("start_date", obj.start_date)
    next_due = values.get("due_date", obj.due_date)
    if next_start and next_due and next_due < next_start:
        from fastapi import HTTPException

        raise HTTPException(422, "dueDate must not be before startDate")
    apply_values(obj, values)
    obj.completed_at = datetime.now(UTC) if obj.status == ProjectStatus.COMPLETED else None
    await service.commit()
    return await service.project_view(obj)


@router.delete("/{project_id}", status_code=204)
async def remove(
    project_id: UUID, session: SessionDep, actor: Annotated[User, Depends(require_manager_or_admin)]
) -> Response:
    service = DomainService(session)
    obj = await service.get(Project, project_id, "Projeto")
    await service.assert_project_access(obj, actor, True)
    obj.is_archived = True
    await service.commit()
    return Response(status_code=204)


@router.post("/{project_id}/members", status_code=201)
async def add_member(
    project_id: UUID,
    data: MemberInput,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> dict[str, object]:
    service = DomainService(session)
    obj = await service.get(Project, project_id, "Projeto")
    await service.assert_project_access(obj, actor, True)
    user = await service.assert_active_team_member(obj.team_id, data.user_id)
    member = ProjectMember(project_id=obj.id, user_id=user.id, role=ProjectMemberRole(data.role))
    session.add(member)
    await service.commit()
    return {
        "userId": user.id,
        "role": member.role,
        "joinedAt": member.joined_at,
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }


@router.patch("/{project_id}/members/{user_id}")
async def update_member(
    project_id: UUID,
    user_id: UUID,
    data: MemberUpdate,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> dict[str, object]:
    service = DomainService(session)
    obj = await service.get(Project, project_id, "Projeto")
    await service.assert_project_access(obj, actor, True)
    member = await session.get(ProjectMember, (project_id, user_id))
    if not member:
        from app.services.domain_service import not_found

        raise not_found("Membro")
    member.role = ProjectMemberRole(data.role)
    await service.commit()
    user = await service.get(User, user_id, "Usuário")
    return {
        "userId": user.id,
        "role": member.role,
        "joinedAt": member.joined_at,
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }


@router.delete("/{project_id}/members/{user_id}", status_code=204)
async def remove_member(
    project_id: UUID,
    user_id: UUID,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> Response:
    service = DomainService(session)
    obj = await service.get(Project, project_id, "Projeto")
    await service.assert_project_access(obj, actor, True)
    member = await session.get(ProjectMember, (project_id, user_id))
    if member:
        await session.delete(member)
        await service.commit()
    return Response(status_code=204)
