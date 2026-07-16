"""esfera.py — MCREsfera: Correlação N-dimensional entre níveis.

Princípios MCR:
  TUDO é P(b|a) — aprende P(valor_B | valor_A) entre QUALQUER par de níveis
  Entropia descobre estrutura — poda correlações fracas (freq < 2)
  Mesmo motor, N domínios — mesma esfera pra NPC, monstro, sprite, audio

Uso:
  esfera.alimentar_par("palavra", "lookType", "Mago", "128")
  esfera.alimentar_par("palavra", "health", "Mago", "100")
  esfera.predizer_cross("lookType", palavra="Mago") → "128"
  esfera.predizer_cross("health", palavra="Mago") → "100"
"""
from collections import defaultdict
from typing import Dict, Optional, Any


class MCREsfera:
    """Aprendizado N-dimensional de correlações entre níveis.

    cross[nivel_a][valor_a][nivel_b][valor_b] = contagem
    Permite predizer qualquer valor em qualquer nível dado contexto.
    """

    def __init__(self):
        self.cross: Dict[str, Dict] = {}
        self.freq: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.total = 0

    def _init(self, nivel):
        if nivel not in self.cross:
            self.cross[nivel] = {}

    def alimentar_par(self, nivel_a, nivel_b, valor_a, valor_b):
        """Registra correlação bidirecional entre dois níveis."""
        va, vb = str(valor_a), str(valor_b)
        self._init(nivel_a)
        self._init(nivel_b)

        # A → B
        c = self.cross[nivel_a]
        if va not in c: c[va] = {}
        if nivel_b not in c[va]: c[va][nivel_b] = defaultdict(int)
        c[va][nivel_b][vb] += 1
        self.freq[nivel_a][va] += 1

        # B → A (simétrico)
        c2 = self.cross[nivel_b]
        if vb not in c2: c2[vb] = {}
        if nivel_a not in c2[vb]: c2[vb][nivel_a] = defaultdict(int)
        c2[vb][nivel_a][va] += 1
        self.freq[nivel_b][vb] += 1

        self.total += 2

    def predizer_cross(self, nivel_alvo, **contexto) -> Optional[str]:
        """Prediz valor em nivel_alvo dado contexto em QUALQUER nível.

        Args:
            nivel_alvo: nome do nível a prever (ex: "lookType")
            **contexto: pares nivel=valor (ex: palavra="Mago")
        Returns:
            Valor mais provável ou None
        """
        candidatos = defaultdict(float)

        for nivel_ctx, valor_ctx in contexto.items():
            vc = str(valor_ctx)
            if nivel_ctx not in self.cross:
                continue
            if vc not in self.cross[nivel_ctx]:
                continue
            if nivel_alvo not in self.cross[nivel_ctx][vc]:
                continue

            dist = self.cross[nivel_ctx][vc][nivel_alvo]
            total = sum(dist.values()) or 1
            for val, count in dist.items():
                candidatos[val] += count / total

        if not candidatos:
            return None
        return max(candidatos, key=candidatos.get)

    def predizer_multi(self, nivel_alvo, n: int = 3, **contexto) -> list:
        """Retorna os N valores mais prováveis."""
        candidatos = defaultdict(float)

        for nivel_ctx, valor_ctx in contexto.items():
            vc = str(valor_ctx)
            if nivel_ctx not in self.cross: continue
            if vc not in self.cross[nivel_ctx]: continue
            if nivel_alvo not in self.cross[nivel_ctx][vc]: continue

            dist = self.cross[nivel_ctx][vc][nivel_alvo]
            total = sum(dist.values()) or 1
            for val, count in dist.items():
                candidatos[val] += count / total

        return sorted(candidatos, key=candidatos.get, reverse=True)[:n]

    def estatisticas(self) -> Dict:
        niveis = list(self.cross.keys())
        return {
            'total': self.total,
            'niveis': len(niveis),
            'niveis_nomes': niveis[:10],
            'pares': sum(len(self.cross[n]) for n in niveis),
        }
