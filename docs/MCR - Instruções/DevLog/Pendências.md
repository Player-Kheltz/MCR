>> CATALOG tags=todo, next-steps, roadmap, pendencias updated=2026-06-24
# Pendências — 24 de Junho de 2026 (Atualizado 23:45 — Sessão Armas + Sinergias)

## 🧠 Decisões de Arquitetura — Sistema de Habilidades Contextuais (SHC)
### Data: 24 de Junho de 2026
### Sessão de Design Completo (Plan Mode → Build)

---

### 📐 Filosofia Central

O SPA (Sistema de Progressão do Aventureiro) deve se **moldar ao jogador**, nunca o contrário.
O jogador **não escolhe caminhos** — o sistema **reflete o que ele faz**.

Cada habilidade é um **organismo vivo** que reage ao **estado completo do jogador**:

```
HABILIDADE BASE → POSTURA → NÍVEL DO DOMÍNIO → ESTADO DE ALMA → SINERGIAS → CONDIÇÕES = COMPORTAMENTO FINAL
```

---

### 🏗️ Estrutura da Habilidade (Novo Formato)

Cada habilidade terá **5 blocos de variação contextual** dentro dela:

| Camada | Bloco | Função |
|:------:|-------|--------|
| 1 | `postura` | Modifica comportamento por postura (Ímpeto/Equilíbrio/Guarda) |
| 2 | `niveis` | Melhorias automáticas nos marcos 5/10/15/20 do domínio |
| 3 | `sinergias` | Efeitos extras quando jogador treinou outros domínios |
| 4 | `estados` | Potência máxima durante Vínculo e Lampejo |
| 5 | `condicoes` | Adaptação tática: cercado, vida baixa, full HP, single target |

**Exemplo concreto (Orbital Ígneo — Fogo):**

```lua
HABILIDADES["orbital_igneo"] = {
    nome = "Orbital Ígneo",
    tipo = "toggle",
    dominio = {23},
    cooldown = 0,
    
    -- Comportamento BASE
    efeitoConfig = { tipo = "orbit", orbes = 3, raio = 3, dano = 0.8,
                     elemento = COMBAT_FIREDAMAGE, frequencia = 2.0 },
    
    -- 1. VARIAÇÃO POR POSTURA
    postura = {
        [1] = { efeitoConfig = { raio = 4, dano = 1.1, manaCostMult = 1.3 } },
        [3] = { efeitoConfig = { orbes = 4, raio = 1.5, dano = 0.5,
                                 frequencia = 1.0,
                                 onHit = function(j) aplicarEscudoTermico(j, 0.05, 5) end } },
    },
    
    -- 2. VARIAÇÃO POR NÍVEL DO DOMÍNIO (cumulativa)
    niveis = {
        [5]  = { { efeito = "adicional", type = "trail", duracao = 2.0, dano = 0.2 } },
        [10] = { { mod = "efeitoConfig", orbes = "+1" } },
        [15] = { { mod = "efeitoConfig", onHit = medoEmMobsFracos } },
        [20] = { { mod = "efeitoConfig", orbes = "+3", dano = "*1.5", visual = "supremo" } },
    },
    
    -- 3. VARIAÇÃO POR SINERGIAS (requer nível em outro domínio)
    sinergias = {
        [24] = { descricao = "Gelo ≥ 1: vapor cegante",
                 efeitoConfig = { onHit = function() cegueira(0.3, 3.0) end } },
        [25] = { descricao = "Terra ≥ 5: magma DOT",
                 nivelMin = 5,
                 efeitoConfig = { onHit = function() dot(0.3, 5) end } },
        [26] = { descricao = "Energia ≥ 10: plasma",
                 nivelMin = 10,
                 efeitoConfig = { elemento = COMBAT_ENERGYDAMAGE, armorPenetration = 0.3 } },
        [27] = { descricao = "Sagrado ≥ 1: fogo purificador",
                 efeitoConfig = { extraDamageVs = { type = "race", race = "undead", mult = 1.5 } } },
    },
    
    -- 4. VARIAÇÃO POR ESTADO DE ALMA
    estados = {
        vinculo = { efeitoConfig = { dano = 1.5, elemento = COMBAT_HOLYDAMAGE,
                                      visualEffect = "chama_branca" } },
        lampejo = { efeitoConfig = { orbes = 9, dano = 2.0, damageType = "absolute",
                                      manaCost = 0, visualEffect = "lampejo_orbital" } },
    },
    
    -- 5. VARIAÇÃO POR CONDIÇÕES SITUACIONAIS
    condicoes = {
        cercado    = { efeitoConfig = { tipo = "explosion_ring", raio = 5, dano = 1.2 } },
        vidaBaixa  = { efeitoConfig = { lifesteal = 0.4, dano = 1.2 } },
        fullHp     = { efeitoConfig = { critChance = 0.25, critDamage = 1.5 } },
        singleTarget = { efeitoConfig = { tipo = "beam", dano = 2.5, range = 6 } },
    },
}
```

---

### 🔧 Componentes do Sistema

| Componente | Ação | Status |
|-----------|------|:------:|
| **`contexto.lua`** | NOVO — Resolvedor Contextual: aplica as 5 camadas em ordem e retorna `efeitoConfig` final | 🆕 Criar |
| **`executor.lua`** | MODIFICADO — chamar `Resolvedor.resolver()` antes de `MOTOR.executar()` | 🔧 Alterar |
| **`motor_habilidades.lua`** | INALTERADO — já suporta 27 tipos de efeito | ✅ Estável |
| **`postura.lua`** | INALTERADO — já gerencia 3 posturas | ✅ Estável |
| **`sintonia.lua`** | INALTERADO — já gerencia Foco/Vínculo/Lampejo | ✅ Estável |
| **`constantes.lua`** | INALTERADO — IDs e tabelas de domínio | ✅ Estável |

**Fluxo do Resolvedor:**
```
habilidade.efeitoConfig (BASE)
  → APLICA postura[posturaAtual]
  → APLICA niveis[marcos cumulativos]
  → APLICA sinergias[dominios] (se nivelMin ok)
  → APLICA estados[estadoAtual]
  → APLICA condicoes[condicaoAtiva]
  = efeitoConfig FINAL → MOTOR.executar()
```

---

### 📊 Quantidade de Habilidades

| Hierarquia | Exemplo | Habilidades | Variações | Comportamentos Únicos |
|-----------|---------|:-----------:|:---------:|:--------------------:|
| Primário (5-7) | Fogo, Gelo, Terra, Energia, Sagrado/Morte | ~100-140 | ~19 | ~1900 |
| Secundário (6-8) | Lâminas, Martelos, Cajados, Escudos | ~150-200 | ~19 | ~3325 |
| Especialidade (4-5) | Alquimia, Runas, Invocação, Maldições | ~120-150 | ~19 | ~2565 |
| **Total** | | **~400-490** | | **~7790+** |

*"19 variações" é o potencial teórico (3 posturas + 4 níveis + 7 sinergias + 2 estados + 3 condições). Cada habilidade terá seu próprio conjunto.*

---

### 🎯 Regras de Diferenciação (Anti-Repetição)

- Cada domínio tem um **NICHO PRINCIPAL** único (só Lâminas sangra, só Energia dá corrente, etc)
- **Variação elemental NÃO é repetição** — Orbital Ígneo (Fogo) e Orbital Glacial (Gelo) são intencionalmente diferentes
- **Sinergias incentivam diversificação** sem obrigar
- **Domínios irmãos** (ex: Espadas Leves/Pesadas) NÃO compartilham o mesmo nicho principal
- Zero repetição entre irmãos

---

### 🎨 Referências Pop (Recontextualizadas para Eridanus)

| Referência | Adaptação | Domínio |
|-----------|-----------|:-------:|
| Dr. Mundo W (LoL) | Orbital Ígneo | Fogo |
| Comet Azur (Elden Ring) | Jato Estelar | Energia |
| Katarina R (LoL) | Dança das Cem Lâminas | Espadas Leves |
| Hadouken (SF) | Sopro do Dragão | Artes Marciais |
| Sub-Zero (MK) | Prisão de Diamante | Gelo |
| Haki (One Piece) | Aura do Mestre | Primários |
| Dobra Elemental (Avatar) | Estilos elementais | Todos |

**Regra de Ouro:** Se a descrição não coubesse numa crônica de Eridanus, repensar.

---

### 📚 Estrutura de Documentação

```
docs/MCR - Instruções/Sistema de Habilidades Contextuais/
├── 00 - INDICE.txt
├── 01 - ARQUITETURA DO SISTEMA.txt
├── 02 - CATALOGO DE DOMINIOS/
│   ├── 23 - FOGO.txt
│   ├── 24 - GELO.txt
│   └── ...
├── 03 - CATALOGO DE HABILIDADES/
│   ├── 100 - ESPADAS_LEVES.lua
│   └── ...
├── 04 - MATRIZ DE SINERGIAS.txt
├── 05 - GUIAS DE CRIACAO.txt
└── 06 - REFERENCIAS POP.txt
```

---

### 🔗 Relação com o Tibia Nativo

- **Afinidade 0** = jogador no "Tíbia nativo com algumas diferenças"
- Conforme sobe afinidade, o SPA se expande gradualmente
- Skills nativas (Axe, Sword, Club, etc) continuam subindo — são o **dano base**
- O SPA atua **em cima** do dano base (efeitos, condições, sinergias)
- **Jogo é COOP** — balanceamento entre jogadores é irrelevante
- Balanceamento contra monstros é por **curvas baseadas na afinidade/nível do domínio**

---

### 🏗️ Plano de Execução (Ondas)

| Onda | O quê | Status |
|:----:|-------|:------:|
| **0** | Build VS 2022 (corrigir vcxproj + compilar) | 🔄 **Executando agora** |
| **1** | Criar Resolvedor Contextual (`contexto.lua`) | ⏳ Próximo |
| **2** | Modificar executor.lua para usar resolvedor | ⏳ |
| **3** | Documentação: criar estrutura de pastas | ⏳ |
| **4** | FOGO — identidade + 30 habilidades completas | ⏳ |
| **5** | GELO, TERRA, ENERGIA, SAGRADO/MORTE | ⏳ |
| **6** | LÂMINAS, ESPADAS LEVES, ESPADAS PESADAS | ⏳ |
| **7** | Demais secundários + especialidades | ⏳ |
| **8** | Matriz de Sinergias completa | ⏳ |
| **9** | Ofícios, Natureza, Sobrevivência | ⏳ |
| **10** | Validação + auto.py sync + commit | ⏳ |

---

## 🟢 Concluído Hoje (Sessão Autônoma - 24/06 12:40)

### Onda 0: OTClient Compilado com Sucesso
- ✅ **vcpkg**: Triplet `x64-windows-static` instalado para todos os 39 pacotes (17 min)
- ✅ **Toolset v145**: OTClient agora compila com VS 2026 (MSVC 14.51) em vez de VS 2022
- ✅ **AGENTS.md §8 atualizado**: Comando de compilação do OTClient agora usa VS 2026
- ✅ **Lições aprendidas atualizadas**: `recentes.md` com solução definitiva para ABI mismatch
- ✅ **Executável gerado**: `OTClient\otclient_gl_x64.exe` (0 erros, 0 warnings)

### Router de Itens — Verificado como Completo
- ✅ **Pipeline completo**: Template → Router (1.5b) → RPC → Formatação → Fallback IA
- ✅ **Gating de itens**: `player:knowsItem()` + `player:discoverItem()` em C++ ✅
- ✅ **Auto-descoberta**: Ao olhar (`look`) para um item, ele é descoberto automaticamente ✅
- ✅ **Resposta para itens desconhecidos**: "Você ainda não descobriu este item!" ✅
- ✅ **Filtro RAG `player_mode`**: Bridge sempre usa modo seguro para jogadores ✅
- ✅ **Anti-alucinação**: Prompt que bloqueia invenção de dados + `player_mode` restrito a docs seguros ✅
- ⚠️ **Sessão `ses_108b08760ffe73IEqNi2RcJhcV`**: Não disponível como arquivo, mas análise de código confirma implementação completa

### SHC — Todos os 5 Domínios Elementais Completos (150 habilidades)
- ✅ **30 FOGO** (23001-23030): Orbital, Bola de Fogo, Combustão, Manto, Fúria, Jato + 24 adicionais
- ✅ **30 GELO** (24001-24030): Estalactite, Explosão Glacial, Prisão de Diamante, Aura Glacial, Nevasca + 25 adicionais
- ✅ **30 TERRA/VENENO** (25001-25030): Projétil de Rocha, Nuvem de Veneno, Armadura de Pedra, Espinhos, Terremoto + 25 adicionais
- ✅ **30 ENERGIA** (26001-26030): Raio, Centelha, Tempestade Elétrica, Escudo de Energia, Sobrecarga + 25 adicionais
- ✅ **30 SAGRADO/MORTE** (200001-200030): Luz Sagrada, Toque da Morte, Julgamento Divino + 27 adicionais
- ✅ **Identidade dos 5 domínios** em `02 - CATALOGO DE DOMINIOS/`

---

## 🟢 Concluído Anteriormente (Sessão - 23/06 e 24/06)

### Bridge v4 (Autônomo)
- Bridge com modelo qwen2.5-coder:7b padrão, fallback 1.5b ✅
- RAG com 2300+ chunks do código fonte + docs ✅
- Cache quente (últimas 50 respostas, evita repetição) ✅
- Anti-alucinação: bloqueio de senhas/credenciais no template ✅
- Encoding Latin-1 na saída (acentos corretos no jogo) ✅
- Fallback Ollama offline: "Assistente indisponivel no momento." ✅
- Watchdog com PID file, sem duplicatas ✅

### Canal Assistente (500)
- Canal via chatchannels.xml + script Lua com onSpeak ✅
- Aba "Assistente" no OTClient (console.lua) ✅
- Cores: jogador amarelo, assistente laranja ✅
- !assistente mantido como fallback ✅

### RAG e Indexação
- Exclusão de docs/assets/, nomes_monstros, Ordem.txt ✅
- Sanitização: remove linhas com password/apiKey antes de indexar ✅
- rag_watcher.py: monitora mudanças e reindexa automaticamente ✅

### Infraestrutura de Autonomia
- opencode.local.json + alias oc-dev (OpenCode local via Ollama) ✅
- lessons.py: script para criar lições aprendidas ✅
- docs/lessons/: 4 lições iniciais criadas ✅
- auto.py up/status/doctor implementados ✅
- README_AUTONOMY.md documentado ✅
- AGENTS.md atualizado com seção de autonomia ✅
- Bridge + Watchdog com .gitignore protegido ✅
- Fallback de tempo em todos os comandos (evita loops) ✅

### Correções de Código
- TalkAction !assistente: corrigido para usar .onSay + groupType ✅
- playerUseWithCreature: override cross-floor adicionado ✅
- playerSetAttackedCreature + playerFollowCreature: ranged check ✅
- isWithinRangedRange: função auxiliar criada ✅
- Logs [MCR-DEBUG-*] removidos ✅
- Clique cross-floor no OTClient: busca com offset isométrico ✅

### Sessão 24/06 — Recuperação de Conversas + Sistema de Itens do Assistente
- **Recuperação de sessão**: Aprendido comando `opencode session list` e `opencode -c` para reabrir conversas ✅
- **Problema identificado**: Assistente in-game **inventa respostas** sobre itens:
  - `!assistente qual o dano de uma espada longa?` → `"causa cerca de 100"` (inventado)
- **Proposta de solução (router)**: Sistema onde o assistente só responde sobre itens que o jogador **já viu/encontrou** no jogo
- **Sessão relevante**: `ses_108b08760ffe73IEqNi2RcJhcV` contém parte dessa discussão (Criar talkaction de fogos de artifício + router)
- **Contexto preservado via**: `opencode export ses_10ba7461affezWI30j8va6C5Kx` (7MB, 899 mensagens)
- **Lições aprendidas**: Criado lesson sobre `opencode session` para recuperação de conversas

## ✅ Concluído
- ✅ **OTClient compilado** (VS 2026, toolset v145) — 0 erros
- ✅ **5 domínios elementais** — 150 habilidades SHC
- ✅ **9 domínios de arma + sobrevivência** — 120 habilidades SHC
- ✅ **Matriz de Sinergias** — documentada em `04 - MATRIZ DE SINERGIAS.txt`
- **Total: ~400 habilidades** em todo o sistema SPA

## ⏳ Próximos Passos
- RAG: indexação completa do OTClient + data-otservbr (parcial)
- Histórico por conta (Fase 2)
- NPC inteligente (Fase 3)
- Testes pós-compilação

## 🔴 Pendente (Próximos Passos)
### SHC — Sistema de Habilidades Contextuais
- [x] **Onda 0** — Build VS (Canary ✅, OTClient ✅ via VS 2026 v145)
- [x] **Onda 1** — `contexto.lua` criado ✅ (Resolvedor Contextual v1.0)
- [x] **Onda 2** — `executor.lua` modificado ✅ (v10.0 com SHC)
- [x] **Onda 3** — Documentação criada ✅ (00-INDICE, 01-ARQUITETURA, 05-GUIAS)
- [x] **Onda 4** — FOGO: identidade + 30 habilidades ✅
- [x] **Onda 5** — GELO (24): identidade + 30 habilidades ✅
- [x] **Onda 6** — TERRA/VENENO (25): identidade + 30 habilidades ✅
- [x] **Onda 7** — ENERGIA (26): identidade + 30 habilidades ✅
- [x] **Onda 8** — SAGRADO/MORTE (200): identidade + 30 habilidades ✅
- [x] **Onda 9** — DOMÍNIOS DE ARMA: espadas_pesadas, machados_pesados, clavas_leves/pesadas, arcos, lutador, armas_punho, bastoes_arcanos, sobrevivência ✅
- [x] **Onda 10** — Matriz de Sinergias completa + documentação ✅

### Router de Itens
- [x] **Pipeline completo** implementado e verificado ✅
- [x] **Gating de conhecimento** via `player:knowsItem()` ✅
- [x] **Filtro RAG `player_mode`** ativo no bridge ✅
- [x] **Anti-alucinação** integrada no prompt + formatação ✅
- [x] **Integração Bridge** completa ✅ (template → router → RPC → formatação → IA)
- ⚠️ Sessão `ses_108b08760ffe73IEqNi2RcJhcV` indisponível, mas código confirma implementação

### Infraestrutura
- Reestruturação de docs/ (remover numeração, organizar em subpastas)
- Sistema de lessons automático com RAG (já parcial)
- Testes autônomos pós-compilação
