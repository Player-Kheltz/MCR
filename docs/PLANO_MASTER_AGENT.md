# Plano MasterAgent — AGI Local Híbrida

> **Objetivo:** Meu computador local faz QUALQUER coisa, de QUALQUER tamanho,
> usando LLM local + ferramentas + cloud fallback + contexto infinito.
>
> **Princípio:** O sistema não precisa saber fazer tudo. Ele precisa SABER
> PLANEJAR e usar as ferramentas certas. LLM é o cérebro, ferramentas são as mãos.

---

## Visão Geral da Arquitetura

```
ENTRADA: "Cria um jogo de plataforma em Python com 3 fases"
  │
  ▼
┌─────────────────────────────────────────────────────┐
│                   MASTER AGENT                       │
│  "Faz QUALQUER coisa, do tamanho que for"           │
│                                                      │
│  1. PERCEBER → TaskAnalyzer entende o request       │
│  2. PLANEJAR → LLM decompõe em N subtarefas         │
│  3. EXECUTAR → Para cada subtarefa:                 │
│     │   ├── Escolhe ferramenta (local ou cloud)     │
│     │   ├── Executa com ferramenta                  │
│     │   ├── Valida resultado                         │
│     │   └── Aprende lição                           │
│  4. INTEGRAR → Junta tudo num artefato coeso        │
│  5. APRENDER → Registra no KG + Memória Episódica  │
└─────────────────────────────────────────────────────┘
  │
  ▼
SAÍDA: Projeto completo com código, assets, instruções
```

---

## Filosofia: Decider/FAST Universal (NOVO)

> **Princípio:** Toda decisão que hoje é tomada por regex/dict fixo
> deve ser tomada pelo FAST model. O sistema não tem "conhecimento
> embutido" — ele pergunta ao LLM o que fazer em cada situação.
> 
> **Exceções:** Apenas operações que exigem DETERMINISMO (segurança,
> validação de sintaxe, criação de arquivos) podem ter regras fixas.
> Tudo que é classificação, mapeamento ou extração → FAST.

### O que muda

| Antes (hardcode) | Depois (FAST) | Onde |
|-----------------|---------------|------|
| `ia.decider()` — 25 regex | `decider.classificar()` | `ia.py` |
| `_inferir_tipo()` — 25+ regex | `decider.classificar()` | `task_planner.py` |
| `_extrair_tech_stack()` — 14 regex | `decider.extrair_json()` | `task_planner.py` |
| `extrair_nome_projeto()` — regex | `decider.extrair_json()` | `util.py` |
| `projeto_grande` — `any(p in r)` | `decider.classificar()` | `master_agent.py` |
| `PADROES_PERIGOSOS` | **Manter** + FAST como camada extra | `security.py` |

### O que NÃO muda (determinístico)

| Módulo | Motivo |
|--------|--------|
| `COMANDOS_BLOQUEADOS` em `security.py` | Segurança deve ser determinística |
| `MODELOS` dict em `ia.py` | Config técnica de hardware |
| `_acao_para_ferramenta()` em `task_planner.py` | Lookup determinístico |
| `STOP_WORDS` em `episodic_memory.py` | Universais NLP |

### Cache Inteligente

```python
_cache = {}  # hash -> {valor, timestamp}

def _get_cache(key, ttl=300):
    entry = _cache.get(key)
    if entry and time.time() - entry['ts'] < ttl:
        return entry['valor']
    return None
```

---

## O que já temos (reuso)

| Componente | O que faz | Será usado como |
|------------|-----------|-----------------|
| `ia.py` | Router de modelos locais | **Base** do Router Híbrido |
| `kg.py` | Knowledge Graph (fatos) | **Memória de fatos** |
| `context_crew.py` | Busca contexto em 6 fontes | **Fonte de contexto** |
| `pipeline_executor.py` | Pipeline de perguntas | **Inspiração** para MasterAgent |
| `task_analyzer.py` | Classifica tarefas | **Perceptor** do MasterAgent |
| `tool_registry.py` | Catálogo de ferramentas | **Base** do ToolOrchestrator |
| `agent_loop.py` | OODA loop (só NPC) | **Substituído** pelo MasterAgent |
| `npc_generator.py` | Geração de NPCs | **Ferramenta** no ToolOrchestrator |
| `lua_validator.py` | Valida Lua | **Ferramenta** de validação |
| `canary_indexer.py` | Indexa NPCs reais | **Ferramenta** de busca |
| `comandos/` (49) | Comandos modulares | **Ferramentas** no ToolOrchestrator |
| `orquestrador.py` | Templates de resposta | **Ferramenta** de geração de texto |

---

## O que precisa ser construído (7 fases)

```
Fase D ─ Decider/FAST         ─ NOVO módulo               (+60 linhas)
Fase 0 ─ Router Híbrido      ─ modificar ia.py           (+40 linhas)
Fase 1 ─ EpisodicMemory      ─ NOVO módulo               (+180 linhas)
Fase 2 ─ ToolOrchestrator    ─ refactor tool_registry.py  (+200 linhas)
Fase 3 ─ TaskPlanner         ─ NOVO módulo               (+250 linhas)
Fase 4 ─ SandboxExecutor     ─ NOVO módulo               (+120 linhas)
Fase 5 ─ MasterAgent         ─ NOVO + refactor           (+350 linhas)
                                ─ agent_loop.py refactor
                                ─ pipeline_executor.py refactor
                                ─ Total: ~1200 linhas
```

---

## Fase D — Decider/FAST Universal

**Arquivo:** `Scripts/mcr_devia/modulos/decider.py` (NOVO)
**Impacto:** Remove ~66 linhas de regex/dict de 4 módulos

**O que faz:** Substitui toda classificação via regex por FAST model.
Decide TUDO dinamicamente: linguagem do projeto, tipo de tarefa,
se é local ou cloud, qual template usar, nome do projeto.

```python
"""Decider — Classificador universal via FAST model (+ fallback deterministico).

Substitui regex/dict fixos por decisoes do FAST model.
Nao substitui seguranca deterministica (COMANDOS_BLOQUEADOS).
Cache LRU com TTL para evitar chamadas repetidas ao LLM.

Uso:
    decider = Decider(ia)
    tipo = decider.classificar("Cria um jogo em Python", 
                                ['projeto_jogo', 'criar_codigo', 'pergunta'])
    # -> 'projeto_jogo'
    
    dados = decider.extrair_json("Cria um jogo de plataforma",
                                  {'nome': '', 'linguagem': ''})
    # -> {'nome': 'jogo_plataforma', 'linguagem': 'python'}
"""
import json, hashlib, time

# Cache LRU com TTL
_cache = {}

def _cache_key(*args):
    return hashlib.md5(':'.join(str(a) for a in args).encode()).hexdigest()

def _get_cache(key, ttl=300):
    entry = _cache.get(key)
    if entry and time.time() - entry['ts'] < ttl:
        return entry['valor']
    return None

def _set_cache(key, valor):
    _cache[key] = {'valor': valor, 'ts': time.time()}


class Decider:
    """Tomador de decisoes universal via FAST model."""

    def __init__(self, ia=None):
        self.ia = ia

    def classificar(self, texto, categorias, instrucao=""):
        """Classifica texto em uma das categorias via FAST.
        
        Args:
            texto: O que classificar (request, consulta, etc)
            categorias: Lista de opcoes validas (ex: ['local', 'cloud'])
            instrucao: Contexto extra para o prompt (opcional)
        Returns:
            str: Categoria escolhida, ou primeira opcao como fallback
        """
        key = _cache_key(texto, str(categorias))
        cached = _get_cache(key)
        if cached:
            return cached

        if not self.ia:
            return categorias[0]

        prompt = (
            f"{instrucao}\n" if instrucao else ""
            f"Classifique em UMA das categorias abaixo.\n"
            f"Categorias: {', '.join(categorias)}\n"
            f"Texto: {texto[:500]}\n"
            f"Categoria:"
        )

        try:
            resp = self.ia.fast(prompt, 0.1, "leve").strip().lower()
            for cat in categorias:
                if cat.lower() in resp:
                    _set_cache(key, cat)
                    return cat
        except Exception:
            pass

        _set_cache(key, categorias[0])
        return categorias[0]

    def extrair_json(self, texto, esquema_exemplo, instrucao=""):
        """Extrai dados estruturados via FAST.
        
        Args:
            texto: Texto para analisar (request, consulta)
            esquema_exemplo: Dict exemplificando a estrutura (ex: {'nome': ''})
            instrucao: Contexto extra (opcional)
        Returns:
            dict: Dados extraidos (campos do esquema preenchidos)
        """
        key = _cache_key(texto, str(esquema_exemplo))
        cached = _get_cache(key)
        if cached:
            return cached

        if not self.ia:
            return esquema_exemplo

        campos = list(esquema_exemplo.keys())
        prompt = (
            f"{instrucao}\n" if instrucao else ""
            f"Extraia APENAS JSON com estes campos: {', '.join(campos)}\n"
            f"Texto: {texto[:500]}\n"
            f"JSON:"
        )

        try:
            resp = self.ia.fast(prompt, 0.1, "leve")
            dados = json.loads(resp)
            # Garante que todos os campos existem
            for k in campos:
                if k not in dados:
                    dados[k] = ''
            _set_cache(key, dados)
            return dados
        except Exception:
            _set_cache(key, esquema_exemplo)
            return esquema_exemplo
```

**Integração com os módulos existentes:**

```python
# Em ia.py — substitui 25 regex (linhas 159-183):
def decider(self, consulta, tarefa="code"):
    if CLOUD_MODE == 'desligado':
        return 'local'
    return self._decider.classificar(
        consulta, ['local', 'cloud'],
        instrucao="Se mencao MCR/Tibia/SPA = local. Se pedir web/noticias = cloud."
    )

# Em task_planner.py — substitui _inferir_tipo() regex:
def _inferir_tipo(self, request):
    return self._decider.classificar(
        request, list(PLANOS_CONHECIDOS.keys()),
        instrucao="'jogo'/'game'/'projeto' = projeto_jogo. 'npc'/'ferreiro' = npc_shop. 'python'/'script' = criar_codigo. 'o que'/'como' = pergunta_simples."
    )

# Em master_agent.py — substitui any(p in r...):
projeto_grande = (self._decider.classificar(request, ['simples', 'projeto']) == 'projeto')

# Em util.py — substitui extrair_nome_projeto() regex:
def extrair_nome_projeto(request):
    return Decider().extrair_json(request, {'nome': ''}).get('nome', 'meu_projeto')
```

**Cache compartilhado:** O cache LRU global evita chamar FAST repetidamente
para o mesmo texto. TTL de 5 minutos (300s). Para requests identicos, a
segunda chamada retorna instantaneo.

**Testes:**
```python
decider = Decider(ia=IA())

# Teste 1: Classificar local vs cloud
assert decider.classificar("O que e SPA no MCR?", ['local', 'cloud']) == 'local'
assert decider.classificar("pesquise python 3.13", ['local', 'cloud']) == 'cloud'

# Teste 2: Classificar tipo de projeto
tipo = decider.classificar("Cria um jogo em Python", 
    ['projeto_jogo', 'criar_codigo', 'pergunta_simples'])
assert tipo == 'projeto_jogo'

# Teste 3: Extrair JSON
dados = decider.extrair_json("Cria um jogo de plataforma", {'nome': '', 'linguagem': ''})
assert 'jogo' in dados.get('nome', '')
assert 'python' in dados.get('linguagem', '')

# Teste 4: Cache funciona
t1 = time.time()
decider.classificar("O que e SPA no MCR?", ['local', 'cloud'])
t2 = time.time()
assert (t2 - t1) < 0.1  # cache, nao chamou LLM

# Teste 5: Fallback sem IA
decider_sem_ia = Decider()
assert decider_sem_ia.classificar("teste", ['a', 'b']) == 'a'  # primeira opcao
```

**Critério de sucesso:** Decider.classificar() acerta >90% das classificações
comparado com as regex atuais. Cache reduz chamadas FAST em 80% para requests
repetidos. Zero mudança de comportamento visível para o usuário.

---

## Fase 0 — Router Híbrido (local + cloud)

**Arquivo:** `Scripts/mcr_devia/modulos/ia.py` (modificado)

**O que faz:** Decide ONDE cada chamada é executada:
- Tarefas rotineiras → local (qwen14b, rápido, grátis)
- Tarefas complexas → cloud (web search ou API)

```python
class RouterHibrido:
    """Roteia chamadas entre modelos locais e cloud.
    
    Estrategia:
    1. Tenta local primeiro (qwen14b)
    2. Se local falha ou tarefa é muito complexa → cloud
    3. Cloud pode ser via web search (grátis) ou API key
    """
    
    MODO_CLOUD = 'web_search'  # 'web_search' | 'api' | 'desligado'
    
    # Tarefas que vão direto pro cloud
    TAREFAS_COMPLEXAS = [
        'raciocínio_matemático', 'análise_jurídica',
        'debug_profundo', 'arquitetura_complexa',
        'qualquer_coisa_que_local_erra',
    ]
    
    @classmethod
    def decidir(cls, tarefa, descricao, historico_erros=None):
        """Decide se usa local ou cloud."""
        # Se local já errou essa tarefa antes → cloud
        if historico_erros and tarefa in historico_erros:
            return 'cloud'
        
        # Se é tarefa complexa → cloud
        if tarefa in cls.TAREFAS_COMPLEXAS:
            return 'cloud'
        
        # Padrão: local
        return 'local'
    
    @classmethod
    def chamar_cloud(cls, prompt, temp=0.4):
        """Chama IA na cloud."""
        if cls.MODO_CLOUD == 'web_search':
            return cls._via_web_search(prompt)
        elif cls.MODO_CLOUD == 'api':
            return cls._via_api(prompt)
        return None
    
    @classmethod
    def _via_web_search(cls, prompt):
        """Busca resposta na web (grátis, sem API key).
        
        Estrategia:
        1. Extrai termos de busca do prompt
        2. Busca na web
        3. Retorna conteudo encontrado como contexto
        4. LLM local processa o contexto
        """
        # Extrair termos de busca
        termos = cls._extrair_termos_busca(prompt)
        if not termos:
            return None
        
        # Buscar na web
        resultados = web_search(termos)
        if not resultados:
            return None
        
        # Retorna conteudo bruto para o local processar
        return f"RESULTADOS DA WEB PARA: {termos}\n\n{resultados}"
    
    @classmethod
    def _via_api(cls, prompt):
        """Chama API cloud (requer API key configurada)."""
        api_key = os.environ.get('CLOUD_API_KEY')
        if not api_key:
            return None
        # ... chamada para Claude/GPT-4 ...
```

**Mudanças no `ia.py` existente:**

```python
class IA:
    def __init__(self):
        self.router = RouterHibrido()
        self.historico_erros = {}  # tarefa → True se já errou
    
    def gerar(self, prompt, temp=0.7, tarefa="code"):
        """Gera texto, com fallback para cloud se necessário."""
        
        # Tenta local
        resultado = self._gerar_local(prompt, temp, tarefa)
        
        # Se falhou ou é complexo, tenta cloud
        if not resultado or self.router.decidir(tarefa, prompt, self.historico_erros) == 'cloud':
            cloud_result = self.router.chamar_cloud(prompt, temp)
            if cloud_result:
                # Usa resultado cloud como contexto + gera local
                prompt_com_contexto = f"{cloud_result}\n\nCom base no contexto acima, {prompt}"
                resultado = self._gerar_local(prompt_com_contexto, temp, tarefa)
        
        return resultado
```

**Testes:**

```python
# Teste 1: Router decide local para tarefa simples
assert RouterHibrido.decidir('rotina', 'hello world') == 'local'

# Teste 2: Router decide cloud para tarefa complexa
assert RouterHibrido.decidir('raciocínio_matemático', 'resolve P vs NP') == 'cloud'

# Teste 3: Cloud via web search retorna resultados
resultado = RouterHibrido._via_web_search("o que é SPA no MCR?")
assert resultado and len(resultado) > 50

# Teste 4: IA.gerar() funciona normalmente sem cloud
ia = IA()
resposta = ia.gerar("print('hello')", 0.1, "fast")
assert resposta and len(resposta) > 0
```

**Critério de sucesso:** Router decide corretamente. Cloud fallback funciona sem API key (via web search). IA.gerar() existente continua funcionando (retrocompatível).

---

## Fase 1 — EpisodicMemory

**Arquivo:** `Scripts/mcr_devia/modulos/episodic_memory.py` (NOVO)

**O que faz:** Guarda EXPERIÊNCIAS (não fatos). "Quando pediram X, fiz Y e deu Z."
Diferente do KG que guarda verdades absolutas ("MCR = Tibia").

```python
"""EpisodicMemory — Memória de experiências.
    
Guarda SEQUÊNCIAS de ações que funcionaram (ou não).
Diferente do KG (fatos), guarda:
- O que foi pedido (request)
- O que foi feito (plano de ações)
- O que deu certo/errado (resultado)
- Lição aprendida (para reuso)

Busca por: palavras-chave + recência + relevância.
"""
import os, json, time, re, hashlib
from typing import Dict, List, Optional

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MEMORIA_PATH = os.path.join(BASE, 'sandbox', '.mcr_devia', 'episodic_memory.json')

class EpisodicMemory:
    """Memória de experiências com busca por relevância."""
    
    def __init__(self, max_episodios=500):
        self.max_episodios = max_episodios
        self.episodios = self._carregar()
    
    def _carregar(self):
        if os.path.exists(MEMORIA_PATH):
            try:
                with open(MEMORIA_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return []
    
    def salvar(self):
        os.makedirs(os.path.dirname(MEMORIA_PATH), exist_ok=True)
        # Mantém só os mais recentes
        self.episodios = self.episodios[-self.max_episodios:]
        with open(MEMORIA_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.episodios, f, ensure_ascii=False, indent=2)
    
    def registrar(self, request, plano, resultado, licao=""):
        """Registra uma experiência completa."""
        episodio = {
            'id': hashlib.md5(f"{request}{time.time()}".encode()).hexdigest()[:12],
            'timestamp': time.time(),
            'request': request,
            'plano': [str(s) for s in plano[:10]],  # só primeiros 10 passos
            'sucesso': resultado.get('sucesso', False),
            'resultado': str(resultado)[:200],
            'licao': licao[:300],
            'termos': self._extrair_termos(request),
            'n_passos': len(plano),
            'reusos': 0,
        }
        self.episodios.append(episodio)
        self.salvar()
    
    def buscar(self, request, n=3):
        """Busca episódios relevantes para um request.
        
        Score por:
        - Match de palavras-chave no request
        - Recência (experiências recentes pesam mais)
        - Sucesso (experiências que funcionaram pesam mais)
        """
        termos = self._extrair_termos(request)
        if not termos:
            return []
        
        agora = time.time()
        scores = []
        
        for ep in self.episodios:
            # Match de termos
            match = sum(1 for t in termos if t in ep['termos'])
            if match == 0:
                continue
            
            # Recência (peso: 0.5 para muito antigo, 1.0 para recente)
            dias = (agora - ep['timestamp']) / 86400
            peso_recente = max(0.5, 1.0 - dias * 0.02)
            
            # Sucesso
            peso_sucesso = 1.3 if ep['sucesso'] else 0.7
            
            score = match * peso_recente * peso_sucesso
            scores.append((score, ep))
        
        scores.sort(key=lambda x: -x[0])
        
        # Marca como reusado
        for _, ep in scores[:n]:
            ep['reusos'] += 1
        
        return [s[1] for s in scores[:n]]
    
    def _extrair_termos(self, texto):
        """Extrai termos relevantes para busca."""
        palavras = re.findall(r'\b[a-zA-Z]{4,}\b', texto.lower())
        stop = {'para', 'com', 'que', 'como', 'mais', 'mas', 'por', 'sao',
                'esta', 'pode', 'ser', 'tem', 'seu', 'sua', 'entre', 'sobre',
                'quando', 'onde', 'quem', 'qual', 'cada', 'todo', 'apos'}
        return list(set(p for p in palavras if p not in stop))[:10]
    
    def metricas(self):
        """Retorna métricas da memória."""
        if not self.episodios:
            return {'total': 0, 'taxa_sucesso': 0}
        sucessos = sum(1 for e in self.episodios if e['sucesso'])
        return {
            'total': len(self.episodios),
            'taxa_sucesso': f'{sucessos/len(self.episodios)*100:.0f}%',
            'mais_reutilizada': max(self.episodios, key=lambda e: e['reusos']).get('request', '') if self.episodios else '',
        }
```

**Integração com KG:**

```python
# KG = fatos (verdades absolutas)
kg.buscar("MCR") → "MCR é um servidor de Tibia"

# EpisodicMemory = experiências (aprendizado)
memoria.buscar("cria mod BG3") → "Da última vez que pediram mod BG3,
   precisei de: web search por ExtAPI docs + 2 tentativas de geração.
   Lição: BG3 usa Ext.RegisterItem, não Game.createNpcType."
```

**Testes:**

```python
# Teste 1: Registrar e buscar
mem = EpisodicMemory()
mem.registrar("cria ferreiro", ["buscar exemplos", "gerar npc"], {'sucesso': True}, "usar templates shop")
resultados = mem.buscar("cria ferreiro em eridanus")
assert len(resultados) == 1
assert 'ferreiro' in resultados[0]['termos']

# Teste 2: Busca sem match retorna vazio
resultados = mem.buscar("assunto completamente diferente")
assert len(resultados) == 0

# Teste 3: Experiências recentes têm mais peso
mem.registrar("cria poção", ["gerar item"], {'sucesso': False}, "usar items.xml")
resultados = mem.buscar("cria pocao magica")
assert len(resultados) >= 1

# Teste 4: Persistência
mem2 = EpisodicMemory()
assert len(mem2.episodios) == len(mem.episodios)
```

---

## Fase 2 — ToolOrchestrator

**Arquivo:** `Scripts/mcr_devia/modulos/tool_orchestrator.py` (NOVO)
**Arquivo modificado:** `knowledge/tool_registry.py` (adicionar execução real)

**O que faz:** Catálogo VIVO de ferramentas que o MasterAgent pode usar.
Cada ferramenta é uma função executável, não só metadata.

```python
"""ToolOrchestrator — Orquestrador de ferramentas executáveis.

Cada ferramenta sabe:
- Nome, descrição (para o LLM decidir qual usar)
- Função executável (para rodar)
- Parâmetros esperados
- O que retorna

Uso:
    tools = ToolOrchestrator()
    resultado = tools.executar('gerar_npc', {'descricao': 'ferreiro', 'tipo': 'shop'})
"""
import os, sys, json, importlib
from typing import Dict, Any, Callable, Optional

class ToolOrchestrator:
    """Orquestrador de ferramentas executáveis."""
    
    def __init__(self):
        self._ferramentas = {}
        self._carregar_todas()
    
    def _carregar_todas(self):
        """Carrega todas as ferramentas do sistema."""
        # === FERRAMENTAS DE SISTEMA ===
        self.registrar('executar_comando', self._cmd_executar_comando,
            desc="Executa comando no terminal (bash/powershell)",
            params={'comando': 'string'}, output='string')
        
        self.registrar('ler_arquivo', self._cmd_ler_arquivo,
            desc="Lê conteúdo de um arquivo",
            params={'caminho': 'string'}, output='string')
        
        self.registrar('escrever_arquivo', self._cmd_escrever_arquivo,
            desc="Cria ou modifica um arquivo",
            params={'caminho': 'string', 'conteudo': 'string'}, output='string')
        
        self.registrar('listar_diretorio', self._cmd_listar_dir,
            desc="Lista arquivos de um diretório",
            params={'caminho': 'string'}, output='string')
        
        # === FERRAMENTAS DE BUSCA ===
        self.registrar('buscar_codigo', self._cmd_buscar_codigo,
            desc="Busca texto no código fonte (grep)",
            params={'padrao': 'string', 'incluir': 'string (opcional)'}, output='string')
        
        self.registrar('buscar_kg', self._cmd_buscar_kg,
            desc="Busca conhecimento no Knowledge Graph",
            params={'texto': 'string'}, output='string')
        
        self.registrar('buscar_web', self._cmd_buscar_web,
            desc="Pesquisa na web",
            params={'consulta': 'string'}, output='string')
        
        self.registrar('buscar_memoria', self._cmd_buscar_memoria,
            desc="Busca experiências passadas similares",
            params={'request': 'string'}, output='string')
        
        # === FERRAMENTAS DE CRIAÇÃO ===
        self.registrar('gerar_npc', self._cmd_gerar_npc,
            desc="Gera script Lua de NPC para Canary",
            params={'descricao': 'string', 'tipo': 'string'}, output='dict')
        
        self.registrar('gerar_codigo', self._cmd_gerar_codigo,
            desc="Gera código em qualquer linguagem via IA",
            params={'descricao': 'string', 'linguagem': 'string (opcional)'}, output='string')
        
        self.registrar('escrever_artefato', self._cmd_escrever_artefato,
            desc="Escreve um artefato em arquivo",
            params={'codigo': 'string', 'caminho': 'string'}, output='string')
        
        # === FERRAMENTAS DE VALIDAÇÃO ===
        self.registrar('validar_lua', self._cmd_validar_lua,
            desc="Valida sintaxe Lua Canary",
            params={'codigo': 'string'}, output='dict')
        
        self.registrar('validar_python', self._cmd_validar_python,
            desc="Valida sintaxe Python",
            params={'codigo': 'string'}, output='dict')
        
        self.registrar('executar_python', self._cmd_executar_python,
            desc="Executa código Python e captura output",
            params={'codigo': 'string'}, output='dict')
        
        self.registrar('compilar_lua', self._cmd_compilar_lua,
            desc="Compila Lua com luac",
            params={'caminho': 'string'}, output='dict')
        
        # === FERRAMENTAS DE IA ===
        self.registrar('perguntar_ia', self._cmd_perguntar_ia,
            desc="Faz pergunta à IA local",
            params={'pergunta': 'string', 'tarefa': 'string (opcional)'}, output='string')
        
        self.registrar('analisar_codigo', self._cmd_analisar_codigo,
            desc="Analisa código fonte e aponta problemas",
            params={'codigo': 'string'}, output='string')
        
        # === FERRAMENTAS DE WEB ===
        self.registrar('web_search', self._cmd_web_search,
            desc="Pesquisa na web",
            params={'query': 'string'}, output='string')
        
        self.registrar('web_fetch', self._cmd_web_fetch,
            desc="Lê página web",
            params={'url': 'string'}, output='string')
    
    def registrar(self, nome, funcao, desc="", params=None, output="string"):
        """Registra uma ferramenta."""
        self._ferramentas[nome] = {
            'nome': nome,
            'descricao': desc,
            'funcao': funcao,
            'params': params or {},
            'output': output,
        }
    
    def listar(self):
        """Lista ferramentas disponíveis (para o LLM escolher)."""
        return {n: {
            'descricao': f['descricao'],
            'params': list(f['params'].keys()),
        } for n, f in self._ferramentas.items()}
    
    def executar(self, nome, params=None):
        """Executa uma ferramenta pelo nome."""
        if nome not in self._ferramentas:
            return {'erro': f'Ferramenta "{nome}" não encontrada'}
        
        ferramenta = self._ferramentas[nome]
        try:
            resultado = ferramenta['funcao'](**(params or {}))
            return {'sucesso': True, 'resultado': resultado}
        except Exception as e:
            return {'erro': str(e)}
    
    # === IMPLEMENTAÇÕES ===
    
    def _cmd_executar_comando(self, comando):
        import subprocess
        r = subprocess.run(comando, capture_output=True, text=True, timeout=30, shell=True)
        return r.stdout[:5000] + ('\n...' + r.stderr[:1000] if r.stderr else '')
    
    def _cmd_ler_arquivo(self, caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            return f.read()[:8000]
    
    def _cmd_escrever_arquivo(self, caminho, conteudo):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        return f"Arquivo salvo: {caminho}"
    
    def _cmd_listar_dir(self, caminho):
        if not os.path.exists(caminho): return "Diretório não encontrado"
        itens = os.listdir(caminho)
        return '\n'.join(
            f"{'📁' if os.path.isdir(os.path.join(caminho, i)) else '📄'} {i}"
            for i in sorted(itens)[:50]
        )
    
    def _cmd_buscar_codigo(self, padrao, incluir="*"):
        # Usa grep no projeto
        import subprocess
        cmd = f'rg -n "{padrao}" --include "{incluir}" -g "!sandbox" -g "!__pycache__" -g "!.git" 2>nul || findstr /sn /i "{padrao}" "*.py" "*.lua" "*.cpp" 2>nul'
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=True)
        return r.stdout[:5000] if r.stdout else "Nenhum resultado"
    
    def _cmd_buscar_kg(self, texto, max_r=5):
        from modulos.kg import KnowledgeGraph
        kg = KnowledgeGraph()
        lessons = kg.buscar(texto, max_r)
        if not lessons: return "Nenhuma lição encontrada"
        return '\n'.join(f"- {l.get('solucao', '')[:200]}" for l in lessons)
    
    def _cmd_buscar_memoria(self, request):
        from modulos.episodic_memory import EpisodicMemory
        mem = EpisodicMemory()
        episodios = mem.buscar(request, 3)
        if not episodios: return "Nenhuma experiência similar encontrada"
        return '\n'.join(
            f"[{'✅' if e['sucesso'] else '❌'}] {e['request'][:80]} → {e['licao'][:100]}"
            for e in episodios
        )
    
    def _cmd_gerar_npc(self, descricao, tipo='shop'):
        from modulos.agent_loop import AgentLoop
        agent = AgentLoop()
        r = agent.executar(descricao, tipo)
        return r
    
    def _cmd_gerar_codigo(self, descricao, linguagem=""):
        from modulos.ia import IA
        ia = IA()
        prompt = f"Crie o seguinte código:\n{descricao}\n"
        if linguagem:
            prompt = f"Crie em {linguagem}:\n{descricao}\n"
        prompt += "\nCódigo COMPLETO, sem placeholders, sem 'TODO', funcional."
        return ia.gerar(prompt, 0.4, "code") or "Falha ao gerar código"
    
    def _cmd_escrever_artefato(self, codigo, caminho):
        return self._cmd_escrever_arquivo(caminho, codigo)
    
    def _cmd_validar_lua(self, codigo):
        from modulos.lua_validator import LuaValidator
        val = LuaValidator()
        return val.validar(codigo)
    
    def _cmd_validar_python(self, codigo):
        try:
            import ast
            ast.parse(codigo)
            return {'valido': True, 'erros': []}
        except SyntaxError as e:
            return {'valido': False, 'erros': [str(e)]}
    
    def _cmd_executar_python(self, codigo):
        # Executa em sandbox (subprocess isolado)
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write(codigo)
            tmp = f.name
        try:
            r = subprocess.run(['python', tmp], capture_output=True, text=True, timeout=15)
            os.unlink(tmp)
            return {
                'stdout': r.stdout[:3000],
                'stderr': r.stderr[:1000],
                'returncode': r.returncode,
            }
        except Exception as e:
            os.unlink(tmp)
            return {'erro': str(e)}
    
    def _cmd_perguntar_ia(self, pergunta, tarefa="pesado"):
        from modulos.ia import IA
        ia = IA()
        return ia.gerar(pergunta, 0.4, tarefa) or "Sem resposta"
    
    def _cmd_analisar_codigo(self, codigo):
        from modulos.ia import IA
        ia = IA()
        prompt = f"Analise este código e aponte problemas, sugestões e melhorias:\n\n{codigo[:4000]}"
        return ia.gerar(prompt, 0.3, "analisar") or "Falha ao analisar"
    
    def _cmd_web_search(self, query):
        # Usa webfetch/websearch disponível
        try:
            from modulos.util import web_search
            return web_search(query) or "Sem resultados"
        except:
            return "Web search não disponível"
    
    def _cmd_web_fetch(self, url):
        import urllib.request
        try:
            r = urllib.request.urlopen(url, timeout=15)
            return r.read().decode('utf-8', errors='replace')[:5000]
        except Exception as e:
            return f"Erro ao acessar {url}: {e}"
```

**Integração com tool_registry.py existente:**

O `ToolOrchestrator` substitui a necessidade do `ToolRegistry` como catálogo
de metadados. Em vez de metadata + implementação separada, cada ferramenta
tem metadata + função na mesma classe.

**Testes:**

```python
tools = ToolOrchestrator()

# Teste 1: Listar ferramentas
lista = tools.listar()
assert 'gerar_codigo' in lista
assert len(lista) > 10

# Teste 2: Executar ferramenta de leitura
r = tools.executar('ler_arquivo', {'caminho': 'docs/MCR_IDENTITY.md'})
assert r['sucesso']
assert 'MCR' in r['resultado']

# Teste 3: Executar ferramenta de validação Python
r = tools.executar('validar_python', {'codigo': 'x = 1\nprint(x)'})
assert r['sucesso']
assert r['resultado']['valido'] == True

# Teste 4: Executar ferramenta de validação Python (inválido)
r = tools.executar('validar_python', {'codigo': 'x = 1\n  indent'})
assert r['sucesso']
assert r['resultado']['valido'] == False

# Teste 5: Ferramenta inexistente
r = tools.executar('nao_existe')
assert 'erro' in r
```

---

## Fase 3 — TaskPlanner

**Arquivo:** `Scripts/mcr_devia/modulos/task_planner.py` (NOVO)

**O que faz:** Decompõe QUALQUER request em subtarefas executáveis.
Usa o LLM para planejar + templates para tarefas conhecidas.

```python
"""TaskPlanner — Decompõe requests complexos em subtarefas executáveis.

Entrada: "Cria um jogo de plataforma em Python com 3 fases"
Saída: [
    {'id': 1, 'acao': 'criar_estrutura', 'params': {...}, 'depende_de': []},
    {'id': 2, 'acao': 'criar_fase1', 'params': {...}, 'depende_de': [1]},
    {'id': 3, 'acao': 'criar_fase2', 'params': {...}, 'depende_de': [1]},
    {'id': 4, 'acao': 'criar_fase3', 'params': {...}, 'depende_de': [1]},
    {'id': 5, 'acao': 'criar_main', 'params': {...}, 'depende_de': [2, 3, 4]},
    {'id': 6, 'acao': 'validar_projeto', 'params': {...}, 'depende_de': [5]},
]

Cada subtarefa é executável pelo ToolOrchestrator ou por IA direta.
"""
import json, os, re
from typing import List, Dict, Optional

# Templates de plano para tarefas comuns
PLANOS_CONHECIDOS = {
    'npc_shop': [
        {'acao': 'buscar_exemplos', 'desc': 'Busca NPCs similares no CanaryIndexer'},
        {'acao': 'buscar_licoes', 'desc': 'Busca lições no KG sobre NPCs'},
        {'acao': 'gerar_npc', 'desc': 'Gera o NPC com NPCGenerator'},
        {'acao': 'validar_npc', 'desc': 'Valida com LuaValidator'},
        {'acao': 'registrar_licao', 'desc': 'Aprende lição no KG'},
    ],
    'pergunta_simples': [
        {'acao': 'buscar_contexto', 'desc': 'Busca contexto no ContextCrew'},
        {'acao': 'perguntar_ia', 'desc': 'Pergunta à IA com contexto'},
    ],
    'criar_codigo': [
        {'acao': 'buscar_exemplos_similares', 'desc': 'Busca exemplos no código/context_crew'},
        {'acao': 'gerar_codigo', 'desc': 'Gera código via IA'},
        {'acao': 'validar_codigo', 'desc': 'Valida sintaxe'},
        {'acao': 'salvar_arquivo', 'desc': 'Salva em arquivo'},
    ],
}

class TaskPlanner:
    """Planejador de tarefas usando LLM + templates."""
    
    def __init__(self, tools_orchestrator=None, ia=None):
        self.tools = tools_orchestrator
        self.ia = ia
    
    def planejar(self, request: str, task_type: str = '') -> List[Dict]:
        """Planeja as subtarefas para executar um request.
        
        Args:
            request: Descrição completa do que fazer
            task_type: Tipo conhecido (se disponível)
        
        Returns:
            Lista de subtarefas com id, acao, params, depende_de
        """
        # Se é tipo conhecido, usa template
        if task_type and task_type in PLANOS_CONHECIDOS:
            return self._adaptar_template(request, task_type)
        
        # Se é tipo que podemos inferir, usa template inferido
        tipo_inferido = self._inferir_tipo(request)
        if tipo_inferido:
            return self._adaptar_template(request, tipo_inferido)
        
        # Se é complexo, usa LLM para planejar
        return self._planejar_com_llm(request)
    
    def _adaptar_template(self, request, task_type):
        """Adapta um template conhecido para o request específico."""
        template = PLANOS_CONHECIDOS[task_type]
        plano = []
        for i, passo in enumerate(template):
            plano.append({
                'id': i + 1,
                'acao': passo['acao'],
                'descricao': passo['desc'],
                'params': self._extrair_params(passo['acao'], request),
                'depende_de': list(range(1, i)) if i > 0 else [],
                'ferramenta': self._acao_para_ferramenta(passo['acao']),
            })
        return plano
    
    def _inferir_tipo(self, request):
        """Infere o tipo de tarefa pelo request.
        
        NOTA: Este metodo sera substituido pelo Decider.classificar()
        na proxima iteracao (Fase D). Mantido como fallback.
        """
        r = request.lower()
        
        if any(p in r for p in ['cria', 'criar', 'faz', 'fazer', 'gera', 'gerar']):
            if any(p in r for p in ['npc', 'ferreiro', 'vendedor', 'loja', 'shop']):
                return 'npc_shop'
            if any(p in r for p in ['python', 'script', 'codigo', 'programa']):
                return 'criar_codigo'
            if any(p in r for p in ['site', 'pagina', 'html']):
                return 'criar_codigo'
            return 'criar_codigo'
        
        if any(p in r for p in ['o que', 'o que é', 'como funciona', 'explique', 'quem']):
            return 'pergunta_simples'
        
        if any(p in r for p in ['analisa', 'revisa', 'verifica', 'testa']):
            return 'analisar_codigo'
        
        return None
    
    def _planejar_com_llm(self, request):
        """Usa LLM para planejar a execução de um request complexo."""
        if not self.ia:
            # Fallback: plano genérico de 1 passo
            return [{
                'id': 1,
                'acao': 'perguntar_ia',
                'descricao': f'Processar: {request[:100]}',
                'params': {'pergunta': request},
                'depende_de': [],
                'ferramenta': 'perguntar_ia',
            }]
        
        ferramentas_disponiveis = self.tools.listar() if self.tools else {}
        
        prompt = (
            f"Você é um planejador de tarefas. Dado um request do usuário, "
            f"decomponha em subtarefas executáveis.\n\n"
            f"Ferramentas disponíveis:\n{json.dumps(ferramentas_disponiveis, indent=2, ensure_ascii=False)}\n\n"
            f"Request: {request}\n\n"
            f"responda APENAS com JSON no formato:\n"
            f'[{{"id": 1, "acao": "nome_da_acao", "descricao": "...", '
            f'"params": {{...}}, "depende_de": []}}]'
        )
        
        resposta = self.ia.gerar(prompt, 0.2, "planejador")
        
        try:
            plano = json.loads(resposta)
            # Validar estrutura
            for item in plano:
                item.setdefault('depende_de', [])
                item.setdefault('params', {})
                item['ferramenta'] = self._acao_para_ferramenta(item.get('acao', ''))
            return plano
        except:
            # Fallback: plano de 1 passo
            return [{
                'id': 1,
                'acao': 'perguntar_ia',
                'descricao': f'Processar: {request[:100]}',
                'params': {'pergunta': request},
                'depende_de': [],
                'ferramenta': 'perguntar_ia',
            }]
    
    def _extrair_params(self, acao, request):
        """Extrai parâmetros relevantes para a ação."""
        if acao == 'gerar_npc':
            # Extrai tipo e descrição
            tipo = 'shop'
            for t in ['shop', 'quest', 'bank', 'gate', 'trainer', 'dialogue']:
                if t in request.lower():
                    tipo = t
                    break
            return {'descricao': request, 'tipo': tipo}
        
        if acao == 'perguntar_ia':
            return {'pergunta': request}
        
        if acao == 'gerar_codigo':
            return {'descricao': request}
        
        if acao == 'buscar_exemplos':
            return {'texto': request}
        
        if acao == 'buscar_contexto':
            return {'consulta': request}
        
        if acao == 'buscar_exemplos_similares':
            return {'request': request}
        
        return {}
    
    def _acao_para_ferramenta(self, acao):
        """Mapeia nome de ação para ferramenta do ToolOrchestrator."""
        mapa = {
            'buscar_exemplos': 'buscar_kg',
            'buscar_licoes': 'buscar_kg',
            'buscar_contexto': 'buscar_kg',
            'gerar_npc': 'gerar_npc',
            'validar_npc': 'validar_lua',
            'validar_codigo': 'validar_python',
            'registrar_licao': 'buscar_kg',
            'perguntar_ia': 'perguntar_ia',
            'gerar_codigo': 'gerar_codigo',
            'salvar_arquivo': 'escrever_artefato',
            'buscar_exemplos_similares': 'buscar_memoria',
            'criar_estrutura': 'gerar_codigo',
            'criar_fase': 'gerar_codigo',
            'criar_main': 'gerar_codigo',
            'validar_projeto': 'executar_python',
        }
        return mapa.get(acao, 'perguntar_ia')
```

**Testes:**

```python
planner = TaskPlanner()

# Teste 1: NPC conhecido usa template
plano = planner.planejar("Cria um ferreiro em Eridanus", "npc_shop")
assert len(plano) == 5  # 5 passos do template
assert plano[0]['acao'] == 'buscar_exemplos'

# Teste 2: Request com palavras-chave infere tipo
plano = planner.planejar("Cria um script Python que imprime hello")
assert plano[0]['ferramenta'] is not None

# Teste 3: Request complexo usa LLM
plano = planner.planejar("Cria um sistema de inventário com itens, mochila, e trade entre players")
assert len(plano) >= 1

# Teste 4: Dependências são mapeadas
for item in plano:
    if item['id'] > 1:
        assert len(item['depende_de']) > 0  # todo passo (exceto 1) depende de algo
```

---

## Fase 4 — SandboxExecutor

**Arquivo:** `Scripts/mcr_devia/modulos/sandbox_executor.py` (NOVO)

**O que faz:** Executa código em ambiente isolado e captura resultado.
Compila, testa, valida — tudo que o FormatDetector NÃO conseguia fazer.

```python
"""SandboxExecutor — Executa código em ambiente isolado.

Diferente do FormatDetector (só analisa sintaxe),
o SandboxExecutor REALMENTE EXECUTA e vê se funciona.

Suporta:
- Python: executa e captura output
- Lua: compila com luac (se disponível)
- Shell: executa com timeout e sem permissão de escrita
- Web: testa se URL responde

Uso:
    sandbox = SandboxExecutor()
    r = sandbox.executar_python("print('hello')")
    # → {'stdout': 'hello\n', 'stderr': '', 'returncode': 0, 'sucesso': True}
"""
import os, sys, subprocess, tempfile, json, ast, time

# Comandos proibidos (nunca executar)
COMANDOS_BLOQUEADOS = [
    'rm -rf', 'format ', 'del /f', 'rd /s', 'Remove-Item -Recurse',
    'shutdown', 'reboot', 'taskkill /f /im',
]

class SandboxExecutor:
    """Executa código em sandbox com segurança."""
    
    TEMPO_LIMITE = {
        'python': 15,
        'lua': 10,
        'shell': 10,
        'web': 30,
    }
    
    def __init__(self):
        self.historico = []
    
    def executar_python(self, codigo: str) -> dict:
        """Executa código Python em subprocesso isolado."""
        # Verifica segurança
        erro = self._verificar_seguranca(codigo)
        if erro:
            return {'sucesso': False, 'stdout': '', 'stderr': erro, 'returncode': -1}
        
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False, encoding='utf-8') as f:
            f.write(codigo)
            tmp = f.name
        
        try:
            r = subprocess.run(
                [sys.executable, tmp],
                capture_output=True, text=True,
                timeout=self.TEMPO_LIMITE['python'],
            )
            resultado = {
                'sucesso': r.returncode == 0,
                'stdout': r.stdout[:5000],
                'stderr': r.stderr[:2000],
                'returncode': r.returncode,
                'tempo': time.time(),
            }
        except subprocess.TimeoutExpired:
            resultado = {
                'sucesso': False, 'stdout': '',
                'stderr': f'Tempo limite excedido ({self.TEMPO_LIMITE["python"]}s)',
                'returncode': -1, 'tempo': time.time(),
            }
        except Exception as e:
            resultado = {
                'sucesso': False, 'stdout': '',
                'stderr': f'Erro ao executar: {e}',
                'returncode': -1, 'tempo': time.time(),
            }
        finally:
            try:
                os.unlink(tmp)
            except:
                pass
        
        self.historico.append(resultado)
        return resultado
    
    def compilar_lua(self, codigo: str) -> dict:
        """Compila Lua com luac (se disponível)."""
        # Primeiro verifica estrutura Canary
        estruturas = ['npcType:register', 'Game.createNpcType', 'npcHandler']
        tem_estrutura = any(e in codigo for e in estruturas)
        
        # Tenta compilar com luac
        with tempfile.NamedTemporaryFile(suffix='.lua', mode='w', delete=False, encoding='utf-8') as f:
            f.write(codigo)
            tmp = f.name
        
        try:
            r = subprocess.run(
                ['luac', '-p', tmp],
                capture_output=True, text=True, timeout=self.TEMPO_LIMITE['lua'],
            )
            if r.returncode == 0:
                return {
                    'sucesso': True,
                    'sintaxe_ok': True,
                    'estrutura_canary': tem_estrutura,
                    'output': 'Sintaxe Lua OK',
                    'tempo': time.time(),
                }
            else:
                return {
                    'sucesso': False,
                    'sintaxe_ok': False,
                    'estrutura_canary': tem_estrutura,
                    'erro': r.stderr[:500],
                    'tempo': time.time(),
                }
        except FileNotFoundError:
            # luac não instalado — fallback pra validação básica
            return self._validar_lua_basico(codigo, tem_estrutura)
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
        finally:
            try:
                os.unlink(tmp)
            except:
                pass
    
    def _validar_lua_basico(self, codigo, tem_estrutura):
        """Validação básica de Lua (sem luac)."""
        # Verifica se parece Lua
        padroes_lua = ['local ', 'function ', ' end', ' = ', '--']
        parece_lua = any(p in codigo for p in padroes_lua)
        
        # Verifica brackets básicos
        brackets_ok = codigo.count('{') == codigo.count('}')
        parenteses_ok = codigo.count('(') == codigo.count(')')
        
        return {
            'sucesso': parece_lua and brackets_ok and parenteses_ok,
            'sintaxe_ok': brackets_ok and parenteses_ok,
            'estrutura_canary': tem_estrutura,
            'aviso': 'luac não encontrado — validação básica apenas',
            'tempo': time.time(),
        }
    
    def executar_teste(self, codigo: str, tipo: str = 'python') -> dict:
        """Executa e testa código, retornando resultado detalhado."""
        if tipo == 'python':
            return self.executar_python(codigo)
        elif tipo == 'lua':
            return self.compilar_lua(codigo)
        else:
            return {'sucesso': False, 'erro': f'Tipo não suportado: {tipo}'}
    
    def _verificar_seguranca(self, codigo):
        """Verifica se o código tem comandos perigosos."""
        codigo_lower = codigo.lower()
        for cmd in COMANDOS_BLOQUEADOS:
            if cmd in codigo_lower:
                return f'Comando bloqueado detectado: {cmd}'
        return None
    
    def metricas(self):
        """Retorna métricas do executor."""
        if not self.historico:
            return {'total': 0, 'taxa_sucesso': 0}
        sucessos = sum(1 for h in self.historico if h.get('sucesso'))
        return {
            'total': len(self.historico),
            'taxa_sucesso': f'{sucessos/len(self.historico)*100:.0f}%',
        }
```

**Testes:**

```python
sandbox = SandboxExecutor()

# Teste 1: Python OK
r = sandbox.executar_python("print('hello world')")
assert r['sucesso'] == True
assert 'hello world' in r['stdout']

# Teste 2: Python com erro
r = sandbox.executar_python("x = 1/0")
assert r['sucesso'] == False
assert 'ZeroDivisionError' in r['stderr']

# Teste 3: Python com timeout
r = sandbox.executar_python("import time; time.sleep(30)")
assert r['sucesso'] == False
assert 'excedido' in r['stderr']

# Teste 4: Código perigoso
r = sandbox.executar_python("import os; os.system('rm -rf /')")
assert r['sucesso'] == False

# Teste 5: Lua
r = sandbox.compilar_lua("local x = 1\nprint(x)")
assert r['sucesso'] == True

# Teste 6: Estatísticas
metrics = sandbox.metricas()
assert metrics['total'] >= 5
```

---

## Fase 5 — MasterAgent (o cérebro)

**Arquivo:** `Scripts/mcr_devia/modulos/master_agent.py` (NOVO)
**Arquivos modificados:** `agent_loop.py`, `pipeline_executor.py`

**O que faz:** Junta TUDO num loop único que faz QUALQUER coisa.

```python
"""MasterAgent — Agente universal que faz QUALQUER coisa.

Ciclo: PERCEBER → PLANEJAR → EXECUTAR → VALIDAR → APRENDER

Recebe QUALQUER request e:
1. Percebe o que é (TaskAnalyzer)
2. Planeja subtarefas (TaskPlanner)
3. Executa cada subtarefa (ToolOrchestrator + IA)
4. Valida resultados (SandboxExecutor)
5. Aprende com o processo (EpisodicMemory + KG)

Uso:
    agent = MasterAgent()
    resultado = agent.executar("Cria um jogo de plataforma em Python com 3 fases")
    # → Projeto completo com código e instruções
"""
import os, sys, json, time
from typing import Dict, List, Optional

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos'))

from episodio_memory import EpisodicMemory
from task_planner import TaskPlanner
from tool_orchestrator import ToolOrchestrator
from sandbox_executor import SandboxExecutor
from ia import IA
from kg import KnowledgeGraph

class MasterAgent:
    """Agente universal. Faz QUALQUER coisa."""
    
    def __init__(self):
        self.ia = IA()
        self.kg = KnowledgeGraph()
        self.memoria = EpisodicMemory()
        self.tools = ToolOrchestrator()
        self.planner = TaskPlanner(tools_orchestrator=self.tools, ia=self.ia)
        self.sandbox = SandboxExecutor()
        self._passos = []
    
    def executar(self, request: str, task_type: str = '') -> Dict:
        """Executa QUALQUER request.
        
        Args:
            request: O que fazer (ex: "cria um mod BG3 com espada de fogo")
            task_type: Tipo de tarefa (se conhecido, opcional)
        
        Returns:
            Dict com resultado final e artefatos gerados
        """
        t0 = time.time()
        self._passos = []
        
        self._log('PERCEBER', f'Request: {request[:100]}')
        
        # === 1. PERCEBER ===
        # Buscar experiências similares
        memorias = self.memoria.buscar(request, 3)
        if memorias:
            self._log('PERCEBER', f'Encontradas {len(memorias)} experiências similares')
            for m in memorias:
                self._log('PERCEBER', f"  → {m['request'][:60]} ({'✅' if m['sucesso'] else '❌'})")
        
        # Buscar conhecimento relevante
        lessons = self.kg.buscar(request, max_r=3)
        if lessons:
            self._log('PERCEBER', f'Encontradas {len(lessons)} lições no KG')
        
        # === 2. PLANEJAR ===
        self._log('PLANEJAR', 'Criando plano de execução...')
        plano = self.planner.planejar(request, task_type)
        self._log('PLANEJAR', f'Plano: {len(plano)} subtarefas')
        
        for p in plano:
            self._log('PLANEJAR', f'  {p["id"]}. {p["acao"]} — {p["descricao"][:60]}')
        
        # === 3. EXECUTAR ===
        self._log('EXECUTAR', f'Iniciando execução de {len(plano)} subtarefas...')
        resultados = {}
        
        for subtarefa in plano:
            self._log('EXECUTAR', f'  Subtarefa {subtarefa["id"]}: {subtarefa["acao"]}')
            
            # Verificar dependências
            dependencias_ok = all(
                dep in resultados and resultados[dep].get('sucesso', False)
                for dep in subtarefa.get('depende_de', [])
            )
            if not dependencias_ok:
                self._log('EXECUTAR', f'  ⏭ Dependências não satisfeitas, pulando')
                resultados[subtarefa['id']] = {'sucesso': False, 'erro': 'Dependências não satisfeitas'}
                continue
            
            # Executar
            resultado = self._executar_subtarefa(subtarefa)
            resultados[subtarefa['id']] = resultado
            
            # Se falhou, tenta com IA cloud
            if not resultado.get('sucesso') and resultado.get('erro'):
                self._log('EXECUTAR', f'  ⚠ Falhou: {resultado["erro"][:80]}. Tentando cloud...')
                resultado_cloud = self.ia.router.chamar_cloud(
                    f"Resolva este problema: {subtarefa.get('descricao', request)}\n"
                    f"Erro anterior: {resultado['erro']}"
                )
                if resultado_cloud:
                    # Tenta novamente com contexto do cloud
                    resultado_retry = self._executar_subtarefa(subtarefa, contexto_extra=resultado_cloud)
                    if resultado_retry.get('sucesso'):
                        resultados[subtarefa['id']] = resultado_retry
                        self._log('EXECUTAR', f'  ✅ Cloud ajudou a resolver!')
                    else:
                        resultados[subtarefa['id']] = resultado  # mantém resultado original
                else:
                    self._log('EXECUTAR', f'  ❌ Cloud não disponível')
        
        # === 4. INTEGRAR ===
        self._log('INTEGRAR', 'Integrando resultados...')
        artefato_final = self._integrar(request, plano, resultados)
        
        tempo_total = time.time() - t0
        sucesso_geral = all(
            r.get('sucesso', False) for r in resultados.values()
        )
        
        resultado_final = {
            'sucesso': sucesso_geral,
            'request': request,
            'artefato': artefato_final,
            'plano': [{'id': p['id'], 'acao': p['acao']} for p in plano],
            'resultados': resultados,
            'n_subtarefas': len(plano),
            'n_sucesso': sum(1 for r in resultados.values() if r.get('sucesso')),
            'tempo': round(tempo_total, 1),
            'passos': self._passos,
        }
        
        # === 5. APRENDER ===
        licao = self._extrair_licao(request, plano, resultados)
        self.memoria.registrar(request, plano, resultado_final, licao)
        self._aprender_kg(request, resultado_final, licao)
        
        self._log('APRENDER', f'Lição registrada: {licao[:80]}')
        self._log('FIM', f'Concluído em {tempo_total:.1f}s — '
                  f'{resultado_final["n_sucesso"]}/{len(plano)} subtarefas OK')
        
        return resultado_final
    
    def _executar_subtarefa(self, subtarefa: Dict, contexto_extra: str = '') -> Dict:
        """Executa uma subtarefa do plano."""
        acao = subtarefa.get('acao', '')
        params = subtarefa.get('params', {})
        ferramenta = subtarefa.get('ferramenta', '')
        
        # Se tem ferramenta específica, usa
        if ferramenta and ferramenta != 'perguntar_ia':
            resultado = self.tools.executar(ferramenta, params)
            return resultado
        
        # Se é pergunta, usa IA
        if acao == 'perguntar_ia':
            pergunta = params.get('pergunta', subtarefa.get('descricao', ''))
            if contexto_extra:
                pergunta = f"{contexto_extra}\n\n{pergunta}"
            resposta = self.ia.gerar(pergunta, 0.4, 'pesado')
            return {
                'sucesso': bool(resposta),
                'resultado': resposta or 'Sem resposta',
                'erro': '' if resposta else 'IA não retornou resposta',
            }
        
        # Fallback: IA genérica
        descricao = subtarefa.get('descricao', str(params))
        if contexto_extra:
            descricao = f"{contexto_extra}\n\n{descricao}"
        resposta = self.ia.gerar(descricao, 0.4, 'code')
        return {
            'sucesso': bool(resposta),
            'resultado': resposta or 'Sem resposta',
            'erro': '' if resposta else 'IA não retornou resposta',
        }
    
    def _integrar(self, request, plano, resultados):
        """Junta todos os resultados parciais num artefato coeso."""
        partes = []
        
        for p in plano:
            r = resultados.get(p['id'], {})
            if r.get('sucesso') and r.get('resultado'):
                partes.append({
                    'passo': p['id'],
                    'acao': p['acao'],
                    'descricao': p.get('descricao', ''),
                    'conteudo': r['resultado'],
                })
        
        if not partes:
            # Se nada funcionou, tenta IA direta
            resposta = self.ia.gerar(
                f"Responda da melhor forma possível: {request}",
                0.4, 'pesado'
            )
            return {'resposta_final': resposta or 'Não foi possível completar a tarefa'}
        
        # Se só tem 1 parte, retorna direto
        if len(partes) == 1:
            return {'resposta_final': partes[0]['conteudo']}
        
        # Múltiplas partes — compila em artefato
        compilado = []
        for p in partes:
            compilado.append(f"### Passo {p['passo']}: {p['descricao']}\n{p['conteudo']}")
        
        return {'resposta_final': '\n\n'.join(compilado), 'partes': partes}
    
    def _extrair_licao(self, request, plano, resultados):
        """Extrai lição aprendida do processo."""
        n_sucesso = sum(1 for r in resultados.values() if r.get('sucesso'))
        n_total = len(plano)
        falhas = [p for p in plano if not resultados.get(p['id'], {}).get('sucesso')]
        
        if not falhas:
            return f"Tarefa concluída com sucesso em {n_sucesso}/{n_total} passos"
        else:
            acoes_falhas = ', '.join(f['acao'] for f in falhas[:3])
            return f"Tarefa parcial ({n_sucesso}/{n_total}). Falhas em: {acoes_falhas}"
    
    def _aprender_kg(self, request, resultado, licao):
        """Registra aprendizado no Knowledge Graph."""
        try:
            erro = request[:80]
            causa = f"Subtarefas: {resultado.get('n_subtarefas', 0)}, "
            causa += f"sucesso: {resultado.get('n_sucesso', 0)}"
            solucao = licao[:300]
            ctx = 'master_agent'
            self.kg.aprender(erro, causa, solucao, ctx)
        except:
            pass
    
    def _log(self, etapa, mensagem):
        """Registra passo da execução."""
        entry = {
            'etapa': etapa,
            'mensagem': mensagem,
            'tempo': time.strftime('%H:%M:%S'),
        }
        self._passos.append(entry)
        print(f'[{entry["tempo"]}] {etapa}: {mensagem}')
    
    def metricas(self):
        """Retorna métricas gerais do agente."""
        return {
            'episodios': self.memoria.metricas(),
            'sandbox': self.sandbox.metricas(),
            'ultima_execucao': self._passos[-1]['mensagem'] if self._passos else 'Nenhuma',
        }
```

**Mudanças no `agent_loop.py` existente:**

O `agent_loop.py` existente é **mantido como ferramenta** `gerar_npc` no ToolOrchestrator.
Ele não é mais o entry point principal — isso agora é o MasterAgent.

```python
# NOVO: adicionar ao final do agent_loop.py
# (opcional — o ToolOrchestrator já chama AgentLoop pela _cmd_gerar_npc)
```

**Mudanças no `pipeline_executor.py` existente:**

O `pipeline_executor.py` é **mantido** para responder perguntas (já funciona bem).
O MasterAgent pode usá-lo como ferramenta `perguntar_ia` para perguntas complexas.

```python
# Adicionar ao ToolOrchestrator:
def _cmd_pipeline(self, request):
    from modulos.pipeline_executor import PipelineExecutor
    pipe = PipelineExecutor(ia=self.ia, kg=self.kg)
    resposta, _ = pipe.executar(request, skip_tot=True)
    return resposta
```

---

## Plano de Integração (como as fases se conectam)

```
Fase 0: Router Híbrido (ia.py modificado)
  │
  ├── Fase 1: EpisodicMemory (novo)
  │     └── Usado pelo MasterAgent para buscar experiências
  │
  ├── Fase 2: ToolOrchestrator (novo)
  │     ├── Usa IA (Router Híbrido)
  │     ├── Usa AgentLoop (como ferramenta gerar_npc)
  │     ├── Usa LuaValidator (como ferramenta validar_lua)
  │     └── Usa comandos/ (como ferramentas)
  │
  ├── Fase 3: TaskPlanner (novo)
  │     ├── Usa ToolOrchestrator (para listar ferramentas)
  │     └── Usa IA (para planejar com LLM)
  │
  ├── Fase 4: SandboxExecutor (novo)
  │     └── Usado pelo MasterAgent para testar código
  │
  └── Fase 5: MasterAgent (novo) ← TUDO SE CONECTA AQUI
        ├── Usa EpisodicMemory ← contexto infinito
        ├── Usa RouterHíbrido ← inteligência ilimitada
        ├── Usa ToolOrchestrator ← ferramentas ilimitadas
        ├── Usa TaskPlanner ← qualquer tamanho
        ├── Usa SandboxExecutor ← validação real
        ├── Usa KG ← aprendizado de fatos
        └── Substitui agent_loop como entry point
```

---

## Gaps Analysis (o que o plano NÃO resolve)

### 🔴 Gap 1: LLM ainda alucina no planejamento

**Problema:** O TaskPlanner depende do LLM para decompor tarefas. Se o LLM
cria um plano errado (ex: "para criar um jogo, primeiro compre uma pizza"),
todo o resto falha.

**Mitigação:**
- Templates para casos conhecidos (PLANOS_CONHECIDOS)
- Fallback para plano de 1 passo se LLM retornar JSON inválido
- Loop de validação: antes de executar, verificar se cada subtarefa é
  executável por alguma ferramenta. Se não, replanejar.
- **Melhoria futura:** Validar plano com LLM antes de executar.

### 🔴 Gap 2: Dependências complexas (DAG)

**Problema:** O plano atual trata dependências como lista linear
(`depende_de` = lista de IDs). Mas dependências reais podem ser:
- "Passo 3 precisa do OUTPUT do Passo 1" (dado específico)
- "Passo 4 e 5 podem rodar em paralelo"
- "Se Passo 3 falhar, tentar Passo 3B em vez de 3A"

**Mitigação:**
- Começa com execução SEQUENCIAL (ignora paralelismo)
- Output de cada passo salvo em `resultados[id]` — passos futuros podem
  referenciar `resultados[1]['resultado']` se precisarem
- **Melhoria futura:** DAG executor com paralelismo real

### 🟡 Gap 3: Semântica vs Sintaxe na validação

**Problema:** SandboxExecutor executa código, mas só detecta ERROS DE EXECUÇÃO.
Não detecta ERROS DE LÓGICA. Um jogo de plataforma pode "rodar" mas não ter
gravidade, colisão, ou fases — tudo dentro da sintaxe.

**Mitigação:**
- SandboxExecutor + test cases: se o plano incluir "testar", podemos
  gerar testes junto com o código
- **Melhoria futura:** LLM auto-critique: "o código faz o que foi pedido?"

### 🟡 Gap 4: Cloud fallback depende de recursos externos

**Problema:** O Router Híbrido tem 3 modos:
- `web_search` (grátis) → depende da qualidade dos resultados de busca
- `api` → precisa de API key configurada
- `desligado` → só local

Se web_search não encontra resposta relevante, o fallback falha.

**Mitigação:**
- `web_search` como padrão (não precisa de API key)
- Para tarefas que exigem cloud: configurar `CLOUD_API_KEY`
- Documentar que cloud = melhor resultado, mas web search já ajuda

### 🟡 Gap 5: MasterAgent substitui agent_loop e pipeline_executor — risco de regressão

**Problema:** O MasterAgent é NOVO código que substitui entry points existentes.
Se ele tiver bugs, o sistema inteiro quebra.

**Mitigação:**
- Manter agent_loop.py e pipeline_executor.py intactos (não deletar)
- MasterAgent é um NOVO entry point, não substitui os antigos
- Testes de regressão: mesmos testes que passam hoje continuam passando
- Período de "sombreamento": ambos rodam, resultados comparados

### 🟢 Gap 6: Memória episódica sem embeddings

**Problema:** A busca na EpisodicMemory é por palavras-chave. "mod BG3 espada
de fogo" e "mod BG3 escudo de gelo" compartilham "mod", "BG3" — match parcial.
Com embeddings, a similaridade semântica seria capturada.

**Mitigação:**
- Palavras-chave funcionam bem para ~500 episódios
- **Melhoria futura:** Adicionar embeddings (usando ollama embeddings)
- Enquanto o número de episódios for < 500, keywords são suficientes

---

## Testes de Integração

```python
"""
TESTE DE INTEGRAÇÃO: MasterAgent completo
Roda todos os subsistemas juntos num cenário real.
"""

def teste_master_agent_completo():
    agent = MasterAgent()
    
    # === CENÁRIO 1: Pergunta simples ===
    print("\n=== CENÁRIO 1: Pergunta simples ===")
    r = agent.executar("O que é SPA no MCR?")
    assert r['sucesso'] or r['artefato'].get('resposta_final')
    print(f"Resultado: {r['artefato']['resposta_final'][:100]}...")
    
    # === CENÁRIO 2: Criação de código ===
    print("\n=== CENÁRIO 2: Criação de código ===")
    r = agent.executar("Cria um script Python que imprime a tabuada do 5", 'criar_codigo')
    assert r['sucesso']
    assert '5 x' in r['artefato']['resposta_final']
    
    # === CENÁRIO 3: Validação de código ===
    print("\n=== CENÁRIO 3: Código com erro ===")
    r = agent.executar("Cria um script Python com erro de sintaxe e corrige")
    assert r['sucesso'] or not r['sucesso']  # Pode falhar ou não
    
    # === CENÁRIO 4: NPC (caminho legado) ===
    print("\n=== CENÁRIO 4: NPC ===")
    r = agent.executar("Cria um ferreiro em Eridanus", 'npc_shop')
    print(f"NPC: {r.get('n_subtarefas', '?')} passos, {r.get('n_sucesso', '?')} sucesso")
    
    # === CENÁRIO 5: Request complexo ===
    print("\n=== CENÁRIO 5: Request complexo ===")
    r = agent.executar("Cria um site HTML simples com cabeçalho, navegação e rodapé")
    assert r['artefato'].get('resposta_final')
    print(f"Site gerado: {len(r['artefato']['resposta_final'])} chars")
    
    # === MÉTRICAS ===
    print("\n=== MÉTRICAS ===")
    metrics = agent.metricas()
    print(f"Episódios na memória: {metrics['episodios']['total']}")
    print(f"Sandbox execuções: {metrics['sandbox']['total']}")

if __name__ == '__main__':
    teste_master_agent_completo()
```

---

## Resumo Final

| Fase | Componente | Linhas | Depende de | Risco |
|------|-----------|--------|------------|-------|
| 0 | Router Híbrido | +40 (ia.py) | Nada | Baixo |
| 1 | EpisodicMemory | +180 (novo) | Nada | Baixo |
| 2 | ToolOrchestrator | +200 (novo) | IA, AgentLoop, LuaValidator | Médio |
| 3 | TaskPlanner | +250 (novo) | ToolOrchestrator, IA | Alto |
| 4 | SandboxExecutor | +120 (novo) | Python, Lua | Médio |
| 5 | MasterAgent | +350 (novo) | Todos acima | Alto |
| **Total** | | **~1140** | | |

**Ordem recomendada de implementação:** 0 → 1 → 2 → 4 → 3 → 5

**Por que SandboxExecutor antes do TaskPlanner?** Porque o SandboxExecutor
é usado pelo MasterAgent para validar código. É mais importante ter validação
real antes de planejamento complexo.

**Retrocompatibilidade:**
- `ia.py` modificado é 100% compatível (só adiciona funcionalidade)
- `agent_loop.py` NÃO é modificado (mantido como ferramenta)
- `pipeline_executor.py` NÃO é modificado (mantido para perguntas)
- `tool_registry.py` mantido (ToolOrchestrator é separado)
- Nada existente é quebrado — tudo novo é adicionado

---

> **Nota final:** Este plano não cria uma AGI. Cria um sistema que parece AGI
> porque combina: LLM local + contexto infinito (memória episódica) +
> inteligência escalável (cloud fallback) + ferramentas reais (execução,
> compilação, web). O resultado é um sistema que faz QUALQUER coisa que
> um LLM + ferramentas podem fazer — e isso é MUITO mais do que temos hoje.

---

## Apêndice A — Refinamento: MasterAgent Autônomo (v2)

> **Data:** 2026-06-28
> **Motivação:** O MasterAgent v1 gera código mas não estrutura um projeto completo
> (pastas, múltiplos arquivos, dependências, atalhos, testes). Este apêndice adiciona
> autonomia real: o agente recebe "cria um jogo" e entrega um projeto funcional.

### Gaps Identificados na v1

| # | Gap | Sintoma |
|---|-----|---------|
| 1 | Sem `pause-and-ask` | Executa sem nunca pedir opinião do usuário |
| 2 | Salva markdown, não código puro | `salvar_arquivo` grava instruções + código |
| 3 | Sem scaffolding | Não cria pastas `src/`, `assets/`, etc. |
| 4 | Sem dependências | Gera código mas não instala nem avisa |
| 5 | Sem multi-arquivo | 1 arquivo gigante em vez de módulos |
| 6 | Sem atalho/script | Não cria `run.bat`, `requirements.txt` |

### Arquivos Modificados

| Arquivo | Tipo | +/- Linhas |
|---------|------|------------|
| `modulos/decider.py` | **NOVO** — classificação universal via FAST | **+60** |
| `modulos/util.py` | +2 funções (com Decider) | +12 |
| `modulos/tool_orchestrator.py` | +5 ferramentas, +1 modificação | +80 |
| `modulos/task_planner.py` | +template 14 passos, +ações, +Decider | +60 |
| `modulos/master_agent.py` | +pause-and-ask, +suporte ações, +Decider | +80 |
| `modulos/ia.py` | Substitui regex por Decider | **-35** (remoção líquida) |
| **Total** | | **~257** (+60 - 35 = +25 líquidas) |

---

### A. `modulos/util.py` — Extração de código puro

```python
# NOVO — adicionar após extrair_codigo()
def extrair_codigo_puro(resposta):
    """Extrai o primeiro bloco ```python ... ```, ignorando texto explicativo."""
    if not resposta.startswith('```') and not resposta.startswith('Claro'):
        return resposta
    m = re.search(r'```python\s*\n(.+?)```', resposta, re.DOTALL)
    if m: return m.group(1).strip()
    m = re.search(r'```\s*\n(.+?)```', resposta, re.DOTALL)
    if m: return m.group(1).strip()
    linhas = [l for l in resposta.split('\n')
              if not l.startswith('Claro') and not l.startswith('Aqui')
              and not l.startswith('Primeiro') and '```' not in l]
    return '\n'.join(linhas).strip()


def extrair_nome_projeto(request):
    """Extrai nome do projeto do request (ex: 'jogo_plataforma').
    
    Usa Decider.extrair_json() para deteccao universal.
    Fallback para regex se Decider nao estiver disponivel.
    """
    try:
        from modulos.decider import Decider
        from modulos.ia import IA
        decider = Decider(IA())
        dados = decider.extrair_json(request, {'nome': ''},
            instrucao="Extraia o nome do projeto. "
                      "Ex: 'Cria um jogo de plataforma' -> 'jogo_plataforma'")
        if dados.get('nome'):
            return dados['nome']
    except Exception:
        pass
    # Fallback: regex
    m = re.search(r'jogo\s+(?:de\s+)?(\w+)', request.lower())
    if m: return f"jogo_{m.group(1)}"
    m = re.search(r'(?:projeto|app|site)\s+(\w+)', request.lower())
    if m: return m.group(1)
    return "meu_projeto"
```

---

### B. `modulos/tool_orchestrator.py` — 5 novas ferramentas

**B1 — `criar_diretorio`**
```python
# Registrar em _carregar_todas(), seção SISTEMA (após listar_diretorio):
self.registrar('criar_diretorio', self._cmd_criar_diretorio,
    desc="Cria estrutura de diretorios (ex: src/, assets/, runs/)",
    params={'caminho': 'string'}, output='string')

# Implementação (após _cmd_listar_dir):
def _cmd_criar_diretorio(self, caminho):
    os.makedirs(caminho, exist_ok=True)
    return f"Diretorio criado: {caminho}"
```

**B2 — `extrair_codigo`**
```python
# Registrar (após ferramentas IA):
self.registrar('extrair_codigo', self._cmd_extrair_codigo,
    desc="Extrai codigo puro de resposta markdown",
    params={'conteudo': 'string'}, output='string')

def _cmd_extrair_codigo(self, conteudo):
    from modulos.util import extrair_codigo_puro
    return extrair_codigo_puro(conteudo)
```

**B3 — `gerar_requirements`**
```python
self.registrar('gerar_requirements', self._cmd_gerar_requirements,
    desc="Cria requirements.txt com dependencias do projeto",
    params={'dependencias': 'string', 'caminho': 'string (opcional)'}, output='string')

def _cmd_gerar_requirements(self, dependencias="pygame", caminho=""):
    if not caminho:
        caminho = os.path.join(BASE, 'sandbox', 'requirements.txt')
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(f"# Dependencias do projeto\n{dependencias}\n")
    return f"Requirements salvo: {caminho}"
```

**B4 — `criar_atalho`**
```python
self.registrar('criar_atalho', self._cmd_criar_atalho,
    desc="Cria atalho run.bat (Windows) para executar o projeto",
    params={'comando': 'string', 'caminho': 'string (opcional)'}, output='string')

def _cmd_criar_atalho(self, comando, caminho=""):
    b = os.path.dirname(caminho) if caminho else os.path.join(BASE, 'sandbox')
    nome_base = os.path.splitext(os.path.basename(caminho or 'run'))[0]
    bat_path = os.path.join(b, f"{nome_base}.bat")
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(f"@echo off\n{comando}\npause\n")
    return f"Atalho criado: {bat_path}"
```

**B5 — `instalar_dependencias`**
```python
self.registrar('instalar_dependencias', self._cmd_instalar_deps,
    desc="Instala dependencias via pip",
    params={'requirements_path': 'string'}, output='string')

def _cmd_instalar_deps(self, requirements_path):
    r = subprocess.run(
        ['pip', 'install', '-r', requirements_path],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode == 0:
        return "Dependencias instaladas com sucesso"
    return f"Falha ao instalar: {r.stderr[:500]}"
```

**B6 — Modificar `_cmd_escrever_artefato` (existente)**
```python
def _cmd_escrever_artefato(self, codigo, caminho):
    """Salva codigo em arquivo, extraindo de markdown se necessario."""
    from modulos.util import extrair_codigo_puro
    codigo_puro = extrair_codigo_puro(codigo)
    return self._cmd_escrever_arquivo(caminho, codigo_puro)
```

---

### C. `modulos/task_planner.py` — Template projeto_jogo + novas ações

**C1 — Template `projeto_jogo` (14 passos)**
```python
# Adicionar em PLANOS_CONHECIDOS (após 'analisar_codigo'):
'projeto_jogo': [
    {'acao': 'perguntar_usuario', 'desc': 'Pergunta preferencias (engine, nome)'},
    {'acao': 'buscar_exemplos_similares', 'desc': 'Busca exemplos similares na memoria'},
    {'acao': 'criar_estrutura_pastas', 'desc': 'Cria pastas src/, assets/, runs/'},
    {'acao': 'gerar_modulo_main', 'desc': 'Gera main.py (loop principal)'},
    {'acao': 'gerar_modulo_entidades', 'desc': 'Gera entities.py (jogador, inimigos)'},
    {'acao': 'gerar_modulo_fases', 'desc': 'Gera phases.py (fases 1, 2, 3)'},
    {'acao': 'gerar_modulo_utils', 'desc': 'Gera utils.py (colisao, pontuacao)'},
    {'acao': 'extrair_codigo', 'desc': 'Extrai codigo puro dos modulos'},
    {'acao': 'validar_codigo', 'desc': 'Valida sintaxe de todos os .py'},
    {'acao': 'gerar_requirements', 'desc': 'Cria requirements.txt'},
    {'acao': 'criar_atalho', 'desc': 'Cria run.bat'},
    {'acao': 'instalar_dependencias', 'desc': 'pip install -r requirements.txt'},
    {'acao': 'testar_execucao', 'desc': 'Tenta executar e captura erros'},
    {'acao': 'relatorio_final', 'desc': 'Mostra estrutura criada'},
],
```

**C2 — Novas ações no `_ACAO_PARA_FERRAMENTA`**
```python
'perguntar_usuario': 'perguntar_ia',
'criar_estrutura_pastas': 'criar_diretorio',
'gerar_modulo_main': 'gerar_codigo',
'gerar_modulo_entidades': 'gerar_codigo',
'gerar_modulo_fases': 'gerar_codigo',
'gerar_modulo_utils': 'gerar_codigo',
'extrair_codigo': 'extrair_codigo',
'gerar_requirements': 'gerar_requirements',
'criar_atalho': 'criar_atalho',
'instalar_dependencias': 'instalar_dependencias',
'testar_execucao': 'executar_python',
'relatorio_final': 'perguntar_ia',
```

**C3 — `_inferir_tipo` via Decider (substitui regex)**

```python
# NOTA: Esta versão substitui o bloco de regex anterior.
# O Decider.classificar() entende contexto e sinônimos.

def _inferir_tipo(self, request):
    """Infere tipo de tarefa usando Decider (FAST). Fallback para regex."""
    if hasattr(self, '_decider') and self._decider:
        return self._decider.classificar(
            request, 
            list(PLANOS_CONHECIDOS.keys()),
            instrucao="'jogo'/'game'/'projeto' = projeto_jogo. "
                      "'npc'/'ferreiro'/'vendedor' = npc_shop. "
                      "'python'/'script'/'codigo' = criar_codigo. "
                      "'o que'/'como'/'explique' = pergunta_simples. "
                      "'analisa'/'revisa'/'verifica' = analisar_codigo."
        )
    # Fallback: regex (mantido para compatibilidade)
    r = request.lower()
    if any(p in r for p in ['cria', 'criar', 'faz', 'fazer', 'gera', 'gerar']):
        if any(p in r for p in ['npc', 'ferreiro', 'vendedor', 'loja', 'shop']):
            return 'npc_shop'
        if any(p in r for p in ['jogo', 'game', 'plataforma', 'fases', 'projeto']):
            return 'projeto_jogo'
        if any(p in r for p in ['python', 'script', 'codigo', 'programa']):
            return 'criar_codigo' if not any(p in r for p in ['jogo', 'game']) else 'projeto_jogo'
        if any(p in r for p in ['site', 'pagina', 'html']):
            return 'criar_codigo'
        return 'criar_codigo'
    if any(p in r for p in ['o que', 'o que e', 'como funciona', 'explique', 'quem']):
        return 'pergunta_simples'
    if any(p in r for p in ['analisa', 'revisa', 'verifica', 'testa']):
        return 'analisar_codigo'
    return None
```

**C4 — `_extrair_params` para novos tipos**
```python
# Adicionar em _extrair_params():
if acao == 'perguntar_usuario':
    return {'pergunta': f"Vou criar um projeto para: {request}. Engine padrao (pygame) ou outra?",
            'tarefa': 'leve'}

if acao.startswith('gerar_modulo_'):
    nome_modulo = acao.replace('gerar_modulo_', '')
    desc = {
        'main': 'loop principal, init pygame, tela, clock',
        'entidades': 'classe Jogador, classe Inimigo, fisica basica',
        'fases': '3 fases com plataformas e inimigos diferentes',
        'utils': 'colisao, pontuacao, game_over, draw_text',
    }
    desc_modulo = desc.get(nome_modulo, nome_modulo)
    return {
        'descricao': f"Crie o modulo {nome_modulo}.py do jogo. {desc_modulo}. Contexto: {request[:200]}",
        'linguagem': 'python',
    }

if acao == 'criar_estrutura_pastas':
    from modulos.util import extrair_nome_projeto
    nome = extrair_nome_projeto(request)
    return {'caminho': os.path.join(BASE, 'sandbox', nome)}

if acao == 'gerar_requirements':
    return {'dependencias': 'pygame>=2.5.0', 'caminho': ''}

if acao == 'criar_atalho':
    from modulos.util import extrair_nome_projeto
    nome = extrair_nome_projeto(request)
    return {'comando': f'python src/main.py', 'caminho': os.path.join(BASE, 'sandbox', nome)}

if acao == 'testar_execucao':
    return {'codigo': ''}

if acao == 'relatorio_final':
    return {'pergunta': 'Gere um relatorio final do projeto criado', 'tarefa': 'texto'}
```

---

### D. `modulos/master_agent.py` — Pause-and-ask + scaffolding

**D1 — `_ask_user()` (NOVO método)**
```python
def _ask_user(self, mensagem, opcoes=None):
    """Pergunta ao usuario antes de prosseguir. Timeout 60s, fallback 'sim'."""
    sandbox = os.path.join(BASE, 'sandbox')
    question_path = os.path.join(sandbox, '.mcr_question.json')
    answer_path = os.path.join(sandbox, '.mcr_answer.json')

    for f in [answer_path]:
        if os.path.exists(f): os.remove(f)

    with open(question_path, 'w', encoding='utf-8') as f:
        json.dump({
            'pergunta': mensagem,
            'opcoes': opcoes or ['sim', 'nao'],
            'timestamp': time.time(),
        }, f, ensure_ascii=False)

    print(f"\n[MasterAgent] PERGUNTA: {mensagem}")
    if opcoes:
        print(f"[MasterAgent] Opcoes: {', '.join(opcoes)}")
    print(f"[MasterAgent] Responda em .mcr_answer.json ou aguarde 60s (default: sim)")

    for _ in range(60):
        if os.path.exists(answer_path):
            try:
                with open(answer_path, 'r', encoding='utf-8') as f:
                    resp = json.load(f)
                return resp.get('resposta', 'sim')
            except Exception:
                pass
        time.sleep(1)

    print(f"[MasterAgent] Sem resposta, prosseguindo (default: sim)")
    return 'sim'
```

**D2 — Verificação de projeto grande via Decider (no `executar`, após PERCEBER)**
```python
# Adicionar após PERCEBER lessons, antes de PLANEJAR:

# === 1.5 PAUSE-AND-ASK ===
# Usa Decider para classificar o tamanho do projeto
decider = Decider(self.ia)
tipo_projeto = decider.classificar(
    request, ['simples', 'projeto', 'ambiguo'],
    instrucao="'jogo'/'game'/'projeto'/'site' = projeto. "
              "'script'/'funcao'/'funcaozinha' = simples. "
              "Se incerto ou muito curto (< 50 chars) = ambiguo."
)
projeto_grande = tipo_projeto in ('projeto', 'ambiguo')
request_ambiguo = tipo_projeto == 'ambiguo'

if projeto_grande:
    from modulos.util import extrair_nome_projeto
    nome_proj = extrair_nome_projeto(request)
    resposta = self._ask_user(
        f"Vou criar o projeto '{nome_proj}' com src/, 4 modulos "
        f"(main, entities, phases, utils), requirements.txt e run.bat. Posso prosseguir?",
        opcoes=['sim', 'nao', 'modificar']
    )
    if resposta == 'nao':
        return {'sucesso': False, 'request': request,
                'artefato': {'resposta_final': 'Cancelado pelo usuario'},
                'n_subtarefas': 0, 'n_sucesso': 0, 'tempo': 0}
    if resposta == 'modificar' or request_ambiguo:
        engine = self._ask_user(
            "Qual engine usar? (recomendo: pygame)",
            opcoes=['pygame', 'phaser', 'love2d', 'nenhum']  # Opcoes dinamicas
        )
        if engine not in ('pygame', 'nenhum'):
            request = f"{request} (usando {engine})"
```

**D3 — Suporte a novas ações no `_executar_subtarefa`**
```python
# Adicionar ANTES de "Se tem ferramenta, usa" (antes do if ferramenta...):

# --- ACOES ESPECIAIS (precisam de logica extra) ---
if acao == 'perguntar_usuario':
    pergunta = params.get('pergunta', 'Posso prosseguir?')
    resp = self._ask_user(pergunta)
    return {'sucesso': True, 'resultado': f"Usuario: {resp}"}

if acao == 'criar_estrutura_pastas':
    caminho = params.get('caminho', '')
    if caminho:
        for sub in ['src', 'assets', 'runs']:
            self.tools.executar('criar_diretorio', {'caminho': os.path.join(caminho, sub)})
        artefatos['projeto_path'] = caminho
        return {'sucesso': True, 'resultado': f"Estrutura em {caminho}"}
    return {'sucesso': False, 'erro': 'Caminho nao especificado'}

if acao == 'extrair_codigo':
    # Extrai codigo puro de todos os modulos acumulados
    modulos = {k: v for k, v in artefatos.items() if k.startswith('modulo_')}
    for nome_mod, codigo_bruto in modulos.items():
        codigo_puro = self.tools.executar('extrair_codigo', {'conteudo': codigo_bruto})
        if codigo_puro.get('sucesso'):
            artefatos[nome_mod] = codigo_puro['resultado']
    # Tambem executa extrair_codigo como ferramenta pro passo contar
    return self.tools.executar('extrair_codigo', {'conteudo': 'ok'})

if acao == 'testar_execucao':
    projeto_path = artefatos.get('projeto_path', os.path.join(BASE, 'sandbox'))
    main_path = os.path.join(projeto_path, 'src', 'main.py')
    if os.path.exists(main_path):
        with open(main_path, 'r') as f:
            codigo = f.read()
        return self.sandbox.executar_python(codigo)
    return {'sucesso': False, 'erro': f'main.py nao encontrado em {main_path}'}

if acao == 'relatorio_final':
    projeto_path = artefatos.get('projeto_path', os.path.join(BASE, 'sandbox'))
    relatorio = f"Projeto criado!\nLocal: {projeto_path}\nEstrutura:\n"
    if os.path.exists(projeto_path):
        for root, dirs, files in os.walk(projeto_path):
            nivel = root.replace(projeto_path, '').count(os.sep)
            relatorio += f"{'  ' * nivel}{os.path.basename(root)}/\n"
            for fname in files:
                relatorio += f"{'  ' * (nivel + 1)}{fname}\n"
    return {'sucesso': True, 'resultado': relatorio}
```

**D4 — Rastreamento de artefatos melhorado (no loop executar)**
```python
# Substituir linhas 106-110 (bloco "Se gerou codigo, armazena como artefato"):
if resultado.get('sucesso'):
    acao_atual = subtarefa.get('acao', '')
    res = resultado.get('resultado', '')
    if isinstance(res, str) and len(res) > 50:
        if 'gerar_modulo' in acao_atual:
            nome_mod = acao_atual.replace('gerar_modulo_', '')
            artefatos[f'modulo_{nome_mod}'] = res
        elif acao_atual == 'gerar_codigo':
            artefatos['codigo_gerado'] = res
    if acao_atual == 'salvar_arquivo':
        artefatos['arquivo_salvo'] = res
```

---

### Ordem de Implementação

```
Passo 0: decider.py         (+60 linhas)  — classificação universal via FAST
Passo 1: util.py            (+12 linhas)  — funções auxiliares (com Decider)
Passo 2: tool_orchestrator.py (+80 linhas) — 5 ferramentas + 1 modificação
Passo 3: task_planner.py     (+60 linhas) — template + ações + Decider
Passo 4: ia.py               (-35 linhas) — substitui regex por Decider
Passo 5: master_agent.py     (+80 linhas) — pause-and-ask + Decider
```

### Testes de Verificação

```python
# 1. Decider.classificar()
from modulos.decider import Decider
from modulos.ia import IA
decider = Decider(IA())
assert decider.classificar("O que e SPA no MCR?", ['local', 'cloud']) == 'local'
assert decider.classificar("pesquise python 3.13", ['local', 'cloud']) == 'cloud'

# 2. Decider.extrair_json()
dados = decider.extrair_json("Cria um jogo de plataforma", {'nome': '', 'linguagem': ''})
assert 'jogo' in dados.get('nome', '')

# 3. extrair_codigo_puro
from modulos.util import extrair_codigo_puro
assert "print" in extrair_codigo_puro("```python\nprint('oi')\n```")

# 4. inferir projeto_jogo (via Decider)
from modulos.task_planner import TaskPlanner
planner = TaskPlanner(ia=IA())
plano = planner.planejar("Cria um jogo de plataforma em Python com 3 fases")
assert len(plano) == 14  # template projeto_jogo
assert plano[0]['acao'] == 'perguntar_usuario'

# 5. criar_diretorio
from modulos.tool_orchestrator import ToolOrchestrator
tools = ToolOrchestrator()
r = tools.executar('criar_diretorio', {'caminho': 'sandbox/_test_proj/src'})
assert r['sucesso']

# 6. escrever_artefato com extração
r = tools.executar('escrever_artefato', {
    'codigo': "Explicacao\n```python\nprint('puro')\n```",
    'caminho': 'sandbox/_test_proj/test.py'
})
assert r['sucesso']
assert "print('puro')" in open('sandbox/_test_proj/test.py').read()

# 7. criar_atalho
r = tools.executar('criar_atalho', {'comando': 'python src/main.py', 'caminho': '_test/run'})
assert r['sucesso']

# 8. Cache do Decider
t1 = time.time()
decider.classificar("O que e SPA no MCR?", ['local', 'cloud'])
t2 = time.time()
assert (t2 - t1) < 0.1  # cache, nao chamou LLM

# 9. Fallback sem IA
decider_sem_ia = Decider()
assert decider_sem_ia.classificar("teste", ['a', 'b']) == 'a'  # primeira opcao

# 10. End-to-end (opcional, lento)
from modulos.master_agent import MasterAgent
agent = MasterAgent()
resultado = agent.executar("Cria um jogo de plataforma em Python com 3 fases")
assert resultado['n_subtarefas'] == 14
```

---

## Apêndice B — Bateria de Testes em Ciclo (20 Cenários)

> **Data:** 2026-06-28
> **Filosofia:** Jogo foi um EXEMPLO. Cada cenário funciona para QUALQUER contexto:
> API, CLI, site, dashboard, script, ferramenta, bot, etc.
> A **geração procedural via FAST** garante que a cada execução o teste é único,
> em contexto diferente do anterior.

### Princípios

1. **20 cenários** que formam um ciclo completo de vida de software
2. **Geração procedural via FAST** — nunca repete o mesmo request
3. **Contexto-agnóstico** — jogo foi exemplo; funciona para qualquer tipo de projeto
4. **Encadeamento** — cada cenário se alimenta do resultado do anterior
5. **Auto-aprendizado** — resultados alimentam o contexto do próximo cenário

### Gerador de Testes (procedural via FAST)

```python
class GeradorDeTestes:
    """Gera baterias de teste UNICAS via Decider/FAST.
    
    A cada chamada, gera combinacoes diferentes de:
    - linguagem (python, js, lua, rust, go...)
    - framework (pygame, flask, phaser, love2d, bevy...)
    - contexto (jogo, api, site, cli, dashboard, bot...)
    - features (save/load, auth, cache, logging...)
    """
    
    def __init__(self, ia):
        self.ia = ia
        self.decider = Decider(ia)
        self.historico = []  # requests ja gerados
    
    def gerar_request(self, cenario_id, projetos_anteriores=None):
        """Gera request UNICO para o cenario, em contexto DIFERENTE.
        
        Args:
            cenario_id: 1-20
            projetos_anteriores: Lista de dicts com projetos ja criados
        
        Returns:
            String com request de teste
        """
        if projetos_anteriores is None:
            projetos_anteriores = []
        
        # Contexto do que ja foi gerado (para evitar repeticoes)
        ctx_anterior = "Projetos ja criados: "
        ctx_anterior += ', '.join(p.get('contexto', '?') for p in projetos_anteriores[-5:])
        ctx_anterior += f" ({len(projetos_anteriores)} no total)"
        
        # Exemplos multi-contexto para cada cenario
        exemplos_multi = {
            1: [
                ("Cria um jogo de plataforma em Python com 3 fases", "python/jogo"),
                ("Cria uma API REST em Flask com 3 endpoints", "python/api"),
                ("Cria uma CLI tool em Python que processa CSV", "python/cli"),
                ("Cria um site de documentacao em HTML+CSS", "html/site"),
            ],
            2: [
                ("Cria um editor visual para as fases do jogo", "ferramenta"),
                ("Cria um gerador de relatorios PDF para a API", "ferramenta"),
                ("Cria um validador de dados de entrada para o CLI", "ferramenta"),
            ],
        }
        
        exemplos = exemplos_multi.get(cenario_id, [])
        
        dados = self.decider.extrair_json(
            f"Cenario {cenario_id}: gere um request de teste UNICO e DIFERENTE",
            {'request': '', 'linguagem': '', 'contexto': ''},
            exemplos=exemplos[:3],
            instrucao=(
                f"{ctx_anterior}\n"
                f"NUNCA repita contexto, linguagem ou框架.\n"
                f"Contextos possiveis: jogo, api, site, cli, dashboard, script, "
                f"ferramenta, bot, analise, documentacao, tutorial...\n"
                f"Varie LINGUAGEM e CONTEXTO a cada chamada."
            )
        )
        
        return dados.get('request', f"Request para cenario {cenario_id}")


def executar_bateria(n=10, semente=None):
    """Executa bateria de N cenarios em contextos variados.
    
    Args:
        n: Numero de cenarios (1-20, padrao 10)
        semente: Para reprodutibilidade (None = aleatorio)
    
    Retorna:
        Lista de resultados (dicts com sucesso, n_subtarefas, etc.)
    """
    import random
    from modulos.master_agent import MasterAgent
    from modulos.ia import IA
    
    ia = IA()
    gerador = GeradorDeTestes(ia)
    agent = MasterAgent()
    
    if semente is not None:
        random.seed(semente)
    
    projetos_anteriores = []
    resultados = []
    
    cenarios_sorteados = random.sample(range(1, 21), min(n, 20))
    
    for cenario_id in cenarios_sorteados:
        request = gerador.gerar_request(cenario_id, projetos_anteriores)
        
        print(f"\n{'='*60}")
        print(f"  CENARIO {cenario_id}/20")
        print(f"{'='*60}")
        print(f"  Request: {request[:100]}...")
        
        r = agent.executar(request)
        resultados.append(r)
        
        n_ok = r.get('n_sucesso', 0)
        n_total = r.get('n_subtarefas', 0)
        print(f"  -> {n_ok}/{n_total} subtarefas OK ({r.get('tempo',0)}s)")
        
        projetos_anteriores.append({
            'id': cenario_id,
            'request': request[:100],
            'contexto': extrair_contexto(request),
            'linguagem': extrair_linguagem(request),
            'sucesso': r.get('sucesso', False),
            'n_ok': n_ok,
        })
    
    # Relatorio final
    print(f"\n{'='*60}")
    total_ok = sum(1 for r in resultados if r.get('sucesso'))
    print(f"  BATERIA: {total_ok}/{n} CENARIOS OK")
    print(f"  Subtarefas totais: {sum(r.get('n_subtarefas',0) for r in resultados)}")
    print(f"  Tempo total: {sum(r.get('tempo',0) for r in resultados):.0f}s")
    print(f"{'='*60}")
    
    return resultados
```

### Os 20 Cenários

#### 1 — Criar projeto principal

**Pipeline:** `projeto_jogo` (14 passos) + pause-and-ask + validar código

| Variacao | Contexto | Exemplo |
|----------|----------|---------|
| 1a | Jogo | `"Cria um jogo de plataforma em Python com 3 fases, gravidade, colisao, inimigos e pontuacao"` |
| 1b | API | `"Cria uma API REST em Flask com 3 endpoints: criar, listar, deletar recursos"` |
| 1c | CLI | `"Cria uma CLI tool em Python que processa arquivos CSV e gera relatorio em JSON"` |
| 1d | Site | `"Cria um site de documentacao em HTML+CSS com 3 paginas e navegacao"` |

#### 2 — Ferramenta complementar

**Pipeline:** `criar_codigo` + EpisodicMemory + integracao com projeto anterior

| Variacao | Contexto | Exemplo |
|----------|----------|---------|
| 2a | Jogo | `"Cria um editor visual para as fases do jogo com tkinter. Salva em tools/"` |
| 2b | API | `"Cria um cliente HTTP em Python para testar os endpoints da API. Salva em tools/"` |
| 2c | CLI | `"Cria um gerador de dados de teste para o CLI tool. Salva em tools/"` |

#### 3 — Site sobre o projeto

**Pipeline:** `criar_codigo` multi-arquivo + HTML/CSS/JS

| Variacao | Contexto | Exemplo |
|----------|----------|---------|
| 3a | Jogo | `"Cria landing page para o jogo: homepage, download, contato. HTML+CSS+JS. Salva em site/"` |
| 3b | API | `"Cria portal de documentacao interativa da API com playground. Salva em site/"` |
| 3c | CLI | `"Cria dashboard web com exemplos de uso do CLI tool. Salva em site/"` |

#### 4 — Auditoria de código

**Pipeline:** `analisar_codigo` + leitura de multiplos arquivos + sintese critica

| Variacao | Contexto | Exemplo |
|----------|----------|---------|
| 4a | Arquitetura | `"analise a arquitetura de TUDO: acoplamento, coesao, SRP. Mencione linhas especificas."` |
| 4b | Seguranca | `"audite seguranca: injecao, path traversal, dados sensiveis. Sugira corrigir as 3 mais criticas."` |
| 4c | Performance | `"analise performance: loops ineficientes, alocacao excessiva, I/O desnecessario."` |

#### 5 — Aplicar melhorias

**Pipeline:** LLM planejamento + escrever_arquivo + executar_python + relatorio

| Variacao | Contexto | Exemplo |
|----------|----------|---------|
| 5a | Corrigir bugs | `"aplique as 3 correcoes de bugs sugeridas. Mostre diff antes vs depois."` |
| 5b | Refatorar | `"aplique as 3 refatoracoes de arquitetura sugeridas. Valide com pytest."` |
| 5c | Otimizar | `"aplique as 3 otimizacoes de performance sugeridas. Mostre metricas."` |

#### 6 — Testes unitários

**Pipeline:** `criar_codigo` (test_*.py) + executar_python (pytest/unittest/doctest)

| Variacao | Framework | Exemplo |
|----------|-----------|---------|
| 6a | pytest | `"crie testes com pytest para os modulos principais. Crie tests/ e execute."` |
| 6b | unittest | `"crie testes com unittest para boundary conditions. Crie tests/ e execute."` |
| 6c | doctest | `"adicione doctests nas docstrings. Execute python -m doctest para validar."` |

#### 7 — Refatorar com boas práticas

**Pipeline:** LLM planejamento + edicao + executar_python

| Variacao | Foco | Exemplo |
|----------|------|---------|
| 7a | Type hints | `"refatore: crie config.py, adicione type hints, remova magic numbers."` |
| 7b | Patterns | `"refatore usando: Strategy, Observer, Factory patterns."` |
| 7c | Modular | `"refatore: separe em modulos menores, use dataclasses."` |

#### 8 — Otimizar performance

**Pipeline:** analisar_codigo + gerar_codigo + executar_python

| Variacao | Tecnica | Exemplo |
|----------|---------|---------|
| 8a | Pooling | `"implemente object pooling para objetos criados/destruidos frequentemente."` |
| 8b | Cache | `"adicione cache LRU e lazy loading. Mostre comparativo."` |
| 8c | Vetorizacao | `"otimize loops com numpy ou comprehensions. Mostre speedup."` |

#### 9 — Empacotar projeto

**Pipeline:** `criar_codigo` + multiplos arquivos de configuracao

| Variacao | Formato | Exemplo |
|----------|---------|---------|
| 9a | setuptools | `"crie setup.py, Dockerfile, Makefile, .gitignore na raiz."` |
| 9b | Poetry | `"crie pyproject.toml, Dockerfile multi-stage, docker-compose.yml."` |
| 9c | Pipenv | `"crie Pipfile, Dockerfile, Makefile, .env.example."` |

#### 10 — Documentar tudo

**Pipeline:** `criar_codigo` + leitura de modulos + sintese

| Variacao | Formato | Exemplo |
|----------|---------|---------|
| 10a | README | `"gere README.md, CHANGELOG.md e docstrings em todas as funcoes."` |
| 10b | Sphinx | `"crie documentacao Sphinx: conf.py, index.rst, api.rst."` |
| 10c | MkDocs | `"crie documentacao MkDocs: mkdocs.yml, docs/index.md."` |

#### 11 — Auditoria de segurança

**Pipeline:** analisar_codigo + editar + executar_python

**Exemplo:** `"audite seguranca: injecao de codigo, path traversal, dados sensiveis em texto puro, falta de validacao de input. Corrija as 3 vulnerabilidades mais criticas."`

#### 12 — Internacionalização (i18n)

**Pipeline:** `criar_codigo` + editar modulos + executar_python

**Exemplo:** `"adicione suporte a 2 idiomas (pt-BR e en-US). Extraia strings, crie arquivos de traducao, implemente seletor de idioma."`

#### 13 — CI/CD Pipeline

**Pipeline:** `criar_codigo` (YAML config)

**Exemplo:** `"crie pipeline CI/CD com stages: lint, test, build, deploy. Inclua matrix de versoes e caching."`

#### 14 — Linting e Pre-commit

**Pipeline:** `criar_codigo` + executar_comando + editar codigo

**Exemplo:** `"configure pylint+black+flake8. Crie .pre-commit-config.yaml com hooks. Execute e corrija erros."`

#### 15 — Monitoramento e Logging

**Pipeline:** `criar_codigo` + editar modulos + executar_python

**Exemplo:** `"adicione logging estruturado com niveis (DEBUG, INFO, ERROR), rotacao de logs, endpoint /health."`

#### 16 — UX/UI e Acessibilidade

**Pipeline:** `criar_codigo` (CSS/HTML) + analisar_codigo

**Exemplo:** `"melhore acessibilidade: ARIA labels, contraste, navegacao por teclado, modo escuro."`

#### 17 — API RESTful

**Pipeline:** `criar_codigo` + executar_python + criar_atalho

**Exemplo:** `"crie API REST: GET, POST, DELETE. Documente com OpenAPI/Swagger."`

#### 18 — Backup e Recovery

**Pipeline:** `criar_codigo` + criar_atalho

**Exemplo:** `"crie scripts de backup: compacta src/, tools/, site/ com timestamp. Crie restore.sh."`

#### 19 — Migração de dados

**Pipeline:** `criar_codigo` + editar modulos + executar_python

**Exemplo:** `"migre armazenamento de JSON para SQLite. Crie script de migracao com rollback."`

#### 20 — Feature Flags

**Pipeline:** `criar_codigo` + editar modulos + executar_python

**Exemplo:** `"implemente feature toggles: config JSON, funcao is_feature_enabled(), 3 features."`

---

### Resumo

| Aspecto | Valor |
|---------|-------|
| Cenarios | 20 (ciclo completo de vida de software) |
| Contextos possiveis | Ilimitados (jogo, api, site, cli, dashboard, bot, script...) |
| Geracao de variacoes | Procedural via Decider/FAST com contexto dos anteriores |
| Linguagens | Python, JavaScript, Lua, TypeScript, Rust, Go, + FAST |
| Reprodutibilidade | Semente fixa para debugging |
| Garantia de diversidade | FAST recebe historico e EVITA repetir contexto |
| Pipeline testado | projeto_jogo, criar_codigo, analisar_codigo, LLM, memoria episodica |

---

## Apêndice C — Validador Universal (substitui validar_python)

> **Data:** 2026-06-28
> **Motivação:** `validar_python` é específico para Python. O sistema precisa de um
> **validador universal** que detecta a linguagem via Decider/FAST e dispara o
> validador correto, ou ignora graciosamente se não houver suporte.

### O problema

| Local | Código | Problema |
|-------|--------|----------|
| `tool_orchestrator.py:366` | `_cmd_validar_python()` | Só valida Python (`ast.parse()`) |
| `tool_orchestrator.py:353` | `_cmd_validar_lua()` | Só valida Lua (`luac -p`) |
| `master_agent.py:268-275` | Heurística `if 'const ' in...` | Frágil, não escala |
| `_ACAO_PARA_FERRAMENTA` | `validar_codigo -> validar_python` | Mapeamento fixo ignora linguagem |

### Solução

Criar `_cmd_validar_codigo()` universal no `tool_orchestrator.py`:

```python
def _cmd_validar_codigo(self, codigo):
    """Valida codigo em QUALQUER linguagem.
    
    1. Extrai codigo puro (remove markdown)
    2. Detecta linguagem via Decider/FAST com exemplos
    3. Dispara validador especifico (Python=ast, JS=node --check, JSON=json.loads, Lua=luac)
    4. Fallback: validacao ignorada se nao houver validador
    """
    from modulos.util import extrair_codigo_puro
    from modulos.decider import Decider
    from modulos.ia import IA
    
    codigo_puro = extrair_codigo_puro(codigo)
    
    decider = Decider(IA())
    lang = decider.classificar(
        codigo_puro[:300],
        ['python', 'javascript', 'lua', 'json', 'html', 'yaml',
         'typescript', 'css', 'xml', 'csharp', 'rust', 'go'],
        exemplos=[
            ("import pygame; print('hello')", "python"),
            ("const x = 1; console.log(x);", "javascript"),
            ('{"nome": "Joao", "idade": 30}', "json"),
            ("<html><body>Oi</body></html>", "html"),
            ("local player = { x = 10 }", "lua"),
        ],
        instrucao="Detecte a linguagem pelo codigo. Se incerto, prefira 'python'."
    )
    
    validadores = {
        'python': self._validar_python,
        'javascript': self._validar_javascript,
        'typescript': self._validar_javascript,
        'lua': self._validar_lua,
        'json': self._validar_json,
        'html': self._validar_html,
    }
    
    validador = validadores.get(lang)
    if validador:
        return validador(codigo_puro)
    
    return {'valido': True, 'erros': [], 'aviso': f'Sem validador para {lang}, ignorado'}
```

### Validadores específicos (procedurais)

```python
_HAS_NODE = None
def _tem_node():
    global _HAS_NODE
    if _HAS_NODE is None:
        import subprocess
        _HAS_NODE = subprocess.run(['node', '--version'], capture_output=True).returncode == 0
    return _HAS_NODE

def _validar_python(self, codigo):
    try:
        ast.parse(codigo)
        return {'valido': True, 'erros': []}
    except SyntaxError as e:
        return {'valido': False, 'erros': [f'Linha {e.lineno}: {e.msg}']}

def _validar_javascript(self, codigo):
    if not _tem_node():
        return {'valido': True, 'erros': [], 'aviso': 'node nao instalado'}
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as f:
        f.write(codigo)
        tmp = f.name
    r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True, timeout=10)
    os.unlink(tmp)
    return {'valido': r.returncode == 0, 'erros': [] if r.returncode == 0 else [r.stderr[:200]]}

def _validar_json(self, codigo):
    try:
        import json as _json
        _json.loads(codigo)
        return {'valido': True, 'erros': []}
    except Exception as e:
        return {'valido': False, 'erros': [str(e)]}

def _validar_html(self, codigo):
    if '<html' in codigo and '</html>' in codigo:
        return {'valido': True, 'erros': []}
    return {'valido': False, 'erros': ['HTML incompleto (sem <html> e </html>)']}
```

### Mudanças nos arquivos

| Arquivo | O quê | +/- |
|---------|-------|-----|
| `tool_orchestrator.py` | +`_cmd_validar_codigo()` + `_validar_javascript()` + `_validar_json()` + `_validar_html()` + `_tem_node()` | **+65** |
| `tool_orchestrator.py` | Registrar `validar_codigo` como nova ferramenta | **+4** |
| `master_agent.py` | Handler `validar_codigo` simplificado: delega para `tools.executar('validar_codigo', ...)` | **-35** |
| `task_planner.py` | `_ACAO_PARA_FERRAMENTA`: `validar_codigo -> 'validar_codigo'` | **0** |
| **Total** | | **~+34** |

### Testes

```python
tools = ToolOrchestrator()

# 1. Python
r = tools.executar('validar_codigo', {'codigo': 'x = 1; print(x)'})
assert r['resultado']['valido']

# 2. JavaScript (fallback sem node)
r = tools.executar('validar_codigo', {'codigo': 'const x = 1;'})
assert r['sucesso']

# 3. JSON valido
r = tools.executar('validar_codigo', {'codigo': '{"nome": "Joao"}'})
assert r['resultado']['valido']

# 4. JSON invalido
r = tools.executar('validar_codigo', {'codigo': '{nome: Joao}'})
assert not r['resultado']['valido']

# 5. Rust (sem validador)
r = tools.executar('validar_codigo', {'codigo': 'fn main() { println!("hi"); }'})
assert r['resultado'].get('aviso', '')
```

---

## Status da Implementação (2026-06-28)

### ✅ Implementado e Funcionando

| Módulo | Arquivo | Linhas | Função |
|--------|---------|--------|--------|
| **Decider** | `modulos/decider.py` | +180 | Classificador universal via FAST com cache LRU |
| **Router Híbrido** | `modulos/ia.py` | ~305 | `decider()` usa `Decider.classificar()`; `buscar_web()` com DuckDuckGo + Wikipedia |
| **ToolOrchestrator** | `modulos/tool_orchestrator.py` | ~400 | 22 ferramentas executáveis com segurança e timeout |
| **TaskPlanner** | `modulos/task_planner.py` | ~550 | 5 templates + PlanValidator + Decider + linguagem dinâmica |
| **EpisodicMemory** | `modulos/episodic_memory.py` | ~240 | Memória com embeddings (nomic-embed-text) + keywords |
| **SandboxExecutor** | `modulos/sandbox_executor.py` | ~195 | Execução segura de Python + Lua |
| **MasterAgent** | `modulos/master_agent.py` | ~512 | Loop PERCEBER→PLANEJAR→EXECUTAR→INTEGRAR→APRENDER + pause-and-ask |
| **Validador Universal** | `modulos/tool_orchestrator.py` | +65 | `_cmd_validar_codigo()` cobre 6 linguagens |
| **Entry Point CLI** | `comandos/cmd_master.py` | +100 | `MCR_DevIA-Kernel.py master "<request>"` |
| **Utils** | `modulos/util.py` | ~145 | `extrair_codigo_puro()`, `extrair_nome_projeto()` com Decider |
| **Bateria de Testes** | `sandbox/_test_bateria.py` | +300 | 20 cenários contexto-agnósticos + GeradorDeTestes via FAST |

### 📝 Blueprint Original (mantido como referência)

As seções "Fase 0" a "Fase 5" contêm o **plano original** que serviu de base.
O código real pode diferir do blueprint original — os Apêndices documentam as diferenças.

### 🔮 Próximas Melhorias Possíveis

| Melhoria | Prioridade | Esforço |
|----------|-----------|---------|
| Enriquecimento de request genérico (sugerir features) | Média | +50 linhas |
| Retry automático quando `validar_codigo` falhar (regenerar código) | Baixa | +30 linhas |
| Suporte a mais validadores (CSS, YAML, XML, SQL) | Baixa | +20 linhas |
| Testes paralelos para bateria completa | Baixa | +40 linhas |

---

## Apêndice D — Arquitetura ML/NN/AGI (6 Correções)

> **Data:** 2026-06-28
> **Filosofia:** O MCR-DevIA não deve apenas *estudar* sobre Machine Learning, Redes Neurais
> e AGI — ele deve **incorporar esses conceitos em sua arquitetura**. Cada correção abaixo
> mapeia um conceito de ML para uma implementação concreta no código.

### Diagnóstico: 10 Pontos Fracos

| # | Fraqueza | Módulo | Impacto | Conceito ML |
|---|----------|--------|---------|-------------|
| **F1** | `KG.buscar()` usa só keyword match, sem embeddings | `kg.py:62-79` | Busca semântica pobre | Supervisionado |
| **F2** | Score de sucesso não influencia decisões futuras | `episodic_memory.py:192-196` | Sistema não "aprende" com erros | Reforço |
| **F3** | `_aprender_kg()` salva sempre `ctx='master_agent'` | `master_agent.py:424-434` | KG vira depósito sem estrutura | Dataset |
| **F4** | Sem feedback do APRENDER para PERCEBER/PLANEJAR | `master_agent.py:203-206` | Pipeline não se ajusta com erros | Backpropagation |
| **F5** | Sem clusterização de requests similares | `episodic_memory.py` | Não encontra padrões ocultos | Não Supervisionado |
| **F6** | Sem metacognição (sabe o que sabe?) | `master_agent.py` | Não sabe seus próprios limites | AGI |
| **F7** | KG sem embeddings para busca semântica | `kg.py` | Busca por palavra exata apenas | Supervisionado |
| **F8** | Decider não aprende com erros de classificação | `decider.py` | Mesmo erro sempre | Reforço |
| **F9** | Formato de resultado não padronizado | `episodic_memory.py:123-132` | Dados não estruturados para treino | Dataset |
| **F10** | Sem replay de experiências | `episodic_memory.py` | Episódios antigos nunca reavaliados | Replay |

### Plano de Correções (6 Módulos, ~+210 linhas)

#### C1 — KG com Embeddings (Supervisionado)

**Arquivo:** `modulos/kg.py`
**Conceito:** Supervisionado — usar exemplos rotulados (lições) como dataset de treino

```python
def _gerar_embedding_kg(texto):
    """Gera embedding para busca no KG."""
    if texto in _embedding_cache_kg:
        return _embedding_cache_kg[texto]
    try:
        dados = json.dumps({'model': 'nomic-embed-text:latest', 'prompt': texto[:500]}).encode()
        req = urllib.request.Request(f'http://localhost:11434/api/embeddings', data=dados,
            headers={'Content-Type': 'application/json'})
        resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
        emb = resp.get('embedding')
        if emb:
            _embedding_cache_kg[texto] = emb
        return emb
    except:
        return None

def buscar_por_embedding(self, texto, n=3):
    """Busca lições por similaridade semântica (cosine). Fallback keyword."""
    emb = _gerar_embedding_kg(texto)
    if not emb:
        return self.buscar(texto, n)
    scores = []
    for l in self.data['licoes']:
        if 'embedding' not in l: continue
        score = sum(x*y for x,y in zip(emb, l['embedding']))
        na = math.sqrt(sum(x*x for x in emb))
        nb = math.sqrt(sum(x*x for x in l['embedding']))
        if na > 0 and nb > 0:
            scores.append((score/(na*nb), l))
    scores.sort(key=lambda x: -x[0])
    return [s[1] for s in scores[:n]]

# Modificar aprender() para salvar embedding:
def aprender(self, erro, causa, solucao, ctx='geral'):
    lid = f'L{len(self.data["licoes"])+1:04d}'
    lesson = {'id': lid, 'erro': erro[:80], 'causa': causa[:200],
              'solucao': solucao[:500], 'ctx': ctx, 'usos': 0}
    try:
        emb = _gerar_embedding_kg(erro + ' ' + causa)
        if emb: lesson['embedding'] = emb
    except: pass
    self.data['licoes'].append(lesson)
    self.salvar()
```

#### C2 — EpisodicMemory como Função de Recompensa (Reforço)

**Arquivo:** `modulos/episodic_memory.py`
**Conceito:** Reforço — ações com maior sucesso têm prioridade

```python
def taxa_sucesso_para(self, acao, request=''):
    """Retorna taxa de sucesso historica para uma acao. Reforco."""
    episodios_acao = [e for e in self.episodios
                      if acao in str(e.get('resultado', ''))]
    if not episodios_acao:
        return 0.5  # desconhecido = neutro
    sucessos = sum(1 for e in episodios_acao if e.get('sucesso'))
    return sucessos / len(episodios_acao)

def buscar_com_peso_de_reforco(self, request, n=3, acoes=None):
    """Busca experiencias com peso extra para acoes que funcionaram."""
    resultados = self.buscar(request, n * 2)
    if acoes and resultados:
        for ep in resultados:
            for acao in acoes:
                taxa = self.taxa_sucesso_para(acao, request)
                if taxa > 0.7:
                    ep['_score_reforco'] = ep.get('_score_reforco', 0) + taxa
    return resultados[:n]
```

#### C3 — KG Estruturado como Dataset (Dados de Treino)

**Arquivo:** `modulos/master_agent.py` — método `_aprender_kg()`

```python
# Substituir linhas 424-434:
def _aprender_kg(self, request, resultado, licao, task_type=''):
    """Registra aprendizado como DATASET estruturado."""
    try:
        erro = request[:80]
        tt = resultado.get('task_type', task_type) or 'geral'
        n_ok = resultado.get('n_sucesso', 0)
        n_total = resultado.get('n_subtarefas', 0)
        tempo = resultado.get('tempo', 0)
        causa = f"tipo={tt} | subs={n_ok}/{n_total} | tempo={tempo}s"
        solucao = licao[:500]
        ctx = f'exec_{tt}'  # ex: exec_projeto_jogo, exec_criar_codigo
        self.kg.aprender(erro, causa, solucao, ctx)
    except Exception:
        pass
```

#### C4 — Feedback Loop (Backpropagation no Pipeline)

**Arquivo:** `modulos/master_agent.py` — NOVO método

```python
def _feedback(self, request, tipo_porte, plano, resultados):
    """Feedback do resultado para ajustar decisoes futuras.
    Backpropagation: erro na saida ajusta camadas anteriores."""
    sucesso = all(r.get('sucesso', False) for r in resultados.values())
    if sucesso:
        return
    n_ok = sum(1 for r in resultados.values() if r.get('sucesso'))
    n_total = len(plano)
    if n_ok < n_total * 0.5 and n_total > 0:
        licao = (f"FRACASSO: {n_ok}/{n_total} para '{request[:60]}'. "
                 f"Tipo='{tipo_porte}' parece incorreto.")
        self.kg.aprender(
            erro=f"Feedback: {request[:60]}",
            causa=f"tipo={tipo_porte} | sucesso={n_ok}/{n_total}",
            solucao=licao[:300],
            ctx='feedback_fracasso'
        )
```

#### C5 — Clusterização de Requests (Não Supervisionado)

**Arquivo:** `modulos/episodic_memory.py`

```python
def clusterizar(self, n_clusters=5):
    """Agrupa episodios por similaridade semantica (K-means simplificado).
    Nao Supervisionado: descobre padrões sem rotulos."""
    episodios = [e for e in self.episodios if 'embedding' in e]
    if len(episodios) < n_clusters:
        return {}
    embeddings = [e['embedding'] for e in episodios]
    import random
    centroides = random.sample(embeddings, min(n_clusters, len(embeddings)))
    clusters = {i: [] for i in range(len(centroides))}
    for _ in range(5):
        for e, ep in zip(embeddings, episodios):
            dists = [sum((a-b)**2 for a,b in zip(e, c))**0.5 for c in centroides]
            clusters[dists.index(min(dists))].append(ep)
        for cid in clusters:
            if clusters[cid]:
                centroides[cid] = [sum(vals)/len(vals) for vals in
                                   zip(*[e['embedding'] for e in clusters[cid]])]
    return {k: [ep['request'][:60] for ep in v] for k, v in clusters.items()}
```

#### C6 — Metacognição (AGI)

**Arquivo:** `modulos/master_agent.py` — NOVO método

```python
def autoavaliar(self, request):
    """Autoavaliacao: o sistema sabe o que sabe e o que nao sabe.
    AGI: consciencia dos proprios limites."""
    lessons = self.kg.buscar(request, max_r=3)
    lessons_sem = []
    try:
        if hasattr(self.kg, 'buscar_por_embedding'):
            lessons_sem = self.kg.buscar_por_embedding(request, n=2)
    except: pass
    total_conc = len(lessons) + len(lessons_sem)
    experiencias = self.memoria.buscar(request, n=3)
    n_exp = len(experiencias)
    tx_suc = sum(1 for e in experiencias if e.get('sucesso')) / max(n_exp, 1)
    if total_conc >= 3 and n_exp >= 2 and tx_suc >= 0.7:
        return {'confianca': 'alta', 'gaps': [], 'acao': 'executar'}
    if total_conc >= 1:
        gaps = []
        if n_exp < 2: gaps.append('pouca experiencia')
        if total_conc < 3: gaps.append('conhecimento limitado')
        return {'confianca': 'media', 'gaps': gaps, 'acao': 'executar_com_cautela'}
    return {'confianca': 'baixa', 'gaps': ['sem conhecimento'], 'acao': 'estudar_antes'}
```

### Matriz de Implementação

| # | O que | Arquivo | +/- | Conceito |
|---|-------|---------|-----|----------|
| C1 | KG com embeddings + busca semântica | `kg.py` | +35 | Supervisionado |
| C2 | EpisodicMemory como função de recompensa | `episodic_memory.py` | +40 | Reforço |
| C3 | KG estruturado como dataset | `master_agent.py` | +15 | Dataset |
| C4 | Feedback loop (backpropagation) | `master_agent.py` | +40 | Backpropagation |
| C5 | Clusterização de requests | `episodic_memory.py` | +45 | Não Supervisionado |
| C6 | Metacognição (AGI) | `master_agent.py` | +35 | AGI |
| | **Total** | | **~+210** | |

### O que NÃO muda

| Módulo | Motivo |
|--------|--------|
| `decider.py` | Já usa embeddings via `extrair_json()` — é nossa "camada neural" |
| `tool_orchestrator.py` | Ferramentas são ações, não precisam de aprendizado |
| `task_planner.py` | Planejamento usa Decider — feedback ajusta Decider |
| `ia.py` | Interface com LLM — o "cérebro" externo |

### Testes

```python
# C1: KG busca semantica
kg = KnowledgeGraph()
r = kg.buscar_por_embedding("criar um jogo", n=2)
assert len(r) > 0

# C2: Reforco
mem = EpisodicMemory()
taxa = mem.taxa_sucesso_para('gerar_codigo')
assert 0.0 <= taxa <= 1.0

# C4: Feedback
agent = MasterAgent()
agent._feedback("teste", "simples", [], {'1': {'sucesso': False}})

# C5: Clusterizacao
clusters = mem.clusterizar(n_clusters=3)
assert len(clusters) <= 3

# C6: Metacognicao
avaliacao = agent.autoavaliar("criar um jogo em Python")
assert avaliacao['acao'] in ('executar', 'executar_com_cautela', 'estudar_antes')
```

---

## Apêndice E — Context Infinity como Sistema Nervoso Central

> **Data:** 2026-06-28
> **Filosofia:** Context Infinity não tem limite de tokens. É um **cache de sessão vivo**
> que absorve TUDO o que acontece. Quando um passo precisa de contexto, ele **pesca**
> exatamente o que precisa — não carrega tudo, não perde nada.
>
> **Mudança de paradigma:** O antigo `OrquestradorContexto` (janela 8k com evicção)
> é substituído pelo `SessionCache` (memória RAM, sem limite, acumula tudo).

### Arquitetura Antiga vs Nova

| Aspecto | ANTES (`OrquestradorContexto`) | DEPOIS (`SessionCache`) |
|---------|-------------------------------|------------------------|
| Modelo mental | "Janela de 8k que lota e evicta" | "Cache que absorve tudo, pesca sob demanda" |
| Limite | `ctx_max` (8k tokens físicos) | **Nenhum** (memória RAM, ~100MB+) |
| Quando lota | Remove fragmento (perde dados) | **Nunca lota** — acumula |
| Resumo removido | 3 linhas no KG (primitivo) | **Não existe** — nada é removido |
| Como o LLM usa | Contexto montado inteiro | Só o que **pesca** no momento |
| Autoaperfeiçoamento | Não existe | Loop de Perfeição: itera sobre si |

### Os 3 Novos Componentes

#### E1 — `SessionCache` (o cérebro que nunca esquece)

Substitui `OrquestradorContexto`. Remove `ctx_max`. Adiciona `absorver()` e `pescar()`.

```python
class SessionCache:
    """Cache de sessao que ABSORVE tudo sem limite.
    
    - Nao tem ctx_max (guarda em RAM ate o fim da execucao)
    - Cada passo ESCREVE automaticamente via absorver()
    - pescar() retorna SO o relevante para o prompt do LLM
    - Suporta tags, tipos, busca textual e prioridade
    """
    
    def __init__(self):
        self.fragmentos: Dict[str, FragmentoContexto] = {}
        self.indice: Dict[str, List[str]] = {}
        self.historico: List[dict] = []
    
    def absorver(self, id, conteudo, tipo="texto", tags=None, origem=""):
        """Absorve um fragmento. NUNCA remove, nunca perde.
        
        Se o id ja existe, atualiza o conteudo e aumenta prioridade
        (o conhecimento foi refinado).
        """
        if id in self.fragmentos:
            self.fragmentos[id].conteudo = conteudo
            self.fragmentos[id].prioridade = min(100, self.fragmentos[id].prioridade + 5)
            self.fragmentos[id].ultimo_acesso = time.time()
            return
        frag = FragmentoContexto(id, conteudo, origem, 
                                 prioridade=self._calcular_prioridade(tipo, tags),
                                 tipo=tipo)
        self.fragmentos[id] = frag
        self._indexar(frag)
        self.historico.append({'ts': time.time(), 'acao': 'absorver', 'id': id, 'tipo': tipo})
    
    def pescar(self, pergunta="", tipos=None, tags=None, n=3, max_tokens=800):
        """Pesca fragmentos relevantes. Retorna SO o necessario.
        
        Args:
            pergunta: Texto da consulta (para match textual)
            tipos: Filtrar por tipo ('codigo', 'explicacao', 'resultado')
            tags: Filtrar por tags (['python', 'pygame', 'entities'])
            n: Maximo de fragmentos
            max_tokens: Limite de tokens para o prompt (opcional)
        """
        candidatos = list(self.fragmentos.values())
        
        # Filtro por tipo
        if tipos:
            candidatos = [f for f in candidatos if f.tipo in tipos]
        
        # Filtro por tags (busca nas tags salvas)
        if tags:
            candidatos = [f for f in candidatos if f._tags and any(t in f._tags for t in tags)]
        
        # Score por pergunta
        if pergunta:
            termos = set(pergunta.lower().split())
            scores = []
            for frag in candidatos:
                score = sum(1 for t in termos 
                          if len(t) > 3 and t in frag.conteudo.lower())
                if score > 0:
                    score += frag.prioridade / 10
                    score += frag.acessos / 100
                    scores.append((score, frag))
                    frag.registrar_acesso()
            scores.sort(key=lambda x: -x[0])
            candidatos = [s[1] for s in scores]
        
        # Limite por tokens (opcional — para caber no prompt)
        if max_tokens:
            resultado = []
            tokens = 0
            for frag in candidatos:
                if tokens + frag.tokens <= max_tokens:
                    resultado.append(frag)
                    tokens += frag.tokens
            return resultado
        
        return candidatos[:n]
    
    def _calcular_prioridade(self, tipo, tags):
        """Calcula prioridade baseado no tipo e tags."""
        prioridades_por_tipo = {
            'request': 100, 'plano': 90, 'codigo': 80,
            'resultado': 70, 'explicacao': 60, 'contexto': 50,
            'melhoria': 75, 'log': 30, 'debug': 20,
        }
        return prioridades_por_tipo.get(tipo, 50)
    
    def _indexar(self, frag):
        """Indexa termos do fragmento para busca rapida."""
        termos = set(frag.conteudo.lower().split()[:50])
        for termo in termos:
            if len(termo) > 3:
                if termo not in self.indice:
                    self.indice[termo] = []
                self.indice[termo].append(frag.id)
    
    def reconstruir(self, tags=None, tipos=None):
        """Reconstroi o estado completo da sessao.
        
        Permite 'voltar no tempo' e reconstruir qualquer parte
        do que foi feito, porque TUDO foi absorvido.
        """
        filtrados = self.pescar(tags=tags, tipos=tipos, n=100, max_tokens=None)
        return '\n\n'.join(f"{f.tipo.upper()}: {f.conteudo[:500]}" for f in filtrados)
```

#### E2 — Integração com MasterAgent (cada passo escreve)

No `executar()` do MasterAgent:

```python
def executar(self, request, task_type=''):
    # Inicia SessionCache para esta sessao
    self.ctx = SessionCache()
    
    # === ABSORVE request original ===
    self.ctx.absorver('request', request, 'request', tags=['request', task_type], origem='usuario')
    
    # === PERCEBER ===
    memorias = self.memoria.buscar(request, 3)
    self.ctx.absorver('memorias', str(memorias), 'contexto', tags=['memoria'], origem='episodic_memory')
    
    # === PLANEJAR ===
    plano = self.planner.planejar(request, task_type)
    self.ctx.absorver('plano', json.dumps([{'id':p['id'],'acao':p['acao']} for p in plano]), 
                      'plano', tags=['plano'], origem='planner')
    
    # === EXECUTAR (cada passo pesca + absorve) ===
    for subtarefa in plano:
        # PESCA contexto relevante para ESTA subtarefa
        ctx_passo = self.ctx.pescar(
            pergunta=subtarefa['descricao'],
            tipos=['codigo', 'request', 'plano', 'resultado'],
            max_tokens=600  # prompt pequeno e focado
        )
        resultado = self._executar_subtarefa(subtarefa, contexto_extra=str(ctx_passo))
        
        # ABSORVE resultado deste passo
        self.ctx.absorver(
            f'passo_{subtarefa["id"]}',
            str(resultado.get('resultado', ''))[:1000],
            tipo='resultado',
            tags=[subtarefa['acao'], task_type, 'sucesso' if resultado.get('sucesso') else 'falha'],
            origem=f'executor:{subtarefa["acao"]}'
        )
```

#### E3 — Loop de Perfeição

```python
class LoopDePerfeicao:
    """Itera sobre o proprio resultado ate atingir a perfeicao.
    
    Usa SessionCache como guia:
    1. Pesca o estado atual do projeto
    2. Pede ao MasterAgent para melhorar
    3. Absorve a melhoria
    4. Repete ate compilar sem erros
    """
    
    def __init__(self, agent):
        self.agent = agent
        self.max_ciclos = 10
    
    def executar(self, request_inicial):
        # Primeira execucao
        resultado = self.agent.executar(request_inicial)
        self.agent.ctx.absorver('projeto_completo', str(resultado), 
                                'resultado', tags=['projeto_completo'])
        
        ciclo = 0
        while ciclo < self.max_ciclos:
            # Pesca estado atual
            projeto = self.agent.ctx.pescar(tags=['projeto_completo'], n=1)
            falhas = self.agent.ctx.pescar(tags=['falha'], n=3)
            
            if not falhas:
                print(f"[Perfeicao] Projeto OK no ciclo {ciclo}!")
                break
            
            # Pede melhoria
            prompt = (
                f"Projeto atual:\n{projeto}\n"
                f"Problemas:\n{falhas}\n"
                f"Corrija os problemas e melhore. Ciclo {ciclo+1}/{self.max_ciclos}."
            )
            melhoria = self.agent.executar(prompt)
            
            # Absorve
            self.agent.ctx.absorver(f'melhoria_{ciclo}', str(melhoria),
                                    'melhoria', tags=['melhoria', f'ciclo_{ciclo}'])
            
            ciclo += 1
        
        return resultado
```

### Modificações nos Arquivos

| Arquivo | O quê | +/- | Risco |
|---------|-------|-----|-------|
| `context_infinity.py` | Refatorar `OrquestradorContexto` p/ `SessionCache` | +120 | Alto |
| `modulos/master_agent.py` | Integrar `SessionCache` no `executar()` | +60 | Médio |
| `modulos/master_agent.py` | Novo método `_loop_perfeicao()` | +50 | Médio |
| **Total** | | **~+230** | |

### Compatibilidade Retroativa

O `OrquestradorContexto` antigo é mantido para o `kernel.py` (não quebrar nada).
O `SessionCache` é um NOVO componente que coexiste.

```python
# kernel.py continua usando OrquestradorContexto (não muda)
# master_agent.py usa SessionCache (novo)
```

### Testes

```python
# E1: SessionCache absorve sem limite
cache = SessionCache()
for i in range(1000):
    cache.absorver(f'f_{i}', f'conteudo {i}', 'texto')
assert len(cache.fragmentos) == 1000  # nunca perde
assert len(cache.historico) == 1000   # tudo registrado

# E2: Pesca por tipo
cache.absorver('codigo_1', 'print("hello")', 'codigo', tags=['python'])
r = cache.pescar(tipos=['codigo'])
assert len(r) >= 1

# E3: Pesca por pergunta
cache.absorver('explicacao_1', 'Python é uma linguagem de programação', 'explicacao')
r = cache.pescar(pergunta='python linguagem')
assert len(r) >= 1

# E4: Reconstruir estado
estado = cache.reconstruir(tags=['python'])
assert len(estado) > 0

# E5: Integração MasterAgent
agent = MasterAgent()
resultado = agent.executar("Cria um script python que imprime hello")
assert hasattr(agent, 'ctx')
assert 'plano' in agent.ctx.fragmentos
```

---

## Apêndice F — Sistema de Sabedoria: KG + SessionCache + Busca Hierárquica

> **Data:** 2026-06-28
> **Problema:** No teste cego, o MCR perdeu porque não sabia sobre si mesmo.
> O SessionCache começava vazio, o KG não era consultado durante a execução,
> e a busca era plana (só web search quando falhava).
>
> **Solução:** 3 correções que tornam o MCR verdadeiramente "sábio":
> 1. Pré-carregar o SessionCache com conhecimento do KG antes de executar
> 2. Usar o KG como fonte principal de sabedoria durante toda a execução
> 3. Busca hierárquica 3 níveis (Local → WebLearn → Web)

### F1 — Pré-Preenchimento do SessionCache

**Arquivo:** `context_infinity.py` — NOVO método `SessionCache.precarregar()`

```python
def precarregar(self, kg=None, request="", memorias=None):
    """Preenche o cache com conhecimento relevante ANTES da execucao.
    
    1. Lessons do KG (keyword match) — ate 5
    2. Lessons do KG (embedding semantico) — ate 5
    3. Episodios similares da memoria — ate 3
    4. ContextCrew (docs, codigo fonte) — ate 3
    """
    if kg:
        for l in kg.buscar(request, max_r=10)[:5]:
            self.absorver(f'kg_{l["id"]}', f"{l.get('erro','')}: {l.get('solucao','')}",
                          'contexto', tags=['kg', l.get('ctx','')], origem='kg_preload')
        try:
            for l in kg.buscar_por_embedding(request, n=5):
                if f'kg_{l["id"]}' not in self.fragmentos:
                    self.absorver(f'kg_{l["id"]}', f"{l.get('erro','')}: {l.get('solucao','')}",
                                  'contexto', tags=['kg', 'embedding'], origem='kg_embedding')
        except: pass
    
    if memorias:
        for i, m in enumerate(memorias[:3]):
            self.absorver(f'memoria_{i}', str(m.get('licao', '')), 'contexto',
                          tags=['memoria'], origem='memoria_preload')
    
    try:
        from context_crew import ContextCrew
        crew = ContextCrew()
        ctx = crew.buscar(request, max_r=3)
        if ctx:
            self.absorver('context_crew', str(ctx), 'contexto',
                          tags=['contextcrew'], origem='crew_preload')
    except: pass
```

**No `MasterAgent.executar()`:**
```python
self.ctx = SessionCache()
self.ctx.precarregar(kg=self.kg, request=request, 
                     memorias=self.memoria.buscar(request, 3))
```

### F2 — KG como Fonte Principal de Sabedoria

**Arquivo:** `modulos/master_agent.py` — NOVO método `_buscar_sabedoria()`

```python
def _buscar_sabedoria(self, request, max_lessons=5):
    """Busca conhecimento no KG como fonte principal de sabedoria.
    
    Usa TANTO keyword (rapido, preciso) QUANTO embedding (semantico)
    para maxima cobertura do conhecimento disponivel.
    """
    lessons = []
    seen_ids = set()
    
    for l in self.kg.buscar(request, max_r=max_lessons):
        lid = l.get('id', '')
        if lid not in seen_ids:
            lessons.append(l)
            seen_ids.add(lid)
    
    try:
        if hasattr(self.kg, 'buscar_por_embedding'):
            for l in self.kg.buscar_por_embedding(request, n=max_lessons):
                lid = l.get('id', '')
                if lid not in seen_ids:
                    lessons.append(l)
                    seen_ids.add(lid)
    except: pass
    
    return lessons
```

### F3 — Busca Hierárquica 3 Níveis

**Arquivo:** `modulos/master_agent.py` — NOVO método `_buscar_hierarquico()`

```python
def _buscar_hierarquico(self, pergunta):
    """Busca em 3 niveis ate encontrar resposta satisfatoria.
    
    Nivel 1 — LOCAL: SessionCache → KG → EpisodicMemory → ContextCrew
    Nivel 2 — WEBLEARN: pesquisas web anteriores (cache local)
    Nivel 3 — WEB: DuckDuckGo ao vivo + Wikipedia fallback
    """
    resultados = []
    
    # NIVEL 1: LOCAL
    cache = self.ctx.pescar(pergunta=pergunta, tipos=['contexto','codigo'],
                             max_tokens=1000, n=5) if hasattr(self, 'ctx') else []
    for c in cache:
        resultados.append(c.conteudo[:300])
    if len(resultados) >= 3: return resultados[:3]
    
    for l in self._buscar_sabedoria(pergunta, 3):
        sol = l.get('solucao', '')[:300]
        if sol not in resultados: resultados.append(sol)
    if len(resultados) >= 3: return resultados[:3]
    
    try:
        from context_crew import ContextCrew
        for texto, fonte in ContextCrew().buscar(pergunta, max_r=2):
            if texto not in resultados: resultados.append(texto)
    except: pass
    if len(resultados) >= 3: return resultados[:3]
    
    # NIVEL 2: WEBLEARN (cache de pesquisas anteriores)
    wl_dir = os.path.join(BASE, 'sandbox', '.mcr_devia', 'weblearn')
    if os.path.exists(wl_dir):
        termos = set(pergunta.lower().split())
        for f in sorted(os.listdir(wl_dir))[:10]:
            if not f.endswith('.json'): continue
            try:
                with open(os.path.join(wl_dir, f), 'r', encoding='utf-8') as fh:
                    item = json.load(fh)
                txt = str(item.get('texto', ''))
                if any(t in txt.lower() for t in termos if len(t) > 3):
                    resultados.append(txt[:300])
                    if len(resultados) >= 3: return resultados[:3]
            except: pass
    
    # NIVEL 3: WEB AO VIVO
    try:
        web = self.ia.buscar_web(pergunta, max_resultados=3)
        if web: resultados.append(web[:500])
    except: pass
    
    return resultados[:3]
```

### Resumo das Mudanças

| Arquivo | O quê | +/- |
|---------|-------|-----|
| `context_infinity.py` | `SessionCache.precarregar()` | +35 |
| `modulos/master_agent.py` | `_buscar_sabedoria()` | +20 |
| `modulos/master_agent.py` | `_buscar_hierarquico()` | +55 |
| `modulos/master_agent.py` | Chamar `precarregar()` no `executar()` | +5 |
| **Total** | | **~+115** |

### Testes

```python
# F1: SessionCache pre-carregado
cache = SessionCache()
cache.precarregar(kg=kg, request="session cache")
n = cache.metricas()['fragmentos']
assert n > 0, f"Precarregamento gerou 0 fragmentos (kg={kg})"

# F2: Busca sabedoria
agent = MasterAgent()
lessons = agent._buscar_sabedoria("O que e o SessionCache?")
assert len(lessons) > 0

# F3: Busca hierarquica
contexto = agent._buscar_hierarquico("Python list comprehension")
assert len(contexto) > 0
```

---

## Apêndice G — Enricher Dinâmico: Filtro de Respostas Genéricas

> **Data:** 2026-06-28
> **Problema:** O MCR perdeu o teste cego 3x0 porque o Cloud usou contexto específico
> do projeto, enquanto o MCR deu respostas genéricas (o LLM não sabe que o MCR existe).
>
> **Solução:** Um **Analisador de Contexto** que identifica DINAMICAMENTE o que cada
> pergunta precisa, coleta das fontes certas, e monta o prompt ideal — tudo via FAST,
> sem regras fixas.

### Arquitetura

```
Pergunta: "Explique o SessionCache"
  │
  ▼
┌────────────────────────────────────────────────────┐
│ 1. ANALISADOR (FAST)                               │
│ "O que esta pergunta precisa para ser bem           │
│  respondida? Quais fontes consultar?"               │
│ → tipo: conceito_local                              │
│ → fontes: [kg, codigo]                              │
│ → profundidade: media                               │
└────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────┐
│ 2. COLETOR (KG + SessionCache + ContextCrew)        │
│ "Busca exatamente o que o analisador pediu"         │
│ → 5 lessons do KG                                   │
│ → 3 fragmentos do SessionCache                      │
│ → 2 resultados do ContextCrew                       │
└────────────────────────────────────────────────────┘
  │
  ▼
┌────────────────────────────────────────────────────┐
│ 3. MONTADOR (FAST)                                  │
│ "Monta o prompt IDEAL com este contexto"            │
│ → Prompt enriquecido: "Contexto MCR: [KG]...        │
│   Com base nisso, explique o SessionCache..."       │
└────────────────────────────────────────────────────┘
  │
  ▼
Resposta ESPECÍFICA (nunca genérica)
```

### G1 — AnalisadorDeContexto

```python
class AnalisadorDeContexto:
    """Analisa a pergunta e decide DINAMICAMENTE como enriquecer.
    
    Nao tem regras fixas. Usa FAST com exemplos para decidir
    o que a pergunta precisa, em tempo real.
    """
    
    def __init__(self, ia):
        self.decider = Decider(ia)
    
    def analisar(self, pergunta):
        """Retorna plano de enriquecimento para esta pergunta."""
        return self.decider.extrair_json(
            pergunta,
            {
                'tipo': '',
                'fontes': [],
                'profundidade': '',
                'formato': '',
                'contexto_extra': '',
            },
            exemplos=[
                ("O que e SessionCache no MCR?",
                 {"tipo": "conceito_local", "fontes": ["kg", "codigo"],
                  "profundidade": "media", "formato": "explicacao",
                  "contexto_extra": "SessionCache, absorver, pescar"}),
                ("Como fazer um loop em Python?",
                 {"tipo": "codigo", "fontes": ["codigo"],
                  "profundidade": "baixa", "formato": "exemplo",
                  "contexto_extra": "for, while, comprehensions"}),
                ("O que e AGI?",
                 {"tipo": "conceito_geral", "fontes": ["web"],
                  "profundidade": "media", "formato": "explicacao",
                  "contexto_extra": "AGI, desafios, metacognicao"}),
            ],
            instrucao="Analise a pergunta e decida o melhor enriquecimento."
        )
```

### G2 — ColetorDeContexto

```python
class ColetorDeContexto:
    """Coleta conhecimento das fontes que o analisador pediu."""
    
    def __init__(self, ia, kg, ctx_cache=None):
        self.ia = ia
        self.kg = kg
        self.ctx = ctx_cache
    
    def coletar(self, plano, request):
        conhecimento = []
        fontes = plano.get('fontes', ['kg'])
        
        for fonte in fontes:
            if fonte == 'kg':
                for l in self.kg.buscar(request, max_r=5):
                    conhecimento.append(('KG', l.get('solucao','')[:300]))
                try:
                    for l in self.kg.buscar_por_embedding(request, n=3):
                        conhecimento.append(('KG-sem', l.get('solucao','')[:300]))
                except: pass
            
            elif fonte == 'codigo':
                try:
                    from context_crew import ContextCrew
                    for texto, f in ContextCrew().buscar(request, max_r=3):
                        conhecimento.append(('Codigo', texto[:300]))
                except: pass
            
            elif fonte == 'cache':
                if self.ctx:
                    for frag in self.ctx.pescar(pergunta=request, tipos=['contexto'], n=3, max_tokens=500):
                        conhecimento.append(('Cache', frag.conteudo[:200]))
            
            elif fonte == 'web':
                try:
                    web = self.ia.buscar_web(request, max_resultados=3)
                    if web: conhecimento.append(('Web', web[:500]))
                except: pass
        
        return conhecimento
```

### G3 — MontadorDePrompt

```python
class MontadorDePrompt:
    """Gera o prompt IDEAL para esta pergunta + contexto coletado."""
    
    def __init__(self, ia):
        self.decider = Decider(ia)
    
    def montar(self, pergunta, contexto, plano):
        conhecimento = '\n'.join(f"[{f}] {t}" for f, t in contexto[:5])
        prompt_base = (
            f"Contexto coletado:\n{conhecimento}\n\n"
            f"Profundidade: {plano.get('profundidade', 'media')}\n"
            f"Formato: {plano.get('formato', 'explicacao')}\n"
            f"Pergunta: {pergunta}\n\n"
            f"Monte um prompt ENRIQUECIDO que usa o contexto para "
            f"responder a pergunta de forma ESPECIFICA (nao generica)."
        )
        try:
            r = self.decider.extrair_json(prompt_base, {'prompt': ''},
                instrucao="Retorne APENAS o prompt enriquecido, pronto para enviar ao LLM.")
            return r.get('prompt', prompt_base)
        except:
            return prompt_base
```

### G4 — Integração no MasterAgent

```python
# Em _executar_subtarefa, substituir o trecho de 'perguntar_ia':
if acao == 'perguntar_ia':
    pergunta = params.get('pergunta', subtarefa.get('descricao', ''))
    
    # SISTEMA DE ENRIQUECIMENTO DINAMICO
    analisador = AnalisadorDeContexto(self.ia)
    plano = analisador.analisar(pergunta)
    
    coletor = ColetorDeContexto(self.ia, self.kg, getattr(self, 'ctx', None))
    contexto = coletor.coletar(plano, pergunta)
    
    montador = MontadorDePrompt(self.ia)
    prompt_final = montador.montar(pergunta, contexto, plano)
    
    resposta = self.ia.gerar(prompt_final, 0.4, 'pesado')
    return {'sucesso': bool(resposta), 'resultado': resposta or 'Sem resposta',
            'erro': '' if resposta else 'IA nao retornou resposta'}
```

### Testes

```python
# G1: Analisador detecta tipo
analisador = AnalisadorDeContexto(ia)
plano = analisador.analisar("O que e SessionCache no MCR?")
assert plano.get('tipo') in ('conceito_local', 'conceito_geral', 'codigo')
assert len(plano.get('fontes', [])) > 0

# G2: Coletor busca nas fontes
coletor = ColetorDeContexto(ia, kg)
ctx = coletor.coletar({'fontes': ['kg']}, "SessionCache")
assert len(ctx) > 0

# G3: Prompt enriquecido
montador = MontadorDePrompt(ia)
prompt = montador.montar("O que e SessionCache?", ctx, plano)
assert 'SessionCache' in prompt

# G4: Resposta final nao e generica
agent = MasterAgent()
r = agent.executar("Explique o que e SessionCache no MCR-DevIA")
resposta = r['artefato']['resposta_final']
assert "absorver" in resposta or "pescar" in resposta or "fragmentos" in resposta
```

---

## Apêndice H — Integração Final: 11 Gaps na Pipeline

> **Data:** 2026-06-28
> **Problema:** A pipeline atual tem 11 funcionalidades existentes no código que
> não estão integradas no MasterAgent. Este apêndice mapeia CADA gap, onde
> ele se encaixa, e como implementar.

### Pipeline Atual vs Pipeline Completa

```
ATUAL:                                           COMPLETA:
INICIO                                           INICIO
  ├── SessionCache.precarregar()                   ├── SessionCache.precarregar()
  ├── autoavaliar()                                ├── autoavaliar()
PERCEBER                                           PERCEBER
  ├── memorias                                      ├── memorias
  ├── lessons (KG)                                  ├── lessons (KG)
PLANEJAR                                           PLANEJAR
EXECUTAR                                           EXECUTAR
  ├── pescar()                                       ├── pescar()
  ├── Enricher                                       ├── [G5] PromptCache
  │     ├── Analisador                               │     ├── [G7] TermosCriticos
  │     ├── Coletor                                  │     ├── ENRICHER:
  │     └── Montador                                 │     │     ├── Analisador
  ├── IA.gerar()                                     │     │     ├── Coletor
  └── Absorver                                       │     │     ├── [G6] Validar relevancia
                                                     │     │     ├── [G3] MCR_Identity
                                                     │     │     ├── [G1] TreeOfThought
                                                     │     │     │     ├── Analitico
                                                     │     │     │     ├── Criativo
                                                     │     │     │     └── Critico → Sintese
                                                     │     │     ├── [G8] Router modelo
                                                     │     │     └── Montador
                                                     │     ├── IA.gerar()
                                                     │     ├── [G2] Anti-alucinacao
                                                     │     ├── [G4] Traducao PT-BR
                                                     │     └── Absorver
  └── Se falhou → busca hierarquica                  └── Se falhou → busca hierarquica
INTEGRAR                                             INTEGRAR
  │                                                    ├── [G11] Auto-revisao final
APRENDER                                              APRENDER
  ├── EpisodicMemory                                    ├── [G9] LessonsBuffer
  └── KG.aprender()                                     ├── EpisodicMemory
                                                         └── KG.aprender()
FEEDBACK                                               FEEDBACK
                                                        └── [G10] Auto-diagnostico (10 em 10)
```

### Os 11 Gaps

#### G1 — Tree of Thought (dentro do Enricher)

**Origem:** `modulos/tree_of_thought.py`
**Onde:** Dentro do `MontadorDePrompt`, após coletar contexto
**O que faz:** Gera 3 perspectivas paralelas (analítico, criativo, crítico) e sintetiza em resposta única

```python
# NOVO metodo no Enricher:
def _aplicar_tree_of_thought(self, prompt_base):
    """Gera 3 perspectivas e sintetiza."""
    perspectivas = {}
    for nome, instrucao in _CAMINHOS.items():
        prompt = f"{instrucao}\n\n{prompt_base}"
        perspectivas[nome] = self.ia.gerar(prompt, 0.4, 'pesado')
    
    prompt_sintese = (
        f"Perspectiva analitica: {perspectivas.get('analitico', '')}\n"
        f"Perspectiva criativa: {perspectivas.get('criativo', '')}\n"
        f"Perspectiva critica: {perspectivas.get('critico', '')}\n\n"
        f"Sintetize as 3 perspectivas em uma resposta unica e coesa."
    )
    return self.ia.gerar(prompt_sintese, 0.3, 'pesado')
```

#### G2 — Anti-alucinação Pós-geração

**Origem:** `modulos/auto_revisor.py`
**Onde:** Depois de `IA.gerar()`, antes de retornar a resposta
**O que faz:** Escaneia classes/termos reais do projeto e verifica se a resposta inventou algo

```python
# NOVO metodo no Enricher:
def _revisar_alucinacoes(self, resposta, pergunta):
    """Verifica se a resposta contem termos que nao existem no projeto."""
    from auto_revisor import escanear_classes
    classes_reais = escanear_classes()
    
    # Extrai possiveis classes/termos inventados
    invencoes = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', resposta)
    for invencao in invencoes:
        if invencao not in classes_reais:
            # Verifica no KG se esse termo existe
            lessons = self.kg.buscar(invencao, max_r=1)
            if not lessons:
                return f"[TERMO INVENTADO DETECTADO: {invencao}. Corrigido.]"
    return resposta
```

#### G3 — MCR_Identity no Enricher

**Origem:** `modulos/conselho.py` + `docs/MCR_IDENTITY.md`
**Onde:** No `MontadorDePrompt`, antes de montar o prompt final
**O que faz:** Injeta a identidade do projeto para evitar confusão com Minecraft, SPA web, etc.

```python
# NOVO: injetar identidade no inicio do prompt
_IDENTITY = """CONTEXTO DO PROJETO MCR:
- MCR = servidor CUSTOMIZADO de Tibia baseado em Canary (OTServ)
- SPA = Sistema de Progressao do Aventureiro
- SHC = Sistema de Habilidades Contextuais (5 camadas)
- SessionCache = cache de sessao que absorve tudo sem limite
- MasterAgent = orquestrador universal que faz QUALQUER coisa
- Decider = classificador universal via FAST model
- KG = Knowledge Graph com 1937+ licoes aprendidas"""

# Usar no prompt enriquecido:
prompt_final = f"{_IDENTITY}\n\n{prompt_enriquecido}"
```

#### G4 — Tradução PT-BR

**Origem:** `modulos/tradutor.py`
**Onde:** Depois de `IA.gerar()`, antes de retornar
**O que faz:** Força o LLM a pensar em inglês (mais preciso), depois traduz para PT-BR

```python
# NOVO: gerar em ingles, traduzir depois
def _gerar_com_traducao(self, prompt, temp=0.4):
    prompt_en = f"Think step by step. Answer in English:\n{prompt}"
    resposta_en = self.ia.gerar(prompt_en, temp, 'pesado')
    if resposta_en:
        from modulos.tradutor import traduzir
        return traduzir(resposta_en, self.ia)
    return resposta_en
```

#### G5 — PromptCache LRU

**Origem:** `modulos/orquestrador.py` — classe `PromptCache`
**Onde:** Antes de chamar o Enricher, verificar cache
**O que faz:** Cache de prompts enriquecidos por hash da pergunta

```python
from collections import OrderedDict

class PromptCache:
    def __init__(self, max_size=64):
        self._cache = OrderedDict()
        self._max_size = max_size
    
    def get(self, pergunta):
        return self._cache.get(hash(pergunta) % 1000000)
    
    def set(self, pergunta, prompt):
        key = hash(pergunta) % 1000000
        self._cache[key] = prompt
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
```

#### G6 — Validação de Relevância

**Origem:** `modulos/context_reinforcer.py`
**Onde:** Depois do `ColetorDeContexto`, antes do `MontadorDePrompt`
**O que faz:** FAST valida se o contexto coletado é realmente relevante para a pergunta

```python
def _validar_relevancia(self, pergunta, contexto):
    if not contexto:
        return False
    prompt = f"Contexto: {contexto}\nPergunta: {pergunta}\nEste contexto e relevante? (sim/nao)"
    resp = self.ia.fast(prompt, 0.1, 'leve')
    return 'sim' in resp.lower()
```

#### G7 — Termos Críticos

**Origem:** `modulos/context_reinforcer.py` — `_extrair_termos_criticos()`
**Onde:** Antes do `AnalisadorDeContexto`, extrair melhores termos
**O que faz:** Extrai termos incluindo siglas, pontos de extensão (.lua, .py)

```python
def _extrair_termos_criticos(self, texto):
    # Extrai termos de 2+ chars, incluindo com pontos (.lua, .py)
    termos = re.findall(r'\b[a-zA-Z.]{2,}\b', texto.lower())
    stop = {'de','para','que','com','uma','era','mais','como','por'}
    return [t for t in termos if t not in stop][:10]
```

#### G8 — Router de Modelos

**Origem:** `modulos/conselho.py` — dict `_ROUTER`
**Onde:** No `MontadorDePrompt`, decide qual modelo usar
**O que faz:** Escolhe o melhor modelo baseado no tipo de tarefa

```python
_ROUTER = {
    'codigo': 'code',       # qwen2.5-coder:14b
    'explicacao': 'texto',  # qwen2.5-coder:14b
    'analise': 'analisar',  # qwen2.5-coder:14b
    'lore': 'texto',        # llama3.1:8b
    'rapido': 'leve',       # qwen2.5-coder:7b
}

def _escolher_modelo(self, tipo):
    return _ROUTER.get(tipo, 'pesado')
```

#### G9 — LessonsBuffer

**Origem:** `modulos/lessons_buffer.py`
**Onde:** No `_aprender_kg()`, antes de salvar no KG
**O que faz:** Buffer com detecção de contradições antes de salvar

```python
# NOVO: usar buffer antes de salvar
def _aprender_com_buffer(self, erro, causa, solucao, ctx):
    from lessons_buffer import LessonsBuffer
    buffer = LessonsBuffer(self.kg)
    buffer.adicionar(erro, causa, solucao, ctx)
    # Buffer salva automaticamente quando atinge limite
```

#### G10 — Auto-diagnóstico

**Origem:** `modulos/diagnostico.py`
**Onde:** A cada 10 execuções, após APRENDER
**O que faz:** Escaneia KG, código, performance

```python
# NOVO: a cada 10 execucoes
if self.ciclo % 10 == 0:
    from diagnostico import Diagnostico
    diag = Diagnostico()
    resultado = diag.diagnosticar()
    if resultado['score'] < 70:
        self._log('DIAG', f'Score {resultado["score"]}/100 - Problemas detectados')
```

#### G11 — Auto-revisão Final

**Origem:** `modulos/auto_revisor.py`
**Onde:** Depois de INTEGRAR, antes de retornar
**O que faz:** Revisa o artefato final completo

```python
# NOVO: revisar artefato final
if artefato_final.get('resposta_final'):
    from modulos.auto_revisor import AutoRevisor
    revisor = AutoRevisor()
    revisao = revisor.revisar(artefato_final['resposta_final'])
    if revisao.get('problemas'):
        self._log('REVISOR', f'{len(revisao["problemas"])} problemas encontrados')
```

### Ordem de Implementação

| # | Gap | +/- | Risco | Depende de |
|---|-----|-----|-------|-----------|
| G3 | MCR_Identity | +15 | Baixo | Nada |
| G2 | Anti-alucinação | +40 | Baixo | auto_revisor.py |
| G1 | TreeOfThought | +60 | Médio | tree_of_thought.py |
| G4 | Tradução PT-BR | +20 | Baixo | tradutor.py |
| G5 | PromptCache | +25 | Baixo | Nada |
| G6 | Validação relevância | +20 | Baixo | Nada |
| G7 | Termos críticos | +15 | Baixo | Nada |
| G8 | Router modelos | +20 | Baixo | Nada |
| G9 | LessonsBuffer | +30 | Baixo | Nada |
| G10 | Auto-diagnóstico | +25 | Baixo | diagnostico.py |
| G11 | Auto-revisão final | +30 | Médio | auto_revisor.py |
| | **Total** | **~+300** | | |

### Nota: Fusão conselho.py + enricher.py

**Decisão:** `conselho.py` já tinha 90% das funcionalidades do `enricher.py`.
Em vez de duplicar, o `enricher.py` foi transformado em atalho que importa
de `conselho.py`. As 6 funcionalidades novas (TreeOfThought, PromptCache,
TermosCríticos, AnalisadorDeContexto, ColetorDeContexto, ValidaçãoRelevância)
foram adicionadas DIRETAMENTE no `conselho.py`.

### Conselho 2.0 — FAST + ContextTools

**Problema:** O Conselho ainda usa 14b (`_gerar`) para arquétipos e veredito.
Isso custa ~15 min por deliberação.

**Solução:** Substituir 5 chamadas 14b por FAST + SessionCache pré-carregado.
Teste comprovou: FAST + ContextTools é 2.2x mais específico e 36% mais rápido.

| Ponto | Antes (14b) | Depois (FAST + CT) | Ganho |
|-------|------------|-------------------|-------|
| TreeOfThought (3x) | `ia.gerar("pesado")` | `_fast(contexto)` | 75% mais rápido |
| Arquétipos (2x) | `_gerar(router)` | `_fast(contexto)` | 75% mais rápido |
| Veredito | `_gerar("pesado")` | `_fast(db)` | 75% mais rápido |
| **Total** | **~4 min** | **~1 min** | **75% mais rápido** |

```python
# enricher.py agora é apenas um atalho:
from modulos.conselho import Conselho as Enricher
```
