"""VALIDAÇÃO: DescobridorUniversal v2 — frequência diferencial por diretório."""
import sys, time
sys.path.insert(0, 'E:/MCR')
from mcr.descobridor import DescobridorUniversal
from mcr.paths import CANARY_NPC_DIR, CANARY_MONSTER_DIR

print('=' * 65)
print('  VALIDACAO — DESCOBRIDOR UNIVERSAL v2')
print('  Zero hardcode. Zero conhecimento de dominio.')
print('=' * 65)

t0 = time.time()

# Descobre ancoras comparando NPCs vs Monstros
d = DescobridorUniversal(max_arquivos_por_dir=100)
d.descobrir([CANARY_NPC_DIR, CANARY_MONSTER_DIR])

stats = d.estatisticas()
print(f'\n  Diretorios: {stats["diretorios"]}')
print(f'  Arquivos: {stats["arquivos_total"]}')
print(f'  Ancoras totais: {stats["ancoras_total"]}')
for dname, n in stats["ancoras_por_dir"].items():
    print(f'  {dname}: {n} ancoras')

# Mostra top ancoras de cada diretorio
print(f'\n  TOP ANCORAS — NPCs:')
for token, freq in d.ancoras_do_diretorio(CANARY_NPC_DIR)[:15]:
    print(f'    {token:25s} freq={freq:.2f}')

print(f'\n  TOP ANCORAS — Monstros:')
for token, freq in d.ancoras_do_diretorio(CANARY_MONSTER_DIR)[:15]:
    print(f'    {token:25s} freq={freq:.2f}')

# Testa classificacao
print(f'\n  CLASSIFICACAO AUTOMATICA:')
testes = ['npc', 'monster', 'monstro', 'internalnpcname', 'monstertype',
          'npctype', 'npcname', 'register', 'shop', 'loot', 'dragon',
          'ferreiro', 'orc', 'demon', 'quest', 'keywordhandler',
          'monsterloot', 'outfit', 'looktype', 'npcHandler']
for token in testes:
    c = d.classificar(token)
    if c:
        print(f'    {token:20s} -> {c}')
    else:
        print(f'    {token:20s} -> (sem dominio)')

print(f'\n{"="*65}')
print(f'  Tempo: {time.time()-t0:.1f}s')
npc_ok = any('npc' in t.lower() or 'internal' in t.lower() 
             for t, _ in d.ancoras_do_diretorio(CANARY_NPC_DIR)[:3])
mons_ok = any('monster' in t.lower() or 'loot' in t.lower()
              for t, _ in d.ancoras_do_diretorio(CANARY_MONSTER_DIR)[:3])
print(f'  NPC ancoras ok: {npc_ok}')
print(f'  Monstro ancoras ok: {mons_ok}')
print(f'{"="*65}')
