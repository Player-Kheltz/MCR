#!/usr/bin/env python3
"""evolution.py — Spawning, expansion, fuel, and auto-improvement.

Mecanismos de expansão: workers paralelos, fuel (auto-alimentação),
expansão de conhecimento, e melhoria contínua.
"""
import os, json, math, time as _time

from .engine import MCR, MCRBridge
from .decisor import MCRDecisor, MCRPesoNota, MCRThreshold


class MCRTarefa:
    """UMA tarefa que o MCR decide executar."""
    
    def __init__(self, nome: str, fn, args: dict = None):
        self.nome = nome
        self.fn = fn
        self.args = args or {}
        self.resultado = None
        self.erro = None
        self.tempo = 0.0
    
    def executar(self):
        import time as _t
        t0 = _t.time()
        try:
            self.resultado = self.fn(**self.args)
        except Exception as e:
            self.erro = str(e)[:100]
        self.tempo = _t.time() - t0
        return self


class MCRWorker:
    """UM MCR que executa UMA MCRTarefa."""
    
    def __init__(self, tarefa: MCRTarefa):
        self.tarefa = tarefa
        self.mk = MCR(f"worker_{tarefa.nome}")
        from .memory import MCRConector
        self.conector = MCRConector()
        self.resultado = None
        self.nota = 0
        self.erro = None
        self.tempo = 0
    
    def executar(self):
        import time
        t0 = time.time()
        try:
            self.tarefa.executar()
            self.resultado = self.tarefa.resultado
            self.erro = self.tarefa.erro
            self.nota = 10 if self.erro is None else 0
            if self.resultado and not self.erro:
                self.mk.aprender(f"OK:{self.tarefa.nome}", f"t:{int(time.time()-t0)}")
        except Exception as e:
            self.erro = str(e)[:50]
            self.mk.aprender(f"ERRO:{self.tarefa.nome[:30]}", str(e)[:30])
        self.tempo = time.time() - t0
        return self


class MCRSpawner:
    """Cria workers em threads. MCR decide quantos e distribui."""
    
    def __init__(self):
        self.mk = MCR("spawner")
        self.mk_nworkers = MCR('n_workers')
        self.workers = []
        for _n in [(10, 2), (50, 4), (100, 8), (500, 12)]:
            self.mk_nworkers.aprender(f"n:{_n[0]}", str(_n[1]))
    
    def decidir_n_workers(self, n_tarefas: int, tempo_medio: float = 0.0) -> int:
        if n_tarefas <= 0:
            return 1
        bucket = int(n_tarefas / 10) * 10
        pred = self.mk_nworkers.predizer(f"n:{bucket}")
        if pred[0] is not None and pred[1] > 0.3:
            try:
                return max(1, min(32, int(str(pred[0]))))
            except:
                pass
        n = max(1, min(16, n_tarefas // 10))
        self.mk_nworkers.aprender(f"n:{bucket}", str(n))
        return n
    
    def spawnar(self, tarefas: list, n_workers: int = None) -> list:
        import threading
        import math
        if n_workers is None:
            n_workers = self.decidir_n_workers(len(tarefas))
        tarefas_por_worker = max(1, math.ceil(len(tarefas) / n_workers))
        lotes = []
        for i in range(0, len(tarefas), tarefas_por_worker):
            lotes.append(tarefas[i:i + tarefas_por_worker])
        workers = []
        threads = []
        for i, lote in enumerate(lotes):
            nome_lote = f"worker_{i}_de_{len(lotes)}"
            w = MCRTarefa(nome_lote, _executar_lote, {'lote': lote})
            workers.append(w)
            self.mk.aprender(f"LOTE:{len(lote)}", nome_lote)
            t = threading.Thread(target=w.executar)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        self.workers = workers
        return workers


def _executar_lote(lote: list):
    resultados = []
    for tarefa in lote:
        tarefa.executar()
        if tarefa.resultado is not None or tarefa.erro:
            resultados.append(tarefa.resultado if tarefa.erro is None else {'erro': tarefa.erro})
    return resultados


class MCRExpansao:
    """AutoLoop que usa TODOS os modulos, comandos e ferramentas."""
    
    COMANDOS_MCR = ['explorar', 'aprender_conceito', 'conectar', 'analisar', 'memoria']
    
    def __init__(self, kg=None, bridge=None):
        from .memory import _get_kg
        self.kg = kg or (_get_kg())
        self.bridge = bridge or MCRBridge()
        self.mk = MCR("expansao")
    
    def expandir(self, tema: str, max_recursos: int = 10) -> dict:
        from .memory import _get_kg
        from .persistence import _get_doc_index
        if not self.kg: return {'tema': tema, 'expansoes': 0}
        if not self.bridge._descobriu:
            disc = self.bridge.descobrir()
        resultados = []
        recursos_usados = []
        try:
            idx = _get_doc_index()
            idx.indexar()
            tem_docs = len(idx._indice) > 0
        except:
            tem_docs = False
        ordem = ['docs', 'modulos', 'comandos', 'kg'] if tem_docs else ['modulos', 'comandos', 'kg']
        try:
            dec = MCRDecisor("expansao_ordem")
            ordem_str = dec.decidir(f"EXPANDIR:{tema}")
            if ordem_str and '_' in str(ordem_str):
                ordem = str(ordem_str).split('_')
        except:
            pass
        for etapa in ordem:
            if etapa == 'docs':
                try:
                    idx = _get_doc_index()
                    docs = idx.buscar(tema)
                    for doc in docs:
                        conteudo = idx.ler(doc['caminho'], 500)
                        if conteudo and tema.lower() in conteudo.lower():
                            resultados.append(f"[DOCS:{os.path.basename(doc['caminho'])}] OK")
                            recursos_usados.append(f"docs:{doc['caminho']}")
                            self.mk.aprender(f"EXPANDIR:{tema}", f"DOCS:{doc['caminho']}")
                except:
                    pass
            elif etapa == 'modulos':
                for nome, mod in list(self.bridge.modulos.items())[:max_recursos//3]:
                    for func_nome in ['buscar', 'buscar_expandido', 'get', 'listar']:
                        if hasattr(mod, func_nome):
                            try:
                                res = getattr(mod, func_nome)(tema)
                                if res:
                                    resultados.append(f"[MOD:{nome}.{func_nome}] OK")
                                    recursos_usados.append(f"modulo:{nome}")
                                    self.mk.aprender(f"EXPANDIR:{tema}", f"MOD:{nome}")
                                break
                            except:
                                pass
            elif etapa == 'comandos':
                for nome in self.COMANDOS_MCR:
                    if nome not in self.bridge.comandos: continue
                    try:
                        cmd_result = self.bridge.usar_comando(nome)
                    except:
                        cmd_result = None
                    if cmd_result and isinstance(cmd_result, str) and len(cmd_result) > 20:
                        resultados.append(f"[CMD:{nome}] OK")
                        recursos_usados.append(f"comando:{nome}")
                        self.mk.aprender(f"EXPANDIR:{tema}", f"CMD:{nome}")
            elif etapa == 'kg':
                licoes = self.kg.buscar(tema, max_r=5)
                if licoes:
                    resultados.append(f"[KG] {len(licoes)} lessons")
                    recursos_usados.append("kg")
        lessons_tema = self.kg.buscar(tema, max_r=20)
        self.kg.aprender_conceito(
            f"expansao_{tema}",
            f"Expandido via {len(recursos_usados)} recursos. "
            f"Agora temos {len(lessons_tema)} lessons sobre o tema. "
            f"Recursos: {', '.join(recursos_usados)}.",
            ctx="expansao_auto"
        )
        return {
            'tema': tema,
            'expansoes': len(resultados),
            'recursos_usados': recursos_usados,
            'lessons_agora': len(lessons_tema),
            'detalhes': resultados,
        }


class MCRFuel:
    """MCR busca o proprio combustivel."""
    
    def __init__(self, kg=None, bridge=None):
        from .memory import _get_kg
        self.kg = kg or (_get_kg())
        self.bridge = bridge or MCRBridge()
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._base_mod = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.mk = MCR("fuel")
        self.total_lessons = 0
    
    def _ler(self, caminho, max_bytes=1000):
        try:
            if not os.path.exists(caminho): return ''
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(max_bytes)
        except: return ''
    
    def _listar_arquivos(self, diretorio, ext, max_n=100):
        if not os.path.isdir(diretorio): return []
        arquivos = []
        for fname in os.listdir(diretorio):
            if fname.endswith(ext) and not fname.startswith('__'):
                arquivos.append(os.path.join(diretorio, fname))
                if len(arquivos) >= max_n: break
        return arquivos
    
    def _alimentar(self, erro, solucao, ctx='fuel'):
        if not solucao or len(solucao) < 20: return
        texto = solucao.replace('\n', ' ').strip()
        if texto.startswith('{') or texto.startswith('['): return
        self.kg.aprender(erro=erro, causa=f"fuel:{ctx}", solucao=texto, ctx=ctx)
        self.total_lessons += 1
    
    def abastecer(self, fontes=None) -> int:
        if not self.kg: return 0
        if not self.bridge._descobriu:
            self.bridge.descobrir()
        self.total_lessons = 0
        fontes_escolhidas = fontes or ['lore', 'codigo', 'docs', 'modulos', 'comandos',
                                        'manifesto', 'prototipos', 'cache', 'ferramentas', 'kg']
        for fonte in fontes_escolhidas:
            if fonte == 'codigo':
                for f in self._listar_arquivos(os.path.join(self._base_mod, 'modulos'), '.py', 20):
                    nome = os.path.basename(f)
                    conteudo = self._ler(f, 500)
                    if conteudo:
                        self._alimentar(f"modulo_{nome}", f"Codigo do modulo {nome}: {conteudo}", "fuel_codigo")
                for f in self._listar_arquivos(os.path.join(self._base_mod, 'comandos'), '.py', 20):
                    nome = os.path.basename(f)
                    conteudo = self._ler(f, 300)
                    if conteudo:
                        self._alimentar(f"comando_{nome}", f"Comando {nome}: {conteudo}", "fuel_codigo")
            elif fonte == 'docs':
                docs_dir = os.path.join(self._base, 'docs')
                for f in self._listar_arquivos(docs_dir, '.md', 15):
                    conteudo = self._ler(f, 500)
                    if conteudo:
                        self._alimentar(f"doc_{os.path.basename(f)}", conteudo, "fuel_docs")
                instr_dir = os.path.join(docs_dir, 'MCR - Instrucoes')
                for f in self._listar_arquivos(instr_dir, '.txt', 10):
                    conteudo = self._ler(f, 500)
                    if conteudo:
                        self._alimentar(f"instr_{os.path.basename(f)}", conteudo, "fuel_docs")
            elif fonte == 'modulos':
                for nome in sorted(self.bridge.modulos.keys()):
                    mod = self.bridge.modulos[nome]
                    doc = (mod.__doc__ or '')
                    if doc:
                        self._alimentar(f"mod:{nome}", doc, "fuel_modulos")
                    funcoes = [a for a in dir(mod) if not a.startswith('_') and callable(getattr(mod, a, None))]
                    if funcoes:
                        self._alimentar(f"mod:{nome}_funcoes", f"Funcoes: {', '.join(funcoes)}", "fuel_modulos")
            elif fonte == 'comandos':
                for nome in sorted(self.bridge.comandos.keys()):
                    self._alimentar(f"cmd:{nome}", f"Comando disponivel: {nome}", "fuel_comandos")
            elif fonte == 'manifesto':
                manifesto = self._ler(os.path.join(self._base, 'docs', 'MANIFEST.md'), 2000)
                if manifesto:
                    self._alimentar("manifesto", manifesto, "fuel_manifesto")
            elif fonte == 'prototipos':
                sandbox_dir = os.path.join(self._base, 'sandbox')
                for f in self._listar_arquivos(sandbox_dir, '.py', 15):
                    if f.endswith('.py') and ('prototipo' in f or 'test_' in f):
                        conteudo = self._ler(f, 300)
                        if conteudo:
                            nome = os.path.basename(f)
                            self._alimentar(f"prototipo_{nome}", conteudo, "fuel_prototipos")
            elif fonte == 'cache':
                ep_path = os.path.join(self._base, 'sandbox', '.mcr_episodios.json')
                if os.path.exists(ep_path):
                    try:
                        with open(ep_path, 'r', encoding='utf-8') as f:
                            dados = json.load(f)
                        for ep in dados:
                            req = ep.get('request', '')
                            suc = ep.get('sucesso', False)
                            if req:
                                self._alimentar(f"episodio_{req}", f"Request: {req} | Sucesso: {suc}", "fuel_cache")
                    except: pass
                conv_path = os.path.join(self._base, 'sandbox', '.mcr_conversa.jsonl')
                if os.path.exists(conv_path):
                    try:
                        with open(conv_path, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f):
                                if i >= 10: break
                                try:
                                    entry = json.loads(line.strip())
                                    msg = entry.get('msg', '')
                                    if msg:
                                        self._alimentar(f"conversa_{i}", msg, "fuel_cache")
                                except: pass
                    except: pass
            elif fonte == 'ferramentas':
                ferramentas_list = [
                    'buscar_kg', 'buscar_estrategico', 'pattern_analyze',
                    'ler_arquivo', 'validar_codigo', 'gerar_esqueleto'
                ]
                for f in ferramentas_list:
                    self._alimentar(f"tool:{f}", f"Ferramenta disponivel: {f}", "fuel_ferramentas")
            elif fonte == 'kg':
                try:
                    licoes = self.kg._get_licoes()
                    uteis = [l for l in licoes 
                             if l.get('solucao','') and len(l.get('solucao','')) > 50
                             and not l.get('solucao','').startswith('{')
                             and not l.get('inactive')]
                    self._alimentar("kg_sumario",
                        f"KG tem {len(licoes)} lessons, {len(uteis)} uteis, "
                        f"{len(licoes)-len(uteis)} lixo. "
                        f"Distribuicao: {dict(__import__('collections').Counter(l.get('ctx','?') for l in licoes).most_common(10))}",
                        "fuel_kg")
                except: pass
        if self.total_lessons > 0:
            for _ in range(10):
                try: self.kg.aprender_conceito("_fuel_flush", "_", ctx="_flush")
                except: pass
        self.mk.aprender("FUEL", f"LESSONS:{self.total_lessons}")
        return self.total_lessons
    
    def abastecer_se_precisar(self, min_uteis=100) -> bool:
        try:
            licoes = self.kg._get_licoes()
            uteis = [l for l in licoes 
                     if l.get('solucao','') and len(l.get('solucao','')) > 50
                     and not l.get('solucao','').startswith('{')
                     and not l.get('inactive')]
            if len(uteis) < min_uteis:
                n = self.abastecer()
                return n > 0
            return False
        except:
            return False


class MCRAutoMelhoria:
    """MCR que se autoaperfeicoa com 7 perguntas."""
    
    def __init__(self, kg=None, bridge=None):
        from .memory import _get_kg
        from .meta import MCRMetaGap
        from .persistence import MCRFragmentador, _get_doc_index
        self.kg = kg or (_get_kg())
        self.bridge = bridge or MCRBridge()
        self.meta = MCRMetaGap(self.kg, self.bridge)
        self.fuel = MCRFuel(self.kg, self.bridge)
        self.frag = MCRFragmentador()
        self.mk = MCR("auto_melhoria")
    
    def _p1_gaps(self):
        gaps = self.meta.diagnosticar_gaps(min_por_prefixo=5)
        for gap in gaps:
            n = self.meta.buscar_para_gap(gap)
            if n > 0:
                self.mk.aprender(f"GAP:{gap['prefixo']}", f"{n}")
        return [f"gap_{g['prefixo']}" for g in gaps if g]
    
    def _p2_lento(self):
        if not self.frag.fragmentos: return []
        for f in self.frag.fragmentos:
            if f.tempo > 1.0:
                self.mk.aprender(f"LENTO:{f.nome}", f"{f.tempo:.1f}s")
        return [f"lento:{f.nome}:{f.tempo:.1f}s" for f in self.frag.fragmentos if f.tempo > 1.0]
    
    def _p7_esqueceu(self):
        from .persistence import _get_doc_index
        import os
        try:
            idx = _get_doc_index()
            idx.indexar()
            for termo in ['eridanus','spa','shc','npc','lore']:
                docs = idx.buscar(termo)
                for doc in docs:
                    c = idx.ler(doc['caminho'], 500)
                    if c and self.kg:
                        self.kg.aprender_conceito(f"auto_{os.path.basename(doc['caminho']).replace('.','_')}", c, ctx="auto_descoberta")
            return ["docs_autodescobertos"] if any(idx.buscar(t) for t in ['eridanus','spa','lore']) else []
        except: return []
    
    def _p3_repetiu(self):
        if self.fuel.mk.total > 10 and self.fuel.mk.entropia_media() < 0.5:
            self.mk.aprender("LOOP", "detectado")
            return ["loop_detectado"]
        return []
    
    def _p4_errou(self):
        if not self.kg: return []
        e = [l for l in self.kg._get_licoes() if 'erro' in l.get('ctx','')]
        if e: self.mk.aprender("ERROS", str(len(e)))
        return [f"erros:{len(e)}"] if e else []
    
    def _p5_aprendeu(self):
        if not self.kg: return []
        r = [l for l in self.kg._get_licoes() if l.get('timestamp',0) > 0]
        return [f"aprendeu:{len(r)}"] if r else []
    
    def _p6_precisa(self):
        pn = MCRPesoNota("check")
        if len(pn.historico) < 5: return ["peso_nota_sem_treino"]
        return []
    
    def ciclo(self):
        try:
            kk_licoes = len(self.kg._get_licoes()) if self.kg else 0
        except:
            kk_licoes = 0
        todas = []
        if kk_licoes > 200:
            for fn in [self._p3_repetiu, self._p4_errou, self._p5_aprendeu, self._p6_precisa]:
                try: todas.extend(fn())
                except: pass
        else:
            for fn in [self._p1_gaps, self._p2_lento, self._p7_esqueceu,
                       self._p3_repetiu, self._p4_errou, self._p5_aprendeu, self._p6_precisa]:
                try: todas.extend(fn())
                except: pass
        self.mk.aprender("CICLO", str(len(todas)))
        return {'acoes': todas, 'n': len(todas)}
