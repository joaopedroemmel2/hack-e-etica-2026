import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-thirty-two-characters"
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_session
from app.main import app

app.state.limiter.enabled = False

engine = create_async_engine("sqlite+aiosqlite:///./test.db")
factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override() -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        yield session


app.dependency_overrides[get_session] = override


@pytest.fixture(autouse=True)
async def database() -> AsyncIterator[None]:
    app.state.limiter.reset()
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as value:
        yield value
