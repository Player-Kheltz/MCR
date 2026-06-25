"""Upgrade no toquinho - correlacionar metricas"""
import os, json

KG_PATH = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
SCANNER = r'E:\Projeto MCR\sandbox\resolver_ultra.py'

def contar_detectores_no_scanner():
    """Conta quantas funcoes detectar_* existem no scanner."""
    if not os.path.exists(SCANNER): return 0
    with open(SCANNER, 'r', encoding='utf-8') as f:
        c = f.read()
    import re
    return len(re.findall(r'def detectar_\w+', c))

def contar_detectores_chamados():
    """Conta quantos detectores sao efetivamente chamados."""
    if not os.path.exists(SCANNER): return 0
    with open(SCANNER, 'r', encoding='utf-8') as f:
        c = f.read()
    import re
    functions = re.findall(r'def (detectar_\w+)', c)
    chamados = 0
    for fn in functions:
        if fn in c.split('def ')[0]:  # Verifica se aparece antes das definicoes
            pass
        if fn in c:
            # Procura se a funcao e chamada em algum lugar
            chamado = 0
            for line in c.split('\n'):
                if fn + '(' in line and 'def ' not in line:
                    chamado = 1
                    break
            chamados += chamado
    return chamados

print('=== TOQUINHO MELHORADO — CORRELACIONANDO METRICAS ===\n')

licoes_antes = 0
if os.path.exists(KG_PATH):
    with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
        kg = json.load(f)
    licoes_antes = len(kg.get('licoes', []))

detectores_total = contar_detectores_no_scanner()
detectores_usados = contar_detectores_chamados()
detectores_orfaos = detectores_total - detectores_usados

print(f'  KG: {licoes_antes} licoes')
print(f'  Detectores no scanner: {detectores_total}')
print(f'  Detectores chamados pelo scan(): {detectores_usados}')
print(f'  Detectores ORFAOS: {detectores_orfaos}')
print()

# Correlaciona
if licoes_antes > 50 and detectores_orfaos > 5:
    print('  [TOQUE] CONCLUSAO:')
    print(f'  O KG cresceu para {licoes_antes} licoes, mas {detectores_orfaos} detectores')
    print(f'  estao orfaos — foram gerados mas nunca chamados pelo scan().')
    print(f'  O aprendizado existe mas nao esta sendo APLICADO.')
    print()
    print(f'  CAUSA RAIZ: O auto_aprender_detector.py gera funcoes detectar_*')
    print(f'  mas o resolver_ultra.py (scan()) nunca as invoca.')
    print(f'  Elas viram codigo morto.')
    print()
    print(f'  SOLUCAO: No final do scan(), adicionar um loop que:')
    print(f'    1. Procura funcoes detectar_* no proprio modulo')
    print(f'    2. Para cada arquivo, chama cada detector')
    print(f'    3. Se retornar True, adiciona na lista de problemas')
    print()
    print(f'  Se isso for feito, {detectores_orfaos} novas deteccoes entrarao em acao.')

# Registra a correlacao no KG
if os.path.exists(KG_PATH):
    with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
        kg = json.load(f)
    
    kg['licoes'].append({
        'id': f'C{len(kg["licoes"])+1:04d}',
        'erro': f'{detectores_orfaos} detectores orfaos — gerados mas nunca integrados ao scan()',
        'causa': 'KG cresce mas deteccao nao melhora. Aprendizado sem aplicacao.',
        'solucao': 'Adicionar loop no scan() que descobre e chama automaticamente funcoes detectar_*',
        'ctx': 'meta_correlacao',
        'usos': 0,
    })
    
    kg['versoes'] += 1
    with open(KG_PATH, 'w', encoding='utf-8') as f:
        json.dump(kg, f, ensure_ascii=False, indent=2)
    print(f'\nCorrelacao registrada no KG. Total: {kg["metricas"]["licoes"]} licoes')
