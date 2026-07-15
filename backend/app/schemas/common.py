from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.title() for part in tail)


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True, extra="forbid"
    )


class PageMeta(APIModel):
    page: int
    limit: int
    total: int
    total_pages: int


class Page(APIModel, Generic[T]):
    data: list[T]
    meta: PageMeta


class UserPublic(APIModel):
    id: UUID
    name: str
    email: str
    role: str
    is_active: bool = True
    weekly_capacity_hours: Decimal = Decimal("40")
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserBrief(APIModel):
    id: UUID
    name: str
    email: str


class Message(APIModel):
    message: str
