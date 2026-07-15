from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field, model_validator

from app.models.entities import ProjectStatus, Role, TaskPriority, TaskStatus
from app.schemas.common import APIModel, UserBrief


class UserCreate(APIModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.COLABORADOR
    weekly_capacity_hours: Decimal = Field(default=Decimal("40"), ge=1, le=168)


class UserUpdate(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: Role | None = None
    is_active: bool | None = None
    weekly_capacity_hours: Decimal | None = Field(default=None, ge=1, le=168)


class ProfileUpdate(APIModel):
    name: str = Field(min_length=2, max_length=120)


class TeamCreate(APIModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    manager_id: UUID | None = None


class TeamUpdate(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    manager_id: UUID | None = None


class MemberInput(APIModel):
    user_id: UUID
    role: Literal["MANAGER", "MEMBER"] = "MEMBER"


class MemberUpdate(APIModel):
    role: Literal["MANAGER", "MEMBER"]


class MemberView(APIModel):
    user_id: UUID
    role: str
    joined_at: datetime
    user: UserBrief


class TeamView(APIModel):
    id: UUID
    name: str
    description: str | None
    created_by_id: UUID
    manager_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    members: list[MemberView] = []


class ProjectCreate(APIModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    team_id: UUID
    manager_id: UUID | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: datetime | None = None
    due_date: datetime | None = None

    @model_validator(mode="after")
    def valid_period(self) -> "ProjectCreate":
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValueError("dueDate must not be before startDate")
        return self


class ProjectUpdate(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    manager_id: UUID | None = None
    status: ProjectStatus | None = None
    start_date: datetime | None = None
    due_date: datetime | None = None


class ProjectView(APIModel):
    id: UUID
    name: str
    description: str | None
    status: ProjectStatus
    team_id: UUID
    manager_id: UUID | None
    start_date: datetime | None
    due_date: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    team: dict[str, object]
    manager: UserBrief | None
    members: list[MemberView] = []
    tasks_count: int = 0


class TaskCreate(APIModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    project_id: UUID
    assignee_id: UUID | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_date: datetime | None = None
    estimated_hours: Decimal | None = Field(default=None, ge=0)


class TaskUpdate(APIModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    assignee_id: UUID | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = None
    estimated_hours: Decimal | None = Field(default=None, ge=0)


class TaskStatusUpdate(APIModel):
    status: TaskStatus


class TaskView(APIModel):
    id: UUID
    title: str
    description: str | None
    priority: TaskPriority
    status: TaskStatus
    project_id: UUID
    assignee_id: UUID | None
    due_date: datetime | None
    estimated_hours: Decimal | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    logged_minutes: int = 0
    project: dict[str, object]
    assignee: UserBrief | None


class TimeLogCreate(APIModel):
    task_id: UUID
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: int = Field(gt=0, le=1440)
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def dates(self) -> "TimeLogCreate":
        if self.ended_at and self.ended_at <= self.started_at:
            raise ValueError("endedAt must be after startedAt")
        return self


class TimeLogUpdate(APIModel):
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    description: str | None = Field(default=None, max_length=1000)


class AnalyzeOperations(APIModel):
    team_id: UUID
    start_date: datetime | None = None
    end_date: datetime | None = None

    @model_validator(mode="after")
    def valid_period(self) -> "AnalyzeOperations":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("endDate must not be before startDate")
        return self


class InsightStatusUpdate(APIModel):
    status: Literal["OPEN", "ACKNOWLEDGED", "RESOLVED", "DISMISSED"]
