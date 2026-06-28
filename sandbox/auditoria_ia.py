"""Auditoria: encontrar todas as chamadas de IA e classificar como:
- [IA] = precisa de IA (geracao, interpretacao)
- [V12] = Python estrutura + IA preenche (pode ser otimizado)
- [PY] = pode virar Python puro

Depois aplicar as substituicoes [PY] e [V12] automaticamente.
"""
import re, ast

code = open("E:\\Projeto MCR\\scripts\\mcr_devia\\mcr_devia.py", encoding="utf-8").read()
linhas = code.split('\n')

print("=" * 70)
print("AUDITORIA DE CHAMADAS DE IA NO MCR-DEVIA")
print("=" * 70)

# Encontrar todas as chamadas de IA
padroes = [
    (r'self\.ia\.gerar\(', 'IA.gerar()'),
    (r'fast\(', 'fast()'),
    (r'\.Request\(OLLAMA_URL', 'API direta Ollama'),
    (r'kg\.aprender\(', 'KG.aprender() (registro, nao chamada)'),
]

resultados = []
for i, line in enumerate(linhas, 1):
    for padrao, nome in padroes:
        if re.search(padrao, line):
            line_strip = line.strip()
            resultados.append((i, nome, line_strip[:100]))
            break

print(f"\nTotal de chamadas: {len(resultados)}\n")

# Classificar cada chamada
print(f"{'Linha':<6} {'Tipo':<8} {'Contexto':<50}")
print("-" * 64)

substituicoes = []  # (linha, tipo, descricao)

for linha, tipo, ctx in resultados:
    # Classificar
    if tipo == 'KG.aprender() (registro, nao chamada)':
        classificacao = 'REG'
    elif 'compilar' in ctx.lower() or 'msbuild' in ctx.lower():
        classificacao = 'PY'  # Já é Python
    elif 'genero' in ctx.lower() or 'genero' in ctx.lower():
        classificacao = 'PY'  # Já substituído
    elif 'extract' in ctx.lower() and 'dados' in ctx.lower():
        classificacao = 'V12'
    elif 'review' in ctx.lower() and 'item' in ctx.lower():
        classificacao = 'V12'
    elif 'avaliacao' in ctx.lower() or 'avaliaca' in ctx.lower():
        classificacao = 'V12'  # Pode ser regra
    elif 'gerar' in ctx.lower() and ('npc' in ctx.lower() or 'monster' in ctx.lower()):
        classificacao = 'IA'  # Geração criativa
    elif 'perguntar' in ctx.lower() or 'supervisor' in ctx.lower():
        classificacao = 'IA'  # QA com KG
    elif 'analisar' in ctx.lower() or 'codigo' in ctx.lower():
        classificacao = 'V12'  # Já tem AST
    elif 'fast(' in ctx.lower() and 'v12' not in ctx.lower():
        classificacao = 'V12'  # Classificação com fallback
    else:
        classificacao = 'IA'
    
    print(f"{linha:<6} {classificacao:<8} {ctx[:50]}")
    
    if classificacao in ('PY', 'V12'):
        substituicoes.append((linha, classificacao, ctx))

print(f"\n\n=== SUBSTITUICOES POSSIVEIS: {len(substituicoes)} ===")
print(f"\n{'Linha':<6} {'Tipo':<8} {'Acao':<50}")
print("-" * 64)
for linha, tipo, ctx in substituicoes:
    print(f"{linha:<6} {tipo:<8} {ctx[:50]}")
