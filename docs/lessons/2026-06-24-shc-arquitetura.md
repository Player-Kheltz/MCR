# 2026-06-24 — SHC: Sistema de Habilidades Contextuais

## O que foi decidido
Criamos um sistema de 5 camadas de modificação contextual para as habilidades do SPA:
1. Postura (Ímpeto/Equilíbrio/Guarda)
2. Nível do domínio (marcos 5/10/15/20 cumulativos)
3. Sinergias (outros domínios treinados)
4. Estados de alma (Vínculo/Lampejo)
5. Condições situacionais (cercado/vida baixa/full HP/single target)

## Arquivos criados/modificados
- **NOVO**: `contexto.lua` — Resolvedor Contextual (aplica as 5 camadas)
- **MODIFICADO**: `executor.lua` v10.0 — chama CONTEXTO.resolver() antes de MOTOR.executar()
- **INALTERADO**: `motor_habilidades.lua` — motor puro, não precisa saber de contexto

## Princípios fundamentais
- O jogador NÃO escolhe caminhos; o sistema reflete o que ele faz
- Cada habilidade carrega DENTRO DE SI suas variações (blocos postura/niveis/sinergias/estados/condicoes)
- ~400 habilidades com ~7600+ comportamentos únicos potenciais
- Habilidades existentes continuam funcionando (fallback para efeitoConfig base)
- O motor_habilidades.lua NÃO precisa ser alterado (estabilidade)

## Próximos passos
- Onda 4: FOGO (primeiro domínio completo com identidade + 30 habilidades)
- ATUALIZAR docs se algo mudar na arquitetura
- ATUALIZAR Pendências.md ao final de cada conversa
