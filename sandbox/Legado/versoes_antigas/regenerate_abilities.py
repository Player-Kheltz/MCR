#!/usr/bin/env python3
"""Regenera os 9 ability files com sintaxe SHC correta (multi-linha)."""
import os

HABIL_DIR = r"E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades"
TEMPLATE = """--[[
    Projeto MCR — SPA — {NAME} ({ID})
    Perfil: {PROFILE}
    IDs: {ID_RANGE}
--]]
-- Traco: "{TRAIT}" — Nv5: {T5} | Nv10: {T10} | Nv15: {T15} | Nv20: {T20}

{ABILITIES}

print(">> SPA: habilidades/{FILENAME} carregado")
"""

ABILITY_TEMPLATE = """HABILIDADES[{ID}] = {{
    nome = "{NOME}",
    tipo = "{TIPO}",
    dominio = {{DOM}},
    cooldown = {CD},
    categoria = "{CAT}",
    descricao = "{DESC}",
    efeitoConfig = {{
        tipo = "{EF_TIPO}",
        dano = {DANO},
        percentual = {PCT},
        elemento = {ELEM},
    }},
    postura = {{
        [1] = {{ efeitoConfig = {{ dano = {P1_DANO} }} }},
        [3] = {{ efeitoConfig = {{ dano = {P3_DANO} }} }},
    }},
    niveis = {{
        [5] = {{ {{ mod = "efeitoConfig", dano = "*1.15" }} }},
        [10] = {{ {{ mod = "efeitoConfig", {N10_MOD} = "{N10_VAL}" }} }},
    }},
}}
"""

def abil(id, nome, tipo, dom, cd, cat, desc, ef_tipo, dano, pct, elem,
         p1_dano, p3_dano, n10_mod, n10_val):
    return ABILITY_TEMPLATE.format(ID=id, NOME=nome, TIPO=tipo, DOM=dom, CD=cd,
        CAT=cat, DESC=desc, EF_TIPO=ef_tipo, DANO=dano, PCT=pct, ELEM=elem,
        P1_DANO=p1_dano, P3_DANO=p3_dano, N10_MOD=n10_mod, N10_VAL=n10_val)

DOMINIOS = {
    "arcos": {
        "file": "arcos.lua", "id": 120, "name": "ARCOS", "profile": "Especialidade (Precisao 13 -> Combate 1)",
        "id_start": 12001, "id_end": 12020,
        "trait": "Mira Infalivel", "elem": "COMBAT_PHYSICALDAMAGE",
        "t5": "alcance+1", "t10": "critico+5%", "t15": "perfuracao", "t20": "olho de aguia",
        "data": [
             (12001, "Tiro Certeiro", "gatilho", 120, 3, "single", "Disparo preciso de longa distancia.",
             "projectile", 1.6, 0.55, 1.3, 0.9, "distancia", 1),
            (12002, "Chuva de Flechas", "gatilho", 120, 6, "aoe", "Bombardeio de flechas em area.",
             "area_target", 1.0, 0.35, 1.2, 0.7, "raio", 1),
            (12003, "Flecha Perfurante", "gatilho", 120, 4, "single", "Flecha que atravessa armaduras.",
             "projectile", 1.8, 0.6, 1.5, 1.0, "alcance", "+1"),
            (12004, "Mira Precisa", "passiva", 120, 0, "passiva", "Aumenta chance de critico por nivel.",
             "passive_scaling", 0, 0, 0, 0, "critChance", "+0.05"),
            (12005, "Flecha Elemental", "gatilho", 120, 4, "single", "Flecha imbuida com elemento.",
             "projectile", 1.4, 0.5, 1.2, 0.8, "elemento", "COMBAT_FIREDAMAGE"),
            (12006, "Disparo Triplo", "gatilho", 120, 5, "aoe", "Dispara tres flechas em cone.",
             "cone", 0.9, 0.3, 1.1, 0.6, "alcance", "+1"),
            (12007, "Olho de Aguia", "gatilho", 120, 8, "buff", "Aumenta precisao temporariamente.",
             "buff", 0, 0, 0, 0, "duracao", "+2"),
            (12008, "Tiro Rapido", "gatilho", 120, 2, "single", "Disparo rapido de baixo dano.",
             "projectile", 0.8, 0.3, 1.0, 0.5, "dano", "*1.2"),
            (12009, "Flecha de Gelo", "gatilho", 120, 4, "single", "Flecha que lentifica o alvo.",
             "projectile", 1.2, 0.4, 1.0, 0.7, "lentidao", "+0.2"),
            (12010, "Tempestade de Flechas", "gatilho", 120, 14, "finisher", "Rajada massiva de flechas.",
             "storm", 2.0, 0.0, 2.5, 1.5, "acertos", "+2"),
        ]
    },
    "armas_punho": {
        "file": "armas_punho.lua", "id": 132, "name": "ARMAS DE PUNHO", "profile": "Especialidade (Artes Marciais 14 -> Combate 1)",
        "id_start": 13201, "id_end": 13220,
        "trait": "Soco Rapido", "elem": "COMBAT_PHYSICALDAMAGE",
        "t5": "velocidade+5%", "t10": "multi-hit+1", "t15": "precisao", "t20": "mestre dos punhos",
        "data": [
            (13201, "Soco Rapido", "gatilho", 132, 1, "single", "Golpe rapido com chance de duplo.",
             "melee", 0.5, 0.2, 0.7, 0.3, "dano", "*1.2"),
            (13202, "Chute Baixo", "gatilho", 132, 3, "single", "Chute que derruba o inimigo.",
             "melee", 0.8, 0.3, 1.0, 0.5, "dano", "*1.15"),
            (13203, "Joelhada", "gatilho", 132, 3, "single", "Joelhada que atordoa.",
             "melee", 1.0, 0.35, 1.3, 0.7, "dano", "*1.15"),
            (13204, "Combo de Punhos", "gatilho", 132, 4, "single", "Sequencia de golpes rapidos.",
             "multi_hit", 0.5, 0.2, 0.6, 0.3, "acertos", "+1"),
            (13205, "Esquiva Felina", "passiva", 132, 0, "passiva", "Aumenta chance de esquiva.",
             "passive_scaling", 0, 0, 0, 0, "esquivaPorNivel", "+0.01"),
            (13206, "Giro de Tornado", "gatilho", 132, 5, "aoe", "Golpe giratorio que atinge varios.",
             "explosion_ring", 0.8, 0.3, 1.0, 0.5, "raio", "+1"),
            (13207, "Punho de Ferro", "gatilho", 132, 4, "single", "Soco que penetra armaduras.",
             "melee", 1.5, 0.5, 1.8, 1.0, "dano", "*1.15"),
            (13208, "Vento Cortante", "gatilho", 132, 4, "aoe", "Golpe que cria uma onda de choque.",
             "cone", 0.7, 0.25, 0.9, 0.4, "alcance", "+1"),
            (13209, "Foco dos Punhos", "gatilho", 132, 8, "buff", "Aumenta dano e velocidade.",
             "buff", 0, 0, 0, 0, "duracao", "+2"),
            (13210, "Danca dos Punhos", "gatilho", 132, 12, "finisher", "Sequencia devastadora de golpes.",
             "storm", 1.8, 0.0, 2.2, 1.2, "acertos", "+2"),
        ]
    },
    "bastoes_arcanos": {
        "file": "bastoes_arcanos.lua", "id": 133, "name": "BASTOES ARCANOS", "profile": "Especialidade (Artes Marciais 14 -> Combate 1)",
        "id_start": 13301, "id_end": 13320,
        "trait": "Sabedoria Arcana", "elem": "COMBAT_ENERGYDAMAGE",
        "t5": "dano+5%", "t10": "mana+10%", "t15": "canalizacao", "t20": "arquimago",
        "data": [
            (13301, "Projetil Arcano", "gatilho", 133, 2, "single", "Disparo magico de energia.",
             "projectile", 1.2, 0.4, 1.5, 0.8, "distancia", "+1"),
            (13302, "Sabedoria Arcana", "passiva", 133, 0, "passiva", "Aumenta mana por nivel.",
             "passive_scaling", 0, 0, 0, 0, "manaPorNivel", "+5"),
            (13303, "Explosao Arcana", "gatilho", 133, 5, "aoe", "Explosao de energia arcana.",
             "area_target", 1.3, 0.45, 1.6, 0.9, "raio", "+1"),
            (13304, "Barreira Arcana", "gatilho", 133, 8, "defense", "Escudo magico absorvedor.",
             "buff", 0, 0, 0, 0, "absorcao", "+50"),
            (13305, "Toque Arcano", "gatilho", 133, 4, "single", "Toque que drena mana.",
             "melee", 1.4, 0.5, 1.7, 1.0, "dano", "*1.15"),
            (13306, "Rajada Arcana", "gatilho", 133, 4, "aoe", "Cone de energia arcana.",
             "cone", 0.9, 0.3, 1.1, 0.6, "alcance", "+1"),
            (13307, "Foco Arcano", "gatilho", 133, 10, "buff", "Aumenta poder magico.",
             "buff", 0, 0, 0, 0, "duracao", "+2"),
            (13308, "Teletransporte Arcano", "gatilho", 133, 6, "mobility", "Teleporte curto.",
             "teleport", 0.5, 0.0, 0.0, 0.0, "distancia", "+1"),
            (13309, "Drenagem Arcana", "gatilho", 133, 5, "debuff", "Drena mana ao longo do tempo.",
             "debuff", 0.5, 0.0, 0.0, 0.0, "drenaMana", "+10"),
            (13310, "Tempestade Arcana", "gatilho", 133, 15, "finisher", "Tempestade arcana devastadora.",
             "storm", 2.0, 0.0, 2.5, 1.5, "acertos", "+2"),
        ]
    },
    "clavas_leves": {
        "file": "clavas_leves.lua", "id": 112, "name": "CLAVAS LEVES", "profile": "Especialidade (Clavas 12 -> Combate 1)",
        "id_start": 11201, "id_end": 11220,
        "trait": "Toque Rapido", "elem": "COMBAT_PHYSICALDAMAGE",
        "t5": "velocidade+5%", "t10": "atordoamento+5%", "t15": "combo", "t20": "mestre do ritmo",
        "data": [
            (11201, "Toque Rapido", "gatilho", 112, 2, "single", "Golpe rapido que atordoa.",
             "melee", 0.7, 0.25, 0.9, 0.4, "dano", "*1.2"),
            (11202, "Ritmo de Batalha", "passiva", 112, 0, "passiva", "Aumenta velocidade de ataque.",
             "passive_scaling", 0, 0, 0, 0, "velocidadeAtaque", "+0.01"),
            (11203, "Golpe Rapido", "gatilho", 112, 2, "single", "Soco rapido que atordoa levemente.",
             "melee", 1.0, 0.35, 1.2, 0.7, "dano", "*1.15"),
            (11204, "Combo Agil", "gatilho", 112, 4, "single", "Sequencia de golpes ageis.",
             "multi_hit", 0.6, 0.2, 0.8, 0.4, "acertos", "+1"),
            (11205, "Clava Giratoria", "gatilho", 112, 5, "aoe", "Golpe giratorio que atinge varios.",
             "explosion_ring", 1.0, 0.35, 1.3, 0.7, "raio", "+1"),
            (11206, "Mobilidade", "passiva", 112, 0, "passiva", "Aumenta velocidade de movimento.",
             "passive_scaling", 0, 0, 0, 0, "velocidadeMovimento", "+0.01"),
            (11207, "Golpe Atordoante", "gatilho", 112, 5, "single", "Golpe que atordoa o alvo.",
             "melee", 1.3, 0.45, 1.6, 0.9, "dano", "*1.15"),
            (11208, "Esquiva Agil", "gatilho", 112, 6, "defense", "Aumenta esquiva temporariamente.",
             "buff", 0, 0, 0, 0, "duracao", "+1"),
            (11209, "Foco Total", "gatilho", 112, 8, "buff", "Foco que aumenta acerto critico.",
             "buff", 0, 0, 0, 0, "duracao", "+2"),
            (11210, "Danca das Clavas", "gatilho", 112, 12, "finisher", "Danca letal de golpes.",
             "storm", 1.8, 0.0, 2.2, 1.2, "acertos", "+2"),
        ]
    },
    "clavas_pesadas": {
        "file": "clavas_pesadas.lua", "id": 113, "name": "CLAVAS PESADAS", "profile": "Especialidade (Clavas 12 -> Combate 1)",
        "id_start": 11301, "id_end": 11320,
        "trait": "Esmagador", "elem": "COMBAT_PHYSICALDAMAGE",
        "t5": "dano+5%", "t10": "stun+5%", "t15": "impacto", "t20": "tremor",
        "data": [
            (11301, "Esmagador", "gatilho", 113, 4, "single", "Golpe que esmaga o inimigo.",
             "melee", 2.0, 0.7, 2.5, 1.3, "dano", "*1.15"),
            (11302, "Parede de Ferro", "passiva", 113, 0, "passiva", "Aumenta resistencia a dano.",
             "passive_scaling", 0, 0, 0, 0, "reducaoDano", "+0.01"),
            (11303, "Impacto Brutal", "gatilho", 113, 5, "single", "Impacto que atordoa e empurra.",
             "melee", 2.4, 0.8, 3.0, 1.5, "dano", "*1.15"),
            (11304, "Tremor", "gatilho", 113, 6, "aoe", "Tremor que derruba inimigos.",
             "explosion_ring", 1.2, 0.4, 1.5, 0.8, "raio", "+1"),
            (11305, "Postura Imovel", "toggle", 113, 0, "defense", "Postura que reduz dano recebido.",
             "toggle_effect", 0, 0, 0, 0, "reducaoDano", "+0.05"),
            (11306, "Golpe de Exaustao", "gatilho", 113, 5, "debuff", "Golpe que reduz velocidade.",
             "debuff", 0.5, 0.0, 0.0, 0.0, "duracao", "+1"),
            (11307, "Furia do Gigante", "gatilho", 113, 8, "buff", "Aumenta poder temporariamente.",
             "buff", 0, 0, 0, 0, "duracao", "+2"),
            (11308, "Quebra-Ossos", "gatilho", 113, 5, "single", "Golpe que reduz armadura.",
             "melee", 1.8, 0.6, 2.2, 1.2, "dano", "*1.15"),
            (11309, "Impeto de Ferro", "gatilho", 113, 6, "mobility", "Investida que atordoa.",
             "dash", 1.5, 0.0, 0.0, 0.0, "distancia", "+1"),
            (11310, "Cataclismo", "gatilho", 113, 15, "finisher", "Golpe devastador na area.",
             "storm", 2.8, 0.0, 3.5, 2.0, "acertos", "+2"),
        ]
    },
    "espadas_pesadas": {
        "file": "espadas_pesadas.lua", "id": 101, "name": "ESPADAS PESADAS", "profile": "Especialidade (Laminas 10 -> Combate 1)",
        "id_start": 10101, "id_end": 10125,
        "trait": "Lamina Colossal", "elem": "COMBAT_PHYSICALDAMAGE",
        "t5": "dano+5%", "t10": "critico+10%", "t15": "penetracao", "t20": "golpe sismico",
        "data": [
            (10101, "Corte Colossal", "gatilho", 101, 4, "single", "Corte poderoso com espada grande.",
             "melee", 2.0, 0.7, 2.5, 1.3, "dano", "*1.15"),
            (10102, "Postura do Guardiao", "passiva", 101, 0, "passiva", "Postura que reduz dano.",
             "passive_scaling", 0, 0, 0, 0, "reducaoDano", "+0.01"),
            (10103, "Ataque Carregado", "gatilho", 101, 6, "single", "Ataque poderoso que requer carga.",
             "melee", 3.0, 1.0, 3.5, 2.0, "dano", "*1.15"),
            (10104, "Lamina Gelada", "gatilho", 101, 5, "single", "Golpe elemental de gelo.",
             "melee", 1.5, 0.5, 1.8, 1.0, "dano", "*1.15"),
            (10105, "Lamina Flamejante", "gatilho", 101, 5, "single", "Golpe elemental de fogo.",
             "melee", 1.6, 0.55, 2.0, 1.0, "dano", "*1.15"),
            (10106, "Golpe de Autoridade", "gatilho", 101, 6, "aoe", "Golpe que atinge area frontal.",
             "cone", 1.3, 0.45, 1.6, 0.9, "alcance", "+1"),
            (10107, "Quebra-Armadura", "gatilho", 101, 5, "debuff", "Golpe que reduz armadura do alvo.",
             "debuff", 0.8, 0.0, 0.0, 0.0, "duracao", "+2"),
            (10108, "Furia do Berserker", "gatilho", 101, 10, "buff", "Aumenta poder de ataque.",
             "buff", 0, 0, 0, 0, "duracao", "+2"),
            (10109, "Investida", "gatilho", 101, 6, "mobility", "Investida que atordoa o alvo.",
             "dash", 1.0, 0.0, 0.0, 0.0, "distancia", "+1"),
            (10110, "Corte Giratorio", "gatilho", 101, 5, "aoe", "Giro com a espada atingindo todos ao redor.",
             "explosion_ring", 1.2, 0.4, 1.5, 0.8, "raio", "+1"),
        ]
    },
    "lutador": {
        "file": "lutador.lua", "id": 130, "name": "LUTADOR", "profile": "Especialidade (Artes Marciais 14 -> Combate 1)",
        "id_start": 13001, "id_end": 13020,
        "trait": "Punhos de Aco", "elem": "COMBAT_PHYSICALDAMAGE",
        "t5": "dano+10%", "t10": "combo+1", "t15": "quebra-ossos", "t20": "mestre do combate",
        "data": [
            (13001, "Jab", "gatilho", 130, 1, "single", "Soco rapido que aumenta combo.",
             "melee", 0.6, 0.2, 0.8, 0.3, "dano", "*1.2"),
            (13002, "Cruzado", "gatilho", 130, 3, "single", "Cruzado que atordoa o oponente.",
             "melee", 1.2, 0.4, 1.5, 0.8, "dano", "*1.15"),
            (13003, "Combinacao", "gatilho", 130, 4, "single", "Sequencia de golpes ritmados.",
             "multi_hit", 0.7, 0.25, 0.9, 0.4, "acertos", "+1"),
            (13004, "Gancho", "gatilho", 130, 4, "single", "Gancho que empurra o inimigo.",
             "melee", 1.4, 0.5, 1.7, 1.0, "dano", "*1.15"),
            (13005, "Esquiva", "gatilho", 130, 5, "defense", "Esquiva que permite contra-ataque.",
             "buff", 0, 0, 0, 0, "duracao", "+1"),
            (13006, "Upper Cut", "gatilho", 130, 5, "single", "Uppercut que lanca o inimigo ao ar.",
             "melee", 1.6, 0.55, 2.0, 1.0, "dano", "*1.15"),
            (13007, "Foco Interior", "passiva", 130, 0, "passiva", "Aumenta dano por nivel.",
             "passive_scaling", 0, 0, 0, 0, "danoPorNivel", "+0.01"),
            (13008, "Quebra-Costas", "gatilho", 130, 6, "debuff", "Golpe que reduz atributos do alvo.",
             "debuff", 0.8, 0.0, 0.0, 0.0, "duracao", "+1"),
            (13009, "Furia Marcial", "gatilho", 130, 8, "buff", "Aumenta poder de luta.",
             "buff", 0, 0, 0, 0, "duracao", "+2"),
            (13010, "Combo Final", "gatilho", 130, 12, "finisher", "Sequencia devastadora final.",
             "multi_hit", 0.9, 0.0, 1.2, 0.5, "acertos", "+2"),
        ]
    },
    "machados_pesados": {
        "file": "machados_pesados.lua", "id": 111, "name": "MACHADOS PESADOS", "profile": "Especialidade (Machados 11 -> Combate 1)",
        "id_start": 11101, "id_end": 11120,
        "trait": "Furia do Norte", "elem": "COMBAT_PHYSICALDAMAGE",
        "t5": "dano+5%", "t10": "sangramento+10%", "t15": "furia", "t20": "golpe devastador",
        "data": [
            (11101, "Golpe Devastador", "gatilho", 111, 4, "single", "Golpe que causa sangramento.",
             "melee", 2.2, 0.75, 2.8, 1.5, "dano", "*1.15"),
            (11102, "Furia de Batalha", "passiva", 111, 0, "passiva", "Aumenta dano por nivel.",
             "passive_scaling", 0, 0, 0, 0, "danoPorNivel", "+0.01"),
            (11103, "Corte Duplo", "gatilho", 111, 3, "single", "Dois cortes rapidos.",
             "multi_hit", 1.0, 0.35, 1.3, 0.6, "acertos", "+1"),
            (11104, "Grito de Guerra", "gatilho", 111, 8, "buff", "Grito que aumenta poder do grupo.",
             "buff", 0, 0, 0, 0, "duracao", "+2"),
            (11105, "Machado Arremessado", "gatilho", 111, 5, "single", "Machado arremessado a distancia.",
             "projectile", 1.4, 0.5, 1.7, 1.0, "distancia", "+1"),
            (11106, "Rodopio", "gatilho", 111, 5, "aoe", "Giro com machado atingindo todos ao redor.",
             "explosion_ring", 1.3, 0.45, 1.6, 0.9, "raio", "+1"),
            (11107, "Fracao de Armadura", "gatilho", 111, 6, "debuff", "Golpe que reduz defesa do alvo.",
             "debuff", 0.5, 0.0, 0.0, 0.0, "duracao", "+2"),
            (11108, "Investida Bruta", "gatilho", 111, 6, "mobility", "Investida que derruba inimigos.",
             "dash", 1.2, 0.0, 0.0, 0.0, "distancia", "+1"),
            (11109, "Furia Sangrenta", "gatilho", 111, 12, "finisher", "Ataque furioso que sangra.",
             "storm", 2.5, 0.0, 3.0, 1.8, "acertos", "+2"),
            (11110, "Ataque Macico", "gatilho", 111, 6, "single", "Golpe massivo que empurra.",
             "melee", 2.8, 0.9, 3.5, 2.0, "dano", "*1.15"),
        ]
    },
    "sobrevivencia": {
        "file": "sobrevivencia.lua", "id": 400, "name": "SOBREVIVENCIA", "profile": "Especialidade (Natureza 4)",
        "id_start": 40001, "id_end": 40020,
        "trait": "Sobrevivente", "elem": "COMBAT_PHYSICALDAMAGE",
        "t5": "regen+1%", "t10": "velocidade+5%", "t15": "faro", "t20": "mestre da selva",
        "data": [
            (40001, "Faro Aguado", "passiva", 400, 0, "passiva", "Aumenta deteccao de inimigos.",
             "passive_scaling", 0, 0, 0, 0, "deteccaoPorNivel", "+0.1"),
            (40002, "Armadilha de Caca", "gatilho", 400, 6, "debuff", "Armadilha que imobiliza.",
             "trap", 0.6, 0.0, 0.0, 0.0, "raio", "+1"),
            (40003, "Rastreamento", "gatilho", 400, 4, "debuff", "Marca o alvo para o grupo.",
             "debuff", 0.0, 0.0, 0.0, 0.0, "duracao", "+2"),
            (40004, "Primeiros Socorros", "gatilho", 400, 8, "buff", "Cura rapida emergencial.",
             "heal", 0, 0, 0, 0, "curaFixa", "+50"),
            (40005, "Flecha de Caca", "gatilho", 400, 3, "single", "Flecha precisa de cacador.",
             "projectile", 1.3, 0.45, 1.6, 0.9, "distancia", "+1"),
            (40006, "Fogueira", "toggle", 400, 0, "buff", "Fogueira que regenera aliados.",
             "field_aura", 0, 0, 0, 0, "raio", "+1"),
            (40007, "Couro Reforcado", "passiva", 400, 0, "passiva", "Aumenta armadura natural.",
             "passive_scaling", 0, 0, 0, 0, "armaduraPorNivel", "+1"),
            (40008, "Emboscada", "gatilho", 400, 5, "single", "Ataque surpresa que causa dano extra.",
             "melee", 1.8, 0.6, 2.2, 1.2, "dano", "*1.15"),
            (40009, "Instinto Selvagem", "gatilho", 400, 8, "buff", "Aumenta velocidade e esquiva.",
             "buff", 0, 0, 0, 0, "duracao", "+2"),
            (40010, "Cacada", "gatilho", 400, 14, "finisher", "Cacada implacavel contra o alvo.",
             "storm", 2.0, 0.0, 2.5, 1.5, "acertos", "+2"),
        ]
    },
}

def _fmt_val(v):
    """Formata valor para Lua: se comeca com +, remove o + e retorna como numero.
    Se tem operador (*), mantem como string. Senao retorna como numero."""
    if isinstance(v, str):
        if v.startswith("+"):
            return v[1:]  # +1 -> 1
        if v.startswith("*") or v.startswith("+"):
            return f'"{v}"'
    return str(v)

def gerar_arquivo(dom):
    abilities = []
    for data in dom["data"]:
        id_, nome, tipo, dom_id, cd, cat, desc, ef_tipo, dano, pct, p1, p3, n10m, n10v = data
        elem = dom["elem"]
        # Remove + prefix de n10v
        if isinstance(n10v, str) and n10v.startswith("+"):
            n10v_clean = n10v[1:]
        else:
            n10v_clean = str(n10v)
        
        # Determina se precisa de quotes: se comeca com + ou * ou e string nao numerica
        n10v_str = str(n10v_clean)
        needs_quotes = n10v_str.startswith("*") or n10v_str.startswith("+")
        n10v_out = f'"{n10v_str}"' if needs_quotes else n10v_str
        
        if tipo == "passiva":
            a = f"""HABILIDADES[{id_}] = {{
    nome = "{nome}",
    tipo = "passiva",
    dominio = {{{dom_id}}},
    cooldown = {cd},
    categoria = "passiva",
    descricao = "{desc}",
    efeitoConfig = {{
        tipo = "{ef_tipo}",
        {n10m} = {n10v_out},
    }},
    niveis = {{
        [5] = {{ {{ mod = "efeitoConfig", {n10m} = {n10v_out} }} }},
        [10] = {{ {{ mod = "efeitoConfig", {n10m} = {n10v_out} }} }},
    }},
}}"""
        else:
            a = f"""HABILIDADES[{id_}] = {{
    nome = "{nome}",
    tipo = "{tipo}",
    dominio = {{{dom_id}}},
    cooldown = {cd},
    categoria = "{cat}",
    descricao = "{desc}",
    efeitoConfig = {{
        tipo = "{ef_tipo}",
        dano = {dano},
        percentual = {pct},
        elemento = {elem},
    }},
    postura = {{
        [1] = {{ efeitoConfig = {{ dano = {p1} }} }},
        [3] = {{ efeitoConfig = {{ dano = {p3} }} }},
    }},
    niveis = {{
        [5] = {{ {{ mod = "efeitoConfig", dano = "*1.15" }} }},
        [10] = {{ {{ mod = "efeitoConfig", {n10m} = {n10v_out} }} }},
    }},
}}"""
        abilities.append(a)
    
    content = f"""--[[
    Projeto MCR — SPA — {dom['name']} ({dom['id']})
    Perfil: {dom['profile']}
    SHC: 5 camadas contextuais
    IDs: {dom['id_start']}-{dom['id_end']}
--]]
-- Traco: "{dom['trait']}" — Nv5: {dom['t5']} | Nv10: {dom['t10']} | Nv15: {dom['t15']} | Nv20: {dom['t20']}

{chr(10).join(abilities)}

print(">> SPA: habilidades/{dom['file']} carregado")
"""
    
    path = os.path.join(HABIL_DIR, dom["file"])
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ {dom['file']}: {len(abilities)} habilidades ({dom['id_start']}-{dom['id_start']+len(abilities)-1})")

# Gerar todos
for nome, dom in DOMINIOS.items():
    gerar_arquivo(dom)

print("\nTodos os arquivos regenerados!")
