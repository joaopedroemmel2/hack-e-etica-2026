from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import func
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDep
from app.models.entities import Project, Role, Task, TeamMember, TeamMemberRole, TimeLog, User
from app.schemas.domain import TimeLogCreate, TimeLogUpdate
from app.services.domain_service import DomainService, apply_values, camelize, page

router = APIRouter(prefix="/time-logs", tags=["Apontamentos"])


async def allowed(log: TimeLog, actor: User, session: SessionDep) -> None:
    if actor.role != Role.ADMIN and log.user_id != actor.id:
        raise HTTPException(403, "Acesso negado")


@router.post("", status_code=201)
async def create(data: TimeLogCreate, session: SessionDep, actor: CurrentUser) -> dict[str, object]:
    service = DomainService(session)
    task = await service.get(Task, data.task_id, "Tarefa")
    project = await service.get(Project, task.project_id, "Projeto")
    await service.assert_project_access(project, actor)
    if actor.role == Role.COLABORADOR and task.assignee_id != actor.id:
        raise HTTPException(403, "Acesso negado")
    log = TimeLog(**data.model_dump(), user_id=actor.id)
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return camelize(log)


@router.get("")
async def listing(
    session: SessionDep,
    actor: CurrentUser,
    page_number: int = Query(1, alias="page", ge=1),
    limit: int = Query(20, ge=1, le=100),
    task_id: UUID | None = Query(None, alias="taskId"),
    user_id: UUID | None = Query(None, alias="userId"),
    start_date: datetime | None = Query(None, alias="startDate"),
    end_date: datetime | None = Query(None, alias="endDate"),
) -> dict[str, object]:
    c = []
    c += [TimeLog.user_id == actor.id] if actor.role == Role.COLABORADOR else []
    if actor.role == Role.GESTOR:
        managed_teams = select(TeamMember.team_id).where(
            TeamMember.user_id == actor.id,
            TeamMember.role.in_([TeamMemberRole.OWNER, TeamMemberRole.MANAGER]),
        )
        managed_tasks = (
            select(Task.id)
            .join(Project, Project.id == Task.project_id)
            .where(Project.team_id.in_(managed_teams))
        )
        c.append(TimeLog.task_id.in_(managed_tasks))
    c += [TimeLog.task_id == task_id] if task_id else []
    c += [TimeLog.user_id == user_id] if user_id else []
    c += [TimeLog.started_at >= start_date] if start_date else []
    c += [TimeLog.started_at <= end_date] if end_date else []
    total = (await session.exec(select(func.count()).select_from(TimeLog).where(*c))).one()
    rows = (
        await session.exec(select(TimeLog).where(*c).offset((page_number - 1) * limit).limit(limit))
    ).all()
    return page(rows, page_number, limit, total)


@router.patch("/{log_id}")
async def update(
    log_id: UUID, data: TimeLogUpdate, session: SessionDep, actor: CurrentUser
) -> dict[str, object]:
    service = DomainService(session)
    log = await service.get(TimeLog, log_id, "Apontamento")
    await allowed(log, actor, session)
    apply_values(log, data.model_dump(exclude_unset=True))
    await service.commit()
    return camelize(log)


@router.delete("/{log_id}", status_code=204)
async def remove(log_id: UUID, session: SessionDep, actor: CurrentUser) -> Response:
    service = DomainService(session)
    log = await service.get(TimeLog, log_id, "Apontamento")
    await allowed(log, actor, session)
    await session.delete(log)
    await service.commit()
    return Response(status_code=204)
