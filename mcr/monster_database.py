"""mcr.monster_database — Base de dados de monstros (data-driven).

Modelado em item_database.py. Mina dados reais dos 1,678 monstros.
Zero hardcode — tudo extraído dos arquivos .lua do Canary.
"""
import re, statistics
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Optional


class MonsterDatabase:
    """Database de monstros minerada dos arquivos reais."""

    def __init__(self, monster_dir: Path = None):
        if monster_dir is None:
            from mcr.paths import CANARY_MONSTER_DIR
            monster_dir = CANARY_MONSTER_DIR
        self._dir = monster_dir
        self._monsters: Dict[str, dict] = {}
        self._stats_all: List[tuple] = []
        self._tiers: Dict[str, tuple] = {}
        self._race_map: Dict[str, str] = {}
        self._loot: List[dict] = []
        self._carregado = False

    def _carregar(self):
        if self._carregado:
            return
        race_cooc = defaultdict(Counter)
        name_health = defaultdict(list)

        for f in self._dir.glob('**/*.lua'):
            try:
                c = f.read_text(encoding='latin-1', errors='replace')
            except Exception:
                continue
            h = re.search(r'health\s*=\s*(\d+)', c)
            e = re.search(r'experience\s*=\s*(\d+)', c)
            s = re.search(r'speed\s*=\s*(\d+)', c)
            rm = re.search(r'race\s*=\s*"(\w+)"', c)
            lt = re.search(r'lookType\s*=\s*(\d+)', c)
            name = re.search(r'name\s*=\s*"([^"]+)"', c)

            if h and e and s:
                self._stats_all.append((int(h.group(1)), int(e.group(1)), int(s.group(1))))

            if rm and name:
                race = rm.group(1)
                n = name.group(1).lower()
                self._monsters[n] = {
                    'name': n, 'race': race,
                    'health': int(h.group(1)) if h else 0,
                    'experience': int(e.group(1)) if e else 0,
                    'speed': int(s.group(1)) if s else 0,
                    'looktype': int(lt.group(1)) if lt else 0,
                }
                for t in re.findall(r'[a-z]{3,}', f.stem.lower()):
                    race_cooc[t][race] += 1
                    if h:
                        name_health[t].append(int(h.group(1)))

            for lm in re.finditer(r'\{\s*id\s*=\s*(\d+)\s*,\s*chance\s*=\s*(\d+)\s*,\s*maxCount\s*=\s*(\d+)\s*\}', c):
                self._loot.append({
                    'id': int(lm.group(1)), 'chance': int(lm.group(2)),
                    'maxCount': int(lm.group(3))
                })

        # Tiers por percentil de health
        hs = sorted(s[0] for s in self._stats_all) if self._stats_all else [100, 1000, 5000]
        n = len(hs)
        p33 = hs[int(n * 0.33)] if n > 2 else 1000
        p66 = hs[int(n * 0.66)] if n > 2 else 7320

        def _med(tier):
            if not tier: return (240, 100, 95)
            return (int(statistics.median([x[0] for x in tier])),
                    int(statistics.median([x[1] for x in tier])),
                    int(statistics.median([x[2] for x in tier])))

        low = [x for x in self._stats_all if x[0] <= p33]
        mid = [x for x in self._stats_all if p33 < x[0] <= p66]
        high = [x for x in self._stats_all if x[0] > p66]
        self._tiers = {'low': _med(low), 'medium': _med(mid), 'high': _med(high)}
        self._thresholds = (p33, p66)

        # Race keywords (>= 3 monstros, dominante > 50%)
        for kw, races in race_cooc.items():
            total = sum(races.values())
            if total >= 3:
                top_race, top_count = races.most_common(1)[0]
                if top_count / total > 0.5 and top_race != 'blood':
                    self._race_map[kw] = top_race

        # Name → health (para inferência de perigo)
        self._name_health = {k: int(statistics.median(v)) for k, v in name_health.items() if len(v) >= 2}

        self._carregado = True

    def buscar_por_nome(self, nome: str) -> Optional[dict]:
        self._carregar()
        return self._monsters.get(nome.lower())

    def get_tiers(self) -> Dict[str, tuple]:
        self._carregar()
        return self._tiers

    def get_race(self, keywords: List[str]) -> str:
        self._carregar()
        for kw in sorted(keywords, key=lambda x: -len(x)):
            if kw in self._race_map:
                return self._race_map[kw]
        return 'blood'

    def get_perigo(self, keywords: List[str]) -> str:
        self._carregar()
        p33, p66 = self._thresholds
        for kw in keywords:
            if kw in self._name_health:
                h = self._name_health[kw]
                if h > p66: return 'high'
                if h < p33: return 'low'
                return 'medium'
        return 'medium'

    def get_loot(self, n: int = 3) -> List[dict]:
        self._carregar()
        freq = Counter((l['id'], l['chance'], l['maxCount']) for l in self._loot)
        return [{'id': lid, 'chance': lc, 'maxCount': lm}
                for (lid, lc, lm), _ in freq.most_common(n)]

    def estatisticas(self) -> Dict:
        self._carregar()
        return {
            'total_monstros': len(self._monsters),
            'tiers': {k: v[0] for k, v in self._tiers.items()},
            'race_keywords': len(self._race_map),
            'loot_items': len(self._loot),
        }
