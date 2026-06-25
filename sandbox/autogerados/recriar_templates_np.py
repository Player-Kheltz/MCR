#!/usr/bin/env python3
# recriar templates npc monster item quest spell para o mcr_ultimate.py baseado nos padroes do projeto MCR
import os, sys, json

def main():
    import os
# Template NPC
npc_template = {
    "id": None,
    "name": "",
    "description": "",
    "level": 0,
    "hp": 100,
    "mp": 50,
    "strength": 10,
    "defense": 5,
    "speed": 8,
    "drops": []
}

# Template Monstro
monster_template = {
    "id": None,
    "name": "",
    "description": "",
    "level": 0,
    "hp": 200,
    "mp": 100,
    "strength": 20,
    "defense": 15,
    "speed": 12,
    "drops": []
}

# Template Item
item_template = {
    "id": None,
    "name": "",
    "description": "",
    "type": "",  # Ex: 'weapon', 'armor', 'potion'
    "effect": ""
}

# Template Quest
quest_template = {
    "id": None,
    "title": "",
    "description": "",
    "objective": "",
    "rewards": []
}

# Template Spell
spell_template = {
    "id": None,
    "name": "",
    "description": "",
    "mana_cost": 20,
    "damage": 30,
    "effect": ""
}
#```

if __name__ == '__main__':
    main()
