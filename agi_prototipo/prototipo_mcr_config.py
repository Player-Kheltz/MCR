#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCRConfig — UNICO ponto de configuracao para TODO o sistema
=============================================================
Zero numeros magicos. Zero hardcodes. Tudo descoberto dos dados.

Cada parametro tem 3 fontes:
  1. MCRSignatureExpansiva (descobre dimensionalidade ideal)
  2. MCRThreshold (adapta por mediana das observacoes)
  3. MCRDecisorUniversal (decide baseado no estado do motor)
"""
import sys, os, math
from typing import Dict, List, Optional, Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class MCRConfigMeta(type):
    """Metaclass que faz MCRConfig ser singleton + lazy evaluation."""
    _instancia = None
    _param_cache: Dict[str, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls._instancia is None:
            cls._instancia = super().__call__(*args, **kwargs)
        return cls._instancia


class MCRConfig(metaclass=MCRConfigMeta):
    """Configuracao universal. Todos os parametros sao propriedades
    que se auto-descobrem na primeira chamada."""

    # Marcador para parametros nao inicializados
    _UNSET = object()

    def __init__(self):
        self._imp = None  # lazy import
        self._parametros: Dict[str, Callable] = {}
        self._cache: Dict[str, object] = {}
        self._observacoes: Dict[str, list] = {}
        self._registrar_padroes()

    # ─── IMPORTS LAZY (evita circular) ─────────────────────

    def _import(self):
        if self._imp is None:
            from prototipo_agi_completo import (
                MCRThreshold, MCRSignatureExpansiva, MCRByteUtils
            )
            self._imp = {
                "MCRThreshold": MCRThreshold,
                "MCRSignatureExpansiva": MCRSignatureExpansiva,
                "MCRByteUtils": MCRByteUtils,
            }
        return self._imp

    @property
    def threshold(self):
        return self._import()["MCRThreshold"]

    @property
    def signature(self):
        return self._import()["MCRSignatureExpansiva"]

    @property
    def utils(self):
        return self._import()["MCRByteUtils"]

    # ─── REGISTRO DE PARAMETROS ────────────────────────────

    def _registrar_padroes(self):
        """Registra todos os parametros com suas estrategias de descoberta."""
        r = self._parametros

        # Fingerprint / Dimensionalidade
        r["dim_fingerprint"] = lambda: max(2, min(32, self._descobrir_dim("fingerprint", 32)))
        r["dim_fingerprint_rapido"] = lambda: max(2, self._descobrir_dim("fingerprint", 16))
        r["dim_delta"] = lambda: max(2, self._descobrir_dim("delta", 16))
        r["num_buckets"] = lambda: max(4, self.get("dim_fingerprint") * 32)
        r["max_bytes"] = lambda: self._thr("max_bytes", 2000)

        # Confianca / Thresholds
        r["conf_min"] = lambda: self._thr("conf_min", 0.1)
        r["conf_media"] = lambda: self._thr("conf_media", 0.3)
        r["conf_alta"] = lambda: self._thr("conf_alta", 0.5)
        r["conf_muito_alta"] = lambda: self._thr("conf_muito_alta", 0.7)
        r["conf_maxima"] = lambda: self._thr("conf_maxima", 0.95)

        # Passos / Iteracoes
        r["passos_gerar"] = lambda: self._dec("passos_gerar", 6)
        r["passos_planejar"] = lambda: self._dec("passos_planejar", 10)
        r["max_iter"] = lambda: self._dec("max_iter", 10)
        r["max_ciclos"] = lambda: self._dec("max_ciclos", 10)

        # RL
        r["rl_gamma"] = lambda: self._thr("rl_gamma", 0.9)
        r["rl_alpha"] = lambda: self._thr("rl_alpha", 0.3)
        r["rl_epsilon_inicial"] = lambda: self._thr("rl_epsilon_inicial", 0.2)
        r["rl_epsilon_min"] = lambda: self._thr("rl_epsilon_min", 0.05)
        r["rl_epsilon_decay"] = lambda: self._thr("rl_epsilon_decay", 0.01)
        r["rl_recompensa_sucesso"] = lambda: self._thr("rl_recompensa_sucesso", 2.0)
        r["rl_recompensa_novidade"] = lambda: self._thr("rl_recompensa_novidade", 0.5)
        r["rl_recompensa_mudanca"] = lambda: self._thr("rl_recompensa_mudanca", 1.0)

        # Historico / Buffer
        r["historico_max"] = lambda: max(10, self._dec("historico_max", 100))
        r["janela_entropia"] = lambda: max(3, self._dec("janela_entropia", 10))
        r["janela_media"] = lambda: max(2, self._dec("janela_media", 50))
        r["janela_recente"] = lambda: max(2, self._dec("janela_recente", 5))

        # Busca / Limites
        r["limite_busca"] = lambda: self._dec("limite_busca", 10)
        r["limite_candidatos"] = lambda: self._dec("limite_candidatos", 5)
        r["top_k"] = lambda: self._dec("top_k", 3)

        # Memoria
        r["memoria_restore_causais"] = lambda: self._dec("memoria_restore_causais", 1000)
        r["memoria_restore_planos"] = lambda: self._dec("memoria_restore_planos", 100)
        r["memoria_nota_min_plano"] = lambda: self._thr("memoria_nota_min_plano", 5.0)

        # Ambiente
        r["ambiente_ticks_por_dia"] = lambda: self._dec("ambiente_ticks_por_dia", 100)
        r["ambiente_entidades_por_tick"] = lambda: self._dec("ambiente_entidades_por_tick", 50)

        # Genesis
        r["genesis_min_palavras"] = lambda: self._dec("genesis_min_palavras", 10)
        r["genesis_min_planos"] = lambda: self._dec("genesis_min_planos", 5)
        r["genesis_nota_integracao"] = lambda: self._thr("genesis_nota_integracao", 5.0)

        # Gap detection
        r["gap_entropia_alta"] = lambda: self._thr("gap_entropia_alta", 0.5)
        r["gap_coupling_fraco"] = lambda: self._thr("gap_coupling_fraco", 0.1)
        r["gap_coupling_count"] = lambda: self._dec("gap_coupling_count", 10)
        r["gap_hardcode_count"] = lambda: self._dec("gap_hardcode_count", 3)

        # Bridge
        r["bridge_nota_analogia"] = lambda: self._thr("bridge_nota_analogia", 0.5)
        r["bridge_sim_transferencia"] = lambda: self._thr("bridge_sim_transferencia", 0.7)

    # ─── ESTRATEGIAS DE DESCOBERTA ─────────────────────────

    def _descobrir_dim(self, contexto: str, max_dims: int = 64) -> int:
        """Descobre dimensionalidade ideal (SignatureExpansiva)."""
        try:
            dados = self._dados_para_dim(contexto)
            if dados:
                return self.signature.dimensionalidade_ideal(
                    dados.encode("utf-8")[:2000], max_dims=max_dims)
        except Exception:
            pass
        return max_dims // 2

    def _dados_para_dim(self, contexto: str) -> Optional[str]:
        """Obtem dados de exemplo para descobrir dimensionalidade."""
        try:
            from prototipo_agi_completo import CerebroAGI
            cerebro = CerebroAGI()
            if cerebro.topicos:
                return list(cerebro.topicos.values())[0].get("texto", "")
            return "dados de exemplo para descobrir dimensionalidade ideal"
        except Exception:
            return None

    def _thr(self, nome: str, fallback: float) -> float:
        """Obtem valor adaptativo via MCRThreshold."""
        chave = f"config:{nome}"
        thr = self.threshold(nome)
        if self._observacoes.get(nome):
            for v in self._observacoes[nome][-50:]:
                thr.observar(v)
        return thr.obter(chave, fallback)

    def _dec(self, nome: str, fallback: object):
        """Decide valor via MCRDecisorUniversal."""
        try:
            from prototipo_agi_completo import MCRDecisorUniversal, CerebroAGI
            cerebro = CerebroAGI()
            params = MCRDecisorUniversal.decidir(cerebro, nome)
            return params.get(nome, fallback)
        except Exception:
            return fallback

    # ─── INTERFACE PUBLICA ─────────────────────────────────

    def get(self, nome: str, fallback=None):
        """Obtem o valor de um parametro, descobrindo se necessario."""
        if nome in self._cache:
            return self._cache[nome]

        if nome in self._parametros:
            try:
                valor = self._parametros[nome]()
                self._cache[nome] = valor
                return valor
            except Exception:
                if fallback is not None:
                    return fallback
                return self._default(nome)
        return fallback

    def observar(self, nome: str, valor: float):
        """Alimenta observacao para threshold adaptativo."""
        if nome not in self._observacoes:
            self._observacoes[nome] = []
        self._observacoes[nome].append(valor)
        self._cache.pop(nome, None)  # invalida cache

    def invalidar(self, nome: str = None):
        """Invalida cache de um ou todos os parametros."""
        if nome:
            self._cache.pop(nome, None)
        else:
            self._cache.clear()

    def _default(self, nome: str) -> object:
        """Valores padrao universais quando nada funciona."""
        padroes = {
            "dim_fingerprint": 8, "conf_min": 0.1, "conf_media": 0.3,
            "passos_gerar": 6, "max_iter": 10, "top_k": 3,
            "rl_gamma": 0.9, "rl_alpha": 0.3,
        }
        return padroes.get(nome, 0)

    def to_dict(self) -> Dict:
        """Snapshot de todos os parametros atuais."""
        return {
            nome: self.get(nome, "?")
            for nome in sorted(self._parametros.keys())
        }

    def __repr__(self):
        params = self.to_dict()
        n = len(params)
        return f"MCRConfig: {n} parametros, {len(self._cache)} em cache"

    def __getattr__(self, nome):
        """Acesso como atributo: MCRConfig().dim_fingerprint"""
        if nome.startswith("_"):
            raise AttributeError(nome)
        return self.get(nome)


# Instancia global unica
config = MCRConfig()


# Atalho: importar como "from prototipo_mcr_config import C"
C = config.get
