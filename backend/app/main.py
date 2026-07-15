from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from app.api.routes import (
    auth,
    dashboard,
    insights,
    notifications,
    projects,
    reports,
    tasks,
    teams,
    time_logs,
    users,
    workload,
)
from app.core.config import settings
from app.core.database import session_factory
from app.core.rate_limit import limiter

app = FastAPI(
    title=settings.app_name,
    description="API de gerenciamento operacional, carga de trabalho e insights do FlowLog AI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    size = request.headers.get("content-length")
    try:
        too_large = bool(size and int(size) > settings.max_body_bytes)
    except ValueError:
        return JSONResponse({"message": "Content-Length inválido"}, status_code=400)
    if too_large:
        return JSONResponse({"message": "Corpo da requisição excede o limite"}, status_code=413)
    response = await call_next(request)
    response.headers.update(
        {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
    messages = [str(item["msg"]) for item in error.errors()]
    return JSONResponse(
        {"message": messages, "error": "Bad Request", "statusCode": 422}, status_code=422
    )


@app.exception_handler(HTTPException)
async def http_error(request: Request, error: HTTPException) -> JSONResponse:
    message = error.detail if isinstance(error.detail, (str, list)) else "Falha na requisição"
    return JSONResponse(
        {"message": message, "statusCode": error.status_code},
        status_code=error.status_code,
        headers=error.headers,
    )


@app.get(f"{settings.api_prefix}/health", tags=["Health"])
async def health() -> dict[str, str]:
    async with session_factory() as session:
        await session.exec(text("SELECT 1"))
    return {
        "status": "ok",
        "service": "flowlog-ai-api",
        "database": "up",
        "timestamp": datetime.now(UTC).isoformat(),
    }


for router in [
    auth.router,
    users.router,
    teams.router,
    projects.router,
    tasks.router,
    time_logs.router,
    workload.router,
    dashboard.router,
    notifications.router,
    insights.router,
    reports.router,
]:
    app.include_router(router, prefix=settings.api_prefix)
