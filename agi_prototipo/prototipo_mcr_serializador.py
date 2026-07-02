#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCRSerializador — Serializacao Universal de Entidades
======================================================
Zero formatos especificos. Zero if/elif por tipo.
Serializa QUALQUER entidade de QUALQUER tipo.
"""
import sys, os
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_mcr_config import C


class MCRSerializador:
    """Serializa e desserializa entidades de forma universal.
    
    Formato: nome:tipo:prop=val;prop=val|nome2:tipo2:...
    """
    
    SEP_ENTIDADE = "|"
    SEP_PROPS = ";"
    SEP_CHAVE_VALOR = "="
    SEP_NOME_TIPO = ":"
    
    @classmethod
    def serializar(cls, entidades: Dict) -> str:
        """Serializa dict de entidades para string."""
        partes = []
        for nome in sorted(entidades.keys()):
            ent = entidades[nome]
            props_str = cls.SEP_PROPS.join(
                f"{k}{cls.SEP_CHAVE_VALOR}{v}" 
                for k, v in sorted(ent.props.items())
            )
            partes.append(f"{ent.nome}{cls.SEP_NOME_TIPO}{ent.tipo}{cls.SEP_NOME_TIPO}{props_str}")
        return cls.SEP_ENTIDADE.join(partes)
    
    @classmethod
    def serializar_bytes(cls, entidades: Dict) -> bytes:
        """Serializa para bytes (mais rapido que string)."""
        return cls.serializar(entidades).encode("utf-8")
    
    @classmethod
    def desserializar(cls, texto: str) -> Dict:
        """Converte string de volta para dict de entidades."""
        from prototipo_agi_completo import Entidade
        entidades = {}
        if not texto:
            return entidades
        
        for parte in texto.split(cls.SEP_ENTIDADE):
            if not parte:
                continue
            partes_nome = parte.split(cls.SEP_NOME_TIPO, 2)
            if len(partes_nome) < 3:
                continue
            nome, tipo, props_str = partes_nome
            props = {}
            if props_str:
                for p in props_str.split(cls.SEP_PROPS):
                    if cls.SEP_CHAVE_VALOR in p:
                        k, v = p.split(cls.SEP_CHAVE_VALOR, 1)
                        try:
                            v = int(v)
                        except ValueError:
                            try:
                                v = float(v)
                            except ValueError:
                                if v == "True": v = True
                                elif v == "False": v = False
                        props[k] = v
            entidades[nome] = Entidade(nome, tipo, props)
        
        return entidades
    
    @classmethod
    def fingerprint_de_entidades(cls, entidades: Dict, dim: int = None) -> List[float]:
        """Calcula fingerprint de um conjunto de entidades."""
        from prototipo_agi_completo import MCRByteUtils
        dim = dim if dim is not None else C("dim_fingerprint")
        return MCRByteUtils.fingerprint(cls.serializar(entidades), dim)
    
    @classmethod
    def fingerprint_bytes(cls, dados: bytes, dim: int = None) -> List[float]:
        """Fingerprint direto de bytes."""
        from prototipo_agi_completo import MCRSignatureExpansiva
        dim = dim if dim is not None else C("dim_fingerprint")
        return MCRSignatureExpansiva.fingerprint(dados, dim)
