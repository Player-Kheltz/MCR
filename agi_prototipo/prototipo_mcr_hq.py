#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 1: MCRMemory — Memoria de Longo Prazo Persistente
========================================================
Substitui List[Dict] por SQLite. Suporta milhoes de exemplos.
Busca por similaridade de fingerprint em O(log n) com indice bucketed.
"""
import os, sys, json, sqlite3, math, time, struct
from typing import Dict, List, Tuple, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import (
    MCR, MCRByteUtils, MCRSignatureExpansiva, MCRThreshold,
    EstadoMundo, MotorFisica, Entidade
)
from prototipo_mcr_config import C

DB_PATH = os.path.join(os.path.dirname(__file__), "mcr_hq.db")


class MCRMemory:
    """Memoria persistente em SQLite com indice de fingerprint.
    
    Tabelas:
      - transicoes_byte:   (antes, depois, peso)
      - estados_mundo:     (fp, serial, timestamp)
      - planos:            (fp_objetivo, sequencia_acoes, nota)
      - causais:           (fp_antes, acao, fp_depois, delta)
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.con = sqlite3.connect(db_path, check_same_thread=False)
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute("PRAGMA synchronous=NORMAL")
        self._criar_tabelas()
        self.total_insercoes = 0
        self.threshold = MCRThreshold("hq")

    def _criar_tabelas(self):
        c = self.con.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS estados_mundo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fp TEXT NOT NULL,
                serial TEXT NOT NULL,
                timestamp REAL NOT NULL,
                bucket INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_estados_fp ON estados_mundo(fp);
            CREATE INDEX IF NOT EXISTS idx_estados_bucket ON estados_mundo(bucket);
            
            CREATE TABLE IF NOT EXISTS causais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fp_antes TEXT NOT NULL,
                acao TEXT NOT NULL,
                fp_depois TEXT NOT NULL,
                delta TEXT NOT NULL,
                timestamp REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_causais_antes ON causais(fp_antes);
            CREATE INDEX IF NOT EXISTS idx_causais_delta ON causais(delta);
            
            CREATE TABLE IF NOT EXISTS planos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fp_objetivo TEXT NOT NULL,
                acoes TEXT NOT NULL,
                nota REAL DEFAULT 0,
                timestamp REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_planos_fp ON planos(fp_objetivo);
            
            CREATE TABLE IF NOT EXISTS transicoes_byte (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                antes TEXT NOT NULL,
                depois TEXT NOT NULL,
                peso INTEGER DEFAULT 1,
                UNIQUE(antes, depois)
            );
            
            CREATE TABLE IF NOT EXISTS metadados (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            );
        """)
        self.con.commit()

    def salvar_estado(self, estado: EstadoMundo) -> str:
        fp = str(estado.fingerprint(C("dim_fingerprint")))
        serial = estado.serializar()
        bucket = hash(fp) % 256
        self.con.execute(
            "INSERT OR REPLACE INTO estados_mundo (fp, serial, timestamp, bucket) VALUES (?,?,?,?)",
            (fp, serial, time.time(), bucket))
        self.con.commit()
        self.total_insercoes += 1
        self.threshold.observar(1.0)
        return fp

    def salvar_causal(self, antes: EstadoMundo, acao: str, depois: EstadoMundo):
        fp_a = str(antes.fingerprint(C("dim_fingerprint")))
        fp_d = str(depois.fingerprint(C("dim_fingerprint")))
        delta = str(MCRByteUtils.delta_fingerprint(antes.serializar(), depois.serializar(), 8))
        self.con.execute(
            "INSERT INTO causais (fp_antes, acao, fp_depois, delta, timestamp) VALUES (?,?,?,?,?)",
            (fp_a, acao, fp_d, delta, time.time()))
        self.con.commit()
        self.total_insercoes += 1

    def salvar_plano(self, fp_objetivo: str, acoes: List[str], nota: float = 0.0):
        self.con.execute(
            "INSERT INTO planos (fp_objetivo, acoes, nota, timestamp) VALUES (?,?,?,?)",
            (fp_objetivo, "|".join(acoes), nota, time.time()))
        self.con.commit()

    def buscar_estado_similar(self, fp_alvo: str, limite: int = 10) -> List[Tuple[str, str, float]]:
        """Busca estados por similaridade de fingerprint usando bucket index."""
        bucket = hash(fp_alvo) % 256
        resultados = self.con.execute(
            "SELECT fp, serial FROM estados_mundo WHERE bucket=? ORDER BY timestamp DESC LIMIT ?",
            (bucket, limite * 10)).fetchall()
        if not resultados:
            resultados = self.con.execute(
                "SELECT fp, serial FROM estados_mundo ORDER BY timestamp DESC LIMIT ?",
                (limite,)).fetchall()

        # Parse fp_alvo
        fp_alvo_lista = [float(x) for x in fp_alvo.strip("[]").split(",") if x.strip()]
        
        # Score por similaridade de cosseno
        scored = []
        for fp_str, serial in resultados:
            fp_outra = [float(x) for x in fp_str.strip("[]").split(",") if x.strip()]
            if not fp_outra: continue
            sim = MCRByteUtils.similaridade_cosseno(fp_alvo_lista, fp_outra)
            scored.append((sim, fp_str, serial))
        
        scored.sort(key=lambda x: -x[0])
        return [(fp, ser, s) for s, fp, ser in scored[:limite]]

    def buscar_causal(self, fp_antes: str, acao: str) -> Optional[str]:
        """Encontra estado resultante de (fp_antes + acao)."""
        r = self.con.execute(
            "SELECT fp_depois FROM causais WHERE fp_antes=? AND acao=? ORDER BY timestamp DESC LIMIT 1",
            (fp_antes, acao)).fetchone()
        return r[0] if r else None

    def buscar_plano(self, fp_objetivo: str) -> Optional[Tuple[List[str], float]]:
        """Encontra plano para atingir um objetivo."""
        r = self.con.execute(
            "SELECT acoes, nota FROM planos WHERE fp_objetivo=? ORDER BY nota DESC LIMIT 1",
            (fp_objetivo,)).fetchone()
        if r:
            return (r[0].split("|"), r[1])
        return None

    def buscar_delta(self, delta_str: str) -> Optional[str]:
        """Encontra acao que produz um determinado delta."""
        r = self.con.execute(
            "SELECT acao FROM causais WHERE delta=? ORDER BY timestamp DESC LIMIT 1",
            (delta_str,)).fetchone()
        return r[0] if r else None

    def restaurar_para(self, world, planner=None):
        """Restaura o estado do mundo a partir do banco."""
        # Restaura causais no MCRWorld
        causais = self.con.execute(
            "SELECT fp_antes, acao, fp_depois FROM causais ORDER BY timestamp DESC LIMIT 1000"
        ).fetchall()
        for fp_a, acao, fp_d in causais:
            world.mk_estado.aprender(fp_a, fp_d)
            world.mk_acao.aprender(f"{fp_a}:{acao}", fp_d)
        # Restaura planos
        if planner:
            planos = self.con.execute(
                "SELECT fp_objetivo, acoes, nota FROM planos ORDER BY nota DESC LIMIT 100"
            ).fetchall()
            for fp_obj, acoes_str, nota in planos:
                if nota >= 5.0:
                    planner.mk_plano.aprender(fp_obj, acoes_str)

    def estatisticas(self) -> Dict:
        c = self.con.cursor()
        return {
            "estados": c.execute("SELECT COUNT(*) FROM estados_mundo").fetchone()[0],
            "causais": c.execute("SELECT COUNT(*) FROM causais").fetchone()[0],
            "planos": c.execute("SELECT COUNT(*) FROM planos").fetchone()[0],
            "transicoes_byte": c.execute("SELECT COUNT(*) FROM transicoes_byte").fetchone()[0],
            "total_insercoes": self.total_insercoes,
        }

    def fechar(self):
        self.con.close()


class MCRIndex:
    """Indice de fingerprint para busca kNN rapida.
    
    Usa bucketing + re-ranking por cosseno.
    """
    def __init__(self, db: MCRMemory, dim: int = 8):
        self.db = db
        self.dim = dim
        self.num_buckets = 256
        self.cache: Dict[str, List[float]] = {}

    def indexar(self, texto: str, id_ref: str = ""):
        fp = MCRByteUtils.fingerprint(texto, self.dim)
        fp_str = str(fp)
        bucket = hash(fp_str) % self.num_buckets
        if id_ref:
            self.db.con.execute(
                "INSERT OR REPLACE INTO metadados (chave, valor) VALUES (?,?)",
                (f"idx:{id_ref}", fp_str))
            self.db.con.commit()
        self.cache[fp_str] = fp

    def buscar(self, fp_alvo: List[float], k: int = 10) -> List[Tuple[str, float]]:
        """k vizinhos mais proximos por similaridade de cosseno."""
        bucket = hash(str(fp_alvo)) % self.num_buckets
        candidatos = self.db.con.execute(
            "SELECT chave, valor FROM metadados WHERE chave LIKE 'idx:%'"
        ).fetchall()
        scored = []
        for chave, fp_str in candidatos:
            fp_outra = [float(x) for x in fp_str.strip("[]").split(",") if x.strip()]
            if len(fp_outra) != len(fp_alvo): continue
            sim = MCRByteUtils.similaridade_cosseno(fp_alvo, fp_outra)
            if sim > 0.1:
                scored.append((sim, chave.replace("idx:", "")))
        scored.sort(key=lambda x: -x[0])
        return [(nome, s) for s, nome in scored[:k]]

    def estatisticas(self) -> Dict:
        return {
            "dimensao": self.dim,
            "buckets": self.num_buckets,
            "cache": len(self.cache),
        }
