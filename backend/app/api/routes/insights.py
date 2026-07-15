from datetime import UTC, datetime
from typing import Annotated, Protocol
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import select

from app.api.dependencies import SessionDep, require_manager_or_admin
from app.models.entities import (
    Insight,
    InsightCategory,
    InsightSeverity,
    InsightStatus,
    TeamMember,
    User,
)
from app.schemas.domain import AnalyzeOperations, InsightStatusUpdate
from app.services.domain_service import DomainService, camelize, page
from app.services.workload_service import WorkloadService

router = APIRouter(tags=["Insights"])


class InsightProvider(Protocol):
    async def generate(self, context: dict[str, object]) -> list[dict[str, object]]: ...


class RulesProvider:
    async def generate(self, context: dict[str, object]) -> list[dict[str, object]]:
        return []


@router.post("/ai/analyze", status_code=201)
async def analyze(
    data: AnalyzeOperations,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> dict[str, object]:
    team_id = data.team_id
    service = DomainService(session)
    await service.assert_manage_team(team_id, actor)
    ids = (
        await session.exec(select(TeamMember.user_id).where(TeamMember.team_id == team_id))
    ).all()
    workloads = [await WorkloadService(session).calculate(x) for x in ids]
    insights = []
    for load in workloads:
        if load["overloaded"]:
            insight = Insight(
                team_id=team_id,
                user_id=load["user"]["id"],
                category=InsightCategory.WORKLOAD,
                severity=InsightSeverity.CRITICAL
                if load["level"] == "CRITICAL"
                else InsightSeverity.WARNING,
                title="Sobrecarga detectada",
                summary=f"Ocupação de {load['utilizationPercentage']}%",
                recommendation="Redistribua tarefas entre os membros da equipe.",
                evidence={"workload": load},
            )
            session.add(insight)
            insights.append(insight)
    await session.commit()
    return camelize(
        {
            "context": {"teamId": team_id, "workload": workloads},
            "insights": insights,
            "generation": {
                "provider": "rules",
                "model": None,
                "usedModel": False,
                "error": None,
            },
        }
    )


@router.get("/ai/insights")
async def listing(
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
    page_number: int = Query(1, alias="page", ge=1),
    limit: int = Query(20, ge=1, le=100),
    team_id: UUID | None = Query(None, alias="teamId"),
    category: InsightCategory | None = None,
    severity: InsightSeverity | None = None,
    status: InsightStatus | None = None,
) -> dict[str, object]:
    c = []
    if actor.role.value == "GESTOR":
        accessible = await DomainService(session).accessible_team_ids(actor)
        c.append(Insight.team_id.in_(accessible or []))
    c += [Insight.team_id == team_id] if team_id else []
    c += [Insight.category == category] if category else []
    c += [Insight.severity == severity] if severity else []
    c += [Insight.status == status] if status else []
    total = (await session.exec(select(func.count()).select_from(Insight).where(*c))).one()
    rows = (
        await session.exec(select(Insight).where(*c).offset((page_number - 1) * limit).limit(limit))
    ).all()
    return page(rows, page_number, limit, total)


@router.get("/ai/insights/{insight_id}")
async def detail(
    insight_id: UUID, session: SessionDep, actor: Annotated[User, Depends(require_manager_or_admin)]
) -> dict[str, object]:
    service = DomainService(session)
    item = await service.get(Insight, insight_id, "Insight")
    if item.team_id is None and actor.role.value != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado")
    if item.team_id is not None:
        await service.assert_team_access(item.team_id, actor)
    return camelize(item)


@router.patch("/ai/insights/{insight_id}/status")
async def update(
    insight_id: UUID,
    data: InsightStatusUpdate,
    session: SessionDep,
    actor: Annotated[User, Depends(require_manager_or_admin)],
) -> dict[str, object]:
    service = DomainService(session)
    item = await service.get(Insight, insight_id, "Insight")
    if item.team_id is None and actor.role.value != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado")
    if item.team_id is not None:
        await service.assert_manage_team(item.team_id, actor)
    item.status = InsightStatus(data.status)
    item.resolved_at = (
        datetime.now(UTC)
        if item.status in [InsightStatus.RESOLVED, InsightStatus.DISMISSED]
        else None
    )
    await session.commit()
    return camelize(item)
