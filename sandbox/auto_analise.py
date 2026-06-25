"""Ensinar MCR-DevIA a se auto-analisar antes de se auto-reparar"""
import json, os

path = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    kg = json.load(f)

licao = {
    'id': f'S{len(kg["licoes"])+1:04d}',
    'erro': 'Reparo falhou porque tentei editar meu proprio arquivo sem entender o formato dele primeiro',
    'causa': 'Auto-reparo tentou encontrar templates com regex de string simples, mas o arquivo usa f-strings multi-linha',
    'solucao': 'Antes de editar um arquivo, primeiro LEIA ele para entender o formato. Depois adapte a edicao ao formato real. Use a mesma funcao de leitura para encontrar e para editar.',
    'ctx': 'meta_aprendizado',
    'usos': 0,
}

kg['licoes'].append(licao)
kg['versoes'] += 1
kg['metricas']['licoes'] = len(kg['licoes'])

with open(path, 'w', encoding='utf-8') as f:
    json.dump(kg, f, ensure_ascii=False, indent=2)

print(f'Licao adicionada! Total: {kg["metricas"]["licoes"]} licoes')

# Agora demonstra: lendo o proprio formato
print('\n--- MCR-DevIA se auto-analisando ---')
print('\nLendo o formato REAL dos templates no mcr_ultimate.py:')
with open(os.path.join(os.path.dirname(path), '..', 'mcr_ultimate.py'), 'r', encoding='utf-8', errors='replace') as f:
    conteudo = f.read()

# Mostra como os templates realmente estao formatados
import re
for tipo in ['npc', 'monster', 'item']:
    m = re.search(r"'" + tipo + r"':\s*\{\s*'template':\s*'([^']+)'", conteudo, re.DOTALL)
    if m:
        print(f'  {tipo}: encontrado no formato esperado (string simples)')
    else:
        print(f'  {tipo}: NAO encontrado no formato esperado')
        # Tenta encontrar de forma alternativa
        idx = conteudo.find(f"'{tipo}':")
        if idx > 0:
            snippet = conteudo[idx:idx+200]
            print(f'    Trecho encontrado: {snippet[:120]}...')
            print(f'    Formato real: f-string multi-linha (diferente do esperado)')
            print(f'    Licao: sempre ler antes de editar!')
