import json
with open('tests/experimento_rigoroso/dataset_500.json','r',encoding='utf-8') as f:
    dados = json.load(f)
for d in dados:
    if 'pocao' in d['input'].lower() or 'machado' in d['input'].lower() or 'vida' in d['input'].lower():
        print(f'  input="{d["input"]}" | expected={d["expected_action"]}')
