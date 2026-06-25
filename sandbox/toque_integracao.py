"""Toque no ombro do MCR-DevIA"""
import json, os

KG_PATH = r'E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json'

print('=== TOQUE NO OMBRO ===')
print()
print('MCR-DevIA, voce gerou 8 detectores novos nos ultimos 5 ciclos.')
print('Mas o scan() nunca os chama. Eles estao orfaos.')
print('O KG cresceu 8 licoes. Mas a deteccao continua 5/12.')
print()
print('O problema nao e GERAR conhecimento.')
print('O problema e INTEGRAR o conhecimento no proprio funcionamento.')
print()
print('Sugestao: no final do scan(), procure por funcoes detectar_*')
print('definidas no mesmo arquivo e EXECUTE elas automaticamente.')
print()

# Registra no KG
if os.path.exists(KG_PATH):
    with open(KG_PATH, 'r', encoding='utf-8', errors='replace') as f:
        kg = json.load(f)
    
    kg['licoes'].append({
        'id': f'D{len(kg["licoes"])+1:04d}',
        'erro': 'Detectores gerados mas nunca chamados pelo scan()',
        'causa': 'Auto-aprendizado cria funcoes detectoras mas nao as integra no fluxo principal',
        'solucao': 'No final do scan(), procurar por funcoes detectar_* no proprio modulo e chama-las para cada arquivo. Assim novos detectores sao automaticamente usados.',
        'ctx': 'auto_integracao',
        'usos': 0,
    })
    
    kg['versoes'] += 1
    with open(KG_PATH, 'w', encoding='utf-8') as f:
        json.dump(kg, f, ensure_ascii=False, indent=2)
    
    print(f'Licao registrada no KG. Total: {kg["metricas"]["licoes"]} licoes')
