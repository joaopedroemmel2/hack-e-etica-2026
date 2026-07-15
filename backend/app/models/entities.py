from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, Enum, Index, Numeric, String
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """Return UTC using the naive representation stored by timestamp mixins."""
    return datetime.now(UTC).replace(tzinfo=None)


class Role(StrEnum):
    ADMIN = "ADMIN"
    GESTOR = "GESTOR"
    COLABORADOR = "COLABORADOR"


class TeamMemberRole(StrEnum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    MEMBER = "MEMBER"


class ProjectMemberRole(StrEnum):
    MANAGER = "MANAGER"
    MEMBER = "MEMBER"


class ProjectStatus(StrEnum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class NotificationType(StrEnum):
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_DUE_SOON = "TASK_DUE_SOON"
    TASK_OVERDUE = "TASK_OVERDUE"
    WORKLOAD_WARNING = "WORKLOAD_WARNING"
    PROJECT_UPDATE = "PROJECT_UPDATE"
    AI_RECOMMENDATION = "AI_RECOMMENDATION"
    SYSTEM = "SYSTEM"


class InsightCategory(StrEnum):
    DELAY = "DELAY"
    PRODUCTIVITY = "PRODUCTIVITY"
    WORKLOAD = "WORKLOAD"
    DISTRIBUTION = "DISTRIBUTION"
    BOTTLENECK = "BOTTLENECK"


class InsightSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class InsightStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class User(TimestampMixin, table=True):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_role_active", "role", "is_active"),)
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=120)
    email: str = Field(sa_column=Column(String(255), unique=True, index=True, nullable=False))
    password_hash: str = Field(max_length=255)
    role: Role = Field(
        default=Role.COLABORADOR, sa_column=Column(Enum(Role, name="role"), nullable=False)
    )
    is_active: bool = True
    weekly_capacity_hours: Decimal = Field(
        default=Decimal("40"), sa_column=Column(Numeric(6, 2), nullable=False)
    )


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_user_revoked", "user_id", "revoked_at"),)
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    token_id: str = Field(index=True, unique=True, max_length=64)
    token_hash: str = Field(unique=True, max_length=64)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE", index=True)
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    revoked_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class Team(TimestampMixin, table=True):
    __tablename__ = "teams"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=120, index=True)
    description: str | None = Field(default=None, max_length=500)
    created_by_id: UUID = Field(foreign_key="users.id", ondelete="RESTRICT", index=True)
    manager_id: UUID | None = Field(
        default=None, foreign_key="users.id", ondelete="SET NULL", index=True
    )
    is_active: bool = Field(default=True, index=True)


class TeamMember(SQLModel, table=True):
    __tablename__ = "team_members"
    team_id: UUID = Field(foreign_key="teams.id", ondelete="CASCADE", primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE", primary_key=True, index=True)
    role: TeamMemberRole = Field(
        default=TeamMemberRole.MEMBER,
        sa_column=Column(Enum(TeamMemberRole, name="team_member_role"), nullable=False),
    )
    joined_at: datetime = Field(
        default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class Project(TimestampMixin, table=True):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_team_status", "team_id", "status"),
        Index("ix_projects_status_due", "status", "due_date"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    status: ProjectStatus = Field(
        default=ProjectStatus.PLANNING,
        sa_column=Column(Enum(ProjectStatus, name="project_status"), nullable=False),
    )
    team_id: UUID = Field(foreign_key="teams.id", ondelete="RESTRICT")
    manager_id: UUID | None = Field(
        default=None, foreign_key="users.id", ondelete="SET NULL", index=True
    )
    start_date: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    due_date: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    is_archived: bool = Field(default=False, index=True)


class ProjectMember(SQLModel, table=True):
    __tablename__ = "project_members"
    project_id: UUID = Field(foreign_key="projects.id", ondelete="CASCADE", primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE", primary_key=True, index=True)
    role: ProjectMemberRole = Field(
        default=ProjectMemberRole.MEMBER,
        sa_column=Column(Enum(ProjectMemberRole, name="project_member_role"), nullable=False),
    )
    joined_at: datetime = Field(
        default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class Task(TimestampMixin, table=True):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_project_status", "project_id", "status"),
        Index("ix_tasks_assignee_status", "assignee_id", "status"),
        Index("ix_tasks_status_due", "status", "due_date"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        sa_column=Column(Enum(TaskPriority, name="task_priority"), nullable=False),
    )
    status: TaskStatus = Field(
        default=TaskStatus.TODO,
        sa_column=Column(Enum(TaskStatus, name="task_status"), nullable=False),
    )
    project_id: UUID = Field(foreign_key="projects.id", ondelete="CASCADE")
    assignee_id: UUID | None = Field(default=None, foreign_key="users.id", ondelete="SET NULL")
    created_by_id: UUID = Field(foreign_key="users.id", ondelete="RESTRICT")
    due_date: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    estimated_hours: Decimal | None = Field(default=None, sa_column=Column(Numeric(8, 2)))
    completed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))


class TimeLog(TimestampMixin, table=True):
    __tablename__ = "time_logs"
    __table_args__ = (
        Index("ix_time_logs_task_started", "task_id", "started_at"),
        Index("ix_time_logs_user_started", "user_id", "started_at"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="tasks.id", ondelete="CASCADE")
    user_id: UUID = Field(foreign_key="users.id", ondelete="RESTRICT")
    started_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    ended_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    duration_minutes: int = Field(ge=0)
    description: str | None = Field(default=None, max_length=1000)


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "read_at", "created_at"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    team_id: UUID | None = Field(default=None, foreign_key="teams.id", ondelete="CASCADE")
    project_id: UUID | None = Field(default=None, foreign_key="projects.id", ondelete="CASCADE")
    task_id: UUID | None = Field(default=None, foreign_key="tasks.id", ondelete="CASCADE")
    type: NotificationType = Field(
        sa_column=Column(Enum(NotificationType, name="notification_type"), nullable=False)
    )
    title: str = Field(max_length=200)
    message: str = Field(max_length=1000)
    metadata_: dict[str, Any] | None = Field(default=None, sa_column=Column("metadata", JSON))
    read_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    created_at: datetime = Field(
        default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class Insight(TimestampMixin, table=True):
    __tablename__ = "insights"
    __table_args__ = (
        Index("ix_insights_status_severity_created", "status", "severity", "created_at"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID | None = Field(default=None, foreign_key="users.id", ondelete="SET NULL")
    team_id: UUID | None = Field(default=None, foreign_key="teams.id", ondelete="SET NULL")
    project_id: UUID | None = Field(default=None, foreign_key="projects.id", ondelete="SET NULL")
    task_id: UUID | None = Field(default=None, foreign_key="tasks.id", ondelete="SET NULL")
    category: InsightCategory = Field(
        sa_column=Column(Enum(InsightCategory, name="insight_category"), nullable=False)
    )
    severity: InsightSeverity = Field(
        default=InsightSeverity.INFO,
        sa_column=Column(Enum(InsightSeverity, name="insight_severity"), nullable=False),
    )
    status: InsightStatus = Field(
        default=InsightStatus.OPEN,
        sa_column=Column(Enum(InsightStatus, name="insight_status"), nullable=False),
    )
    title: str = Field(max_length=200)
    summary: str = Field(max_length=2000)
    recommendation: str = Field(max_length=2000)
    evidence: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    resolved_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
