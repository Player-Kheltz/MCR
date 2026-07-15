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
from collections import defaultdict, Counter
from typing import Dict, Tuple, Optional


class MCRSuperposicao:
    """Colisão de rotas Markov: duas cadeias convergem e geram algo novo."""

    def __init__(self):
        self._historico_colisoes = []
        self.total = 0

    def colidir(self, mk, coupling, estado: str, texto: str,
                mk_pred: Tuple = None) -> Tuple[Optional[str], float, Dict]:
        """Colide Markov (decisão) com Coupling (palavras) no mesmo estado.

        Args:
            mk: MarkovEngine de decisão
            coupling: MCRCoupling multi-nível
            estado: fingerprint atual
            texto: input do usuário
            mk_pred: (acao, conf) da predição Markov (opcional)

        Returns:
            (acao_colisao, confiança, metadados)
        """
        self.total += 1

        # 1. Rota Markov (decisão direta)
        if mk_pred:
            acao_mk, conf_mk = mk_pred
        else:
            acao_mk, conf_mk = mk.predizer(estado)

        # 2. Rota Coupling (palavras → ação)
        import re
        palavras = set(re.findall(r'[a-zà-ÿ]{3,}', texto.lower()))
        scores_cp = defaultdict(float)
        for p in palavras:
            dist = coupling._palavra_acao.get(p, {})
            total = sum(dist.values()) or 1
            for a, c in dist.items():
                scores_cp[a] += c / total

        if not scores_cp:
            return acao_mk, conf_mk, {'rota': 'markov'}

        melhor_cp = max(scores_cp, key=scores_cp.get)
        conf_cp = scores_cp[melhor_cp] / max(sum(scores_cp.values()), 1)

        # 3. Colisão
        acao_mk_norm = str(acao_mk).replace('_lua', '')
        melhor_cp_norm = str(melhor_cp).replace('_lua', '')

        if acao_mk_norm == melhor_cp_norm:
            # Concordam → boost
            return acao_mk, max(conf_mk, conf_cp), {'rota': 'colisao_concordam', 'forca': conf_cp}

        # Discordam → a colisão gera algo NOVO
        # Usa a distribuição completa (não só o argmax) como candidatos
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
