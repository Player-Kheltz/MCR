"""Teste completo Deepseek R1 - raw=false, num_predict=8192"""
import json, urllib.request, time

def testar(prompt, nome):
    payload = json.dumps({
        'model': 'deepseek-r1:7b',
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0.3, 'num_predict': 8192}
    }).encode()
    inicio = time.time()
    req = urllib.request.Request(
        'http://localhost:11434/api/generate',
        data=payload, headers={'Content-Type': 'application/json'}
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=300).read())
    r = resp.get('response', '')
    elapsed = time.time() - inicio
    tokens = resp.get('eval_count', 0)
    tok_s = round(tokens / (resp.get('eval_duration', 1)/1e9), 1)
    
    print(f'\n=== {nome} ===')
    print(f'Tempo: {elapsed:.1f}s | Tokens: {tokens} | Tok/s: {tok_s}')
    
    # Salvar
    path = f'sandbox/testes_modelos/deepseek_v2_{nome.lower().replace(" ","_")}.txt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'PROMPT: {prompt}\n\nRESPOSTA:\n{r}')
    print(f'Salvo em: {path}')
    
    # Amostra
    print(f'Tamanho: {len(r)} chars')
    print(f'Primeiros 300 chars: {r[:300]}')
    return {'resposta': r, 'tokens': tokens, 'tempo': elapsed, 'tok_s': tok_s}

# Teste 1: Raciocinio logico (deve gerar thinking + resposta util)
r1 = testar(
    "Explain the concept of CAP theorem in simple terms. Give a concrete example for an MMORPG server.",
    "CAP Theorem"
)

# Teste 2: Review de codigo (deve encontrar bug)
r2 = testar(
    """Find the bug in this code:
function withdraw(player, amount)
    local balance = player:getBalance()
    if balance >= amount then
        player:setBalance(balance - amount)
        player:addItem(2148, amount)
        return true
    end
    return false
end
What happens if amount is negative?""",
    "Code Review"
)

# Teste 3: Codigo (deve conseguir gerar com espaco para pensar)
r3 = testar(
    "Write a Python function to check if a number is prime. Include comments.",
    "Python Code"
)

# Resumo
print('\n\n=== RESUMO DEEPSEEK R1 ===')
for nome, r in [('CAP Theorem', r1), ('Code Review', r2), ('Python Code', r3)]:
    util = len(r['resposta']) > 50
    print(f'{nome}: {len(r["resposta"])} chars em {r["tempo"]:.1f}s ({r["tok_s"]} tok/s) - {"UTIL" if util else "CURTA DEMAIS"}')
