from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Query
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDep
from app.models.entities import (
    Project,
    ProjectStatus,
    Task,
    TaskPriority,
    TaskStatus,
    TeamMember,
    TimeLog,
    User,
)
from app.services.domain_service import DomainService
from app.services.workload_service import WorkloadService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


async def build(
    session: SessionDep,
    actor: User,
    start: datetime | None,
    end: datetime | None,
    team_id: UUID | None,
) -> dict[str, object]:
    service = DomainService(session)
    ids = await service.accessible_team_ids(actor)
    if team_id is not None:
        await service.assert_team_access(team_id, actor)
        ids = [team_id]
    pc = []
    tc = []
    if ids is not None:
        pc = [Project.team_id.in_(ids)]
        tc = [Task.project_id.in_(select(Project.id).where(Project.team_id.in_(ids)))]
    projects = list(
        (await session.exec(select(Project).where(*pc, Project.is_archived.is_(False)))).all()
    )
    tasks = list((await session.exec(select(Task).where(*tc))).all())
    start = start or datetime.now(UTC) - timedelta(days=29)
    end = end or datetime.now(UTC)
    logs = list(
        (
            await session.exec(
                select(TimeLog).where(
                    TimeLog.task_id.in_(select(Task.id).where(*tc)),
                    TimeLog.started_at >= start,
                    TimeLog.started_at <= end,
                )
            )
        ).all()
    )
    user_query = select(User).where(User.is_active.is_(True))
    if actor.role.value == "COLABORADOR":
        user_query = user_query.where(User.id == actor.id)
    users = (await session.exec(user_query)).all()
    workloads = [
        await WorkloadService(session).calculate(x.id)
        for x in users
        if ids is None
        or (
            await session.exec(
                select(TeamMember).where(TeamMember.user_id == x.id, TeamMember.team_id.in_(ids))
            )
        ).first()
    ]
    done = sum(x.status == TaskStatus.DONE for x in tasks)
    overdue = sum(
        bool(
            x.due_date
            and x.due_date < datetime.now(UTC)
            and x.status not in [TaskStatus.DONE, TaskStatus.CANCELLED]
        )
        for x in tasks
    )
    logged = sum(x.duration_minutes for x in logs) / 60
    summary = {
        "activeProjects": sum(x.status == ProjectStatus.ACTIVE for x in projects),
        "totalProjects": len(projects),
        "totalTasks": len(tasks),
        "completedTasks": done,
        "overdueTasks": overdue,
        "completionPercentage": round(done / len(tasks) * 100, 2) if tasks else 0,
        "loggedHours": logged,
        "overtimeHours": sum(float(x["overtimeHours"]) for x in workloads),
        "overloadedUsers": sum(bool(x["overloaded"]) for x in workloads),
    }
    task_charts = {
        "byStatus": [
            {"status": x.value, "value": sum(t.status == x for t in tasks)}
            for x in TaskStatus
            if x != TaskStatus.CANCELLED
        ],
        "byPriority": [
            {"priority": x.value, "value": sum(t.priority == x for t in tasks)}
            for x in TaskPriority
        ],
    }
    hours = []
    productivity = []
    for offset in range((end.date() - start.date()).days + 1):
        day = start.date() + timedelta(days=offset)
        hours.append(
            {
                "date": day.isoformat(),
                "hours": sum(x.duration_minutes for x in logs if x.started_at.date() == day) / 60,
            }
        )
        productivity.append(
            {
                "date": day.isoformat(),
                "createdTasks": sum(x.created_at.date() == day for x in tasks),
                "completedTasks": sum(
                    bool(x.completed_at and x.completed_at.date() == day) for x in tasks
                ),
            }
        )
    return {
        "summary": summary,
        "taskCharts": task_charts,
        "hoursChart": hours,
        "productivityChart": productivity,
        "workload": workloads,
    }


@router.get("")
async def dashboard(
    session: SessionDep,
    actor: CurrentUser,
    start_date: datetime | None = Query(None, alias="startDate"),
    end_date: datetime | None = Query(None, alias="endDate"),
    team_id: UUID | None = Query(None, alias="teamId"),
) -> dict[str, object]:
    return await build(session, actor, start_date, end_date, team_id)


@router.get("/summary")
async def summary(session: SessionDep, actor: CurrentUser) -> dict[str, object]:
    return (await build(session, actor, None, None, None))["summary"]


@router.get("/charts/tasks")
async def task_charts(session: SessionDep, actor: CurrentUser) -> dict[str, object]:
    return (await build(session, actor, None, None, None))["taskCharts"]


@router.get("/charts/hours")
async def hours(session: SessionDep, actor: CurrentUser) -> object:
    return (await build(session, actor, None, None, None))["hoursChart"]


@router.get("/charts/productivity")
async def productivity(session: SessionDep, actor: CurrentUser) -> object:
    return (await build(session, actor, None, None, None))["productivityChart"]


@router.get("/indicators/workload")
async def workload(session: SessionDep, actor: CurrentUser) -> object:
    return (await build(session, actor, None, None, None))["workload"]
