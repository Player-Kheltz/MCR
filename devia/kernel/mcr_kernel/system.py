#!/usr/bin/env python3
"""system.py — System orchestration, question answering, and narrative generation.

MCRSystem, MCRPergunta, MCRMestre, MCRMestreV2, MCRGeracao,
AutoavaliadorSemantico, GeradorNarrativa.
"""
import os, re, json, math, time as _time
from typing import Dict, List, Tuple

from .engine import MCR, MCRBridge
from .signature import MCRSignature, MCRFingerprint
from .decisor import (
    MCRPesoNota, MCREntropia, MCRDecisor, MCRDiagnostico, MCRThreshold,
    _MCR_THRESHOLD_TAMANHO, _MCR_THRESHOLD_REPETICAO,
    _MCR_THRESHOLD_CONF, _MCR_THRESHOLD_NOTA,
    _MCR_THRESHOLD_PALAVRA, _MCR_THRESHOLD_FILTRO,
)
from .memory import _get_kg, MCRConector, MCRCadeia, _registrar_consumo_global, _buscar_kg_task
from .evolution import MCRExpansao


class AutoavaliadorSemantico:
    """Avalia texto usando MCRSignature + MCRPesoNota."""
    
    def __init__(self, kg=None, precache=None):
        self.kg = kg or (_get_kg())
        self.precache = precache
        self.peso_nota = MCRPesoNota("autoavaliador")
        self.entropia = MCREntropia()
    
    def avaliar(self, texto: str, dominio_esperado='lore') -> dict:
        if not texto or len(texto) < _MCR_THRESHOLD_TAMANHO.obter('min_texto', 20):
            return {'nota': 0.0, 'diagnostico': 'MUITO_CURTO',
                    'detalhes': {'entropia': 0, 'repeticao': 0,
                                 'n_palavras': 0, 'fingerprint': []}}
        sig = MCRSignature.extrair(texto)
        entropia = sig.get('entropia', 0)
        estados = sig.get('estados', 0)
        transicoes = sig.get('transicoes', 0)
        fingerprint = sig.get('fingerprint', [])
        palavras = texto.lower().split()
        n_palavras = len(palavras)
        self.entropia = MCREntropia()
        for p in palavras:
            self.entropia.alimentar(p)
        rep_detectada = 1.0 if self.entropia.esta_em_loop() else 0.0
        originalidade = 1.0
        if self.kg:
            try:
                for l in self.kg._get_licoes():
                    sol = l.get('solucao', '')
                    if sol and len(sol) > _MCR_THRESHOLD_TAMANHO.obter('min_lesson', 50):
                        jac = MCR.jaccard_bytes(texto, sol)
                        thr_copia = _MCR_THRESHOLD_REPETICAO.obter('copia', 0.8)
                        thr_parcial = _MCR_THRESHOLD_REPETICAO.obter('parcial', 0.5)
                        if jac > thr_copia:
                            originalidade = 0.25
                            break
                        elif jac > thr_parcial:
                            originalidade = max(0.5, originalidade - 0.25)
            except Exception:
                pass
        nota = self.peso_nota.calcular(
            byte_s=min(10, entropia * 3),
            palavra_s=min(10, estados * 0.5),
            token_s=min(10, (1 - rep_detectada) * 10),
        )
        nota = max(0, min(10, nota * originalidade))
        mk_diag = MCR('diagnostico_av')
        estado_diag = f"ent:{int(entropia*2)}_est:{estados}_rep:{int(rep_detectada*3)}"
        diag_pred = mk_diag.predizer(estado_diag)
        if diag_pred[0] is not None and diag_pred[1] > 0.3:
            diag = str(diag_pred[0])
        else:
            diag = ('NARRATIVO_COERENTE' if nota >= 7 else
                    'ESTRUTURADO' if nota >= 5 else
                    'FRACO' if nota >= 3 else
                    'GARBAGE' if nota >= 1 else 'VAZIO')
        _MCR_THRESHOLD_CONF.aprender(f"entropia_{dominio_esperado}", min(1.0, entropia / 5))
        self.peso_nota.aprender(
            {'byte': entropia / 5, 'palavra': estados / 30, 'token': 1 - rep_detectada},
            nota / 10
        )
        return {
            'nota': round(nota, 1),
            'diagnostico': diag,
            'detalhes': {
                'entropia': round(entropia, 3),
                'estados': estados,
                'transicoes': transicoes,
                'repeticao': round(rep_detectada, 3),
                'n_palavras': n_palavras,
                'originalidade': round(originalidade, 3),
                'fingerprint': fingerprint,
            }
        }


class GeradorNarrativa:
    """Gera texto narrativo usando MarkovPalavra + contexto longo do KG."""
    
    def __init__(self, kg=None, precache=None):
        self.kg = kg or (_get_kg())
        self.precache = precache
        self.mk_palavra = MCR("narrativa_palavras")
        self.semantico = AutoavaliadorSemantico(kg, precache)
        self.contexto_usado = ""
        self._textos_lore_cache = []
    
    def _carregar_textos_lore(self):
        if self._textos_lore_cache:
            return self._textos_lore_cache
        textos = []
        path_id = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docs', 'MCR_IDENTITY.md')
        if os.path.exists(path_id):
            with open(path_id, 'r', encoding='utf-8') as f:
                textos.append(f.read())
        if self.kg:
            for l in self.kg._get_licoes():
                ctx = l.get('ctx', '')
                sol = l.get('solucao', '')
                if ctx in ('lore', 'conceito', 'identidade', 'tokenizer_cluster',
                           'tokenizer_dominio') and sol and len(sol) > 30:
                    textos.append(sol)
        docs_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docs')
        if os.path.isdir(docs_dir):
            for fname in os.listdir(docs_dir):
                if fname.endswith('.md') and fname[0] != '_':
                    try:
                        with open(os.path.join(docs_dir, fname), 'r', encoding='utf-8') as f:
                            textos.append(f.read())
                    except: pass
        self._textos_lore_cache = textos
        return textos
    
    def preparar_contexto(self, tema, max_lessons=50):
        if not self.kg:
            self.contexto_usado = f"Contexto sobre {tema} (KG indisponivel)"
            return self.contexto_usado
        textos_lore = self._carregar_textos_lore()
        lessons = self.kg.buscar_expandido(tema, max_r=max_lessons)
        partes = [f"Contexto sobre {tema}:\n"]
        n_lessons = 0
        mk_temp = MCR("filtro")
        for l in lessons:
            sol = l.get('solucao', '')
            if not sol or len(sol) < 30: continue
            jac = mk_temp.jaccard_bytes(tema, sol)
            if jac < 0.02: continue
            ctx = l.get('ctx', '')
            erro = l.get('erro', '')
            partes.append(f"[{ctx}] {erro}: {sol}")
            n_lessons += 1
        for texto in textos_lore:
            if len(texto) > 100:
                partes.append(f"[CORPUS] {texto}")
                n_lessons += 1
        self.contexto_usado = '\n\n'.join(partes)
        return self.contexto_usado
    
    def gerar(self, tema='Eridanus', max_palavras=100, temperatura=0.3):
        contexto = self.preparar_contexto(tema, max_lessons=50)
        texto_limpo = re.sub(r'[<>*#\[\]]', ' ', contexto)
        palavras = texto_limpo.split()
        self.mk_palavra = MCR(f"narrativa_{tema}")
        if len(palavras) < 10:
            return {'texto': f"[MCR] Contexto insuficiente sobre {tema}",
                    'tamanho_chars': 0, 'tamanho_palavras': 0,
                    'contexto_chars': len(contexto),
                    'n_lessons_usadas': 0,
                    'avaliacao': self.semantico.avaliar('', 'lore')}
        self.mk_palavra.aprender_sequencia(palavras)
        semente = palavras[0] if palavras else tema
        gerado = self.mk_palavra.gerar(semente, max_palavras)
        texto = ' '.join(str(g) for g in gerado)
        avaliacao = self.semantico.avaliar(texto, 'lore')
        return {
            'texto': texto,
            'tamanho_chars': len(texto),
            'tamanho_palavras': len(gerado),
            'contexto_chars': len(contexto),
            'n_lessons_usadas': contexto.count('['),
            'avaliacao': avaliacao,
        }
    
    def gerar_com_loop(self, tema='Eridanus', max_iter=3):
        melhor = None
        for i in range(max_iter):
            n_lessons = 20 + i * 30
            resultado = self.gerar(tema, max_palavras=100, temperatura=0.3)
            nota_sem = resultado['avaliacao']['nota']
            if melhor is None or nota_sem > melhor['avaliacao']['nota']:
                melhor = resultado
            if nota_sem >= 5.0:
                break
        return melhor


def termo_relevante(pergunta: str, linha: str) -> bool:
    termos = [p.lower() for p in pergunta.split() if len(p) > 3]
    linha_lower = linha.lower()
    return any(t in linha_lower for t in termos) if termos else True


class MCRSystem:
    """Classe SISTEMA do MCR. Orquestrador de alto nivel."""
    
    def __init__(self, kg=None):
        self.kg = kg or (_get_kg())
        self.conector = None
        self.mk = MCR("system")
    
    def _perceber(self, texto: str) -> Dict:
        mk_bytes = MCR("percepcao")
        dados = texto.encode('utf-8')
        mk_bytes.aprender_sequencia(list(dados))
        entropia = mk_bytes.entropia_media()
        return {'texto': texto, 'entropia': round(entropia, 3),
                'bytes': len(dados), 'estados': len(mk_bytes.transicoes)}
    
    def _autoavaliar(self, resposta: str, pergunta: str) -> Tuple[float, Dict]:
        if not resposta: return 0.0, {'motivo': 'vazio'}
        mk = MCR("autoavaliar")
        j_byte = mk.jaccard_bytes(pergunta, resposta)
        j_byte_pond = mk.jaccard_bytes_ponderado(pergunta, resposta)
        h_pergunta = mk.entropia_sequencia(list(pergunta.encode()))
        h_resposta = mk.entropia_sequencia(list(resposta.encode()))
        comp = mk.similaridade_transicoes(pergunta, resposta)
        nota = 0.0
        nota += min(3.0, j_byte * 5)
        nota += min(3.0, j_byte_pond * 4)
        nota += min(2.0, comp * 3)
        nota += min(2.0, min(h_resposta, 4.0) / 2.0)
        return round(min(10, nota), 1), {
            'jaccard_byte': round(j_byte, 3),
            'jaccard_ponderado': round(j_byte_pond, 3),
            'similaridade': round(comp, 3),
            'entropia_resposta': round(h_resposta, 3),
        }
    
    def _filtrar_lessons(self, pergunta: str, lessons: List[Dict], mk_byte=None):
        return [l for l in lessons
                if l.get('solucao', '') and len(l.get('solucao', '')) > 30
                and termo_relevante(pergunta, l.get('solucao', ''))]
    
    def _extrair_termo(self, texto: str) -> str:
        palavras = [p for p in texto.split() if len(p) > 3 and p[0].isupper()]
        return palavras[0] if palavras else texto.split()[0] if texto.split() else texto
    
    def _decidir(self, estado: Dict) -> Tuple[str, float]:
        chave = f"b:{int(estado.get('bytes',0)/100)}_e:{int(estado.get('entropia',0)*10)}"
        acao, conf = self.mk.predizer(chave)
        if acao is None or conf < 0.3:
            if estado.get('entropia', 0) > 4.0: acao = 'conectar'
            elif estado.get('bytes', 0) > 1000: acao = 'extrair'
            else: acao = 'aprender'
        return acao, conf
    
    def _executar(self, acao: str, estado: Dict) -> Tuple[str, str]:
        from .memory import MCRCadeia
        self.conector = MCRConector()
        texto = estado.get('texto', '')
        if acao == 'conectar':
            palavras = texto.split()
            for i, p in enumerate(palavras):
                if i < len(palavras) - 1:
                    nm = f"pal_{i}"
                    self.conector.alimentar(palavras[i], nm)
                    self.conector.conectar(nm, list(self.conector.topicos.keys())[0] if self.conector.topicos else nm)
            return 'conexoes', f"{len(self.conector.topicos)} topicos"
        elif acao == 'aprender':
            if self.kg:
                nome_base = self._extrair_termo(texto)
                self.kg.aprender_conceito(f"percepcao:{nome_base}", texto, ctx="percepcao_auto")
            return 'kg', 'aprendido'
        elif acao == 'extrair':
            semente = self._extrair_termo(texto)
            cadeia = MCRCadeia(self.conector)
            res = cadeia.gerar(semente, n_tokens=30)
            return 'gerado', res.get('texto', '')
        return 'none', 'acao_desconhecida'
    
    def _responder(self, estado: Dict, conhecimento: str) -> str:
        texto = estado.get('texto', '')
        if conhecimento:
            return f"{conhecimento[:200]} [baseado em {len(texto)} bytes]"
        return f"[MCR] Percebi {estado.get('bytes',0)} bytes com entropia {estado.get('entropia',0):.2f}"
    
    def ciclo_unico(self, origem: str, max_bytes: int = 5000) -> dict:
        import time
        t0 = time.time()
        resultado = {'origem': origem, 'etapas': []}
        if os.path.isfile(origem):
            with open(origem, 'rb') as f:
                dados = f.read(max_bytes)
        else:
            dados = origem.encode('utf-8')
        mk_byte = MCR(f"ciclo_byte")
        mk_byte.aprender_sequencia(list(dados))
        resultado['etapas'].append(f"bytes:{len(dados)}")
        entropia = mk_byte.entropia_media()
        n_estados = len(mk_byte.transicoes)
        resultado['entropia'] = round(entropia, 3)
        resultado['estados'] = n_estados
        if entropia < 2.0:
            tipo = "binario_estruturado"
        elif entropia < 4.0:
            tipo = "texto_estruturado"
        elif entropia < 6.0:
            tipo = "texto_livre"
        else:
            tipo = "dados_aleatorios"
        resultado['tipo'] = tipo
        resultado['etapas'].append(f"tipo:{tipo}")
        try:
            texto = dados.decode('utf-8', errors='replace')
            palavras = texto.split()
            if len(palavras) > 2:
                mk_palavra = MCR(f"ciclo_palavra")
                mk_palavra.aprender_sequencia(palavras)
                resultado['palavras_unicas'] = len(set(palavras))
                resultado['etapas'].append(f"palavras:{len(palavras)}")
        except:
            pass
        if self.kg:
            nome_base = os.path.basename(origem) if os.path.isfile(origem) else "texto_direto"
            self.kg.aprender_conceito(
                f"ciclo:{nome_base}",
                f"Tipo: {tipo}, Entropia: {entropia:.2f}, Bytes: {len(dados)}. "
                f"Estados: {n_estados}. Origem: {origem}.",
                ctx="ciclo_unico"
            )
            resultado['etapas'].append("kg:salvo")
        nota = 5.0
        if entropia > 2.0: nota += 2.0
        if n_estados > 20: nota += 2.0
        if resultado.get('palavras_unicas', 0) > 10: nota += 1.0
        resultado['nota'] = round(min(10, nota), 1)
        resultado['etapas'].append(f"nota:{resultado['nota']}")
        if nota >= 5.0:
            try:
                conector = MCRConector()
                conector.alimentar(texto if 'texto' in dir() else origem, "ciclo_entrada")
                for nome, dados_t in list(conector.topicos.items()):
                    if nome != "ciclo_entrada":
                        cx = conector.conectar("ciclo_entrada", nome)
                        if cx:
                            resultado['conexao'] = cx.get('nota', 0)
                            resultado['etapas'].append(f"conexao:{cx.get('nota',0)}")
                            break
            except:
                pass
        resultado['tempo'] = round(time.time() - t0, 2)
        return resultado


class MCRPergunta:
    """Responde perguntas usando MCR puro (sem LLM)."""
    
    def __init__(self, kg=None):
        self.kg = kg or (_get_kg())
        self.conector = MCRConector()
        self.cadeia = MCRCadeia(self.conector)
        self.semantico = AutoavaliadorSemantico(kg, None)
        self.diagnostico = MCRDiagnostico()
        self.peso_nota = MCRPesoNota("pergunta_peso")
        self.expansao = MCRExpansao(self.kg)
        self.log = []
    
    @staticmethod
    def _limpar_texto(texto: str) -> str:
        if not texto: return ''
        if texto.strip().startswith('{') or texto.strip().startswith('['):
            import re
            for campo in ['solucao', 'fragmento', 'texto', 'resposta']:
                m = re.search(r'"{0}"\s*:\s*"([^"]+)"'.format(campo), texto)
                if m: return m.group(1)
            texto = re.sub(r'[{}"\\]', '', texto)
        texto = texto.replace('\\u00e3', 'ã').replace('\\u00e1', 'á')
        texto = texto.replace('\\u00e9', 'é').replace('\\u00ed', 'í')
        texto = texto.replace('\\u00f3', 'ó').replace('\\u00fa', 'ú')
        texto = texto.replace('\\u00e7', 'ç').replace('\\u00f5', 'õ')
        texto = texto.replace('\\u00ea', 'ê').replace('\\u00f4', 'ô')
        texto = texto.replace('\\u00e2', 'â').replace('\\u00ee', 'î')
        texto = texto.replace('\\u00fb', 'û').replace('\\u00c1', 'Á')
        texto = texto.replace('\\u00c9', 'É').replace('\\u00d3', 'Ó')
        texto = texto.replace('**', '')
        return texto.strip()
    
    @staticmethod
    def _filtrar_lesson(sol: str, mk_byte=None) -> bool:
        if not sol or len(sol) < 20: return False
        if mk_byte:
            from collections import Counter
            import math
            dados = sol.encode('utf-8')
            freq = {}
            for b in dados: freq[b] = freq.get(b, 0) + 1
            n = len(dados)
            h = 0.0
            for c in freq.values():
                p = c / n
                if p > 0: h -= p * math.log2(p)
            if h < _MCR_THRESHOLD_FILTRO.calcular(1.0):
                return False
        if sol.strip().startswith('{') or sol.strip().startswith('['):
            return False
        if sol.startswith('[') and ']' in sol:
            return False
        return True
    
    @staticmethod
    def _ranquear_por_assinatura(lessons: list, pergunta: str = '') -> list:
        if not lessons or not pergunta:
            return lessons
        sig_pergunta = MCRSignature.extrair(pergunta)
        fp_pergunta = sig_pergunta.get('fingerprint', [])
        if not fp_pergunta:
            return lessons
        com_pontos = []
        for l in lessons:
            sol = l.get('solucao', '') or l.get('erro', '')
            if not sol: continue
            sig_lesson = MCRSignature.extrair(sol)
            fp_lesson = sig_lesson.get('fingerprint', [])
            if fp_lesson and len(fp_lesson) == len(fp_pergunta):
                dot = sum(a*b for a,b in zip(fp_lesson, fp_pergunta))
                na = sum(a*a for a in fp_lesson) ** 0.5
                nb = sum(b*b for b in fp_pergunta) ** 0.5
                compat = dot / (na * nb) if na*nb > 0 else 0
            else:
                compat = MCR.jaccard_bytes(pergunta, sol)
            com_pontos.append((compat, l))
        com_pontos.sort(key=lambda x: -x[0])
        if com_pontos and com_pontos[0][0] < 0.1:
            return []
        return [l for _, l in com_pontos]
    
    def perguntar(self, pergunta: str, max_tokens: int = 80) -> dict:
        from .memory import MCRWebLearn
        from .meta import MCRMetaGap
        from .feedback import MCRFeedback
        from .memory import CONECTORES
        mk_fluxo = MCR('fluxo_pergunta')
        termos = [p.lower().strip('.,!?') for p in pergunta.split()
                  if len(p) > _MCR_THRESHOLD_PALAVRA.obter('termo_min', 3) and p.lower() not in CONECTORES]
        lessons = []
        topicos_alimentados = []
        conexoes = []
        estado = {
            'fase': 'inicio',
            'n_topicos': 0,
            'n_conexoes': 0,
            'n_lessons': 0,
            'n_expansoes': 0,
            'loop_count': 0,
            'ultima_nota': 0,
        }
        for ciclo in range(8):
            estado_chave = f"F:{estado['fase']}_T:{estado['n_topicos']}_C:{estado['n_conexoes']}"
            acao_pred = mk_fluxo.predizer(estado_chave)
            if acao_pred[0] is not None and acao_pred[1] > 0.3:
                acao = str(acao_pred[0])
            else:
                acao = {
                    'inicio': 'buscar', 'buscou': 'conectar' if len(topicos_alimentados) >= 2 else 'estudar',
                    'estudou': 'buscar', 'expandiu': 'conectar',
                    'conectou': 'gerar', 'avaliou': 'gerar',
                }.get(estado['fase'], 'finalizar')
            if acao == 'buscar' or estado['fase'] == 'inicio':
                for termo in termos:
                    ls = self.kg.buscar(termo, max_r=3, pergunta=pergunta) if self.kg else []
                    lessons.extend(ls)
                lessons = self._ranquear_por_assinatura(lessons, pergunta)
                estado['n_lessons'] = len(lessons)
                estado['fase'] = 'buscou'
                mk_filtro = MCR("filtro_kg")
                for i, l in enumerate(lessons):
                    sol = l.get('solucao', '') or l.get('erro', '')
                    if not self._filtrar_lesson(sol, mk_filtro): continue
                    sol = self._limpar_texto(sol)
                    if sol and len(sol) > _MCR_THRESHOLD_TAMANHO.obter('min_alimento', 30):
                        _registrar_consumo_global(sol)
                        self.conector.alimentar(sol, f"kg_{i}_{l.get('ctx', '?')}")
                        topicos_alimentados.append(f"kg_{i}")
                estado['n_topicos'] = len(topicos_alimentados)
            elif acao == 'estudar' and not lessons:
                try:
                    meta = MCRMetaGap(kg=self.kg)
                    gaps = meta.diagnosticar_gaps(min_por_prefixo=2)
                    if gaps:
                        web = MCRWebLearn()
                        if web.estudar_gaps(2) > 0:
                            for termo in termos:
                                ls = self.kg.buscar(termo, max_r=5, pergunta=pergunta) if self.kg else []
                                lessons.extend(ls)
                            lessons = self._ranquear_por_assinatura(lessons, pergunta)
                except Exception:
                    pass
                estado['fase'] = 'estudou'
            elif acao == 'expandir' and not topicos_alimentados:
                exp = self.expansao.expandir(termos[0] if termos else pergunta, max_recursos=5)
                estado['n_expansoes'] = exp.get('expansoes', 0)
                if estado['n_expansoes'] > 0:
                    for termo in termos:
                        ls = self.kg.buscar(termo, max_r=5, pergunta=pergunta) if self.kg else []
                        for l in ls:
                            sol = l.get('solucao', '') or l.get('erro', '')
                            if self._filtrar_lesson(sol) and sol:
                                sol = self._limpar_texto(sol)
                                self.conector.alimentar(sol, f"kg_exp_{len(topicos_alimentados)}")
                                topicos_alimentados.append(f"kg_exp_{len(topicos_alimentados)}")
                if not topicos_alimentados:
                    self.conector.alimentar(self._limpar_texto(pergunta), "pergunta")
                    topicos_alimentados.append("pergunta")
                estado['n_topicos'] = len(topicos_alimentados)
                estado['fase'] = 'expandiu'
            elif acao == 'conectar' and len(topicos_alimentados) >= 2:
                for i in range(len(topicos_alimentados)):
                    for j in range(i+1, len(topicos_alimentados)):
                        cx = self.conector.conectar(topicos_alimentados[i], topicos_alimentados[j])
                        if cx: conexoes.append(cx)
                estado['n_conexoes'] = len(conexoes)
                estado['fase'] = 'conectou'
            elif acao == 'gerar' and topicos_alimentados:
                resultado_cadeia = self._gerar_resposta(pergunta, topicos_alimentados, max_tokens)
                nota_final, texto, resultado_cadeia = self._avaliar_resposta(
                    pergunta, resultado_cadeia, max_tokens)
                estado['ultima_nota'] = nota_final
                estado['fase'] = 'avaliou'
                if nota_final >= _MCR_THRESHOLD_NOTA.obter('min_entrega', 6.0) or ciclo >= 6:
                    return self._montar_resultado(pergunta, texto, nota_final, resultado_cadeia,
                                                  topicos_alimentados, conexoes)
            elif acao == 'finalizar' or ciclo >= 7:
                if topicos_alimentados:
                    resultado_cadeia = self._gerar_resposta(pergunta, topicos_alimentados, max_tokens)
                    nota_final, texto, resultado_cadeia = self._avaliar_resposta(
                        pergunta, resultado_cadeia, max_tokens)
                    return self._montar_resultado(pergunta, texto, nota_final, resultado_cadeia,
                                                  topicos_alimentados, conexoes)
                return {'erro': 'sem dados', 'pergunta': pergunta, 'nota': 0}
            estado['loop_count'] = ciclo
            mk_fluxo.aprender(estado_chave, acao)
        if topicos_alimentados:
            resultado_cadeia = self._gerar_resposta(pergunta, topicos_alimentados, max_tokens)
            return self._montar_resultado(pergunta, resultado_cadeia['texto'],
                                          resultado_cadeia['nota'], resultado_cadeia,
                                          topicos_alimentados, conexoes)
        return {'erro': 'timeout', 'pergunta': pergunta, 'nota': 0}
    
    def _gerar_resposta(self, pergunta, topicos_alimentados, max_tokens):
        if topicos_alimentados:
            primeiro_texto = self.conector.topicos.get(topicos_alimentados[0], {}).get('texto', pergunta)
        else:
            primeiro_texto = pergunta
        palavras_primeiro = primeiro_texto.split()
        semente = palavras_primeiro[0] if palavras_primeiro else pergunta.split()[0]
        if semente not in self.conector.mcr_palavra.freq and len(palavras_primeiro) > 1:
            semente = palavras_primeiro[1]
        return self.cadeia.gerar(semente, n_tokens=max_tokens, top_k=3)
    
    def _avaliar_resposta(self, pergunta, resultado_cadeia, max_tokens):
        from .feedback import MCRFeedback
        texto = resultado_cadeia['texto']
        if texto and texto[0].islower(): texto = texto[0].upper() + texto[1:]
        if texto and not any(texto.rstrip().endswith(p) for p in '.!?'): texto += '.'
        import re as _re
        texto = _re.sub(r'([.!?])\1+', r'\1', texto)
        if len(texto) > 200:
            idx_ponto = texto.find('.', 80)
            if idx_ponto > 0: texto = texto[:idx_ponto+1]
        av_sem = self.semantico.avaliar(texto, 'lore')
        nota_sem = av_sem.get('nota', 5)
        nota_cadeia = resultado_cadeia.get('nota', 5)
        loops = resultado_cadeia.get('loops_detectados', 0)
        nota_final = self.peso_nota.calcular(
            byte_s=nota_cadeia, palavra_s=nota_sem,
            token_s=8 if loops < 3 else 3
        )
        thr_min = _MCR_THRESHOLD_NOTA.obter('min_entrega', 6.0)
        if nota_final < thr_min and not pergunta.startswith('[MCR Feedback]'):
            fb = MCRFeedback()
            res_fb = fb.processar_com_feedback(pergunta, max_tentativas=2)
            if res_fb.get('nota', 0) > nota_final:
                nota_final = res_fb['nota']
                texto = res_fb.get('resposta', texto)
        return nota_final, texto, resultado_cadeia
    
    def _montar_resultado(self, pergunta, texto, nota_final, resultado_cadeia,
                          topicos_alimentados, conexoes):
        av_sem = self.semantico.avaliar(texto, 'lore')
        resultado = {
            'pergunta': pergunta,
            'resposta': texto,
            'nota': round(nota_final, 1),
            'n_tokens': resultado_cadeia['n_tokens'],
            'topicos_usados': topicos_alimentados,
            'n_conexoes': len(conexoes),
            'loops_detectados': resultado_cadeia['loops_detectados'],
            'repeticoes_evitadas': resultado_cadeia['repeticoes_evitadas'],
            'avaliacao_semantica': av_sem,
        }
        self.log.append(resultado)
        return resultado


class MCRMestre:
    """MCR que GERENCIA outros MCRs (workers)."""
    
    def __init__(self, bridge=None):
        from .evolution import MCRSpawner, MCRTarefa
        from .memory import _buscar_kg_task
        self.mk = MCR("mestre")
        self.bridge = bridge or MCRBridge()
        self.spawner = MCRSpawner()
        self.conector = MCRConector()
        self.cadeia = MCRCadeia(self.conector)
        self.diagnostico = MCRDiagnostico()
    
    def processar(self, pergunta: str) -> dict:
        from .evolution import MCRTarefa
        import time
        t0 = time.time()
        if not self.bridge._descobriu:
            self.bridge.descobrir()
        tipo = 'explicacao'
        if any(w in pergunta.lower() for w in ['crie', 'gere', 'criar']):
            tipo = 'criacao'
        elif any(w in pergunta.lower() for w in ['busque', 'encontre']):
            tipo = 'busca'
        self.mk.aprender(f"PERGUNTA:{tipo}", "PROCESSANDO")
        n_workers = 3
        estado_workers = f"TIPO:{tipo}"
        if estado_workers in self.mk.transicoes:
            prox, conf = self.mk.predizer(estado_workers)
            if prox:
                try: n_workers = int(prox.replace('W:', ''))
                except: pass
        tarefas = []
        termo_kg = pergunta.split()[-1] if pergunta.split() else 'MCR'
        tarefas.append(MCRTarefa("buscar_kg", _buscar_kg_task, {
            'termo': termo_kg, 'pergunta': pergunta, 'conector': self.conector
        }))
        workers = self.spawner.spawnar(tarefas)
        textos = []
        for w in workers:
            if w.resultado and not w.erro:
                if isinstance(w.resultado, str):
                    textos.append(w.resultado)
                elif isinstance(w.resultado, list):
                    textos.extend(w.resultado)
                self.mk.aprender(f"WORKER:{w.nome}", f"T:{int(w.tempo)}")
        if textos:
            for t in textos:
                if isinstance(t, str) and len(t) > 20:
                    self.conector.alimentar(t, "consolidado")
        semente = pergunta.split()[0] if pergunta.split() else 'O'
        res_cadeia = self.cadeia.gerar(semente, n_tokens=40)
        resposta = res_cadeia.get('texto', '')
        nota_cadeia = res_cadeia.get('nota', 0)
        nota = nota_cadeia
        diag = self.diagnostico.diagnosticar({
            'byte': nota_cadeia / 10,
            'palavra': nota_cadeia / 10,
            'token': nota_cadeia > 5,
        })
        self.mk.aprender(f"RESULTADO:{tipo}", f"NOTA:{int(nota)}")
        return {
            'pergunta': pergunta,
            'resposta': resposta,
            'nota': round(nota, 1),
            'n_workers': len(workers),
            'workers': [{'nome': w.nome, 'fn': str(w.fn.__name__ if hasattr(w.fn, '__name__') else w.fn), 'tempo': round(w.tempo, 3)} for w in workers],
            'diagnostico': diag,
            'tempo': round(time.time() - t0, 2),
        }


class MCRMestreV2:
    """Mestre que decide TUDO por Markov, sem if/else."""
    
    def __init__(self, bridge=None):
        from .evolution import MCRSpawner, MCRFuel, MCRExpansao
        from .meta import MCRMetaGap
        self.decisor = MCRDecisor("mestre_v2")
        self.peso_nota = MCRPesoNota()
        self.threshold_loop = MCRThreshold("threshold_loop")
        self.bridge = bridge or MCRBridge()
        self.diagnostico = MCRDiagnostico("mestre_diag")
        self.spawner = MCRSpawner()
        self.conector = MCRConector()
        self.cadeia = MCRCadeia(self.conector)
        self.n_execucoes = 0
    
    def processar(self, pergunta: str) -> dict:
        from .evolution import MCRFuel, MCRExpansao, MCRTarefa
        from .meta import MCRMetaGap
        import time
        t0 = time.time()
        self.n_execucoes += 1
        if not self.bridge._descobriu:
            self.bridge.descobrir()
        fluxo = self.decisor.decidir(pergunta)
        self.decisor.aprender(pergunta, fluxo, True)
        max_ciclos = max(1, min(10, len(pergunta.split()) // 2))
        try:
            dc = MCRDecisor("max_ciclos")
            mc_str = dc.decidir(f"CICLOS:{fluxo}")
            if mc_str:
                max_ciclos = max(1, min(10, int(str(mc_str).replace('C:', ''))))
        except:
            pass
        termo = pergunta.split()[-1] if pergunta.split() else 'MCR'
        semente = pergunta.split()[0] if pergunta.split() else 'O'
        if len(self.peso_nota.historico) < 5:
            self.peso_nota.aprender({'byte': 0.8, 'palavra': 0.2, 'token': 0.3}, 2.0)
            self.peso_nota.aprender({'byte': 0.7, 'palavra': 0.3, 'token': 0.4}, 3.0)
            self.peso_nota.aprender({'byte': 0.4, 'palavra': 0.7, 'token': 0.8}, 8.0)
            self.peso_nota.aprender({'byte': 0.3, 'palavra': 0.8, 'token': 0.7}, 7.5)
            self.peso_nota.aprender({'byte': 0.5, 'palavra': 0.5, 'token': 0.5}, 5.0)
        tarefas = []
        if 'kg' in fluxo:
            tarefas.append(MCRTarefa("kg", "buscar_kg", {'termo': termo, 'pergunta': pergunta}))
        tarefas.append(("gerador", "gerar", {'semente': semente, 'n_tokens': 40}))
        workers = self.spawner.spawnar(tarefas) if tarefas else []
        textos = []
        for w in workers:
            if w.resultado:
                if isinstance(w.resultado, str): textos.append(w.resultado)
                elif isinstance(w.resultado, list): textos.extend(w.resultado)
        if textos:
            for t in textos:
                if isinstance(t, str) and len(t) > 20:
                    self.conector.alimentar(t, "consolidado")
        expansoes_feitas = []
        agora = time.time()
        ultima_exp = getattr(self, '_ultima_expansao', 0)
        if agora - ultima_exp > 30:
            fuel = MCRFuel(bridge=self.bridge)
            n_fuel = fuel.abastecer_se_precisar(min_uteis=200)
            if n_fuel:
                expansoes_feitas.append(f"fuel:{n_fuel}")
            meta = MCRMetaGap(kg=None, bridge=self.bridge)
            gaps = meta.diagnosticar_gaps(min_por_prefixo=3)
            if gaps:
                n = meta.buscar_para_gap(gaps[0])
                if n > 0:
                    expansoes_feitas.append(f"gap:{n}")
            expansao = MCRExpansao(None, self.bridge)
            res_exp = expansao.expandir(termo, max_recursos=3)
            if res_exp.get('expansoes', 0) > 0:
                expansoes_feitas.append(f"exp:{res_exp['expansoes']}")
                if self.conector.topicos:
                    for nome_topico in list(self.conector.topicos.keys()):
                        cx = self.conector.conectar(termo, nome_topico)
                        if cx:
                            self.conector.alimentar(cx.get('sequencia',''), f"emrg_{termo}")
            if 'explorar' in self.bridge.comandos:
                try: self.bridge.usar_comando('explorar', {'termo': termo})
                except: pass
            self._ultima_expansao = agora
        res_cadeia = self.cadeia.gerar(semente, n_tokens=40)
        resposta = res_cadeia.get('texto', '')
        nota_cadeia = res_cadeia.get('nota', 0)
        loops = res_cadeia.get('loops_detectados', 0)
        nota = self.peso_nota.calcular(
            byte_s=nota_cadeia,
            palavra_s=min(10, len(resposta)/30),
            token_s=8 if loops < 3 else 3
        )
        estado_diag = {'byte': nota_cadeia / 10, 'palavra': nota / 10, 'token': nota > 5}
        diag = self.diagnostico.diagnosticar(estado_diag)
        self.diagnostico.alimentar(estado_diag, 'loop' if loops > 3 else 'ok')
        self.threshold_loop.observar(nota / 10)
        self.peso_nota.aprender(
            {'byte': nota/10, 'palavra': nota/10, 'token': nota > 5 and 0.8 or 0.3},
            nota
        )
        return {
            'pergunta': pergunta,
            'resposta': resposta,
            'nota': round(nota, 1),
            'fluxo': fluxo,
            'ciclos': 1,
            'expansoes': expansoes_feitas,
            'diagnostico': diag,
            'n_execucoes': self.n_execucoes,
            'tempo': round(time.time() - t0, 2),
        }


class MCRGeracao:
    """Gera resposta e VALIDA se a assinatura condiz com a pergunta."""
    
    def __init__(self):
        self.decisor = MCRDecisor("geracao")
        self.threshold = MCRThreshold("geracao_comp")
        for v in [0.2, 0.25, 0.3, 0.35, 0.28]:
            self.threshold.observar(v)
        self.mk = MCR("geracao")
        self.mk_pred = MCR("geracao_pred")
    
    def gerar(self, pergunta: str, max_tentativas: int = 3) -> dict:
        sig_pergunta = MCRSignature.extrair(pergunta, rapido=True)
        fp_pergunta = sig_pergunta.get('fingerprint', [])
        fp_chave = '_'.join(str(int(v*10)) for v in fp_pergunta) if fp_pergunta else ''
        fp_resp_esperado = None
        if fp_chave:
            pred = self.mk_pred.predizer(fp_chave)
            if pred[0] is not None and pred[1] > 0.3:
                fp_resp_esperado = str(pred[0])
        melhor_resposta = ''
        melhor_comp = 0
        melhor_estrategia = ''
        tentativas = 0
        for tentativa in range(max_tentativas):
            tentativas += 1
            if tentativa == 1:
                estrategia = 'cadeia_direto'
            else:
                estado = f"COMP:{melhor_comp:.2f}|TENT:{tentativa}"
                estrategia = self.decisor.decidir(estado)
                if not estrategia or estrategia == 'kg_primeiro':
                    estrategia = 'cadeia_direto'
            texto = self._executar_estrategia(pergunta, estrategia)
            sig_resposta = MCRSignature.extrair(texto, rapido=True)
            compatibilidade = MCRSignature.comparar(sig_pergunta, sig_resposta)
            if fp_resp_esperado and texto:
                fp_resp = '_'.join(str(int(v*10)) for v in
                                   sig_resposta.get('fingerprint', []))
                if fp_resp == fp_resp_esperado:
                    compatibilidade = max(compatibilidade, 0.8)
            nota = self._autoavaliar(texto, pergunta, compatibilidade)
            if compatibilidade > melhor_comp:
                melhor_comp = compatibilidade
                melhor_resposta = texto
                melhor_estrategia = estrategia
            limiar = self.threshold.calcular(1.0)
            if compatibilidade >= limiar and nota >= 4:
                if fp_chave and texto and len(texto) > 30:
                    fp_r = '_'.join(str(int(v*10)) for v in
                                    sig_resposta.get('fingerprint', []))
                    if fp_r:
                        self.mk_pred.aprender(fp_chave, fp_r)
                self.mk.aprender(f"GERADO:{pergunta}",
                                f"comp={compatibilidade:.2f} tent={tentativa}")
                return {
                    'texto': texto,
                    'compatibilidade': round(compatibilidade, 3),
                    'nota': round(nota, 1),
                    'tentativas': tentativas,
                    'estrategia': estrategia,
                    'assinatura_pergunta': sig_pergunta,
                    'assinatura_resposta': sig_resposta,
                }
        self.mk.aprender(f"FALHO:{pergunta}", f"melhor_comp={melhor_comp:.2f}")
        return {
            'texto': melhor_resposta,
            'compatibilidade': round(melhor_comp, 3),
            'nota': round(self._autoavaliar(melhor_resposta, pergunta, melhor_comp), 1),
            'tentativas': tentativas,
            'estrategia': melhor_estrategia,
            'assinatura_pergunta': sig_pergunta,
            'assinatura_resposta': MCRSignature.extrair(melhor_resposta),
        }
    
    def _executar_estrategia(self, pergunta: str, estrategia: str) -> str:
        palavras = pergunta.split()
        semente = palavras[0] if palavras else 'O'
        if estrategia == 'cadeia_direto':
            c = MCRConector()
            c.alimentar(pergunta, "pergunta")
            cadeia = MCRCadeia(c)
            res = cadeia.gerar(semente, n_tokens=60)
            return res.get('texto', semente)
        elif estrategia == 'kg_primeiro':
            try:
                from modulos.kg import KnowledgeGraph
                kg = KnowledgeGraph()
                lessons = kg.buscar(semente, max_r=3)
                if lessons:
                    c = MCRConector()
                    for l in lessons:
                        sol = l.get('solucao', '') or l.get('erro', '')
                        if sol:
                            c.alimentar(sol, "kg")
                    cadeia = MCRCadeia(c)
                    res = cadeia.gerar(semente, n_tokens=60)
                    return res.get('texto', semente)
            except: pass
            return self._executar_estrategia(pergunta, 'cadeia_direto')
        elif estrategia == 'semente_alternativa':
            if len(palavras) > 1:
                semente = palavras[-1]
            c = MCRConector()
            c.alimentar(pergunta, "pergunta")
            cadeia = MCRCadeia(c)
            res = cadeia.gerar(semente, n_tokens=60)
            return res.get('texto', semente)
        return pergunta
    
    def _autoavaliar(self, texto, pergunta, compatibilidade):
        if not texto or len(texto) < 20:
            return 0.0
        nota = 0.0
        nota += compatibilidade * 4
        nota += min(2.0, len(texto) / 200)
        nota += min(2.0, len(set(texto.split())) / 20)
        nota += 2.0 if not any(p in texto for p in ['Projeto MCR', 'Guia de']) else 1.0
        return round(min(10, max(0, nota)), 1)
