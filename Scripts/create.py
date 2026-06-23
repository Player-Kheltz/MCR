#!/usr/bin/env python3
"""
create.py — Gerador de Templates do MCR

Uso:
    python scripts/create.py --list                    # Lista templates disponiveis
    python scripts/create.py dominio "Nome" [opcoes]   # Cria novo dominio
    python scripts/create.py habilidade "Nome" [opcoes] # Cria nova habilidade
    python scripts/create.py monster "Nome" [opcoes]    # Cria novo monstro
    python scripts/create.py item "Nome" [opcoes]       # Cria novo item
    python scripts/create.py spell "Nome" [opcoes]      # Cria nova spell
    python scripts/create.py npc "Nome" [opcoes]        # Cria novo NPC
    python scripts/create.py quest "Nome" [opcoes]      # Cria nova quest
    python scripts/create.py quest-stage "Nome" [opcoes] # Adiciona etapa a quest
"""

import os
import sys
import textwrap
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPA_DIR = os.path.join(BASE_DIR, "Canary", "data-canary", "scripts", "MCR", "SPA")
MONSTER_DIR = os.path.join(BASE_DIR, "Canary", "data-canary", "monster")
SPELL_DIR = os.path.join(BASE_DIR, "Canary", "data-canary", "scripts", "spells")
NPC_DIR = os.path.join(BASE_DIR, "Canary", "data-canary", "npc")
ITEMS_XML = os.path.join(BASE_DIR, "Canary", "data-canary", "items", "items.xml")
WORLD_DIR = os.path.join(BASE_DIR, "Canary", "data-canary", "world")


def sanitize_name(name):
    """Converte nome para snake_case."""
    s = name.lower().replace(" ", "_").replace("-", "_").replace("'", "").replace("\u00e7", "c")
    s = s.replace("\u00e3", "a").replace("\u00f5", "o").replace("\u00e1", "a")
    s = s.replace("\u00e9", "e").replace("\u00ed", "i").replace("\u00f3", "o")
    s = s.replace("\u00fa", "u").replace("\u00ea", "e").replace("\u00f4", "o")
    return s


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def cmd_list():
    """Lista todos os templates disponiveis."""
    templates = [
        ("dominio", "Cria dominio SPA completo (~6 arquivos)"),
        ("habilidade", "Cria uma habilidade individual (.lua)"),
        ("monster", "Cria monstro Revscript (.lua + loot)"),
        ("item", "Adiciona item ao items.xml + traducao"),
        ("spell", "Cria spell Revscript (.lua)"),
        ("npc", "Cria NPC Revscript (.lua)"),
        ("quest", "Inicializa quest (.lua + stage 1)"),
        ("quest-stage", "Adiciona etapa a quest existente"),
    ]
    print("Templates disponiveis:\n")
    for name, desc in templates:
        print(f"  {name:<15} {desc}")
    print()


# ─── DOMINIO ─────────────────────────────────────────────────────

def cmd_dominio(args):
    """Cria estrutura de um novo dominio SPA."""
    parser = iter(args)
    name = ""
    dom_id = None
    parent_name = ""
    description = ""
    color = "#FFFFFF"
    for arg in parser:
        if arg == "--id":
            dom_id = int(next(parser, "0"))
        elif arg == "--parent":
            parent_name = next(parser, "")
        elif arg == "--description":
            description = next(parser, "")
        elif arg == "--color":
            color = next(parser, "#FFFFFF")
        elif not name:
            name = arg

    if not name or dom_id is None:
        print("[ERRO] Uso: create.py dominio \"Nome\" --id NUM [--parent \"Pai\"]")
        return

    safe = sanitize_name(name)
    dom_dir = os.path.join(SPA_DIR, "habilidades", safe)
    passivas_dir = os.path.join(SPA_DIR, "core", "passivas")
    ensure_dir(dom_dir)

    # init.lua
    with open(os.path.join(dom_dir, "init.lua"), "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f'''\
            -- {safe}/init.lua
            -- Dominio: {name}
            -- ID: {dom_id}
            -- Habilidades placeholder para {name}

            local DOMINIO_ID = {dom_id}

            -- Placeholder: {skill_count or 35} habilidades
        '''))

    # passivas
    ensure_dir(passivas_dir)
    passiva_path = os.path.join(passivas_dir, safe + ".lua")
    if not os.path.exists(passiva_path):
        with open(passiva_path, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(f'''\
                -- passivas/{safe}.lua
                -- Passivas do dominio {name}
            '''))

    # SQL
    sql_path = os.path.join(dom_dir, "sql.sql")
    with open(sql_path, "w", encoding="utf-8") as f:
        parent_sql = f" (SELECT id FROM dominios WHERE nome = '{parent_name}')" if parent_name else "NULL"
        f.write(textwrap.dedent(f'''\
            -- SQL para registrar o dominio {name}
            INSERT INTO dominios (id, nome, descricao, parent_id, cor, created_at)
            VALUES ({dom_id}, '{name}', '{description or name}', {parent_sql}, '{color}', UNIX_TIMESTAMP());
        '''))

    print(f"[DOMINIO] {name} (id={dom_id}) criado em:")
    print(f"  {dom_dir}/")
    print(f"  {passiva_path}")
    print(f"  {sql_path}")
    print(f"[NEXT] Popule as habilidades em {dom_dir}/")


# ─── HABILIDADE ──────────────────────────────────────────────────

def cmd_habilidade(args):
    """Cria uma habilidade individual."""
    parser = iter(args)
    name = ""
    dom_name = ""
    hab_type = "projectile"
    damage = "physical"
    cooldown = 2000
    level = 1

    for arg in parser:
        if arg == "--dominion":
            dom_name = sanitize_name(next(parser, ""))
        elif arg == "--type":
            hab_type = next(parser, "projectile")
        elif arg == "--damage":
            damage = next(parser, "physical")
        elif arg == "--cooldown":
            cooldown = int(next(parser, "2000"))
        elif arg == "--level":
            level = int(next(parser, "1"))
        elif not name:
            name = arg

    if not name or not dom_name:
        print("[ERRO] Uso: create.py habilidade \"Nome\" --dominion slug-do-dominio")
        return

    safe = sanitize_name(name)
    dom_dir = os.path.join(SPA_DIR, "habilidades", dom_name)
    ensure_dir(dom_dir)

    hab_path = os.path.join(dom_dir, safe + ".lua")
    with open(hab_path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f'''\
            -- {dom_name}/{safe}.lua
            -- {name}
            -- Tipo: {hab_type} | Elemento: {damage} | Cooldown: {cooldown}ms | Nivel: {level}

            local habilidade = Habilidade({{
                name = "{name}",
                description = "Placeholder de {name}",
                dominion = "{dom_name}",
                type = "{hab_type}",
                damage = "{damage}",
                cooldown = {cooldown},
                level = {level},
            }})

            function habilidade.onCast(player, variant)
                -- TODO: implementar logica
                return true
            end

            habilidade:register()
        '''))

    print(f"[HABILIDADE] {name} criada em: {hab_path}")


# ─── MONSTER ─────────────────────────────────────────────────────

def cmd_monster(args):
    """Cria monstro Revscript."""
    parser = iter(args)
    name = ""
    health = 500
    damage = 50
    mon_type = "melee"
    level = 1
    loot_str = ""

    for arg in parser:
        if arg == "--health":
            health = int(next(parser, "500"))
        elif arg == "--damage":
            damage = int(next(parser, "50"))
        elif arg == "--type":
            mon_type = next(parser, "melee")
        elif arg == "--level":
            level = int(next(parser, "1"))
        elif arg == "--loot":
            loot_str = next(parser, "")
        elif not name:
            name = arg

    if not name:
        print("[ERRO] Uso: create.py monster \"Nome\" [--health 500]")
        return

    safe = sanitize_name(name)
    ensure_dir(MONSTER_DIR)

    mon_path = os.path.join(MONSTER_DIR, safe + ".lua")
    with open(mon_path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f'''\
            -- {safe}.lua
            -- {name}

            local combat = Combat()
            combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_PHYSICALDAMAGE)
            combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_HITAREA)

            local function onTargetCreature(creature, target)
                -- TODO: logica de dano
            end

            local monster = Monster("{name}")
            monster:setHealth({health})
            monster:setMaxHealth({health})
            monster:setDamage({damage})
            monster:setType("{mon_type}")
            monster:setLevel({level})
            monster:setBehavior(BEHAVIOR_AGGRESSIVE)
            monster:setTargetDistance(1)

            -- Loot
            monster:registerEvent("onKill", function(m, corpse)
                -- {loot_str or "sem loot configurado"}
            end)

            monster:register()
        '''))

    print(f"[MONSTER] {name} criado em: {mon_path}")


# ─── ITEM ────────────────────────────────────────────────────────

def cmd_item(args):
    """Adiciona item ao items.xml."""
    parser = iter(args)
    name = ""
    item_id = None
    item_type = "weapon"
    damage = 0
    description = ""

    for arg in parser:
        if arg == "--id":
            item_id = int(next(parser, "0"))
        elif arg == "--type":
            item_type = next(parser, "weapon")
        elif arg == "--damage":
            damage = int(next(parser, "0"))
        elif arg == "--description":
            description = next(parser, "")
        elif not name:
            name = arg

    if not name or not item_id:
        print("[ERRO] Uso: create.py item \"Nome\" --id NUM [--type weapon]")
        return

    safe_snake = sanitize_name(name)

    if os.path.exists(ITEMS_XML):
        with open(ITEMS_XML, "r", encoding="utf-8") as f:
            content = f.read()
        insert_before = "</items>"
        xml_entry = textwrap.dedent(f'''\\
            \t<item id="{item_id}" name="{name}" description="{description or name}">
            \t\t<attribute key="type" value="{item_type}" />
            \t\t<attribute key="weight" value="1000" />
            {f'\\t\\t<attribute key="attack" value="{damage}" />' if damage else ""}
            \t</item>
        ''')
        if insert_before in content:
            content = content.replace(insert_before, xml_entry + "\n" + insert_before)
            with open(ITEMS_XML, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[ITEM] {name} (id={item_id}) adicionado ao items.xml")
        else:
            print("[ERRO] Formato do items.xml nao reconhecido")
    else:
        print(f"[ERRO] items.xml nao encontrado em: {ITEMS_XML}")


# ─── SPELL ───────────────────────────────────────────────────────

def cmd_spell(args):
    """Cria spell Revscript."""
    parser = iter(args)
    name = ""
    spell_type = "wave"
    damage = "physical"
    cooldown = 2000
    mana = 100
    level = 1

    for arg in parser:
        if arg == "--type":
            spell_type = next(parser, "wave")
        elif arg == "--damage":
            damage = next(parser, "physical")
        elif arg == "--cooldown":
            cooldown = int(next(parser, "2000"))
        elif arg == "--mana":
            mana = int(next(parser, "100"))
        elif arg == "--level":
            level = int(next(parser, "1"))
        elif not name:
            name = arg

    if not name:
        print("[ERRO] Uso: create.py spell \"Nome\" [--type wave]")
        return

    safe = sanitize_name(name)
    ensure_dir(SPELL_DIR)

    spell_path = os.path.join(SPELL_DIR, safe + ".lua")
    with open(spell_path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f'''\
            -- {safe}.lua
            -- {name}

            local combat = Combat()
            combat:setParameter(COMBAT_PARAM_TYPE, COMBAT_{damage.upper()}DAMAGE)
            combat:setParameter(COMBAT_PARAM_EFFECT, CONST_ME_MAGIC_BLUE)
            combat:setParameter(COMBAT_PARAM_DISTANCEEFFECT, CONST_ANI_{damage.upper()})

            local area = createCombatArea(AREA_WAVE4, AREADIAGONAL_WAVE4)
            combat:setArea(area)

            function onCastSpell(creature, variant)
                return combat:execute(creature, variant)
            end

            local spell = Spell(SPELL_INSTANT)
            spell:name("{name}")
            spell:group("attack")
            spell:id({abs(hash(name)) % 10000 + 100})
            spell:cooldown({cooldown})
            spell:mana({mana})
            spell:level({level})
            spell:isPremium(false)
            spell:needTarget(false)
            spell:register()
        '''))

    print(f"[SPELL] {name} criada em: {spell_path}")


# ─── NPC ─────────────────────────────────────────────────────────

def cmd_npc(args):
    """Cria NPC Revscript."""
    parser = iter(args)
    name = ""
    job = "viajante"
    town = "Templo"

    for arg in parser:
        if arg == "--job":
            job = next(parser, "viajante")
        elif arg == "--town":
            town = next(parser, "Templo")
        elif not name:
            name = arg

    if not name:
        print("[ERRO] Uso: create.py npc \"Nome\" [--job \"funcao\"]")
        return

    safe = sanitize_name(name)
    ensure_dir(NPC_DIR)

    npc_path = os.path.join(NPC_DIR, safe + ".lua")
    with open(npc_path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f'''\
            -- {safe}.lua
            -- {name} ({job})

            local npc = Npc("{name}", "{town}")
            npc:setJob("{job}")

            function npc:onGreet(player)
                player:sendTextMessage(MESSAGE_INFO_DESCR, "Ola, " .. player:getName() .. "!")
            end

            function npc:onSay(player, words, param)
                if words == "missao" or words == "quest" then
                    player:sendTextMessage(MESSAGE_INFO_DESCR, "Ainda nao tenho missoes para voce.")
                end
                return true
            end

            npc:register()
        '''))

    print(f"[NPC] {name} criado em: {npc_path}")


# ─── QUEST ───────────────────────────────────────────────────────

def cmd_quest(args):
    """Cria quest inicial."""
    name = " ".join(args) if args else ""
    if not name:
        print("[ERRO] Uso: create.py quest \"Nome da Quest\"")
        return

    safe = sanitize_name(name)
    quest_dir = os.path.join(SPA_DIR, "quests", safe)
    ensure_dir(quest_dir)

    quest_path = os.path.join(quest_dir, "init.lua")
    with open(quest_path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f'''\
            -- quests/{safe}/init.lua
            -- {name}

            local QUEST_STORAGE = 60000

            local quest = Quest("{name}")

            function quest:onStageChange(player, fromStage, toStage)
                -- Notifica o jogador
                player:sendTextMessage(MESSAGE_INFO_DESCR, "[Quest] {name}: etapa " .. toStage)
            end

            quest:register()

            -- Stage 1 placeholder
            -- Adicione etapas com: create.py quest-stage "{name}" --stage 1 --objective "..."
        '''))

    print(f"[QUEST] {name} criada em: {quest_path}/")


# ─── QUEST-STAGE ─────────────────────────────────────────────────

def cmd_quest_stage(args):
    """Adiciona etapa a quest existente."""
    parser = iter(args)
    name = ""
    stage = 1
    objective = ""
    npc_name = ""
    reward = ""

    for arg in parser:
        if arg == "--stage":
            stage = int(next(parser, "1"))
        elif arg == "--objective":
            objective = next(parser, "")
        elif arg == "--npc":
            npc_name = next(parser, "")
        elif arg == "--reward":
            reward = next(parser, "")
        elif not name:
            name = arg

    if not name or not objective:
        print("[ERRO] Uso: create.py quest-stage \"Quest\" --stage N --objective \"...\"")
        return

    safe = sanitize_name(name)
    quest_dir = os.path.join(SPA_DIR, "quests", safe)
    ensure_dir(quest_dir)

    stage_path = os.path.join(quest_dir, f"stage_{stage}.lua")
    with open(stage_path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f'''\
            -- quests/{safe}/stage_{stage}.lua
            -- {name} - Etapa {stage}
            -- Objetivo: {objective}

            local storageKey = 60000 + {stage}

            -- Condicao de avanco
            -- Ex: storage 5003 >= 5 (derrotou 5 orcs)
            -- Adicione a logica conforme necessario
        '''))

    print(f"[QUEST-STAGE] {name} etapa {stage} criada em: {stage_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "--list": cmd_list,
        "dominio": cmd_dominio,
        "habilidade": cmd_habilidade,
        "monster": cmd_monster,
        "item": cmd_item,
        "spell": cmd_spell,
        "npc": cmd_npc,
        "quest": cmd_quest,
        "quest-stage": cmd_quest_stage,
    }

    if cmd in commands:
        if cmd == "--list":
            commands[cmd]()
        else:
            commands[cmd](args)
    else:
        print(f"[ERRO] Comando desconhecido: {cmd}")
        print(__doc__)


def hash(name):
    h = 0
    for c in name:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return h


if __name__ == "__main__":
    main()
