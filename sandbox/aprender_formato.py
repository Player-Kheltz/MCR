"""MCR-DevIA: formato diferente = aprender, nao ignorar"""
import json, os

path = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    kg = json.load(f)

# Le o formato REAL do mcr_ultimate.py
ult_path = r'E:\Projeto MCR\sandbox\mcr_ultimate.py'
with open(ult_path, 'r', encoding='utf-8', errors='replace') as f:
    conteudo = f.read()

# Detecta o formato real
formatos = {}
for tipo in ['npc', 'monster', 'item', 'quest', 'spell']:
    marker = f"'{tipo}':"
    if marker in conteudo:
        idx = conteudo.find(marker)
        snippet = conteudo[idx:idx+500]
        
        # Detecta o formato
        if "'template': '" in snippet:
            formato = 'string_simples'
        elif "'template':" in snippet and 'f"' in snippet:
            formato = 'f-string'
        elif "'template':" in snippet:
            formato = 'string_multi_linha'
        else:
            formato = 'formato_desconhecido'
        
        formatos[tipo] = formato

# Se algum template mudou de formato, registra
if formatos:
    licao = {
        'id': f'S{len(kg["licoes"])+1:04d}',
        'erro': 'Formato dos templates no mcr_ultimate.py mudou',
        'causa': 'O arquivo foi reescrito entre versoes e os templates mudaram de formato',
        'solucao': 'Formatos detectados: ' + ', '.join(f'{t}={f}' for t, f in formatos.items()),
        'ctx': 'meta_aprendizado',
        'usos': 0,
    }
    kg['licoes'].append(licao)
    kg['versoes'] += 1
    kg['metricas']['licoes'] = len(kg['licoes'])
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(kg, f, ensure_ascii=False, indent=2)

print(f'Licao registrada! Total: {kg["metricas"]["licoes"]} licoes')
print(f'\nFormatos detectados no mcr_ultimate.py:')
for tipo, formato in formatos.items():
    print(f'  {tipo}: {formato}')
print(f'\nNada foi perdido. O MCR-DevIA agora SABE o formato real.')
print(f'Na proxima tentativa de reparo, ele ja conhece o formato.')
