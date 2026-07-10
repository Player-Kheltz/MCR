#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCR-DevIA v2 — Markov decide, LLM gera
======================================
Principio: Markov e 1.000.000x mais rapido que LLM para decisoes.
So chama o LLM para GERACAO de texto.

Arquitetura:
  Entrada → Decider Markov (0.000004s) → Se conhece: resposta direta
                                      → Se nao conhece: LLM gera (10-30s)
                                                      → Markov aprende para prox

Uso:
    python mcr_devia_v2.py                          # modo interativo
    python mcr_devia_v2.py "gerar codigo em python" # pergunta direta
    python mcr_devia_v2.py --llm                    # forcar uso de LLM
    python mcr_devia_v2.py --status                 # estatisticas
"""
import sys, os, json, math, time, re, hashlib

# Compatibilidade: MCRByteUtils do novo MCRFingerprint
try:
    from MCR import MCRFingerprint
    class _MCRByteUtils:
        @staticmethod
        def fingerprint(texto, dim=16):
            fp = MCRFingerprint.gerar(texto)
            return (fp * (dim // 8 + 1))[:dim]
        @staticmethod
        def similaridade_cosseno(a, b):
            dot = sum(x*y for x,y in zip(a,b))
            na = sum(x*x for x in a)**0.5
            nb = sum(y*y for y in b)**0.5
            return dot/(na*nb) if na*nb else 0
    MCRByteUtils = _MCRByteUtils
except:
    from MCR import MCRByteUtils  # fallback legado

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ─── Carrega MCR Engine (0 LLM, 0 GPU, rapido) ───────────────────
MCR_PATH = os.path.join(BASE, "MCR.py")
with open(MCR_PATH, encoding="utf-8") as f:
    _mcr_code = f.read().split("def main():")[0]
exec(compile(_mcr_code, "MCR.py", "exec"))

# ─── Tenta carregar LLM (Ollama, opcional) ──────────────────────
_ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
_HAS_LLM = False
_MODELO_PESADO = "qwen2.5-coder:14b"
_MODELO_LEVE = "qwen2.5-coder:7b"

try:
    import urllib.request as _ur
    _ur.urlopen("http://localhost:11434", timeout=2)
    _HAS_LLM = True
except:
    pass

# ─── Markov Decider (decide TUDO sem LLM) ───────────────────────

class MarkovDecider:
    """Classificador universal via Markov puro (0 LLM, 0.000004s).
    
    Aprende pergunta→classe com o uso.
    Depois de N exemplos, substitui completamente o LLM para classificacao.
    
    Uso:
        md = MarkovDecider()
        md.aprender("cria um jogo em python", "criar_codigo")
        classe = md.classificar("faca um jogo de plataforma")
        # → "criar_codigo" (por similaridade com exemplo anterior)
    """
    
    CLASSES = [
        "criar_codigo", "explicar_conceito", "gerar_texto",
        "analisar_codigo", "busca_informacao", "conversa",
        "planejar_tarefa", "depurar_erro", "escrever_documento",
        "comando_sistema", "criar_sql", "desconhecido",
    ]
    
    def __init__(self):
        self.mk = MCR("decider")
        self.thr = MCRThreshold("decider_conf")
        self.total = 0
        self._carregar()
    
    def _normalizar(self, texto):
        """Normaliza pergunta para usar como estado Markov."""
        t = texto.lower().strip()
        t = re.sub(r'[^\w\s]', '', t)[:100]
        # Pega as primeiras 3 palavras como fingerprint do estado
        palavras = t.split()[:3]
        return "_".join(palavras) if palavras else t
    
    def aprender(self, pergunta, classe):
        """Aprende que pergunta_normalizada → classe."""
        estado = self._normalizar(pergunta)
        self.mk.aprender(estado, classe)
        self.total += 1
        # Alimenta threshold com a confianca (1.0 = aprendizado direto)
        self.thr.observar(1.0)
        self._salvar()
    
    def classificar(self, pergunta, top_k=3):
        """Classifica pergunta via Markov.
        
        Retorna (classe, confianca).
        Se confianca < threshold, retorna ("desconhecido", conf).
        """
        estado = self._normalizar(pergunta)
        # Tenta match exato
        pred, conf = self.mk.predizer(estado)
        if pred and conf > 0.1:
            return pred, conf
        
        # Tenta match parcial (prefixos)
        for i in range(len(estado)-1, 0, -1):
            prefixo = estado[:i]
            p, c = self.mk.predizer(prefixo)
            if p and c > 0.15:
                return p, c * 0.8  # penaliza match parcial
        
        # Tenta por similaridade de fingerprint
        fp_pergunta = MCRByteUtils.fingerprint(pergunta, 16)
        melhor_classe = "desconhecido"
        melhor_conf = 0.0
        for estado_known in self.mk.freq:
            fp_known = MCRByteUtils.fingerprint(estado_known, 16)
            sim = MCRByteUtils.similaridade_cosseno(fp_pergunta, fp_known)
            if sim > melhor_conf:
                pred, _ = self.mk.predizer(estado_known)
                if pred:
                    melhor_classe = pred
                    melhor_conf = sim * 0.5  # penaliza similaridade
    
        return melhor_classe, min(melhor_conf, 0.9)
    
    def _salvar(self):
        path = os.path.join(CACHE_DIR, "decider_markov.json")
        try:
            with open(path, "w") as f:
                json.dump({
                    "trans": {str(k): v for k, v in self.mk.transicoes.items()},
                    "freq": {str(k): int(v) for k, v in self.mk.freq.items()},
                    "total": self.total,
                }, f)
        except:
            pass
    
    def _carregar(self):
        path = os.path.join(CACHE_DIR, "decider_markov.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    d = json.load(f)
                for k, v in d.get("trans", {}).items():
                    self.mk.transicoes[str(k)] = {str(k2): int(v2) for k2, v2 in v.items()}
                for k, v in d.get("freq", {}).items():
                    self.mk.freq[str(k)] = int(v)
                self.total = d.get("total", 0)
            except:
                pass
    
    def stats(self):
        return {
            "total_aprendido": self.total,
            "estados_unicos": len(self.mk.freq),
            "confianca_media": self.thr.calcular() if len(self.thr.obs) >= 3 else 0.5,
        }

# ─── Auto-Validation por Entropia ────────────────────────────────

class EntropyValidator:
    """Valida resposta por similaridade de fingerprint entre pergunta e resposta.
    
    Se similaridade < threshold = possivel alucinacao (resposta fora do contexto).
    Se similaridade >= threshold = resposta consistente com a pergunta.
    
    Substitui AutoRevisor (que chamava LLM para detectar alucinacao).
    Agora e 0.0005s vs 3-5s antes.
    """
    
    def __init__(self):
        self.thr = MCRThreshold("validador_sim")
    
    def validar(self, pergunta, resposta, contexto=""):
        """Valida resposta por similaridade de fingerprint.
        
        Retorna: {
            "valida": bool,
            "similaridade": float,
            "alerta": str or None
        }
        """
        if not resposta or len(resposta.strip()) < 5:
            return {"valida": False, "similaridade": 0.0, "alerta": "resposta_vazia"}
        
        # Fingerprint da pergunta e resposta
        fp_p = MCRByteUtils.fingerprint(pergunta, 16)
        fp_r = MCRByteUtils.fingerprint(resposta, 16)
        sim = MCRByteUtils.similaridade_cosseno(fp_p, fp_r)
        
        # Se tem contexto, verifica tambem
        sim_ctx = 0.0
        if contexto and len(contexto.strip()) > 10:
            fp_ctx = MCRByteUtils.fingerprint(contexto, 16)
            sim_ctx = MCRByteUtils.similaridade_cosseno(fp_ctx, fp_r)
        
        limiar_sim = self.thr.obter("limiar_similaridade", 0.15)
        alerta = None
        
        if sim < limiar_sim:
            alerta = "baixa_similaridade_pergunta_resposta"
        
        self.thr.observar(sim)
        
        return {
            "valida": alerta is None,
            "similaridade": round(sim, 4),
            "similaridade_contexto": round(sim_ctx, 4),
            "alerta": alerta,
        }
    
    def stats(self):
        return {
            "limiar_atual": self.thr.obter("limiar_similaridade", 0.15),
            "observacoes": len(self.thr.obs),
        }

# ─── LLM Interface (Ollama, so para geracao) ─────────────────────

class LLM:
    """LLM interface — SO para geracao de texto.
    
    0 classificacao, 0 reflexao, 0 validacao.
    So o que LLM faz bem: gerar texto.
    """
    
    def __init__(self):
        self.ultima_chamada = 0
        self.total_chamadas = 0
        self.tempo_total = 0.0
    
    def disponivel(self):
        return _HAS_LLM
    
    def gerar(self, prompt, modelo=None, ctx=4096, temp=0.3):
        """Gera texto via LLM local (Ollama)."""
        if not _HAS_LLM:
            return "[LLM indisponivel. Use --llm para forçar se Ollama estiver rodando.]"
        
        modelo = modelo or _MODELO_LEVE
        payload = json.dumps({
            "model": modelo,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": ctx,
                "temperature": temp,
            }
        }).encode()
        
        t0 = time.time()
        try:
            req = _ur.Request(_ollama_url, data=payload,
                            headers={"Content-Type": "application/json"})
            with _ur.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                texto = result.get("response", "")
        except Exception as e:
            return f"[Erro LLM: {e}]"
        
        self.total_chamadas += 1
        self.tempo_total += time.time() - t0
        return texto
    
    def stats(self):
        return {
            "disponivel": _HAS_LLM,
            "total_chamadas": self.total_chamadas,
            "tempo_medio": round(self.tempo_total / max(self.total_chamadas, 1), 2),
        }

# ─── MCR-DevIA v2 Core ────────────────────────────────────────────

class MCRDevIAV2:
    """MCR-DevIA v2 — Markov decide, LLM gera.
    
    Pipeline:
    1. MarkovDecider classifica pergunta (0.000004s)
    2. Se classe conhecida E confianca > threshold:
       → Resposta direta (template ou cache)
    3. Senao:
       → LLM gera resposta (10-30s)
       → Markov aprende pergunta→resumo→classe
       → EntropyValidator valida resposta
    4. Aprende: cada uso melhora o Markov para proxima vez.
    """
    
    def __init__(self):
        self.decider = MarkovDecider()
        self.validator = EntropyValidator()
        self.llm = LLM()
        self.cache_respostas: dict = {}
        self.cache_hits = 0
        self.cache_total = 0
        self._carregar_cache()
    
    def processar(self, pergunta, forcar_llm=False):
        """Processa uma pergunta e retorna resposta."""
        t0 = time.time()
        
        # 1. Normaliza
        pergunta = pergunta.strip()
        if not pergunta:
            return ""
        
        # 2. Cache de respostas (hash da pergunta)
        self.cache_total += 1
        hash_p = hashlib.md5(pergunta.encode()).hexdigest()[:16]
        if hash_p in self.cache_respostas:
            self.cache_hits += 1
            return self.cache_respostas[hash_p]
        
        # 3. Markov decide classe
        classe, conf = self.decider.classificar(pergunta)
        tempo_markov = time.time() - t0
        
        # 4. Se Markov sabe com confianca, tenta responder sem LLM
        if conf > 0.3 and not forcar_llm:
            # Busca no cache de respostas similares
            fp_p = MCRByteUtils.fingerprint(pergunta, 16)
            melhor_resp = None
            melhor_sim = conf * 0.5
            for h, (p_, r_, c_) in self.cache_respostas.items():
                fp_c = MCRByteUtils.fingerprint(p_, 16)
                sim = MCRByteUtils.similaridade_cosseno(fp_p, fp_c)
                if sim > melhor_sim and c_ == classe:
                    melhor_sim = sim
                    melhor_resp = r_
            
            if melhor_resp:
                self.cache_hits += 1
                resultado = {
                    "resposta": melhor_resp,
                    "classe": classe,
                    "confianca": round(melhor_sim, 3),
                    "tempo": round(time.time() - t0, 4),
                    "fonte": "cache_markov",
                    "llm_usado": False,
                }
                return resultado
        
        # 5. LLM gera (so se necessario)
        if self.llm.disponivel() or forcar_llm:
            prompt = self._montar_prompt(pergunta, classe)
            resposta = self.llm.gerar(prompt)
            tempo_total = time.time() - t0
            
            # 6. Valida por entropia
            validacao = self.validator.validar(pergunta, resposta)
            
            # 7. Aprende para proxima vez
            self.decider.aprender(pergunta, classe)
            
            # 8. Cache
            self.cache_respostas[hash_p] = (pergunta, resposta, classe)
            if len(self.cache_respostas) > 1000:
                # Descarta metade das mais antigas
                itens = list(self.cache_respostas.items())
                for k, _ in itens[:500]:
                    del self.cache_respostas[k]
            self._salvar_cache()
            
            resultado = {
                "resposta": resposta,
                "classe": classe,
                "confianca": round(conf, 3),
                "tempo": round(tempo_total, 4),
                "tempo_markov": round(tempo_markov, 6),
                "fonte": "llm" if self.llm.disponivel() else "markov",
                "llm_usado": True,
                "validacao": validacao,
            }
            return resultado
        
        # Fallback: Markov tenta responder mesmo sem LLM
        resultado = {
            "resposta": f"[Classe detectada: {classe} (conf={conf:.2f}). LLM indisponivel para gerar resposta.]",
            "classe": classe,
            "confianca": round(conf, 3),
            "tempo": round(time.time() - t0, 4),
            "fonte": "markov_fallback",
            "llm_usado": False,
        }
        return resultado
    
    def _montar_prompt(self, pergunta, classe):
        """Monta prompt para o LLM baseado na classe detectada."""
        templates = {
            "criar_codigo": (
                "Gere codigo Python para: {pergunta}\n"
                "Responda APENAS com o codigo, sem explicacoes.\n"
                "Use Python puro, sem bibliotecas externas."
            ),
            "explicar_conceito": (
                "Explique o conceito de '{pergunta}' de forma clara e concisa.\n"
                "Use analogias se possivel. Maximo 3 paragrafos."
            ),
            "analisar_codigo": (
                "Analise o seguinte codigo/ideia: {pergunta}\n"
                "Aponte problemas, sugestoes de melhoria e boas praticas."
            ),
            "gerar_texto": (
                "Escreva um texto sobre: {pergunta}\n"
                "Seja criativo e bem estruturado."
            ),
            "depurar_erro": (
                "O seguinte erro ocorreu: {pergunta}\n"
                "Explique a causa e como corrigir."
            ),
            "planejar_tarefa": (
                "Crie um plano passo-a-passo para: {pergunta}\n"
                "Seja pratico e especifico."
            ),
            "conversa": (
                "{pergunta}\n"
                "Responda de forma natural e conversacional."
            ),
            "busca_informacao": (
                "Sobre: {pergunta}\n"
                "Forneca informacoes precisas e baseadas em fatos."
            ),
            "escrever_documento": (
                "Escreva um documento sobre: {pergunta}\n"
                "Estruturado com secoes, claro e completo."
            ),
            "comando_sistema": (
                "Comando solicitado: {pergunta}\n"
                "Explique o comando e seu uso."
            ),
        }
        template = templates.get(classe, templates["conversa"])
        return template.format(pergunta=pergunta)
    
    def _salvar_cache(self):
        path = os.path.join(CACHE_DIR, "respostas_cache.json")
        try:
            serial = {k: v for k, (p, r, c) in self.cache_respostas.items()
                     for v in [(p, r, c)]}
            # So salva os 200 mais recentes
            itens = list(self.cache_respostas.items())[-200:]
            serial = {k: {"p": p, "r": r, "c": c} for k, (p, r, c) in itens}
            with open(path, "w") as f:
                json.dump(serial, f)
        except:
            pass
    
    def _carregar_cache(self):
        path = os.path.join(CACHE_DIR, "respostas_cache.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    d = json.load(f)
                for k, v in d.items():
                    self.cache_respostas[k] = (v["p"], v["r"], v["c"])
            except:
                pass
    
    def stats(self):
        return {
            "decider": self.decider.stats(),
            "validator": self.validator.stats(),
            "llm": self.llm.stats(),
            "cache": {
                "total": len(self.cache_respostas),
                "hits": self.cache_hits,
                "total_consultas": self.cache_total,
                "taxa_hit": round(self.cache_hits / max(self.cache_total, 1) * 100, 1),
            },
        }

# ─── NO-LLM QA (testes sem dependencia externa) ───────────────────

class NoLLMQA:
    """Responde perguntas CMA do conhecimento aprendido, sem LLM.
    
    Usa Markov + cache + fingerprints.
    Para testes e demonstracao sem Ollama.
    """
    
    def __init__(self):
        self.mk = MCR("qa")
        self.respostas: dict = {}
        self._carregar()
    
    def aprender(self, pergunta, resposta):
        estado = pergunta.lower().strip()[:80]
        self.mk.aprender(estado, resposta[:200])
        self.respostas[hashlib.md5(estado.encode()).hexdigest()[:16]] = resposta
        self._salvar()
    
    def perguntar(self, pergunta):
        estado = pergunta.lower().strip()[:80]
        # Match exato
        pred, conf = self.mk.predizer(estado)
        if pred and conf > 0.1:
            return pred, conf
        
        # Match por fingerprint
        fp_p = MCRByteUtils.fingerprint(pergunta, 16)
        melhor_resp = None
        melhor_conf = 0.0
        for hash_k, resp in self.respostas.items():
            fp_r = MCRByteUtils.fingerprint(resp[:100], 16)
            sim = MCRByteUtils.similaridade_cosseno(fp_p, fp_r)
            estado_k = None
            for e in self.mk.freq:
                if hashlib.md5(e.encode()).hexdigest()[:16] == hash_k:
                    estado_k = e
                    break
            if estado_k:
                p, c = self.mk.predizer(estado_k)
                score = sim * c
                if score > melhor_conf:
                    melhor_conf = score
                    melhor_resp = resp
        
        if melhor_resp and melhor_conf > 0.1:
            return melhor_resp, round(melhor_conf, 3)
        return None, 0.0
    
    def _salvar(self):
        path = os.path.join(CACHE_DIR, "no_llm_qa.json")
        try:
            with open(path, "w") as f:
                json.dump({
                    "trans": {str(k): v for k,v in self.mk.transicoes.items()},
                    "freq": {str(k): int(v) for k,v in self.mk.freq.items()},
                    "respostas": self.respostas,
                }, f)
        except: pass
    
    def _carregar(self):
        path = os.path.join(CACHE_DIR, "no_llm_qa.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    d = json.load(f)
                for k,v in d.get("trans",{}).items():
                    self.mk.transicoes[k] = {k2:int(v2) for k2,v2 in v.items()}
                for k,v in d.get("freq",{}).items():
                    self.mk.freq[k] = int(v)
                self.respostas = d.get("respostas", {})
            except: pass
    
    def stats(self):
        return {
            "perguntas_conhecidas": len(self.mk.freq),
            "respostas_cache": len(self.respostas),
        }

# ─── Seed de conhecimento inicial (para testes sem LLM) ──────────

def _seed_knowledge(qa):
    """Alimenta conhecimento basico para testes sem LLM."""
    seeds = [
        ("o que e MCR", "MCR e um sistema de Markov multi-nivel que opera em multiplas dimensoes simultaneamente."),
        ("o que e python", "Python e uma linguagem de programacao de alto nivel, interpretada e multiparadigma."),
        ("como criar uma funcao", "Use 'def nome_funcao(parametros):' seguido do corpo identado."),
        ("o que e uma variavel", "Variavel e um nome que armazena um valor na memoria."),
        ("o que e um loop for", "For e uma estrutura de repeticao que itera sobre uma sequencia."),
        ("o que e inteligencia artificial", "IA e a simulacao de processos de inteligencia humana por maquinas."),
        ("como debuggar codigo", "Use print() para inspecionar variaveis, ou um debugger como pdb."),
        ("o que e git", "Git e um sistema de controle de versao distribuido."),
        ("o que e um algoritmo", "Algoritmo e uma sequencia finita de passos para resolver um problema."),
        ("o que e markov", "Markov e um modelo probabilistico que prediz o proximo estado baseado no atual."),
    ]
    for p, r in seeds:
        qa.aprender(p, r)

# ─── CLI ──────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    
    if "--status" in args:
        dev = MCRDevIAV2()
        print(json.dumps(dev.stats(), indent=2))
        return
    
    forcar_llm = "--llm" in args
    perguntas = [a for a in args if not a.startswith("--")]
    
    if perguntas:
        dev = MCRDevIAV2()
        for p in perguntas:
            r = dev.processar(p, forcar_llm=forcar_llm)
            if isinstance(r, dict):
                print(f"  [{r['classe']} conf={r['confianca']}] {r.get('resposta', '')[:200]}")
                if r.get('llm_usado'):
                    print(f"  (LLM usado, {r['tempo']:.2f}s, validacao={'OK' if r.get('validacao',{}).get('valida') else '?'})")
                else:
                    print(f"  (cache, {r['tempo']:.4f}s)")
            else:
                print(r[:200])
        return
    
    # Modo interativo
    print("MCR-DevIA v2 — Markov decide, LLM gera")
    print("Digite 'sair' para encerrar")
    print("Comandos: /status, /seed, /llm (forcar LLM)")
    print()
    
    dev = MCRDevIAV2()
    qa = NoLLMQA()
    _seed_knowledge(qa)
    
    while True:
        try:
            e = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAte logo!")
            break
        
        if not e:
            continue
        if e.lower() in ("sair", "exit", "quit"):
            break
        if e == "/status":
            print(json.dumps(dev.stats(), indent=2))
            continue
        if e == "/seed":
            _seed_knowledge(qa)
            print(f"Conhecimento semeado: {qa.stats()['perguntas_conhecidas']} perguntas")
            continue
        if e == "/llm":
            forcar_llm = not forcar_llm
            print(f"Forcar LLM: {forcar_llm}")
            continue
        
        # Tenta NoLLMQA primeiro (mais rapido)
        resp, conf = qa.perguntar(e)
        if resp and conf > 0.3:
            print(f"  [QA conf={conf:.2f}] {resp}")
            continue
        
        # MCR-DevIA v2
        r = dev.processar(e, forcar_llm=forcar_llm)
        if isinstance(r, dict):
            resp_texto = r.get("resposta", "")
            fonte = r.get("fonte", "?")
            tempo = r.get("tempo", 0)
            llm = " [LLM]" if r.get("llm_usado") else ""
            val = r.get("validacao", {})
            val_tag = f" val={val.get('valida', '?')}" if val else ""
            print(f"  [{r['classe']} {fonte}{llm} {tempo:.2f}s{val_tag}]")
            print(f"  {resp_texto[:500]}")
        else:
            print(f"  {r[:500]}")
        
        # Aprende para NoLLM tambem
        if isinstance(r, dict) and r.get("resposta"):
            qa.aprender(e, r["resposta"][:200])

if __name__ == "__main__":
    main()
