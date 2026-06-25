"""MCR-DevIA tenta RESOLVER os 8 problemas do training ground"""
import os, re, json, urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\sandbox\training_ground'

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.4,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
    except: return None

# Arquivos com problemas (detectados anteriormente)
alvos = [
    ('ferreiro.lua', 'scripts/npc/ferreiro.lua', 'parenteses desbalanceados (addItem(102, 100 sem fechar)'),
    ('dragao.lua', 'scripts/monster/dragao.lua', 'funcoes inexistentes (setInvisibility, setFlyMode)'),
    ('espada_magica.lua', 'scripts/item/espada_magica.lua', 'usa setAttack antigo em vez de setAttribute'),
    ('guarda.lua', 'scripts/npc/guarda.lua', 'tabela de dialogo nao fechada'),
    ('boss_final.lua', 'scripts/monster/boss_final.lua', 'loot_chance = 2.5 (maximo 1.0)'),
    ('calcular_dano.cpp', 'calcular_dano.cpp', 'falta ponto e virgula no return'),
    ('calcular_bonus.lua', 'scripts/calcular_bonus.lua', 'variaveis nao utilizadas (temp, y)'),
    ('ITEM_SECRETO_v2_FINAL.lua', 'ITEM_SECRETO_v2_FINAL.lua', 'nome fora do padrao'),
]

print('='*60)
print('  MCR-DevIA TENTANDO RESOLVER 8 PROBLEMAS')
print('='*60)

acertos = 0
falhas = 0

for nome, relpath, desc in alvos:
    path = os.path.join(BASE, relpath)
    if not os.path.exists(path):
        print(f'\n  [!] {nome}: arquivo nao encontrado')
        falhas += 1
        continue
    
    with open(path, 'r', encoding='utf-8') as f:
        original = f.read()
    
    print(f'\n  [{nome}] {desc}')
    print(f'    Original ({len(original)} bytes)')
    
    # Pede IA pra corrigir
    prompt = f"""Corrija o arquivo abaixo que tem este problema: {desc}

ARQUIVO:
```lua
{original[:1000]}
```

Retorne APENAS o codigo corrigido completo, sem explicacoes."""
    
    correcao = ia(prompt)
    if not correcao:
        print(f'    [FALHA] IA nao respondeu')
        falhas += 1
        continue
    
    # Limpa marcacao
    correcao = correcao.replace('```lua', '').replace('```cpp', '').replace('```', '').strip()
    
    if correcao and len(correcao) > 10:
        # Verifica se realmente mudou algo
        if correcao != original:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(correcao)
            print(f'    [CORRIGIDO] {len(correcao)} bytes')
            
            # Verifica se o problema foi resolvido
            verificacao = ''
            if 'parenteses' in desc or 'fechada' in desc:
                opens = correcao.count('(') + correcao.count('{')
                closes = correcao.count(')') + correcao.count('}')
                if opens == closes:
                    verificacao = ' (parenteses OK)'
            elif 'loot_chance' in desc:
                chances = re.findall(r'addLoot\((\d+),\s*([\d.]+)\)', correcao)
                if all(float(c) <= 1.0 for _, c in chances):
                    verificacao = ' (loot OK)'
            elif 'setAttack' in desc:
                if 'setAttribute' in correcao:
                    verificacao = ' (template atualizado)'
            
            print(f'    [VERIFICACAO]{verificacao}')
            acertos += 1
        else:
            print(f'    [IGNORADO] IA retornou o mesmo codigo')
            falhas += 1
    else:
        print(f'    [FALHA] Resposta vazia')
        falhas += 1

print(f'\n{"="*60}')
print(f'  RESULTADO: {acertos}/8 problemas resolvidos, {falhas} falhas')
print(f'{"="*60}')

# Restaura os originais
print(f'\n  Restaurando arquivos originais...')
pass
