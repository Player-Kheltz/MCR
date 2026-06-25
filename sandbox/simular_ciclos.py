"""Simular ciclos de aprendizado do MCR-DevIA"""
import subprocess, sys, os

SCANNER = r'E:\Projeto MCR\sandbox\resolver_ultra.py'
LEARNER = r'E:\Projeto MCR\sandbox\auto_aprender_detector.py'
KG_PATH = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'

def contar_detectados(output):
    """Conta quantos problemas foram detectados."""
    lines = output.split('\n')
    detectados = 0
    for line in lines:
        if line.strip().startswith('RESULTADO:'):
            # Extrai: RESULTADO: X/12 arquivos com problemas detectados
            import re
            m = re.search(r'(\d+)/(\d+)', line)
            if m:
                detectados = int(m.group(1))
    return detectados

def contar_licoes():
    """Conta licoes no KG."""
    import json
    if os.path.exists(KG_PATH):
        with open(KG_PATH, 'r', encoding='utf-8') as f:
            kg = json.load(f)
        return len(kg.get('licoes', [])), kg.get('versoes', 0)
    return 0, 0

print('='*60)
print('  SIMULACAO DE CICLOS DE APRENDIZADO')
print('  MCR-DevIA aprendendo sozinho')
print('='*60)

historico = []

for ciclo in range(1, 6):
    print(f'\n{"="*60}')
    print(f'  CICLO {ciclo}')
    print(f'{"="*60}')
    
    # 1. Scanner
    print(f'\n  [SCAN] Executando scanner...')
    r = subprocess.run([sys.executable, SCANNER], capture_output=True, text=True, timeout=300)
    detectados = contar_detectados(r.stdout)
    licoes, versao = contar_licoes()
    
    print(f'  Detectados: {detectados}/12')
    print(f'  KG: {licoes} licoes, V{versao}')
    
    # 2. Auto-aprendizado (se perdeu algo)
    perdidos = 12 - detectados
    if perdidos > 0:
        print(f'  [APRENDER] Gerando detectores para {perdidos} problemas perdidos...')
        r2 = subprocess.run([sys.executable, LEARNER], capture_output=True, text=True, timeout=120)
        
        # Conta quantos detectores foram gerados
        gerados = r2.stdout.count('[GERADO]')
        print(f'  Detectores gerados: {gerados}')
    else:
        print(f'  [APRENDER] Nada a aprender! Todos os 12 detectados.')
    
    historico.append({
        'ciclo': ciclo,
        'detectados': detectados,
        'licoes': licoes,
        'versao': versao,
    })

print(f'\n{"="*60}')
print(f'  HISTORICO DE APRENDIZADO')
print(f'{"="*60}')
print(f'  {"Ciclo":>5} {"Detectados":>10} {"Licoes":>8} {"Versao":>8}')
print(f'  {"-"*35}')
for h in historico:
    print(f'  {h["ciclo"]:>5} {h["detectados"]:>5}/12 {h["licoes"]:>8} V{h["versao"]:>3}')

print(f'\n  Evolucao: {historico[0]["detectados"]}/12 -> {historico[-1]["detectados"]}/12')
print(f'  Licoes: {historico[0]["licoes"]} -> {historico[-1]["licoes"]}')
print(f'  Aprendizado liquido: +{historico[-1]["licoes"] - historico[0]["licoes"]} licoes')
print(f'{"="*60}')
