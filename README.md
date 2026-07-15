# FlowLog AI

Plataforma de gestão operacional, produtividade e saúde organizacional. O monorepo reúne uma API Python/FastAPI com PostgreSQL e uma interface Next.js em português.

## Stack e arquitetura

- Backend: Python 3.12, FastAPI, SQLModel, Pydantic, Alembic, JWT/Argon2 e asyncpg
- Frontend: Next.js, React, TailwindCSS, Shadcn/UI e Recharts
- Infraestrutura: PostgreSQL 16, Docker Compose, health checks e containers sem root
- Camadas: rotas HTTP → serviços de negócio → SQLModel/PostgreSQL

O frontend continua usando `http://localhost:3000/api`, tokens Bearer no `localStorage` e respostas camelCase. Swagger, ReDoc e OpenAPI ficam em `/docs`, `/redoc` e `/openapi.json`.

## Início rápido com Docker

```bash
cp .env.example .env
# substitua JWT_SECRET_KEY e POSTGRES_PASSWORD
docker compose config
docker compose up --build -d
docker compose ps
docker compose logs -f backend frontend
```

| Serviço | Endereço |
| --- | --- |
| Frontend | `http://localhost:3001` |
| API | `http://localhost:3000/api` |
| Health | `http://localhost:3000/api/health` |
| Swagger | `http://localhost:3000/docs` |

O backend aguarda o health check do PostgreSQL, executa `alembic upgrade head` e inicia Uvicorn. Para criar o primeiro administrador:

```bash
docker compose exec backend python -m scripts.create_admin
```

## Desenvolvimento sem Docker

```bash
cd backend
cp .env.example .env
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 3000
```

Em outro terminal:

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

## Qualidade

```bash
cd backend
ruff check .
ruff format --check .
mypy app scripts
pytest --cov=app

cd ../frontend
npm run lint
npm test
npm run build
```

## Principais endpoints

- `/api/auth`: cadastro, login, refresh rotativo, logout, perfil e senha
- `/api/users`, `/api/teams`, `/api/projects`, `/api/tasks`: gestão e RBAC
- `/api/time-logs`: apontamentos por tarefa, usuário e período
- `/api/workload`: carga individual/equipe e alertas
- `/api/dashboard`, `/api/reports/overview`: métricas operacionais
- `/api/notifications`: caixa de notificações e leitura
- `/api/ai/analyze`, `/api/ai/insights`: insights determinísticos extensíveis

## Migrations

```bash
cd backend
alembic revision --autogenerate -m "descricao"
alembic upgrade head
alembic downgrade -1
```

Não há `create_all` na inicialização da aplicação; alterações de produção passam exclusivamente pelo Alembic.

## Solução de problemas

- Banco indisponível: confirme `docker compose ps` e `docker compose logs postgres`.
- API rejeitada pelo navegador: inclua a origem em `CORS_ORIGINS`.
- Host rejeitado: inclua-o em `ALLOWED_HOSTS`.
- Migration divergente: confira `alembic current` e `alembic history`; não apague migrations já aplicadas.
- Login falha após desativação: contas inativas e seus tokens são rejeitados deliberadamente.

Detalhes do backend estão em [backend/README.md](backend/README.md).
