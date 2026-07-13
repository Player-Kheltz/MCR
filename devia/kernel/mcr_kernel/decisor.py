#!/usr/bin/env python3
"""decisor.py — Decision engine, entropy detector, thresholds, and weight learning.

Cálculo de entropia e decisão de estado.
Tudo aprendido por Markov, nada hardcoded.
"""
from typing import Dict, List, Optional

from .engine import MCR


class MCRPeso:
    """Aprende PESOS dos dados, não de regras fixas."""
    
    def __init__(self, nome="pesos"):
        self.mk = MCR(nome)
        self.total_obs = 0
    
    def aprender(self, categoria: str, valor: float):
        self.mk.aprender(f"CAT_{categoria}", f"VAL_{int(valor*10)}")
        self.total_obs += 1
    
    def consultar(self, categoria: str, fallback: float = 1.0) -> float:
        estado = f"CAT_{categoria}"
        if estado not in self.mk.transicoes: return fallback
        prox, conf = self.mk.predizer(estado)
        if prox is None or conf < 0.1: return fallback
        try:
            return int(prox.replace('VAL_', '')) / 10.0
        except Exception:
            return fallback
    
    def pesos_mais_comuns(self, top_n: int = 5) -> list:
        result = []
        for estado, trans in self.mk.transicoes.items():
            if not estado.startswith('CAT_'): continue
            melhor = max(trans, key=trans.get) if trans else ''
            try:
                valor = int(melhor.replace('VAL_', '')) / 10.0
            except Exception:
                valor = 0
            freq = sum(trans.values())
            result.append((freq, estado.replace('CAT_', ''), valor))
        result.sort(key=lambda x: -x[0])
        return [(c, v) for _, c, v in result]


class MCREntropia:
    """Detecta loops. Internamente usa MCR."""
    def __init__(self, nome="entropia"):
        self.mk = MCR(nome)
        self.janela = 10
        self.historico_entropias = []
    
    def alimentar(self, token):
        self.mk.aprender(f"T:{str(token)[:50]}", "V")
        h = self.mk.entropia(f"T:{str(token)[:50]}")
        self.historico_entropias.append(h)
        if len(self.historico_entropias) > 100:
            self.historico_entropias = self.historico_entropias[-50:]
    
    def _entropia_local(self) -> float:
        if len(self.historico_entropias) < 3: return 1.0
        recentes = self.historico_entropias[-10:]
        return sum(recentes) / len(recentes) if recentes else 1.0
    
    def esta_em_loop(self) -> bool:
        return self._entropia_local() < 0.3


class MCRRuido:
    """Aprende QUE TIPO de ruído funciona para quebrar loops."""
    
    def __init__(self, nome="ruido"):
        self.mk = MCR(nome)
        self.tipos = ['byte_global', 'palavra_outro_topico', 'pontuacao', 'semente_original']
    
    def tentar(self, tipo: str, estado_atual: str) -> str:
        return self.mk.predizer(f"{tipo}_{estado_atual}")[0]
    
    def registrar(self, tipo: str, sucesso: bool):
        self.mk.aprender(tipo, "sucesso" if sucesso else "falha")
    
    def melhor_tipo(self) -> str:
        scores = []
        for t in self.tipos:
            if t in self.mk.transicoes:
                prox = self.mk.transicoes[t]
                suc = prox.get('sucesso', 0)
                fal = prox.get('falha', 0)
                taxa = suc / max(suc + fal, 1)
                scores.append((taxa, t))
        scores.sort(key=lambda x: -x[0])
        return scores[0][1] if scores else 'palavra_outro_topico'
    
    def taxa_sucesso(self, tipo: str) -> float:
        if tipo not in self.mk.transicoes: return 0.5
        prox = self.mk.transicoes[tipo]
        suc = prox.get('sucesso', 0)
        fal = prox.get('falha', 0)
        return suc / max(suc + fal, 1)


class MCRDecisor:
    """Decide o FLUXO de ações — thin wrapper em torno de MCR nivel 'decisao'."""
    
    def __init__(self, nome="decisor"):
        self.mk = MCR(nome)
        self.acoes_possiveis = ['kg_primeiro', 'conector_primeiro', 'cadeia_direto',
                                'kg_conector_cadeia', 'conector_kg_cadeia']
    
    def aprender(self, estado_pergunta: str, acao: str, sucesso: bool):
        tag = "ok" if sucesso else "falha"
        self.mk.aprender(f"{estado_pergunta}_{tag}", acao)
    
    def decidir(self, pergunta: str, estado_extra: str = "") -> str:
        tipo = self._classificar_pergunta(pergunta)
        estado = f"{tipo}_{estado_extra}" if estado_extra else tipo
        if estado in self.mk.transicoes:
            melhor = max(self.mk.transicoes[estado], key=self.mk.transicoes[estado].get)
            return melhor
        if tipo == 'explicacao': return 'kg_primeiro'
        if tipo == 'criacao': return 'conector_primeiro'
        if tipo == 'busca': return 'kg_conector_cadeia'
        return 'kg_conector_cadeia'
    
    def _classificar_pergunta(self, pergunta: str) -> str:
        estado = f"PERG:{pergunta.lower()}"
        if estado in self.mk.transicoes:
            prox, conf = self.mk.predizer(estado)
            if prox and conf > 0.2:
                return str(prox)
        p = pergunta.lower()
        for palavra, categoria in [
            ('explique', 'explicacao'), ('o que e', 'explicacao'),
            ('como funciona', 'explicacao'), ('defina', 'explicacao'),
            ('crie', 'criacao'), ('gere', 'criacao'), ('criar', 'criacao'),
            ('implemente', 'criacao'), ('busque', 'busca'),
            ('encontre', 'busca'), ('procure', 'busca'), ('onde', 'busca'),
        ]:
            if palavra in p:
                self.aprender(estado, categoria, True)
                return categoria
        self.aprender(estado, 'geral', True)
        return 'geral'

    # ─── Decisao de pular parser (Fase C→G) ─────────────
    # A decisao usa entropia do cluster + similaridade Jaccard
    # via Ponte Otima, sem thresholds fixos.

    def decidir_pular_parser(self, entropia_cluster: float,
                              similaridade: float,
                              min_similaridade_base: float = 0.3) -> str:
        """Decide se pode pular o tree-sitter para uma entidade.
        
        Usa entropia do cluster como modulador do limiar de similaridade:
        - Cluster homogeneo (entropia baixa): exige menos similaridade
        - Cluster diverso (entropia alta): exige mais similaridade
        
        Formula (Ponte Otima):
            limiar = min_similaridade_base + (1 - min_similaridade_base) * entropia_cluster
            Se similaridade >= limiar → pula parser
        
        Args:
            entropia_cluster: entropia normalizada [0, 1] do cluster
            similaridade: similaridade Jaccard entre raw tokens e o cluster
            min_similaridade_base: similaridade minima (quando entropia = 0)
        
        Returns:
            'pular_parser' se pode pular, 'usar_parser' caso contrario
        """
        if entropia_cluster <= 0:
            return 'pular_parser'  # cluster vazio ou trivial
        
        # Limiar adaptativo: entropia alta → mais exigente
        limiar = min_similaridade_base + (1.0 - min_similaridade_base) * entropia_cluster
        
        # Aprende esta decisao no Markov
        estado = f"H:{entropia_cluster:.2f}_S:{similaridade:.2f}"
        
        if similaridade >= limiar:
            self.mk.aprender(estado, "PULAR_PARSER")
            return 'pular_parser'
        else:
            self.mk.aprender(estado, "USAR_PARSER")
            return 'usar_parser'


class MCRDiagnostico:
    """Diagnostico MCR'zificado — Markov de estado para debug."""
    
    def __init__(self, nome="diagnostico"):
        self.mk = MCR(nome)
        self.historico = []
    
    def alimentar(self, estado: dict, diagnostico: str):
        codigo = self._codificar_estado(estado)
        self.mk.aprender(codigo, diagnostico)
        self.historico.append((codigo, diagnostico))
    
    def diagnosticar(self, estado: dict) -> str:
        codigo = self._codificar_estado(estado)
        if codigo in self.mk.transicoes:
            melhor = max(self.mk.transicoes[codigo], key=self.mk.transicoes[codigo].get)
            return melhor
        return "sem_diagnostico_previo"
    
    def _codificar_estado(self, estado: dict) -> str:
        partes = []
        for k, v in estado.items():
            if isinstance(v, (int, float)):
                nivel = 'alto' if v > 0.7 else 'medio' if v > 0.3 else 'baixo'
                partes.append(f"{k}:{nivel}")
        return '|'.join(partes)


class MCRPesoNota:
    """Aprende pesos ideais para cada componente da nota."""
    
    def __init__(self, nome="peso_nota"):
        self.mk = MCR(nome)
        self.historico = []
    
    def aprender(self, caracteristicas: dict, nota_real: float):
        estado = self._codificar(caracteristicas)
        self.mk.aprender(estado, f"NOTA:{int(nota_real*10)}")
        self.historico.append((caracteristicas, nota_real))
    
    def calcular(self, byte_s=None, palavra_s=None, token_s=None) -> float:
        if not self.historico:
            nota = 5.0
            if byte_s is not None: nota += (byte_s - 5) * 0.3
            if palavra_s is not None: nota += (palavra_s - 5) * 0.5
            if token_s is not None: nota += (token_s - 3) * 0.2
            return max(0, min(10, nota))
        caracteristicas = {}
        if byte_s is not None: caracteristicas['byte'] = byte_s / 10
        if palavra_s is not None: caracteristicas['palavra'] = palavra_s / 10
        if token_s is not None: caracteristicas['token'] = token_s / 10
        estado = self._codificar(caracteristicas)
        if estado in self.mk.transicoes:
            prox, conf = self.mk.predizer(estado)
            if prox and conf > 0.1:
                try:
                    return int(prox.replace('NOTA:', '')) / 10.0
                except Exception:
                    pass
        notas_similares = []
        for c, n in self.historico:
            sim = sum(1 for k in caracteristicas if k in c and abs(caracteristicas[k] - c[k]) < 0.2)
            if sim >= 2:
                notas_similares.append(n)
        return sum(notas_similares)/len(notas_similares) if notas_similares else 5.0
    
    def _codificar(self, carac: dict) -> str:
        partes = []
        for k in ['byte', 'palavra', 'token']:
            v = int(carac.get(k, 0) * 10)
            partes.append(f"{k}:{v}")
        return '|'.join(partes)


class MCRThreshold:
    """Threshold — thin wrapper em torno de MCR nivel 'threshold'."""
    
    def __init__(self, nome="threshold"):
        self.mk = MCR(nome)
        self.observacoes = []
    
    def observar(self, valor: float):
        self.observacoes.append(valor)
        self.mk.aprender(f"VAL:{int(valor*100)}", "OBS")
    
    def calcular(self, multiplicador: float = 1.0) -> float:
        if len(self.observacoes) < 3: return 0.5
        from statistics import median
        return median(self.observacoes) * multiplicador
    
    def obter(self, chave: str, fallback: float = 0.5) -> float:
        pred = self.mk.predizer(f"THR:{chave}")
        if pred[0] is not None and pred[1] > 0.3:
            try: return int(pred[0]) / 100.0
            except Exception: pass
        if len(self.observacoes) >= 3:
            from statistics import median
            return median(self.observacoes)
        return fallback
    
    def aprender(self, chave: str, valor: float):
        self.mk.aprender(f"THR:{chave}", f"{int(valor*100)}")
        self.observar(valor)


_MCR_THRESHOLD_FILTRO = MCRThreshold("filtro_global")
_MCR_THRESHOLD_CONF = MCRThreshold("confianca")
_MCR_THRESHOLD_TAMANHO = MCRThreshold("tamanho")
_MCR_THRESHOLD_REPETICAO = MCRThreshold("repeticao")
_MCR_THRESHOLD_PALAVRA = MCRThreshold("palavra")
_MCR_THRESHOLD_CONEXAO = MCRThreshold("conexao")
_MCR_THRESHOLD_NOTA = MCRThreshold("nota")
