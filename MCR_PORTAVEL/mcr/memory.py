#!/usr/bin/env python3
"""memory.py — Knowledge Graph, connectors, cross-referencing, and buffer.

Knowledge Graph (MCRBufferKG), topic connectors (MCRConector),
cross-reference analyzer (MCRCruzado), chain generator (MCRCadeia),
and KG auto-organization (MCRKGAuto).
"""
import os, re, json, math, random as _random
from collections import Counter
from typing import Dict, List, Optional

from .engine import MCR
from .signature import MCRSignature
from .decisor import (
    MCRPesoNota, MCRThreshold, MCREntropia, MCRRuido, MCRDecisor,
    _MCR_THRESHOLD_TAMANHO, _MCR_THRESHOLD_REPETICAO,
    _MCR_THRESHOLD_CONEXAO, _MCR_THRESHOLD_PALAVRA, _MCR_THRESHOLD_FILTRO,
    _MCR_THRESHOLD_CONF, _MCR_THRESHOLD_NOTA,
)


def _get_kg():
    try:
        from modulos.kg import KnowledgeGraph
        kg = KnowledgeGraph()
        if kg:
            return kg
    except Exception:
        pass
    try:
        return MCRBufferKG()
    except Exception:
        return None


CONECTORES = {
    'a', 'e', 'o', 'de', 'da', 'do', 'em', 'com', 'para', 'por',
    'se', 'no', 'na', 'um', 'uma', 'os', 'as', 'ao', 'aos', 'das',
    'dos', 'num', 'numa', 'pelo', 'pela', 'pelos', 'pelas', 'que',
    'como', 'mas', 'mais', 'ou', 'nem', 'tambem', 'so',
}


class MCRCruzado:
    """Analisa entropia cruzada entre cadeias para emergência."""
    
    def __init__(self, conector):
        self.conector = conector
    
    def analisar(self, topico_a: str, topico_b: str) -> dict:
        if topico_a not in self.conector.topicos or topico_b not in self.conector.topicos:
            return {'erro': 'topico nao encontrado', 'pontes': [], 'melhor': None}
        conteudo_a = self.conector.topicos[topico_a].get('conteudo', set())
        conteudo_b = self.conector.topicos[topico_b].get('conteudo', set())
        candidatas = conteudo_a & conteudo_b
        if not candidatas:
            return self._analisar_sem_compartilhadas(topico_a, topico_b)
        pontes = []
        for palavra in candidatas:
            score, detalhes = self._avaliar_ponte(topico_a, topico_b, palavra)
            pontes.append({'palavra': palavra, 'score': round(score, 2), **detalhes})
        pontes.sort(key=lambda x: -x['score'])
        return {
            'total_candidatas': len(candidatas),
            'divergencia_media': round(sum(p.get('divergencia', 0) for p in pontes)/len(pontes), 3) if pontes else 0,
            'pontes': pontes,
            'melhor': pontes[0] if pontes else None,
        }
    
    def melhor_ponte(self, topico_a: str, topico_b: str) -> dict:
        return self.analisar(topico_a, topico_b).get('melhor')
    
    def _avaliar_ponte(self, topico_a, topico_b, palavra):
        mk_a = self.conector.topicos[topico_a].get('mcr_palavra')
        mk_b = self.conector.topicos[topico_b].get('mcr_palavra')
        if not mk_a or not mk_b: return 0.0, {}
        trans_a = set(mk_a.transicoes.get(palavra, {}).keys())
        trans_b = set(mk_b.transicoes.get(palavra, {}).keys())
        if not trans_a and not trans_b: divergencia = 0.0
        elif not trans_a or not trans_b: divergencia = 1.0
        else:
            inter = trans_a & trans_b; uniao = trans_a | trans_b
            divergencia = 1.0 - (len(inter)/len(uniao) if uniao else 0)
        h_a = mk_a.entropia(palavra) if palavra in mk_a.freq else 0
        h_b = mk_b.entropia(palavra) if palavra in mk_b.freq else 0
        entropia_comb = (h_a + h_b)/2
        freq_global = sum(1 for _, d in self.conector.topicos.items()
                         if palavra in d.get('conteudo', set()))
        especificidade = 1.0 - min(1.0, freq_global/max(1, len(self.conector.topicos)*0.5))
        cadeia_a = len(mk_a.gerar(palavra, passos=5))
        cadeia_b = len(mk_b.gerar(palavra, passos=5))
        profundidade = min(1.0, (cadeia_a + cadeia_b)/10)
        score = divergencia*5 + especificidade*3 + profundidade*2 + min(0.5, entropia_comb*0.2)
        score = min(12, score)
        return score, {
            'divergencia': round(divergencia, 3),
            'especificidade': round(especificidade, 3),
            'profundidade': round(profundidade, 3),
            'entropia_combinada': round(entropia_comb, 3),
            'freq_global': freq_global,
            'cadeia_a': cadeia_a, 'cadeia_b': cadeia_b,
            'nota_divergencia': round(divergencia*5, 2),
            'nota_especificidade': round(especificidade*3, 2),
            'nota_profundidade': round(profundidade*2, 2),
        }
    
    def _analisar_sem_compartilhadas(self, topico_a, topico_b):
        texto_a = self.conector.topicos[topico_a]['texto']
        texto_b = self.conector.topicos[topico_b]['texto']
        da = texto_a.encode('utf-8'); db = texto_b.encode('utf-8')
        bytes_comuns = set(da) & set(db)
        pontes = []
        for byte_val in bytes_comuns:
            pal_a = None; pal_b = None
            for i, b in enumerate(da):
                if b == byte_val:
                    ini, fim = i, i
                    while ini > 0 and da[ini-1] != 32: ini -= 1
                    while fim < len(da) and da[fim] != 32: fim += 1
                    pal_a = da[ini:fim].decode('utf-8', errors='replace')
                    break
            for i, b in enumerate(db):
                if b == byte_val:
                    ini, fim = i, i
                    while ini > 0 and db[ini-1] != 32: ini -= 1
                    while fim < len(db) and db[fim] != 32: fim += 1
                    pal_b = db[ini:fim].decode('utf-8', errors='replace')
                    break
            if not pal_a or not pal_b or pal_a.lower() == pal_b.lower(): continue
            score, det = self._avaliar_ponte(topico_a, topico_b, pal_a)
            score *= 0.7
            det['palavra_a'] = pal_a; det['palavra_b'] = pal_b
            pontes.append({'palavra': f"{pal_a}↔{pal_b}", 'score': round(score, 2), **det})
        pontes.sort(key=lambda x: -x['score'])
        return {'total_candidatas': len(pontes), 'tipo': 'byte_bridge',
                'pontes': pontes, 'melhor': pontes[0] if pontes else None}


class MCRConector:
    """Conecta tópicos distantes usando MCR multi-nível (Byte+Palavra+Token).
    
    Uso:
        c = MCRConector()
        c.alimentar("SPA é progressão", "spa")
        c.alimentar("Eridanus é cidade", "eridanus")
        conexao = c.conectar("spa", "eridanus")
    """
    
    def __init__(self):
        self.mcr_byte = MCR.Nivel("byte_global")
        self.mcr_palavra = MCR.Nivel("palavra_global")
        self.mcr_token = MCR.Nivel("token_global")
        self.topicos = {}
        self.conexoes_feitas = set()
        self.total_conexoes = 0
        self.cruzado = MCRCruzado(self)
        self._peso_nota = MCRPesoNota("conector")
    
    def alimentar(self, texto: str, nome: str = None, contexto: dict = None):
        if nome is None: nome = f"topico_{len(self.topicos)+1}"
        dados = texto.encode('utf-8')
        for i in range(len(dados)-1):
            self.mcr_byte.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
        palavras = texto.split()
        for i in range(len(palavras)-1):
            self.mcr_palavra.aprender(palavras[i], palavras[i+1])
        for i in range(len(palavras)-1):
            ta = palavras[i][0].upper() if palavras[i] else '?'
            tb = palavras[i+1][0].upper() if palavras[i+1] else '?'
            self.mcr_token.aprender(ta, tb)
        
        # Se contexto fornecido, tambem treina estados compostos
        if contexto:
            from .engine import compose_state
            for i in range(len(palavras)-1):
                estado_a = compose_state(palavras[i], contexto)
                estado_b = compose_state(palavras[i+1], contexto)
                self.mcr_palavra.aprender(estado_a, estado_b)
        
        mcr_t = MCR.Nivel(nome)
        for i in range(len(dados)-1):
            mcr_t.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
        mcr_p = MCR.Nivel(f"{nome}_palavra")
        for i in range(len(palavras)-1):
            mcr_p.aprender(palavras[i], palavras[i+1])
        self.topicos[nome] = {
            'texto': texto, 'mcr_byte': mcr_t, 'mcr_palavra': mcr_p,
            'palavras': palavras, 'bytes': len(dados),
            'conteudo': {p.lower() for p in palavras
                        if len(p) >= 4 and p.lower() not in CONECTORES},
        }
        return nome
    
    def alimentar_json(self, arquivo):
        if not os.path.exists(arquivo): return 0
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        conteudo = dados.get('topicos', dados if isinstance(dados, list) else [])
        count = 0
        for item in conteudo:
            if isinstance(item, dict) and 'texto' in item:
                self.alimentar(item['texto'], item.get('nome')); count += 1
            elif isinstance(item, str):
                self.alimentar(item); count += 1
        return count
    
    def conectar(self, topico_a: str, topico_b: str) -> dict:
        if topico_a not in self.topicos or topico_b not in self.topicos: return None
        t_a = self.topicos[topico_a]; t_b = self.topicos[topico_b]
        texto_a = t_a['texto']; texto_b = t_b['texto']
        palavras_a = t_a['palavras']; palavras_b = t_b['palavras']
        import hashlib
        h = hashlib.md5(f"{min(topico_a,topico_b)}|{max(topico_a,topico_b)}".encode()).hexdigest()
        if h in self.conexoes_feitas: return None
        byte_ponte, tipo_ponte, pal_a, pal_b = self._encontrar_ponte(topico_a, topico_b)
        sequencia = ''
        if tipo_ponte in ('conteudo_compartilhado', 'conteudo_mas_parcial'):
            mk_a = t_a['mcr_palavra']; mk_b = t_b['mcr_palavra']
            semente = palavras_a[0] if palavras_a else 'O'
            seq = []; atual = semente; atingiu = False
            for _ in range(14):
                seq.append(atual)
                if not atingiu and atual.lower() == pal_a.lower():
                    atingiu = True; atual = pal_b; continue
                mk = mk_b if atingiu else mk_a
                prox, conf = mk.predizer(atual)
                if prox is None or conf < 0.01: break
                atual = prox
            sequencia = ' '.join(seq)
            if len(sequencia.strip()) < 10: sequencia = ''
        if not sequencia:
            mk_a_byte = t_a['mcr_byte']; mk_b_byte = t_b['mcr_byte']
            inicio = f"B:{texto_a.encode('utf-8')[0]:02x}"
            seq_a = mk_a_byte.gerar(inicio, 8)
            estados_b = set(mk_b_byte.freq.keys())
            ponte = None
            for e in seq_a:
                if e in estados_b: ponte = e; break
            if ponte is None:
                for e in seq_a:
                    if e in self.mcr_byte.freq:
                        prox, _ = self.mcr_byte.predizer(e)
                        if prox and prox in estados_b: ponte = e; break
            if ponte is None: return None
            seq_b = mk_b_byte.gerar(ponte, 8)
            chars = []
            for s in seq_a:
                if s.startswith('B:'):
                    try: chars.append(chr(int(s[2:], 16)))
                    except Exception: chars.append('?')
            chars.append(' ')
            for s in seq_b:
                if s.startswith('B:'):
                    try: chars.append(chr(int(s[2:], 16)))
                    except Exception: chars.append('?')
            sequencia = ''.join(chars)
        nota, detalhes = self._autoavaliar_multinivel(sequencia, texto_a, texto_b, tipo_ponte)
        self.conexoes_feitas.add(h)
        self.total_conexoes += 1
        return {
            'hash': h, 'topico_a': topico_a, 'topico_b': topico_b,
            'tipo_ponte': tipo_ponte, 'palavra_a': pal_a, 'palavra_b': pal_b,
            'sequencia': sequencia, 'nota': round(nota, 2),
            'detalhes_nota': detalhes,
        }
    
    def _encontrar_ponte(self, topico_a, topico_b):
        melhor = self.cruzado.melhor_ponte(topico_a, topico_b)
        if melhor:
            palavra = melhor.get('palavra', '')
            score = melhor.get('score', 0)
            pal_a = melhor.get('palavra_a', palavra) or palavra
            pal_b = melhor.get('palavra_b', palavra) or palavra
            texto_a = self.topicos[topico_a]['texto']
            idx = texto_a.lower().find(pal_a.lower())
            byte_p = f"B:{texto_a.encode('utf-8')[idx if idx>=0 else 0]:02x}"
            tipo = 'conteudo_compartilhado' if score >= 6 else 'conteudo_mas_parcial'
            return byte_p, tipo, pal_a, pal_b
        conteudo_a = self.topicos[topico_a].get('conteudo', set())
        conteudo_b = self.topicos[topico_b].get('conteudo', set())
        comp = conteudo_a & conteudo_b
        if comp:
            pal = max(comp, key=len)
            texto_a = self.topicos[topico_a]['texto']
            idx = texto_a.lower().find(pal)
            byte_p = f"B:{texto_a.encode('utf-8')[idx if idx>=0 else 0]:02x}"
            return byte_p, 'conteudo_mas_parcial', pal, pal
        return self._byte_bridge(topico_a, topico_b)
    
    def _byte_bridge(self, topico_a, topico_b):
        mk_a = self.topicos[topico_a]['mcr_byte']
        mk_b = self.topicos[topico_b]['mcr_byte']
        texto_a = self.topicos[topico_a]['texto']
        inicio = f"B:{texto_a.encode('utf-8')[0]:02x}"
        seq = mk_a.gerar(inicio, 8)
        estados_b = set(mk_b.freq.keys())
        for e in seq:
            if e in estados_b:
                c = chr(int(e[2:], 16)) if e.startswith('B:') else '?'
                return e, 'byte_only', c, c
        for e in seq:
            if e in self.mcr_byte.freq:
                prox, _ = self.mcr_byte.predizer(e)
                if prox and prox in estados_b:
                    c = chr(int(e[2:], 16))
                    return e, 'byte_only', c, c
        return None, 'none', '', ''
    
    def _autoavaliar_multinivel(self, sequencia, texto_a, texto_b, tipo_ponte):
        if not sequencia or len(sequencia.strip()) < _MCR_THRESHOLD_TAMANHO.obter('min_seq', 3):
            return 0.0, {'erro': 'vazia'}
        j_a = self.mcr_byte.jaccard_bytes(sequencia, texto_a)
        j_b = self.mcr_byte.jaccard_bytes(sequencia, texto_b)
        seq_bytes = sequencia.encode('utf-8')
        trans_ok = 0
        for i in range(len(seq_bytes)-1):
            e = f"B:{seq_bytes[i]:02x}"
            p = f"B:{seq_bytes[i+1]:02x}"
            if e in self.mcr_byte.transicoes and p in self.mcr_byte.transicoes.get(e, {}):
                trans_ok += 1
        c_byte = trans_ok / max(len(seq_bytes)-1, 1)
        thr_byte = _MCR_THRESHOLD_CONEXAO.obter('jaccard_byte', 0.3)
        nb = (0.5 if j_a < thr_byte else 0) + (0.5 if j_b < thr_byte else 0) \
             + min(2.0, c_byte * 4)
        pal_seq = sequencia.split()
        c_pal = sum(1 for p in pal_seq if p in self.mcr_palavra.freq)/max(len(pal_seq), 1)
        thr_pal = _MCR_THRESHOLD_PALAVRA.obter('min_palavra', 4)
        cont_a = {p.lower() for p in texto_a.split() if len(p) >= thr_pal}
        cont_b = {p.lower() for p in texto_b.split() if len(p) >= thr_pal}
        cont_seq = {p.lower() for p in pal_seq if len(p) >= thr_pal}
        np = (1.0 if c_pal > 0 else 0) + min(2.0, len(cont_seq & cont_a) * 0.4) \
             + min(2.0, len(cont_seq & cont_b) * 0.4) + min(2.0, c_pal * 3)
        c_tok = 0
        if len(pal_seq) > 1:
            c_tok = sum(1 for i in range(len(pal_seq)-1)
                       if pal_seq[i][0].upper() in self.mcr_token.transicoes
                       and pal_seq[i+1][0].upper() in self.mcr_token.transicoes.get(pal_seq[i][0].upper(), {}))
            c_tok /= (len(pal_seq)-1)
        tipos_a = {p[0].upper() for p in texto_a.split() if p}
        tipos_b = {p[0].upper() for p in texto_b.split() if p}
        tipos_seq = {p[0].upper() for p in pal_seq if p}
        thr_tok = _MCR_THRESHOLD_CONEXAO.obter('token_tipos', 0.3)
        nt = (0.5 if tipos_seq & tipos_a else 0) + (0.5 if tipos_seq & tipos_b else 0) \
             + min(3.0, c_tok * 10)
        penalidade = _MCR_THRESHOLD_CONEXAO.obter(f'penalidade_{tipo_ponte}',
                                                    0.3 if tipo_ponte == 'byte_only' else
                                                    0.1 if tipo_ponte == 'none' else 1.0)
        nota = self._peso_nota.calcular(
            byte_s=min(10, nb * 3),
            palavra_s=min(10, np * 2),
            token_s=min(10, nt * 3),
        )
        nota = max(0, min(10, nota * penalidade))
        _MCR_THRESHOLD_CONEXAO.aprender(f'byte_{tipo_ponte}', nb/4)
        _MCR_THRESHOLD_CONEXAO.aprender(f'palavra_{tipo_ponte}', np/6)
        self._peso_nota.aprender(
            {'byte': nb/4, 'palavra': np/6, 'token': nt/4},
            nota/10
        )
        return nota, {
            'byte': {'diff_a': round(j_a,3), 'diff_b': round(j_b,3), 'nota': round(nb,2)},
            'palavra': {'existe': round(c_pal,3), 'nota': round(np,2)},
            'token': {'coerencia': round(c_tok,3), 'nota': round(nt,2)},
            'penalidade': penalidade, 'nota_final': round(nota,2),
        }
    
    def explorar_todos(self):
        conexoes = []
        nomes = list(self.topicos.keys())
        for i in range(len(nomes)):
            for j in range(i+1, len(nomes)):
                res = self.conectar(nomes[i], nomes[j])
                if res: conexoes.append(res)
        return conexoes
    
    def debug(self, conexao: dict) -> str:
        if not conexao: return "(sem conexao)"
        linhas = [f"DEBUG CONEXAO: {conexao.get('topico_a','?')} <-> {conexao.get('topico_b','?')}"]
        linhas.append(f"  Ponte: {conexao.get('palavra_a','?')} -> {conexao.get('palavra_b','?')} ({conexao.get('tipo_ponte','?')})")
        linhas.append(f"  Sequencia: {conexao.get('sequencia','')}")
        linhas.append(f"  Nota: {conexao.get('nota',0)}/10")
        det = conexao.get('detalhes_nota', {})
        if 'byte' in det:
            linhas.append(f"  Byte: {det['byte'].get('nota',0):.1f}/2 (diff_a={det['byte'].get('diff_a',0):.3f})")
        if 'palavra' in det:
            linhas.append(f"  Palavra: {det['palavra'].get('nota',0):.1f}/5")
        if 'token' in det:
            linhas.append(f"  Token: {det['token'].get('nota',0):.1f}/3")
        linhas.append(f"  Penalidade: x{det.get('penalidade',1)}")
        return '\n'.join(linhas)


class MCRCadeia:
    """Gera N tokens sem repetir, reinjetando contexto a cada passo."""
    
    def __init__(self, conector: MCRConector = None):
        self.conector = conector or MCRConector()
        self.detector = MCREntropia()
        self.ruido = MCRRuido()
        self.historico_ciclos = []
        # Controle de estados compostos (evitae explosao)
        self._freq_compostos = {}
        self._total_compostos = 0
    
    def gerar(self, semente: str, n_tokens: int = 100,
              contexto_tamanho: int = 3, max_tentativas_loop: int = 5,
              top_k: int = 3,
              contexto_sintatico: dict = None) -> dict:
        """Gera N tokens com suporte opcional a estados compostos.
        
        Args:
            semente: token inicial
            n_tokens: numero maximo de tokens
            contexto_tamanho: janela de contexto
            max_tentativas_loop: max tentativas antes de abortar loop
            top_k: top K predicoes para amostragem
            contexto_sintatico: dict com contexto estrutural para compose_state()
                                (ex: {"linguagem": "csharp", "em_bloco": "metodo"})
        """
        from .engine import compose_state, compor_contexto
        import random
        if not self.conector.topicos:
            return {'texto': semente, 'tokens': [semente],
                    'nota': 0, 'loops_detectados': 0, 'erro': 'sem topicos'}
        mk_byte = self.conector.mcr_byte
        mk_palavra = self.conector.mcr_palavra
        mk_token = self.conector.mcr_token
        mk_decisor = MCRDecisor('cadeia_nivel')
        tokens_gerados = [semente]
        loops_detectados = 0
        repeticoes_evitadas = 0
        tentativas_loop = 0
        nivel_atual = 'palavra'
        ctx_sint = dict(contexto_sintatico or {})
        
        for passo in range(n_tokens - 1):
            if len(tokens_gerados) >= contexto_tamanho:
                contexto = tokens_gerados[-contexto_tamanho:]
            else:
                contexto = tokens_gerados
            ultimo = str(contexto[-1])
            
            # Se temos contexto sintatico, usa estado composto
            if ctx_sint:
                estado_pred = compose_state(ultimo, ctx_sint)
            else:
                estado_pred = ultimo
            
            tipo_ultimo = MCR.classificar_token(ultimo)
            esta_em_loop = self.detector.esta_em_loop()
            estado_decisao = f"tipo:{tipo_ultimo}_loop:{esta_em_loop}_nivel:{nivel_atual}"
            nivel_acao = mk_decisor.decidir(estado_decisao)
            niveis_validos = ('byte', 'palavra', 'token')
            for nv in niveis_validos:
                if nv in nivel_acao.lower():
                    nivel_atual = nv
                    break
            prox = None
            conf = 0.0
            if nivel_atual == 'byte':
                mk = mk_byte
                preds = mk.predizer_n(estado_pred, n=top_k)
                if preds:
                    pesos = [c for _, c in preds]
                    total = sum(pesos)
                    r = random.uniform(0, total)
                    acum = 0
                    for p_str, p_conf in preds:
                        acum += p_conf
                        if r <= acum:
                            prox = p_str
                            conf = p_conf
                            break
                if prox is None:
                    prox, conf = mk.predizer(estado_pred)
                if prox is not None:
                    if str(prox).startswith('B:'):
                        try: prox = chr(int(str(prox)[2:], 16))
                        except Exception: pass
            elif nivel_atual == 'token':
                mk = mk_token
                tok_key = estado_pred[0].upper() if estado_pred else '?'
                preds = mk.predizer_n(tok_key, n=top_k)
                if preds:
                    pesos = [c for _, c in preds]
                    total = sum(pesos)
                    r = random.uniform(0, total)
                    acum = 0
                    for p_str, p_conf in preds:
                        acum += p_conf
                        if r <= acum:
                            prox = p_str
                            conf = p_conf
                            break
                if prox is None:
                    prox, conf = mk.predizer(tok_key)
                if prox is not None:
                    prox = str(prox)
            else:
                mk = mk_palavra
                preds = mk.predizer_n(estado_pred, n=top_k)
                if preds:
                    pesos = [c for _, c in preds]
                    total = sum(pesos)
                    r = random.uniform(0, total)
                    acum = 0
                    for p_str, p_conf in preds:
                        acum += p_conf
                        if r <= acum:
                            prox = p_str
                            conf = p_conf
                            break
                if prox is None:
                    prox, conf = mk.predizer(estado_pred)
                if prox is None:
                    prox, conf = mk.predizer(semente)
                if prox is None or conf < 0.01:
                    break
            if prox is None:
                break
            token_str = str(prox)
            
            # Atualiza contexto sintatico com o token gerado
            if ctx_sint is not None:
                ctx_sint = compor_contexto([token_str], ctx_sint)
                # Conta estados compostos
                composto = compose_state(token_str, ctx_sint)
                self._freq_compostos[composto] = self._freq_compostos.get(composto, 0) + 1
                self._total_compostos += 1
                if self._total_compostos % 1000 == 0 and len(self._freq_compostos) > 10000:
                    print('[MCRCadeia] Atencao: %d estados compostos unicos (limiar 10000)' % len(self._freq_compostos))
            
            self.detector.alimentar(token_str)
            em_loop = self.detector.esta_em_loop()
            if em_loop:
                loops_detectados += 1
                tentativas_loop += 1
                if tentativas_loop > max_tentativas_loop: break
                melhor_ruido = self.ruido.melhor_tipo()
                if nivel_atual == 'palavra':
                    nivel_atual = 'byte'
                elif nivel_atual == 'byte':
                    nivel_atual = 'token'
                else:
                    nivel_atual = 'palavra'
                self.ruido.registrar(melhor_ruido, True)
                continue
            tokens_gerados.append(token_str)
        texto = ' '.join(tokens_gerados)
        palavras = texto.split()
        n_palavras = len(palavras)
        if n_palavras >= 4:
            bigramas = [' '.join(palavras[i:i+2]) for i in range(n_palavras-1)]
            repeticao = 1.0 - (len(set(bigramas)) / max(len(bigramas), 1))
        else:
            repeticao = 0.0
        nota = 10.0
        loops_nao_quebrados = max(0, loops_detectados - repeticoes_evitadas)
        pen_loop = _MCR_THRESHOLD_REPETICAO.obter('penalidade_loop', 2.0)
        if loops_nao_quebrados > 0: nota -= loops_nao_quebrados * pen_loop
        thr_rep = _MCR_THRESHOLD_REPETICAO.obter('limiar_repeticao', 0.3)
        if repeticao > thr_rep: nota -= (repeticao - thr_rep) * 10
        nota = max(1, min(10, nota))
        _MCR_THRESHOLD_REPETICAO.aprender('penalidade_loop', pen_loop * 0.99 + (loops_nao_quebrados/3) * 0.01)
        _MCR_THRESHOLD_REPETICAO.aprender('limiar_repeticao', thr_rep * 0.99 + repeticao * 0.01)
        return {
            'texto': texto,
            'tokens': tokens_gerados,
            'n_tokens': len(tokens_gerados),
            'nota': round(nota, 1),
            'loops_detectados': loops_detectados,
            'repeticoes_evitadas': repeticoes_evitadas,
            'repeticao_final': round(repeticao, 3),
        }


class MCRBufferKG:
    """Buffer de operacoes do KG (singleton, evita recarregar)."""
    
    _instancia = None
    _kg = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._buffer = []
            cls._instancia._buffer_limite = 20
            cls._instancia.mk = MCR("buffer_kg")
            cls._instancia._kg = None
        return cls._instancia
    
    @property
    def kg(self):
        if self._kg is None:
            try:
                from modulos.kg import KnowledgeGraph
                self._kg = KnowledgeGraph()
            except Exception:
                self._kg = None
        return self._kg
    
    def aprender(self, erro, solucao, ctx='buffer', **kwargs):
        if not self.kg: return
        self._buffer.append({'erro': erro, 'solucao': solucao, 'ctx': ctx})
        if len(self._buffer) >= self._buffer_limite:
            self.flush()
    
    def flush(self):
        if not self._buffer or not self.kg: return
        n = len(self._buffer)
        for item in self._buffer:
            self.kg.aprender_conceito(item['erro'], item['solucao'], ctx=item['ctx'])
        self._buffer = []
        self.mk.aprender("FLUSH", f"{n} lessons salvas")
    
    def aprender_conceito(self, erro, solucao, ctx='buffer'):
        """Compatibilidade com KnowledgeGraph.aprender_conceito()."""
        if self.kg and hasattr(self.kg, 'aprender_conceito'):
            self.kg.aprender_conceito(erro, solucao, ctx=ctx)
    
    def buscar(self, termo, max_r=5, pergunta=''):
        resultados = []
        for item in self._buffer:
            if termo.lower() in item.get('erro', '').lower() or termo.lower() in item.get('solucao', '').lower():
                resultados.append(item)
        if self._kg and hasattr(self._kg, 'buscar'):
            try:
                kg_results = self._kg.buscar(termo, max_r=max_r)
                if kg_results:
                    resultados.extend(kg_results if isinstance(kg_results, list) else [kg_results])
            except Exception:
                pass
        return resultados[:max_r]


class MCRKGAuto:
    """Organiza o KG automaticamente: categoriza, dedup, limpa.
    
    Tudo MCR: categorias sao descobertas por prefixo do ctx,
    duplicatas sao detectadas por Jaccard, limpeza por MCRSignature.
    """
    
    def __init__(self, kg=None):
        self.kg = kg or (_get_kg())
        self.mk_cat = MCR("categorias")
        self.mk_dedup = MCR("dedup")
        self.mk_qualidade = MCR('qualidade_lesson')
        for _txt in ['SPA e o sistema de progressao do aventureiro',
                     'Eridanus e a cidade inicial do projeto MCR',
                     'O SHC gerencia habilidades contextuais em 5 camadas']:
            sig = MCRSignature.extrair(_txt, rapido=True)
            self.mk_qualidade.aprender(f"ENT:{int(sig['entropia']*10)}_EST:{sig['estados']}", "UTIL")
        for _txt in ['{"nome": "teste", "valor": 123}',
                     '_flush_20260101_000000',
                     "{\'fragmento\': \'texto\', \'score\': 0.5}"]:
            sig = MCRSignature.extrair(_txt, rapido=True)
            self.mk_qualidade.aprender(f"ENT:{int(sig['entropia']*10)}_EST:{sig['estados']}", "LIXO")
    
    @staticmethod
    def _classificar_qualidade(sol: str) -> float:
        if not sol or len(sol) < 10:
            return 0.0
        sig = MCRSignature.extrair(sol, rapido=True)
        fp = sig.get('fingerprint', [])
        if not fp:
            return 0.0
        fp_chave = '_'.join(str(int(v*10)) for v in fp)
        pred = _get_mk_qualidade().predizer(fp_chave)
        if pred[0] is not None and pred[1] > 0.2:
            if pred[0] == 'UTIL':
                return 0.9
            elif pred[0] == 'LIXO':
                return 0.1
        return 0.5
    
    def categorizar(self) -> dict:
        if not self.kg: return {}
        licoes = self.kg._get_licoes()
        cats = {}
        for l in licoes:
            ctx = l.get('ctx', '?')
            sol = l.get('solucao', '')
            cat = ctx.split('_')[0] if '_' in ctx else ctx
            if cat and cat[0].isdigit(): cat = 'numerico'
            if cat not in cats: cats[cat] = []
            cats[cat].append(l)
            self.mk_cat.aprender(f"CTX:{ctx}", f"CAT:{cat}")
        return cats
    
    def dedup(self, min_similaridade: float = 0.95) -> int:
        if not self.kg: return 0
        licoes = self.kg._get_licoes()
        if len(licoes) < 50: return 0
        removidas = 0
        inativas = sum(1 for l in licoes if l.get('inactive'))
        if inativas > len(licoes) * 0.05:
            return 0
        buckets = {}
        for i, l in enumerate(licoes):
            sol = l.get('solucao', '')
            if not sol or len(sol) < 30: continue
            h = hash(sol) % 50
            buckets.setdefault(h, []).append((i, l))
        for h, grupo in buckets.items():
            n = len(grupo)
            if n < 2: continue
            if n > 50:
                continue
            for i in range(n):
                if grupo[i][1].get('inactive'): continue
                for j in range(i + 1, n):
                    if grupo[j][1].get('inactive'): continue
                    sol_i = grupo[i][1].get('solucao', '')
                    sol_j = grupo[j][1].get('solucao', '')
                    if not sol_i or not sol_j: continue
                    jac = MCR("tmp").jaccard_bytes(sol_i, sol_j)
                    if jac >= min_similaridade:
                        if len(sol_i) <= len(sol_j):
                            grupo[i][1]['inactive'] = True
                        else:
                            grupo[j][1]['inactive'] = True
                        removidas += 1
                        self.mk_dedup.aprender("DUPLICATA_BUCKET", f"JAC:{jac:.2f}")
        if removidas:
            self.kg.salvar()
            self.mk_dedup.aprender("TOTAL_REMOVIDAS", str(removidas))
        return removidas
    
    def limpar(self) -> dict:
        if not self.kg: return {'removidos': 0, 'mantidos': 0}
        licoes = self.kg._get_licoes()
        removidos = 0
        mantidos = 0
        for l in licoes:
            if l.get('inactive'): continue
            sol = l.get('solucao', '')
            qualidade = self._classificar_qualidade(sol)
            if qualidade < 0.3:
                l['inactive'] = True; removidos += 1
            elif qualidade < 0.5:
                l['inactive'] = True; removidos += 1
                self.mk_cat.aprender("DUVIDOSO", l.get('ctx', '?'))
            else:
                mantidos += 1
        if removidos:
            self.kg.salvar()
        return {'removidos': removidos, 'mantidos': mantidos}
    
    def registrar_consumo(self, sol: str):
        if not sol: return
        _registrar_consumo_global(sol)
        self.mk_cat.aprender("CONSUMO", sol)
    
    def organizar(self) -> dict:
        cats = self.categorizar()
        removidos_dedup = self.dedup()
        limpeza = self.limpar()
        return {
            'categorias': len(cats),
            'distribuicao': {c: len(v) for c, v in sorted(cats.items(), key=lambda x: -len(x[1]))},
            'dedup_removidos': removidos_dedup,
            'limpeza': limpeza,
            'stats_mk': self.mk_cat.stats(),
        }


def _get_mk_qualidade():
    if not hasattr(_get_mk_qualidade, '_mk'):
        _get_mk_qualidade._mk = MCR('qualidade_global')
    return _get_mk_qualidade._mk


def _registrar_consumo_global(sol: str):
    if not sol: return
    sig = MCRSignature.extrair(sol, rapido=True)
    fp = sig.get('fingerprint', [])
    if fp:
        fp_chave = '_'.join(str(int(v*10)) for v in fp)
        _get_mk_qualidade().aprender(fp_chave, 'UTIL')


def _buscar_kg_task(termo, pergunta, conector=None):
    kg = _get_kg()
    if not kg:
        return []
    lessons = kg.buscar(termo, max_r=10, pergunta=pergunta)
    if conector:
        for i, l in enumerate(lessons):
            sol = l.get('solucao', '') or l.get('erro', '')
            if sol:
                conector.alimentar(sol, f"kg_{i}")
    return [l.get('solucao', '') for l in lessons]
