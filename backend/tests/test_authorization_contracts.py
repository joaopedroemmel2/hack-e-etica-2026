from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.core.security import hash_password
from app.models.entities import (
    Insight,
    InsightCategory,
    Project,
    Role,
    Task,
    Team,
    TeamMember,
    TeamMemberRole,
    User,
)
from tests.conftest import factory

PASSWORD = "strong-password"


async def login(client: AsyncClient, email: str) -> tuple[str, str]:
    response = await client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    return body["accessToken"], body["refreshToken"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def seed_scope() -> dict[str, object]:
    async with factory() as session:
        admin = User(
            name="Admin",
            email="admin@example.com",
            password_hash=hash_password(PASSWORD),
            role=Role.ADMIN,
        )
        manager_a = User(
            name="Manager A",
            email="manager-a@example.com",
            password_hash=hash_password(PASSWORD),
            role=Role.GESTOR,
        )
        manager_b = User(
            name="Manager B",
            email="manager-b@example.com",
            password_hash=hash_password(PASSWORD),
            role=Role.GESTOR,
        )
        worker_a = User(
            name="Worker A",
            email="worker-a@example.com",
            password_hash=hash_password(PASSWORD),
            role=Role.COLABORADOR,
        )
        worker_b = User(
            name="Worker B",
            email="worker-b@example.com",
            password_hash=hash_password(PASSWORD),
            role=Role.COLABORADOR,
        )
        session.add_all([admin, manager_a, manager_b, worker_a, worker_b])
        await session.flush()
        team_a = Team(name="Team A", created_by_id=manager_a.id, manager_id=manager_a.id)
        team_b = Team(name="Team B", created_by_id=manager_b.id, manager_id=manager_b.id)
        session.add_all([team_a, team_b])
        await session.flush()
        session.add_all(
            [
                TeamMember(team_id=team_a.id, user_id=manager_a.id, role=TeamMemberRole.OWNER),
                TeamMember(team_id=team_a.id, user_id=worker_a.id),
                TeamMember(team_id=team_b.id, user_id=manager_b.id, role=TeamMemberRole.OWNER),
                TeamMember(team_id=team_b.id, user_id=worker_b.id),
            ]
        )
        project_a = Project(name="Project A", team_id=team_a.id, manager_id=manager_a.id)
        project_b = Project(name="Project B", team_id=team_b.id, manager_id=manager_b.id)
        session.add_all([project_a, project_b])
        await session.flush()
        task_a = Task(
            title="Task A",
            project_id=project_a.id,
            assignee_id=worker_a.id,
            created_by_id=manager_a.id,
        )
        task_b = Task(
            title="Task B",
            project_id=project_b.id,
            assignee_id=worker_b.id,
            created_by_id=manager_b.id,
        )
        session.add_all([task_a, task_b])
        insight_b = Insight(
            team_id=team_b.id,
            category=InsightCategory.WORKLOAD,
            title="Private insight",
            summary="Private",
            recommendation="Private",
        )
        session.add(insight_b)
        await session.commit()
        return {
            "admin": admin,
            "manager_a": manager_a,
            "worker_a": worker_a,
            "worker_b": worker_b,
            "team_a": team_a,
            "team_b": team_b,
            "project_a": project_a,
            "task_a": task_a,
            "task_b": task_b,
            "insight_b": insight_b,
        }


async def test_manager_cannot_cross_team_boundaries(client: AsyncClient) -> None:
    scope = await seed_scope()
    token, _ = await login(client, "manager-a@example.com")
    auth = headers(token)
    assert (
        await client.get(f"/api/dashboard?teamId={scope['team_b'].id}", headers=auth)
    ).status_code == 403
    assert (
        await client.get(f"/api/workload/users/{scope['worker_b'].id}", headers=auth)
    ).status_code == 403
    assert (
        await client.get(f"/api/ai/insights/{scope['insight_b'].id}", headers=auth)
    ).status_code == 403
    users = await client.get("/api/users?limit=100", headers=auth)
    assert users.status_code == 200
    assert {item["email"] for item in users.json()["data"]} == {
        "manager-a@example.com",
        "worker-a@example.com",
    }


async def test_collaborator_only_sees_assigned_tasks_and_logs(client: AsyncClient) -> None:
    scope = await seed_scope()
    token, _ = await login(client, "worker-a@example.com")
    auth = headers(token)
    tasks = await client.get("/api/tasks?limit=100", headers=auth)
    assert tasks.status_code == 200
    assert [item["id"] for item in tasks.json()["data"]] == [str(scope["task_a"].id)]
    assert (await client.get(f"/api/tasks/{scope['task_b'].id}", headers=auth)).status_code == 403
    forbidden_log = await client.post(
        "/api/time-logs",
        headers=auth,
        json={
            "taskId": str(scope["task_b"].id),
            "startedAt": datetime.now(UTC).isoformat(),
            "durationMinutes": 60,
        },
    )
    assert forbidden_log.status_code == 403


async def test_frontend_project_and_task_contract_is_camel_case(client: AsyncClient) -> None:
    await seed_scope()
    token, _ = await login(client, "admin@example.com")
    auth = headers(token)
    project = (await client.get("/api/projects", headers=auth)).json()["data"][0]
    task = (await client.get("/api/tasks", headers=auth)).json()["data"][0]
    assert {"teamId", "managerId", "startDate", "dueDate", "tasksCount"} <= project.keys()
    assert {"projectId", "assigneeId", "dueDate", "estimatedHours", "loggedMinutes"} <= task.keys()
    assert "team_id" not in project and "project_id" not in task


async def test_deactivation_revokes_access_and_refresh(client: AsyncClient) -> None:
    scope = await seed_scope()
    admin_token, _ = await login(client, "admin@example.com")
    worker_token, worker_refresh = await login(client, "worker-a@example.com")
    response = await client.delete(
        f"/api/users/{scope['worker_a'].id}", headers=headers(admin_token)
    )
    assert response.status_code == 204
    assert (await client.get("/api/users/me", headers=headers(worker_token))).status_code == 401
    assert (
        await client.post("/api/auth/refresh", json={"refreshToken": worker_refresh})
    ).status_code == 401


async def test_validation_rejects_invalid_period_and_excessive_log(client: AsyncClient) -> None:
    scope = await seed_scope()
    token, _ = await login(client, "manager-a@example.com")
    auth = headers(token)
    invalid_project = await client.post(
        "/api/projects",
        headers=auth,
        json={
            "name": "Invalid dates",
            "teamId": str(scope["team_a"].id),
            "startDate": datetime.now(UTC).isoformat(),
            "dueDate": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        },
    )
    assert invalid_project.status_code == 422
    worker_token, _ = await login(client, "worker-a@example.com")
    invalid_log = await client.post(
        "/api/time-logs",
        headers=headers(worker_token),
        json={
            "taskId": str(scope["task_a"].id),
            "startedAt": datetime.now(UTC).isoformat(),
            "durationMinutes": 1441,
        },
    )
    assert invalid_log.status_code == 422
