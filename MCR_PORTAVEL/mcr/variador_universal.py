"""variador_universal.py — Preenche gaps criativos com valores reais.

Princípio MCR: Template + gaps (fixo + variável).
Extrai distribuições de valores dos arquivos-fonte e preenche gaps
com amostragem probabilística. Cross-domínio via coupling.
"""
import re, random, math
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Optional


class VariadorUniversal:
    """Extrai distribuições de valores de arquivos e preenche gaps."""

    def __init__(self):
        self._cache = {}

    def extrair_dominio(self, diretorio: str, max_arquivos: int = 100) -> Dict:
        """Extrai distribuições de valores de todos os arquivos num diretório."""
        cache_key = str(diretorio)
        if cache_key in self._cache:
            return self._cache[cache_key]

        valores = defaultdict(list)
        arquivos = list(Path(diretorio).iterdir())[:max_arquivos]

        for f in arquivos:
            if not f.is_file():
                continue
            try:
                content = f.read_text(encoding='latin-1', errors='replace')
            except Exception:
                continue

            # Extrai pares chave.valor = numero
            for m in re.finditer(r'(\w+)\.(\w+)\s*=\s*(\d+)', content):
                chave = f"{m.group(1)}.{m.group(2)}"
                valores[chave].append(int(m.group(3)))

            # Extrai valores dentro de tabelas aninhadas
            # Ex: monster.outfit = { lookType = 100, lookHead = 0 }
            blocos = re.finditer(
                r'(\w+)\.(\w+)\s*=\s*\{([^}]+)\}',
                content, re.DOTALL)
            for bloco in blocos:
                prefixo = f"{bloco.group(1)}.{bloco.group(2)}"
                corpo = bloco.group(3)
                for m2 in re.finditer(r'(\w+)\s*=\s*(\d+)', corpo):
                    valores[f"{prefixo}.{m2.group(1)}"].append(int(m2.group(2)))

            # Strings entre aspas
            for m in re.finditer(r'"([^"]+)"', content):
                val = m.group(1)
                if 3 <= len(val) <= 40:
                    valores['strings'].append(val)

            # Palavras-chave (race, etc.)
            for m in re.finditer(r'(\w+)\s*=\s*"([^"]+)"', content):
                chave = m.group(1)
                valores[f'kw_{chave}'].append(m.group(2))

        self._cache[cache_key] = dict(valores)
        return self._cache[cache_key]

    def valor(self, dominio: Dict, chave: str, default=None) -> any:
        """Retorna um valor aleatório da distribuição."""
        dist = dominio.get(chave, [])
        if not dist:
            return default
        return random.choice(dist)

    def valor_mediana(self, dominio: Dict, chave: str, default=None) -> int:
        """Retorna a mediana da distribuição."""
        dist = dominio.get(chave, [])
        if not dist:
            return default
        return int(sorted(dist)[len(dist)//2])

    def valor_faixa(self, dominio: Dict, chave: str,
                    p_min: float = 0.1, p_max: float = 0.9,
                    default=None) -> int:
        """Retorna valor aleatório dentro da faixa [p_min, p_max] da distribuição."""
        dist = sorted(dominio.get(chave, []))
        if not dist:
            return default
        lo = dist[int(len(dist) * p_min)]
        hi = dist[min(int(len(dist) * p_max), len(dist) - 1)]
        return random.randint(lo, hi) if lo <= hi else lo

    def valor_cross(self, dominios: List[Dict], chave,
                    p_min: float = 0.1, p_max: float = 0.9,
                    default=None) -> int:
        """Busca valor em múltiplos domínios. chave pode ser str ou lista."""
        chaves = chave if isinstance(chave, list) else [chave]
        for dominio in dominios:
            for c in chaves:
                val = self.valor_faixa(dominio, c, p_min, p_max, None)
                if val is not None and val != default:
                    return val
        return default

    def valor_unico_cross(self, dominios: List[Dict], chave: str,
                          ja_usados: set = None, default=None) -> Optional[str]:
        """Busca string única em múltiplos domínios."""
        for dominio in dominios:
            val = self.valor_unico(dominio, chave, ja_usados, None)
            if val:
                return val
        return default

    def valor_unico(self, dominio: Dict, chave: str, ja_usados: set = None,
                    default=None) -> Optional[str]:
        """Retorna valor da distribuição que ainda não foi usado."""
        dist = dominio.get(chave, [])
        if not dist:
            return default
        disponiveis = [v for v in dist if ja_usados is None or v not in ja_usados]
        if not disponiveis:
            return default
        escolhido = random.choice(disponiveis)
        if ja_usados is not None:
            ja_usados.add(escolhido)
        return escolhido

    def estatisticas(self, dominio: Dict) -> Dict:
        """Resumo das distribuições extraídas."""
        return {k: {'n': len(v), 'min': min(v) if v else 0,
                     'max': max(v) if v else 0}
                for k, v in dominio.items()}
