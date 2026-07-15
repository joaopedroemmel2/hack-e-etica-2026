# FlowLog AI — Backend Python

API assíncrona em FastAPI, SQLModel, PostgreSQL e Alembic para autenticação, usuários, equipes, projetos, tarefas, apontamentos, carga, dashboard, notificações e insights.

## Execução local

Requer Python 3.12+ e PostgreSQL 16+.

```bash
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload --port 3000
```

A API usa `http://localhost:3000/api`. Swagger, ReDoc e OpenAPI ficam em `/docs`, `/redoc` e `/openapi.json`.

## Qualidade e migrations

```bash
ruff check .
ruff format --check .
mypy app scripts
pytest --cov=app
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

## Administrador inicial

Defina `INITIAL_ADMIN_NAME`, `INITIAL_ADMIN_EMAIL` e `INITIAL_ADMIN_PASSWORD` no `.env`, execute as migrations e rode uma vez:

```bash
python -m scripts.create_admin
```

O comando recusa configuração incompleta e e-mail já existente.

## Segurança

Pydantic rejeita campos desconhecidos; senhas usam Argon2; refresh tokens são rotativos e apenas seu SHA-256 é persistido. RBAC, proteção horizontal, CORS, TrustedHost, limite de body, rate limiting e headers seguros são aplicados no backend.

## Docker

O Compose da raiz aguarda o PostgreSQL, aplica `alembic upgrade head` e inicia Uvicorn como usuário não-root:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f backend
```

Consulte o [README principal](../README.md) para a arquitetura, endpoints e solução de problemas.
