"""Testar auto_repair."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.self_study import SelfStudyEngine
from modulos.ia import IA
from modulos.kg import KnowledgeGraph

s = SelfStudyEngine(IA(), KnowledgeGraph())
a = s.escanear_projeto(60)
r = s._analisar_anti_patterns(a)

print('BARE:', len(r.get('except: bare', [])))
print('PASS:', len(r.get('except: pass', [])))

if r.get('except: bare') or r.get('except: pass'):
    print('Executando auto_repair...')
    import time
    t0 = time.time()
    corr = s._auto_repair(r)
    print('Tempo:', round(time.time()-t0, 1), 's')
    print('Correcoes:', sum(len(v) for v in corr.values()), 'em', len(corr), 'arquivos')
    for fname, cs in corr.items():
        for c in cs:
            print(' ', fname, ':L' + str(c['linha']), c.get('antes',''), '->', c.get('depois',''))
else:
    print('Nada a reparar')
