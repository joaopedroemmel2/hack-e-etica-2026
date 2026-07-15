from uuid import UUID

from fastapi import APIRouter, Query, Response
from sqlalchemy import func
from sqlmodel import select

from app.api.dependencies import CurrentUser, SessionDep
from app.models.entities import Notification
from app.services.domain_service import DomainService, camelize, page

router = APIRouter(prefix="/notifications", tags=["Notificações"])


@router.get("")
async def listing(
    session: SessionDep,
    actor: CurrentUser,
    page_number: int = Query(1, alias="page", ge=1),
    limit: int = Query(20, ge=1, le=100),
    unread: bool | None = None,
) -> dict[str, object]:
    c = [Notification.user_id == actor.id]
    c += [Notification.read_at.is_(None)] if unread else []
    total = (await session.exec(select(func.count()).select_from(Notification).where(*c))).one()
    rows = (
        await session.exec(
            select(Notification)
            .where(*c)
            .order_by(Notification.created_at.desc())
            .offset((page_number - 1) * limit)
            .limit(limit)
        )
    ).all()
    return page(rows, page_number, limit, total)


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: UUID, session: SessionDep, actor: CurrentUser
) -> dict[str, object]:
    from datetime import UTC, datetime

    note = await DomainService(session).get(Notification, notification_id, "Notificação")
    if note.user_id != actor.id:
        from fastapi import HTTPException

        raise HTTPException(403, "Acesso negado")
    note.read_at = datetime.now(UTC)
    await session.commit()
    return camelize(note)


@router.post("/read-all", status_code=204)
async def read_all(session: SessionDep, actor: CurrentUser) -> Response:
    from datetime import UTC, datetime

    rows = (
        await session.exec(
            select(Notification).where(
                Notification.user_id == actor.id, Notification.read_at.is_(None)
            )
        )
    ).all()
    for row in rows:
        row.read_at = datetime.now(UTC)
    await session.commit()
    return Response(status_code=204)
