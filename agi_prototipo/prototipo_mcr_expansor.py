#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCRExpansor — Orquestrador OMNI: expande, equacao, constroi
=============================================================
Nao busca. Nao filtra. Nao decide.
So chama TUDO que esta registrado, junta TUDO,
deixa a Equacao MCR decidir, e constroi expandindo de novo.

Uso:
    MCRExpansor.registrar("nome", fn_buscar)
    MCRExpansor.responder("quanto custa o worm")
"""
import sys, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_mcr_config import C


class MCRExpansor:
    """Orquestrador OMNI: expande → equacao → constroi.
    
    Zero lista fixa de extratores. Zero if/elif.
    Qualquer modulo se registra como extrator ou construtor.
    
    Fluxo:
      1. expandir(pergunta) → chama TODOS os extratores em paralelo
      2. equacao(pergunta, resultados) → fingerprint vs assinatura
      3. construir(pergunta, melhores) → constroi resposta expandindo
    """
    
    _extratores: Dict[str, Dict] = {}
    _construtores: Dict[str, Callable] = {}
    
    # ─── REGISTRO UNIVERSAL ──────────────────────────────
    
    @classmethod
    def registrar(cls, nome: str, fn_buscar: Callable,
                  descricao: str = ""):
        """Registra um extrator.
        
        fn_buscar recebe (pergunta: str) e retorna List[Dict]:
            [{"assinatura": str, "meta": dict}, ...]
        
        Qualquer modulo em qualquer arquivo pode chamar isto.
        """
        cls._extratores[nome] = {"buscar": fn_buscar, "desc": descricao}
    
    @classmethod
    def registrar_construtor(cls, nome: str, fn_construir: Callable):
        """Registra um construtor de resposta.
        
        fn_construir recebe (contexto: str, assinatura: dict)
        e retorna str (trecho da resposta).
        """
        cls._construtores[nome] = fn_construir
    
    # ─── FASE 1: EXPANSAO ───────────────────────────────
    
    @classmethod
    def expandir(cls, pergunta: str) -> List[Dict]:
        """Chama TODOS os extratores registrados EM PARALELO.
        
        Junta TUDO. Zero filtro. Zero perda de informacao.
        Cada resultado tem: assinatura, fonte, meta.
        """
        if not cls._extratores:
            return []
        
        resultados = []
        with ThreadPoolExecutor(max_workers=len(cls._extratores)) as ex:
            futures = {
                ex.submit(ext["buscar"], pergunta): nome
                for nome, ext in cls._extratores.items()
            }
            for f in as_completed(futures):
                nome = futures[f]
                try:
                    dados = f.result()
                    if not dados:
                        continue
                    for d in dados:
                        if isinstance(d, dict) and "assinatura" in d:
                            d["fonte"] = nome
                            resultados.append(d)
                        elif isinstance(d, str):
                            resultados.append({
                                "assinatura": d, "fonte": nome, "meta": {}
                            })
                except Exception as e:
                    resultados.append({
                        "assinatura": "", "fonte": nome,
                        "meta": {"erro": str(e)[:60]}, "erro": True
                    })
        
        return resultados
    
    # ─── FASE 2: EQUACAO ────────────────────────────────
    
    @classmethod
    def equacao(cls, pergunta: str, resultados: List[Dict]) -> List[Dict]:
        """Aplica a Equacao MCR em cada resultado.
        
        NOTA = similaridade_cosseno(
            fingerprint(pergunta), fingerprint(assinatura)
        )
        
        0 pesos. 0 if/elif. So a Equacao.
        """
        from prototipo_agi_completo import MCRByteUtils
        
        fp_pergunta = MCRByteUtils.fingerprint(pergunta, C("dim_fingerprint"))
        
        for r in resultados:
            if not r.get("assinatura"):
                r["nota"] = 0.0
                continue
            fp_ass = MCRByteUtils.fingerprint(r["assinatura"], C("dim_fingerprint"))
            r["nota"] = MCRByteUtils.similaridade_cosseno(fp_pergunta, fp_ass)
        
        return sorted(resultados, key=lambda x: -x.get("nota", 0))
    
    # ─── FASE 3: CONSTRUCAO ─────────────────────────────
    
    @classmethod
    def construir(cls, pergunta: str, melhores: List[Dict]) -> str:
        """Constroi a resposta expandindo cada assinatura.
        
        Para cada resultado, chama os construtores registrados.
        Cada construtor recebe (contexto, assinatura) e retorna texto.
        """
        if not melhores:
            return "Nada encontrado."
        
        top_k = max(1, int(C("top_k")))
        contexto = pergunta
        partes = []
        
        for r in melhores[:top_k]:
            if r.get("erro"):
                continue
            if not r.get("assinatura"):
                continue
            
            # Expande com construtores registrados
            for nome, fn in cls._construtores.items():
                try:
                    expansao = fn(contexto, r)
                    if expansao and len(str(expansao).strip()) > 0:
                        partes.append(str(expansao).strip())
                except Exception:
                    pass
        
        if not partes and melhores and melhores[0].get("assinatura"):
            m = melhores[0]
            return f"{m['assinatura']} (fonte: {m.get('fonte', '?')})"
        
        return "\n".join(partes) if partes else "Nada encontrado."
    
    # ─── FLUXO COMPLETO ─────────────────────────────────
    
    @classmethod
    def responder(cls, pergunta: str) -> str:
        """Fluxo OMNI completo."""
        
        if not pergunta:
            return ""
        
        # FASE 1: EXPANDE em TODAS as fontes
        todos = cls.expandir(pergunta)
        
        # FASE 2: EQUACAO MCR pontua cada assinatura
        rankeados = cls.equacao(pergunta, todos)
        
        # FASE 3: CONSTROI resposta expandindo as melhores
        resposta = cls.construir(pergunta, rankeados)
        
        return resposta
    
    # ─── UTILITARIOS ─────────────────────────────────────
    
    @classmethod
    def nomes_extratores(cls) -> List[str]:
        return list(cls._extratores.keys())
    
    @classmethod
    def nomes_construtores(cls) -> List[str]:
        return list(cls._construtores.keys())
    
    @classmethod
    def stats(cls) -> dict:
        return {
            "extratores": len(cls._extratores),
            "construtores": len(cls._construtores),
            "nomes_extratores": cls.nomes_extratores(),
        }
