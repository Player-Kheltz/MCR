"""Registra avaliacoes do Cloud e calcula gaps."""
import json

path = r'E:/Projeto MCR/sandbox/autoteste_historico.json'
with open(path, 'r', encoding='utf-8') as f:
    h = json.load(f)

# Notas do Cloud (cegas, sem ver auto-critica)
avaliacoes_cloud = [5, 5, 3, 0, 0]

testes = h['ciclos'][0]['testes']
for i, nota in enumerate(avaliacoes_cloud):
    testes[i]['cloud_nota'] = nota
    auto = testes[i]['auto_critica']['nota']
    testes[i]['gap'] = abs(nota - auto)

with open(path, 'w', encoding='utf-8') as f:
    json.dump(h, f, ensure_ascii=False, indent=2)

print('Gaps registrados:')
print('  Pergunta                          Auto  Cloud   Gap')
print('  ' + '-' * 48)
for i, t in enumerate(testes):
    auto = t['auto_critica']['nota']
    cloud = t['cloud_nota']
    gap = t['gap']
    alerta = ' PONTO CEGO' if gap > 2 else ''
    print(f'  {t["categoria"]:15s}      {auto:3d}    {cloud:3d}   {gap:3d}{alerta}')

gaps = [t['gap'] for t in testes]
print('  ' + '-' * 48)
print(f'  GAP MEDIO:                       {sum(gaps)/len(gaps):.1f}')
