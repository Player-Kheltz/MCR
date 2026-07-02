#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 5: MCRBridge — Generalizacao Cross-Domain
================================================
Transfer learning entre dominios via fingerprints.
Analogia: "A esta para B assim como C esta para D".
"""
import sys, os, math
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import (
    MCR, MCRByteUtils, MCRSignatureExpansiva, MCRThreshold,
    EstadoMundo, MotorFisica, Entidade
)
from prototipo_mcr_config import C


class MCRBridge:
    """Ponte entre dominios: descobre analogias e transfere aprendizado.
    
    Como funciona:
      - Cada dominio tem seu proprio espaco de fingerprint
      - MCRBridge aprende mapeamentos entre espacos
      - Analogia: se delta(A1, A2) ≈ delta(B1, B2), entao a relacao
        entre A1 e A2 e a mesma que entre B1 e B2
    
    Dominios:
      - "grid": EstadoMundo (posicoes, hp, aberto/fechado)
      - "texto": strings narrativas
      - "byte": sequencias de bytes
      - "numerico": sequencias numericas (sequencias, padroes)
    """
    def __init__(self):
        self.mk_analogia = MCR("bridge_analogia")
        self.mk_delta = MCR("bridge_delta")
        self.dominios: Dict[str, MCR] = {}
        self.mapeamentos: Dict[str, Dict[str, float]] = {}
        self.threshold = MCRThreshold("bridge")
        self.dim = C("dim_fingerprint")
        self.total_analogias = 0

    def registrar_dominio(self, nome: str):
        """Registra um novo dominio."""
        if nome not in self.dominios:
            self.dominios[nome] = MCR(f"dominio_{nome}")
            self.mapeamentos[nome] = {}

    def fingerprint_dominio(self, texto: str, dominio: str) -> List[float]:
        """Calcula fingerprint de um texto no espaco de um dominio."""
        fp_base = MCRByteUtils.fingerprint(texto, self.dim)
        if dominio in self.dominios and self.dominios[dominio].total > 0:
            # Modula fingerprint pelo conhecimento do dominio
            chave = str(fp_base[:C("top_k")])
            mod, conf = self.dominios[dominio].predizer(chave)
            if mod and conf > C("conf_min"):
                mod_list = [float(x) for x in mod.strip("[]").split(",") if x.strip()]
                if len(mod_list) == self.dim:
                    return [
                        (fp_base[i] + mod_list[i]) / 2 for i in range(self.dim)
                    ]
        return fp_base

    def aprender_mapeamento(self, dominio_a: str, objeto_a: str,
                            dominio_b: str, objeto_b: str):
        """Aprende que objeto_a no dominio_a corresponde a objeto_b no dominio_b."""
        fp_a = self.fingerprint_dominio(objeto_a, dominio_a)
        fp_b = self.fingerprint_dominio(objeto_b, dominio_b)
        
        chave = f"MAP:{dominio_a}->{dominio_b}:{str(fp_a[:C("top_k")])}"
        self.dominios[dominio_a].aprender(chave, str(fp_b[:C("top_k")]))
        self.mapeamentos.setdefault(dominio_a, {})[dominio_b] = \
            1.0 - MCRByteUtils.similaridade_cosseno(fp_a, fp_b) if fp_a != fp_b else 0.5

    def transferir(self, texto: str, dominio_origem: str,
                   dominio_destino: str) -> str:
        """Transfere um texto do dominio_origem para o dominio_destino."""
        fp_origem = self.fingerprint_dominio(texto, dominio_origem)
        
        # Busca no destino o objeto mais similar
        chave = f"MAP:{dominio_origem}->{dominio_destino}:{str(fp_origem[:C("top_k")])}"
        fp_destino_str, conf = self.dominios[dominio_origem].predizer(chave)
        
        if fp_destino_str and conf > C("conf_media"):
            fp_destino = [float(x) for x in fp_destino_str.strip("[]").split(",") if x.strip()]
            return f"[Transferido] fp_origem={fp_origem[:C("top_k")]} fp_destino={fp_destino[:C("top_k")]} conf={conf:.2f}"
        
        return f"[Sem mapeamento] {texto[:30]}... ({dominio_origem} -> {dominio_destino})"

    def analogia(self, a1: str, a2: str, b1: str, b2: str) -> Dict:
        """'A1 esta para A2 assim como B1 esta para B2'?
        
        Descobre se a relacao entre A1 e A2 e analoga a relacao entre B1 e B2.
        """
        delta_a = MCRByteUtils.delta_fingerprint(a1, a2, self.dim)
        delta_b = MCRByteUtils.delta_fingerprint(b1, b2, self.dim)
        
        # Similaridade entre os deltas
        sim_delta = MCRByteUtils.similaridade_cosseno(delta_a, delta_b)
        
        # Forca da analogia
        mag_a = math.sqrt(sum(d * d for d in delta_a))
        mag_b = math.sqrt(sum(d * d for d in delta_b))
        razao_mag = min(mag_a, mag_b) / max(mag_a, mag_b, 0.001)
        
        nota_analogia = sim_delta * razao_mag
        
        self.total_analogias += 1
        self.mk_analogia.aprender(
            f"ANALOGIA:{sim_delta:.2f}",
            f"nota:{nota_analogia:.2f}"
        )
        
        return {
            "a1": a1[:30], "a2": a2[:30],
            "b1": b1[:30], "b2": b2[:30],
            "sim_delta": round(sim_delta, 3),
            "razao_mag": round(razao_mag, 3),
            "nota": round(nota_analogia, 3),
            "analogo": nota_analogia > C("bridge_nota_analogia"),
        }

    def analogia_estado(self, e1: EstadoMundo, e2: EstadoMundo,
                        e3: EstadoMundo, e4: EstadoMundo) -> Dict:
        """Analogia entre estados do mundo."""
        return self.analogia(
            e1.serializar(), e2.serializar(),
            e3.serializar(), e4.serializar()
        )

    def aprender_de_experiencia(self, dominio: str, experiencias: List[Tuple[str, str, float]]):
        """Aprende mapeamentos a partir de experiencias (entrada, saida, similaridade)."""
        for entrada, saida, sim in experiencias:
            self.dominios[dominio].aprender(
                f"EXP:{entrada[:30]}", f"{saida[:30]}:{sim:.2f}"
            )
            self.threshold.observar(sim)

    def stats(self) -> Dict:
        return {
            "dominios": list(self.dominios.keys()),
            "analogias": self.total_analogias,
            "mapeamentos": sum(len(m) for m in self.mapeamentos.values()),
            "transicoes": sum(m.total for m in self.dominios.values()),
        }

    def __repr__(self):
        s = self.stats()
        return f"MCRBridge: {s['dominios']}, {s['analogias']} analogias, {s['mapeamentos']} mapeamentos"


class MCRCrossDomain:
    """Aprendizado cross-domain: usa MCRBridge para transferir entre dominios.
    
    Se o MCR aprende "andar_dir" no grid, pode reconhecer
    "caminhar para leste" no dominio de texto.
    """
    def __init__(self, bridge: MCRBridge = None):
        self.bridge = bridge or MCRBridge()
        self.mk = MCR("crossdomain")
        self.historico: List[Dict] = []

    def dominio_de_texto(self, texto: str) -> str:
        """Descobre o dominio de um texto pela sua assinatura."""
        h = MCRByteUtils.entropia_bytes(texto)
        fp = MCRByteUtils.fingerprint(texto, 4)
        if h < 1.0 and any(c.isdigit() for c in texto):
            return "numerico"
        elif "heroi" in texto or "bau" in texto or "monstro" in texto:
            return "grid"
        return "texto"

    def traduzir_acao(self, acao_grid: str, contexto: str = "") -> str:
        """Traduz uma acao do grid para descricao textual."""
        mapa = {
            "andar_cima": "subir",
            "andar_baixo": "descer",
            "andar_esq": "ir para oeste",
            "andar_dir": "ir para leste",
            "atacar": "atacar",
            "abrir": "abrir",
            "empurrar": "empurrar",
        }
        return mapa.get(acao_grid, acao_grid)

    def entender_instrucao(self, instrucao: str) -> List[str]:
        """Converte instrucao textual em acoes do grid.
        Retorna lista vazia se nenhuma acao for reconhecida."""
        instrucao = instrucao.lower()
        acoes = []
        if "atacar" in instrucao or "ataque" in instrucao:
            acoes.append("atacar")
        if "abrir" in instrucao:
            acoes.append("abrir")
        if "leste" in instrucao or "direita" in instrucao:
            acoes.append("andar_dir")
        if "oeste" in instrucao or "esquerda" in instrucao:
            acoes.append("andar_esq")
        if "subir" in instrucao or "norte" in instrucao or "cima" in instrucao:
            acoes.append("andar_cima")
        if "descer" in instrucao or "sul" in instrucao or "baixo" in instrucao:
            acoes.append("andar_baixo")
        if "empurrar" in instrucao:
            acoes.append("empurrar")
        return acoes

    def stats(self) -> Dict:
        return {
            "dominios_conhecidos": list(self.bridge.dominios.keys()),
            "traducoes": len(self.mk.freq),
            "historico": len(self.historico),
        }
