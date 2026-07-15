from decimal import Decimal

from httpx import AsyncClient

from app.core.security import hash_password
from app.models.entities import Role, User
from tests.conftest import factory


async def token(client: AsyncClient, user: User, password: str) -> str:
    async with factory() as session:
        session.add(user)
        await session.commit()
    response = await client.post(
        "/api/auth/login", json={"email": user.email, "password": password}
    )
    return response.json()["accessToken"]


async def test_manager_cannot_create_user(client: AsyncClient) -> None:
    value = await token(
        client,
        User(
            name="Gestor",
            email="manager@example.com",
            password_hash=hash_password("strong-password"),
            role=Role.GESTOR,
        ),
        "strong-password",
    )
    response = await client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {value}"},
        json={
            "name": "Outro",
            "email": "other@example.com",
            "password": "strong-password",
            "role": "COLABORADOR",
        },
    )
    assert response.status_code == 403


async def test_user_without_tasks_has_normal_workload(client: AsyncClient) -> None:
    user = User(
        name="Worker",
        email="worker@example.com",
        password_hash=hash_password("strong-password"),
        role=Role.COLABORADOR,
        weekly_capacity_hours=Decimal("40"),
    )
    value = await token(client, user, "strong-password")
    response = await client.get("/api/workload/me", headers={"Authorization": f"Bearer {value}"})
    assert response.status_code == 200
    assert response.json()["utilizationPercentage"] == 0
    assert response.json()["level"] == "NORMAL"
