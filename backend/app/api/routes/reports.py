from fastapi import APIRouter

from app.api.dependencies import CurrentUser, SessionDep
from app.api.routes.dashboard import build

router = APIRouter(prefix="/reports", tags=["Relatórios"])


@router.get("/overview")
async def overview(session: SessionDep, actor: CurrentUser) -> dict[str, object]:
    return await build(session, actor, None, None, None)
