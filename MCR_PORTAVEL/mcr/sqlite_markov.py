#!/usr/bin/env python3
"""
mcr/sqlite_markov.py — Compatibility wrapper around MCRSQLite.

Canonical implementation lives in mcr.mcr_sqlite (MCRSQLite).
SQLiteMarkov here provides the legacy API surface used by adaptadores.py
and tests: identity-per-call, predizer_adaptativo with entropy threshold,
gerar_com_identidade, close(), etc.
"""
import math, os, random, re
from typing import List, Tuple, Optional, Dict

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

from mcr.mcr_sqlite import MCRSQLite


class SQLiteMarkov:
    """Thin wrapper around MCRSQLite providing the legacy SQLiteMarkov API.

    Uso:
        mk = SQLiteMarkov('cache/mcr_adapt.db', n_max=30)
        mk.alimentar('Ferronius', ['local', 'npcType', '=', 'Game', ...])
        pred, conf, n = mk.predizer_adaptativo('Ferronius', ['local', 'npcType'])
        mk.close()
    """

    def __init__(self, db_path: str, n_max: int = 30):
        self._mcr = MCRSQLite(db_path, n_max=n_max, identidade='__sqlite_markov__')
        self.db_path = db_path
        self.n_max = n_max

    @property
    def conn(self):
        return self._mcr.conn

    def _init_tables(self):
        self._mcr._init_tables()

    def alimentar(self, identity: str, tokens: List[str]) -> int:
        """N adaptativo: N=1..5 sempre, N>5 só se distribuição difere do backoff."""
        nome = re.sub(r'[^\w\s\u00C0-\u00FF-]', '', str(identity)).strip()[:30]
        if not nome or len(tokens) < 3:
            return 0

        counts: Dict[Tuple, Dict[str, int]] = {}
        for n in range(1, self.n_max + 1):
            for i in range(len(tokens) - n):
                chave = (n,) + tuple(tokens[i:i + n])
                prox = tokens[i + n]
                if chave not in counts:
                    counts[chave] = {}
                counts[chave][prox] = counts[chave].get(prox, 0) + 1

        N_KEEP = 5
        batch_trans = []
        batch_freq: Dict[str, int] = {}

        for (n, *ctx), nexts in counts.items():
            keep = n <= N_KEEP
            if not keep:
                sufixo = tuple(ctx[1:])
                parent_key = (n - 1,) + sufixo
                parent = counts.get(parent_key)
                if parent is None or set(nexts.keys()) != set(parent.keys()):
                    keep = True

            if keep:
                chave = f"{nome}|{'|'.join(ctx)}"
                for prox, cnt in nexts.items():
                    batch_trans.append((chave, prox))
                    batch_freq[chave] = batch_freq.get(chave, 0) + cnt

        self.conn.executemany(
            "INSERT INTO trans(key, next, count) VALUES (?, ?, 1) "
            "ON CONFLICT(key, next) DO UPDATE SET count = count + 1",
            batch_trans)

        for chave, delta in batch_freq.items():
            self.conn.execute(
                "INSERT INTO freq(key, total) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET total = total + ?",
                (chave, delta, delta))

        return len(batch_trans)

    def alimentar_sequencia(self, identity: str, tokens: List[str]) -> int:
        return self.alimentar(identity, tokens)

    def commit(self):
        self.conn.commit()

    def obter_distribuicao(self, identity: str, contexto: List[str],
                           n_max: int = None) -> Tuple[List, int]:
        n_max = n_max or self.n_max
        for n in range(min(n_max, len(contexto)), 0, -1):
            chave = f"{identity}|{'|'.join(contexto[-n:])}"
            cur = self.conn.execute(
                "SELECT t.next, t.count, COALESCE(f.total, 0) "
                "FROM trans t LEFT JOIN freq f ON t.key = f.key "
                "WHERE t.key = ? ORDER BY t.count DESC LIMIT 20",
                (chave,))
            rows = cur.fetchall()
            if rows:
                return rows, n
        return [], 0

    @staticmethod
    def entropia(rows: List, total: int) -> float:
        if not rows or total == 0:
            return 1.0
        return -sum((c / total) * math.log2(c / total) for _, c, _ in rows if c > 0)

    def predizer_adaptativo(self, identity: str, contexto: List[str],
                            entropia_max: float = 0.3,
                            fallback_fn=None, deterministico: bool = False):
        """Prediz expandindo contexto até entropia < threshold."""
        max_n = min(self.n_max, len(contexto))
        for n in range(max_n, 0, -1):
            chave = f"{identity}|{'|'.join(contexto[-n:])}"
            cur = self.conn.execute(
                "SELECT t.next, t.count, COALESCE(f.total, 0) "
                "FROM trans t LEFT JOIN freq f ON t.key = f.key "
                "WHERE t.key = ? ORDER BY t.count DESC LIMIT 15",
                (chave,))
            rows = cur.fetchall()
            if not rows:
                continue
            total = rows[0][2]

            if deterministico:
                return rows[0][0], rows[0][1] / max(total, 1), n

            if total < 8:
                total_counts = sum(r[1] for r in rows)
                r = random.random() * total_counts
                acc = 0
                for next_tok, cnt, _ in rows:
                    acc += cnt
                    if r <= acc:
                        return next_tok, 1.0 - (entropia_max / 2), n
                return rows[0][0], 1.0 - (entropia_max / 2), n

            ent = self.entropia(rows, total)
            if ent < entropia_max:
                top5 = rows[:5]
                total_top5 = sum(r[1] for r in top5)
                r = random.random() * total_top5
                acc = 0
                for next_tok, cnt, _ in top5:
                    acc += cnt
                    if r <= acc:
                        return next_tok, 1.0 - ent, n
                return top5[0][0], 1.0 - ent, n

        if fallback_fn:
            pred, conf = fallback_fn(contexto[-1] if contexto else '')
            return pred, conf, 0
        return None, 0.0, 0

    def gerar_com_identidade(self, identity: str, seed: str = 'local',
                             passos: int = 60, entropia_max: float = 0.3,
                             fallback_fn=None) -> List[str]:
        """Gera sequência usando predição adaptativa."""
        seq = [seed]
        for i in range(passos):
            det = i < 5
            pred, conf, n = self.predizer_adaptativo(
                identity, seq, entropia_max, fallback_fn, det)
            if pred is None or conf < 0.01:
                break
            if len(seq) >= 3 and all(t == pred for t in seq[-3:]):
                break
            seq.append(pred)
        return seq

    def stats(self) -> Tuple[int, int]:
        cur = self.conn.execute("SELECT COUNT(*) FROM trans")
        n_trans = cur.fetchone()[0]
        cur = self.conn.execute("SELECT COUNT(*) FROM freq")
        n_freq = cur.fetchone()[0]
        return n_trans, n_freq

    def close(self):
        self.conn.commit()
        self.conn.close()

    def __repr__(self) -> str:
        n_trans, n_freq = self.stats()
        return f"SQLiteMarkov[{self.db_path}]: {n_freq} chaves, {n_trans} transições, N_max={self.n_max}"


# ─── Teste ───────────────────────────────────────────────
if __name__ == '__main__':
    import os, sys

    DB_PATH = os.path.join(_BASE, 'cache', 'mcr_adapt.db')
    if not os.path.exists(DB_PATH):
        print(f'DB não encontrado: {DB_PATH}')
        sys.exit(1)

    print('=' * 60)
    print('  SQLiteMarkov — Teste')
    print('=' * 60)

    mk = SQLiteMarkov(DB_PATH, n_max=30)
    n_trans, n_freq = mk.stats()
    print(f'  Transições: {n_trans:,}')
    print(f'  Chaves: {n_freq:,}')

    # Testa predição
    identidades = ['Adrenius', 'Ahmet', 'Sapo Azul']
    for ident in identidades:
        print(f'\n  [{ident}]')
        ctx = ['local']
        for i in range(5):
            pred, conf, n = mk.predizer_adaptativo(ident, ctx, deterministico=True)
            if pred:
                ctx.append(pred)
                print(f'    N={n}: {ctx[-2]} → {pred} (conf={conf:.3f})')
            else:
                break

    # Geração completa
    print(f'\n  [Gerando Adrenius]')
    seq = mk.gerar_com_identidade('Adrenius', 'local', passos=30)
    print(f'    Tokens: {len(seq)}')
    print(f'    {" ".join(seq[:20])}...')

    mk.close()
    print('\n  OK')
