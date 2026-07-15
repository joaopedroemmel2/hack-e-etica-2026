from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDep, require_manager_or_admin
from app.models.entities import Notification, NotificationType, Team, TeamMember, User
from app.services.domain_service import DomainService
from app.services.workload_service import WorkloadService

router = APIRouter(prefix="/workload", tags=["Carga de trabalho"])


@router.get("/me")
async def mine(
    session: SessionDep, actor: CurrentUser, week: datetime | None = None
) -> dict[str, object]:
    return await WorkloadService(session).calculate(actor.id, week)


@router.get("/users/{user_id}")
async def user_workload(
    user_id: UUID,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
    week: datetime | None = None,
) -> dict[str, object]:
    await DomainService(session).assert_user_access(user_id, actor)
    return await WorkloadService(session).calculate(user_id, week)


async def team_data(
    team_id: UUID, session: SessionDep, actor: User, week: datetime | None
) -> dict[str, object]:
    service = DomainService(session)
    await service.assert_manage_team(team_id, actor)
    team = await service.get(Team, team_id, "Equipe")
    ids = (
        await session.exec(select(TeamMember.user_id).where(TeamMember.team_id == team_id))
    ).all()
    users = [await WorkloadService(session).calculate(x, week) for x in ids]
    capacity = sum(float(x["capacityHours"]) for x in users)
    committed = sum(float(x["committedHours"]) for x in users)
    return {
        "team": {"id": team.id, "name": team.name},
        "period": users[0]["period"] if users else {},
        "users": users,
        "summary": {
            "totalCapacityHours": capacity,
            "totalCommittedHours": committed,
            "averageUtilizationPercentage": round(committed / capacity * 100, 2) if capacity else 0,
            "overloadedUsers": sum(bool(x["overloaded"]) for x in users),
        },
    }


@router.get("/teams/{team_id}")
async def team_workload(
    team_id: UUID,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
    week: datetime | None = None,
) -> dict[str, object]:
    return await team_data(team_id, session, actor, week)


@router.post("/teams/{team_id}/evaluate", status_code=201)
async def evaluate(
    team_id: UUID,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
    week: datetime | None = None,
) -> dict[str, object]:
    workload = await team_data(team_id, session, actor, week)
    alerts = []
    for item in workload["users"]:
        if item["overloaded"]:
            message = f"Ocupação detectada em {item['utilizationPercentage']}%"
            note = Notification(
                user_id=item["user"]["id"],
                team_id=team_id,
                type=NotificationType.WORKLOAD_WARNING,
                title="Alerta de sobrecarga",
                message=message,
                metadata_={"utilizationPercentage": item["utilizationPercentage"]},
            )
            session.add(note)
            alerts.append(note)
    await session.commit()
    return {"workload": workload, "alerts": alerts}


@router.get("/alerts/me")
async def alerts(session: SessionDep, actor: CurrentUser) -> list[Notification]:
    return list(
        (
            await session.exec(
                select(Notification).where(
                    Notification.user_id == actor.id,
                    Notification.type == NotificationType.WORKLOAD_WARNING,
                )
            )
        ).all()
    )
