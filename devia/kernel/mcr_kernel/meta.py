#!/usr/bin/env python3
"""meta.py — Metacognition: self-indexing, self-healing, meta-levels, gap detection.

Auto-organização, meta-níveis, auto-diagnóstico e reparo.
"""
import os, math

from .engine import MCR
from .decisor import MCRThreshold, MCRPesoNota, MCRDecisor


_NIVEIS_BASE = ['byte', 'palavra', 'token', 'intencao', 'padrao',
                'markov', 'pi', 'predizer', 'contexto', 'emergir',
                'filosofia', 'feedback', 'diagnostico', 'memoria',
                'meta', 'cache', 'busca', 'similaridade', 'entropia',
                'ruido', 'threshold', 'peso', 'acao', 'ciclo',
                'spawn', 'mestre', 'pergunta', 'cadeia', 'conector',
                'fuel', 'auto_start', 'auto_melhoria']


class MCRMeta:
    """MCR que gerencia o proprio MCR."""
    
    def __init__(self, kg=None):
        from .memory import _get_kg, MCRKGAuto, MCRExpansao
        self.kg = kg or (_get_kg())
        self.auto_kg = MCRKGAuto(self.kg)
        self.expansao = MCRExpansao(self.kg)
        self.mk = MCR("meta")
        self._ultimo_estado = {}
    
    def diagnosticar(self) -> dict:
        if not self.kg: return {'erro': 'KG indisponivel'}
        licoes = self.kg._get_licoes()
        uteis = [l for l in licoes 
                 if l.get('solucao','') and len(l.get('solucao','')) > 50
                 and not l.get('solucao','').strip().startswith('{')
                 and not l.get('inactive')]
        lixo = len(licoes) - len(uteis)
        cats = self.auto_kg.categorizar()
        categorias_fracas = {c: len(v) for c, v in cats.items() if len(v) < 10}
        estado = {
            'total': len(licoes),
            'uteis': len(uteis),
            'lixo': lixo,
            'aproveitamento': f"{len(uteis)/max(len(licoes),1)*100:.0f}%",
            'categorias': len(cats),
            'categorias_fracas': len(categorias_fracas),
            'precisa_limpar': lixo > len(uteis),
            'precisa_expandir': len(categorias_fracas) > 3,
        }
        self._ultimo_estado = estado
        self.mk.aprender("DIAG", f"uteis:{len(uteis)}|lixo:{lixo}")
        return estado
    
    def auto_organizar(self) -> dict:
        acoes = []
        estado = self.diagnosticar()
        acoes.append(f"diagnostico: {estado['aproveitamento']} util")
        if estado.get('precisa_limpar'):
            limpeza = self.auto_kg.limpar()
            acoes.append(f"limpeza: {limpeza['removidos']} removidos")
            self.mk.aprender("ACAO:LIMPAR", f"removeu:{limpeza['removidos']}")
        if estado.get('total', 0) > 200:
            dedup = self.auto_kg.dedup()
            if dedup:
                acoes.append(f"dedup: {dedup} removidas")
                self.mk.aprender("ACAO:DEDUP", f"removeu:{dedup}")
        if estado.get('precisa_expandir'):
            cats = self.auto_kg.categorizar()
            for cat, lessons in cats.items():
                if len(lessons) < 10:
                    tema = cat
                    res = self.expansao.expandir(tema)
                    if res['expansoes'] > 0:
                        acoes.append(f"expandiu:{tema} ({res['expansoes']} recursos)")
                        self.mk.aprender(f"ACAO:EXPANDIR:{tema}", f"recursos:{res['expansoes']}")
        return {
            'acoes': acoes,
            'n_acoes': len(acoes),
            'estado_final': self.diagnosticar(),
        }


class MCRNivel:
    """UM nivel MCR descoberto."""
    
    def __init__(self, nome: str, dados_iniciais: bytes = None):
        self.nome = nome
        self.mk = MCR(f"nivel_{nome}")
        self.entropia = 0.0
        self.raio = 0.0
        self.conexoes = {}
        self._alimentado = 0
        if dados_iniciais:
            self.alimentar(dados_iniciais)
    
    def alimentar(self, dados: bytes):
        if not dados: return
        self.mk.aprender_sequencia(list(dados))
        self._alimentado += len(dados)
        self.entropia = round(self.mk.entropia_media(), 3)
        n_trans = sum(len(v) for v in self.mk.transicoes.values())
        self.raio = round(self.entropia * max(1, math.log2(n_trans + 1)), 3)
    
    def conectar(self, outro: 'MCRNivel') -> float:
        if not outro.mk.transicoes or not self.mk.transicoes:
            return 0.0
        estados_self = set(self.mk.freq.keys())
        estados_outro = set(outro.mk.freq.keys())
        if not estados_self or not estados_outro:
            return 0.0
        inter = estados_self & estados_outro
        uniao = estados_self | estados_outro
        sim = len(inter) / len(uniao) if uniao else 0.0
        self.conexoes[outro.nome] = sim
        return sim
    
    def stats(self) -> dict:
        return {
            'nome': self.nome, 'entropia': self.entropia,
            'raio': self.raio, 'alimentado': self._alimentado,
            'estados': len(self.mk.transicoes),
            'conexoes': len(self.conexoes),
        }


class MCRMetaNivel:
    """MCR descobre QUANTOS e QUAIS niveis precisa."""
    
    def __init__(self):
        self.niveis = {}
        self._ordem = []
        self.mk = MCR("meta_nivel")
        self._energia_total = 0.0
        self._th = MCRThreshold("meta_nivel_criacao")
        for v in [5, 8, 10, 12, 15, 20]:
            self._th.observar(v)
    
    def alimentar(self, dados: bytes):
        if not dados: return
        if 'byte' not in self.niveis:
            self._criar_nivel('byte')
        self.niveis['byte'].alimentar(dados)
        n_byte = len(self.niveis['byte'].mk.transicoes)
        limiar = self._th.calcular(0.4)
        if n_byte > limiar and 'palavra' not in self.niveis:
            self._criar_nivel('palavra', dados)
        niveis_seq = ['palavra', 'intencao', 'padrao', 'markov', 'predizer']
        for i, nome in enumerate(niveis_seq):
            if nome in self.niveis:
                self.niveis[nome].alimentar(dados)
            elif self._tem_antecessor(nome, niveis_seq):
                n_ant = len(self.niveis[niveis_seq[i-1]].mk.transicoes)
                limiar_seq = self._th.calcular(0.4 * (i + 1))
                if n_ant > limiar_seq:
                    self._criar_nivel(nome, dados)
    
    def _tem_antecessor(self, nome, niveis_seq):
        if nome not in niveis_seq: return False
        i = niveis_seq.index(nome)
        if i == 0: return True
        return niveis_seq[i-1] in self.niveis
    
    def _criar_nivel(self, nome: str, dados: bytes = None):
        nivel = MCRNivel(nome, dados)
        self.niveis[nome] = nivel
        self._ordem.append(nome)
        self.mk.aprender(f"NIVEL:{nome}", f"ordem:{len(self._ordem)}")
        self._conectar_niveis()
        self._energia_total = sum(n.entropia * n.raio for n in self.niveis.values())
    
    def _conectar_niveis(self):
        nomes = list(self.niveis.keys())
        for i in range(len(nomes)):
            for j in range(i+1, len(nomes)):
                a, b = self.niveis[nomes[i]], self.niveis[nomes[j]]
                sim = a.conectar(b)
                if sim > 0:
                    self.mk.aprender(f"LIG:{nomes[i]}-{nomes[j]}", f"sim:{sim:.2f}")
    
    def diagnosticar(self) -> dict:
        if not self.niveis:
            return {'niveis': 0, 'energia': 0}
        stats = {nome: n.stats() for nome, n in self.niveis.items()}
        maior_raio = max(stats.items(), key=lambda x: x[1]['raio']) if stats else ('?', {})
        return {
            'n_niveis': len(self.niveis),
            'ordem': self._ordem,
            'stats': stats,
            'maior_raio': {'nome': maior_raio[0], 'valor': maior_raio[1].get('raio', 0)},
            'energia_total': round(self._energia_total, 2),
            'precisa_mais': len(self.niveis) < len(_NIVEIS_BASE),
        }
    
    def auto_expandir(self, max_niveis: int = 10) -> int:
        if len(self.niveis) >= max_niveis:
            return 0
        proximos = [n for n in _NIVEIS_BASE if n not in self.niveis]
        if not proximos:
            return 0
        novo_nivel = proximos[0]
        self._criar_nivel(novo_nivel)
        if 'byte' in self.niveis:
            nivel_byte = self.niveis['byte']
            semente = list(nivel_byte.mk.freq.keys())[0] if nivel_byte.mk.freq else '0'
            estados = nivel_byte.mk.gerar(semente, passos=50)
            dados_reconstruidos = ' '.join(str(e) for e in estados if e)
            if novo_nivel == 'palavra':
                dados_novo = dados_reconstruidos.encode('utf-8')
            elif novo_nivel == 'token':
                try:
                    tokens_tipos = []
                    for e in estados:
                        pal = str(e).replace('B:', '').strip()
                        if pal:
                            # try/except para import que pode falhar (legado)
                            try:
                                from modulos.MCR import _classificar_token as _mcr_tip
                                tokens_tipos.append(_mcr_tip(pal) or 'outro')
                            except Exception:
                                tokens_tipos.append('outro')
                    dados_novo = ' '.join(tokens_tipos).encode('utf-8')
                except Exception:
                    dados_novo = dados_reconstruidos.encode('utf-8')
            elif novo_nivel == 'intencao':
                dados_novo = dados_reconstruidos.encode('utf-8')
            else:
                dados_novo = dados_reconstruidos.encode('utf-8')
            self.niveis[novo_nivel].alimentar(dados_novo)
        return 1


class MCRMetaGap:
    """MCR descobre o que nao sabe e busca aprender."""
    
    def __init__(self, kg=None, bridge=None):
        from .memory import _get_kg
        from .engine import MCRBridge
        from .persistence import _get_doc_index
        self.kg = kg or (_get_kg())
        self.bridge = bridge or MCRBridge()
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self.mk = MCR("metagap")
        self.gaps_encontrados = []
    
    def diagnosticar_gaps(self, min_por_prefixo: int = 3) -> list:
        if not self.kg: return []
        from .memory import CONECTORES
        licoes = self.kg._get_licoes()
        prefixos = {}
        for l in licoes:
            ctx = l.get('ctx', '')
            sol = l.get('solucao', '')
            if not sol or len(sol) < 20: continue
            if l.get('inactive'): continue
            prefixo = ctx.split('_')[0] if '_' in ctx else ctx
            if prefixo not in prefixos:
                prefixos[prefixo] = {'count': 0, 'termos': set()}
            prefixos[prefixo]['count'] += 1
            for p in sol.lower().split():
                if len(p) > 3 and p not in CONECTORES:
                    prefixos[prefixo]['termos'].add(p)
                    if len(prefixos[prefixo]['termos']) > 5: break
        gaps = []
        for prefixo, dados in sorted(prefixos.items(), key=lambda x: x[1]['count']):
            if dados['count'] < min_por_prefixo and len(prefixo) > 1:
                termo_exemplo = list(dados['termos']) if dados['termos'] else [prefixo]
                gaps.append({
                    'prefixo': prefixo,
                    'n_lessons': dados['count'],
                    'termos': termo_exemplo,
                    'score': min_por_prefixo - dados['count'],
                })
        gaps.sort(key=lambda x: -x['score'])
        self.gaps_encontrados = gaps
        self.mk.aprender("GAPS", f"{len(gaps)} gaps encontrados")
        return gaps
    
    def buscar_para_gap(self, gap: dict) -> int:
        if not self.kg: return 0
        from .persistence import _get_doc_index
        if self.kg._get_licoes() and len(self.kg._get_licoes()) > 300:
            return 0
        termo = gap['termos'][0] if gap['termos'] else gap['prefixo']
        n_antes = len(self.kg._get_licoes())
        doc_idx = _get_doc_index()
        doc_idx.indexar()
        docs_encontrados = doc_idx.buscar(termo)
        for doc in docs_encontrados:
            conteudo = doc_idx.ler(doc['caminho'], max_bytes=2000)
            if conteudo and termo.lower() in conteudo.lower():
                idx = conteudo.lower().find(termo.lower())
                inicio = max(0, idx - 100)
                fim = min(len(conteudo), idx + 300)
                trecho = conteudo[inicio:fim]
                if len(trecho) > 50:
                    self.kg.aprender_conceito(
                        f"{gap['prefixo']}:{os.path.basename(doc['caminho']).replace('.','_')}",
                        f"[Fonte: {doc['caminho']}]\n{trecho}",
                        ctx=f"gap_{gap['prefixo']}"
                    )
        sandbox_dir = os.path.join(self._base, 'sandbox')
        if os.path.isdir(sandbox_dir):
            for fname in os.listdir(sandbox_dir):
                if not (fname.endswith('.py') or fname.endswith('.lua') or fname.endswith('.txt')): continue
                if not termo.lower() in fname.lower(): continue
                fpath = os.path.join(sandbox_dir, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read(1000)
                    if len(conteudo) > 50:
                        self.kg.aprender_conceito(
                            f"{gap['prefixo']}:{fname.replace('.','_')}",
                            f"[Prototipo: {fname}]\n{conteudo}",
                            ctx=f"gap_{gap['prefixo']}"
                        )
                except Exception: pass
        if self.bridge and self.bridge._descobriu:
            for nome, mod in self.bridge.modulos.items():
                if termo.lower() in nome.lower():
                    doc = (mod.__doc__ or '')
                    if doc:
                        self.kg.aprender_conceito(
                            f"{gap['prefixo']}:mod_{nome}",
                            f"[Modulo: {nome}]\n{doc}",
                            ctx=f"gap_{gap['prefixo']}"
                        )
        n_depois = len(self.kg._get_licoes())
        n_criadas = n_depois - n_antes
        self.mk.aprender(f"GAP:{gap['prefixo']}", f"CRIOU:{n_criadas}")
        return n_criadas
    
    def ciclo_completo(self, min_por_prefixo: int = 3) -> dict:
        gaps = self.diagnosticar_gaps(min_por_prefixo)
        resultados = []
        total_criadas = 0
        for gap in gaps:
            n = self.buscar_para_gap(gap)
            if n > 0:
                resultados.append(f"{gap['prefixo']}:{n}")
                total_criadas += n
        if total_criadas > 0:
            for _ in range(10):
                try: self.kg.aprender_conceito("_gap_flush", "_", ctx="_flush")
                except Exception: pass
        self.mk.aprender("CICLO_GAP", f"CRIOU:{total_criadas}")
        return {
            'gaps': len(gaps),
            'preenchidos': len(resultados),
            'total_lessons_criadas': total_criadas,
            'detalhes': resultados,
        }


class MCRSelfIndex:
    """Indexa o proprio MCR.py + modulos + comandos como documentos."""
    
    def __init__(self):
        self._indice = {'classes': {}, 'modulos': {}, 'comandos': {}}
        self.mk = MCR("self_index")
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self._raiz = os.path.abspath(os.path.join(self._base, '..', '..', '..'))
    
    def indexar_tudo(self):
        self._indexar_mcrpy()
        self._indexar_modulos()
        self._indexar_comandos()
        from .state import _MCR_STATE
        _MCR_STATE['indice_modulos'] = self._indice['modulos']
        _MCR_STATE['indice_comandos'] = self._indice['comandos']
        return len(self._indice['classes']) + len(self._indice['modulos']) + len(self._indice['comandos'])
    
    def _indexar_mcrpy(self):
        caminho = os.path.join(self._base, 'MCR.py')
        if not os.path.exists(caminho): return
        with open(caminho, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
        classe_atual = None
        for i, linha in enumerate(linhas):
            if linha.startswith('class '):
                nome_classe = linha.split('(')[0].split(':')[0].replace('class ', '').strip()
                classe_atual = nome_classe
                doc = ''
                for j in range(i+1, min(i+5, len(linhas))):
                    l = linhas[j].strip()
                    if l.startswith('"""') or l.startswith("'''"):
                        doc += l.replace('"""', '').replace("'''", '')
                    elif doc and (l.startswith('"""') or l.startswith("'''")):
                        break
                    elif doc:
                        doc += ' ' + l
                self._indice['classes'][nome_classe] = {
                    'linha': i+1, 'doc': doc,
                }
                self.mk.aprender(f"CLS:{nome_classe}", f"L:{i+1}")
    
    def _indexar_modulos(self):
        mod_path = os.path.join(self._base, '..', 'modulos')
        if not os.path.isdir(mod_path): return
        for fname in os.listdir(mod_path):
            if not fname.endswith('.py') or fname.startswith('_'): continue
            fpath = os.path.join(mod_path, fname)
            try:
                with open(fpath, 'rb') as f:
                    dados = f.read(500)
                mk_mod = MCR(f"mod_{fname[:-3]}")
                mk_mod.aprender_sequencia(list(dados))
                self._indice['modulos'][fname[:-3]] = {
                    'bytes': len(dados),
                    'estados': len(mk_mod.transicoes),
                }
                self.mk.aprender(f"MOD:{fname[:-3]}", f"BYTES:{len(dados)}")
            except Exception: pass
    
    def _indexar_comandos(self):
        cmd_path = os.path.join(self._base, '..', 'comandos')
        if not os.path.isdir(cmd_path): return
        for fname in os.listdir(cmd_path):
            if not fname.startswith('cmd_') or not fname.endswith('.py'): continue
            nome = fname[4:-3]
            fpath = os.path.join(cmd_path, fname)
            try:
                with open(fpath, 'rb') as f:
                    dados = f.read(500)
                mk_cmd = MCR(f"cmd_{nome}")
                mk_cmd.aprender_sequencia(list(dados))
                self._indice['comandos'][nome] = {
                    'bytes': len(dados),
                    'estados': len(mk_cmd.transicoes),
                }
                self.mk.aprender(f"CMD:{nome}", f"BYTES:{len(dados)}")
            except Exception: pass
    
    def buscar_classe(self, nome):
        return self._indice['classes'].get(nome, None)
    
    def buscar_modulo(self, nome):
        return self._indice['modulos'].get(nome, None)
    
    def buscar_comando(self, nome):
        return self._indice['comandos'].get(nome, None)
    
    def estatisticas(self) -> dict:
        return {
            'classes': len(self._indice['classes']),
            'modulos': len(self._indice['modulos']),
            'comandos': len(self._indice['comandos']),
            'total': sum(len(v) for v in self._indice.values()),
        }


class MCRSelfHeal:
    """Auto-reconstroi dados faltantes no startup."""
    
    @staticmethod
    def verificar() -> dict:
        from .state import _MCR_STATE
        from .decisor import MCRThreshold
        acoes = []
        th = MCRThreshold("heal_check")
        if len(th.observacoes) < 3:
            for nome, valores in _MCR_STATE.get('thresholds', {}).items():
                th_temp = MCRThreshold(nome)
                for v in valores:
                    th_temp.observar(v)
            acoes.append("thresholds:restaurados")
        if not _MCR_STATE.get('indice_modulos'):
            idx = MCRSelfIndex()
            n = idx.indexar_tudo()
            acoes.append(f"indices:{n} itens")
        classes = _MCR_STATE.get('classes_essenciais', [])
        presentes = sum(1 for c in classes if c in dir())
        if presentes < len(classes):
            acoes.append(f"classes:{presentes}/{len(classes)}")
        else:
            acoes.append(f"classes:{len(classes)}/OK")
        return {
            'status': 'ok' if not acoes else 'reconstruido',
            'acoes': acoes,
            'n_acoes': len(acoes),
        }
