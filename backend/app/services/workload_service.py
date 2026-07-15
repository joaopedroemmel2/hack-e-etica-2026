from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models.entities import Task, TaskStatus, TimeLog, User


class WorkloadService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate(self, user_id: UUID, week: datetime | None = None) -> dict[str, object]:
        user = await self.session.get(User, user_id)
        if not user:
            from app.services.domain_service import not_found

            raise not_found("Usuário")
        point = week or datetime.now(UTC)
        start = (point - timedelta(days=point.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)
        tasks = (
            await self.session.exec(
                select(Task).where(
                    Task.assignee_id == user_id,
                    Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
                )
            )
        ).all()
        estimated = sum((x.estimated_hours or Decimal(0) for x in tasks), Decimal(0))
        task_logged_minutes = (
            await self.session.exec(
                select(func.coalesce(func.sum(TimeLog.duration_minutes), 0)).where(
                    TimeLog.user_id == user_id,
                    TimeLog.task_id.in_([task.id for task in tasks]),
                )
            )
        ).one()
        logged = (
            Decimal(
                (
                    await self.session.exec(
                        select(func.coalesce(func.sum(TimeLog.duration_minutes), 0)).where(
                            TimeLog.user_id == user_id,
                            TimeLog.started_at >= start,
                            TimeLog.started_at < end,
                        )
                    )
                ).one()
            )
            / 60
        )
        remaining = max(Decimal(0), estimated - Decimal(task_logged_minutes) / 60)
        committed = remaining + logged
        capacity = user.weekly_capacity_hours
        utilization = float(committed / capacity * 100) if capacity else 0
        overdue = sum(1 for x in tasks if x.due_date and x.due_date < datetime.now(UTC))
        level = (
            "NORMAL"
            if utilization < settings.workload_attention_percent
            else "ATTENTION"
            if utilization < settings.workload_overloaded_percent
            else "OVERLOADED"
            if utilization < settings.workload_critical_percent
            else "CRITICAL"
        )
        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "period": {"start": start, "end": end},
            "capacityHours": float(capacity),
            "taskCount": len(tasks),
            "activeTasks": len(tasks),
            "overdueTasks": overdue,
            "estimatedHours": float(estimated),
            "remainingHours": float(remaining),
            "loggedHours": float(logged),
            "committedHours": float(committed),
            "utilizationPercentage": round(utilization, 2),
            "overtimeHours": max(0, float(committed - capacity)),
            "overloaded": utilization >= settings.workload_overloaded_percent,
            "level": level,
        }
