#!/usr/bin/env python3
"""
mcr.mcr_sqlite — MCR com backend SQLite e N adaptativo.

Mesma API de MCR (engine.py), mas:
- Transicoes em disco (SQLite), nao em RAM
- N adaptativo ate 30 (igual mcr_adapt.py)
- Batch insert nativo
- Cache de 64MB + mmap 256MB
"""
import os, math, re, json, sqlite3
import heapq
from collections import Counter
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path


class MCRSQLite:
    """MCR com backend SQLite. N adaptativo ate 30.

    Uso (igual MCR):
        mcr = MCRSQLite('caminho.db')
        mcr.aprender_sequencia(tokens)     # OK
        mcr.aprender_batch([seq1, seq2])   # +rapido
        mcr.predizer(contexto)              # retorna (token, confianca)
        mcr.gerar(semente, passos)          # caminha
        mcr.entropia(chave)                 # H de um estado
        mcr.entropia_media()                # H media
    """

    def __init__(self, db_path: str, n_max: int = 30, identidade: str = 'default'):
        self.db_path = str(db_path)
        self.n_max = n_max
        self.identidade = re.sub(r'[^\w\s-]', '', str(identidade)).strip()[:30]
        self._cache_entropia: Dict[str, float] = {}
        self._entropia_media_cache = 1.0
        self._entropia_media_dirty = True

        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA cache_size=-64000")    # 64MB
        self.conn.execute("PRAGMA mmap_size=268435456")  # 256MB
        self.conn.execute("PRAGMA temp_store=MEMORY")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA page_size=16384")
        self._init_tables()

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trans (
                key TEXT NOT NULL,
                next TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (key, next)
            ) WITHOUT ROWID
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS freq (
                key TEXT PRIMARY KEY,
                total INTEGER DEFAULT 0
            ) WITHOUT ROWID
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_trans_key ON trans(key)
        """)
        self.conn.commit()

    # ─── Aprender ────────────────────────────────────────

    def aprender(self, a: str, b: str):
        """Aprende transicao a → b (compativel com MCR.engine)."""
        chave = f'{self.identidade}|{a}'
        self.conn.execute(
            "INSERT INTO trans(key, next, count) VALUES (?, ?, 1) "
            "ON CONFLICT(key, next) DO UPDATE SET count = count + 1",
            (chave, b))
        self.conn.execute(
            "INSERT INTO freq(key, total) VALUES (?, 1) "
            "ON CONFLICT(key) DO UPDATE SET total = total + 1",
            (chave,))
        self._entropia_media_dirty = True

    def aprender_sequencia(self, seq: List[str]):
        """Aprende sequencia (compativel com MCR.engine)."""
        for i in range(len(seq) - 1):
            self.aprender(seq[i], seq[i + 1])

    def aprender_batch(self, sequencias: List[List[str]]):
        """Aprende multiplas sequencias em batch.

        N adaptativo ate N_MAX: guarda N=1..5 sempre,
        N>5 so se distribuicao difere do backoff.
        """
        counts: Dict[Tuple, Dict[str, int]] = {}

        # Fase 1: contar em memoria
        for seq in sequencias:
            for n in range(1, self.n_max + 1):
                for i in range(len(seq) - n):
                    chave = (n,) + tuple(seq[i:i + n])
                    prox = seq[i + n]
                    if chave not in counts:
                        counts[chave] = {}
                    counts[chave][prox] = counts[chave].get(prox, 0) + 1

        # Fase 2: dedup N>5 vs backoff
        N_KEEP = 5
        batch_trans = []
        batch_freq: Dict[str, int] = {}

        for (n, *ctx), nexts in counts.items():
            keep = n <= N_KEEP
            if not keep:
                parent_key = (n - 1,) + tuple(ctx[1:])
                parent = counts.get(parent_key)
                if parent is None or set(nexts.keys()) != set(parent.keys()):
                    keep = True

            if keep:
                chave = f"{self.identidade}|{'|'.join(ctx)}"
                for prox, cnt in nexts.items():
                    batch_trans.append((chave, prox))
                    batch_freq[chave] = batch_freq.get(chave, 0) + cnt

        # Fase 3: batch insert
        self.conn.executemany(
            "INSERT INTO trans(key, next, count) VALUES (?, ?, 1) "
            "ON CONFLICT(key, next) DO UPDATE SET count = count + 1",
            batch_trans)

        for chave, delta in batch_freq.items():
            self.conn.execute(
                "INSERT INTO freq(key, total) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET total = total + ?",
                (chave, delta, delta))

        self._entropia_media_dirty = True

    # ─── Predizer ─────────────────────────────────────────

    def predizer(self, a: str) -> Tuple[Optional[str], float]:
        """Prediz proximo token (compativel com MCR.engine).

        Tenta N=n_max, ..., 1 ate encontrar dados.
        """
        ctx = a.split('|') if '|' in a else [a]

        for n in range(min(self.n_max, len(ctx)), 0, -1):
            chave = f"{self.identidade}|{'|'.join(ctx[-n:])}"
            cur = self.conn.execute(
                "SELECT t.next, t.count, COALESCE(f.total, 0) "
                "FROM trans t "
                "LEFT JOIN freq f ON t.key = f.key "
                "WHERE t.key = ? "
                "ORDER BY t.count DESC LIMIT 3",
                (chave,))

            rows = cur.fetchall()
            if rows:
                melhor = rows[0]
                return (melhor[0], melhor[1] / max(melhor[2], 1))

        return (None, 0.0)

    def predizer_n(self, a: str, n: int = 3) -> List[Tuple[str, float]]:
        """Top-N proximos tokens (compativel com MCR.engine)."""
        ctx = a.split('|') if '|' in a else [a]

        for depth in range(min(self.n_max, len(ctx)), 0, -1):
            chave = f"{self.identidade}|{'|'.join(ctx[-depth:])}"
            cur = self.conn.execute(
                "SELECT t.next, t.count, COALESCE(f.total, 0) "
                "FROM trans t "
                "LEFT JOIN freq f ON t.key = f.key "
                "WHERE t.key = ? "
                "ORDER BY t.count DESC LIMIT ?",
                (chave, n))

            rows = cur.fetchall()
            if rows:
                total = max(rows[0][2], 1)
                return [(r[0], r[1] / total) for r in rows]

        return []

    def gerar(self, semente: str, passos: int = 10) -> List[str]:
        """Gera sequencia (compativel com MCR.engine)."""
        seq = [semente]
        atual = semente
        for _ in range(passos):
            prox, conf = self.predizer(atual)
            if prox is None or conf < 0.01:
                break
            seq.append(prox)
            atual = prox
        return seq

    # ─── Entropia ─────────────────────────────────────────

    def entropia(self, a: str) -> float:
        """Entropia de Shannon de um estado (com cache)."""
        if a in self._cache_entropia:
            return self._cache_entropia[a]

        ctx = a.split('|') if '|' in a else [a]

        for depth in range(min(self.n_max, len(ctx)), 0, -1):
            chave = f"{self.identidade}|{'|'.join(ctx[-depth:])}"
            cur = self.conn.execute(
                "SELECT t.count, COALESCE(f.total, 0) "
                "FROM trans t "
                "LEFT JOIN freq f ON t.key = f.key "
                "WHERE t.key = ?",
                (chave,))

            rows = cur.fetchall()
            if rows:
                total = max(rows[0][1], 1)
                h = -sum((c / total) * math.log2(c / total) for c, _ in rows)
                self._cache_entropia[a] = h
                return h

        self._cache_entropia[a] = 1.0
        return 1.0

    def entropia_media(self) -> float:
        """Entropia media de todos os estados (com cache lazy)."""
        if self._entropia_media_dirty:
            cur = self.conn.execute("SELECT COUNT(*) FROM freq")
            n = cur.fetchone()[0]
            if n == 0:
                self._entropia_media_cache = 1.0
            else:
                cur = self.conn.execute(
                    "SELECT AVG(e) FROM ("
                    "SELECT -SUM(t.count * 1.0 / f.total * "
                    "  log2(t.count * 1.0 / f.total)) AS e "
                    "FROM trans t "
                    "JOIN freq f ON t.key = f.key "
                    "GROUP BY t.key)")
                row = cur.fetchone()
                self._entropia_media_cache = round(row[0], 3) if row and row[0] else 1.0
            self._entropia_media_dirty = False

        return self._entropia_media_cache

    # ─── Utilidades ───────────────────────────────────────

    def jaccard(self, outra: 'MCRSQLite') -> float:
        """Jaccard entre estados de duas instancias."""
        cur_a = self.conn.execute("SELECT DISTINCT key FROM freq")
        cur_b = outra.conn.execute("SELECT DISTINCT key FROM freq")
        set_a = {r[0] for r in cur_a.fetchall()}
        set_b = {r[0] for r in cur_b.fetchall()}
        if not set_a or not set_b:
            return 0.0
        inter = set_a & set_b
        uniao = set_a | set_b
        return len(inter) / len(uniao) if uniao else 0.0

    def stats(self) -> Dict:
        """Estatisticas do MCR."""
        cur = self.conn.execute("SELECT COUNT(*) FROM freq")
        n_estados = cur.fetchone()[0]
        cur = self.conn.execute("SELECT COUNT(*) FROM trans")
        n_trans = cur.fetchone()[0]
        return {
            'nome': self.identidade,
            'estados': n_estados,
            'transicoes': n_trans,
            'entropia_media': self.entropia_media(),
            'n_max': self.n_max,
            'db': self.db_path,
        }

    def salvar(self, arquivo: str = None) -> bool:
        """Forca checkpoint SQLite (equivalente a salvar JSON)."""
        try:
            self.conn.commit()
            return True
        except Exception:
            return False

    def __repr__(self) -> str:
        s = self.stats()
        return (f"MCRSQLite[{s['nome']}]: {s['estados']} estados, "
                f"{s['transicoes']} transicoes, H={s['entropia_media']}, "
                f"N_max={s['n_max']}")
