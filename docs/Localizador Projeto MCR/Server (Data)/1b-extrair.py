#!/usr/bin/env python3
import re, sys
from pathlib import Path

FORBIDDEN_DIRS = {'lib','libs','migrations','vcproj','tests','src','cmake',
                  '.github','docker','docs','metrics','npclib','scripts/lib',
                  'MCR Scripts','modules','json','reports','logs','XML'}
FORBIDDEN_FILES = {'config.lua','global.lua','core.lua','stages.lua','update.lua',
                   'titles.lua','achievements.lua','badges.lua',
                   'register_npc_type.lua','register_monster_type.lua'}

def is_allowed(filepath):
    parts = filepath.parts
    for part in parts:
        if part in FORBIDDEN_DIRS:
            return False
    return filepath.name not in FORBIDDEN_FILES and filepath.suffix == '.lua'

def main():
    if len(sys.argv) < 3:
        print("Uso: python 1b-extrair-monster-names.py <raiz> saida.txt")
        return
    root = Path(sys.argv[1])
    out = sys.argv[2]
    all_names = set()
    for fp in root.rglob('*.lua'):
        if not is_allowed(fp): continue
        try:
            with open(fp, 'r', encoding='iso-8859-1') as f:
                content = f.read()
        except:
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
            except: continue
        # Somente strings que são nomes (primeira letra maiúscula)
        names = re.findall(r'Game\.createMonsterType\s*\(\s*"([A-Z][^"]*)"\s*\)', content)
        all_names.update(names)
    with open(out, 'w', encoding='utf-8') as f:
        for name in sorted(all_names):
            f.write(name + '\n')
    print(f"{len(all_names)} nomes de monstros extraídos.")

if __name__ == '__main__':
    main()