# Relatório de auditoria técnica

Auditoria concluída em 14/07/2026 sobre backend FastAPI/SQLModel, PostgreSQL/Alembic,
Docker Compose e frontend Next.js.

## Correções aplicadas

- Bloqueadas leituras horizontais entre equipes no dashboard, workload, usuários e insights.
- Colaboradores agora veem e apontam horas somente em tarefas atribuídas a eles.
- Consultas de gestores a usuários, insights e apontamentos foram limitadas às equipes geridas.
- Tokens de atualização são rotacionados com bloqueio de linha e revogados ao desativar a conta.
- Login de usuário inexistente executa verificação Argon2 fictícia para reduzir enumeração temporal.
- O hash de senha foi removido da serialização paginada de usuários.
- Respostas de domínio foram normalizadas para camelCase, compatível com o frontend.
- Erros HTTP e de validação retornam uma mensagem segura consumível pelo frontend.
- Criação e edição validam datas, projetos arquivados, usuários ativos e vínculo com a equipe.
- Apontamentos foram limitados a 1.440 minutos e a carga deixou de contar estimativas já realizadas.
- Sessões de banco executam rollback em exceções; listas de projetos e tarefas evitam N+1.
- Configuração de produção rejeita segredo JWT padrão e parâmetros JWT/thresholds inválidos.
- `.env` foi removido do versionamento e arquivos de segredo/cache passaram ao `.gitignore`.
- A migration inicial dinâmica foi substituída por DDL estático e reversível, incluindo ENUMs.

## Evidências de validação

- `compileall`: aprovado.
- Ruff check/format: aprovado.
- mypy: 49 arquivos, nenhum erro.
- pytest: 9 testes aprovados; cobertura total 62%.
- Bandit: nenhum achado.
- Alembic/PostgreSQL: `upgrade`, `check`, `downgrade`, novo `upgrade` e `check` aprovados.
- Frontend: ESLint aprovado; 5 testes aprovados; TypeScript e build de produção aprovados.
- `npm audit --omit=dev`: nenhuma vulnerabilidade.
- `pip-audit`: nenhuma vulnerabilidade conhecida nas dependências instaladas.
- OpenAPI e stack Docker são validados na etapa final descrita no README.

## Riscos residuais

- A cobertura de 62% protege os fluxos críticos adicionados, mas equipes, notificações e insights
  ainda merecem mais testes de integração antes de mudanças grandes.
- O armazenamento de tokens no `localStorage` foi preservado por compatibilidade com o frontend;
  cookies HttpOnly seriam uma melhoria futura que exige alteração coordenada de contrato/CSRF.
- Os módulos finos de reexportação em `app/models` e `app/schemas` foram preservados por
  compatibilidade de imports, embora tenham pouca lógica própria.
