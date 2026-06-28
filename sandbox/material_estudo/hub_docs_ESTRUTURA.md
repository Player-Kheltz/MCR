# ESTRUTURA.md — Visão Geral do Projeto

## Stack
- **Backend:** Node.js + Express + TypeScript + Prisma + SQLite
- **Mobile:** React Native + Expo + TypeScript
- **Gerenciamento:** Python (server.py) + Batch (iniciar.bat)

## Portas

| Serviço | Porta | Iniciado por |
|---|---|---|
| API (backend) | 3000 | `server.py start` ou `iniciar.bat` |
| App (Expo web) | 8081 | `npx expo start --web` ou `iniciar.bat` |

## Fluxo de Dados

```
Mobile (Expo web 8081) ──HTTP──> API (Express 3000) ──Prisma──> SQLite (dev.db)
```

## Banco de Dados (Prisma / SQLite)

### Modelos
- **Store** — Loja (dados cadastrais)
- **User** — Usuário/funcionário (vinculado à Store)
- **Product** — Produto (nome, preço, fotos, especificações)
- **Post** — Postagem (conteúdo, plataformas, status de publicação)
- **PlatformAccount** — Conta vinculada (Instagram, Facebook, etc)
- **Customer** — Cliente (nome, contato, CPF, endereço)
- **Document** — Documento gerado (template + dados + conteúdo)
- **Promotion** — Promoção (título, desconto, período, produtos)

### Convenções
- IDs: CUID (gerado pelo Prisma)
- JSON strings: `photos`, `specs`, `media`, `platforms`, `platformStatus`, `data` são armazenados como string JSON no SQLite
- Timestamps: `createdAt`/`updatedAt` automáticos

## Estrutura de Pastas

```
E:\Hub do Lojista\
├── backend/
│   ├── src/           ← TypeScript fonte
│   │   ├── controllers/  ← Lógica das rotas
│   │   ├── middleware/   ← Auth, error handler
│   │   ├── routes/       ← Definição de rotas Express
│   │   └── lib/          ← Prisma client
│   ├── prisma/        ← Schema + migrations + dev.db
│   └── dist/          ← Compilado (JS)
├── mobile/
│   ├── src/
│   │   ├── screens/      ← Telas do app
│   │   ├── components/   ← Componentes reutilizáveis
│   │   ├── contexts/     ← Contextos React (Auth)
│   │   ├── services/     ← API client
│   │   ├── navigation/   ← Navegação
│   │   └── utils/        ← Theme, storage
│   └── App.tsx        ← Entry point
├── scripts/            ← Scripts auxiliares
│   ├── checkpoint.py   ← Gerenciamento de sessão
│   ├── lesson.py       ← Lições aprendidas
│   ├── doc_sync.py     ← Regenera CATALOG.md
│   ├── rag_indexer.py  ← Indexa código fonte em embeddings
│   ├── rag_query.py    ← Consulta RAG por similaridade
│   ├── rag_watcher.py  ← Reindex automático a cada 120s
│   └── validate_local.py ← Testes de qualidade do modelo local
├── docs/              ← Documentação
│   ├── rules/          ← Regras modulares (workflow, híbrido, checkpoint, lições, intercâmbio)
│   ├── knowledge/      ← Fatos curados manualmente (portas, stack, convenções)
│   ├── lessons/        ← Lições aprendidas
│   └── LGPD.md         ← Conformidade com proteção de dados
├── server.py          ← Script de gerenciamento (start/stop/typecheck/checkpoint)
├── opencode.json      ← Config OpenCode cloud (padrão)
├── opencode.local.json ← Config OpenCode local (Ollama)
├── oc-dev.ps1         ← Swap seguro cloud↔local
└── iniciar.bat        ← Atalho do servidor
```
