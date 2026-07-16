#!/usr/bin/env python3
"""feedback.py — Feedback loops, author signatures, and sessions.

Aprendizado por reforço (MCRFeedback),
banco de assinaturas de autores, sessões e aprendizado web.
"""
import os, json, time as _time

from .engine import MCR
from .signature import MCRSignature


class MCRFilosofia:
    """Filosofia MCR — valores, princípios e autoavaliação."""
    def __init__(self):
        self.principios = ["1 equação, 1 entropia, 1 markov, N domínios"]

class MCRFeedback:
    """Feedback loop: MCR solicita mais dados quando resposta e insuficiente."""
    
    def __init__(self, mestre=None):
        from .system import MCRMestreV2
        self.mestre = mestre or MCRMestreV2()
        self.historico_tentativas = []
        self.mk = MCR("feedback")
    
    def processar_com_feedback(self, pergunta: str, max_tentativas: int = 3) -> dict:
        from .memory import _get_kg
        try:
            kk = _get_kg()
            lk = kk._get_licoes() if kk else []
            if len(lk) > 200:
                max_tentativas = 1
        except Exception:
            pass
        melhor_resposta = None
        melhor_nota = 0
        contexto_acumulado = pergunta
        for tentativa in range(max_tentativas):
            res = self.mestre.processar(contexto_acumulado)
            nota = res.get('nota', 0)
            self.historico_tentativas.append({
                'tentativa': tentativa + 1,
                'nota': nota,
                'resposta': res.get('resposta', ''),
            })
            self.mk.aprender(f"TENTATIVA:{tentativa}", f"NOTA:{int(nota)}")
            if nota > melhor_nota:
                melhor_nota = nota
                melhor_resposta = res
            if nota >= 7:
                break
            if tentativa < max_tentativas - 1:
                diag = res.get('diagnostico', '')
                if 'loop' in diag:
                    feedback = f"[MCR precisa de mais contexto] {pergunta} pode explicar com mais detalhes?"
                elif nota < 4:
                    feedback = f"[MCR nao encontrou dados] {pergunta} tem alguma fonte ou exemplo especifico?"
                else:
                    feedback = f"[MCR quer confirmar] {pergunta} e isso mesmo que voce quer saber?"
                contexto_acumulado = f"{pergunta} | Contexto extra: {feedback}"
        resultado = melhor_resposta or res
        resultado['feedback'] = {
            'tentativas': len(self.historico_tentativas),
            'historico': self.historico_tentativas,
            'precisou_feedback': len(self.historico_tentativas) > 1,
        }
        return resultado


class MCRSession:
    """Memoria de sessao: salva/carrega estado, historico, checkpoint."""
    
    def __init__(self):
        try:
            self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            self._conv_path = os.path.join(self._base, 'sandbox', '.mcr_conversa.jsonl')
            self._estado_path = os.path.join(self._base, 'sandbox', '.mcr_estado.json')
            self._episodios_path = os.path.join(self._base, 'sandbox', '.mcr_episodios.json')
            self._historico = []
            self._ultima_pergunta = ''
            self._ultima_resposta = ''
            self._ultimo_autor = ''
            self.mk = MCR("session")
        except Exception as e:
            import traceback as _tb
            _tb.print_exc()
            raise
    
    def registrar(self, pergunta, resposta, autor=''):
        self._ultima_pergunta = pergunta
        self._ultima_resposta = resposta
        self._ultimo_autor = autor
        self._historico.append({'pergunta': pergunta, 'resposta': resposta, 'autor': autor})
        try:
            os.makedirs(os.path.dirname(self._conv_path), exist_ok=True)
            with open(self._conv_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'msg': f'{autor}: {pergunta} -> {resposta}',
                                   'timestamp': _time.time()}) + '\n')
        except Exception: pass
        self.mk.aprender(f"CONV:{pergunta}", f"autor:{autor or 'anonimo'}")
    
    def salvar_estado(self):
        estado = {
            'timestamp': _time.time(),
            'ultima_pergunta': self._ultima_pergunta,
            'ultima_resposta': self._ultima_resposta,
            'ultimo_autor': self._ultimo_autor,
            'n_historico': len(self._historico),
        }
        try:
            os.makedirs(os.path.dirname(self._estado_path), exist_ok=True)
            with open(self._estado_path, 'w', encoding='utf-8') as f:
                json.dump(estado, f, ensure_ascii=False, indent=2)
            return True
        except Exception: return False
    
    def carregar_estado(self):
        if not os.path.exists(self._estado_path): return None
        try:
            with open(self._estado_path, 'r', encoding='utf-8') as f:
                estado = json.load(f)
            self._ultima_pergunta = estado.get('ultima_pergunta', '')
            self._ultima_resposta = estado.get('ultima_resposta', '')
            self._ultimo_autor = estado.get('ultimo_autor', '')
            return estado
        except Exception: return None
    
    def ultima_pergunta(self): return self._ultima_pergunta
    def ultima_resposta(self): return self._ultima_resposta
    def ultimo_autor(self): return self._ultimo_autor
    
    def auto_retomar(self):
        estado = self.carregar_estado()
        if estado:
            self.mk.aprender("RETOMADA", f"pergunta:{estado.get('ultima_pergunta','')}")
            return estado
        return None


class MCRAssinatura:
    """Banco de assinaturas de autores conhecidos."""
    
    def __init__(self):
        self._banco = {}
        self.mk = MCR("assinatura")
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self._banco_path = os.path.join(self._base, 'sandbox', '.mcr_assinaturas.json')
        self._carregar()
    
    def _carregar(self):
        if os.path.exists(self._banco_path):
            try:
                with open(self._banco_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                self._banco = dados
                self.mk.aprender("BANCO", f"autores:{len(self._banco)}")
                self._migrar_fingerprints()
            except Exception: pass
    
    def _migrar_fingerprints(self):
        removidos = 0
        for autor in list(self._banco.keys()):
            assinaturas = self._banco[autor]
            novas = []
            for ass in assinaturas:
                fp = ass.get('fingerprint', [])
                if len(fp) >= 8:
                    novas.append(ass)
                else:
                    removidos += 1
            self._banco[autor] = novas
            if not novas:
                del self._banco[autor]
        if removidos:
            self.mk.aprender("MIGRACAO", f"removidos:{removidos}")
            self._salvar()
    
    def _salvar(self):
        try:
            os.makedirs(os.path.dirname(self._banco_path), exist_ok=True)
            with open(self._banco_path, 'w', encoding='utf-8') as f:
                json.dump(self._banco, f, ensure_ascii=False, indent=2)
        except Exception: pass
    
    def aprender(self, texto, autor, rapido=False):
        if not texto or not autor: return
        sig = MCRSignature.extrair(texto, rapido=rapido)
        sig_full = MCRSignature.extrair(texto) if rapido else sig
        sig_palavras = MCRSignature.extrair_palavras(texto)
        if autor not in self._banco:
            self._banco[autor] = []
        entry = {
            'entropia': sig.get('entropia', 0),
            'timestamp': _time.time(),
            'texto': texto,
            'fingerprint': sig.get('fingerprint', []),
            'sequencia': sig_full.get('sequencia', []),
            'vocab': list(sig_palavras.get('vocab', set())),
            'seq_palavras': sig_palavras.get('sequencia', []),
        }
        self._banco[autor].append(entry)
    
    def identificar(self, texto):
        if not texto: return ('desconhecido', 0.0, {})
        sig_palavras = MCRSignature.extrair_palavras(texto)
        voc_alvo = sig_palavras.get('vocab', set())
        if not isinstance(voc_alvo, set):
            voc_alvo = set(voc_alvo)
        sig_char = MCRSignature.extrair(texto, rapido=True)
        fp_char = sig_char.get('fingerprint', [])
        kheltz_ass = self._banco.get('Kheltz', [])
        kheltz_score = 0.0
        if kheltz_ass:
            scores = []
            for ass in kheltz_ass[-5:]:
                texto_ass = ass.get('texto', '')
                comp_byte = 0.0
                if texto_ass and len(texto_ass) > 20 and len(texto) > 20:
                    jac = MCR("tmp").jaccard_bytes(texto, texto_ass)
                    comp_byte = jac
                voc_ass = ass.get('vocab', [])
                comp_word = 0.0
                if voc_ass:
                    inter = voc_alvo & set(voc_ass)
                    uniao = voc_alvo | set(voc_ass)
                    comp_word = len(inter) / max(len(uniao), 1)
                fp_ass = ass.get('fingerprint', [])
                comp_char = 0.0
                if fp_ass and len(fp_ass) == 8 == len(fp_char):
                    dot = sum(a*b for a,b in zip(fp_ass, fp_char))
                    na = sum(a*a for a in fp_ass) ** 0.5
                    nb = sum(b*b for b in fp_char) ** 0.5
                    comp_char = dot / (na * nb) if na*nb > 0 else 0
                score = comp_byte * 0.5 + comp_word * 0.3 + comp_char * 0.2
                scores.append(score)
            if scores:
                kheltz_score = sum(scores) / len(scores)
        if kheltz_score >= 0.55:
            return ('Kheltz', round(kheltz_score, 3), {
                'status': 'confirmado', 'score': round(kheltz_score, 3),
            })
        elif kheltz_score >= 0.20:
            return ('Kheltz?', round(kheltz_score, 3), {
                'status': 'duvida', 'score': round(kheltz_score, 3),
            })
        return ('desconhecido', round(kheltz_score, 3), {'score': round(kheltz_score, 3)})
    
    def auto_popular(self):
        conv_path = os.path.join(self._base, 'sandbox', '.mcr_conversa.jsonl')
        if not os.path.exists(conv_path): return 0
        n_autores = 0
        n_anteriores = len(self._banco)
        autor_atual = 'desconhecido'
        ultima_sig = None
        roles_vistos = set()
        processadas = 0
        ultimos_20_roles = []
        baixa_consec = 0
        mk_popular = MCR('auto_popular')
        mk_popular.aprender("baixa_x3", "parar")
        mk_popular.aprender("baixa_x3_ja_aprendeu", "parar")
        mk_popular.aprender("alta_variada", "continuar")
        mk_popular.aprender("media_normal", "continuar")
        try:
            with open(conv_path, 'r', encoding='utf-8') as f:
                for linha in f:
                    try:
                        entry = json.loads(linha.strip())
                        msg = entry.get('msg', '')
                        if not msg or len(msg) < 20: continue
                        role = entry.get('role', entry.get('origem', '')).strip().lower()
                        if processadas > 10:
                            ultimos_20_roles.append(role or '?')
                            if len(ultimos_20_roles) > 20:
                                ultimos_20_roles.pop(0)
                            roles_unicos = len(set(ultimos_20_roles))
                            diver = roles_unicos / max(len(ultimos_20_roles), 1)
                            diver_cat = 'alta' if diver > 0.7 else 'media' if diver > 0.3 else 'baixa'
                            if diver_cat == 'baixa':
                                baixa_consec += 1
                            else:
                                baixa_consec = 0
                            if baixa_consec >= 3 and len(self._banco) > n_anteriores + 2:
                                estado = f"baixa_x3"
                                pred = mk_popular.predizer(estado)
                                if pred[0] is not None and 'parar' in str(pred[0]):
                                    break
                        processadas += 1
                        if role and role in ('cloud', 'user', 'system', 'assistant'):
                            autor_atual = role
                            roles_vistos.add(role)
                        else:
                            sig_atual = MCRSignature.extrair(msg, rapido=True)
                            if ultima_sig is not None:
                                comp = MCRSignature.comparar(ultima_sig, sig_atual)
                                if comp < 0.5:
                                    autor_atual = f'autor_{n_autores}'
                                    n_autores += 1
                            ultima_sig = sig_atual
                        self.aprender(msg, autor_atual, rapido=True)
                    except Exception: pass
        except Exception: pass
        if roles_vistos:
            nomes = ', '.join(sorted(roles_vistos))
            self.mk.aprender("AUTO_POP", f"roles:{nomes} total:{len(self._banco)-n_anteriores}")
        else:
            self.mk.aprender("AUTO_POP", f"autores:{n_autores} total:{len(self._banco)-n_anteriores}")
        self._salvar()
        return len(self._banco) - n_anteriores
    
    def confirmar(self, texto, autor='Kheltz'):
        self.aprender(texto, autor)
        self._salvar()
        self.mk.aprender("CONFIRMOU", f"autor:{autor}")
        if autor == 'Kheltz':
            n_conf = self._banco.get('Kheltz', [])
            return {
                'status': 'confirmado',
                'autor': autor,
                'n_fingerprints': len(n_conf) if n_conf else 0,
            }
        return {'status': 'aprendido', 'autor': autor}
    
    def autores_conhecidos(self):
        return list(self._banco.keys())
    
    def estatisticas(self):
        return {'autores': len(self._banco),
                'total_assinaturas': sum(len(v) for v in self._banco.values())}


class MCRWebLearn:
    """Estudo web AUTONOMO."""
    
    def __init__(self):
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        self.mk = MCR("weblearn")
        self._cache = {}
        self._kg = None
        try:
            from modulos.kg import KnowledgeGraph
            self._kg = KnowledgeGraph()
        except Exception:
            pass
        try:
            import urllib.request
            self._urlopen = urllib.request.urlopen
        except Exception:
            self._urlopen = None
    
    def estudar_gaps(self, n_gaps=3):
        if not self._kg: return 0
        from .meta import MCRMetaGap
        from .decisor import MCRDecisor
        decisor = MCRDecisor('weblearn_decision')
        licoes = self._kg._get_licoes()
        uteis = sum(1 for l in licoes if l.get('solucao', '') and len(l.get('solucao', '')) > 50)
        total = len(licoes)
        if uteis > 400:
            decisao = decisor.decidir(f"kg_rico_{uteis}")
            if 'pular' in str(decisao).lower():
                return 0
        gaps = MCRMetaGap().diagnosticar_gaps(min_por_prefixo=5)
        if not gaps: return 0
        total_estudados = 0
        for gap in gaps:
            termo = gap['prefixo']
            if termo in self._cache:
                self.mk.aprender(f"CACHE:{termo}", "hit")
                continue
            if self._kg:
                ja_tem = self._kg.buscar(termo, max_r=3)
                if ja_tem and len(ja_tem) > 0:
                    self._cache[termo] = ja_tem[0].get('solucao', f'[KG] {termo}')
                    continue
            resultado = self._buscar_web(termo)
            if resultado and not resultado.startswith('[WebLearn]'):
                self._kg.aprender_conceito(
                    f"weblearn:{termo}",
                    f"[WebLearn] {resultado}",
                    ctx="weblearn"
                )
                total_estudados += 1
                self.mk.aprender(f"WWW:{termo}", "OK")
        return total_estudados
    
    def _buscar_web(self, termo):
        if not self._urlopen: return None
        if termo in self._cache:
            self.mk.aprender(f"CACHE:{termo}", "hit")
            return self._cache[termo]
        try:
            url = f"https://pt.wikipedia.org/w/api.php?action=query&list=search&srsearch={termo}&format=json&srlimit=1"
            resp = self._urlopen(url, timeout=10).read()
            dados = json.loads(resp.decode('utf-8'))
            resultados = dados.get('query', {}).get('search', [])
            resultado = f"[Wikipedia] Resultado sobre {termo} encontrado."
            if resultados:
                titulo = resultados[0].get('title', '')
                if titulo:
                    url2 = f"https://pt.wikipedia.org/w/api.php?action=query&titles={titulo}&prop=extracts&exintro=true&format=json"
                    resp2 = self._urlopen(url2, timeout=10).read()
                    dados2 = json.loads(resp2.decode('utf-8'))
                    pages = dados2.get('query', {}).get('pages', {})
                    for page_id, page_data in pages.items():
                        extract = page_data.get('extract', '')
                        if extract:
                            import re
                            texto = re.sub(r'<[^>]+>', '', extract)
                            resultado = f"[Wikipedia: {titulo}] {texto}"
            self._cache[termo] = resultado
            self.mk.aprender(f"WEB:{termo}", "OK")
            return resultado
        except Exception as e:
            erro = f"[WebLearn] {termo}: {str(e)[:50]}"
            self._cache[termo] = erro
            return erro
    
    def ciclo_auto_estudo(self):
        if not self._kg: return {'estudados': 0, 'erro': 'KG indisponivel'}
        from .meta import MCRMetaGap
        gaps = MCRMetaGap().diagnosticar_gaps(min_por_prefixo=5)
        n_estudados = 0
        erros = 0
        max_gaps = min(5, len(gaps))
        for gap in gaps:
            termo = gap['prefixo']
            resultado = self._buscar_web(termo)
            if resultado and len(resultado) > 30:
                self._kg.aprender_conceito(
                    f"weblearn_auto:{termo}",
                    resultado,
                    ctx="webrearn"
                )
                n_estudados += 1
                self.mk.aprender(f"AUTO_WWW:{termo}", "OK")
            else:
                erros += 1
        return {'estudados': n_estudados, 'erros': erros, 'total_gaps': len(gaps)}
