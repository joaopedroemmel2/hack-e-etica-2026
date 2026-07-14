# FlowLog AI

Plataforma de gestão operacional, produtividade e saúde organizacional. O monorepo reúne uma API NestJS/PostgreSQL e uma interface Next.js em português.

## Funcionalidades

- autenticação JWT com refresh token rotativo e papéis
- administração de usuários, equipes e membros
- projetos, responsáveis, status e prazos
- tarefas, prioridades, responsáveis, estimativas e métricas de horas
- cálculo de carga semanal e alertas de sobrecarga
- dashboard com indicadores e gráficos
- insights por regras e integração opcional com modelo de IA

## Stack

- Backend: NestJS 11, TypeScript, Prisma, PostgreSQL, JWT e Swagger
- Frontend: Next.js, React, TailwindCSS, Shadcn/UI e Recharts
- Infraestrutura: Docker Compose, imagens multi-stage e health checks

## Início rápido com Docker

```bash
cp .env.example .env
docker compose config
docker compose up --build -d
docker compose ps
```

Antes de subir em produção, substitua `JWT_SECRET`, `JWT_REFRESH_SECRET` e `POSTGRES_PASSWORD` por valores aleatórios fortes. Nunca envie o arquivo `.env` ao repositório.

| Serviço | Endereço padrão |
| --- | --- |
| Frontend | `http://localhost:3001` |
| API | `http://localhost:3000/api` |
| Health check | `http://localhost:3000/api/health` |
| Swagger | `http://localhost:3000/docs`, quando habilitado |

As migrations são aplicadas antes da inicialização da API. O PostgreSQL é persistido no volume `postgres_data` e sua porta é vinculada somente ao loopback do host.

Para acompanhar a inicialização:

```bash
docker compose logs -f backend frontend
```

## Desenvolvimento local

```bash
cd backend
cp .env.example .env
npm ci
npm run prisma:generate
npm run prisma:migrate
npm run start:dev
```

Em outro terminal:

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

## Validação

```bash
cd backend
npm run lint
npm test
npm run test:e2e
npm run build

cd ../frontend
npm run lint
npm test
npm run build
```

## Segurança de produção

- JWT, papéis e rotas públicas explícitas
- Refresh tokens rotacionados e persistidos somente como hash
- Helmet, CORS restritivo, DTOs com whitelist e rate limiting global
- Swagger desabilitado por padrão em produção
- Containers sem root, filesystem somente leitura e `no-new-privileges`
- Segredos recebidos por ambiente, nunca incorporados às imagens

Em uma implantação pública, termine TLS em um proxy reverso, mantenha PostgreSQL em rede privada, use um gerenciador de segredos e configure backups e observabilidade.

Backup e restauração devem ser exercitados de acordo com a infraestrutura escolhida. Um exemplo local é `pg_dump`/`pg_restore`, executado com credenciais fornecidas pelo gerenciador de segredos. Não armazene dumps com dados reais no repositório.

## Limites atuais

O schema contém `TimeLog` e `Notification`, usados pelos cálculos e alertas, mas ainda não há módulos HTTP dedicados para CRUD geral dessas entidades. Relatórios exportáveis, recuperação de senha, MFA, SSO, auditoria imutável e observabilidade distribuída são evoluções recomendadas antes de uso em organizações com requisitos regulatórios.

## Variáveis principais

| Variável | Descrição |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | URL pública da API usada pelo navegador |
| `CORS_ORIGIN` | Origens permitidas, separadas por vírgula |
| `JWT_SECRET` / `JWT_REFRESH_SECRET` | Segredos distintos, mínimo de 32 caracteres |
| `ENABLE_SWAGGER` | Expõe a documentação da API em produção |
| `THROTTLE_TTL_MS` / `THROTTLE_LIMIT` | Janela e limite global de requisições |
| `AI_PROVIDER` | `rules` ou `openai` |

Consulte [backend/README.md](backend/README.md) e [frontend/README.md](frontend/README.md) para detalhes.
