#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCRRegistry — Registro Universal de Tipos, Entidades e Conceitos
=================================================================
Zero listas fixas. Zero dicts hardcoded. Tudo registrado dinamicamente.
"""
import sys, os, random as _rand
from typing import Dict, List, Optional, Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_mcr_config import C


class MCRRegistry:
    """Registro universal. Qualquer entidade/tipo/conceito se registra aqui.
    
    Uso:
        MCRRegistry.registrar_tipo("terreno", {"grama": {"custo":1, "bloqueia":False}})
        MCRRegistry.registrar_nome("orc", "monstro")
        MCRRegistry.gerar_entidade("monstro", x=10, y=10)
    """
    
    _tipos: Dict[str, Dict] = {}
    _nomes: Dict[str, List[str]] = {}
    _conceitos: Dict[str, List[str]] = {}
    _entidades_instanciadas: List[str] = []
    
    @classmethod
    def registrar_tipo(cls, categoria: str, nome: str, props: Dict):
        """Registra um tipo de entidade."""
        cls._tipos.setdefault(categoria, {})[nome] = dict(props)
    
    @classmethod
    def registrar_nome(cls, nome: str, categoria: str = "geral"):
        """Registra um nome possivel para entidades."""
        cls._nomes.setdefault(categoria, []).append(nome)
    
    @classmethod
    def registrar_conceito(cls, conceito: str, categoria: str):
        """Registra um conceito textual para NLP."""
        cls._conceitos.setdefault(categoria, []).append(conceito)
    
    @classmethod
    def tipo_props(cls, categoria: str, nome: str) -> Dict:
        """Retorna props de um tipo."""
        return dict(cls._tipos.get(categoria, {}).get(nome, {}))
    
    @classmethod
    def tipos_por_categoria(cls, categoria: str) -> List[str]:
        """Lista tipos de uma categoria."""
        return list(cls._tipos.get(categoria, {}).keys())
    
    @classmethod
    def nome_aleatorio(cls, categoria: str = "geral") -> str:
        """Gera nome aleatorio de uma categoria."""
        nomes = cls._nomes.get(categoria, [])
        return _rand.choice(nomes) if nomes else f"{categoria}_{_rand.randint(0,999)}"
    
    @classmethod
    def registrar_nomes_padrao(cls):
        """Registra nomes padrao do projeto."""
        for nome in ["guerreiro", "mago", "arqueiro", "campones", "mercador",
                      "guardiao", "ferreiro", "alquimista", "bardo", "ladrao",
                      "elfo", "anao", "orc", "troll", "goblin",
                      "lobo", "urso", "aguia", "cervo", "jabali",
                      "Bruno", "Maria", "Joao", "Ana", "Carlos",
                      "Sofia", "Pedro", "Lucas", "Julia", "Rafael"]:
            cat = "monstro" if nome in ["orc","troll","goblin","lobo","urso","aguia","cervo","jabali"] else "npc"
            cls.registrar_nome(nome, cat)

    @classmethod
    def registrar_tipos_padrao(cls):
        """Registra tipos padrao (terreno, entidade, etc)."""
        # Terrenos
        for nome, props in [
            ("grama", {"custo": 1, "bloqueia": False}),
            ("agua", {"custo": 5, "bloqueia": True}),
            ("pedra", {"custo": 3, "bloqueia": False}),
            ("areia", {"custo": 2, "bloqueia": False}),
            ("muro", {"custo": 99, "bloqueia": True}),
            ("floresta", {"custo": 4, "bloqueia": False}),
            ("gelo", {"custo": 1, "bloqueia": False}),
            ("lava", {"custo": 10, "bloqueia": False}),
        ]:
            cls.registrar_tipo("terreno", nome, props)
        
        # Entidades
        cls.registrar_tipo("entidade", "heroi", {"hp": 10, "x": 0, "y": 0})
        cls.registrar_tipo("entidade", "monstro", {"hp": 5, "alcance": 1})
        cls.registrar_tipo("entidade", "npc", {"dialogo": True})
        cls.registrar_tipo("entidade", "objeto", {"interagivel": False})
        
        # Props especificas
        cls.registrar_tipo("item", "bau", {"aberto": False})
        cls.registrar_tipo("item", "pedra", {"gravidade": True})
    
    @classmethod
    def registrar_conceitos_padrao(cls):
        """Registra conceitos para NLP."""
        for c in ["SPA", "SHC", "sistema", "progressao", "habilidade", "lore"]:
            cls.registrar_conceito(c, "texto")
        for c in ["heroi", "grid", "andar", "bau", "monstro", "posicao"]:
            cls.registrar_conceito(c, "grid")
        for c in ["fibonacci", "sequencia", "numero", "potencia", "1 2 3"]:
            cls.registrar_conceito(c, "numerico")
    
    @classmethod
    def limpar(cls):
        """Limpa todo o registro."""
        cls._tipos.clear()
        cls._nomes.clear()
        cls._conceitos.clear()
        cls._entidades_instanciadas.clear()


_registrar = False
if not _registrar:
    MCRRegistry.registrar_nomes_padrao()
    MCRRegistry.registrar_tipos_padrao()
    MCRRegistry.registrar_conceitos_padrao()
    _registrar = True
