from httpx import AsyncClient


async def register(client: AsyncClient, email: str = "ana@example.com") -> dict[str, object]:
    response = await client.post(
        "/api/auth/register",
        json={"name": "Ana Silva", "email": email, "password": "strong-password"},
    )
    assert response.status_code == 201
    return response.json()


async def test_register_login_me_and_no_token(client: AsyncClient) -> None:
    body = await register(client)
    assert "password" not in str(body).lower()
    assert (await client.get("/api/auth/me")).status_code == 401
    token = body["accessToken"]
    response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"
    assert (
        await client.post(
            "/api/auth/login", json={"email": "ana@example.com", "password": "strong-password"}
        )
    ).status_code == 200


async def test_wrong_password_refresh_rotation_and_logout(client: AsyncClient) -> None:
    body = await register(client)
    assert (
        await client.post(
            "/api/auth/login", json={"email": "ana@example.com", "password": "incorrect-password"}
        )
    ).status_code == 401
    first = body["refreshToken"]
    rotated = await client.post("/api/auth/refresh", json={"refreshToken": first})
    assert rotated.status_code == 200
    assert (await client.post("/api/auth/refresh", json={"refreshToken": first})).status_code == 401
    second = rotated.json()["refreshToken"]
    assert (await client.post("/api/auth/logout", json={"refreshToken": second})).status_code == 204
    assert (
        await client.post("/api/auth/refresh", json={"refreshToken": second})
    ).status_code == 401
