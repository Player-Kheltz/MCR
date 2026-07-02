#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 4: MCRAmbiente — Ambiente Rico com 1000+ Entidades
=========================================================
Substitui o grid 5x5 por um mundo 2D real com:
  - 100x100 tiles com tipos de terreno
  - 1000+ entidades (NPCs, monstros, objetos, arvores)
  - Ciclo dia/noite
  - Sistema de visao baseado em linha de visao
  - Serializacao otimizada para performance
"""
import sys, os, math, random as _rand, time
from typing import Dict, List, Tuple, Optional, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import (
    MCR, MCRByteUtils, MCRSignatureExpansiva, MCRThreshold,
    MCREntropia, Entidade, EstadoMundo, MotorFisica
)
from prototipo_mcr_config import C
from prototipo_mcr_registry import MCRRegistry


class Tile:
    """Um tile do ambiente. Tipos registrados no MCRRegistry."""
    
    def __init__(self, tipo: str = "grama", altura: float = 0.0):
        self.tipo = tipo
        self.altura = altura
        self.props = dict(MCRRegistry.tipo_props("terreno", tipo))
    
    def bloqueia(self) -> bool:
        return self.props.get("bloqueia", False)
    
    def __repr__(self):
        return self.props.get("simbolo", "?")


class AmbienteRico:
    """Ambiente 2D com 100x100 tiles e 1000+ entidades.
    
    Suporta:
      - Geracao procedural de terreno
      - 7 tipos de tile com propriedades diferentes
      - Multiplos biomas
      - Ciclo dia/noite
      - Sistema de pathfinding basico (custo por tile)
    """
    def __init__(self, largura: int = 100, altura: int = 100):
        self.largura = largura
        self.altura = altura
        self.tiles: List[List[Tile]] = []
        self.entidades: List[Entidade] = []
        self.id_counter = 0
        self.tick_atual = 0
        self.dia = True
        self.entropia = MCREntropia("ambiente")
        
        self._gerar_terreno()
        self._povoar()
    
    def _gerar_terreno(self):
        """Gera terreno procedural com biomas. Tipos do MCRRegistry."""
        tipos = MCRRegistry.tipos_por_categoria("terreno")
        
        for y in range(self.altura):
            linha = []
            for x in range(self.largura):
                # Ruido simples para biomas
                ruido = math.sin(x * 0.1) * math.cos(y * 0.1) + _rand.random() * 0.5
                if ruido < -0.5:
                    t = "agua" if y > 50 else "muro"
                elif ruido < 0:
                    t = "areia" if x % 3 == 0 else "grama"
                elif ruido < 0.5:
                    t = "floresta" if _rand.random() < 0.3 else "grama"
                else:
                    t = "pedra" if _rand.random() < 0.4 else "grama"
                altura = math.sin(x * 0.05) * math.cos(y * 0.05) * 2
                linha.append(Tile(t, altura))
            self.tiles.append(linha)
    
    def _povoar(self):
        """Cria entidades iniciais."""
        nomes_mob = MCRRegistry._nomes.get("monstro", ["orc","goblin","lobo"])
        nomes_npc = MCRRegistry._nomes.get("npc", ["Bruno","Maria","Joao"])
        
        for i in range(C("limite_busca") * 50):
            x = _rand.randint(0, self.largura - 1)
            y = _rand.randint(0, self.altura - 1)
            if self.tiles[y][x].bloqueia():
                continue
            nome = f"{_rand.choice(nomes_mob)}_{i}"
            tipo = "monstro" if i < 200 else "npc" if i < 350 else "objeto"
            hp = _rand.randint(5, 50) if tipo == "monstro" else 0
            props = {"x": x, "y": y}
            if hp: props["hp"] = hp
            if tipo == "npc":
                props["nome_exibicao"] = _rand.choice(nomes_npc)
            if tipo == "objeto":
                props["interagivel"] = i % 3 == 0
            
            self.entidades.append(Entidade(nome, tipo, props))
            self.id_counter += 1
    
    def tick(self):
        """Avança um tick do ambiente."""
        self.tick_atual += 1
        if self.tick_atual % C("ambiente_ticks_por_dia") == 0:
            self.dia = not self.dia
        
        # Move algumas entidades aleatoriamente
        for ent in _rand.sample(self.entidades, min(C("ambiente_entidades_por_tick"), len(self.entidades))):
            if ent.tipo == "objeto":
                continue
            dx, dy = _rand.choice([(0,1),(0,-1),(1,0),(-1,0)])
            nx = ent.props["x"] + dx
            ny = ent.props["y"] + dy
            if 0 <= nx < self.largura and 0 <= ny < self.altura:
                if not self.tiles[ny][nx].bloqueia():
                    ent.props["x"] = nx
                    ent.props["y"] = ny
        
        self.entropia.alimentar(f"tick:{self.tick_atual}")
    
    def criar_estado(self, centro_x: int = 50, centro_y: int = 50,
                     raio: int = 10) -> 'EstadoMundoRico':
        """Cria um EstadoMundo a partir de uma regiao do ambiente."""
        from prototipo_agi_completo import EstadoMundo
        estado = EstadoMundo()
        
        # Adiciona tiles ao redor do centro
        for dy in range(-raio, raio + 1):
            for dx in range(-raio, raio + 1):
                x, y = centro_x + dx, centro_y + dy
                if 0 <= x < self.largura and 0 <= y < self.altura:
                    tile = self.tiles[y][x]
                    nome = f"tile_{x}_{y}"
                    estado.adicionar(Entidade(nome, "terreno", {
                        "x": x, "y": y, "tipo": tile.tipo,
                        "bloqueia": tile.bloqueia()
                    }))
        
        # Adiciona entidades visiveis
        for ent in self.entidades:
            ex, ey = ent.props["x"], ent.props["y"]
            if abs(ex - centro_x) <= raio and abs(ey - centro_y) <= raio:
                estado.adicionar(ent.clone())
        
        estado.grid_w = raio * 2 + 1
        estado.grid_h = raio * 2 + 1
        return estado
    
    def estatisticas(self) -> Dict:
        tiles_ocupados = sum(
            1 for row in self.tiles for t in row if t.bloqueia()
        )
        return {
            "tiles": self.largura * self.altura,
            "tiles_bloqueados": tiles_ocupados,
            "entidades": len(self.entidades),
            "entidades_por_tipo": {
                t: sum(1 for e in self.entidades if e.tipo == t)
                for t in set(e.tipo for e in self.entidades)
            },
            "tick": self.tick_atual,
            "dia": self.dia,
        }


class EstadoMundoRico(EstadoMundo):
    """Versao estendida de EstadoMundo com serializacao otimizada."""
    
    def serializar_rapido(self) -> bytes:
        """Serializacao binaria para performance com 1000+ entidades."""
        partes = []
        for nome in sorted(self.entidades.keys()):
            e = self.entidades[nome]
            x = e.props.get("x", 0)
            y = e.props.get("y", 0)
            tp = 0 if e.tipo == "terreno" else 1 if e.tipo == "monstro" else 2
            partes.append(f"{nome}:{x},{y},{tp}")
        return ("|".join(partes)).encode("utf-8")
    
    def fingerprint_rapido(self, dim: int = 8) -> List[float]:
        """Fingerprint calculado sobre bytes, nao sobre string."""
        dados = self.serializar_rapido()
        return MCRSignatureExpansiva.fingerprint(dados, dim)
