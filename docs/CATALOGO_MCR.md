# Catálogo MCR — Organizado por Função

> **LEIA ANTES de criar qualquer código novo.**
> **CONSULTE para saber se algo já existe antes de implementar.**
> Versão: 1.0 | Data: 2026-07-12

---

## Como usar este catálogo

```
TENHO UM PROBLEMA: "quero conectar sprite a texto"
  → Busco neste catálogo por "conexão" ou "ponte"
  → Encontro: MCRConexao (emergence/conexao.py)
  → Vejo que ele aceita dois tópicos e retorna pontes
  → Uso SEM criar nada novo
```

---

## 1. NÚCLEO MARKOV (engine MCR)

O coração do MCR. Tudo é transição entre dois estados consecutivos.

### `MCR` — Markov 1ª ordem universal
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/engine.py` |
| **Classe** | `MCR` (linha 13) |
| **Métodos** | `aprender(a, b)`, `aprender_sequencia(seq)`, `aprender_batch(seqs)`, `predizer(a)`, `predizer_n(a, n)`, `gerar(semente, passos)`, `entropia(a)`, `entropia_media()`, `jaccard(outra)`, `jaccard_transicoes(outra)`, `stats()`, `entropia_sequencia(seq)` |
| **Depende de** | `collections.Counter`, `math` |
| **Usado por** | ~50 módulos em todo o ecossistema |
| **O que faz** | Aprende P(B\|A) = count(A→B)/count(A). 256 valores byte, N tokens. |
| **Notas** | N=1 fixo. Em memória (dict aninhado). |

### `MCRSQLite` — Markov N-adaptativo com persistência
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/mcr_sqlite.py` |
| **Classe** | `MCRSQLite` (linha 18) |
| **Métodos** | Mesma API de `MCR` + `aprender_batch()`, `salvar()` |
| **Depende de** | `sqlite3`, `math`, `re` |
| **Usado por** | `MCRSpriteMotor` |
| **O que faz** | Mesmo algoritmo de MCR mas em SQLite. N-adaptativo até 30. Sem RAM blowup. |
| **Notas** | Cache 64MB + mmap 256MB. WAL mode. `synchronous=NORMAL`. |

### `MCRSQLite (adaptativo, nichos)` — Versão nichos/tibia
| Campo | Valor |
|-------|-------|
| **Path** | `nichos/tibia/mcr_adapt.py` |
| **Classe** | `SQLiteMarkov` (linha 20) |
| **Métodos** | `alimentar(identity, tokens)`, `commit()`, `obter_distribuicao(identity, contexto)`, `predizer_adaptativo(identity, contexto)` |
| **Depende de** | `sqlite3`, `re` |
| **O que faz** | N-adaptativo até 30 com identidade. Usado para NPCs. |
| **Notas** | `synchronous=OFF`. 8MB cache. ~4M transições típico. |

### `MCR (legado, 311KB)` — Monolito original
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/MCR_legacy.py` |
| **Classes** | 60+ (MCR, MCRByteUtils, MCRSignatureExpansiva, MCRSuperposicao, MCREsfera, MCRAutoTopologia, MCRTokenizadorUniversal, CerebroAGI, etc.) |
| **Status** | ✅ DESMEMBRADO em `mcr_kernel/`. Manter apenas para referência. |

---

## 2. FINGERPRINT / ASSINATURA

Identificam dados de QUALQUER domínio por distribuição de bytes.

### `MCRFingerprint` — Fingerprint 8D universal
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/signature.py` |
| **Classe** | `MCRFingerprint` (linha 14) |
| **Métodos** | `gerar(texto)` → 8-dim fingerprint, `extrair_estilo(texto)` → 11-dim style |
| **Depende de** | `collections.Counter`, `math` |
| **O que faz** | 8 buckets: lowercase, uppercase, digits, space, punct, low, high, other. Normalizado para soma=10. |
| **Notas** | Universal: funciona em QUALQUER dado de bytes. |

### `MCRSignature` — Assinatura completa com cache
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/signature.py` |
| **Classe** | `MCRSignature` (linha 90) |
| **Métodos** | `extrair(dados)` → {entropia, estados, transicoes, fingerprint, tamanho}, `comparar(a, b)`, `extrair_palavras(texto)`, `comparar_palavras(a, b)`, `metaniveis(dados)` → descobre níveis intrínsecos, `identificar(dados, banco)` |
| **O que faz** | Extrai fingerprint + entropia + estados de QUALQUER dado. Cache por hash. |
| **Notas** | Use `metaniveis()` para descobrir quantos níveis de Markov um dado precisa. |

### `MCRSignatureExpansiva` — Dimensionalidade auto-descoberta
| Campo | Valor |
|-------|-------|
| **Path** | `prototypes/mcr-universal/mcr_universal/core/signature.py` |
| **Classe** | `MCRSignatureExpansiva` (linha 10) |
| **Métodos** | `fingerprint(dados, n_dims)`, `fingerprint_texto(texto, n_dims)`, `similaridade(fp_a, fp_b)`, `entropia_fingerprint(fp)`, `dimensionalidade_ideal(dados)` → descobre N ideal, `niveis_ideais(dados)` → descobre níveis relevantes |
| **O que faz** | Testa 2,4,8,16... dimensões até fingerprint estabilizar (cosseno > 0.99). |
| **Notas** | Use `dimensionalidade_ideal(bytes_sprite)` para saber quantos bits de cor usar. |

### `raw_token_set` — Tokenização sem parser
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/signature.py` (linha 236) |
| **Funções** | `raw_token_set(texto)` → Set[str], `raw_token_set_from_file(path)` → Set[str] |
| **O que faz** | Divide texto por delimitadores universais `{}();.,:[]"'`/\\#<>!=+-*%&\|^~@?`. Retorna SET (perde ordem). |
| **Notas** | Use `list(raw_token_set(texto))` se precisar de ordem. |

### `MCRByteUtils` — Utilitários de byte
| Campo | Valor |
|-------|-------|
| **Path** | `prototypes/mcr-universal/mcr_universal/core/byte_utils.py` (linha 7) |
| **Métodos** | `transicoes_bytes(texto)`, `jaccard_bytes(a, b)`, `similaridade_cosseno(a, b)`, `entropia_bytes(dados)`, `fingerprint(texto, dims=8)` |
| **O que faz** | Byte-level Jaccard, coseno, entropia, fingerprint. |
| **Notas** | Similar ao MCRFingerprint mas com foco em byte transições. |

---

## 3. THRESHOLDS / DECISÃO

Adaptam parâmetros automaticamente observando dados reais.

### `MCRThreshold` — Threshold adaptativo
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/decisor.py` (linha 263) |
| **Classe** | `MCRThreshold` |
| **Métodos** | `observar(valor)`, `calcular(multiplicador)`, `obter(chave, fallback)`, `aprender(chave, valor)` |
| **O que faz** | Mediana de observações + Markov. Fallback: mediana. |
| **Notas** | Use para TUDO que hoje é hardcoded: temperatura, bits, limiares. |

### `MCRDecisor` — Decisor de ações
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/decisor.py` (linha 104) |
| **Classe** | `MCRDecisor` |
| **Métodos** | `aprender(estado, acao, sucesso)`, `decidir(pergunta, estado_extra)`, `decidir_pular_parser(entropia, similaridade)` |
| **O que faz** | Aprende P(ação \| estado). Decide qual ação tomar baseado em entropia. |
| **Notas** | Use para rotear: "gerar via palavra vs byte vs token". |

### `MCRPesoNota` — Descoberta de pesos ótimos
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/decisor.py` (linha 217) |
| **Classe** | `MCRPesoNota` |
| **Métodos** | `aprender(caracteristicas, nota_real)`, `calcular(byte_s, palavra_s, token_s)` |
| **O que faz** | Aprende pesos ideais para equação NOTA = (byte + palavra + token) × penalidade. |
| **Notas** | Use para calcular qualidade de sprite: `peso_nota.calcular(byte_s=0.7, palavra_s=0.5, token_s=0.3)`. |

### `MCREntropia` — Detector de loop
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/decisor.py` (linha 48) |
| **Classe** | `MCREntropia` |
| **Métodos** | `alimentar(token)`, `esta_em_loop()` |
| **O que faz** | Mantém rolling history de 10 entropias. Loop se H < 0.3. |
| **Notas** | Use para detectar se geração está repetindo. |

### `MCRRuido` — Aprendizado de ruído
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/decisor.py` (linha 71) |
| **Classe** | `MCRRuido` |
| **Métodos** | `tentar(tipo, estado)`, `registrar(tipo, sucesso)`, `melhor_tipo()`, `taxa_sucesso(tipo)` |
| **O que faz** | Aprende qual tipo de ruído quebra loop. Tipos: byte_global, palavra_outro_topico, pontuacao, semente_original. |
| **Notas** | Use quando `esta_em_loop()` = True. |

### `MCRDiagnostico` — Diagnóstico Markov
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/decisor.py` (linha 189) |
| **Classe** | `MCRDiagnostico` |
| **Métodos** | `alimentar(estado, diagnostico)`, `diagnosticar(estado)` |
| **O que faz** | Aprende P(diagnóstico \| estado). Codifica estado em baixo/medio/alto. |

---

## 4. EMERGÊNCIA / CONEXÕES

Conectam domínios diferentes através de pontes semânticas.

### `MCRConexao` — Ponte ótima entre tópicos
| Campo | Valor |
|-------|-------|
| **Path** | `prototypes/mcr-universal/mcr_universal/emergence/conexao.py` (linha 18) |
| **Classe** | `MCRConexao` |
| **Métodos** | `analisar(topic_a, topic_b)` → pontes, `melhor_ponte(topic_a, topic_b)`, `relatorio()` |
| **Fórmula** | `score = (divergencia*5 + especificidade*3 + profundidade*2) / 10` |
| **O que faz** | Encontra a melhor palavra-ponte entre dois tópicos. Fallback byte-bridge. |
| **Notas** | **Use para conectar SPRITE a TEXTO**: extraia tokens de ambos, alimente como tópicos, encontre pontes. |

### `MCRCruzado` — Análise cruzada (memória)
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/memory.py` (linha 44) |
| **Classe** | `MCRCruzado` |
| **Métodos** | `analisar(topic_a, topic_b)`, `melhor_ponte(a, b)`, `_avaliar_ponte(candidato, a, b)` |
| **O que faz** | Mesmo algoritmo de MCRConexao mas integrado ao sistema de memória. |
| **Notas** | Use quando precisar de persistência (KG). |

### `MCRConector` — Conector multi-nível
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/memory.py` (linha 139) |
| **Classe** | `MCRConector` |
| **Métodos** | `alimentar(texto, topico)`, `alimentar_json(arquivo)`, `conectar(a, b)`, `explorar_todos()`, `debug()` |
| **O que faz** | Mantém 3 MCRs globais (byte, word, token). Para cada tópico, cria byte+word MCRs. Conecta tópicos via MCRCruzado. |
| **Notas** | **O orquestrador multi-domínio ideal.** Alimente com texto E sprite tokens. |

### `MCRMotor` — Motor multi-nível (emergence)
| Campo | Valor |
|-------|-------|
| **Path** | `prototypes/mcr-universal/mcr_universal/emergence/motor.py` (linha 18) |
| **Classe** | `MCRMotor` |
| **Métodos** | `alimentar(texto, topico)`, `alimentar_json(arquivo)`, `conectar(a, b)`, `explorar_todos()`, `gerar_por_assinatura(texto)`, `salvar()`, `carregar()` |
| **O que faz** | 3 níveis (byte/palavra/token). Multi-level bridge. Geração por assinatura. |
| **Notas** | **Base para MCRSpriteMotor.** O sprite motor seguiu EXATAMENTE este padrão. |

### `MCRCadeia` — Gerador de cadeia (loop-safe)
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/memory.py` (linha 393) |
| **Classe** | `MCRCadeia` |
| **Métodos** | `gerar(semente, passos, contexto)` |
| **O que faz** | Gera N tokens sem repetição. Troca de nível se detecta loop. Usa compose_state para contexto. |
| **Notas** | **Use para geração com loop detection.** Melhor que MCR.gerar() direto. |

### `EmergirCrossModal` — Conexão cross-domínio
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/emergir_crossmodal.py` (linha 204) |
| **Classe** | `EmergirCrossModal` |
| **Métodos** | `despachar(ideia, dominios)`, `listar_dominios()` |
| **Handlers** | `LuaHandler` (código), `VisualHandler` (sprite), `AudioHandler`, `TextoHandler` |
| **O que faz** | Despacha ideias para múltiplos domínios. Cada handler converte a ideia em representação específica. |
| **Notas** | **Use para gerar sprite a partir de descrição textual.** |

### `SignatureAnalyzer` — Descoberta automática de tipos
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/mcr_signature_cluster.py` (linha 124) |
| **Classe** | `SignatureAnalyzer` |
| **Métodos** | `clusterizar(threshold)` → [SignatureCluster], `classificar(assinatura)` → (nome, confianca), `entropia_entre_clusters()`, `meta_clusterizar(threshold)` |
| **O que faz** | Agrupa entidades por similaridade de assinatura Jaccard. Descobre tipos automaticamente. |
| **Notas** | **Use para descobrir tipos de sprite automaticamente.** Alimente fingerprints de sprite, ele clusteriza em Type_A, Type_B. |

### `SignatureCluster` — Um cluster descoberto
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/mcr_signature_cluster.py` (linha 48) |
| **Classe** | `SignatureCluster` |
| **Métodos** | `adicionar(entidade)`, `similaridade(entidade)`, `similaridade_raw(tokens)`, `calcular_entropia()`, `get_nome_legivel()`, `computar_raw_fingerprint()` |
| **O que faz** | Cada cluster = um "tipo" descoberto (Type_A). Tem assinatura média e raw fingerprint. |
| **Notas** | Use `similaridade()` para classificar sprite desconhecido contra clusters existentes. |

---

## 5. MEMÓRIA / KG

Armazenam e recuperam conhecimento aprendido.

### `MCRBufferKG` — Buffer de KG
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/memory.py` (linha 577) |
| **Classe** | `MCRBufferKG` |
| **Métodos** | `aprender(erro, solucao, ctx)`, `flush()`, `buscar(termo)` |
| **O que faz** | Buffer singleton. Acumula lessons e faz flush em lote de 20. |

### `MCRKGAuto` — Auto-organização de KG
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/memory.py` (linha 631) |
| **Classe** | `MCRKGAuto` |
| **Métodos** | `categorizar()`, `dedup()`, `limpar()`, `organizar()`, `registrar_consumo()` |
| **O que faz** | Categoriza lessons por prefixo, deduplica (Jaccard > 0.95), limpa (qualidade < threshold). |

### `KnowledgeGraph` (modules) — KG principal
| Campo | Valor |
|-------|-------|
| **Path** | `devia/modules/kg.py` (linha 77) |
| **Classe** | `KnowledgeGraph` |
| **Métodos** | `buscar(termo)`, `aprender(erro, solucao, ctx)`, `purgar()`, `estatisticas()` |
| **O que faz** | KG baseado em JSON. Lessons com erro/solução/contexto. Cache LRU. |

### `EpisodicMemory` — Memória episódica
| Campo | Valor |
|-------|-------|
| **Path** | `devia/knowledge/episodic_memory.py` (linha 73) |
| **Classe** | `EpisodicMemory` |
| **Métodos** | `store(request, result, lesson)`, `search(query, k)`, `cluster()`, `log()` |
| **O que faz** | Armazena experiências com request+resultado+lição. Embeddings + fallback keyword. |

---

## 6. GERAÇÃO DE TEXTO / CÓDIGO

Geram conteúdo usando Markov.

### `MCRGeracao` — Geração com validação por assinatura
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/system.py` (linha 792) |
| **Classe** | `MCRGeracao` |
| **Métodos** | `gerar(pergunta, max_tentativas)`, `_autoavaliar(texto, pergunta)` |
| **O que faz** | Gera resposta, valida se fingerprint da resposta combina com fingerprint da pergunta. |
| **Notas** | Use para gerar texto que DEVE combinar com o contexto. |

### `MCRPergunta` — Pipeline de pergunta-resposta
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/system.py` (linha 357) |
| **Classe** | `MCRPergunta` |
| **Métodos** | `perguntar(pergunta)` |
| **O que faz** | 8-step: parse → search KG → rank by signature → connect → generate → evaluate → feedback → return. |
| **Notas** | Pipeline completo de QA. Use para responder perguntas sobre sprites. |

### `MCRSystem` — Orquestrador de ciclo único
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/system.py` (linha 205) |
| **Classe** | `MCRSystem` |
| **Métodos** | `ciclo_unico(origem, max_bytes)` |
| **O que faz** | Lê bytes → classifica por entropia → treina byte+word → salva no KG → conecta. |
| **Notas** | Use para processar um sprite do zero: bytes → classificação → KG. |

### `MCRPipeline` (nichos/tibia) — Pipeline de geração de texto
| Campo | Valor |
|-------|-------|
| **Path** | `nichos/tibia/mcr_pipeline.py` (linha 21) |
| **Classe** | `MCRPipeline` |
| **Métodos** | `executar(entrada, max_passos, contexto_extra)` |
| **O que faz** | 6 estágios: parse → contexto → pontes → fragmentos → geração → aprendizado. |
| **Notas** | Pipeline completo de geração de texto. Use como modelo para pipeline de sprite. |

### `GeradorNarrativa` — Geração de narrativa
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/system.py` (linha 99) |
| **Classe** | `GeradorNarrativa` |
| **Métodos** | `gerar(semente)`, `gerar_com_loop(semente, max_iter)` |
| **O que faz** | Gera narrativa usando Markov + KG context. |
| **Notas** | Use para gerar lore a partir de sprites. |

---

## 7. VALIDAÇÃO / QUALIDADE

Verificam se o que foi gerado é válido.

### `MCRDiscriminador` — Validador de sprite (P(token|ctx))
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/meus_olhos.py` (linha 21) |
| **Classe** | `MCRDiscriminador` |
| **Métodos** | `treinar(grids)`, `avaliar(grid)`, `diagnostico(resultado)` |
| **O que faz** | Treina com grids reais (B/L/F). Avalia P(token\|esquerda, cima). Score > 0.5 = aceitável. |
| **Notas** | **Use para validar QUALIDADE de sprite gerado.** Score real vs gerado. |

### `RadarMCR` — Busca por similaridade em 4 ondas
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/mcr_radar.py` (linha 14) |
| **Classe** | `RadarMCR` |
| **Métodos** | `buscar(consulta, candidatos)`, `expandir_consulta(texto, candidatos, resultados)`, `similaridade_visual(regioes_a, regioes_b)`, `buscar_visual(regioes_query, candidatos)`, `fingerprint_visual(regioes)`, `fingerprint_visual_sim(fp_a, fp_b)` |
| **O que faz** | 4 ondas: exata (70%) → parcial (50%) → fingerprint (30%) → contextual (10%). |
| **Notas** | **Use para validar sprite contra corpus real.** `buscar_visual()` compara por cor + geometria + posição. |

### `LuaValidator` — Validador Lua
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/lua_validator.py` (linha 38) |
| **Classe** | `LuaValidator` |
| **Métodos** | `validar(codigo)`, `_verificar_sql_injection()`, `_verificar_boas_praticas()`, `_verificar_estrutura()`, `_verificar_sintaxe()` |
| **O que faz** | Valida sintaxe Lua, SQL injection, boas práticas Canary. |

### `SanityValidator` — Validador universal
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/sanity_validator.py` (linha 24) |
| **Classe** | `SanityValidator` |
| **Métodos** | `minerar_apis()`, `validar_script(codigo, linguagem)`, `resetar_cache()` |

### `AutoavaliadorSemantico` — Auto-avaliação de texto
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/system.py` (linha 22) |
| **Classe** | `AutoavaliadorSemantico` |
| **Métodos** | `avaliar(texto)` |
| **O que faz** | Avalia texto usando MCRSignature + MCRPesoNota. |

### `MCRValidator` (prototype) — Validador universal
| Campo | Valor |
|-------|-------|
| **Path** | `prototypes/mcr-universal/mcr_universal/generate/validator.py` (linha 11) |
| **Classe** | `MCRValidator` |
| **Métodos** | `validar(texto, referencia)` |
| **O que faz** | Entropia, tamanho, Jaccard com referência, cobertura de vocabulário. |
| **Notas** | Anomalia se H < 0.3 ou H > 7.0. |

---

## 8. EVOLUÇÃO / APRENDIZADO

Melhoram o sistema continuamente.

### `MCRAutoMelhoria` — Ciclo de 7 perguntas
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/evolution.py` (linha 371) |
| **Classe** | `MCRAutoMelhoria` |
| **Métodos** | `ciclo()` — roda as 7 perguntas |
| **O que faz** | 1. gaps? 2. lento? 3. repetiu? 4. errou? 5. aprendeu? 6. precisa? 7. esqueceu? |
| **Notas** | **Use no estágio 6 do PipelineUniversal.** |

### `MCRFuel` — Auto-aprendizado de fontes
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/evolution.py` (linha 215) |
| **Classe** | `MCRFuel` |
| **Métodos** | `abastecer(fontes)`, `abastecer_se_precisar(min_uteis)` |
| **O que faz** | Varre diretórios do projeto, lê arquivos, armazena no KG. |
| **Notas** | Use para alimentar MCR com dados do projeto automaticamente. |

### `MCRSelfHeal` — Auto-cura
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/meta.py` (linha 453) |
| **Classe** | `MCRSelfHeal` |
| **Métodos** | `verificar()` |
| **O que faz** | Verifica thresholds, módulos, classes essenciais no startup. Reconstrói se necessário. |

### `MCRAutoEvolution` — Mutação de thresholds
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/mcr_auto_evolution.py` (linha 14) |
| **Classe** | `MCRAutoEvolution` |
| **Métodos** | `entropia_global()`, `mutar()`, `ciclo(n)`, `estatisticas()` |
| **O que faz** | Muta thresholds, aceita se entropia diminuiu. |

---

## 9. SPRITES / VISUAL

Pipeline completo de sprites.

### `MCRSpriteMotor` — Motor multi-nível de sprite
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/mcr_sprite_motor.py` (linha 30) |
| **Classe** | `MCRSpriteMotor` |
| **Métodos** | `treinar(sprites, categoria)`, `gerar(n, temperatura)`, `renderizar(dados)`, `avaliar(tokens)`, `stats()` |
| **Níveis** | `mk_byte` (bytes RGBA), `mk_palavra` (regiões), `mk_token` (B/L/F), `mk_cor` (cores com compose_state) |
| **Depende de** | `MCRSQLite`, `compose_state`, `MCRDecisor`, `ThreadPoolExecutor` |
| **O que faz** | 4 níveis em paralelo. Geração com temperatura. Cores com contexto. |
| **Notas** | **Motor principal para geração de sprite.** 4 DBs SQLite, ~140K estados byte. |

### `MCRSpriteUniversal` — Gerador universal de sprite
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/mcr_sprite_universal.py` (linha 73) |
| **Classe** | `MCRSpriteUniversal` |
| **Métodos** | `treinar(categoria)`, `gerar(n)`, `avaliar(sprites)`, `buscar_similares(sprite)`, `stats()` |
| **Integra** | MCRDiscriminador, RadarMCR, SignatureAnalyzer, MCRThreshold, MCREntropia, MCRPesoNota |
| **Notas** | Pipeline completa de sprite com todos os módulos MCR conectados. |

### `MCRConectorSprite` — Conector de sprite (legado)
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/mcr_conector_sprite.py` (linha 57) |
| **Classe** | `MCRSpriteConector` |
| **O que faz** | Versão anterior do motor. Substituído por MCRSpriteMotor. |
| **Status** | ⚠️ Manter para compatibilidade. Novos desenvolvimentos usar MCRSpriteMotor. |

### `sprite_corpus` — Carregador de corpus
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/sprite_corpus.py` |
| **Funções** | `carregar_categoria(nome)`, `extrair_grid_papel(sprite)`, `extrair_paleta_mediana(grid)`, `salvar_grid_como_png(grid, paleta, path)`, `sprite_para_ascii(grid)`, `jaccard_silhueta(sprites)`, `jaccard_gerados_vs_reais(gerados, reais)` |
| **O que faz** | Carrega sprites do corpus, extrai papel B/L/F, paleta, métricas. |

### `tokenizador_hierarquico` — Tokenizador de regiões
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/tokenizador_hierarquico.py` |
| **Funções** | `extrair_regioes(grid)`, `ordenar_regioes(regioes)`, `extrair_relacoes(regioes)`, `propriedades_para_vetor(regioes)`, `token_grid_para_linear(grid)`, `tokenizar_hierarquico(grid)`, `_convex_hull(pontos)`, `_rasterizar_hull(hull)`, `regioes_para_grid(regioes)`, `regioes_para_grid_com_borda(regioes)` |
| **O que faz** | Flood fill em pixels adjacentes → regiões conectadas. Extrai propriedades: área, centroide, bbox, orientação. |

### `template_entropico` — Template por entropia
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/template_entropico.py` |
| **Funções** | `entropia_shannon(sequencia)`, `extrair_template_entropico(sequencias, limiar)`, `gerar_do_template(template, temperatura)`, `resumir_template(template)` |
| **O que faz** | Para cada posição em N sequências: H < limiar → fixo (estrutura), H >= limiar → gap (criativo). |
| **Notas** | **Use para extrair estrutura invariante de múltiplos sprites da mesma categoria.** |

### `template_regiao` — Template de região (legado)
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/template_regiao.py` |
| **Status** | ⚠️ Legado. `template_entropico` + `tokenizador_hierarquico` fazem o mesmo de forma mais limpa. |

### `olhos_mcr` — Olhos do MCR (ASCII rico)
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/olhos_mcr.py` |
| **Funções** | `sprite_para_ascii_rich(grid_papel, grid_cor, nome)`, `sprite_para_ascii_compacto(grid_papel, grid_cor)`, `categoria_para_ascii_rich(categoria, sprites)` |
| **O que faz** | Gera representação ASCII multi-camada: PAPEL + LUMINANCE + MATIZ + PERFIL + DIAGNÓSTICO. |

### `regioes_anatomicas` — Regiões anatômicas
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/regioes_anatomicas.py` |
| **Funções** | `projetar_densidade(grid)`, `projetar_diversidade(grid)`, `cortar_em_regioes(grid)`, `extrair_regioes_cromaticas(img_rgb)`, `fingerprint_cromatico(regioes)`, `comparar_regioes_cromaticas(a, b)` |
| **O que faz** | Duas abordagens: projeção de densidade 1D ou clustering CIELAB + flood fill. |

### `visual_coupling` — Acoplamento visual
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/visual_coupling.py` |
| **Classe** | `VisualCoupling` |
| **Métodos** | `alimentar_sprite(regioes)`, `alimentar_sprites(regioes_list)`, `predizer_cor(geometria, posicao)`, `predizer_posicao(cor, geometria)`, `predizer_geometria(cor, posicao)` |
| **O que faz** | Aprende correlações entre cor, geometria e posição de regiões. |
| **Notas** | **Use para predizer cor de uma região baseado em sua geometria e posição.** |

### `PipelineMCRSprite` — Pipeline de métricas de sprite
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/pipeline_mcr_sprite.py` |
| **Funções** | `medir_coerencia_estrutural()`, `medir_diversidade()`, `medir_paleta()`, `rodar_categoria()` |
| **O que faz** | Pipeline de avaliação: carrega → treina → gera → colore → mede. |

### `PipelineUniversal` — Pipeline universal de 6 estágios
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/pipeline_universal.py` (linha 48) |
| **Classe** | `PipelineUniversal` |
| **Métodos** | `registrar(dominio, config)`, `executar(dados, dominio)`, `stats()` |
| **Integra** | MCRThreshold, MCRDecisor, MCRPesoNota, MCREntropia, MCRAutoMelhoria, MCRSignatureExpansiva, MCRMetaNivel |
| **O que faz** | 6 estágios: LOAD → TOKENIZE → TEMPLATE → FILL → VALIDATE → LEARN. 4 domínios: texto, código, sprite, API. |

### `dominios/` — Registro de domínios do PipelineUniversal
| Campo | Valor |
|-------|-------|
| **Path** | `mcr/dominios/` |
| **Arquivos** | `texto.py`, `codigo.py`, `sprite.py`, `api.py` |
| **Cada um exporta** | `DOMINIO = {tokenizer, validator, builder, loader, template_engine, filler}` |

---

## 10. FERRAMENTAS / COMANDOS

### `ToolOrchestrator` — 30 ferramentas executáveis
| Campo | Valor |
|-------|-------|
| **Path** | `devia/modules/tool_orchestrator.py` (linha 25) |
| **Classe** | `ToolOrchestrator` |
| **O que faz** | Registra e executa 30 ferramentas: ler/escrever arquivo, buscar código, gerar NPC, validar, etc. |

### `comandos/` — 52 comandos
| Campo | Valor |
|-------|-------|
| **Path** | `devia/comandos/` |
| **Padrão** | Cada arquivo `cmd_*.py` exporta `register()` e `execute()` |
| **Lista completa** | `analisar`, `aprender_conceito`, `autoteste`, `build`, `bugfinder`, `compilar`, `conectar`, `conselho`, `criar`, `debate`, `edit`, `ensinar`, `estrategia`, `explorar`, `extract`, `fast`, `fazer`, `fix_excepts`, `gerar`, `gerar_componentes`, `gerar_npc`, `glob`, `grep`, `lore`, `loop`, `master`, `memoria`, `patch`, `pensar`, `perguntar`, `plan`, `proativo`, `question`, `read`, `refresh`, `resume`, `review`, `revisar`, `revisar_docs`, `status`, `super_test`, `system`, `system_scan`, `task`, `todo`, `toolkit`, `turbo`, `verificar_mudancas`, `webfetch`, `weblearn`, `write` |

---

## 11. META / AUTO-CONHECIMENTO

### `MCRMetaNivel` — Descoberta automática de níveis
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/meta.py` (linha 128) |
| **Classe** | `MCRMetaNivel` |
| **Métodos** | `alimentar(dados)`, `diagnosticar()`, `auto_expandir(max_niveis)` |
| **O que faz** | Cria níveis (byte → palavra → intenção → padrão → ...) baseado em threshold de estados. |
| **Notas** | **Use para descobrir quantos níveis de abstração um sprite precisa.** Já conectado no PipelineUniversal. |

### `MCRMetaGap` — Detecção de lacunas
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/meta.py` (linha 234) |
| **Classe** | `MCRMetaGap` |
| **Métodos** | `diagnosticar_gaps(min_por_prefixo)`, `buscar_para_gap(gap)`, `ciclo_completo(min_por_prefixo)` |
| **O que faz** | Encontra tópicos com poucas lessons, busca dados para preencher. |

### `MCRSelfIndex` — Auto-indexação
| Campo | Valor |
|-------|-------|
| **Path** | `devia/kernel/mcr_kernel/meta.py` (linha 356) |
| **Classe** | `MCRSelfIndex` |
| **Métodos** | `indexar_tudo()`, `buscar_classe(nome)`, `buscar_modulo(nome)`, `buscar_comando(nome)` |
| **O que faz** | Indexa o próprio código-fonte como documentos buscáveis. |

---

## 12. LEGADO / DUPLICATAS (arquivar)

| Arquivo | Tamanho | Substituído por | Motivo |
|---------|---------|----------------|--------|
| `devia/kernel/MCR_legacy.py` | 311KB | `mcr_kernel/` (11 módulos) | Desmembrado |
| `devia/kernel/mcr_devia.py` | 25KB | `mcr_devia_v2.py` | Versão antiga |
| `historia/scripts/mcr_devia/modulos/MCR.py` | 457KB | `mcr_kernel/` | Cópia massiva |
| `mcr/discriminador_anatomia.py` | 6.6KB | `meus_olhos.py` | Discriminador mais simples |
| `mcr/template_regiao.py` | 25KB | `template_entropico.py` + `tokenizador_hierarquico.py` | Funcionalidades separadas |
| `mcr/mcr_conector_sprite.py` | 13KB | `mcr_sprite_motor.py` | Motor mais completo |
| `nichos/tibia/mk_id.py` | 11KB | `mcr_adapt.py` (SQLite) | Sem persistência |
| `devia/kernel/MCR.py` | 1KB | `mcr_kernel/__init__.py` | Shim vazio |
| `mcr/anti_pattern_injector.py` | 3KB | `anti_pattern.py` | Mesma função, separado |
| `historia/` | ~2MB | `devia/` | Cópias legadas |

---

## 13. CONEXÕES ENTRE MÓDULOS (como conectar)

```
PROBLEMA: "gerar sprite com estrutura e cor"
  PipelineUniversal.executar(dados, 'sprite')
    → MCRSpriteMotor.treinar() [4 niveis em paralelo]
    → MCRSpriteMotor.gerar() [temperatura + compose_state]
    → MCRSpriteMotor.renderizar() [banco de regioes reais]
    → MCRDiscriminador.avaliar() [score de qualidade]

PROBLEMA: "conectar sprite a texto"
  MCRConector.alimentar(sprite_tokens, 'sprite_X')
  MCRConector.alimentar(texto_descricao, 'texto_X')
  MCRConector.conectar('sprite_X', 'texto_X')
    → MCRConexao.analisar() [divergencia*5 + especificidade*3 + profundidade*2]

PROBLEMA: "descobrir tipos de sprite"
  SignatureAnalyzer.clusterizar()
    → extrai fingerprint de cada sprite
    → Jaccard > threshold → mesmo tipo
    → nomeia Type_A, Type_B

PROBLEMA: "validar qualidade de sprite"
  MCRDiscriminador.treinar(grids_reais)
  MCRDiscriminador.avaliar(grid_gerado) → score
  RadarMCR.buscar_visual(regioes_gerado, regioes_reais) → ondas

PROBLEMA: "auto-melhorar geracao"
  MCRAutoMelhoria.ciclo()
    → detecta gaps, loops, erros
    → busca novos dados
    → re-treina
```

---

## 14. ÍNDICE POR PALAVRA-CHAVE

| Palavra-chave | Módulo |
|---------------|--------|
| **byte-level** | MCR, MCRSQLite, MCRByteUtils, engine.py |
| **fingerprint** | MCRFingerprint, MCRSignature, MCRSignatureExpansiva |
| **threshold** | MCRThreshold, MCRAutoEvolution |
| **decisão** | MCRDecisor |
| **peso** | MCRPesoNota, mcr_meta.py |
| **entropia** | MCREntropia, template_entropico |
| **ruído** | MCRRuido |
| **loop** | MCREntropia |
| **conexão** | MCRConexao, MCRCruzado, MCRConector, emergir_crossmodal |
| **ponte** | MCRConexao, MCRCruzado |
| **emergência** | MCRMotor, emergir.py, emergir_crossmodal.py |
| **cadeia** | MCRCadeia |
| **memória** | MCRBufferKG, MCRKGAuto, KnowledgeGraph, EpisodicMemory |
| **evolução** | MCRAutoMelhoria, MCRFuel, MCRAutoEvolution |
| **auto-cura** | MCRSelfHeal |
| **auto-índice** | MCRSelfIndex |
| **sprite** | MCRSpriteMotor, sprite_corpus, tokenizador_hierarquico, template_entropico |
| **região** | extrair_regioes, regioes_anatomicas, visual_coupling |
| **cor** | cielab.py, compose_state (engine.py) |
| **ASCII** | olhos_mcr.py |
| **validação sprite** | MCRDiscriminador, RadarMCR, pipeline_mcr_sprite |
| **pipeline** | PipelineUniversal, PipelineMCRSprite, MCRPipeline |
| **template** | template_entropico, TemplateExtractor |
| **N-adaptativo** | MCRSQLite, SQLiteMarkov (mcr_adapt) |
| **compose_state** | engine.py (compose_state, compor_contexto) |
| **dicionário** | MCRSignature (fingerprint 8D = dicionário universal) |


---

## 15. MÓDULOS DE E:\COISAS (validados e funcionais)

Modulos prototipo encontrados em E:\Coisas\, testados e funcionais em 11/07/2026.

### fingerprint_puro — Fingerprint 3 modos (raw/bytes/markov)
| Campo | Valor |
|-------|-------|
| Path | E:\Coisas\MCR Prototipos\prototipos\core\fingerprint_puro.py |
| Classe | FingerprintMCRPuro |
| Modos | raw (11-dim: hashes, lengths, case), bytes (13-dim: bytes, entropia, proporcoes), markov (6-dim: transicoes) |
| Testado | raw=11, bytes=13, markov=6 dimensoes |
| Notas | Dimensionalidade diferente do fingerprint 8D em MCRFingerprint. Util para analise multi-perspectiva. |

### jaccard_byte — Jaccard com peso posicional
| Campo | Valor |
|-------|-------|
| Path | E:\Coisas\MCR Prototipos\prototipos\core\jaccard_byte.py |
| Funcoes | jaccard_bytes(a, b), jaccard_bytes_ponderado(a, b) (primeiros 10 bytes pesam 2x), fingerprint_bytes(texto, dims) |
| Testado | simples=0.312, ponderado=0.488 para textos similares |
| Notas | jaccard_bytes_ponderado() nao existe em E:\MCR\. Util para matching onde inicio e mais importante. |

### markov_cruzado — Ponte entre topicos (divergencia*5 + especificidade*3 + profundidade*2)
| Campo | Valor |
|-------|-------|
| Path | E:\Coisas\MCR Prototipos\prototipos\core\markov_cruzado.py |
| Classe | MarkovCruzado |
| Metodos | analisar(a, b), melhor_ponte(a, b) |
| Notas | Mesmo algoritmo de MCRConexao em devia/kernel/mcr_kernel/memory.py. Prototipo mais limpo. |

### mcr_emergir — Motor de emergencia completo
| Campo | Valor |
|-------|-------|
| Path | E:\Coisas\MCR Prototipos\prototipos\mcr_emergir.py |
| Classe | MCREmergir |
| Metodos | alimentar(texto, topico), conectar(a, b), explorar_todos(), _autoavaliar_multinivel() |
| Notas | Implementacao completa e limpa do motor de emergencia com geracao crossover palavra-a-palavra. |

### MCR.py (monolito prototipo) — Classes uteis
| Campo | Valor |
|-------|-------|
| Path | E:\Coisas\MCR Prototipos\MCR.py |
| Classes | MCR, MCRByteUtils, MCRThreshold, MCREntropia, MCRBuffer, MCRSession, MCRConexao, MCRMotor, MCRAutoLoop |
| Testado | MCRThreshold.calcular()=0.600, MCREntropia.esta_em_loop()=True |
| Notas | Mesmas classes que existem em devia/kernel/mcr_kernel/. Mantido como referencia historica. |

### Experimentos cientificos validados
| Experimento | Path | O que prova | Valor |
|-------------|------|-------------|-------|
| exp1_mudanca_stream.py | E:\Coisas\trash\ | MCR multi-level entropia detecta mudancas de regime | Alto - detector anomalias |
| exp2_gridworld_critical.py | E:\Coisas\trash\ | MCR entropia 0.2-0.7 regula exploracao vs explotacao | Alto - curiosidade |

### Documentos estrategicos
| Documento | Path | Conteudo | Valor |
|-----------|------|----------|-------|
| Modulos Orfaos.md | E:\Coisas\ | Lista de modulos nao integrados com prioridades | Alto - guia |
| ANALISE_ARQUITETURAL_MCR_v5.md | E:\Coisas\ | Analise independente (40+ anos IA) | Alto - validacao |
| ROADMAP_EVOLUTIVO.md | E:\Coisas\ | 5 fases de evolucao | Alto - planejamento |


---

## 16. PRIORIDADES DE INTEGRACAO (Top 5)

Baseado em Modulos Orfaos.md (E:\Coisas\). Modulos funcionais mas nao integrados ao pipeline mcr/.

| # | Modulo | Path | Lacuna que preenche | Linhas |
|---|--------|------|---------------------|--------|
| 1 | hybrid/pipeline.py | prototypes/mcr-universal/mcr/hybrid/pipeline.py | Roteamento MCR->LLM com guardrail + custo | ~200 |
| 2 | lua_validator.py | devia/modules/lua_validator.py | Validacao especifica Canary (alem do shadow generico) | ~250 |
| 3 | npc_generator.py | devia/modules/npc_generator.py | Templates de NPC extraidos de NPCs reais | ~600 |
| 4 | item_database.py | devia/knowledge/item_database.py | Dados reais de items.xml para NPCs de loja | ~400 |
| 5 | learn/fuel.py | prototypes/mcr-universal/mcr/learn/fuel.py | Ingestao de .lua no motor Markov | ~120 |

---

## 17. ROADMAP ESTRATEGICO (7 Fases)

Baseado em ROADMAP_EVOLUTIVO.md (E:\Coisas\).

Dependencias entre fases:
  FASE 0 -> FASE 1 -> FASE 2 -> FASE 6 -> FASE 3 -> FASE 4 -> FASE 5 -> FASE 7

| Fase | Nome | O que faz | Status |
|------|------|-----------|--------|
| 0 | Consolidacao | Documentar, proteger, limpar base | EM ANDAMENTO |
| 1 | Universalizacao | PatternMiner via AST (tree-sitter) para C++/Lua | Pendente |
| 2 | Metacognicao | Gateway de incerteza: bloquear se KG nao sabe | Pendente |
| 3 | Auto-Curiosidade | Background self-study: MCRMetaGap + MCRCuriosidade | Pendente |
| 4 | Validacao Empirica | LogWatcher -> Anti-Patterns no KG | Pendente |
| 5 | Shadow Canary | Mock environment para testar codigo sem servidor real | Pendente |
| 6 | Motor de Criatividade | Emergir operacional: gerar ideias, testar, promover | Pendente |
| 7 | Caminho Druida | Ponte Lua->MCR para NPCs vivos (dialogo Markov 0.006s) | Pendente |

### Relacao com o PipelineUniversal:
  - FASE 0 = Nosso catalogo + arquivamento de duplicatas
  - FASE 1 = PatternMiner ja existe em mcr/pattern_miner.py
  - FASE 2 = Gateway semelhante ao nosso MCRDecisor + MCRThreshold
  - FASE 6 = EmergirCrossModal ja existe em mcr/emergir_crossmodal.py
  - FASE 3 = MCRAutoMelhoria.ciclo() ja faz auto-estudo
  - FASE 4 = world_anomaly_detector ja detecta anomalias
  - FASE 5 = shadow_canary.py ja faz mock de Lua
  - FASE 7 = npc_server.py ja faz NPC via MCR

Conclusao: todas as 7 fases tem modulos equivalentes em E:\MCR\. Falta INTEGRACAO, nao criacao.

---

## 18. METRICAS DE MATURIDADE

Baseado em ANALISE_ARQUITETURAL_MCR_v5.md (E:\Coisas\, analise independente).

### Split Real vs Prototipo
  - ~60% do codigo e funcional e integrado
  - ~40% e prototipo funcional mas isolado (nao conectado ao pipeline)
  - Fonte: analise de 40+ anos de pesquisa em IA

### Componentes Genuinamente Originais
  1. MCRWorld.simular — JEPA simbolico em Python puro (50 linhas, Counter)
     Prediz fingerprint(depois) de fingerprint(antes) + acao
     Nao existe equivalente em nenhum sistema neuro-simbolico conhecido
  2. Equacao MCR — NOTA = (BYTE + PALAVRA + TOKEN) x (1 - PENALIDADE)
     Gradiente simbolico para hill-climbing generativo
  3. MCRGuardrail — Validacao pos-hoc via cadeias Markov
     Nao constrange distribuicao (Logits Bias), mas e unico na abordagem

### Componentes Subutilizados
  1. HDC (hdc_core.py) — Raciocinio analogico construido, ninguem chama
  2. SDM+MDL (sdm_core.py) — Memoria distribuida, nao integrada ao pipeline
  3. MarkovDecider (mcr_devia_v2.py) — 10^6x mais rapido que LLM, nao esta no PipelineExecutor
  4. Dim_ideal (MCRSignatureExpansiva) — Descoberta de dimensionalidade, nenhum lugar ativo chama

---

## 19. COMANDOS DE ORGANIZACAO (Cleanup)

Baseado em PLANO_ORGANIZACAO_MCR.md (E:\Coisas\).

### Arquivos para arquivar em legacy/ (ja identificados no catalogo secoes 12 e 15)

| Arquivo | Tamanho | Destino | Motivo |
|---------|---------|---------|--------|
| devia/kernel/MCR_legacy.py | 311KB | legacy/kernel/ | Desmembrado em mcr_kernel/ (11 modulos) |
| devia/kernel/mcr_devia.py | 25KB | legacy/kernel/ | Versao antiga, substituida por mcr_devia_v2.py |
| mcr/discriminador_anatomia.py | 6.6KB | legacy/mcr/ | Mesma funcao de meus_olhos.py |
| mcr/template_regiao.py | 25KB | legacy/mcr/ | Separado em template_entropico + tokenizador_hierarquico |
| mcr/mcr_conector_sprite.py | 13KB | legacy/mcr/ | Substituido por mcr_sprite_motor.py |
| mcr/anti_pattern_injector.py | 3KB | legacy/mcr/ | Mesma funcao de anti_pattern.py |

### Arquivos para manter (unicos)

| Arquivo | Path | Motivo |
|---------|------|--------|
| fingerprint_puro.py | E:\Coisas\ | 3 modos (raw/bytes/markov) nao existem em E:\MCR\ |
| jaccard_byte.py | E:\Coisas\ | jaccard_bytes_ponderado() e unico |
| markov_cruzado.py | E:\Coisas\ | Implementacao mais limpa que MCRConexao |
| mcr_emergir.py | E:\Coisas\ | Motor de emergencia completo, referencia arquitetural |
| exp1_mudanca_stream.py | E:\Coisas\trash\ | Unico benchmark contra Page-Hinkley/CUSUM/ADWIN |
| exp2_gridworld_critical.py | E:\Coisas\trash\ | Unico experimento de criticalidade auto-regulada |
| Modulos Orfaos.md | E:\Coisas\ | Guia de prioridades |
| ANALISE_ARQUITETURAL_MCR_v5.md | E:\Coisas\ | Unica avaliacao externa |
| ROADMAP_EVOLUTIVO.md | E:\Coisas\ | Unico roadmap estrategico |
| PLANO_ORGANIZACAO_MCR.md | E:\Coisas\ | Unico plano de limpeza |
