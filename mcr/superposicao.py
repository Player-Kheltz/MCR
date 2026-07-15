"""superposicao.py — Colisão real de cadeias Markov.

Princípio MCR:
  Duas cadeias colidem no mesmo ponto → geram algo que NENHUMA previu sozinha.
  Entropia decide qual colisão é "nova" vs "óbvia".

Uso:
  sp = MCRSuperposicao()
  resultado = sp.colidir(mk, coupling, estado, texto)
  → ação que emerge da colisão, não da predição individual
"""
import math
import re
from collections import defaultdict, Counter
from typing import Dict, Tuple, Optional


class MCRSuperposicao:
    """Colisão de rotas Markov: duas cadeias convergem e geram algo novo."""

    def __init__(self):
        self._historico_colisoes = []
        self.total = 0

    def colidir(self, mk, coupling, estado: str, texto: str,
                mk_pred: Tuple = None, mk_palavra=None) -> Tuple[Optional[str], float, Dict]:
        """Colide Markov (decisão) + Coupling (palavras) + mk_palavra (bigramas).
        
        Tres rotas colidem no mesmo estado:
        1. Markov: P(acao | estado) — decisao direta
        2. Coupling: P(acao | palavras) — correlacao palavra→acao
        3. mk_palavra: P(acao | bigramas) — estrutura do comando
        
        mk_palavra distingue "crie mago" (comando) de "mago elfico" (pergunta)
        porque o bigrama "crie→mago" so aparece em comandos.
        """
        self.total += 1

        # 1. Rota Markov (decisão direta)
        if mk_pred:
            acao_mk, conf_mk = mk_pred
        else:
            acao_mk, conf_mk = mk.predizer(estado)

        # 2. Rota Coupling (palavras → ação) — sem ordem
        palavras = set(re.findall(r'[a-zà-ÿ]{3,}', texto.lower()))
        scores_cp = defaultdict(float)
        for p in palavras:
            dist = coupling._palavra_acao.get(p, {})
            total = sum(dist.values()) or 1
            for a, c in dist.items():
                scores_cp[a] += c / total

        # 2b. Rota Coupling POSIÇÃO (P0 → ação) — com ordem
        # P0 (primeira palavra) tem H=0 para verbos específicos (analise, busque, edite)
        # e deve pesar MAIS que _palavra_acao que ignora ordem
        scores_p0 = defaultdict(float)
        lista_palavras = re.findall(r'[a-zà-ÿ]{3,}', texto.lower())
        if lista_palavras:
            primeira = lista_palavras[0][:10]
            p0_dist = coupling._posicao_acao.get(f'P0:{primeira}', {})
            total_p0 = sum(p0_dist.values()) or 1
            if total_p0 >= 2:
                h_p0 = 0.0
                for c in p0_dist.values():
                    p = c / total_p0
                    if p > 0: h_p0 -= p * math.log2(p)
                max_h_p0 = math.log2(max(len(p0_dist), 2))
                h_norm_p0 = h_p0 / max_h_p0 if max_h_p0 > 0 else 0
                # P0 com baixa entropia = verbo específico (analise, busque)
                # P0 com alta entropia = verbo genérico (crie, gere)
                # Verbo específico deve DOMINAR a decisão
                peso_p0 = 1.0 - h_norm_p0  # H=0 → peso=1, H=1 → peso=0
                for a, c in p0_dist.items():
                    scores_p0[a] += (c / total_p0) * peso_p0 * 2.0  # peso 2x

        # Combina palavra + posição
        for a, s in scores_p0.items():
            scores_cp[a] += s

        # 3. Self-correção: se P0 tem verbo específico (H baixa), deve dominar
        # "analise o npc" → analisar (não gerar_npc) porque "analise" em P0 é certeza
        # Mas se P0 tem verbo genérico (H alta como "crie", "create"), NÃO domina
        # porque "crie sprite" vs "crie npc" — a palavra específica decide, não o verbo
        if lista_palavras and scores_p0:
            # Calcula H de P0 para decidir se domina
            primeira = lista_palavras[0][:10]
            p0_dist_raw = coupling._posicao_acao.get(f'P0:{primeira}', {})
            total_p0_raw = sum(p0_dist_raw.values()) or 1
            if total_p0_raw >= 2:
                h_p0 = 0.0
                for c in p0_dist_raw.values():
                    p = c / total_p0_raw
                    if p > 0: h_p0 -= p * math.log2(p)
                max_h_p0 = math.log2(max(len(p0_dist_raw), 2))
                h_norm_p0 = h_p0 / max_h_p0 if max_h_p0 > 0 else 0
                # Só domina se H baixa (verbo específico: analise, busque, edite)
                # Se H alta (verbo genérico: crie, create, faca), não boosta
                if h_norm_p0 < 0.3:
                    melhor_p0 = max(scores_p0, key=scores_p0.get)
                    if scores_p0[melhor_p0] > 0.5:
                        scores_cp[melhor_p0] += scores_p0[melhor_p0]

        if not scores_cp:
            return acao_mk, conf_mk, {'rota': 'markov'}

        melhor_cp = max(scores_cp, key=scores_cp.get)
        conf_cp = scores_cp[melhor_cp] / max(sum(scores_cp.values()), 1)

        # Colisão
        acao_mk_norm = str(acao_mk)
        melhor_cp_norm = str(melhor_cp)

        if acao_mk_norm == melhor_cp_norm:
            return acao_mk, max(conf_mk, conf_cp), {'rota': 'colisao_concordam', 'forca': conf_cp}

        # Discordam → combinacao ponderada
        combinada = defaultdict(float)
        if acao_mk:
            combinada[str(acao_mk)] = conf_mk * 0.4
        for a, s in scores_cp.items():
            combinada[a] += s * 0.6

        if not combinada:
            return acao_mk, conf_mk, {'rota': 'markov'}

        melhor = max(combinada, key=combinada.get)
        conf_final = combinada[melhor] / max(sum(combinada.values()), 1)

        # Entropia da colisão
        h = 0.0
        for v in combinada.values():
            p = v / max(sum(combinada.values()), 1)
            if p > 0: h -= p * math.log2(p)
        max_h = math.log2(max(len(combinada), 2))
        h_norm = h / max_h if max_h > 0 else 1.0

        self._historico_colisoes.append({
            'acao_mk': acao_mk, 'acao_cp': melhor_cp,
            'resultado': melhor, 'entropia': h_norm,
            'concordam': acao_mk_norm == melhor_cp_norm,
        })
        if len(self._historico_colisoes) > 200:
            self._historico_colisoes = self._historico_colisoes[-200:]

        return melhor, conf_final, {
            'rota': 'colisao',
            'mk': str(acao_mk_norm),
            'cp': melhor_cp_norm,
            'entropia': round(h_norm, 3),
        }

    def estatisticas(self) -> Dict:
        if not self._historico_colisoes:
            return {'total': self.total, 'colisoes': 0}
        concordam = sum(1 for h in self._historico_colisoes if h['concordam'])
        return {
            'total': self.total,
            'colisoes': len(self._historico_colisoes),
            'concordam': concordam,
            'discordam': len(self._historico_colisoes) - concordam,
            'entropia_media': round(
                sum(h['entropia'] for h in self._historico_colisoes) /
                max(len(self._historico_colisoes), 1), 3),
        }
