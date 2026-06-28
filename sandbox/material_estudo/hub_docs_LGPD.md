# LGPD.md — Conformidade com Lei Geral de Proteção de Dados

> Este documento descreve as práticas de proteção de dados do Hub do Lojista.

## Dados Pessoais Coletados

| Dado | Onde | Finalidade | Base Legal |
|---|---|---|---|
| Nome | Cliente, Usuário | Identificação | Execução do serviço |
| CPF | Cliente | Documentação fiscal | Obrigação legal |
| Telefone | Cliente | Contato | Interesse legítimo |
| Email | Cliente, Usuário | Contato, login | Execução do serviço |
| Endereço | Cliente, Loja | Entrega, fiscal | Execução do serviço |
| Senha (hash) | Usuário | Autenticação | Execução do serviço |
| Token JWT | Storage local | Sessão | Execução do serviço |

## Medidas de Segurança Implementadas

### ✅ Implementado
- Senhas armazenadas com **bcrypt** (salt rounds: 10)
- JWT não contém dados pessoais (apenas userId + storeId)
- Autenticação obrigatória para todas as rotas (JWT Bearer)
- Isolamento por loja: cada usuário só acessa dados da própria loja
- `onDelete: Cascade` em relações — exclusão de loja remove todos os dados
- Upload de arquivos validado por tipo e tamanho (antivirus indireto)
- Helmet middleware para headers de segurança
- CORS restrito à origem do frontend
- Logs não contêm dados pessoais (stack traces sem dados do usuário)

### ⚠️ Melhorias Futuras
- Criptografar `accessToken` do PlatformAccount no banco
- Implementar `expo-secure-store` para tokens em dispositivos móveis
- Adicionar rota de exportação de dados (portabilidade)
- Adicionar rota de exclusão de conta (direito ao esquecimento)
- Implementar rate limiting em auth endpoints
- Adicionar logs de auditoria (quem acessou o quê)

## Direitos do Titular (LGPD Art. 18)

| Direito | Implementado? | Como exercer? |
|---|---|---|
| Confirmação da existência de tratamento | ✅ | Login exibe dados do perfil |
| Acesso aos dados | ✅ | Dashboard + listas do app |
| Correção de dados incompletos/inadequados | ✅ | Editar cliente/produto |
| Exclusão dos dados | ✅ | Remover cliente/produto |
| Portabilidade | ❌ | Futuro |
| Informação sobre compartilhamento | ✅ | Dados não são compartilhados |

## Boas Práticas para o Desenvolvedor

1. **NUNCA** logar dados pessoais no console
2. **SEMPRE** usar `safeJsonParse` para evitar crash ao ler dados do banco
3. **SEMPRE** verificar `storeId` antes de retornar dados
4. **NUNCA** retornar o campo `password` em respostas da API
5. **NUNCA** incluir dados sensíveis em mensagens de erro
6. **SEMPRE** usar `select` em vez de `include` ao retornar dados sensitivos

## Em Caso de Vazamento

1. Identificar a extensão (quais dados, quantos registros)
2. Notificar os titulares afetados em até 72h (LGPD Art. 48)
3. Notificar a ANPD (Autoridade Nacional de Proteção de Dados)
4. Tomar medidas para mitigar o dano
5. Registrar o incidente e as ações tomadas
