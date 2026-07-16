#!/usr/bin/env python3
"""planejador.py — Gerador hierarquico de scripts Lua do Canary.
Niveis: M2 (marcos) → M3 (secoes) → M4 (tokens).
Gera codigo Lua valido para NPCs, sem LLM."""
import random
import re
from collections import Counter
from typing import List, Dict, Optional

# ─── Dados extraidos do corpus (1069 scripts) ────────────

# Template de marcos (M2)
MARCOS = [
    'cabecalho', 'npc_type_def', 'config_init',
    'config_field', 'config_outfit', 'config_flags',
    'handler_init', 'npc_handler',
    'callback',   # repetivel
    'keyword',    # repetivel
    'module',     # repetivel
    'register',
]

# Distribuicoes de cardinalidade (percentuais acumulados)
CARD_CONFIG_FIELDS = [(6, 55.1), (7, 34.7), (8, 9.5), (9, 0.4)]
CARD_CALLBACKS = [(6, 63.5), (9, 26.8), (5, 2.8), (0, 4.2)]
CARD_KEYWORDS = [(0, 65.8), (1, 5.8), (2, 5.7), (3, 2.4), (4, 2.0)]
CARD_MODULES = [(1, 94.7), (0, 5.3)]

# Campos de config (M3)
CONFIG_BASE = [
    ('npcConfig.name', lambda ctx: f'npcConfig.name = "{ctx["nome"]}"'),
    ('npcConfig.description', lambda ctx: f'npcConfig.description = "{ctx["nome"]}"'),
    ('npcConfig.health', lambda ctx: f'npcConfig.health = {ctx["health"]}'),
    ('npcConfig.maxHealth', lambda ctx: f'npcConfig.maxHealth = npcConfig.health'),
    ('npcConfig.walkInterval', lambda ctx: f'npcConfig.walkInterval = {ctx["walk_interval"]}'),
    ('npcConfig.walkRadius', lambda ctx: f'npcConfig.walkRadius = {ctx["walk_radius"]}'),
]

CONFIG_OPCIONAIS = [
    ('shop', 0.30, lambda ctx: 'npcConfig.shop = {\n\t\t{ item = {"key", "value"}, sell = 0, buy = 0 },\n\t}'),
    ('voices', 0.239, lambda ctx: f'npcConfig.voices = {{\n\t\tinterval = 15000,\n\t\tchance = 20,\n\t\t{{ text = "Bem-vindo a {ctx["nome"]}." }},\n\t}}'),
]

# Outfit default (amostrado de valores comuns do corpus)
OUTFITS = [
    {'lookType': 73, 'lookHead': 0, 'lookBody': 0, 'lookLegs': 0, 'lookFeet': 0, 'lookAddons': 0},
    {'lookType': 132, 'lookHead': 19, 'lookBody': 113, 'lookLegs': 112, 'lookFeet': 114, 'lookAddons': 0},
    {'lookType': 294, 'lookHead': 0, 'lookBody': 0, 'lookLegs': 0, 'lookFeet': 0, 'lookAddons': 0},
    {'lookType': 20, 'lookHead': 0, 'lookBody': 0, 'lookLegs': 0, 'lookFeet': 0, 'lookAddons': 0},
    {'lookType': 128, 'lookHead': 86, 'lookBody': 120, 'lookLegs': 117, 'lookFeet': 115, 'lookAddons': 0},
    {'lookType': 2, 'lookHead': 0, 'lookBody': 0, 'lookLegs': 0, 'lookFeet': 0, 'lookAddons': 0},
]

# Callbacks base (M3)
CALLBACKS_BASE = [
    'npcType.onThink = function(npc, interval)\n\tnpcHandler:onThink(npc, interval)\nend',
    'npcType.onAppear = function(npc, creature)\n\tnpcHandler:onAppear(npc, creature)\nend',
    'npcType.onDisappear = function(npc, creature)\n\tnpcHandler:onDisappear(npc, creature)\nend',
    'npcType.onMove = function(npc, creature, fromPosition, toPosition)\n\tnpcHandler:onMove(npc, creature, fromPosition, toPosition)\nend',
    'npcType.onSay = function(npc, creature, type, message)\n\tnpcHandler:onSay(npc, creature, type, message)\nend',
    'npcType.onCloseChannel = function(npc, creature)\n\tnpcHandler:onCloseChannel(npc, creature)\nend',
]

CALLBACKS_SHOP = [
    'npcType.onBuyItem = function(npc, player, itemId, subType, amount, ignore, inBackpacks)\n\tnpcHandler:onBuyItem(npc, player, itemId, subType, amount, ignore, inBackpacks)\nend',
    'npcType.onSellItem = function(npc, player, itemId, subtype, amount, ignore, name, totalCost)\n\tnpcHandler:onSellItem(npc, player, itemId, subtype, amount, ignore, name, totalCost)\nend',
    'npcType.onCheckItem = function(npc, player, clientId, subType)\n\tnpcHandler:onCheckItem(npc, player, clientId, subType)\nend',
]

# Keywords genericas (M4)
KEYWORDS_POOL = [
    'keywordHandler:addKeyword({ "job" }, StdModule.say, { npcHandler = npcHandler, text = "Sou o {nome}." })',
    'keywordHandler:addKeyword({ "name" }, StdModule.say, { npcHandler = npcHandler, text = "Me chamo {nome}." })',
    'keywordHandler:addKeyword({ "time" }, StdModule.say, { npcHandler = npcHandler, text = "Nao tenho relogio, amigo." })',
    'keywordHandler:addKeyword({ "help" }, StdModule.say, { npcHandler = npcHandler, text = "Em que posso ajudar?" })',
    'keywordHandler:addKeyword({ "bye" }, StdModule.say, { npcHandler = npcHandler, text = "Volte sempre!" })',
    'keywordHandler:addAliasKeyword({ "hello" })',
    'keywordHandler:addAliasKeyword({ "hi" })',
]

# Nomes de NPC (pool tematico)
NOMES_MASC = ['Brunin', 'Thorgrim', 'Alistair', 'Cedric', 'Magnus', 'Valtor', 'Grimm', 'Kael', 'Doran', 'Fenris']
NOMES_FEM = ['Elara', 'Seraphina', 'Lyra', 'Morgana', 'Isolde', 'Rowan', 'Vexia', 'Thalia', 'Nyra', 'Aria']
SOBRENOMES = ['Forjador', 'Guarda', 'Mago', 'Andarilho', 'Ferro', 'Sombra', 'Luz', 'Martelo', 'Escudo', 'Fogo']

# Templates de nome por tipo
NOME_TEMPLATES = {
    'ferreiro': lambda: f'{random.choice(NOMES_MASC)} {random.choice(SOBRENOMES[:5])}',
    'mago': lambda: f'{random.choice(NOMES_MASC + NOMES_FEM)} {random.choice(SOBRENOMES[5:])}',
    'guarda': lambda: f'{random.choice(NOMES_MASC)} {random.choice(SOBRENOMES[:3])}',
    'mercador': lambda: f'{random.choice(NOMES_MASC + NOMES_FEM)} {random.choice(SOBRENOMES)}',
    'bardo': lambda: f'{random.choice(NOMES_MASC + NOMES_FEM)} {random.choice(SOBRENOMES)}',
    'alquimista': lambda: f'Alquimista {random.choice(NOMES_MASC + NOMES_FEM)}',
}


def amostrar_card(distribuicao):
    r = random.random() * 100
    acum = 0
    for valor, pct in distribuicao:
        acum += pct
        if r <= acum:
            return valor
    return distribuicao[-1][0]


class Planejador:
    def __init__(self):
        self._indice_nome = 0

    def _proximo_nome(self, tipo: str = 'geral') -> str:
        template = NOME_TEMPLATES.get(tipo, lambda: f'{random.choice(NOMES_MASC)} {random.choice(SOBRENOMES)}')
        return template()

    # ─── M2: Gerador de Marcos ─────────────────────────────────

    def gerar_marcos(self, tipo: str = 'geral') -> List[Dict]:
        """Gera a sequencia de marcos com cardinalidades do corpus."""
        n_cfg = amostrar_card(CARD_CONFIG_FIELDS)
        n_cb = amostrar_card(CARD_CALLBACKS)
        n_kw = amostrar_card(CARD_KEYWORDS)
        n_mod = amostrar_card(CARD_MODULES)

        ctx = {
            'nome': self._proximo_nome(tipo),
            'health': random.randint(80, 500),
            'walk_interval': random.choice([1000, 1500, 2000, 2500]),
            'walk_radius': random.randint(1, 5),
            'has_shop': random.random() < 0.30,
        }
        ctx['outfit'] = random.choice(OUTFITS)

        marcos = [
            {'tipo': 'cabecalho', 'ctx': ctx},
            {'tipo': 'npc_type_def', 'ctx': ctx},
            {'tipo': 'config_init', 'ctx': ctx},
        ]
        for _ in range(n_cfg):
            marcos.append({'tipo': 'config_field', 'ctx': ctx})
        marcos.append({'tipo': 'config_outfit', 'ctx': ctx})
        marcos.append({'tipo': 'config_flags', 'ctx': ctx})
        marcos.append({'tipo': 'handler_init', 'ctx': ctx})
        marcos.append({'tipo': 'npc_handler', 'ctx': ctx})
        for _ in range(n_cb):
            marcos.append({'tipo': 'callback', 'ctx': ctx})
        for _ in range(n_kw):
            marcos.append({'tipo': 'keyword', 'ctx': ctx})
        for _ in range(n_mod):
            marcos.append({'tipo': 'module', 'ctx': ctx})
        marcos.append({'tipo': 'register', 'ctx': ctx})

        return marcos, ctx

    # ─── M3: Gerador de Seções ─────────────────────────────────

    def gerar_secoes(self, marcos: List[Dict], ctx: Dict) -> List[str]:
        """Para cada marco, gera o codigo Lua da secao."""
        secoes = []

        for marco in marcos:
            tipo = marco['tipo']
            if tipo == 'cabecalho':
                secoes.append(f'local internalNpcName = "{ctx["nome"]}"')
            elif tipo == 'npc_type_def':
                secoes.append(f'local npcType = Game.createNpcType(internalNpcName)')
                secoes.append(f'local npcConfig = {{}}')
            elif tipo == 'config_init':
                pass  # ja incluido no npc_type_def
            elif tipo == 'config_field':
                # Alterna entre campos base e opcionais
                if not hasattr(self, '_cfg_idx'):
                    self._cfg_idx = 0
                if self._cfg_idx < len(CONFIG_BASE):
                    _, fn = CONFIG_BASE[self._cfg_idx]
                    secoes.append(fn(ctx))
                else:
                    # Campos opcionais
                    idx = self._cfg_idx - len(CONFIG_BASE)
                    opcionais = [c for c in CONFIG_OPCIONAIS if random.random() < c[1]]
                    if idx < len(opcionais):
                        _, _, fn = opcionais[idx]
                        secoes.append(fn(ctx))
                self._cfg_idx += 1
            elif tipo == 'config_outfit':
                o = ctx['outfit']
                secoes.append(f'npcConfig.outfit = {{\n\t\tlookType = {o["lookType"]},\n\t\tlookHead = {o["lookHead"]},\n\t\tlookBody = {o["lookBody"]},\n\t\tlookLegs = {o["lookLegs"]},\n\t\tlookFeet = {o["lookFeet"]},\n\t\tlookAddons = {o["lookAddons"]},\n\t}}')
            elif tipo == 'config_flags':
                secoes.append('npcConfig.flags = {\n\t\tfloorchange = false,\n\t}')
            elif tipo == 'handler_init':
                secoes.append('local keywordHandler = KeywordHandler:new()')
                secoes.append('local npcHandler = NpcHandler:new(keywordHandler)')
            elif tipo == 'npc_handler':
                pass  # ja incluido no handler_init
            elif tipo == 'callback':
                base = list(CALLBACKS_BASE)
                if ctx.get('has_shop'):
                    base.extend(CALLBACKS_SHOP)
                if not hasattr(self, '_cb_idx'):
                    self._cb_idx = 0
                if self._cb_idx < len(base):
                    secoes.append(base[self._cb_idx])
                self._cb_idx += 1
            elif tipo == 'keyword':
                kw = random.choice(KEYWORDS_POOL)
                secoes.append(kw.replace('{nome}', ctx['nome']))
            elif tipo == 'module':
                secoes.append(f'npcHandler:addModule(FocusModule:new(), npcConfig.name, true, true, true)')
                secoes.append('')
                secoes.append('-- npcType registering the npcConfig table')
            elif tipo == 'register':
                secoes.append('npcType:register(npcConfig)')

        return secoes

    # ─── M4: Preenchedor de Tokens ──────────────────────────────

    def gerar(self, tipo: str = 'geral') -> str:
        """Gera script Lua completo para um NPC."""
        self._cfg_idx = 0
        self._cb_idx = 0

        marcos, ctx = self.gerar_marcos(tipo)
        secoes = self.gerar_secoes(marcos, ctx)

        # Junta linhas, mantendo quebras entre secoes
        linhas = []
        for i, sec in enumerate(secoes):
            linhas.append(sec)
        return '\n\n'.join(linhas)


# ─── CLI de teste ─────────────────────────────────────────

if __name__ == '__main__':
    import sys
    tipo = sys.argv[1] if len(sys.argv) > 1 else 'ferreiro'
    p = Planejador()
    codigo = p.gerar(tipo)
    print(f'-- Script gerado para NPC tipo: {tipo}')
    print(f'-- ShadowCanary target\n')
    print(codigo)
