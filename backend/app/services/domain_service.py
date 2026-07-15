from math import ceil
from typing import Any, TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.entities import (
    Project,
    Role,
    Task,
    Team,
    TeamMember,
    TeamMemberRole,
    TimeLog,
    User,
    utcnow,
)

M = TypeVar("M", bound=SQLModel)


def camelize(value: Any) -> Any:
    if isinstance(value, SQLModel):
        return camelize(value.model_dump())
    if isinstance(value, dict):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            parts = key.rstrip("_").split("_")
            converted[parts[0] + "".join(part.title() for part in parts[1:])] = camelize(item)
        return converted
    if isinstance(value, (list, tuple)):
        return [camelize(item) for item in value]
    return value


def not_found(label: str = "Recurso") -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"{label} não encontrado")


def page(data: list[Any], current: int, limit: int, total: int) -> dict[str, Any]:
    return {
        "data": camelize(data),
        "meta": {
            "page": current,
            "limit": limit,
            "total": total,
            "totalPages": ceil(total / limit) if total else 0,
        },
    }


class DomainService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, model: type[M], object_id: UUID, label: str) -> M:
        obj = await self.session.get(model, object_id)
        if not obj:
            raise not_found(label)
        return obj

    async def can_manage_team(self, team_id: UUID, actor: User) -> bool:
        if actor.role == Role.ADMIN:
            return True
        return (
            await self.session.exec(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == actor.id,
                    TeamMember.role.in_([TeamMemberRole.OWNER, TeamMemberRole.MANAGER]),
                )
            )
        ).first() is not None

    async def assert_manage_team(self, team_id: UUID, actor: User) -> None:
        if not await self.can_manage_team(team_id, actor):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado")

    async def assert_team_access(self, team_id: UUID, actor: User) -> None:
        if actor.role == Role.ADMIN:
            return
        membership = (
            await self.session.exec(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == actor.id,
                )
            )
        ).first()
        if membership is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado")

    async def assert_user_access(self, user_id: UUID, actor: User) -> None:
        if actor.role == Role.ADMIN or actor.id == user_id:
            return
        if actor.role != Role.GESTOR:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado")
        managed_team_ids = select(TeamMember.team_id).where(
            TeamMember.user_id == actor.id,
            TeamMember.role.in_([TeamMemberRole.OWNER, TeamMemberRole.MANAGER]),
        )
        target_membership = (
            await self.session.exec(
                select(TeamMember).where(
                    TeamMember.user_id == user_id,
                    TeamMember.team_id.in_(managed_team_ids),
                )
            )
        ).first()
        if target_membership is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado")

    async def assert_active_team_member(self, team_id: UUID, user_id: UUID) -> User:
        user = await self.get(User, user_id, "Usuário")
        if not user.is_active:
            raise HTTPException(status.HTTP_409_CONFLICT, "Usuário inativo")
        membership = await self.session.get(TeamMember, (team_id, user_id))
        if membership is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Usuário não pertence à equipe")
        return user

    async def accessible_team_ids(self, actor: User) -> list[UUID] | None:
        if actor.role == Role.ADMIN:
            return None
        return list(
            (
                await self.session.exec(
                    select(TeamMember.team_id).where(TeamMember.user_id == actor.id)
                )
            ).all()
        )

    async def team_view(self, team: Team) -> dict[str, Any]:
        rows = (
            await self.session.exec(
                select(TeamMember, User)
                .join(User, User.id == TeamMember.user_id)
                .where(TeamMember.team_id == team.id)
            )
        ).all()
        result = team.model_dump()
        result["members"] = [
            {
                "userId": member.user_id,
                "role": member.role,
                "joinedAt": member.joined_at,
                "user": {"id": user.id, "name": user.name, "email": user.email},
            }
            for member, user in rows
        ]
        return camelize(result)

    async def project_view(self, project: Project) -> dict[str, Any]:
        team = await self.get(Team, project.team_id, "Equipe")
        manager = await self.session.get(User, project.manager_id) if project.manager_id else None
        count = (
            await self.session.exec(
                select(func.count()).select_from(Task).where(Task.project_id == project.id)
            )
        ).one()
        result = project.model_dump()
        result.update(
            {
                "team": {"id": team.id, "name": team.name},
                "manager": (
                    {"id": manager.id, "name": manager.name, "email": manager.email}
                    if manager
                    else None
                ),
                "members": [],
                "tasksCount": count,
            }
        )
        return camelize(result)

    async def project_views(self, projects: list[Project]) -> list[dict[str, Any]]:
        if not projects:
            return []
        team_ids = {item.team_id for item in projects}
        manager_ids = {item.manager_id for item in projects if item.manager_id is not None}
        project_ids = [item.id for item in projects]
        teams = {
            item.id: item
            for item in (await self.session.exec(select(Team).where(Team.id.in_(team_ids)))).all()
        }
        managers = {
            item.id: item
            for item in (
                await self.session.exec(select(User).where(User.id.in_(manager_ids)))
            ).all()
        }
        counts = dict(
            (
                await self.session.exec(
                    select(Task.project_id, func.count(Task.id))
                    .where(Task.project_id.in_(project_ids))
                    .group_by(Task.project_id)
                )
            ).all()
        )
        result = []
        for project in projects:
            team = teams[project.team_id]
            manager = managers.get(project.manager_id)
            value = project.model_dump()
            value.update(
                {
                    "team": {"id": team.id, "name": team.name},
                    "manager": (
                        {"id": manager.id, "name": manager.name, "email": manager.email}
                        if manager
                        else None
                    ),
                    "members": [],
                    "tasksCount": counts.get(project.id, 0),
                }
            )
            result.append(camelize(value))
        return camelize(result)

    async def task_view(self, task: Task) -> dict[str, Any]:
        project = await self.get(Project, task.project_id, "Projeto")
        assignee = await self.session.get(User, task.assignee_id) if task.assignee_id else None
        logged = (
            await self.session.exec(
                select(func.coalesce(func.sum(TimeLog.duration_minutes), 0)).where(
                    TimeLog.task_id == task.id
                )
            )
        ).one()
        result = task.model_dump()
        result.update(
            {
                "loggedMinutes": logged,
                "project": {"id": project.id, "name": project.name, "teamId": project.team_id},
                "assignee": (
                    {"id": assignee.id, "name": assignee.name, "email": assignee.email}
                    if assignee
                    else None
                ),
            }
        )
        return camelize(result)

    async def task_views(self, tasks: list[Task]) -> list[dict[str, Any]]:
        if not tasks:
            return []
        project_ids = {item.project_id for item in tasks}
        assignee_ids = {item.assignee_id for item in tasks if item.assignee_id is not None}
        task_ids = [item.id for item in tasks]
        projects = {
            item.id: item
            for item in (
                await self.session.exec(select(Project).where(Project.id.in_(project_ids)))
            ).all()
        }
        assignees = {
            item.id: item
            for item in (
                await self.session.exec(select(User).where(User.id.in_(assignee_ids)))
            ).all()
        }
        logged = dict(
            (
                await self.session.exec(
                    select(TimeLog.task_id, func.coalesce(func.sum(TimeLog.duration_minutes), 0))
                    .where(TimeLog.task_id.in_(task_ids))
                    .group_by(TimeLog.task_id)
                )
            ).all()
        )
        result = []
        for task in tasks:
            project = projects[task.project_id]
            assignee = assignees.get(task.assignee_id)
            value = task.model_dump()
            value.update(
                {
                    "loggedMinutes": logged.get(task.id, 0),
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "teamId": project.team_id,
                    },
                    "assignee": (
                        {"id": assignee.id, "name": assignee.name, "email": assignee.email}
                        if assignee
                        else None
                    ),
                }
            )
            result.append(camelize(value))
        return result

    async def assert_project_access(
        self, project: Project, actor: User, manage: bool = False
    ) -> None:
        if manage:
            await self.assert_manage_team(project.team_id, actor)
            return
        ids = await self.accessible_team_ids(actor)
        if ids is not None and project.team_id not in ids:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso negado")

    async def commit(self) -> None:
        await self.session.commit()


def apply_values(obj: SQLModel, values: dict[str, Any]) -> None:
    for key, value in values.items():
        setattr(obj, key, value)
    if hasattr(obj, "updated_at"):
        obj.updated_at = utcnow()
