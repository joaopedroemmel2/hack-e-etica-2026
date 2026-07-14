# FlowLog AI — Frontend

Interface Next.js do FlowLog AI, executada por padrão na porta `3001`.

## Configuração

```bash
cp .env.example .env.local
npm ci
npm run dev
```

`NEXT_PUBLIC_API_URL` deve apontar para o prefixo público da API, por exemplo `http://localhost:3000/api`. Por ser pública no Next.js, a variável não deve conter credenciais.

## Scripts

```bash
npm run dev
npm run lint
npm test
npm run test:watch
npm run build
npm run start
```

## Estrutura

- `src/app`: login e páginas autenticadas
- `src/components`: layout, gráficos e componentes de interface
- `src/contexts`: estado de autenticação
- `src/lib`: cliente HTTP, tokens e formatadores
- `src/types`: contratos consumidos da API

A aplicação renova o access token automaticamente. Respostas não autorizadas limpam a sessão e redirecionam para o login.
