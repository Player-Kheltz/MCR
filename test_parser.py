import sys; sys.path.insert(0, r'E:\MCR')
from code_parser import get_parser

p = get_parser()
# Testa com um arquivo .lua
r = p.parse(r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades\arcos.lua')
if r:
    print('Arquivo:', r.get('arquivo'))
    print('Linguagem:', r.get('linguagem'))
    print('Funcoes:', len(r.get('funcoes',[])))
    for f in r.get('funcoes',[])[:5]:
        print(f'  {f.get("nome")}: L{f.get("inicio")}-L{f.get("fim")} ({f.get("linhas")} linhas)')
    print('Chamadas:', len(r.get('chamadas',[])))
    for c in r.get('chamadas',[])[:10]:
        print(f'  {c.get("funcao")} (L{c.get("linha")})')
    
    if r.get('fallback'):
        print('FALLBACK')
    else:
        print('PARSE REAL (tree-sitter)')
