# Catalogo de Documentacao MCR

> Gerado por scripts/doc-sync.py em 2026-06-24
> Leia este arquivo no inicio de toda conversa para saber quais docs carregar.

## Tabela de Decisao Rapida

| Sua tarefa envolve... | Leia |
|---|---|
| LOS, visao, BattleList, projeteis, multi-piso | DevLog/Sistema Multi-Piso.md |
| SPA, dominios, habilidades, progressao, Maestria | [Documentacao] MCR - Documentacao Tecnica do Motor SPA.txt + [Documentacao] MCR - Filosofia do SPA...txt |
| Montaria como summon, pets | [Documentacao] MCR - Sistema de Montaria como Summon (MountSummon).txt + DevLog/Sistema de Montarias.md |
| Perseguicao multi-piso, pathfinding, monster AI | [Documentacao] MCR - Sistema de Perseguicao Multi-Piso.txt + DevLog/Sistema Multi-Piso.md |
| Compilacao (servidor) | AGENTS.md §8 + Guia [1] |
| Compilacao (cliente) | AGENTS.md §8 + Guia [2] |
| Configuracao de servidor/rede | Guia [3] |
| Login Server, API REST, autenticacao | Guia [4] |
| Interface OTUI, Lua cliente | Guia [5] |
| Narrativa, dialogos, NPCs, cores | Guia [6] + Guia [11] |
| Quests, SQH, HUD, toasts | Guia [7] |
| Criacao de conta, personagem, Oráculo | Guia [8] |
| Banco de dados, schema MySQL | Guia [9] |
| Traducao, localizacao, encoding | Guia [10] + DevLog/Sistema de Codificacao.md |
| Criacao de habilidades, game design | Guia [13] + [Gabarito] Habilidade Gabarito.txt |
| Identidade de dominios, design narrativo | [Personalidade] MCR - Personalidade e Identidade de Dominios.txt |
| Lista de itens, IDs, atributos | [Aquivo Complementar] Lista de Items Uteis.txt |
| Visao geral do projeto, pilares, roadmap | Guia [0] (Indice Geral) |
| Tarefas pendentes, estado atual, planejamento | DevLog/Pendencias.md |
| Tutorial, Eridanus, novo jogador | Guia [12] |

## Indice Completo

| Arquivo | Tags | Atualizado | Resumo |
|---|---|---|---|
| `DevLog\Pendências.md` | `todo, next-steps, roadmap, pendencias` | 2026-06-24 | Estado atual do projeto, tarefas pendentes e decisoes em aberto |
| `DevLog\Sistema Multi-Piso.md` | `multi-piso, los, battlelist, navigation, combat, monster-ai` | 2026-06-23 | Decisoes e historico do sistema multi-piso: LOS, BattleList, perseguicao, navegacao do jogador |
| `DevLog\Sistema de Codificação.md` | `encoding, utf-8, devlog` | 2026-06-23 | Decisoes e historico sobre encoding e padronizacao UTF-8 |
| `DevLog\Sistema de Montarias.md` | `mounts, summon, devlog` | 2026-06-23 | Decisoes e historico do sistema MountSummon |
| `[0] MCR - INDICE GERAL.txt` | `index, overview, geral` | 2026-06-23 | Indice geral do projeto, pilares permanentes, estado da implementacao e indice de todos os guias |
| `[10] MCR - Guia de Tradução e Localização (PT‑BR).txt` | `translation, localization, pt-br, encoding` | 2026-06-23 | Codificacao por tipo de arquivo, error codes, pipeline de traducao |
| `[11] MCR - Guia de Experiência do Jogador.txt` | `player-experience, journey, overview` | 2026-06-23 | A jornada completa do jogador, do Alma ao heroi |
| `[12] MCR - Guia de Conteúdo Inicial e Tutorial.txt` | `tutorial, eridanus, new-player` | 2026-06-23 | Tutorial de Eridanus, NPCs, missoes iniciais |
| `[13] MCR - Guia de Criacao de Habilidades.txt` | `skills, abilities, game-design` | 2026-06-23 | Filosofia de design, estrutura por hierarquia, pacotes tematicos, processo de geracao |
| `[1] MCR - Guia de Compilação (Servidor).txt` | `compilation, server, canary, build` | 2026-06-23 | Compilacao do servidor Canary com SPA e sistema de perseguicao multi-piso |
| `[2] MCR - Guia de Compilação (Cliente).txt` | `compilation, client, otclient, build` | 2026-06-23 | Compilacao do OTClient com opcodes e mascara de Alma |
| `[3] MCR - Guia de Configuração (Servidor e Rede).txt` | `config, network, server` | 2026-06-23 | Configuracao de portas, storages, opcodes e OTCFeatures |
| `[4] MCR - Guia do Login Server.txt` | `login-server, auth, api` | 2026-06-23 | API REST do Login Server, endpoints, error codes e guest accounts |
| `[5] MCR - Guia de Interface (OTUI e Lua Cliente).txt` | `interface, otui, lua-client` | 2026-06-23 | Sintaxe OTUI, fontes, codificacao, opcodes visuais |
| `[6] MCR - Guia de Narrativa e Diálogos.txt` | `narrative, npc, dialogs` | 2026-06-23 | Imersao narrativa, personalidade de NPCs, sistema de cores |
| `[7] MCR - Guia de Quests (Sistema Híbrido SQH).txt` | `quests, sqh, missions` | 2026-06-23 | Criacao de missoes com HUD, toasts e integracao SPA |
| `[8] MCR - Guia de Criação de Conta e Personagem.txt` | `account, character, oracle, alma` | 2026-06-23 | Fluxo do Salao dos Destinos, Oráculo, Alma, pronomes |
| `[9] MCR - Guia de Banco de Dados e Infraestrutura.txt` | `database, schema, infrastructure` | 2026-06-23 | Schema do banco, tabelas do SPA, populacao inicial de dominios |
| `[Aquivo Complementar] Lista de Items Uteis.txt` | `items, reference, list` | 2026-06-23 | Lista com mais de 3000 itens traduzidos, IDs e atributos |
| `[Documentação] MCR - Documentação Técnica do Motor SPA.txt` | `spa, technical, api, progressao, dominios` | 2026-06-23 | Documentacao tecnica completa de todas as APIs C++ do SPA, metodos e sistemas |
| `[Documentação] MCR - Filosofia do SPA – Sistema de Progressão do Aventureiro.txt` | `spa, philosophy, design, vision` | 2026-06-23 | Visao filosofica e canonica do Sistema de Progressao do Aventureiro |
| `[Documentação] MCR - Sistema de Montaria como Summon (MountSummon).txt` | `mounts, summon, pet` | 2026-06-23 | Sistema de montaria como summon persistente: eventos C++, Lua mount_summon.lua, PetSystem |
| `[Documentação] MCR - Sistema de Perseguição Multi-Piso.txt` | `multi-piso, pursuit, pathfinding, monster-ai, crowd-control` | 2026-06-23 | Sistema de perseguicao multi-piso v8 com GlobalMonsterMap, cercamento, anti-ping-pong |
| `[Gabarito] Habilidade Gabarito.txt` | `skills, template, reference, game-design` | 2026-06-23 | Referencia maxima de todos os campos e regras para criacao de habilidades |
| `[Personalidade] MCR - Personalidade e Identidade de Dominios.txt` | `domains, design, narrative, identity` | 2026-06-23 | Guia universal de design narrativo e mecanico para criacao de dominios |
