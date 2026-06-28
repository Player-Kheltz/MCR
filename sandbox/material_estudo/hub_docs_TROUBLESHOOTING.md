# TROUBLESHOOTING.md — Problemas Comuns

## Servidor

### Porta 3000 já em uso (EADDRINUSE)
```powershell
python server.py stop   # mata processo na porta 3000
python server.py start  # inicia novamente
```

### Servidor inicia mas login retorna erro
Testar conexão com banco:
```powershell
node -e "const{PrismaClient}=require('@prisma/client');const p=new PrismaClient();p.user.findMany().then(u=>console.log(u.length,'users')).catch(e=>console.error(e)).finally(()=>p.\$disconnect())"
```

### Login retorna "Erro ao fazer login" (500)
Causa mais comum: curl do PowerShell tem escaping diferente. Usar `server.py` ou Node para testes.

## Mobile

### App não carrega em localhost:8081
1. Verificar se Expo está rodando: `npx expo start --web` na pasta `mobile/`
2. Verificar se a porta não está ocupada
3. Se o `iniciar.bat` matou o Expo, reiniciar o app

### Fotos não aparecem (web)
Upload de fotos só funciona em dispositivo nativo (Expo Go). Em web, as fotos são mostradas como placeholder.

### TypeScript não compila
Verificar strict mode no `tsconfig.json`. Erros comuns:
- `import { api }` → deve ser `import api` (default export)
- `primaryLight` não existe no theme → usar hex inline

### Alert.alert não funciona (web)
`Alert.alert` não é suportado em Expo web. O app usa Toast e modais inline.

## Build

### Backend
```powershell
cd backend
npx tsc                        # compila
npx tsc --noEmit              # só type-check
npx prisma generate           # regenerar Prisma Client
npx prisma migrate dev        # criar migration
```

### Mobile
```powershell
cd mobile
npx tsc --noEmit              # type-check
npx expo start --web          # iniciar dev server
```

## Processos

### Como matar processos esquecidos
```powershell
python server.py stop    # mata só a porta 3000
taskkill /f /im node.exe # mata TODOS os node (inclui Expo!)
```
Preferir `server.py stop` para não matar o Expo.

### Expo foi morto acidentalmente
Reiniciar com `npx expo start --web` na pasta `mobile/`.
