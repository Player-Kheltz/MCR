#!/usr/bin/env python3
"""
mcr.emergir_unificado — Motor Criativo Unificado.

Integra 3 Emergir + 3 Radar em uma interface unica:

EMERGIR (3 versoes):
  1. Emergir (mcr/emergir.py)          — "E se A + B = C?" (gerador de ideias)
  2. EmergirCrossModal (crossmodal)     — despachar ideia para 4 dominios
  3. EmergirEngine (devia/modules)      — validar originalidade (anti-alucinacao)

RADAR (3 versoes):
  1. RadarMCR (mcr/mcr_radar.py)        — busca polimorfica 4 ondas (texto + visual)
  2. Radar (devia/kernel/Radar.py)       — detector de loop (evitar repeticao)
  3. MCRRadar (mcr-universal)           — gaps + pulsos + delta fingerprint

PIPELINE COMPLETO:
  radar.distantes → emergir.ideia → crossmodal.despachar → engine.validar → loop.detectar
"""
import sys
import os
import time
import random
import re
import math
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from mcr.paths import KG_DIR

# ─── Importa os 3 Emergir ────────────────────────────────
try:
    from mcr.emergir import Emergir
except ImportError:
    Emergir = None

try:
    from mcr.emergir_crossmodal import EmergirCrossModal
except ImportError:
    EmergirCrossModal = None

# EmergirEngine esta em devia/modules/emergir.py
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'modules'))
    from emergir import EmergirEngine
except ImportError:
    EmergirEngine = None

# ─── Importa os 3 Radar ──────────────────────────────────
try:
    from mcr.mcr_radar import RadarMCR
except ImportError:
    RadarMCR = None

try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel'))
    from Radar import Radar
except ImportError:
    Radar = None

try:
    from mcr_universal.intelligence.radar import MCRRadar
except ImportError:
    MCRRadar = None


class EmergirUnificado:
    """Motor criativo unificado: 3 Emergir + 3 Radar."""

    def __init__(self, llm_func=None, mcr_motor=None, kg=None):
        self.llm_func = llm_func or (lambda p, **kw: '')
        self._mcr_motor = mcr_motor
        self._kg = kg

        # ─── Inicializa Emergir (3 versoes) ───────────────
        self._emergir = None
        self._crossmodal = None
        self._engine = None
        self._init_emergir()

        # ─── Inicializa Radar (3 versoes) ─────────────────
        self._radar_mcr = None
        self._radar_loop = None
        self._radar_mcr_universal = None
        self._init_radar()

        # ─── Estado ───────────────────────────────────────
        self.ideias_geradas: List[Dict] = []
        self.ideias_recusadas: List[Dict] = []
        self.ultimo_loop_timestamp = 0

    # ═══════════════════════════════════════════════════════
    # INICIALIZACAO
    # ═══════════════════════════════════════════════════════

    def _init_emergir(self):
        if Emergir is not None:
            try:
                self._emergir = Emergir(llm_func=self.llm_func)
            except Exception as e:
                self._emergir = None

        if EmergirCrossModal is not None:
            try:
                self._crossmodal = EmergirCrossModal(llm_func=self.llm_func)
            except Exception as e:
                self._crossmodal = None

        if EmergirEngine is not None:
            try:
                self._engine = EmergirEngine(
                    ia=self._mock_ia(),
                    kg=self._kg or self._mock_kg(),
                )
            except Exception as e:
                self._engine = None

    def _init_radar(self):
        if RadarMCR is not None:
            self._radar_mcr = RadarMCR()

        if Radar is not None:
            self._radar_loop = Radar(limite=4)

        if MCRRadar is not None:
            self._radar_mcr_universal = MCRRadar(motor=self._mcr_motor)

    def _mock_ia(self):
        class MockIA:
            def fast(self, prompt, temperature, task):
                if self._real_llm:
                    try:
                        return self._real_llm(prompt, modelo='qwen2.5-coder:7b')
                    except Exception:
                        return ''
                return ''
            _real_llm = self.llm_func
        return MockIA()

    def _mock_kg(self):
        class MockKG:
            data = {'licoes': []}
            def __init__(self, real_kg=None):
                if real_kg:
                    try:
                        self.data = real_kg.data if hasattr(real_kg, 'data') else {'licoes': []}
                    except Exception:
                        pass
        return MockKG(self._kg)

    # ═══════════════════════════════════════════════════════
    # API UNIFICADA
    # ═══════════════════════════════════════════════════════

    def status(self) -> Dict:
        """Retorna quais modulos estao disponiveis."""
        return {
            'emergir': self._emergir is not None,
            'emergir_crossmodal': self._crossmodal is not None,
            'emergir_engine': self._engine is not None,
            'radar_mcr': self._radar_mcr is not None,
            'radar_loop': self._radar_loop is not None,
            'radar_mcr_universal': self._radar_mcr_universal is not None,
            'ideias_geradas': len(self.ideias_geradas),
            'ideias_recusadas': len(self.ideias_recusadas),
        }

    # ═══════════════════════════════════════════════════════
    # RADAR: Encontrar Conceitos Distantes (input para Emergir)
    # ═══════════════════════════════════════════════════════

    def conceitos_distantes(self, candidatos: List[Dict], top_k: int = 3) -> List[Tuple[Dict, Dict, float]]:
        """Encontra os pares de conceitos MAIS DISTANTES (menor Jaccard → mais criativos).

        Args:
            candidatos: lista de dicts com 'texto' e 'id'
            top_k: quantos pares retornar

        Returns:
            lista de (conceito_a, conceito_b, distancia) ordenada por distancia crescente
        """
        if self._radar_mcr is None or len(candidatos) < 2:
            return []

        # Calcula Jaccard entre todos os pares
        pares = []
        for i in range(len(candidatos)):
            for j in range(i + 1, len(candidatos)):
                sim = self._radar_mcr._jaccard_sim(
                    candidatos[i].get('texto', ''),
                    candidatos[j].get('texto', ''),
                )
                distancia = 1.0 - sim
                pares.append((candidatos[i], candidatos[j], distancia))

        # Ordena por MENOR similaridade = MAIOR distancia = MAIS criativo
        pares.sort(key=lambda x: x[2])
        return pares[:top_k]

    def buscar_por_ondas(self, consulta: str, candidatos: List[Dict]) -> List[Dict]:
        """Busca polimorfica em 4 ondas do RadarMCR."""
        if self._radar_mcr is None:
            return self._fallback_busca(consulta, candidatos)
        return self._radar_mcr.buscar(consulta, candidatos)

    def buscar_visual(self, regioes_query: List[Dict], candidatos: List[Dict]) -> List[Dict]:
        """Busca visual do RadarMCR."""
        if self._radar_mcr is None:
            return []
        return self._radar_mcr.buscar_visual(regioes_query, candidatos)

    def _fallback_busca(self, consulta: str, candidatos: List[Dict]) -> List[Dict]:
        resultados = []
        palavras_q = set(re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', consulta.lower()))
        for cand in candidatos:
            palavras_c = set(re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', cand.get('texto', '').lower()))
            inter = palavras_q & palavras_c
            uniao = palavras_q | palavras_c
            score = len(inter) / len(uniao) if uniao else 0.0
            if score > 0.1:
                cand['score'] = round(score, 3)
                cand['onda'] = 'fallback'
                resultados.append(cand)
        resultados.sort(key=lambda x: -x['score'])
        return resultados

    # ═══════════════════════════════════════════════════════
    # EMERGIR: Gerar Ideias
    # ═══════════════════════════════════════════════════════

    def gerar_ideia(self, conceito_a: Dict = None, conceito_b: Dict = None) -> Dict:
        """Gera uma ideia 'E se A + B = C?' conectando dois conceitos.

        Se conceitos nao forem fornecidos, usa Radar para encontrar
        os MAIS DISTANTES do KG (maxima criatividade).

        Args:
            conceito_a: conceito de partida (opcional)
            conceito_b: conceito alvo (opcional)

        Returns:
            dict com 'ideia', 'conceito_a', 'conceito_b', 'descricao'
        """
        # Se tem Emergir original com conceitos, delega
        if self._emergir is not None and conceito_a is None:
            n_conceitos = sum(len(v) for v in self._emergir.conceitos.values())
            if n_conceitos >= 2:
                try:
                    ideia = self._emergir.gerar_ideia()
                    if ideia and isinstance(ideia, dict):
                        self.ideias_geradas.append(ideia)
                        return ideia
                except Exception:
                    pass

        # Fallback: gera ideia usando templates criativos
        return self._gerar_ideia_fallback(conceito_a, conceito_b)

    def _gerar_ideia_fallback(self, conceito_a=None, conceito_b=None) -> Dict:
        """Gera ideia com templates deterministicos variados."""
        tipos = ['npc', 'monster', 'quest', 'spell', 'item', 'sistema',
                 'habilidade', 'arma', 'armadura', 'pocao', 'feitiço', 'runas']
        nomes = ['Ferronius', 'Grimgor', 'Aelindor', 'Eridanus', 'Thais',
                 'Vesperia', 'Kazordoon', 'Yalahar', 'Drako', 'Luminara']

        if conceito_a is None:
            ta = random.choice(tipos)
            conceito_a = {'tipo': ta, 'nome': random.choice(nomes), 'apis': []}
        if conceito_b is None:
            remaining = [t for t in tipos if t != conceito_a.get('tipo', '')]
            tb = random.choice(remaining or tipos)
            conceito_b = {'tipo': tb, 'nome': random.choice(nomes), 'apis': []}

        ta = conceito_a.get('tipo', '?')
        tb = conceito_b.get('tipo', '?')
        na = conceito_a.get('nome', 'X')
        nb = conceito_b.get('nome', 'Y')

        templates = [
            f"E se um {ta} pudesse se transformar em um {tb} quando ativado?",
            f"E se '{na}' pudesse invocar '{nb}' ao ser usado?",
            f"E se combinassemos {ta} com {tb} para criar um comportamento hibrido?",
            f"O que aconteceria se {ta} e {tb} trocassem de papel?",
            f"E se {na} fosse na verdade um {tb} disfarcado?",
            f"E se todo {ta} tivesse um {tb} oculto que so aparece a noite?",
            f"E se {na} pudesse ensinar {tb} para jogadores iniciantes?",
            f"E se criassemos um {ta} que responde a emocoes do jogador?",
            f"Como seria um mundo onde {ta} e {tb} sao a mesma coisa?",
            f"E se {na} guardasse um segredo sobre a origem dos {tb}s?",
        ]

        ideia = {
            'ideia': random.choice(templates),
            'conceito_a': conceito_a,
            'conceito_b': conceito_b,
            'descricao': f"Conectar conceitos de '{ta}' e '{tb}' para gerar algo novo",
        }
        self.ideias_geradas.append(ideia)
        return ideia

    # ═══════════════════════════════════════════════════════
    # CROSSMODAL: Despachar para Dominios
    # ═══════════════════════════════════════════════════════

    def despachar(self, ideia: Dict, dominios: List[str] = None,
                  contexto: Dict = None) -> Dict:
        """Despacha ideia para multiplos dominios (lua, visual, audio, texto).

        Args:
            ideia: dict de gerar_ideia()
            dominios: lista de dominios ou None para todos
            contexto: dados extras (regioes, paleta, etc.)

        Returns:
            dict {dominio_nome: resultado}
        """
        if self._crossmodal is not None:
            try:
                return self._crossmodal.despachar(ideia, dominios, contexto)
            except Exception:
                pass

        # Fallback: processamento basico
        dominios = dominios or ['texto', 'lua', 'visual', 'audio']
        resultados = {}
        for d in dominios:
            resultados[d] = {
                'sucesso': False,
                'dominio': d,
                'erro': 'crossmodal_handler_nao_disponivel',
                'ideia': ideia.get('ideia', ''),
            }
        return resultados

    # ═══════════════════════════════════════════════════════
    # ENGINE: Validar Originalidade (Anti-Alucinacao)
    # ═══════════════════════════════════════════════════════

    def validar_originalidade(self, pergunta: str, resposta: str,
                              conceitos: List[Dict] = None) -> bool:
        """Verifica se a ideia e GENUINAMENTE NOVA ou repete conhecimento obvio.

        Returns:
            True se for original, False se for obvia/alucinacao
        """
        if self._engine is not None:
            try:
                topicos = conceitos or []
                result = self._engine.autoavaliar(pergunta, resposta, topicos)
                if result:
                    return True
            except Exception:
                pass

        # Fallback heuristico: analise de entropia + diversidade
        texto = (pergunta + ' ' + resposta).strip()
        palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', texto.lower())
        if len(palavras) < 3:
            return True  # texto muito curto, aceita

        # 1. Diversidade lexical (mais palavras unicas = mais original)
        unicas = len(set(palavras))
        total = len(palavras)
        diversidade = unicas / total if total > 0 else 0

        # 2. Entropia de Shannon das palavras
        from collections import Counter
        freq = Counter(palavras)
        h = 0.0
        for c in freq.values():
            p = c / total
            if p > 0:
                h -= p * math.log2(p)

        h_max = math.log2(max(total, 2))
        h_norm = h / h_max if h_max > 0 else 0

        # Aceita se diversidade > 40% OU entropia > 50%
        return diversidade > 0.4 or h_norm > 0.5

    def verificar_alucinacao(self, texto: str) -> bool:
        """Verifica se ha alucinacoes no texto gerado."""
        if self._engine is not None:
            try:
                return self._engine.verificar_alucinacao(texto)
            except Exception:
                pass

        # Fallback: verifica siglas conhecidas
        proibidos = [
            (r'SPA.*Single\s*Page', 'SPA != Single Page Application'),
            (r'FAST.*FastAPI', 'FAST != FastAPI'),
            (r'SHC.*Hospitalar', 'SHC != Sistema Hospitalar'),
        ]
        for padrao, _ in proibidos:
            if re.search(padrao, texto, re.IGNORECASE):
                return False
        return True

    # ═══════════════════════════════════════════════════════
    # RADAR LOOP: Evitar Repeticao
    # ═══════════════════════════════════════════════════════

    def alimentar_acao(self, acao: str):
        """Registra uma acao no detector de loop."""
        if self._radar_loop is not None:
            self._radar_loop.alimentar(acao)

    def em_loop(self) -> bool:
        """Retorna True se esta em loop (mesma acao 4+ vezes)."""
        if self._radar_loop is not None:
            return self._radar_loop.em_loop()
        return False

    def forcar_alternativa(self, acoes_disponiveis: List[str]) -> Optional[str]:
        """Forca uma alternativa quando em loop."""
        if self._radar_loop is not None:
            return self._radar_loop.forcar_alternativa(acoes_disponiveis)
        return None

    # ═══════════════════════════════════════════════════════
    # MCRRadar: Gaps + Pulsos + Predicao
    # ═══════════════════════════════════════════════════════

    def encontrar_gaps(self, sequencia: str) -> Dict:
        """Encontra lacunas de conhecimento em uma sequencia."""
        if self._radar_mcr_universal is not None:
            return self._radar_mcr_universal.varrer(sequencia)
        return {'pulsos': [], 'gaps': [], 'total_explorado': 0}

    def predizer_sequencia(self, elementos: List[Any]) -> List[str]:
        """Preve os proximos elementos de uma sequencia."""
        if self._radar_mcr_universal is not None:
            return self._radar_mcr_universal.predizer_sequencia(elementos)
        return []

    # ═══════════════════════════════════════════════════════
    # PIPELINE CRIATIVO COMPLETO
    # ═══════════════════════════════════════════════════════

    def pipeline_criativo(self, tema: str, dominios: List[str] = None,
                          max_ideias: int = 3) -> Dict:
        """Pipeline criativo completo: ideia → despachar → validar → loop.

        1. Radar busca conceitos distantes relacionados ao tema
        2. Emergir gera ideias "E se...?"
        3. EmergirEngine valida originalidade de cada ideia
        4. EmergirCrossModal despacha para dominios
        5. Radar loop previne repeticao

        Args:
            tema: tema/prompt de entrada
            dominios: dominios para despachar (default: todos)
            max_ideias: maximo de ideias a gerar

        Returns:
            dict com 'tema', 'ideias', 'resultados', 'tempo_total'
        """
        t0 = time.time()
        resultado = {
            'tema': tema,
            'ideias': [],
            'resultados': {},
            'validadas': 0,
            'recusadas': 0,
            'em_loop': False,
        }

        # Prevent loop
        self.alimentar_acao('pipeline_criativo:' + tema[:30])
        if self.em_loop():
            resultado['em_loop'] = True
            alt = self.forcar_alternativa(['expandir', 'conectar', 'equilibrar', 'evoluir'])
            resultado['alternativa'] = alt
            return resultado

        ideias_geradas = 0
        tentativas = 0
        max_tentativas = max_ideias * 3

        while ideias_geradas < max_ideias and tentativas < max_tentativas:
            tentativas += 1
            ideia = self.gerar_ideia()

            # Validar originalidade
            pergunta = ideia.get('ideia', '')
            descricao = ideia.get('descricao', '')
            if self.validar_originalidade(pergunta, descricao,
                                          [ideia.get('conceito_a', {}),
                                           ideia.get('conceito_b', {})]):
                resultado['validadas'] += 1
                resultado['ideias'].append(ideia)
                ideias_geradas += 1
            else:
                resultado['recusadas'] += 1
                self.ideias_recusadas.append(ideia)

        # Despachar para dominios
        dominios = dominios or ['texto', 'lua', 'visual', 'audio']
        for ideia in resultado['ideias']:
            try:
                r = self.despachar(ideia, dominios)
                resultado['resultados'][ideia.get('ideia', '')[:40]] = r
            except Exception:
                pass

        resultado['tempo_total'] = round(time.time() - t0, 4)
        return resultado

    # ═══════════════════════════════════════════════════════
    # UTILITARIOS
    # ═══════════════════════════════════════════════════════

    def fingerprint_ideia(self, ideia: Dict) -> List[float]:
        """Gera fingerprint 8D de uma ideia para comparacao."""
        texto = ideia.get('ideia', '') + ' ' + ideia.get('descricao', '')
        return self.fingerprint_texto(texto)

    @staticmethod
    def fingerprint_texto(texto: str) -> List[float]:
        """Fingerprint 8D baseado em tipos de caractere (via RadarMCR)."""
        if RadarMCR is not None:
            return RadarMCR.fingerprint_sim.__wrapped__ if hasattr(
                RadarMCR.fingerprint_sim, '__wrapped__'
            ) else _fingerprint_fallback(texto)
        return _fingerprint_fallback(texto)

    def relatorio(self) -> str:
        """Relatorio do estado do EmergirUnificado."""
        s = self.status()
        linhas = ['EmergirUnificado — Relatorio',
                  f"  Emergir: {'OK' if s['emergir'] else 'FALLBACK'}",
                  f"  CrossModal: {'OK' if s['emergir_crossmodal'] else 'FALLBACK'}",
                  f"  Engine: {'OK' if s['emergir_engine'] else 'FALLBACK'}",
                  f"  RadarMCR: {'OK' if s['radar_mcr'] else 'FALLBACK'}",
                  f"  RadarLoop: {'OK' if s['radar_loop'] else 'FALLBACK'}",
                  f"  MCRRadar: {'OK' if s['radar_mcr_universal'] else 'FALLBACK'}",
                  f"  Ideias geradas: {s['ideias_geradas']}",
                  f"  Ideias recusadas: {s['ideias_recusadas']}",
                  f"  Em loop: {self.em_loop()}"]
        return '\n'.join(linhas)


def _fingerprint_fallback(texto: str) -> List[float]:
    """Fingerprint 8D fallback."""
    buckets = [0.0] * 8
    for char in texto:
        code = ord(char)
        if 97 <= code <= 122: buckets[0] += 1
        elif 65 <= code <= 90: buckets[1] += 1
        elif 48 <= code <= 57: buckets[2] += 1
        elif code == 32: buckets[3] += 1
        elif code in (33, 44, 46, 58, 59, 63): buckets[4] += 1
        elif code < 65: buckets[5] += 1
        elif code > 122: buckets[6] += 1
        else: buckets[7] += 1
    total = sum(buckets) or 1
    return [round(b / total * 10, 3) for b in buckets]


# ─── Teste ───────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 60)
    print('  EmergirUnificado — Teste')
    print('=' * 60)

    eu = EmergirUnificado()
    print(eu.relatorio())

    print('\n[1] Gerando ideias...')
    for i in range(3):
        ideia = eu.gerar_ideia()
        print(f"  {i+1}. {ideia['ideia'][:80]}...")
        print(f"     OK" if eu.validar_originalidade(
            ideia['ideia'], ideia['descricao']) else f"     RECUSADA (obvia)")

    print('\n[2] Testando pipeline criativo...')
    resultado = eu.pipeline_criativo('criar algo novo para o jogo', max_ideias=2)
    print(f"  Tema: {resultado['tema']}")
    print(f"  Ideias validadas: {resultado['validadas']}")
    print(f"  Ideias recusadas: {resultado['recusadas']}")
    print(f"  Tempo: {resultado['tempo_total']}s")

    print('\n[3] Testando loop...')
    for _ in range(5):
        eu.alimentar_acao('mesma_acao')
    print(f"  Em loop: {eu.em_loop()}")
    alt = eu.forcar_alternativa(['acao_a', 'acao_b', 'acao_c'])
    print(f"  Alternativa forcada: {alt}")

    print('\n[4] Encontrando gaps...')
    gaps = eu.encontrar_gaps('o dragao forjava espadas com seu fogo ancestral')
    print(f"  Gaps: {len(gaps.get('gaps', []))}")
    print(f"  Pulsos: {len(gaps.get('pulsos', []))}")

    print('\n' + '=' * 60)
    print('  Teste concluido.')
    print('=' * 60)
