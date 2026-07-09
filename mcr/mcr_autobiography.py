"""mcr.mcr_autobiography — A Memoria Narrativa do MCR.
Traduz dados crus do EpisodicMemory em lembrancas de longo prazo."""
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from mcr.paths import KG_DIR


class Autobiography:
    """Memoria narrativa de longo prazo. Lembrancas, nao apenas dados."""

    def __init__(self):
        self._path = KG_DIR / "autobiography.json"
        self._memorias: List[Dict] = []
        self._carregar()

    def _carregar(self):
        if self._path.exists():
            try:
                with open(self._path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                self._memorias = dados.get('memorias', [])
            except Exception:
                self._memorias = []

    def _salvar(self):
        try:
            KG_DIR.mkdir(parents=True, exist_ok=True)
            # Mantem apenas as 200 mais recentes
            mems = self._memorias[-200:]
            with open(self._path, 'w', encoding='utf-8') as f:
                json.dump({'memorias': mems, 'total': len(mems)}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record_memory(self, event_type: str, summary: str, actors: List[str],
                      detalhes: str = '', opiniao: str = '') -> bool:
        """Registra uma memoria narrativa."""
        memoria = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'event_type': event_type,
            'summary': summary[:300],
            'actors': actors[:5],
            'detalhes': detalhes[:500] if detalhes else '',
            'opiniao': opiniao[:200] if opiniao else '',
            'id': int(time.time() * 1000) % 1000000,
        }
        self._memorias.append(memoria)
        self._salvar()
        return True

    def recall(self, query: str, limit: int = 3) -> List[str]:
        """Busca memorias narrativas por palavra-chave ou ator."""
        if not self._memorias:
            return []

        query_lower = query.lower()
        termos = set(re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', query_lower))

        pontuadas = []
        for m in reversed(self._memorias):  # Mais recentes primeiro
            score = 0
            corpo = (m['summary'] + ' ' + ' '.join(m['actors']) + ' ' + m.get('opiniao', '')).lower()

            # Score por termo
            for t in termos:
                if t in corpo:
                    score += 2
            # Score por match exato de ator
            for ator in m['actors']:
                if ator.lower() in query_lower:
                    score += 5
            # Score por tipo de evento
            if m['event_type'].lower() in query_lower:
                score += 3

            if score > 0:
                # Formata como narrativa
                data = m['timestamp'][:10]
                narrativa = f"[{data}] {m['summary']}"
                if m.get('opiniao'):
                    narrativa += f" (Eu pensei: {m['opiniao'][:80]})"
                pontuadas.append((score, narrativa))

        pontuadas.sort(key=lambda x: -x[0])
        return [n for _, n in pontuadas[:limit]]

    def estatisticas(self) -> Dict:
        tipos = {}
        for m in self._memorias:
            t = m.get('event_type', 'unknown')
            tipos[t] = tipos.get(t, 0) + 1
        return {
            'total_memorias': len(self._memorias),
            'tipos': tipos,
            'ultima': self._memorias[-1]['timestamp'] if self._memorias else 'nenhuma',
        }
