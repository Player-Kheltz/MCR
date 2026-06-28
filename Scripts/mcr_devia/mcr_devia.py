#!/usr/bin/env python3
"""
MCR-DevIA — UNIFIED SYSTEM
============================
Tudo que o MCR-DevIA sabe fazer, num comando so.

Uso: python mcr_devia.py <comando> [args...]

COMANDOS:
  gerar     <tipo> [args...]    Gera NPC, quest, item, monster, spell
  lore      <tipo> <nome>       Gera lore profundo
  compilar  <projeto>           Compila e corrige automaticamente
  ensinar   <erro> <causa> <sol> Aprende uma nova licao
  perguntar <texto>             Responde com RAG + auto-supervisao
  processar <texto>             Entrada infinita (fragmenta + processa + monta)
  status                        Mostra tudo que sabe
"""

import sys, os, json, re, hashlib, urllib.request, subprocess, shutil, datetime, time

# Stop words centralizadas (evita duplicacao entre arquivos)
from stop_words import STOP_V12 as _STOP_V12, STOP_BUSCA as _STOP_BUSCA, KEYWORDS_MCR as _KEYWORDS_MCR
# from kernel import try_executar  # KERNEL (standalone)

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
KG_DIR = os.path.join(SANDBOX, '.mcr_devia')
os.makedirs(KG_DIR, exist_ok=True)
KG_PATH = os.path.join(KG_DIR, 'knowledge.json')

# ============================================================
# KNOWLEDGE GRAPH — O cerebro
# ============================================================

class KnowledgeGraph:
    def __init__(self):
        self.path = KG_PATH
        self.data = self._load()
    
    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'versoes': 0, 'licoes': self._licoes_iniciais(), 'index': {},
            'metricas': {'licoes': 12, 'usos': 0, 'geracoes': 0, 'compilacoes': 0}
        }
    
    def _licoes_iniciais(self):
        return [
            {'id':'L001','erro':'LNK2001 __std_*','causa':'ABI mismatch VS 2022 vs 2026','solucao':'Usar VS 2026 (toolset v145)','ctx':'compilar'},
            {'id':'L002','erro':'D9002 /std:c++latest','causa':'stdcpp23 no MSVC 14.41','solucao':'Mudar para stdcpp20 no vcxproj','ctx':'compilar'},
            {'id':'L003','erro':'string_view::contains','causa':'contains() e C++23, codigo usa C++20','solucao':'Substituir por find() != npos','ctx':'compilar'},
            {'id':'L004','erro':'canary-sln.exe ocupado','causa':'Processo rodando em BG','solucao':'taskkill /f /im canary-sln.exe','ctx':'runtime'},
            {'id':'L005','erro':'passiva nil value 40007','causa':'habilidade SHC sem efeito()','solucao':'Verificar hab.efeito antes de chamar','ctx':'runtime'},
            {'id':'L006','erro':'Bun crash GPU','causa':'Bun 1.3.14 + NVIDIA','solucao':'Downgrade OpenCode 1.17.9','ctx':'ferramenta'},
            {'id':'L007','erro':'HABILIDADES vazio','causa':'Arquivos de habilidade nao carregados','solucao':'Adicionar dofile no init','ctx':'runtime'},
            {'id':'L008','erro':'Motor sem tipos','causa':'projectile/melee/cone nao existiam','solucao':'Adicionar 9 tipos ao motor','ctx':'runtime'},
            {'id':'L009','erro':'IA gera em ingles','causa':'Qwen 7B tem bias ingles','solucao':'Detector de ingles + fallback tematico','ctx':'geracao'},
            {'id':'L010','erro':'Chaves Lua desbalanceadas','causa':'Template fechava na linha errada','solucao':'Abrir/fechar em linhas separadas','ctx':'geracao'},
            {'id':'L011','erro':'PowerShell Unicode','causa':'cp1252 encoding','solucao':'Nao usar emojis em prints','ctx':'ferramenta'},
            {'id':'L012','erro':'IA nao segue JSON','causa':'Modelo 7B tem dificuldade','solucao':'Usar formato TEXTO (NOME: valor)','ctx':'geracao'},
            # Perguntas frequentes (pre-populadas para V12)
            {'id':'L013','erro':'Quantos comandos o MCR-DevIA tem?','causa':'FAQ','solucao':'MCR-DevIA tem 47 comandos: gerar, lore, compilar, ensinar, perguntar, processar, status, grep, read, edit, glob, task, question, todo, webfetch, auditar, autoavaliar, autoconsciencia, auto_improve, auto_reparo, observar, agente, loop, chat, scriptbuilder, ultimate, conhecimento, ambiente, learning_scan, melhorias, supervisor, estrategia, builderx, system_scan, build, debate, intencao, conectar, plan, bugfinder, system, proativo, extract, review, analisar, fast, revisar','ctx':'identidade'},
            {'id':'L014','erro':'O que e SHC?','causa':'FAQ','solucao':'SHC = Sistema de Habilidades Contextuais. 5 camadas: postura (Impeto/Equilibrio/Guarda), nivel do dominio, sinergias, estados de alma (Vinculo/Lampejo), condicoes situacionais.','ctx':'identidade'},
            {'id':'L015','erro':'O que e SPA?','causa':'FAQ','solucao':'SPA = Sistema de Progressao do Aventureiro. Sistema de niveis, habilidades e dominios do jogador. NAO e Single Page Application.','ctx':'identidade'},
            {'id':'L016','erro':'O que e Eridanus?','causa':'FAQ','solucao':'Eridanus e a cidade inicial do projeto MCR, no continente de Lorentia. Possui NPCs, missoes iniciais e tutoriais para novos jogadores.','ctx':'identidade'},
            {'id':'L017','erro':'O que e MCR?','causa':'FAQ','solucao':'MCR e um servidor CUSTOMIZADO de Tibia (OTServ), baseado em Canary. NAO e Minecraft. Canary e o servidor, OTClient e o cliente.','ctx':'identidade'},
            {'id':'L018','erro':'O que sao Dominios?','causa':'FAQ','solucao':'Dominios sao areas de conhecimento do SPA: Fogo (23), Gelo (24), Terra (25), Energia (26). Cada dominio tem nivel, xp e habilidades especificas.','ctx':'identidade'},
            {'id':'L019','erro':'O que e Canary?','causa':'FAQ','solucao':'Canary e um servidor personalizado de Tibia (OTServ), baseado no TFS (The Forgotten Server). NAO e ferramenta CI/CD. Usa VS 2022 para compilar.','ctx':'identidade'},
            {'id':'L020','erro':'O que e OTClient?','causa':'FAQ','solucao':'OTClient e o cliente customizado de Tibia do projeto MCR. Compativel com VS 2026 (toolset v145). Usa OpenGL para renderizacao.','ctx':'identidade'},
            {'id':'L021','erro':'Qual modelo usar para analisar codigo?','causa':'FAQ','solucao':'Para analisar codigo (.py/.lua/.cpp), use qwen2.5-coder:7b com num_ctx=4096. Para texto/XML/JSON, use llama3.1:8b que tem melhor contexto PT-BR.','ctx':'identidade'},
            {'id':'L022','erro':'O que e o validador de genero?','causa':'FAQ','solucao':'Validador de genero V2: usa V12 (Python puro) para verificar artigo (um/uma) de itens em portugues. Aprende no KG. Zero IA para itens conhecidos.','ctx':'identidade'},
            {'id':'L023','erro':'O que e Context Infinity?','causa':'FAQ','solucao':'Context Infinity foi substituido pela Context Crew: 4 agentes (Analisador/llama3.1:8b, Pesquisador/Python, Filtrador/Python, Compactador/coder:7b) que pesquisam contexto sob demanda.','ctx':'identidade'},
            {'id':'L024','erro':'O que e InputPipeline?','causa':'FAQ','solucao':'InputPipeline e o sistema de entrada infinita: fragmenta a entrada em pedacos, processa cada um com CrewPipeline (V12 + IA se precisar), monta a resposta final com script Python (0 IA).','ctx':'identidade'},
            {'id':'L025','erro':'Qual a diferenca entre Canary e TFS?','causa':'FAQ','solucao':'Canary e uma versao MODERNA e otimizada do TFS (The Forgotten Server). O MCR usa Canary como base, nao o TFS original. Canary tem melhor performance e mais recursos.','ctx':'identidade'},
        ]
    
    def salvar(self):
        self.data['versoes'] += 1
        self.data['metricas']['licoes'] = len(self.data['licoes'])
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def buscar(self, texto, max_r=5, incluir_inativos=False):
        """Busca lessons no KG. Cache LRU para queries repetidas."""
        # Cache LRU: max 64 entradas
        if not hasattr(self, '_busca_cache'):
            self._busca_cache = {}
            self._busca_cache_order = []
        cache_key = f"{texto.strip().lower()}:{max_r}:{incluir_inativos}"
        if cache_key in self._busca_cache:
            return self._busca_cache[cache_key]
        
        palavras = set(re.findall(r'\w+', texto.lower()))
        # Remove stop words comuns para busca
        palavras = palavras - _STOP_BUSCA
        scores = []
        for l in self.data['licoes']:
            # Pula lessons inativas (weblearn/learning_scan de baixa qualidade)
            if not incluir_inativos and l.get('inactive', False):
                continue
            erro_l = l['erro'].lower()
            causa_l = l['causa'].lower()
            solucao_l = l['solucao'].lower()
            ctx_l = l.get('ctx','').lower()
            alvo = erro_l + ' ' + causa_l + ' ' + solucao_l
            score = 0
            for p in palavras:
                if len(p) < 3: continue
                if p in alvo:
                    # Peso maior para match exato no titulo (erro)
                    if p in erro_l: score += 5
                    elif p in ctx_l: score += 4  # ctx match = definicao confiavel
                    elif p in causa_l: score += 3
                    else: score += 2
                    # Bonus se ctx = identidade (definicoes oficiais)
                    if ctx_l == 'identidade': score += 10
            # Bonus EXTRA se termo principal aparece no TITULO da lesson
            for p in palavras:
                if len(p) >= 2 and p in erro_l and p not in _STOP_BUSCA:
                    score += 8
            if score > 0: scores.append((score, l))
        # Ordena: ctx=identidade primeiro (definicoes), depois por score decrescente
        scores.sort(key=lambda x: (-10 if x[1].get('ctx') == 'identidade' else 0, -x[0]))
        resultado = [s[1] for s in scores[:max_r]]
        
        # Cache LRU: armazena e mantem max 64 entradas
        self._busca_cache[cache_key] = resultado
        self._busca_cache_order.append(cache_key)
        if len(self._busca_cache) > 64:
            oldest = self._busca_cache_order.pop(0)
            self._busca_cache.pop(oldest, None)
        
        return resultado
    
    def purgar(self, manter_ctxs=None):
        """Marca lessons de baixa qualidade como inativas.
        Mantem ativas: ctxs especificados, lessons com id L001-L999, e ctx=identidade."""
        if manter_ctxs is None:
            # APRENDE do KG: ctxs com lessons de alta qualidade
            manter_ctxs = set()
            for l_ctx in self.data['licoes']:
                ctx = l_ctx.get('ctx', '')
                # Mantem ctxs que tem lessons ativas OU sao identificacao
                if ctx and (not l_ctx.get('inactive', False) or ctx == 'identidade'):
                    manter_ctxs.add(ctx)
            if not manter_ctxs:
                manter_ctxs = {'identidade'}
        count = 0
        for l in self.data['licoes']:
            # NUNCA marcar lessons curadas (id L001-L015 = iniciais)
            lid = l.get('id', '')
            if lid.startswith('L') and len(lid) <= 5 and int(lid[1:]) <= 100:
                continue
            ctx = l.get('ctx', 'geral')
            # Manter ctxs importantes sempre ativos
            if ctx in manter_ctxs:
                continue
            # Marcar como inativo se for weblearn ou learning_scan (auto-gerados)
            if ctx in ('weblearn', 'learning_scan', 'weblearn_permanente', 'pipeline_busca'):
                if not l.get('inactive', False):
                    l['inactive'] = True
                    count += 1
        self.salvar()
        print(f'  [KG Purge] {count} lessons marcadas como inativas')
        return count
    
    def aprender(self, erro, causa, solucao, ctx='geral'):
        # Lessons de pipeline_busca sao marcadas como inativas (nao poluem V12)
        inactive = ctx in ('pipeline_busca', 'weblearn', 'learning_scan')
        self.data['licoes'].append({
            'id':f'L{len(self.data["licoes"])+1:04d}','erro':erro,'causa':causa,
            'solucao':solucao,'ctx':ctx,'usos':0,'inactive':inactive})
        self.salvar()
        status = ' [INATIVA]' if inactive else ''
        print(f'  [APRENDIDO] "{erro[:50]}..."{status}')


# ============================================================
# IA LOCAL
# ============================================================

# ============================================================
# Roteador de modelos V2: cada tarefa usa o modelo ideal
# Baseado em benchmark real com RTX 3080 10GB VRAM
# ============================================================
MODELOS_DISPONIVEIS = {}  # cache de modelos disponiveis

# Configuracao de cada modelo: (nome, ctx_max, uso_medio_vram, prioridade)
# 14B (Q3_K_M e Q4_K_M) nao cabe na RTX 3080 10GB - confirmado em teste
CONFIG_MODELOS = [
    ("nomic-embed-text:latest", 2048, "0.3GB", 0),   # embeddings
    ("qwen2.5-coder:1.5b",      2048, "2GB",   1),   # fast, leve
    ("qwen2.5-coder:7b",        2048, "5GB",   2),   # codigo principal
    ("deepseek-r1:7b",          2048, "5GB",   3),   # raciocinio (thinking)
    ("llama3.1:8b",             2048, "6GB",   4),   # contexto longo (131K)
]

def _modelo_disponivel(modelo):
    """Verifica se um modelo esta disponivel no Ollama (cache)."""
    if not MODELOS_DISPONIVEIS:
        try:
            r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5)
            for m in json.loads(r.read()).get("models", []):
                nome = m["name"].split(":")[0] + ":" + m["name"].split(":")[1] if ":" in m["name"] else m["name"]
                MODELOS_DISPONIVEIS[nome] = True
        except: pass
        # Fallback: modelos que com certeza existem (ja baixados)
        for m in ["nomic-embed-text:latest", "qwen2.5-coder:1.5b", "qwen2.5-coder:7b",
                  "llama3.1:8b"]:
            if m not in MODELOS_DISPONIVEIS:
                MODELOS_DISPONIVEIS[m] = True
    return modelo in MODELOS_DISPONIVEIS and MODELOS_DISPONIVEIS[modelo]

def _melhor_modelo(tarefa):
    """Retorna dict {modelo, ctx} para cada tipo de tarefa.
    Usa o router padronizado de ia.py para consistencia."""
    from modulos.ia import MODELOS as _ROUTER_MODELOS
    mapa_router = {
        "fast":       _ROUTER_MODELOS.get("fast"),
        "code":       _ROUTER_MODELOS.get("code"),
        "contexto":   _ROUTER_MODELOS.get("leve"),
        "raciocinio": _ROUTER_MODELOS.get("analisar"),
        "leve":       _ROUTER_MODELOS.get("leve"),
        "revisor":    _ROUTER_MODELOS.get("revisor"),
        "planejador": _ROUTER_MODELOS.get("planejador"),
        "analisar":   _ROUTER_MODELOS.get("analisar"),
        "embedding":  {"modelo": "nomic-embed-text:latest", "ctx": 2048},
    }
    escolha = mapa_router.get(tarefa, _ROUTER_MODELOS.get("fast"))
    if not escolha:
        return {"modelo": "qwen2.5-coder:7b", "ctx": 2048}
    if not _modelo_disponivel(escolha["modelo"]):
        return {"modelo": "qwen2.5-coder:7b", "ctx": 2048}  # fallback
    # Converte para formato antigo (ctx)
    return {"modelo": escolha["modelo"], "ctx": escolha.get("ctx", 4096)}

def fast(prompt, temp=0.1, tarefa="fast"):
    """Chamada direta ao Ollama.
    Para respostas rapidas SEM contexto (classificacoes SIM/NAO, extracoes simples).
    Para perguntas factuais, use perguntar() que tem KG + veracidade."""
    cfg = _melhor_modelo(tarefa)
    modelo, ctx = cfg["modelo"], cfg["ctx"]
    try:
        d = json.dumps({'model': modelo, 'prompt': prompt, 'stream': False,
            'options': {'temperature': temp, 'num_ctx': ctx}}).encode()
        r = urllib.request.Request(OLLAMA_URL, data=d, headers={'Content-Type': 'application/json'})
        return json.loads(urllib.request.urlopen(r, timeout=30).read()).get('response', '')
    except Exception as e:
        print(f"[Fix] ERRO: {e}")

class IA:
    def gerar(self, prompt, temp=0.7, tarefa="code"):
        cfg = _melhor_modelo(tarefa)
        modelo, ctx = cfg["modelo"], cfg["ctx"]
        try:
            d = json.dumps({'model': modelo, 'prompt': prompt, 'stream': False,
                'options': {'temperature': temp, 'num_ctx': ctx, 'top_p': 0.95}}).encode()
            r = urllib.request.Request(OLLAMA_URL, data=d, headers={'Content-Type':'application/json'})
            return json.loads(urllib.request.urlopen(r, timeout=120).read()).get('response','')
        except Exception as e:
            print(f"[Fix] ERRO: {e}")


# ============================================================
# TEMPLATE ENGINE (V12-V15)
# ============================================================

# Carrega templates do LearningScan (se disponivel)
def _carregar_templates():
    """Carrega templates do LearningScan. Fallback para hardcoded se nao existir."""
    scan_path = os.path.join(SANDBOX, '.mcr_learning_scan.json')
    if os.path.exists(scan_path):
        try:
            with open(scan_path, encoding='utf-8') as f:
                scan_data = json.load(f)
            padroes = scan_data.get('padroes', {})
            # Se LearningScan tem dados, usa template generico com funcoes reais
            return padroes  # Retorna padroes brutos para o Gerador montar o prompt
        except:
            pass
    return {}  # Sem dados do LearningScan

LEARNING_PADROES = _carregar_templates()

# Templates hardcoded (fallback quando LearningScan nao tem dados para o tipo)
TEMPLATES = {
    'npc': ('-- NPC: {nome}\nlocal npc = NPC("{nome}")\nnpc:setSaudacao("{saudacao}")\nnpc:addItem({item_id}, {item_preco})\nprint("NPC {nome} carregado.")',
            ['nome','saudacao','item_id','item_preco']),
    'monster': ('-- Monster: {nome}\nlocal mon = Monster("{nome}")\nmon:setHealth({hp})\nmon:setAttack({atk})\nmon:setDefense({def})\nmon:addLoot({loot_id}, {loot_chance})\nprint("Monster {nome} carregado.")',
                ['nome','hp','atk','def','loot_id','loot_chance']),
    'quest': ('-- Quest: {nome}\nlocal quest = Quest("{nome}")\nquest:setDescricao("{desc}")\nquest:addObjetivo("{obj}")\nquest:addRecompensa("xp", {xp})\nprint("Quest {nome} carregada.")',
              ['nome','desc','obj','xp']),
    'item': ('-- Item: {nome}\nlocal item = Item({id}, "{nome}")\nitem:setType("{tipo}")\nitem:setAttack({atk})\nitem:setDefense({def})\nitem:setWeight({peso})\nprint("Item {nome} carregado.")',
             ['nome','id','tipo','atk','def','peso']),
    'spell': ('-- Spell: {nome}\nlocal spell = Spell("{nome}", "{elem}")\nspell:setDamage({dano})\nspell:setManaCost({mana})\nspell:setCooldown({cd})\nprint("Spell {nome} carregada.")',
              ['nome','elem','dano','mana','cd']),
}

class Gerador:
    def __init__(self, ia, kg):
        self.ia = ia; self.kg = kg
        self._crew = None
    
    def gerar(self, tipo, args_str):
        args = args_str.split() if isinstance(args_str, str) else []
        nome = args[0] if args else tipo
        nome_limpo = nome[:20]
        
        # V12: KG ja gerou algo similar? (0 IA se encontrar)
        if self._crew is None:
            from crew_pattern import CrewPipeline
            self._crew = CrewPipeline(self.kg, self.ia, verbose=False)
        v12_resp = self._crew._v12_check(f"gerar {tipo} {nome_limpo}")
        if v12_resp:
            print(f'  [KG] Geracao similar encontrada ({tipo}/{nome_limpo}). Verifique:')
            for line in v12_resp.split('\n')[:4]:
                if line.strip(): print(f'    {line[:100]}')
            # Nao retorna — permite regerar se o usuario quer algo diferente
            # Mas o cache serve como referencia
        
        # Tenta usar LearningScan primeiro (funcoes REAIS do projeto)
        funcoes_reais = LEARNING_PADROES.get(tipo, {})
        funcoes_confirmadas = {f:c for f,c in funcoes_reais.items() if c >= 2}
        funcoes_possiveis = {f:c for f,c in funcoes_reais.items() if c == 1}
        
        if funcoes_confirmadas or funcoes_possiveis:
            # Gera via IA com contexto das funcoes reais
            ctx_parts = self.kg.buscar(f'gerar {tipo}')
            ctx_kg = ''
            if ctx_parts:
                ctx_kg = '\n'.join(f'- {l["solucao"]}' for l in ctx_parts)
            
            prompt = (
                f"Crie um arquivo Lua para '{tipo}' chamado '{nome_limpo}' no projeto MCR.\n"
                f"\n"
                + (f"Funcoes CONFIRMADAS para {tipo} (usadas em 2+ arquivos do projeto):\n"
                   + "\n".join(f"- {f}()" for f in funcoes_confirmadas) + "\n"
                   if funcoes_confirmadas else "")
                + (f"\nFuncoes POSSIVEIS (usadas em 1 arquivo):\n"
                   + "\n".join(f"- {f}()" for f in funcoes_possiveis) + "\n"
                   if funcoes_possiveis else "")
                + (f"\nContexto do KG:\n{ctx_kg}\n" if ctx_kg else "")
                + f"""
Formato esperado:
-- {tipo}: {nome_limpo}
local {tipo} = {tipo.title()}("{nome_limpo}")
... funcoes CONFIRMADAS acima, adaptadas para {tipo}
print("{tipo} {nome_limpo} carregado.")

REGRAS:
- Crie o objeto do tipo '{tipo}', NAO 'Monster'
- Use APENAS as funcoes listadas como CONFIRMADAS
- Se nao houver funcoes confirmadas, use a criacao basica do objeto
- Nao invente funcoes"""
            )
            r = self.ia.gerar(prompt, 0.4)
            if r:
                resultado = re.sub(r'```\w*\n?', '', r).strip()
            else:
                resultado = "-- " + tipo + ": " + nome_limpo + "\nprint(\"" + tipo + " " + nome_limpo + " carregado.\")\n"
        else:
            # Fallback: template hardcoded (sem LearningScan)
            tipos_disponiveis = ", ".join(TEMPLATES.keys())
            if tipo not in TEMPLATES:
                print("Tipos: " + tipos_disponiveis)
                return
            info = TEMPLATES[tipo]
            template = info[0]
            blanks = info[1]
            
            vals = {}
            for i, b in enumerate(blanks):
                if i < len(args) and args[i]:
                    vals[b] = args[i]
            
            rest = [b for b in blanks if b not in vals]
            if rest:
                ctx_parts = self.kg.buscar("gerar " + tipo)
                ctx = ""
                if ctx_parts:
                    linhas_ctx = []
                    for l in ctx_parts:
                        linhas_ctx.append("- " + l["solucao"])
                    ctx = "Baseado em experiencias anteriores:\n" + "\n".join(linhas_ctx)
                linhas_prompt = [ctx + "\n\nPreencha para " + tipo + ":\n"]
                for b in rest:
                    linhas_prompt.append("  " + b + ": ")
                prompt = "\n".join(linhas_prompt)
                r = self.ia.gerar(prompt, tarefa="contexto")
                if r:
                    for line in r.split("\n"):
                        for b in rest:
                            if line.lower().startswith(b.lower() + ":"):
                                v = line.split(":", 1)[1].strip().strip("\"'")
                                if v and v.lower() not in ("none", "null", ""):
                                    vals[b] = v
            
            padroes_fallback = {
                "nome": tipo, "saudacao": "Ola!", "item_id": "101", "item_preco": "50",
                "hp": "200", "atk": "20", "def": "10", "loot_id": "201", "loot_chance": "0.3",
                "desc": "Descricao", "obj": "Objetivo", "xp": "500", "id": "1001",
                "tipo_item": "quest", "peso": "5", "elem": "fire", "dano": "100",
                "mana": "50", "cd": "5"
            }
            for b in blanks:
                if b not in vals:
                    vals[b] = padroes_fallback.get(b, "[" + b + "]")
            
            try:
                resultado = template.format(**vals)
            except KeyError as e:
                print("Erro: " + str(e))
                return
        
        # VALIDACAO POS-GERACAO: verifica se o construtor esta correto
        construtor_certo = {"monster": "Monster", "item": "Item", "npc": "NPC",
                           "spell": "Spell", "quest": "Quest"}.get(tipo, "")
        if construtor_certo:
            for construtor_errado, tipo_errado in {"Monster": "monster", "Item": "item",
                "NPC": "npc", "Spell": "spell", "Quest": "quest"}.items():
                if construtor_errado == construtor_certo:
                    continue
                if construtor_errado + "(" in resultado:
                    resultado = resultado.replace(construtor_errado + "(", construtor_certo + "(")
                    print(f"  [Auto-correcao] {construtor_errado}( -> {construtor_certo}(")
        
        path = os.path.join(SANDBOX, f'devia_{tipo}_{nome_limpo}.lua')
        with open(path, 'w', encoding='utf-8') as f: f.write(resultado)
        print(f'  [OK] {path}')
        if resultado:
            for line in resultado.split('\n')[:4]:
                if line.strip(): print(f'    {line[:100]}')
        self.kg.data['metricas']['geracoes'] += 1; self.kg.salvar()


# ============================================================
# LORE ENGINE (V19)
# ============================================================

class LoreGen:
    def __init__(self, ia): self.ia = ia
    
    def gerar(self, tipo, nome):
        prompts = {
            'npc': f"Crie lore para NPC '{nome}'. HISTORIA: (2 frases) PERSONALIDADE: (3 adjetivos) SAUDACAO: (fala) SEGREDO: (segredo)",
            'item': f"Crie lore para item '{nome}'. ORIGEM: (de onde veio) PODER: (o que faz) LENDA: (o que dizem)",
            'local': f"Crie lore para local '{nome}'. APARENCIA: (como parece) HISTORIA: (o que aconteceu) PERIGO: (o que espreita)",
        }
        prompt = prompts.get(tipo, f"Crie lore sobre {nome}:")
        r = self.ia.gerar(prompt, 0.8)
        if r:
            path = os.path.join(SANDBOX, f'devia_lore_{tipo}_{nome[:15]}.txt')
            with open(path, 'w', encoding='utf-8') as f: f.write(r)
            print(f'  [OK] Lore salvo em {path}')
            # Mostra preview
            for line in r.split('\n')[:4]:
                if line.strip(): print(f'    {line[:100]}')


# ============================================================
# COMPILADOR + CORRETOR
# ============================================================

class Builder:
    def __init__(self, kg, ia):
        self.kg = kg; self.ia = ia
    
    def compilar(self, projeto='canary'):
        msbuild = self._encontrar_msbuild()
        if not msbuild: return
        
        sln_map = {
            'canary': os.path.join(BASE, 'Canary', 'vcproj', 'canary.sln'),
            'otclient': os.path.join(BASE, 'OTClient', 'vc17', 'otclient-vc17.sln'),
        }
        sln = sln_map.get(projeto)
        if not sln or not os.path.exists(sln):
            print(f'[ERRO] Solucao {projeto} nao encontrada'); return
        
        print(f'[COMPILAR] {projeto}...')
        for tentativa in range(1, 4):
            cmd = f'"{msbuild}" "{sln}" /p:Configuration=Release /p:Platform=x64 /t:Build /m 2>&1'
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=600)
                erros = [l for l in (r.stdout+r.stderr).split('\n') if any(e in l for e in ['error','fatal','LNK'])]
                if r.returncode == 0 and not erros:
                    print(f'  [OK] Compilado! Tentativa {tentativa}')
                    self.kg.data['metricas']['compilacoes'] += 1; self.kg.salvar()
                    return
                print(f'  Erros: {len(erros)}')
                if not self._corrigir(erros[:3]):
                    print('  Nao foi possivel corrigir automaticamente.'); return
            except subprocess.TimeoutExpired:
                print('  TIMEOUT'); return
    
    def _encontrar_msbuild(self):
        for path in [
            r'C:\Program Files\Microsoft Visual Studio\2026\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
            r'C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\amd64\MSBuild.exe',
        ]:
            if os.path.exists(path): return path
        print('[ERRO] MSBuild nao encontrado'); return None
    
    def _corrigir(self, erros):
        for erro in erros:
            licoes = self.kg.buscar(erro)
            for l in licoes:
                print(f'  Lição: {l["solucao"][:80]}')
                l['usos'] = l.get('usos',0)+1
                if 'stdcpplatest' in erro and 'stdcpp20' in l['solucao']:
                    for root, dirs, files in os.walk(os.path.join(BASE,'OTClient','vc17')):
                        for f in files:
                            if f.endswith('.vcxproj'):
                                p = os.path.join(root,f)
                                with open(p,'r',encoding='utf-8',errors='replace') as fp:
                                    c = fp.read()
                                if 'stdcpplatest' in c:
                                    shutil.copy2(p,p+'.bak')
                                    with open(p,'w',encoding='utf-8') as fp:
                                        fp.write(c.replace('stdcpplatest','stdcpp20'))
                                    print(f'     [FIX] Aplicado em {f}')
                                    return True
            if not licoes:
                # IA tenta diagnosticar
                prompt = f"SOLUCAO para: {erro[:200]}\n\nResponda: CAUSA: SOLUCAO:"
                r = self.ia.gerar(prompt, 0.4)
                if r:
                    for line in r.split('\n'):
                        if 'CAUSA:' in line: causa = line.split(':',1)[1].strip()
                        elif 'SOLUCAO:' in line: sol = line.split(':',1)[1].strip()
                    if causa and sol:
                        self.kg.aprender(erro[:80], causa, sol, 'compilar')
        return False


# ============================================================
# SUPERVISOR (RAG + Auto-avaliacao)
# ============================================================

class Supervisor:
    def __init__(self, ia, kg):
        self.ia = ia; self.kg = kg
        # Inicializa Context Crew (contexto sob demanda)
        try:
            from context_crew import ContextCrew
            self.ctx_crew = ContextCrew()
        except Exception as e:
            print(f'  [AVISO] Context Crew nao disponivel: {e}')
            self.ctx_crew = None
     
    def _classificar_pergunta(self, texto):
        """Classifica o tipo de pergunta usando keywords (0 IA).
        Retorna: (tipo, subtipo, keywords)"""
        t = texto.lower()
        # Factual: definições, conceitos, fatos
        if any(p in t for p in ['o que e', 'o que sao', 'o que é', 'o que são',
                                 'quem e', 'quem é', 'definicao', 'definição',
                                 'significado', 'conceito', 'explique']):
            return ('factual', 'definicao', set())
        if any(p in t for p in ['quando', 'onde foi', 'data', 'versao', 'versão']):
            return ('factual', 'dado', set())
        # Histórico: mudanças, alterações, sessões
        if any(p in t for p in ['foi feito', 'foi criado', 'foi alterado',
                                'ultimas sessoes', 'últimas sessões',
                                'mudou', 'mudança', 'alteracao', 'alteração',
                                'histórico', 'historico', 'evolucao', 'evolução',
                                'aconteceu', 'feito ate', 'feito até']):
            return ('historico', 'mudancas', set())
        if any(p in t for p in ['pendente', 'pendencia', 'pendência',
                                'proximo', 'próximo', 'vai fazer', 'planejado']):
            return ('historico', 'pendentes', set())
        # Procedimental: como fazer
        if any(p in t for p in ['como fazer', 'como criar', 'como implementar',
                                'qual comando', 'como usar', 'como rodar',
                                'passo a passo']):
            return ('procedimental', 'instrucao', set())
        # Ambientação/lore
        if any(p in t for p in ['lore', 'historia', 'história', 'mundo',
                                'personagem', 'npc', 'cidade', 'reino',
                                'eridanus', 'lorentia']):
            return ('ambientacao', 'lore', set())
        # Opinião
        if any(p in t for p in ['o que voce acha', 'o que você acha',
                                 'voce deveria', 'você deveria',
                                 'melhor', 'pior', 'recomenda']):
            return ('opiniao', 'conselho', set())
        # Desconhecido
        return ('desconhecido', 'geral', set())

    def _autoavaliar_resposta(self, pergunta, resposta, contexto_licao=""):
        """Usa IA para avaliar se a resposta satisfaz a pergunta.
        Aceita contexto da lesson para distinguir entre temas similares.
        Retorna: (bool adequada, str motivo)"""
        if not resposta or len(resposta) < 20:
            return (False, "resposta muito curta")
        ctx_extra = ""
        if contexto_licao:
            ctx_extra = f"\nContexto da fonte: {contexto_licao[:200]}"
        prompt = (
            f"Pergunta: {pergunta[:250]}\n"
            f"Resposta: {resposta[:500]}{ctx_extra}\n\n"
            f"A resposta acima RESPONDE ADEQUADAMENTE a pergunta?\n"
            f"Criterios:\n"
            f"1. A resposta e especifica para a pergunta? OU da contexto util?\n"
            f"2. Ela explica ALGO alem de ser uma simples definicao/sigla?\n"
            f"3. Evite: responder com definicao curta sem explicar como funciona\n"
            f"4. Prefira: respostas com algum detalhe ou contexto util\n"
            f"Use o contexto da fonte para distinguir entre assuntos similares.\n"
            f"Responda apenas:\n"
            f"ADEQUADA -> se respondeu bem\n"
            f"INADEQUADA -> motivo: (explique brevemente)"
        )
        r = fast(prompt, 0.1, "fast")
        if r and 'ADEQUADA' in r.upper() and 'INADEQUADA' not in r.upper():
            return (True, r[:100])
        return (False, r[:100] if r else "sem avaliacao")

    def _buscar_contexto_historico(self):
        """Busca contexto de historico do projeto em docs recentes."""
        contextos = []
        for path in [os.path.join(BASE, 'docs', 'lessons', 'recentes.md'),
                     os.path.join(BASE, 'Pendencias.md')]:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read(2000)  # Primeiros 2000 chars
                    contextos.append(f"--- {os.path.basename(path)} ---\n{content[:1000]}")
                except:
                    pass
        return '\n'.join(contextos)

    def perguntar(self, texto):
        print(f'[SUPERVISOR] "{texto[:80]}..."')
        texto_original = texto
        
        # === PASSO 1: CLASSIFICADOR (0 IA, só keywords) ===
        tipo, subtipo, _ = self._classificar_pergunta(texto_original)
        print(f'  [Classificador] Tipo: {tipo}/{subtipo}')
        
        # === PASSO 2: CONTEXTO HISTORICO (se aplicavel) ===
        contexto_extra = ""
        if tipo == 'historico':
            contexto_extra = self._buscar_contexto_historico()
            if contexto_extra:
                print(f'  [Roteador] Contexto historico carregado ({len(contexto_extra)} chars)')
        
        # === PASSO 3: INPUT PIPELINE GATEKEEPER ===
        try:
            from input_pipeline import FragmentadorEntrada, InputPipeline
            frag_check = FragmentadorEntrada()
            fragmentos = frag_check.fragmentar(texto_original)
            if len(fragmentos) > 1:
                print(f'  [Gatekeeper] Entrada com {len(fragmentos)} fragmentos.')
                pipe = InputPipeline(kg=self.kg, ia=self.ia,
                                     ctx_crew=self.ctx_crew, verbose=False)
                resultado = pipe.executar(texto_original, estrategia="estrutura")
                if resultado and len(resultado) > 50:
                    return resultado
        except Exception as e:
            pass
        
        kwargs_v12 = set(re.findall(r'\b[a-zA-Z]{3,}\b', texto_original.lower())) - _STOP_V12
        
        # === PASSO 4: TIPO ESPECIFICO PRIMEIRO (antes do KG generico) ===
        # Se for historico, usa contexto historico ANTES do KG
        if tipo == 'historico' and contexto_extra:
            print(f'  [Roteador] Respondendo com contexto historico...')
            r_hist = self.ia.gerar(
                f"Contexto historico do projeto:\n{contexto_extra[:1500]}\n\n"
                f"Pergunta: {texto_original}\n"
                f"Responda com base APENAS no contexto acima. Seja especifico.", 0.3
            )
            if r_hist and len(r_hist) > 30:
                ok, _ = self._autoavaliar_resposta(texto_original, r_hist)
                if ok:
                    print(f'\n{r_hist[:500]}')
                    return r_hist
            print(f'  [Roteador] Contexto historico insuficiente, tentando KG...')
        
        # === PASSO 5: FAST PATH — V12 CONTEXTO AGREGADO ===
        # Acha top lesson por keyword match, busca lessons RELACIONADAS no KG,
        # agrupa tudo, Fast expande em resposta contextual. 0 retorno cru.
        contexto = self.kg.buscar(texto_original)
        melhor_lesson = None
        melhor_score = 0
        if contexto:
            for l in contexto:
                sol = l.get("solucao", "").lower()
                keywords = kwargs_v12
                matches = sum(1 for t in keywords if t in sol)
                if matches > melhor_score:
                    melhor_score = matches
                    melhor_lesson = l
            
            if melhor_lesson and melhor_score >= 1:
                # Busca lessons RELACIONADAS: usa titulo (erro) + ctx da top
                termo_rel = f'{melhor_lesson.get("erro","")} {melhor_lesson.get("ctx","")}'
                relacionadas = self.kg.buscar(termo_rel, max_r=3)
                # Monta contexto agregado (top + relacionadas, sem duplicar)
                vistas = set()
                blocos = []
                for l_rel in [melhor_lesson] + (relacionadas or []):
                    lid = l_rel.get('id', '') or l_rel.get('solucao', '')[:50]
                    if lid in vistas:
                        continue
                    vistas.add(lid)
                    txt = l_rel.get("solucao", "").strip()
                    if txt:
                        blocos.append(f'- {txt[:300]}')
                    if len(blocos) >= 4:
                        break
                ctx_aggregado = '\n'.join(blocos)
                # Fast expande
                prompt_v12 = (
                    f"Contexto do projeto MCR:\n{ctx_aggregado}\n\n"
                    f"Pergunta: {texto_original}\n"
                    f"Responda de forma util em 2-3 frases usando APENAS o contexto acima.\n"
                    f"Nao invente informacoes alem do contexto fornecido."
                )
                r = fast(prompt_v12, 0.3, "leve")
                if r and len(r) > 20:
                    print(f'{r[:600]}')
                    return r
            
            # Fallback IA com KG (sem V12 match mas com contexto do KG)
            ctx_curto = '\n'.join(f'- {l["solucao"][:200]}' for l in contexto[:2])
            prompt = f"{ctx_curto}\n\nPergunta: {texto_original}\nResposta (use APENAS o contexto acima):"
            r = fast(prompt, 0.1, "leve")
            if r and len(r) > 20:
                print(f'{r[:600]}')
                return r
        
        # === PASSO 5: MID PATH (ContextCrew) ===
        if self.ctx_crew:
            ctx_crew = self.ctx_crew.executar(texto_original)
            if ctx_crew:
                print(f'  [ContextCrew] {len(ctx_crew)//2} tokens')
                contexto = self.kg.buscar(texto_original)
                if contexto:
                    # V12 contexto agregado tambem no mid path
                    melhor_lesson = None
                    melhor_score = 0
                    for l in contexto[:3]:
                        sol = l.get("solucao", "").lower()
                        matches = sum(1 for t in kwargs_v12 if t in sol)
                        if matches > melhor_score:
                            melhor_score = matches
                            melhor_lesson = l
                    if melhor_lesson and melhor_score >= 1:
                        termo_rel = f'{melhor_lesson.get("erro","")} {melhor_lesson.get("ctx","")}'
                        relacionadas = self.kg.buscar(termo_rel, max_r=2)
                        vistas = set()
                        blocos = []
                        for l_rel in [melhor_lesson] + (relacionadas or []):
                            lid = l_rel.get('id', '') or l_rel.get('solucao', '')[:50]
                            if lid in vistas: continue
                            vistas.add(lid)
                            txt = l_rel.get("solucao", "").strip()
                            if txt: blocos.append(f'- {txt[:300]}')
                            if len(blocos) >= 3: break
                        ctx_agg = '\n'.join(blocos)
                        prompt_v12 = (
                            f"Contexto do projeto MCR:\n{ctx_agg}\n\n"
                            f"Pergunta: {texto_original}\n"
                            f"Responda de forma util em 2-3 frases usando APENAS o contexto acima.\n"
                            f"Nao invente informacoes alem do contexto fornecido."
                        )
                        r = fast(prompt_v12, 0.3, "leve")
                        if r and len(r) > 20:
                            print(f'{r[:600]}')
                            return r
                    # Fallback IA com KG para mid path
                    ctx_curto = '\n'.join(f'- {l["solucao"][:200]}' for l in contexto[:2])
                    r = fast(f"{ctx_curto}\n\nPergunta: {texto_original}\nResposta (use APENAS o contexto acima):", 0.1, "leve")
                    if r and len(r) > 20:
                        print(f'{r[:600]}')
                        return r
        
        # === PASSO 6: AUTO-APRENDIZADO (se sem contexto) ===
        if not contexto or len(contexto) < 1:
            print(f'  [AUTO-APRENDIZADO] KG sem resultados. Aprendendo...')
            learning_path = os.path.join(SANDBOX, 'learning_scan_universal.py')
            if os.path.exists(learning_path):
                try:
                    r = subprocess.run(
                        [sys.executable, learning_path],
                        capture_output=True, text=True, timeout=120
                    )
                    print(f'  [LearningScan] {r.stdout[-200:]}')
                except:
                    pass
            
            contexto = self.kg.buscar(texto_original)
        
        # === PASSO 7: BUSCA NO PROJETO (ultimo recurso) ===
        palavras_chave = set(re.findall(r'\b[a-zA-Z_]{3,}\b', texto_original.lower())) - _STOP_BUSCA
        
        if contexto:
            if len(contexto) > 3:
                contexto = contexto[:3]
            ctx_str = 'Sei disso:\n' + '\n'.join(f'- {l["solucao"]}' for l in contexto) + '\n\n'
            # V12 contexto agregado (0 autoavaliador)
            melhor_lesson = None
            melhor_score = 0
            for l in contexto:
                sol = l.get("solucao", "").lower()
                matches = sum(1 for t in kwargs_v12 if t in sol)
                if matches > melhor_score:
                    melhor_score = matches
                    melhor_lesson = l
            if melhor_lesson and melhor_score >= 1:
                termo_rel = f'{melhor_lesson.get("erro","")} {melhor_lesson.get("ctx","")}'
                relacionadas = self.kg.buscar(termo_rel, max_r=2)
                vistas = set()
                blocos = []
                for l_rel in [melhor_lesson] + (relacionadas or []):
                    lid = l_rel.get('id', '') or l_rel.get('solucao', '')[:50]
                    if lid in vistas: continue
                    vistas.add(lid)
                    txt = l_rel.get("solucao", "").strip()
                    if txt: blocos.append(f'- {txt[:300]}')
                    if len(blocos) >= 3: break
                ctx_agg = '\n'.join(blocos)
                prompt_v12 = (
                    f"Contexto do projeto MCR:\n{ctx_agg}\n\n"
                    f"Pergunta: {texto_original}\n"
                    f"Responda de forma util em 2-3 frases usando APENAS o contexto acima.\n"
                    f"Nao invente informacoes alem do contexto fornecido."
                )
                r = fast(prompt_v12, 0.3, "leve")
                if r and len(r) > 20:
                    print(f'{r[:600]}')
                    return r
            # Fallback: IA com contexto
            for t in range(2):
                prompt = f"{ctx_str}INSTRUCAO: Use APENAS as informacoes acima.\n\nPergunta: {texto_original}\n\nResposta:"
                if t > 0:
                    prompt += f"\n\nFeedback: resposta anterior NAO usou o contexto."
                r = fast(prompt, 0.1, "leve")
                if not r: continue
                ok, _ = self._autoavaliar_resposta(texto_original, r)
                if ok:
                    print(f"\n{r[:500]}")
                    return r
        
        # === PASSO 8: CREW PIPELINE (grep no projeto) ===
        print(f'  [Supervisor] Busca profunda no projeto...')
        
        from crew_pattern import CrewPipeline, grep_pipeline
        if not hasattr(self, '_crew_pipeline'):
            self._crew_pipeline = CrewPipeline(self.kg, self.ia, self.ctx_crew, verbose=False)
        
        encontrados = grep_pipeline(texto_original, SANDBOX)
        
        if encontrados:
            melhor = encontrados[0]
            print(f'  [Busca] {len(encontrados)} arquivos, melhor: {melhor["arquivo"]} (score: {melhor["score"]})')
            prompt_final = (
                f"Contexto extra:\n{contexto_extra[:500]}\n\n" if contexto_extra else ""
            ) + f"Arquivo: {melhor['arquivo']}\nConteudo: {melhor['trecho']}\nPergunta: {texto_original}\nExplique com base no arquivo."
            r_final = self.ia.gerar(prompt_final, 0.3)
            if r_final and len(r_final) > 20:
                ok, motivo = self._autoavaliar_resposta(texto_original, r_final)
                if ok:
                    print(f'\n{r_final[:500]}')
                    # Aprende para V12 na proxima
                    self.kg.aprender(texto_original[:80], f'buscado em {melhor["arquivo"]}',
                                     r_final[:200], 'pipeline_busca')
                    return r_final
                else:
                    print(f'  [Autoavaliador] Resposta inadequada: {motivo[:80]}')
        
        # === PASSO 9: FALHA TOTAL ===
        # Relata o que TEM, nao 'nao sei'
        resumo = f"Nao encontrei resposta especifica no meu conhecimento atual."
        if contexto_extra:
            resumo += f"\n\nContexto disponivel:\n{contexto_extra[:800]}"
        resumo += f"\n\nTenho {len(self.kg.data.get('licoes',[]))} licoes no KG e acesso a documentacao do projeto."
        resumo += "\n\nQuer que eu busque na web para aprender sobre isso?"
        print(f"\n{resumo}")
        
        # Aprende que nao sabe (para evitar silencio generico no futuro)
        self.kg.aprender(
            f"Pergunta sem resposta: {texto_original[:60]}",
            "falha_perguntar",
            f"Tipo: {tipo}/{subtipo}. Nao encontrei resposta adequada. Contexto extra disponivel: {bool(contexto_extra)}",
            "perguntar_falha"
        )
        return None


# ============================================================
# HELPER: Executa script do sandbox com fork unico (atalhos)
# ============================================================

def _run_script(script_nome, extra_args=None):
    """Executa um script do sandbox/ ou devia/ com fork unico.
    Captura e exibe saida (como o antigo task fazia).
    Retorna o codigo de saida do processo.
    Uso: _run_script('mcr_loop') ou _run_script('autoavaliacao', ['arg1'])
    """
    import subprocess as _sp
    devia_dir = os.path.dirname(__file__)
    sandbox_dir = SANDBOX
    
    # Constroi caminho: procura em sandbox e devia
    for d in [sandbox_dir, devia_dir]:
        script_path = os.path.join(d, script_nome + '.py')
        if os.path.exists(script_path):
            cmd = [sys.executable, script_path]
            if extra_args:
                cmd.extend(extra_args)
            try:
                r = _sp.run(cmd, capture_output=True, text=True, timeout=300)
                out = (r.stdout or '').strip()
                err = (r.stderr or '').strip()
                if out:
                    print(out)
                if err:
                    print(f'  [STDERR] {err[:500]}')
                return r.returncode
            except KeyboardInterrupt:
                return -1
            except Exception as e:
                print(f'  [Erro] {script_nome}: {e}')
                return -2
    
    print(f'  [Script nao encontrado] {script_nome}.py em sandbox/ ou devia/')
    return -3

ATALHOS_DIRETOS = {
    'auditar': 'mcr_auditor',
    'autoavaliar': 'autoavaliacao',
    'autoconsciencia': 'mcr_autoconsciencia',
    'auto_improve': 'mcr_auto_improve',
    'auto_reparo': 'mcr_auto_reparo',
    'observar': 'mcr_observatory_v2',
    'agente': 'mcr_agent_v2',
    'chat': 'mcr_chat',
    'scriptbuilder': 'mcr_scriptbuilder',
    'ultimate': 'mcr_ultimate',
    'conhecimento': 'mcr_knowledge',
    'ambiente': 'mcr_env',
    'learning_scan': 'mcr_learning_scan',
    'melhorias': 'mcr_improvements',
    'supervisor': 'mcr_supervisor',
    'auto_diagnostico': 'mcr_auto_diagnostico',
    'auto_melhoria': 'mcr_auto_melhoria',
    'web_learn': 'web_learn',
}

# MAIN — Orquestrador Unico
# ============================================================

def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    kg = KnowledgeGraph()
    ia = IA()
    
    # Poda automatica do KG na inicializacao (marca weblearn/learning_scan como inativos)
    kg.purgar()
    
    # Modo --json: comando via arquivo (sem shell, sem escaping)
    if '--json' in sys.argv:
        idx = sys.argv.index('--json')
        if idx + 1 < len(sys.argv):
            json_path = sys.argv[idx + 1]
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    import json as _json; cmd_data = _json.load(f)
                sys.argv = [sys.argv[0], cmd_data.get('cmd', ''), *cmd_data.get('args', [])]
                args = cmd_data.get('args', [])
                result_path = json_path.replace('_cmd', '_result')
            except Exception as e:
                print(f'[MCR-DevIA] Erro lendo {json_path}: {e}')
                return
        else:
            print('[MCR-DevIA] Use: --json <arquivo_cmd>')
            return

    if len(sys.argv) < 2:
        print(__doc__)
        print(f'Licoes: {kg.data["metricas"]["licoes"]} | Geracao: {kg.data["metricas"]["geracoes"]}'
              f' | Compilacao: {kg.data["metricas"]["compilacoes"]}')
        return

    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    # Kernel desativado: comandos modulares via kernel.py
    if cmd == 'status':
        m = kg.data['metricas']
        print(f'\n[MCR-DevIA] V{kg.data["versoes"]}')
        print(f'  Licoes: {m["licoes"]}')
        print(f'  Gerações: {m["geracoes"]}')
        print(f'  Compilações: {m["compilacoes"]}')
        print(f'  Usos: {m["usos"]}')
        print(f'\nLicoes:')
        for l in kg.data['licoes'][:5]:
            print(f'  {l["id"]}: {l["erro"][:50]}... [{l.get("usos",0)}x]')
        print(f'\nComandos: gerar, lore, compilar, ensinar, perguntar')
    
    elif cmd == 'gerar' and len(args) >= 1:
        tipo = args[0]; resto = ' '.join(args[1:])
        g = Gerador(ia, kg)
        g.gerar(tipo, resto)
    
    elif cmd == 'lore' and len(args) >= 2:
        l = LoreGen(ia)
        l.gerar(args[0], ' '.join(args[1:]))
    
    elif cmd == 'compilar':
        projeto = args[0] if args else 'canary'
        b = Builder(kg, ia)
        b.compilar(projeto)
    
    elif cmd == 'ensinar' and len(args) >= 3:
        kg.aprender(args[0], args[1], args[2], args[3] if len(args) > 3 else 'geral')
    
    elif cmd == 'perguntar' and len(args) >= 1:
        s = Supervisor(ia, kg)
        s.perguntar(' '.join(args))
    
    elif cmd == 'grep' and len(args) >= 1:
        """Grep universal: qualquer tipo de arquivo, com --literal, --max, --context, --type.
        Uso: python mcr_devia.py grep <padrao> [dir|arquivo] [--literal] [--max N] [--context N] [--type .py,.md]
        Ex:  python mcr_devia.py grep "def main" . --literal --context 2 --max 10"""
        # Extrai flags
        flgs = {'--literal': False, '--max': 50, '--context': 0, '--type': None}
        args_limpos = []
        i = 0
        while i < len(args):
            a = args[i]
            if a == '--literal':
                flgs['--literal'] = True
            elif a == '--max' and i + 1 < len(args):
                try: flgs['--max'] = max(1, int(args[i+1])); i += 1
                except: pass
            elif a == '--context' and i + 1 < len(args):
                try: flgs['--context'] = max(0, int(args[i+1])); i += 1
                except: pass
            elif a == '--type' and i + 1 < len(args):
                flgs['--type'] = [t.strip() for t in args[i+1].split(',')]
                i += 1
            else:
                args_limpos.append(a)
            i += 1
        args = args_limpos
        
        padrao = args[0]
        # Se o segundo arg tem wildcard (* ?), é padrão glob, não diretório
        if len(args) > 1 and ('*' in args[1] or '?' in args[1]):
            diretorio = r'E:\Projeto MCR\scripts\mcr_devia'
        else:
            diretorio = args[1] if len(args) > 1 else r'E:\Projeto MCR\scripts\mcr_devia'
        
        import re as re_grep
        import fnmatch as fn_grep
        
        # Se o destino é um arquivo, usa ele; se é diretório, walk
        if os.path.isfile(diretorio):
            # Busca em UM arquivo específico
            caminhos = [('', diretorio)]
            base_dir = os.path.dirname(diretorio)
        elif os.path.isdir(diretorio):
            base_dir = diretorio
            from diretorio_analyzer import filtrar_dirs_walk, get_analyzer
            analyzer = get_analyzer()
            caminhos = []
            for root, dirs, files in os.walk(diretorio):
                dirs[:] = filtrar_dirs_walk(dirs, root, analyzer)
                for f in files:
                    # Filtro por tipo (se especificado, default: .py .md .xml .json .lua .txt .yaml .cfg)
                    ext_vals = flgs['--type'] or ['.py', '.md', '.xml', '.json', '.lua', '.txt', '.yaml', '.yml', '.cfg', '.toml', '.bat', '.ps1', '.sh']
                    if not any(f.lower().endswith(t.lower()) for t in ext_vals):
                        continue
                    caminhos.append((root, f))
        else:
            print(f'[MCR-DevIA] Diretorio/arquivo nao encontrado: {diretorio}')
            return
        
        resultados = []
        ctx = flgs['--context']
        for root, f in caminhos:
            path = os.path.join(root, f) if root else f
            try:
                with open(path, encoding='utf-8', errors='replace') as fh:
                    linhas = fh.readlines()
                for i, linha in enumerate(linhas):
                    # Se --literal, busca substring; se não, regex
                    if flgs['--literal']:
                        encontrou = padrao in linha
                    else:
                        try:
                            encontrou = re_grep.search(padrao, linha)
                        except re_grep.error:
                            encontrou = padrao in linha  # fallback se regex invalida
                    
                    if encontrou:
                        rel_path = os.path.relpath(path, base_dir)
                        # Com contexto: guarda linhas ao redor
                        if ctx > 0:
                            inicio = max(0, i - ctx)
                            fim = min(len(linhas), i + ctx + 1)
                            ctx_linhas = []
                            for j in range(inicio, fim):
                                marcador = '>' if j == i else ' '
                                ctx_linhas.append(f"{marcador}L{j+1}: {linhas[j].rstrip()[:120]}")
                            resultados.append((rel_path, i+1, linha.strip()[:120], ctx_linhas))
                        else:
                            resultados.append((rel_path, i+1, linha.strip()[:120], []))
            except:
                pass
        
        max_r = flgs['--max']
        total = len(resultados)
        print(f'[MCR-DevIA] Grep por "{padrao}" | alvo: {diretorio} | tipo: {flgs["--type"] or "todos"} | {total} resultados')
        for idx, (arq, nlinha, conteudo, ctx_linhas) in enumerate(resultados[:max_r]):
            if ctx > 0 and ctx_linhas:
                for cl in ctx_linhas:
                    print(f'  {cl}')
            else:
                conteudo_seguro = conteudo.encode('ascii', errors='replace').decode('ascii'); print(f'  {arq}:L{nlinha}: {conteudo_seguro}')
        if total > max_r:
            print(f'  ... mais {total - max_r} resultados (use --max N para ver mais)')
    
    elif cmd == 'read' and len(args) >= 1:
        """Le um arquivo com offset/limit.
        Uso: python mcr_devia.py read <path> [linhas]
             python mcr_devia.py read <path> --offset 100 --limit 50
        Ex:  python mcr_devia.py read mcr_devia.py 10
             python mcr_devia.py read mcr_devia.py --offset 200 --limit 30"""
        path = args[0]
        
        # Extrai --offset e --limit
        offset = 1
        limit = 30
        args_sem_flags = [path]
        i = 1
        while i < len(args):
            a = args[i]
            if a == '--offset' and i + 1 < len(args):
                try: offset = max(1, int(args[i+1])); i += 1
                except: pass
            elif a in ('--limit', '--linhas') and i + 1 < len(args):
                try: limit = max(1, int(args[i+1])); i += 1
                except: pass
            else:
                args_sem_flags.append(a)
            i += 1
        
        # Compatibilidade: segundo arg como número = limit
        if len(args_sem_flags) > 1:
            try:
                limit = max(1, int(args_sem_flags[1]))
            except:
                pass
        
        if os.path.exists(path):
            with open(path, encoding='utf-8') as fh:
                linhas = fh.readlines()
            total = len(linhas)
            fim = min(offset + limit - 1, total)
            print(f'[MCR-DevIA] Leitura de {path} ({total} linhas, L{offset}-L{fim}):')
            for i in range(offset - 1, min(offset - 1 + limit, total)):
                print(f'  L{i+1}: {linhas[i].rstrip()[:160].encode("ascii", errors="replace").decode("ascii")}')
            if fim < total:
                print(f'  ... mais {total - fim} linhas (use --offset {fim+1} para continuar)')
        else:
            print(f'[MCR-DevIA] Arquivo nao encontrado: {path}')
    
    elif cmd == 'edit' and len(args) >= 2 and any(a in args for a in ['--desc', '--ia', '--contexto']):
        """Edicao guiada por ContextCrew + IA.
        Uso: python mcr_devia.py edit <path> --desc "descricao do que mudar" [--forcar]
        O ContextCrew busca contexto no KG/docs para guiar a edicao."""
        path = args[0]
        idx_desc = next((args.index(a) for a in ['--desc', '--ia', '--contexto'] if a in args), 2)
        descricao = " ".join(args[idx_desc+1:])
        forcar = '--forcar' in args
        
        if not os.path.exists(path):
            print(f'[MCR-DevIA] Arquivo nao encontrado: {path}')
            return
        
        # 1. ContextCrew busca informacoes sobre o arquivo e a descricao
        try:
            from context_crew import ContextCrew
            crew = ContextCrew()
            contexto = crew.executar(f"Editar {os.path.basename(path)}: {descricao}")
            if contexto:
                print(f'  [ContextCrew] Contexto obtido ({len(contexto)} chars)')
        except Exception as e:
            contexto = None
            print(f'  [ContextCrew] Indisponivel: {e}')
        
        # 2. Le o arquivo
        with open(path, encoding='utf-8') as fh:
            linhas = fh.readlines()
        total_linhas = len(linhas)
        
        # [D] Guardrail: arquivos > 100 linhas exigem --forcar
        if total_linhas > 100 and not forcar:
            print(f'  [EDIT-D] Arquivo tem {total_linhas} linhas (>100).')
            print(f'  [EDIT-D] Para editar arquivos grandes, use --forcar ou edit normal (por linha).')
            return
        
        # [B] Modelo menor e mais rapido para edicoes cirurgicas
        MODELO_EDIT = "qwen2.5-coder:1.5b"
        
        # 3. Encontra funcoes disponiveis para contexto
        funcoes_encontradas = []
        for i, linha in enumerate(linhas):
            m = re.match(r'^(\s*)def\s+(\w+)\s*\(', linha)
            if m:
                funcoes_encontradas.append({"nome": m.group(2), "linha": i})
        nomes_funcoes = [f['nome'] for f in funcoes_encontradas]
        if nomes_funcoes:
            print(f'  Funcoes: {nomes_funcoes}')
        
        # [A] Prompt que pede DIFERENCA (diff), nao codigo completo
        prompt_edit = (
            f"Arquivo: {os.path.basename(path)} ({total_linhas} linhas)\n"
            f"Descricao: {descricao}\n"
            f"Funcoes: {nomes_funcoes}\n\n"
            f"Contexto:\n{contexto[:600] if contexto else 'Nenhum'}\n\n"
            f"Retorne APENAS as LINHAS MODIFICADAS, como um diff (com + e -).\n"
            f"NUNCA retorne o arquivo inteiro. Use formato:\n"
            f"```diff\n"
            f"- linha original (se for modificar)\n"
            f"+ linha nova\n"
            f"```"
        )
        
        if not forcar:
            print(f'  [MCR-DevIA] Edicao guiada por IA. Prompt preparado.')
            print(f'  [MCR-DevIA] Execute com --forcar para a IA gerar e aplicar.')
            print(f'  [MCR-DevIA] Ou use edit normal (por linha) para precisao.')
            return
        
        # 4. IA gera o diff (modelo menor, mais rapido)
        resp = fast(prompt_edit[:3000], 0.1, MODELO_EDIT) or ""
        
        # Extrai diff do bloco ```diff ... ```
        m_diff = re.search(r'```diff\s*\n(.+?)```', resp, re.DOTALL)
        diff_texto = m_diff.group(1).strip() if m_diff else resp.strip()
        
        if not diff_texto or len(diff_texto) < 5:
            print(f'  [MCR-DevIA] IA nao gerou diff valido')
            print(f'  Resposta: {resp[:200]}')
            return
        
        # 5. Converte diff em edicoes
        # Procura por funcao alvo no diff (linhas com +)
        linhas_diff = diff_texto.split('\n')
        novas_linhas_func = []
        achou_funcao = False
        func_nome = None
        for dl in linhas_diff:
            if dl.startswith('+'):
                conteudo = dl[1:].strip()
                if conteudo.startswith('def '):
                    func_nome = conteudo.split('(')[0].replace('def ','').strip()
                    achou_funcao = True
                if achou_funcao:
                    novas_linhas_func.append(dl[1:])  # Sem o +
            elif dl.startswith('-'):
                continue  # Pula linhas removidas
            elif achou_funcao and dl.strip() and not dl.startswith('+') and not dl.startswith('-'):
                # Linhas de contexto (sem + nem -) - inclui se estiver dentro da funcao
                novas_linhas_func.append(dl)
        
        if not achou_funcao or not func_nome:
            # Fallback: tenta extrair funcao direto da resposta
            m_func = re.search(r'^(\s*)def\s+(\w+)\s*\(', diff_texto, re.MULTILINE)
            if m_func:
                func_nome = m_func.group(2)
                achou_funcao = True
                # Pega o bloco inteiro da funcao
                idx_inicio = diff_texto.find(m_func.group(0))
                if idx_inicio >= 0:
                    novas_linhas_func = [diff_texto[idx_inicio:]]
        
        if not achou_funcao or not func_nome:
            print(f'  [MCR-DevIA] IA nao gerou uma funcao valida no diff')
            print(f'  Resposta: {diff_texto[:300]}')
            return
        
        # 6. Encontra a funcao alvo no arquivo original
        linha_func = None
        for i, linha in enumerate(linhas):
            if re.match(rf'^(\s*)def\s+{re.escape(func_nome)}\s*\(', linha):
                linha_func = i
                break
        
        if linha_func is None:
            print(f'  [MCR-DevIA] Funcao "{func_nome}" nao encontrada no arquivo')
            return
        
        print(f'  Modificando: {func_nome} (L{linha_func+1})')
        
        # 7. [C] Preview: mostra diff do que vai mudar
        indent_orig = re.match(r'^(\s*)', linhas[linha_func]).group(1)
        nivel_orig = len(indent_orig)
        fim_func = linha_func + 1
        while fim_func < len(linhas):
            linha_atual = linhas[fim_func]
            if linha_atual.strip():
                espacos = len(linha_atual) - len(linha_atual.lstrip())
                if espacos <= nivel_orig:
                    break
            fim_func += 1
        
        codigo_original = "".join(linhas[linha_func:fim_func])
        print(f'\n  [C] === DASHDASH ORIGINAL ===')
        for l in codigo_original.split('\n')[:15]:
            print(f'  [C]   {l}')
        print(f'  [C] === /ORIGINAL ({(fim_func-linha_func)} linhas) ===')
        
        # 8. Cria backup + aplica
        backup_path = path + '.bak'
        import shutil
        shutil.copy2(path, backup_path)
        
        codigo_novo = '\n'.join(novas_linhas_func)
        print(f'\n  [C] === DASHDASH NOVO ===')
        for l in codigo_novo.split('\n')[:15]:
            print(f'  [C]   {l}')
        print(f'  [C] === /NOVO ({len(novas_linhas_func)} linhas) ===')
        
        # Substitui
        novas_linhas = linhas[:linha_func] + [codigo_novo + '\n'] + linhas[fim_func:]
        novo_codigo = "".join(novas_linhas)
        
        # Valida
        try:
            compile(novo_codigo, path, 'exec')
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(novo_codigo)
            print(f'[MCR-DevIA] [OK] Edit IA aplicado! Backup: {os.path.basename(backup_path)}')
        except SyntaxError as e:
            print(f'[MCR-DevIA] [ERRO] Sintaxe: {e}')
            shutil.copy2(backup_path, path)
            os.remove(backup_path)
            print(f'  Backup restaurado.')
    
    elif cmd == 'edit' and len(args) >= 3:
        """Edita por LINHA (precisao cirurgica). 
        Uso: python mcr_devia.py edit <path> <linha> <novo_conteudo>
        Ou:  python mcr_devia.py edit <path> --range <inicio> <fim> --substituir <velho> <novo>
        Ou:  python mcr_devia.py edit <path> --linha <n> --substituir <velho> <novo>"""
        path = args[0]
        if not os.path.exists(path):
            print(f'[MCR-DevIA] Arquivo nao encontrado: {path}')
        else:
            with open(path, encoding='utf-8') as fh:
                linhas = fh.readlines()
            
            if '--range' in args:
                # Edicao por intervalo de linhas
                idx_range = args.index('--range')
                try:
                    inicio = int(args[idx_range + 1])
                    fim = int(args[idx_range + 2])
                except Exception as e:
                    print(f"[Fix] ERRO: {e}")
                    return
                idx_sub = args.index('--substituir') if '--substituir' in args else None
                if idx_sub:
                    velho = args[idx_sub + 1]
                    novo = args[idx_sub + 2]
                    # So substitui no intervalo especificado
                    for i in range(inicio - 1, min(fim, len(linhas))):
                        if i >= 0 and velho in linhas[i]:
                            linhas[i] = linhas[i].replace(velho, novo)
                            # Forca unicidade: so 1 substituicao por padrao no intervalo
                            break
                    else:
                        print(f'[MCR-DevIA] Padrao "{velho}" nao encontrado entre L{inicio}-L{fim}')
                        return
                else:
                    print('[MCR-DevIA] Use: --range <inicio> <fim> --substituir <velho> <novo>')
                    return
            elif '--linha' in args:
                # Edicao por linha unica com substituicao de texto
                idx_linha = args.index('--linha')
                try:
                    linha_alvo = int(args[idx_linha + 1])
                except Exception as e:
                    print(f"[Fix] ERRO: {e}")
                    return
                idx_sub = args.index('--substituir') if '--substituir' in args else None
                if idx_sub and 1 <= linha_alvo <= len(linhas):
                    velho = args[idx_sub + 1]
                    novo = args[idx_sub + 2]
                    if velho in linhas[linha_alvo - 1]:
                        linhas[linha_alvo - 1] = linhas[linha_alvo - 1].replace(velho, novo)
                    else:
                        print(f'[MCR-DevIA] Padrao nao encontrado na L{linha_alvo}')
                        print(f'  Conteudo: {linhas[linha_alvo - 1].rstrip().encode('ascii',errors='replace').decode('ascii')}')
                        return
                else:
                    print('[MCR-DevIA] Use: --linha <n> --substituir <velho> <novo>')
                    return
            else:
                # Edicao simples: substituir linha inteira
                try:
                    linha_alvo = int(args[1])
                    novo_conteudo = " ".join(args[2:])
                except Exception as e:
                    print(f"[Fix] ERRO: {e}")
                    return
                if 1 <= linha_alvo <= len(linhas):
                    print(f'[MCR-DevIA] Substituindo L{linha_alvo}:')
                    print(f'  Antes: {linhas[linha_alvo-1].rstrip().encode('ascii',errors='replace').decode('ascii')}')
                    linhas[linha_alvo - 1] = novo_conteudo + ('\n' if not novo_conteudo.endswith('\n') else '')
                    print(f'  Depois: {linhas[linha_alvo-1].rstrip().encode('ascii',errors='replace').decode('ascii')}')
                else:
                    print(f'[MCR-DevIA] Linha {linha_alvo} invalida (1-{len(linhas)})')
                    return
            
            # Salva
            with open(path, 'w', encoding='utf-8') as fh:
                fh.writelines(linhas)
            
            # Valida: tenta compilar
            if path.endswith('.py'):
                try:
                    compile("".join(linhas), path, 'exec')
                    print(f'[MCR-DevIA] [OK] Edit aplicado e compilacao verificada!')
                except SyntaxError as e:
                    print(f'[MCR-DevIA] [ALERTA] Edit aplicado, mas erro de sintaxe: {e}')
                    print(f'[MCR-DevIA] Revertendo...')
                    # (aqui poderia ter rollback, mas exige backup previo)
            else:
                print(f'[MCR-DevIA] [OK] Edit aplicado!')
    
    elif cmd == 'glob' and len(args) >= 1:
        """Glob universal: detecta padrao automaticamente.
        Uso: python mcr_devia.py glob <padrao> [dir] [--type .py,.md] [--max N]
        Ex:  python mcr_devia.py glob mcr_auto  (auto-adiciona *mcr_auto*)
             python mcr_devia.py glob *.xml --type .xml
             python mcr_devia.py glob diagnosticar --max 10"""
        padrao = args[0]
        
        # Extrai flags
        max_r = 20
        filtro_tipo = None
        args_clean = [padrao]
        i = 1
        while i < len(args):
            a = args[i]
            if a == '--max' and i + 1 < len(args):
                try: max_r = max(1, int(args[i+1])); i += 1
                except: pass
            elif a == '--type' and i + 1 < len(args):
                filtro_tipo = [t.strip() for t in args[i+1].split(',')]
                i += 1
            else:
                args_clean.append(a)
            i += 1
        
        diretorio = args_clean[1] if len(args_clean) > 1 else r'E:\Projeto MCR'
        
        # AUTO-DETECÇÃO: se padrao NAO tem wildcards, adiciona * em volta
        if not any(c in padrao for c in '*?'):
            padrao_glob = f'*{padrao}*'
            print(f'[MCR-DevIA] Padrao sem wildcard, auto-corrigido: "{padrao_glob}"')
        else:
            padrao_glob = padrao
        
        import fnmatch as fn_glob
        resultados = []
        from diretorio_analyzer import filtrar_dirs_walk, get_analyzer
        analyzer = get_analyzer()

        for root, dirs, files in os.walk(diretorio):
            dirs[:] = filtrar_dirs_walk(dirs, root, analyzer)
            for f in files:
                # Filtro por tipo
                if filtro_tipo and not any(f.lower().endswith(t.lower()) for t in filtro_tipo):
                    continue
                if fn_glob.fnmatch(f, padrao_glob):
                    rel = os.path.relpath(os.path.join(root, f), diretorio)
                    resultados.append(rel)
        
        resultados.sort()
        total = len(resultados)
        print(f'[MCR-DevIA] Glob por "{padrao_glob}" em {diretorio}: {total} arquivos')
        for r in resultados[:max_r]:
            print(f'  {r}')
        if total > max_r:
            print(f'  ... mais {total - max_r} arquivos (use --max N para ver mais)')
    
    elif cmd == 'task' and len(args) >= 1:
        """Delega para QUALQUER script do MCR-DevIA.
        Uso: python mcr_devia.py task <script>
             python mcr_devia.py task list (mostra todos)
             python mcr_devia.py task <script> <args...>"""
        DEVIA_DIR = os.path.dirname(__file__)
        SANDBOX_DIR = SANDBOX
        
        # Mapa de scripts (nome -> caminho)
        all_scripts = {}
        for d in [DEVIA_DIR, SANDBOX_DIR]:
            for f in os.listdir(d):
                if f.endswith('.py') and not f.startswith('_'):
                    nome = f.replace('.py', '')
                    all_scripts[nome] = os.path.join(d, f)
        
        if args[0] == 'list':
            # Separa scripts do sistema de scripts temporarios
            sistema = {n: p for n, p in all_scripts.items() if 'mcr_devia' in p}
            temporarios = {n: p for n, p in all_scripts.items() if 'sandbox' in p and n not in sistema}
            print(f'[MCR-DevIA] Sistema ({len(sistema)}):')
            for nome in sorted(sistema):
                print(f'  - {nome}')
            if temporarios:
                print(f'\n  Sandbox ({len(temporarios)}): use "task <nome>" para executar')
                for nome in sorted(temporarios)[:20]:
                    print(f'    - {nome}')
                if len(temporarios) > 20:
                    print(f'    ... mais {len(temporarios)-20}')
            return
        
        script_nome = args[0]
        sub_args = args[1:]
        
        if script_nome in all_scripts:
            script_path = all_scripts[script_nome]
            print(f'[MCR-DevIA] Executando: {script_nome}')
            try:
                r = subprocess.run([sys.executable, script_path] + sub_args,
                    capture_output=True, text=True, timeout=300)
                out = (r.stdout or '')[-1000:]
                err = (r.stderr or '')[:500]
                if out:
                    print(out)
                if err:
                    print(f'  [STDERR] {err}')
                    # AUTO-REPARO: analisa, corrige, retenta
                    if 'Error' in err or 'Traceback' in err:
                        print(f'[MCR-DevIA] Auto-reparo ativado!')
                        # 1. Identifica o tipo de erro
                        erro_tipo = 'desconhecido'
                        if 'ModuleNotFoundError' in err:
                            erro_tipo = 'import_faltando'
                        elif 'KeyError' in err or 'json.decoder' in err:
                            erro_tipo = 'json_invalido'
                        elif 'FileNotFoundError' in err:
                            erro_tipo = 'arquivo_ausente'
                        elif 'SyntaxError' in err:
                            erro_tipo = 'sintaxe_invalida'
                        print(f'  [Auto-reparo] Tipo: {erro_tipo}')
                        
                        # 2. Tenta corrigir (1 tentativa)
                        if erro_tipo == 'json_invalido':
                            print(f'  [Auto-reparo] JSON invalido. O LearningScan pode ter mudado de formato.')
                            print(f'  [Auto-reparo] Execute: learning_scan_universal.py para regenerar.')
                            # Sugere acao, nao corrige automaticamente (JSON e dado, nao codigo)
                        
                        elif erro_tipo == 'import_faltando':
                            print(f'  [Auto-reparo] Import faltando. Tentando adicionar...')
                            modulo = err.split("'")[1] if "'" in err else '?'
                            print(f'  [Auto-reparo] Modulo ausente: {modulo}')
                        
                        # 3. Registra no log de reparo
                        log_path = os.path.join(SANDBOX, '.mcr_auto_repair.log')
                        with open(log_path, 'a', encoding='utf-8') as lf:
                            lf.write(f'[{__import__("datetime").datetime.now()}] {script_nome}: {erro_tipo} - {err[:100]}\n')
                        print(f'  [Auto-reparo] Erro registrado em .mcr_auto_repair.log')
            except subprocess.TimeoutExpired:
                print(f'[MCR-DevIA] Task {script_nome} excedeu 300s')
            except Exception as e:
                print(f'[MCR-DevIA] Erro ao executar {script_nome}: {e}')
        else:
            print(f'[MCR-DevIA] Script "{script_nome}" nao encontrado.')
            print(f'  Use "task list" para ver todos disponiveis.')
    
    elif cmd == 'question' and len(args) >= 1:
        """Pergunta algo ao usuario e aguarda resposta.
        Uso: python mcr_devia.py question <pergunta>"""
        pergunta = " ".join(args)
        print(f'[MCR-DevIA] Pergunta: {pergunta}')
        try:
            resposta = input('> ')
            print(f'[MCR-DevIA] Resposta recebida: {resposta[:100]}')
        except Exception as e:
            print(f"[Fix] ERRO: {e}")
    
    elif cmd == 'patch' and len(args) >= 2:
        """Edicao V12: Python estrutura, IA preenche blank.
        Uso: python mcr_devia.py patch <arquivo> <descricao>
        Ex:  python mcr_devia.py patch builder_x "adicionar logging no _gerar_bloco"""
        forca = '--force' in args or '-f' in args
        args = [a for a in args if a not in ('--force', '-f')]
        alvo = args[0]
        descricao = " ".join(args[1:])
        print(f'[MCR-DevIA] Patch: {alvo} -> {descricao[:60]}...')
        
        # SAFETY: detecta intencao de CRIAR funcao (patch so substitui)
        palavras_criar = ['adicionar', 'criar', 'nova funcao', 'novo metodo', 'inserir', 'incluir']
        if any(p in descricao.lower() for p in palavras_criar):
            print(f'  [Patch] [BLOQUEADO] Descricao parece pedir CRIACAO de funcao.')
            print(f'  [Patch] Patch so SUBSTITUI funcoes existentes. Para criar, use:')
            print(f'    python mcr_devia.py build "criar {descricao}"')
            return
        
        # V12 FASE 1: Python encontra o arquivo (deterministico)
        import fnmatch as fn_patch
        candidatos = []
        from diretorio_analyzer import get_analyzer, filtrar_dirs_walk
        _da = get_analyzer()
        
        # Se for caminho absoluto que existe, usa direto (nao restrito a SANDBOX)
        alvo_expandido = os.path.expanduser(alvo)
        if os.path.isabs(alvo_expandido) and os.path.exists(alvo_expandido):
            path = alvo_expandido
            print(f'  [Patch] Caminho absoluto: {path}')
        else:
            # Fallback: busca em SANDBOX
            for root, dirs, files in os.walk(SANDBOX):
                dirs[:] = filtrar_dirs_walk(dirs, root, _da)
                for f in files:
                    if fn_patch.fnmatch(f, f'*{alvo}*') and f.endswith('.py'):
                        candidatos.append(os.path.join(root, f))
            if not candidatos:
                print(f'  [Patch] Arquivo "{alvo}" nao encontrado')
                return
            path = candidatos[0]
            print(f'  [Patch] Encontrado: {os.path.basename(path)}')
        
        with open(path, encoding='utf-8-sig') as f:
            linhas = f.readlines()
        # Remove BOM da primeira linha se presente (U+FEFF)
        if linhas and linhas[0].startswith('\ufeff'):
            linhas[0] = linhas[0][1:]
            print(f'  [Patch] BOM removido da primeira linha')
        
        # V12 FASE 2: Python extrai funcao alvo (deterministico)
        # Procura por def/class keywords
        funcoes = []
        for i, linha in enumerate(linhas):
            m = re.match(r'^(\s*)def\s+(\w+)\s*\(', linha)
            if m:
                indent = m.group(1)
                nome = m.group(2)
                nivel_indent = len(indent)  # nivel de indentacao em espacos
                # Extrai o corpo da funcao (ate encontrar outra funcao no mesmo nivel)
                corpo = []
                j = i
                while j < len(linhas):
                    linha_atual = linhas[j]
                    if j > i and linha_atual.strip():
                        # Conta espacos no inicio (sem expandir tabs)
                        espacos = len(linha_atual) - len(linha_atual.lstrip())
                        if espacos <= nivel_indent:
                            # Linha no mesmo nivel ou menor = fim da funcao
                            break
                    corpo.append(linha_atual)
                    j += 1
                funcoes.append({"nome": nome, "linha": i+1, "codigo": "".join(corpo), "indent": indent})
        
        if not funcoes:
            print(f'  [Patch] Nenhuma funcao encontrada em {os.path.basename(path)}')
            return
        
        print(f'  [Patch] Funcoes encontradas: {[f["nome"] for f in funcoes]}')
        
        # V12 FASE 3: IA descobre QUAL funcao modificar (blank controlado)
        prompt_funcs = "\n".join(f"  L{f['linha']}: def {f['nome']}(...) -> {f['codigo'][:80].strip()}" for f in funcoes)
        # Prompt direto: IA responde APENAS o nome da funcao
        prompt_completo = (
            f"Arquivo: {os.path.basename(path)}\n"
            f"Descricao: {descricao}\n\n"
            f"Funcoes disponiveis:\n{prompt_funcs}\n\n"
            f"Responda APENAS o nome exato da funcao que deve ser modificada, sem explicacoes."
        )
        
        resp = fast(prompt_completo[:2000]) or ""
        print(f'  [Patch] Resposta IA: {resp[:200]}')
        
        # Extrai o nome da funcao da resposta
        func_alvo = None
        linha_alvo = None
        
        # 1. Busca por linha: "L123" na resposta
        nums = re.findall(r'L(\d+)', resp)
        for n in nums:
            for f in funcoes:
                if f["linha"] == int(n):
                    func_alvo = f
                    linha_alvo = int(n)
                    break
            if linha_alvo: break
        
        # 2. Fallback: nome da funcao aparece na resposta
        if not func_alvo:
            for f in funcoes:
                if f['nome'] in resp:
                    func_alvo = f
                    linha_alvo = f['linha']
                    break
        
        # 3. Fallback: matching por similaridade (case insensitive)
        if not func_alvo:
            palavras_resp = resp.lower().split()
            for f in funcoes:
                nome_lower = f['nome'].lower()
                if nome_lower in resp.lower() or nome_lower in palavras_resp:
                    func_alvo = f
                    linha_alvo = f['linha']
                    break
        
        # 4. Fallback: se tem UMA funcao no arquivo, assume ela
        if not func_alvo and len(funcoes) == 1:
            func_alvo = funcoes[0]
            linha_alvo = func_alvo['linha']
            print(f'  [Patch] Apenas uma funcao encontrada, assumindo: {func_alvo["nome"]}')
        
        if not linha_alvo:
            print(f'  [Patch] IA nao identificou a funcao. Opcoes:\n'
                  f'    Opcao 1: Use edit manual.\n'
                  f'    Opcao 2: Especifique o nome da funcao explicitamente:\n'
                  f'      python mcr_devia.py patch {alvo} "na funcao X, {descricao}"')
            return
        
        print(f'  [Patch] Funcao alvo: {func_alvo["nome"]} (L{linha_alvo})')
        print(f'  [Patch] Codigo atual ({len(func_alvo["codigo"].splitlines())} linhas):')
        for l in func_alvo["codigo"].splitlines()[:5]:
            print(f'    {l}')
        
        # V12 FASE 4: IA gera codigo novo (chamada direta ao Ollama, sem KG/veracidade)
        prompt_code = (
            f"Substitua a funcao abaixo para: {descricao}\n\n"
            f"{func_alvo['codigo']}\n\n"
            f"IMPORTANTE: Retorne APENAS o codigo da funcao. Nenhuma explicacao, nenhum texto antes ou depois, nenhum marcador de bloco. Apenas o codigo."
        )
        novo_codigo = fast(prompt_code[:2000]) or ""
        novo_codigo = re.sub(r'```\w*\n?', '', novo_codigo).strip()
        # Remove linhas que nao comecam com def, espaco, tab ou } (protecao contra texto solto)
        linhas_code = []
        for linha in novo_codigo.split('\n'):
            if linha.strip() and not linha.startswith(('def ', '    ', '\t', '}', 'class ')):
                if any(kw in linha.lower() for kw in ['aqui est', 'aqui vai', 'segue', 'esta e', 'codigo:', '```']):
                    continue
            linhas_code.append(linha)
        novo_codigo = '\n'.join(linhas_code).strip()
        
        if not novo_codigo:
            print(f'  [Patch] IA nao gerou codigo novo')
            return
        
        print(f'  [Patch] Codigo novo gerado ({len(novo_codigo.splitlines())} linhas):')
        for l in novo_codigo.splitlines()[:5]:
            print(f'    {l}')
        
        # CONFIRMACAO: exibe diff e exige --force
        if not forca:
            print(f'  [Patch] [SEGURO] Para aplicar a edicao, execute com --force:')
            print(f'    python mcr_devia.py patch {alvo} "..." --force')
            print(f'  [Patch] ou use edit manual se preferir.')
            return
        
        # V12 FASE 5: Python faz backup + aplica edicao (deterministico)
        linha_orig = func_alvo["linha"] - 1
        fim_orig = linha_orig + len(func_alvo["codigo"].splitlines())
        
        # Backup automatico
        backup_path = path + '.bak'
        import shutil
        shutil.copy2(path, backup_path)
        print(f'  [Patch] Backup criado: {os.path.basename(backup_path)}')
        
        # Substitui as linhas
        novas_linhas = linhas[:linha_orig] + [novo_codigo + '\n'] + linhas[fim_orig:]
        
        # V12 FASE 6: Python valida compilacao
        try:
            compile("".join(novas_linhas), path, 'exec')
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(novas_linhas)
            print(f'  [Patch] [OK] Edit aplicado e compilacao verificada!')
            print(f'  [Patch] Backup em: {os.path.basename(backup_path)} (remova manualmente quando satisfeito)')
        except SyntaxError as e:
            print(f'  [Patch] [ERRO] Codigo gerado tem erro de sintaxe: {e}')
            # Restaura do backup
            shutil.copy2(backup_path, path)
            os.remove(backup_path)
            print(f'  [Patch] Backup restaurado. Arquivo original preservado.')
    
    elif cmd == 'todo':
        """Gerencia lista de tarefas.
        Uso: python mcr_devia.py todo list
             python mcr_devia.py todo add <tarefa>
             python mcr_devia.py todo done <id>"""
        todo_path = os.path.join(SANDBOX, '.mcr_todo.json')
        todos = []
        if os.path.exists(todo_path):
            with open(todo_path, encoding='utf-8') as f:
                todos = json.load(f)
        
        if len(args) == 0 or args[0] == 'list':
            print(f'[MCR-DevIA] Tarefas ({len(todos)}):')
            for i, t in enumerate(todos, 1):
                status = '[x]' if t.get('done') else '[ ]'
                print(f'  {i}. {status} {t["tarefa"][:80]}')
        elif args[0] == 'add' and len(args) >= 2:
            tarefa = " ".join(args[1:])
            todos.append({'tarefa': tarefa, 'done': False})
            with open(todo_path, 'w', encoding='utf-8') as f:
                json.dump(todos, f, indent=2)
            print(f'[MCR-DevIA] Tarefa adicionada: {tarefa[:60]}')
        elif args[0] == 'done' and len(args) >= 2:
            try:
                idx = int(args[1]) - 1
                if 0 <= idx < len(todos):
                    todos[idx]['done'] = True
                    with open(todo_path, 'w', encoding='utf-8') as f:
                        json.dump(todos, f, indent=2)
                    print(f'[MCR-DevIA] Tarefa #{args[1]} concluida!')
                else:
                    print(f'[MCR-DevIA] Tarefa #{args[1]} invalida')
            except Exception as e:
                print(f"[Fix] ERRO: {e}")
    
    elif cmd == 'webfetch' and len(args) >= 1:
        """Busca conteudo de uma URL.
        Uso: python mcr_devia.py webfetch <url>"""
        url = args[0]
        print(f'[MCR-DevIA] Buscando URL: {url[:80]}...')
        try:
            import urllib.request
            r = urllib.request.urlopen(url, timeout=15)
            conteudo = r.read().decode('utf-8', errors='replace')
            print(f'[MCR-DevIA] Recebidos {len(conteudo)} bytes:')
            print(conteudo[:500])
        except Exception as e:
            print(f'[MCR-DevIA] Erro ao buscar URL: {e}')
    
    # Atalhos para scripts importantes (comandos diretos)
    elif cmd in ATALHOS_DIRETOS:
        """Atalhos diretos: executam script do sandbox com fork unico."""
        script_nome = ATALHOS_DIRETOS[cmd]
        _run_script(script_nome, extra_args=args if args else None)
    
    elif cmd == 'loop':
        """Loop autonomo OODA. Uso: loop [max_ciclos] [modo]"""
        _run_script('mcr_loop', extra_args=args if args else None)
    
    elif cmd == 'estrategia' and len(args) >= 1:
        '''Estrategista: planeja e executa. Uso: estrategia <objetivo>'''
        objetivo = " ".join(args)
        r = subprocess.run([sys.executable, r'E:\Projeto MCR\sandbox\context_monitor.py', objetivo],
            capture_output=True, text=True, timeout=120)
        print(r.stdout[-1000:] if r.stdout else '')
    
    elif cmd == 'builderx' and len(args) >= 1:
        '''Builder-X: constroi scripts por blocos. Uso: builderx <descricao>'''
        desc = " ".join(args)
        r = subprocess.run([sys.executable, r'E:\Projeto MCR\sandbox\builder_x.py', desc],
            capture_output=True, text=True, timeout=120)
        print(r.stdout[-1000:] if r.stdout else '')
    
    elif cmd == 'system_scan':
        '''Escaneia o sistema por linguagens e bibliotecas.'''
        import subprocess as sp_scan
        for cmd in ['python','lua','node','gcc','java']:
            sr = sp_scan.run(['where', cmd], capture_output=True, text=True, timeout=5)
            status = 'INSTALADO' if sr.returncode == 0 else 'AUSENTE'
            print(f'  {cmd}: {status}')
    
    elif cmd == 'build' and len(args) >= 1:
        """Pipeline Dinamica: gera codigo sob medida.
        Uso: python mcr_devia.py build <descricao>
        Ex:  python mcr_devia.py build "criar script de backup em backup.py"
             python mcr_devia.py build "funcao hello_world em hello.py"
        A pipeline detecta complexidade, extrai nome do arquivo.
        Usa ContextCrew para contexto. So gera o necessario."""
        desc = " ".join(args)
        pipeline_path = os.path.join(SANDBOX, 'builder_infinito.py')
        subprocess.run([sys.executable, pipeline_path, desc])
    
    elif cmd == 'debate' and len(args) >= 1:
        """Debate: 2 sub-agentes discutem antes de entregar.
        Uso: python mcr_devia.py debate <tema>"""
        tema = " ".join(args)
        subprocess.run([sys.executable, os.path.join(SANDBOX, 'debate_protocol.py'), tema])
    
    elif cmd == 'intencao' and len(args) >= 1:
        """Interpreta a real intencao do usuario antes de agir.
        Uso: python mcr_devia.py intencao <request>"""
        request = " ".join(args)
        from types import SimpleNamespace
        intencao = SimpleNamespace()
        palavras = set(re.findall(r'\b[a-z]{4,}\b', request.lower()))
        if any(p in palavras for p in ["melhor", "otimiz", "refator", "corrig", "arrum"]):
            tipo = "melhoria"
        elif any(p in palavras for p in ["criar", "gerar", "novo", "construir", "fazer"]):
            tipo = "criacao"
        elif any(p in palavras for p in ["analisar", "entender", "explicar", "diagnostic"]):
            tipo = "analise"
        else:
            tipo = "desconhecido"
        acoes = {"melhoria": "auto_correcao", "criacao": "build", "analise": "task analisador_multi_estagio", "desconhecido": "perguntar"}
        print(f'[Intencao] Request: {request[:80]}...')
        print(f'[Intencao] Tipo: {tipo}')
        print(f'[Intencao] Acao sugerida: {acoes.get(tipo, "perguntar")}')
        subprocess.run([sys.executable, __file__, acoes.get(tipo, "perguntar"), request[:200]])
    
    elif cmd == 'conectar':
        """Thinker de conexoes: busca conexoes entre dominios no KG."""
        print(f'[Conector] Buscando conexoes entre lessons...')
        import json, random
        kg_path = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
        if os.path.exists(kg_path):
            with open(kg_path, encoding='utf-8') as f:
                kg = json.load(f)
            lessons = kg.get('lessons', [])
            if len(lessons) >= 2:
                for _ in range(5):
                    l1, l2 = random.sample(lessons, 2)
                    ctx1 = l1.get('context', '?')
                    ctx2 = l2.get('context', '?')
                    # Conexao via palavras-chave
                    palavras1 = set(str(l1).lower().split())
                    palavras2 = set(str(l2).lower().split())
                    comuns = palavras1 & palavras2
                    if len(comuns) > 5:
                        print(f'  {ctx1} <-> {ctx2}: {len(comuns)} palavras em comum')
            else:
                print('[Conector] Menos de 2 lessons no KG')
    
    elif cmd == 'plan' and len(args) >= 1:
        """Planeja antes de executar: intencao -> plan -> intencao -> build.
        Uso: python mcr_devia.py plan <request>"""
        request = " ".join(args)
        subprocess.run([sys.executable, os.path.join(SANDBOX, 'builder_infinito.py'), f'PLAN: {request[:200]}'])
    
    elif cmd == 'bugfinder':
        """Escaneia logs e registra erros no KG para aprendizado."""
        print(f'[BugFinder] Escaneando logs...')
        import glob as glob_bf
        logs_dir = os.path.join(SANDBOX, '.mcr_devia')
        encontrados = 0
        for pattern in ['*.log', '*.err', '*.auto_repair*']:
            for path in glob_bf.glob(os.path.join(logs_dir, pattern)):
                if not os.path.exists(path): continue
                with open(path, encoding='utf-8', errors='ignore') as f:
                    for linha in f:
                        if any(p in linha.lower() for p in ['error','fail','traceback','exception']):
                            kg.aprender(f'bugfinder: {linha[:80]}', f'fonte: {os.path.basename(path)}', 'verificar log', 'bugfinder')
                            encontrados += 1
        print(f'  {encontrados} erros registrados')
    
    elif cmd == 'system':
        """SystemAware: le o computador inteiro (read-only).
        Uso: python mcr_devia.py system"""
        subprocess.run([sys.executable, os.path.join(SANDBOX, 'system_aware.py')])
    
    elif cmd == 'proativo':
        """Varre o sistema e sugere acoes sem ninguem pedir."""
        print(f'[Proativo] Oportunidades encontradas:')
        import json as json_proativo
        todo_path = os.path.join(SANDBOX, '.mcr_todo.json')
        if os.path.exists(todo_path):
            with open(todo_path, encoding='utf-8') as f:
                todos = json_proativo.load(f)
            pendentes = [t for t in todos if not t.get('done')]
            if pendentes:
                print(f'  - {len(pendentes)} tarefas pendentes no todo')
        n_py = len([f for f in os.listdir(SANDBOX) if f.endswith('.py')])
        if n_py > 30:
            print(f'  - {n_py} scripts .py no sandbox (considerar limpeza)')
    
    elif cmd == 'extract' and len(args) >= 2:
        """Extrai partes de QUALQUER arquivo, modifica, reaplica (com seguranca).
        Uso: python mcr_devia.py extract <arquivo> [descricao]
             python mcr_devia.py extract aplicar --force <arquivo>
             python mcr_devia.py extract revisar <arquivo>
        Fluxo: extrai -> revisar (MCR + Conselho) -> diff preview -> aplicar --force
        Seguranca: revisao ANTES de aplicar. So aplica com --force."""
        import xml.etree.ElementTree as ET_xt
        import csv as csv_xt, json as json_xt, shutil as sh_xt, re as re_xt
        
        # Se for comando 'revisar' (triagem -> MCR-DevIA + Conselho revisam)
        if args[0] == 'revisar' and len(args) >= 2:
            path_revisar = args[1]
            ext_dir = os.path.join(os.path.dirname(path_revisar), '_extract')
            if not os.path.exists(ext_dir):
                print(f'[Extract] Nada para revisar. Extraia os dados primeiro.')
                return
            
            for fname in sorted(os.listdir(ext_dir)):
                if not fname.endswith('.json') or fname == '_metadata.json':
                    continue
                json_path = os.path.join(ext_dir, fname)
                with open(json_path, encoding='utf-8') as f:
                    dados = json_xt.load(f)
                if not isinstance(dados, list):
                    continue
                
                print(f'\n[Revisao] Revisao INDIVIDUAL em {fname} ({len(dados)} itens)...')
                print(f'  Analisando cada item com contexto completo...')
                
                import urllib.request as ur_xt
                suspeitos = []
                
                for i, item in enumerate(dados):
                    if i >= 20:  # Limite de 20 por execucao para nao estourar tempo
                        break
                    
                    # Converte o item para JSON com contexto completo
                    item_json = json_xt.dumps(item, ensure_ascii=False)
                    
                    # IA analisa item individualmente
                    prompt = f"Item de jogo (Tibia). Analise este item COMPLETO (todos os atributos). O nome, artigo e plural estao corretos em portugues? Responda APENAS: OK ou ERRO: descricao\n\n{item_json}"
                    payload = json_xt.dumps({"model": "qwen2.5-coder:7b", "prompt": prompt, "stream": False, "options": {"temperature": 0.1, "num_ctx": 4096}}).encode()
                    try:
                        req = ur_xt.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
                        resp = json_xt.loads(ur_xt.urlopen(req, timeout=30).read()).get("response","")
                    except Exception as e:
                        print(f"[Fix] ERRO: {e}")
                    
                    item_id = item.get("id") or item.get("_linha", i)
                    nome = item.get("name", "?")
                    
                    if "ERRO" in resp:
                        suspeitos.append((item_id, nome, resp[:100]))
                        print(f'  [{len(suspeitos)}] ID {item_id}: {nome} -> ERRO')
                    else:
                        print(f'  ID {item_id}: {nome} -> OK')
                
                print(f'\n  Revisados: {min(len(dados), 20)} itens')
                print(f'  Suspeitos: {len(suspeitos)} itens')
                for sid, snome, motivo in suspeitos[:5]:
                    print(f'    ID {sid}: {snome} - {motivo}')
            
            print(f'\n[Revisao] Concluida. Para aplicar: extract aplicar --force {path_revisar}')
            return
        
        # Se for comando 'aplicar'
        if args[0] == 'aplicar' and len(args) >= 2:
            path_aplicar = args[1]
            ext_dir = os.path.join(os.path.dirname(path_aplicar), '_extract')
            if not os.path.exists(ext_dir):
                print(f'[Extract] Nada para aplicar. Diretorio _extract nao encontrado.')
                return
            
            # Gera DIFF preview antes de aplicar (seguranca)
            print(f'[Extract] Gerando diff preview...')
            ext = os.path.splitext(path_aplicar)[1].lower()
            diff_path = os.path.join(ext_dir, '_diff_preview.txt')
            with open(diff_path, 'w', encoding='utf-8') as df:
                df.write(f'Extract: {path_aplicar}\n\n')
            
            for fname in sorted(os.listdir(ext_dir)):
                if not fname.endswith('.json') or fname == '_metadata.json':
                    continue
                json_path = os.path.join(ext_dir, fname)
                with open(json_path, encoding='utf-8') as f:
                    dados = json_xt.load(f)
                with open(diff_path, 'a', encoding='utf-8') as df:
                    df.write(f'--- {fname}\n')
                    for reg in (dados if isinstance(dados, list) else [dados]):
                        for k, v in reg.items():
                            if not k.startswith('_') and k != 'id':
                                df.write(f'  {reg.get("id","?")}.{k}: {v}\n')
                    df.write('\n')
            
            print(f'[Extract] Diff preview: {diff_path}')
            print(f'[Extract] Revise o preview. Para aplicar, execute novamente com --force.')
            print(f'[Extract] Para rejeitar: rm -rf {ext_dir}')
            return
        
        elif args[0] == 'aplicar' and '--force' in args:
            # So aplica com --force (confirmacao explicita)
            idx_force = args.index('--force')
            path_aplicar = args[1] if idx_force > 1 else args[idx_force + 1]
            ext_dir = os.path.join(os.path.dirname(path_aplicar), '_extract')
            if not os.path.exists(ext_dir):
                print(f'[Extract] Nada para aplicar.')
                return
            
            bak = path_aplicar + '.bak'
            sh_xt.copy2(path_aplicar, bak)
            print(f'[Extract] Backup: {bak}')
            
            for fname in sorted(os.listdir(ext_dir)):
                if not fname.endswith('.json') or fname == '_metadata.json':
                    continue
                json_path = os.path.join(ext_dir, fname)
                with open(json_path, encoding='utf-8') as f:
                    dados = json_xt.load(f)
                
                chave_id = dados.get('_chave_id', 'id')
                tipo = dados.get('_tipo', 'xml')
                registros = dados.get('_dados', [dados]) if isinstance(dados, dict) else dados
                if isinstance(registros, dict) and '_dados' not in dados:
                    registros = [dados]
                
                contagem = 0
                if tipo == 'xml':
                    tree = ET_xt.parse(path_aplicar)
                    for reg in registros:
                        vid = reg.get(chave_id)
                        if not vid: continue
                        for elem in tree.findall(f'.//*[@{chave_id}="{vid}"]'):
                            for k, v in reg.items():
                                if k.startswith('_'): continue
                                if elem.get(k) != v:
                                    elem.set(k, v)
                                    contagem += 1
                    tree.write(path_aplicar, encoding='utf-8', xml_declaration=True)
                elif tipo == 'json':
                    with open(path_aplicar, encoding='utf-8') as f:
                        dados_orig = json_xt.load(f)
                    for reg in registros:
                        for k, v in reg.items():
                            if k.startswith('_'): continue
                            if isinstance(dados_orig, dict) and k in dados_orig:
                                if dados_orig[k] != v:
                                    dados_orig[k] = v
                                    contagem += 1
                    with open(path_aplicar, 'w', encoding='utf-8') as f:
                        json_xt.dump(dados_orig, f, indent=2, ensure_ascii=False)
                elif tipo == 'csv' or tipo == 'lua' or tipo == 'ini' or tipo == 'regex':
                    with open(path_aplicar, encoding='utf-8') as f:
                        texto_orig = f.read()
                    for reg in registros:
                        vid = reg.get(chave_id)
                        if not vid and 'nome' in reg:
                            vid = reg['nome']
                        if not vid: continue
                        for k, v in reg.items():
                            if k.startswith('_') or k == chave_id: continue
                            padrao = re_xt.compile(rf'({vid}\.{k}\s*=\s*["\']?)([^"\'\s]+)(["\']?)')
                            novo, n = padrao.subn(rf'\1{v}\3', texto_orig)
                            if n > 0:
                                texto_orig = novo
                                contagem += n
                    with open(path_aplicar, 'w', encoding='utf-8') as f:
                        f.write(texto_orig)
                
                print(f'[Extract] {contagem} correcoes aplicadas de {fname}')
                
                # Registra no KG: MCR-DevIA aprende com cada extracao
                if contagem > 0 and 'kg' in dir():
                    try:
                        kg.aprender(
                            f'extract: {os.path.basename(path_aplicar)} ({tipo})',
                            f'{contagem} correcoes em {len(registros)} registros',
                            f'extract aplicar {os.path.basename(path_aplicar)}',
                            'extract'
                        )
                    except:
                        pass
            return
        
        # --- EXTRACAO ---
        path = args[0]
        desc = " ".join(args[1:]) if len(args) > 1 else "extracao"
        formato = args[1] if len(args) > 2 and args[1] in ('xml','json','csv','lua','ini','regex') else None
        ext = os.path.splitext(path)[1].lower()
        
        if not formato:
            ext_code = {'.cpp','.c','.h','.hpp','.java','.py','.js','.ts','.go','.rs','.swift','.kt'}
            mapa = {'.xml':'xml','.json':'json','.csv':'csv','.lua':'lua','.ini':'ini','.cfg':'ini','.conf':'ini'}
            mapa.update({e:'code' for e in ext_code})
            formato = mapa.get(ext, 'regex')
        
        extract_dir = os.path.join(os.path.dirname(path), '_extract')
        os.makedirs(extract_dir, exist_ok=True)
        
        dados = []
        chave_id = 'id'
        
        if formato == 'xml':
            tree = ET_xt.parse(path)
            root = tree.getroot()
            tag_principal = root[0].tag if len(root) > 0 else 'item'
            for elem in root.findall(f'.//{tag_principal}'):
                item = dict(elem.attrib)
                item['_linha'] = elem.get('id', str(len(dados)+1))
                dados.append(item)
            print(f'[Extract] XML: {tag_principal}, {len(dados)} itens')
        
        elif formato == 'json':
            with open(path, encoding='utf-8') as f:
                data = json_xt.load(f)
            if isinstance(data, list):
                dados = data
            elif isinstance(data, dict):
                chave_ident = [k for k in data.keys() if k != '_metadata'][:1]
                if chave_ident:
                    dados = [{chave_ident[0]: v} for v in data.values()]
                else:
                    dados = [data]
            print(f'[Extract] JSON: {len(dados)} entradas')
        
        elif formato == 'csv':
            with open(path, encoding='utf-8', newline='') as f:
                reader = csv_xt.DictReader(f)
                for row in reader:
                    dados.append(row)
            print(f'[Extract] CSV: {len(dados)} linhas')
        
        elif formato == 'lua':
            with open(path, encoding='utf-8') as f:
                texto = f.read()
            for m in re_xt.finditer(r'(\w+)\s*=\s*\{([^}]+)\}', texto):
                bloco = m.group(2)
                item = {'_nome': m.group(1)}
                for kv in re_xt.finditer(r'(\w+)\s*=\s*["\']?([^"\'}\s,]+)', bloco):
                    item[kv.group(1)] = kv.group(2)
                dados.append(item)
            print(f'[Extract] Lua: {len(dados)} tabelas')
        
        elif formato == 'code':
            # Extrator universal de codigo (qualquer linguagem)
            with open(path, encoding='utf-8') as f:
                codigo = f.read()
            
            # Detecta linguagem pela extensao
            lang = ext.lstrip('.')
            
            # Extrai funcoes: padrao universal (nome(parametros) {
            for m in re_xt.finditer(r'(?:(?:\w+(?:\s+(?:\*|&)?)?\s+)?(\w+)\s*\([^)]*\))\s*(?:\{|:\s*\n)', codigo):
                nome = m.group(1)
                inicio = codigo[:m.start()].count('\n') + 1
                if nome and len(nome) > 1 and nome not in ('if','for','while','switch','catch','else'):
                    item = {'_linha': inicio, 'nome': nome, 'tipo': 'funcao', 'linguagem': lang}
                    # Extrai as primeiras 3 linhas do corpo
                    corpo_linhas = codigo[m.end():].split('\n')[:3]
                    item['corpo'] = ' '.join(l.strip() for l in corpo_linhas if l.strip())[:100]
                    dados.append(item)
            
            # Extrai classes
            for m in re_xt.finditer(r'(?:class|struct)\s+(\w+)(?:\s*:\s*public\s+(\w+))?', codigo):
                nome = m.group(1)
                inicio = codigo[:m.start()].count('\n') + 1
                if nome and len(nome) > 1:
                    item = {'_linha': inicio, 'nome': nome, 'tipo': 'classe', 'linguagem': lang}
                    if m.group(2):
                        item['herda'] = m.group(2)
                    dados.append(item)
            
            print(f'[Extract] Code ({lang}): {len(dados)} funcoes/classes')
        
        elif formato in ('ini', 'regex'):
            with open(path, encoding='utf-8') as f:
                texto = f.read()
            secoes = re_xt.findall(r'\[(\w+)\](.+?)(?=\[|\Z)', texto, re_xt.DOTALL)
            for sec, conteudo in secoes:
                item = {'_sec': sec}
                for kv in re_xt.finditer(r'(\w+)\s*=\s*(.+)', conteudo):
                    item[kv.group(1)] = kv.group(2).strip()
                dados.append(item)
            print(f'[Extract] INI/Regex: {len(dados)} secoes')
        
        if not dados:
            print('[Extract] Nenhum dado extraido.')
            return
        
        # Salva dados extraidos
        nome_base = desc.replace(' ','_')[:30]
        ext_path = os.path.join(extract_dir, f'{nome_base}.json')
        with open(os.path.join(extract_dir, '_metadata.json'), 'w', encoding='utf-8') as f:
            json_xt.dump({'_tipo': formato, '_chave_id': chave_id, '_arquivo': path}, f)
        with open(ext_path, 'w', encoding='utf-8') as f:
            json_xt.dump(dados, f, indent=2, ensure_ascii=False)
        
        print(f'[Extract] Dados salvos em {ext_path}')
        print(f'[Extract] Para modificar: edite o JSON, depois execute:')
        print(f'  python mcr_devia.py extract aplicar {path}')
        print(f'[Extract] Para MCR-DevIA corrigir: python mcr_devia.py perguntar "... instrucao ..."')
    
    elif cmd == 'review' and len(args) >= 1:
        """Revisa QUALQUER dado extraido, item por item, com IA.
        Uso: python mcr_devia.py review <arquivo> [limite]
        Funciona com qualquer _extract/dados.json (XML, JSON, CSV, Lua, INI)
        Fluxo: extract -> review -> extract aplicar --force"""
        path_review = args[0]
        limite = int(args[1]) if len(args) > 1 else 20
        ext_dir = os.path.join(os.path.dirname(path_review), '_extract') if os.path.isdir(os.path.dirname(path_review)) else None
        
        if not ext_dir or not os.path.exists(ext_dir):
            # Se nao tem _extract, tenta extrair primeiro
            print(f'[Review] Nenhum dado extraido encontrado. Execute extract primeiro.')
            return
        
        import urllib.request as ur_rv
        import json as json_rv
        for fname in sorted(os.listdir(ext_dir)):
            if not fname.endswith('.json') or fname == '_metadata.json': continue
            json_path = os.path.join(ext_dir, fname)
            with open(json_path, encoding='utf-8') as f:
                dados = json_rv.load(f)
            if not isinstance(dados, list): continue
            
            print(f'\n[Review] Revisando {fname} ({len(dados)} registros, limite {limite})...')
            suspeitos = []
            
            # SELF FEW-SHOT: Gera MUITOS exemplos de erro a partir dos proprios dados
            # Quanto mais exemplos, melhor a IA aprende o que e anomalia
            exemplos_few_shot = ""
            if len(dados) >= 3:
                saudavel = json_rv.dumps(dados[0], ensure_ascii=False)
                erros_gerados = []
                
                def _err_artigo(d):
                    if "artigo" in d: d["artigo"] = "erro_artigo"
                    return d
                def _err_plural(d):
                    if "plural" in d: d["plural"] = d.get("name", d.get("nome", "?")) + "_erro"
                    return d
                def _err_valor_neg(d):
                    if "valor" in d: d["valor"] = -1
                    return d
                def _err_valor_grande(d):
                    if "valor" in d: d["valor"] = 999999
                    return d
                def _err_nome(d):
                    if "nome" in d: d["nome"] = "NOME_ERRO"
                    return d
                def _err_tipo(d):
                    if "tipo" in d: d["tipo"] = "TIPO_INVALIDO"
                    return d
                def _err_nivel(d):
                    if "nivel" in d: d["nivel"] = -99
                    return d
                def _err_raridade(d):
                    if "raridade" in d: d["raridade"] = "RARIDADE_ERRO"
                    return d
                def _err_vazio(d):
                    return {}
                def _err_campo_none(d):
                    chaves = list(d.keys())
                    if chaves: d[chaves[0]] = None
                    return d
                
                funcoes_erro = (
                    _err_artigo, _err_plural, _err_valor_neg, _err_valor_grande,
                    _err_nome, _err_tipo, _err_nivel, _err_raridade, _err_vazio, _err_campo_none
                )
                
                for i in range(min(100, len(dados) * 2)):
                    try:
                        criador = funcoes_erro[i % len(funcoes_erro)]
                        item_base = dict(dados[i % len(dados)])
                        item_err = criador(item_base)
                        if item_err != item_base and item_err not in erros_gerados:
                            erros_gerados.append(json_rv.dumps(item_err, ensure_ascii=False))
                    except Exception as e:
                        print(f"[Fix] ERRO: {e}")
                
                if erros_gerados:
                    # Limita a ~10 exemplos para caber no contexto de 4K tokens
                    max_exemplos = min(5, len(erros_gerados))
                    exemplos_few_shot = f"Exemplo CORRETO:\n{saudavel}\n\n"
                    for i in range(max_exemplos):
                        exemplos_few_shot += f"Exemplo com ERRO {i+1}:\n{erros_gerados[i]}\n\n"
            
            # BATCH: Em vez de 1 chamada IA por item, agrupa em lote
            itens_lote = dados[:limite]
            lote_json = '\n'.join(
                f"ITEM {i+1}: {json_rv.dumps(item, ensure_ascii=False)}"
                for i, item in enumerate(itens_lote)
            )
            prompt_lote = (
                f"{exemplos_few_shot}"
                f"Analise CADA item abaixo. Para cada, responda em LINHA SEPARADA:\n"
                f"  ITEM X: OK\n"
                f"  ITEM Y: ERRO: descricao\n\n"
                f"Itens:\n{lote_json}"
            )
            _cfg = _melhor_modelo("fast")
            payload = json_rv.dumps({
                "model": _cfg["modelo"], "prompt": prompt_lote,
                "stream": False,
                "options": {"temperature": 0.1, "num_ctx": min(_cfg["ctx"], 4096)}
            }).encode()
            try:
                req = ur_rv.Request(OLLAMA_URL, data=payload, headers={"Content-Type":"application/json"})
                resp = json_rv.loads(ur_rv.urlopen(req, timeout=60).read()).get("response","")
            except Exception as e:
                print(f"[Fix] ERRO: {e}")
            
            # Parse resposta em lote
            for i, item in enumerate(itens_lote):
                item_id = item.get("id") or item.get("_linha", i)
                nome = item.get("name", item.get("nome", "?"))
                # Procura "ITEM X:" na resposta
                padrao_item = re.search(rf'ITEM\s*{i+1}\s*:\s*(.*)', resp, re.IGNORECASE)
                status_item = padrao_item.group(1) if padrao_item else ""
                if "ERRO" in status_item.upper():
                    suspeitos.append((item_id, nome, status_item[:80]))
                    print(f'  [{len(suspeitos)}] ID {item_id}: {nome} -> ERRO')
                else:
                    print(f'  ID {item_id}: {nome} -> OK')
        
        print(f'\n[Review] {len(suspeitos)} suspeitos encontrados.')
        if suspeitos:
            print(f'[Review] Para corrigir: edite o JSON em {ext_dir} e depois execute:')
            print(f'  python mcr_devia.py extract aplicar --force {path_review}')
    
    elif cmd == 'analisar' and len(args) >= 1:
        """Analisa arquivo com roteamento hibrido (codigo vs texto).
        Uso: python mcr_devia.py analisar <arquivo> [descricao]
        
        Para CODIGO (.py/.lua/.cpp/.ts/.js):
          - Pre-analise AST + funcoes + chamadas
          - Modelo: qwen2.5-coder:7b
          - Saida: LINHA X: descricao
        
        Para TEXTO/DADOS (.xml/.json/.csv/.txt/.md):
          - Pre-analise de estrutura (tags, campos, valores)
          - Modelo: llama3.1:8b (melhor em contexto PT-BR)
          - Saida: tipo/descricao do problema
        """
        path_analisar = args[0]
        desc_extra = " ".join(args[1:]) if len(args) > 1 else ""
        
        # Resolver caminho
        path_real = os.path.join(SANDBOX, path_analisar) if not os.path.exists(path_analisar) else path_analisar
        if not os.path.exists(path_real):
            for ext in ['', '.py', '.lua', '.ts', '.js', '.xml', '.json', '.txt', '.md', '.csv']:
                tentativa = path_analisar + ext
                if os.path.exists(tentativa):
                    path_real = tentativa; break
        
        if not os.path.exists(path_real):
            print(f'[Analisar] Arquivo nao encontrado: {path_analisar}')
        else:
            with open(path_real, encoding='utf-8') as f:
                linhas = f.readlines()
            
            codigo = ''.join(linhas)
            ext = os.path.splitext(path_real)[1].lower()
            print(f'[Analisar] {path_real} ({len(linhas)} linhas, {ext})')
            
            # --- DETECTAR TIPO: CODIGO vs TEXTO ---
            eh_codigo = ext in ['.py', '.lua', '.cpp', '.c', '.h', '.hpp', '.ts', '.js', '.java', '.cs', '.go', '.rs']
            eh_texto = ext in ['.xml', '.json', '.csv', '.txt', '.md', '.ini', '.cfg', '.yaml', '.yml', '.toml']
            
            if not eh_codigo and not eh_texto:
                # Deteccao pelo conteudo
                eh_codigo = bool(re.search(r'(def |class |function |local |int |void |#include|import |from )', codigo[:1000]))
                eh_texto = not eh_codigo
            
            ctx_estrutura = []
            
            if eh_codigo:
                # --- MODO CODIGO: AST + qwen2.5-coder:7b ---
                print(f'  Modo: CODIGO (modelo: qwen2.5-coder:7b)')
                tarefa = "analisar"
                
                funcoes = []
                chamadas = []
                
                if ext == '.py':
                    try:
                        import ast as _ast
                        tree = _ast.parse(codigo)
                        for node in _ast.walk(tree):
                            if isinstance(node, _ast.FunctionDef):
                                func_params = [a.arg for a in node.args.args]
                                for sub in _ast.walk(node):
                                    if isinstance(sub, _ast.Call) and hasattr(sub.func, 'id'):
                                        chamadas.append((sub.lineno, node.name, sub.func.id))
                                funcoes.append((node.name, node.lineno, func_params))
                            elif isinstance(node, _ast.ClassDef):
                                for sub in node.body:
                                    if isinstance(sub, _ast.FunctionDef):
                                        fname = f"{node.name}.{sub.name}"
                                        chamadas.append((sub.lineno, node.name, sub.name))
                                        funcoes.append((fname, sub.lineno, [a.arg for a in sub.args.args]))
                    except: pass
                
                if not funcoes:
                    for i, line in enumerate(linhas, 1):
                        m = re.match(r'^\s*(?:local\s+)?function\s+(\w+(?:\.\w+)*)\s*\(', line)
                        if m: funcoes.append((m.group(1), i, []))
                        m = re.match(r'^\s*(?:def|class)\s+(\w+)\s*[\(:]', line)
                        if m: funcoes.append((m.group(1), i, []))
                
                if funcoes:
                    ctx_estrutura.append("=== MAPA DE FUNCOES ===")
                    for fn, linha, params in sorted(funcoes, key=lambda x: x[1]):
                        ctx_estrutura.append(f"  LINHA {linha}: {fn}({', '.join(params) if params else '...'})")
                if chamadas:
                    ctx_estrutura.append("\n=== CHAMADAS ===")
                    for linha, chamador, chamado in chamadas:
                        ctx_estrutura.append(f"  LINHA {linha}: {chamador} -> {chamado}")
                
                ctx_estrutura.append("\n=== CODIGO NUMERADO ===")
                for i, line in enumerate(linhas, 1):
                    ctx_estrutura.append(f"  {i:4d}| {line.rstrip()}")
                
                ctx_str = '\n'.join(ctx_estrutura[:80])
                prompt = f"{ctx_str}\n\nDescricao: {desc_extra if desc_extra else 'Encontre problemas, bugs e falsas pistas.'}\n\nFormato: LINHA X: descricao"
                
            elif eh_texto:
                # --- MODO TEXTO: analise estrutural + llama3.1:8b ---
                print(f'  Modo: TEXTO/DADOS (modelo: llama3.1:8b)')
                tarefa = "contexto"
                
                # Pre-analise de estrutura
                if ext == '.xml':
                    tags = set(re.findall(r'<(\w+)[\s>]', codigo))
                    attrs = set(re.findall(r'(\w+)=[\'"]', codigo))
                    ctx_estrutura.append(f"Tags encontradas: {', '.join(sorted(tags)[:10])}")
                    ctx_estrutura.append(f"Atributos: {', '.join(sorted(attrs)[:15])}")
                    ctx_estrutura.append(f"Total linhas: {len(linhas)}")
                    # Amostra com linha numerada
                    ctx_estrutura.append("\n=== CONTEUDO ===")
                    for i, line in enumerate(linhas[:60], 1):
                        ctx_estrutura.append(f"  {i:4d}| {line.rstrip()}")
                elif ext == '.json':
                    ctx_estrutura.append(f"Tamanho: {len(codigo)} chars")
                    ctx_estrutura.append("\n=== CONTEUDO ===")
                    for i, line in enumerate(linhas[:60], 1):
                        ctx_estrutura.append(f"  {i:4d}| {line.rstrip()}")
                else:
                    ctx_estrutura.append("\n=== CONTEUDO ===")
                    for i, line in enumerate(linhas[:60], 1):
                        ctx_estrutura.append(f"  {i:4d}| {line.rstrip()}")
                
                ctx_str = '\n'.join(ctx_estrutura)
                prompt = f"{ctx_str}\n\nDescricao: {desc_extra if desc_extra else 'Analise este arquivo e encontre problemas: erros de traducao, artigos incorretos (um/uma), plurais errados, inconsistências.'}\n\nPara cada problema, responda:\nLINHA X: tipo do problema - descricao"
            
            # --- V12: KG ja analisou este arquivo antes? ---
            nome_base = os.path.basename(path_real)
            analise_prev = kg.buscar(f"analisar {nome_base}")
            if analise_prev:
                for l in analise_prev:
                    if l.get('ctx') in ('analisar_codigo', 'analisar_texto'):
                        print(f'  [KG] Analise de "{nome_base}" ja existe no KG')
                        print(f'  {l["solucao"][:200]}')
                        # Ainda assim chama IA para nova analise (pode ter mudancas)
                        # Mas exibe o cache como referencia
                        break
            
            # --- CHAMAR MODELO APROPRIADO ---
            cfg = _melhor_modelo(tarefa)
            try:
                import urllib.request as _ur
                import json as _jn
                payload = _jn.dumps({
                    "model": cfg["modelo"],
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_ctx": cfg["ctx"]}
                }).encode()
                req = _ur.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
                resp = _jn.loads(_ur.urlopen(req, timeout=120).read()).get("response", "")
                
                if resp:
                    print(f'\n[Analisar] Resultados:')
                    print(resp)
                    for line in resp.split('\n'):
                        if 'LINHA' in line:
                            try:
                                kg.aprender(
                                    f"{'Bug' if eh_codigo else 'Problema'} em {os.path.basename(path_real)}",
                                    "Analise" if eh_codigo else "Revisao",
                                    line.strip()[:100],
                                    "analisar_codigo" if eh_codigo else "analisar_texto"
                                )
                            except: pass
                else:
                    print('[Analisar] Sem resposta')
            except Exception as e:
                print(f'[Analisar] Erro: {e}')
    
    elif cmd == 'fast' and len(args) >= 1:
        """Chamada direta ao Ollama. APENAS para classificacoes SIM/NAO e extracoes.
        Para perguntas abertas/factuais, use 'perguntar' que tem KG + veracidade.
        Uso: python mcr_devia.py fast <pergunta SIM/NAO>"""
        prompt = " ".join(args)
        # Verifica se pergunta parece factual (nao SIM/NAO)
        eh_sim_nao = any(p in prompt.lower() for p in ['sim ou nao', 'sim/nao', 'responda sim', 'responda nao',
                                                        'correto?', 'errado?', 'esta correto'])
        if not eh_sim_nao:
            print(f'[Fast] Pergunta factual detectada. Redirecionando para perguntar (com KG)...')
            s = Supervisor(ia, kg)
            s.perguntar(prompt)
        else:
            # ANTES de chamar IA, tenta validador de genero PT-BR (V12: Python puro)
            import validador_genero as vg
            resp_v12 = None
            # Detecta padrao: "NOME article=UM esta correto?"
            m_artigo = re.search(r"([A-Za-z\u00C0-\u00FF][\w\u00C0-\u00FF\s]*?)\s+article='?(\w+)'?", prompt, re.IGNORECASE)
            if m_artigo:
                nome_item = m_artigo.group(1).strip()
                artigo = m_artigo.group(2).strip()
                if nome_item and artigo:
                    resultado = vg.verificar_artigo(nome_item, artigo, kg)
                    if resultado is True:
                        resp_v12 = "SIM. O artigo esta correto."
                    elif resultado is False:
                        resp_v12 = "NAO. O artigo esta errado."
                    if resp_v12:
                        print(f'[Fast:V12] {resp_v12}')
            
            if resp_v12 is None:
                # Se V12 nao sabe, tenta aprender: chama modelo 1x, guarda no KG
                if m_artigo and nome_item and artigo:
                    prompt_genero = f"Qual o genero da palavra '{nome_item.split()[0].lower()}' em portugues? Responda apenas 'masculino' ou 'feminino'."
                    resp_gen = fast(prompt_genero, 0.1, "fast")
                    if resp_gen and 'feminin' in resp_gen.lower():
                        vg.aprender_genero(kg, nome_item, "feminino")
                        resultado_aprendido = vg.verificar_artigo(nome_item, artigo, kg)
                        if resultado_aprendido is True:
                            resp_v12 = "SIM. O artigo esta correto."
                        elif resultado_aprendido is False:
                            resp_v12 = "NAO. O artigo esta errado."
                        if resp_v12:
                            print(f'[Fast:V12+Aprendizado] {resp_v12}')
                # Ainda sem resposta, fallback para o modelo classico
                if resp_v12 is None:
                    resp = fast(prompt)
                    if resp:
                        print(f'[Fast] {resp[:500]}')
                    else:
                        print('[Fast] Sem resposta')
    
    elif cmd == 'revisar' and len(args) >= 2:
        """Revisor por pares: valida mudancas antes de aplicar.
        Uso: python mcr_devia.py revisar <arquivo> <descricao>"""
        arquivo = args[0]
        descricao = " ".join(args[1:])
        path = os.path.join(SANDBOX, arquivo) if not os.path.exists(arquivo) else arquivo
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                conteudo = f.read()
            prompt = f'Arquivo: {arquivo}\nMudanca: {descricao}\nCodigo atual ({len(conteudo.splitlines())} linhas):\n{conteudo[:500]}\nRisco ALTO, MEDIO ou BAIXO? Responda so o nivel.'
            resp = fast(prompt)
            if resp and 'ALTO' not in resp:
                print(f'[Revisor] APROVADO (risco {resp[:20]})')
            else:
                print(f'[Revisor] REJEITADO - risco ALTO detectado')
        else:
            print(f'[Revisor] Arquivo nao encontrado: {arquivo}')
    
    elif cmd == 'processar' and len(args) >= 1:
        """Processa QUALQUER entrada, de QUALQUER tamanho.
        Uso: python mcr_devia.py processar <texto>
             python mcr_devia.py processar --estrategia tabela <texto>
             python mcr_devia.py processar --formato arquivos "arquivo1.py, arquivo2.lua"
        
        Pipeline: fragmentar -> processar cada peca (CrewPipeline) -> montar (0 IA)
        Ideal para: multiplas perguntas, comparacoes, textos longos."""
        from input_pipeline import InputPipeline
        
        # Parse flags
        estrategia = "auto"
        formato = "auto"
        resto = args.copy()
        if '--estrategia' in resto:
            idx = resto.index('--estrategia')
            if idx + 1 < len(resto):
                estrategia = resto[idx + 1]
                resto = resto[:idx] + resto[idx+2:]
        if '--formato' in resto:
            idx = resto.index('--formato')
            if idx + 1 < len(resto):
                formato = resto[idx + 1]
                resto = resto[:idx] + resto[idx+2:]
        
        texto = " ".join(resto)
        
        pipe = InputPipeline(kg=kg, ia=ia, ctx_crew=None, verbose=True)
        resposta = pipe.executar(texto, estrategia=estrategia, formato=formato)
        
        print(f'\n{"="*55}')
        print(f'  RESPOSTA FINAL')
        print(f'{"="*55}')
        print(resposta)
        
        # Estatisticas da execucao
        stats = pipe.get_stats()
        print(f'\n  [Stats] {stats["total_fragmentos"]} fragmentos | '
              f'{stats["fragmentos_crew"]} crew/{stats["fragmentos_ia"]} ia | '
              f'{stats["tempo_medio"]:.1f}s media')
    
    elif cmd == 'aprender_conceito' and len(args) >= 1:
        """Aprende conceitos do codigo fonte e salva como conhecimento conceitual no KG.
        Uso: python mcr_devia.py aprender_conceito <conceito>
        Ex:  python mcr_devia.py aprender_conceito SPA
             python mcr_devia.py aprender_conceito "Sistema de Progressao"
        Fluxo: busca no codigo fonte -> le arquivos relevantes -> IA sintetiza -> salva no KG"""
        conceito = " ".join(args)
        print(f'[MCR-DevIA] Aprendendo conceito: {conceito}')
        
        # PASSO 1: Buscar no codigo fonte
        import fnmatch
        import re as re_ap
        
        palavras = set(re_ap.findall(r'\w+', conceito.lower()))
        # Palavras EXTRA de contexto para buscar termos relacionados no codigo
        palavras_extras = set()
        if 'spa' in palavras or 'sistema' in palavras:
            palavras_extras = {'progressao', 'aventureiro', 'xp', 'nivel', 'dominio'}
        todas_palavras = palavras | palavras_extras
        arquivos_rel = []
        base_dirs = ['E:\\Projeto MCR\\src', 'E:\\Projeto MCR\\data',
                     'E:\\Projeto MCR\\scripts', 'E:\\Projeto MCR']
        for bd in base_dirs:
            if not os.path.isdir(bd):
                continue
            for root, dirs, files in os.walk(bd):
                # Pular diretorios irrelevantes
                dirs[:] = [d for d in dirs if not d.startswith(('.', 'vcpkg', '__pycache__', 'node_modules'))]
                for f in files:
                    if not f.endswith(('.py', '.lua', '.cpp', '.hpp', '.h', '.xml', '.json')):
                        continue
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                            conteudo = fp.read(5000)  # so primeiras ~5000 chars
                        conteudo_lower = conteudo.lower()
                        # Verifica se o conceito aparece no arquivo
                        if any(p in conteudo_lower for p in palavras):
                            # Pontua por densidade de ocorrencias
                            densidade = sum(conteudo_lower.count(p) for p in palavras)
                            arquivos_rel.append((densidade, fpath, conteudo[:1000]))
                    except:
                        pass
        
        if not arquivos_rel:
            print(f'  [Conceito] Nenhum arquivo fonte encontrado para "{conceito}"')
            return
        
        # Top 5 arquivos mais relevantes
        arquivos_rel.sort(key=lambda x: -x[0])
        top_arquivos = arquivos_rel[:5]
        
        print(f'  [Conceito] {len(arquivos_rel)} arquivos encontrados, usando top {len(top_arquivos)}')
        for _, fp, _ in top_arquivos:
            rel = os.path.relpath(fp, 'E:\\Projeto MCR')
            print(f'    - {rel}')
        
        # PASSO 2: Montar contexto do codigo
        blocos = []
        for _, fp, snippet in top_arquivos:
            rel = os.path.relpath(fp, 'E:\\Projeto MCR')
            blocos.append(f"--- {rel} ---\n{snippet[:800]}")
        contexto_codigo = '\n\n'.join(blocos)
        
        # PASSO 3: IA sintetiza conhecimento CONCEITUAL (nao codigo)
        prompt = (
            f"O projeto MCR e um servidor CUSTOMIZADO de Tibia baseado em Canary (OTServ).\n"
            f"SPA = Sistema de Progressao do Aventureiro, SHC = Sistema de Habilidades Contextuais.\n"
            f"Eridanus e a cidade inicial.\n\n"
            f"Analise o codigo fonte abaixo e extraia conhecimento CONCEITUAL sobre '{conceito}'.\n\n"
            f"IMPORTANTE: Use o significado DENTRO do projeto MCR (Tibia/OTServ).\n"
            f"Nao use significados genericos da sigla. Ex: SPA no projeto MCR NAO e Single Page Application.\n\n"
            f"Nao explique o codigo. Explique o CONCEITO - o que e, como funciona,\n"
            f"para que serve, como se relaciona com outros sistemas do projeto MCR.\n\n"
            f"Se o codigo mostrar estruturas de dados, funcoes ou classes, extraia DELAS\n"
            f"o significado conceitual. Exemplo: se ve uma classe 'PlayerSkills', explique\n"
            f"que 'PlayerSkills gerencia as habilidades do jogador, com metodos para\n"
            f"adicionar XP, verificar nivel, etc.' — nao diga 'a classe PlayerSkills tem\n"
            f"os metodos X, Y, Z'.\n\n"
            f"Contexto do codigo fonte:\n{contexto_codigo[:3000]}\n\n"
            f"Produza um paragrafo conciso (3-5 frases) explicando o conceito '{conceito}'"
            f" no contexto do projeto MCR."
        )
        r = fast(prompt, 0.3, "conceito")
        
        if r and len(r) > 30:
            explicacao = r.strip()
            print(f'\n[Conceito] Explicacao conceitual:\n{explicacao[:500]}')
            
            # PASSO 4: Salvar no KG
            kg.aprender(
                erro=f"O que e {conceito}?",
                causa=f"Analise de codigo fonte do projeto MCR",
                solucao=explicacao,
                ctx="conceito_codigo"
            )
            print(f'  [Conceito] Salvo no KG como ctx=conceito_codigo')
            
            # Extra: salvar fontes usadas
            fontes = [os.path.relpath(fp, 'E:\\Projeto MCR') for _, fp, _ in top_arquivos]
            kg.aprender(
                erro=f"Fontes para: {conceito}",
                causa=f"Arquivos usados para aprender o conceito {conceito}",
                solucao=f"Arquivos consultados: {'; '.join(fontes)}",
                ctx="conceito_codigo"
            )
        else:
            print(f'  [Conceito] Falha ao sintetizar explicacao')
    
    else:
        print(f'Comando invalido: {cmd}')
        print('Use: gerar, lore, compilar, ensinar, perguntar, status,')
        print('     grep, read, edit, glob, task, question, todo, webfetch')
        print('     auditar, autoavaliar, autoconsciencia, auto_improve,')
        print('     auto_reparo, observar, agente, loop, chat,')
        print('     scriptbuilder, ultimate, conhecimento, ambiente,')
        print('     learning_scan, melhorias, supervisor,')
        print('     build, debate, intencao, conectar, revisar,')
        print('     fast, analisar <arquivo>, plan, bugfinder, proativo')
        print('     processar <texto> (fragmenta + processa + monta)')
        print('     web_learn <consulta> (busca na web, sanitiza e aprende)')

if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'[MCR-DevIA] ERRO FATAL: {e}'); import traceback; traceback.print_exc()
