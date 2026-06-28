#!/usr/bin/env python3
"""Analisa todos os except: genericos no projeto e classifica por gravidade."""
import os, re

BASE = r'E:\Projeto MCR'

print('='*80)
print('ANALISE DE except: GENERICOS NO PROJETO')
print('='*80)

resultados = []

for root, dirs, files in os.walk(BASE):
    skip = {'.git', '__pycache__', 'node_modules', 'vcpkg', '.vcpkg',
            'bin', 'obj', 'build', '.cmake', 'localStorage', '.mcr_devia',
            'autogerados', 'raw', 'fragments', 'narratives', 'Downloads',
            'ArquivosComplementares'}
    dirs[:] = [d for d in dirs if d not in skip and not d.startswith('.')]
    
    for f in files:
        if not f.endswith('.py'): continue
        fpath = os.path.join(root, f)
        rel = os.path.relpath(fpath, BASE)
        
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                lines = fh.readlines()
        except: continue
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Procura "except:" (bare except) OU "except :" 
            if re.match(r'^except\s*:', stripped) or stripped == 'except:':
                # Pega contexto (5 linhas ao redor)
                ctx_start = max(0, i-2)
                ctx_end = min(len(lines), i+3)
                ctx = ''.join(lines[ctx_start:ctx_end])
                
                # Classifica gravidade
                if 'pass' in stripped:
                    gravidade = 'BAIXO'
                    motivo = 'Apenas ignorando erro (silencioso)'
                elif 'print' in stripped or 'log' in stripped:
                    gravidade = 'MEDIO'
                    motivo = 'Logando mas sem tratamento especifico'
                elif 'return' in stripped:
                    gravidade = 'MEDIO'
                    motivo = 'Retornando valor padrao em erro'
                else:
                    gravidade = 'ALTO'
                    motivo = 'Comportamento indefinido em erro'
                
                resultados.append({
                    'arquivo': rel,
                    'linha': i+1,
                    'gravidade': gravidade,
                    'motivo': motivo,
                    'codigo': stripped[:80],
                    'ctx': ctx[:200],
                })

# Agrupa por gravidade
print(f'\nTotal de except: genericos encontrados: {len(resultados)}')

for grav in ['ALTO', 'MEDIO', 'BAIXO']:
    items = [r for r in resultados if r['gravidade'] == grav]
    if not items: continue
    print(f'\n## Gravidade {grav} ({len(items)} ocorrencias)')
    print(f'{"Arquivo":50s} {"Linha":6s} {"Codigo":30s}')
    print('-'*86)
    for r in items:
        print(f'{r["arquivo"][:48]:50s} {r["linha"]:6d} {r["codigo"][:28]:30s}')

# Scripts com mais ocorrencias
print(f'\n\n## Scripts com mais except: genericos:')
from collections import Counter
contagem = Counter(r['arquivo'] for r in resultados)
for arquivo, count in contagem.most_common(15):
    graus = [r['gravidade'] for r in resultados if r['arquivo'] == arquivo]
    alertas = sum(1 for g in graus if g == 'ALTO')
    alerta_str = f' ({alertas} ALTO)' if alertas else ''
    print(f'  {arquivo:50s} {count:2d} excepts{alerta_str}')

print(f'\n\n## Recomendacao:')
print(f'  Substituir "except:" por "except Exception as e:"')
print(f'  Adicionar tratamento minimo: logging, print, ou raise')
print(f'  Ex: except Exception as e: print(f\"[ERRO] {e}\")')
