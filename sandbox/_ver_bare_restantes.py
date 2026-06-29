"""Verifica except: bare restantes apos correcoes em modulos."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.self_study import SelfStudyEngine
from modulos.ia import IA
from modulos.kg import KnowledgeGraph

s = SelfStudyEngine(IA(), KnowledgeGraph())
a = s.escanear_projeto(60)
r = s._analisar_anti_patterns(a)
b = r.get('except: bare', [])

print('except: bare restantes:', len(b))
if b:
    # Agrupa por arquivo
    por_arquivo = {}
    for x in b:
        por_arquivo.setdefault(x['arquivo'], []).append(x)
    for fname, ocorrencias in sorted(por_arquivo.items()):
        print(f'\n  {fname} ({len(ocorrencias)}):')
        for x in ocorrencias:
            extra = f' | try: {x["linha_try"]}' if x.get('linha_try') else ''
            print(f'    L{x["linha"]}: {x["codigo"]}{extra}')
