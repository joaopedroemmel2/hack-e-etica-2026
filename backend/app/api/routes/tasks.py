from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDep, require_manager_or_admin
from app.models.entities import (
    Notification,
    NotificationType,
    Project,
    Role,
    Task,
    TaskPriority,
    TaskStatus,
    User,
)
from app.schemas.domain import TaskCreate, TaskStatusUpdate, TaskUpdate
from app.services.domain_service import DomainService, apply_values, page

router = APIRouter(prefix="/tasks", tags=["Tarefas"])


async def access(task: Task, actor: User, service: DomainService, manage: bool = False) -> Project:
    project = await service.get(Project, task.project_id, "Projeto")
    await service.assert_project_access(project, actor, manage)
    return project


@router.post("", status_code=201)
async def create(
    data: TaskCreate, session: SessionDep, actor: Annotated[User, Depends(require_manager_or_admin)]
) -> dict[str, object]:
    service = DomainService(session)
    project = await service.get(Project, data.project_id, "Projeto")
    await service.assert_project_access(project, actor, True)
    if project.is_archived:
        raise HTTPException(409, "Projeto arquivado")
    if data.assignee_id is not None:
        await service.assert_active_team_member(project.team_id, data.assignee_id)
    task = Task(**data.model_dump(), created_by_id=actor.id)
    session.add(task)
    if task.assignee_id:
        session.add(
            Notification(
                user_id=task.assignee_id,
                project_id=project.id,
                task_id=task.id,
                type=NotificationType.TASK_ASSIGNED,
                title="Nova tarefa atribuída",
                message=f"A tarefa {task.title} foi atribuída a você.",
            )
        )
    await session.commit()
    await session.refresh(task)
    return await service.task_view(task)


@router.get("")
async def list_tasks(
    session: SessionDep,
    actor: CurrentUser,
    page_number: int = Query(1, alias="page", ge=1),
    limit: int = Query(20, ge=1, le=100),
    project_id: UUID | None = Query(None, alias="projectId"),
    assignee_id: UUID | None = Query(None, alias="assigneeId"),
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    overdue: bool | None = None,
) -> dict[str, object]:
    service = DomainService(session)
    ids = await service.accessible_team_ids(actor)
    c = []
    if ids is not None:
        c.append(
            Task.project_id.in_(
                select(Project.id).where(Project.team_id.in_(ids), Project.is_archived.is_(False))
            )
        )
    else:
        c.append(Task.project_id.in_(select(Project.id).where(Project.is_archived.is_(False))))
    if actor.role == Role.COLABORADOR:
        c.append(Task.assignee_id == actor.id)
    c += [Task.project_id == project_id] if project_id else []
    c += [Task.assignee_id == assignee_id] if assignee_id else []
    c += [Task.status == status] if status else []
    c += [Task.priority == priority] if priority else []
    if overdue:
        c += [
            Task.due_date < datetime.now(UTC),
            Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
        ]
    total = (await session.exec(select(func.count()).select_from(Task).where(*c))).one()
    rows = (
        await session.exec(select(Task).where(*c).offset((page_number - 1) * limit).limit(limit))
    ).all()
    return page(await service.task_views(list(rows)), page_number, limit, total)


@router.get("/{task_id}")
async def detail(task_id: UUID, session: SessionDep, actor: CurrentUser) -> dict[str, object]:
    service = DomainService(session)
    task = await service.get(Task, task_id, "Tarefa")
    await access(task, actor, service)
    if actor.role == Role.COLABORADOR and task.assignee_id != actor.id:
        raise HTTPException(403, "Acesso negado")
    return await service.task_view(task)


@router.patch("/{task_id}")
async def update(
    task_id: UUID,
    data: TaskUpdate,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> dict[str, object]:
    service = DomainService(session)
    task = await service.get(Task, task_id, "Tarefa")
    project = await access(task, actor, service, True)
    values = data.model_dump(exclude_unset=True)
    if "assignee_id" in values and values["assignee_id"] is not None:
        await service.assert_active_team_member(project.team_id, values["assignee_id"])
    apply_values(task, values)
    task.completed_at = datetime.now(UTC) if task.status == TaskStatus.DONE else None
    await service.commit()
    return await service.task_view(task)


@router.patch("/{task_id}/status")
async def update_status(
    task_id: UUID, data: TaskStatusUpdate, session: SessionDep, actor: CurrentUser
) -> dict[str, object]:
    service = DomainService(session)
    task = await service.get(Task, task_id, "Tarefa")
    await access(task, actor, service)
    if actor.role.value == "COLABORADOR" and task.assignee_id != actor.id:
        raise HTTPException(403, "Acesso negado")
    task.status = data.status
    task.completed_at = datetime.now(UTC) if data.status == TaskStatus.DONE else None
    await service.commit()
    return await service.task_view(task)


@router.delete("/{task_id}", status_code=204)
async def remove(
    task_id: UUID, session: SessionDep, actor: Annotated[User, Depends(require_manager_or_admin)]
) -> Response:
    service = DomainService(session)
    task = await service.get(Task, task_id, "Tarefa")
    await access(task, actor, service, True)
    await session.delete(task)
    await service.commit()
    return Response(status_code=204)
