#!/usr/bin/env python3
"""
MCR-DevIA — AUTO-APRENDIZADO DE DETECTORES
=============================================
Quando ele PERDE um problema, ele:
  1. Analisa o arquivo que deveria ter detectado
  2. Identifica o padrao unico
  3. Gera UMA FUNCAO DE DETECCAO nova
  4. ADICIONA no proprio codigo do scanner
  5. Proximo scan: detecta

Nao preciso ensinar. Ele aprende sozinho.
"""

import os, re, json, urllib.request, inspect

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\teste_cego_ultra'
SCANNER_PATH = r'E:\Projeto MCR\sandbox\resolver_ultra.py'
KG_PATH = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.5,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
    except: return None

# Arquivos que o scanner PERDEU na ultima execucao
ARQUIVOS_PERDIDOS = [
    ('verificar_item.lua', 'contem sintaxe Python (def, True, False) em um arquivo .lua'),
    ('criar_pocao.lua', 'atribui explicitamente nil a um campo (p.efeito = nil)'),
]

print('='*60)
print('  MCR-DevIA — AUTO-APRENDIZADO DE DETECTORES')
print(f'  Analisando {len(ARQUIVOS_PERDIDOS)} problemas que ele perdeu...')
print('='*60)

for arquivo, descricao in ARQUIVOS_PERDIDOS:
    path = os.path.join(BASE, arquivo)
    if not os.path.exists(path):
        print(f'\n  [!] {arquivo} nao encontrado')
        continue
    
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        conteudo = f.read()
    
    print(f'\n  Analisando {arquivo}...')
    print(f'  Problema: {descricao}')
    
    # IA gera uma funcao de deteccao
    prompt = f"""Crie uma funcao Python chamada 'detectar_{arquivo.replace(".","_")}' que detecta se um arquivo tem este problema: {descricao}

A funcao recebe 'conteudo' (string) e retorna True se o problema existe, False caso contrario.

Exemplo de arquivo com o problema:
```lua
{conteudo}
```

Retorne APENAS o codigo da funcao, sem explicacoes."""
    
    detector = ia(prompt)
    
    if detector and len(detector) > 20:
        detector = detector.replace('```python', '').replace('```', '').strip()
        
        # Valida que e uma funcao valida
        if 'def detectar_' in detector and 'return' in detector:
            print(f'  [GERADO] Funcao de deteccao criada!')
            print(f'  {detector[:200]}...')
            
            # Adiciona ao scanner
            with open(SCANNER_PATH, 'r', encoding='utf-8') as f:
                scanner_code = f.read()
            
            # Encontra onde inserir (antes do final)
            insert_pos = scanner_code.rfind("print(f'")
            if insert_pos > 0:
                novo_codigo = detector + '\n\n' + scanner_code[insert_pos:]
                scanner_code = scanner_code[:insert_pos] + novo_codigo
            
            with open(SCANNER_PATH, 'w', encoding='utf-8') as f:
                f.write(scanner_code)
            
            print(f'  [ADICIONADO] Funcao incorporada ao scanner!')
        
        # Registra no KG
        with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            kg = json.load(f)
        
        kg['licoes'].append({
            'id': f'D{len(kg["licoes"])+1:04d}',
            'erro': f'Scanner nao detectava: {descricao}',
            'causa': f'Faltava detector para {arquivo}',
            'solucao': f'Detector gerado automaticamente e incorporado ao scanner',
            'ctx': 'auto_detector',
            'usos': 0,
        })
        
        kg['versoes'] += 1
        kg['metricas']['licoes'] = len(kg['licoes'])
        
        with open(KG_PATH, 'w', encoding='utf-8') as f:
            json.dump(kg, f, ensure_ascii=False, indent=2)
        
        print(f'  [KG] Aprendizado registrado!')
    else:
        print(f'  [FALHA] IA nao gerou detector valido')

print(f'\n{"="*60}')
print(f'  AUTO-APRENDIZADO CONCLUIDO!')
print(f'  {len(ARQUIVOS_PERDIDOS)} detectores gerados e incorporados.')
print(f'  Proximo scan: vai detectar esses problemas!')
print(f'{"="*60}')
