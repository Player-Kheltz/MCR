# CATALOG.md — Indice de Documentos

> Gerado automaticamente por `scripts/doc_sync.py`

## Raiz do Projeto

- `.session_checkpoint.json` — 
- `AGENTS.md` — Regras de ouro do assistente
- `iniciar.bat` — Atalho do servidor (abre API + App)
- `oc-dev.ps1` — Swap seguro cloud para local (Ollama)
- `opencode.local.json` — Config OpenCode modo local (Ollama, 4 agentes)
- `server.py` — Script central (start/stop/typecheck/build/verify/checkpoint/doctor/rag/reindex)

## Backend (`backend/src/`)

| Arquivo | Descricao |
|---|---|
| `controllers\AuthController.ts` | Controller (logica de rota) |
| `controllers\CategoryController.ts` | Controller (logica de rota) |
| `controllers\CustomerController.ts` | Controller (logica de rota) |
| `controllers\DocumentController.ts` | Controller (logica de rota) |
| `controllers\MessageController.ts` | Controller (logica de rota) |
| `controllers\PostController.ts` | Controller (logica de rota) |
| `controllers\ProductController.ts` | Controller (logica de rota) |
| `controllers\PromotionController.ts` | Controller (logica de rota) |
| `lib\optimizer.ts` |  |
| `lib\prisma.ts` |  |
| `lib\safeJson.ts` |  |
| `middleware\auth.ts` | Middleware (auth, error handler) |
| `middleware\errorHandler.ts` | Middleware (auth, error handler) |
| `routes\auth.ts` | Definicao de rotas Express |
| `routes\categories.ts` | Definicao de rotas Express |
| `routes\customers.ts` | Definicao de rotas Express |
| `routes\documents.ts` | Definicao de rotas Express |
| `routes\messages.ts` | Definicao de rotas Express |
| `routes\posts.ts` | Definicao de rotas Express |
| `routes\products.ts` | Definicao de rotas Express |
| `routes\promotions.ts` | Definicao de rotas Express |
| `server.ts` |  |

## Mobile (`mobile/src/`)

| Arquivo | Descricao |
|---|---|
| `components\CategoryField.tsx` |  |
| `components\ConfirmModal.tsx` |  |
| `components\SelectField.tsx` |  |
| `components\Toast.tsx` | Componente de notificacao toast |
| `contexts\AuthContext.tsx` | Estado global de autenticacao |
| `navigation\AppNavigator.tsx` | Stack navigator com todas as rotas |
| `screens\CategoriesScreen.tsx` | Tela do app |
| `screens\ConversationDetailScreen.tsx` | Tela do app |
| `screens\CustomerDetailScreen.tsx` | Tela do app |
| `screens\CustomerFormScreen.tsx` | Tela do app |
| `screens\CustomersScreen.tsx` | Tela do app |
| `screens\DashboardScreen.tsx` | Tela do app |
| `screens\DocumentFormScreen.tsx` | Tela do app |
| `screens\DocumentViewScreen.tsx` | Tela do app |
| `screens\DocumentsScreen.tsx` | Tela do app |
| `screens\LoginScreen.tsx` | Tela do app |
| `screens\MessagesScreen.tsx` | Tela do app |
| `screens\PostFormScreen.tsx` | Tela do app |
| `screens\PostsScreen.tsx` | Tela do app |
| `screens\ProductFormScreen.tsx` | Tela do app |
| `screens\ProductsScreen.tsx` | Tela do app |
| `screens\PromotionDetailScreen.tsx` | Tela do app |
| `screens\PromotionFormScreen.tsx` | Tela do app |
| `screens\PromotionsScreen.tsx` | Tela do app |
| `screens\RegisterScreen.tsx` | Tela do app |
| `services\api.ts` | Axios client config |
| `utils\storage.ts` | Storage cross-platform (AsyncStorage / localStorage) |
| `utils\theme.ts` | Tokens de design (cores, espacamento, sombras) |

## Scripts (`scripts/`)

- `scripts\checkpoint.py` — Gerenciamento de checkpoint de sessao
- `scripts\doc_sync.py` — Regenera CATALOG.md automaticamente
- `scripts\lesson.py` — Registro de licoes aprendidas
- `scripts\rag_indexer.py` — Indexa codigo fonte em embeddings (nomic-embed-text)
- `scripts\rag_query.py` — Consulta RAG por similaridade
- `scripts\rag_watcher.py` — Reindex automatico a cada 120s
- `scripts\validate_local.py` — Testes de qualidade do modelo local (anti-alucinacao)

## Documentacao (`docs/`)

- `docs\CATALOG.md` — 
- `docs\ESTRUTURA.md` — 
- `docs\LGPD.md` — 
- `docs\Pendencias.md` — 
- `docs\TROUBLESHOOTING.md` — 
- `docs\knowledge\convencoes.md` — 
- `docs\knowledge\portas.md` — 
- `docs\knowledge\stack.md` — 
- `docs\lessons\20260624_211747_bun_crash_no_mcr_resolvido_com.md` — 
- `docs\lessons\20260624_213501_upload_de_fotos_requer_android.md` — 
- `docs\lessons\recentes.md` — 
- `docs\rules\autonomia.md` — 
- `docs\rules\checkpoint.md` — 
- `docs\rules\encoding.md` — 
- `docs\rules\hibrido.md` — 
- `docs\rules\intercambio.md` — 
- `docs\rules\licoes.md` — 
- `docs\rules\workflow.md` — 

## Outros

- `backend\package-lock.json` — 
- `backend\package.json` — 
- `backend\tsconfig.json` — 
- `mobile\.claude\settings.json` — 
- `mobile\AGENTS.md` — Regras de ouro do assistente
- `mobile\App.tsx` — 
- `mobile\CLAUDE.md` — 
- `mobile\app.json` — 
- `mobile\index.ts` — 
- `mobile\package-lock.json` — 
- `mobile\package.json` — 
- `mobile\tsconfig.json` — 
