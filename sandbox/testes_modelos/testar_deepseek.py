"""
TESTE REAL DEEPSEEK R1 - Com configuracao correta (raw:true, num_predict:8192)
Data: 27/06/2026
Objetivo: Verificar se o Deepseek R1 e viavel para uso no MCR-DevIA
Testa 3 cenarios onde ele pode ser superior aos outros modelos.
"""

import json, time, os, urllib.request, urllib.error

OLLAMA_URL = "http://localhost:11434/api/generate"
PASTA = os.path.dirname(os.path.abspath(__file__))

CONFIG_CERTA = {
    "model": "deepseek-r1:7b",
    "stream": False,
    "options": {
        "temperature": 0.3,
        "num_predict": 8192,
        "raw": True  # ESSENCIAL: sem template de chat
    }
}

CONFIG_ERRADA = {
    "model": "deepseek-r1:7b",
    "stream": False,
    "options": {
        "temperature": 0.3,
        "num_predict": 2048,
        # sem raw: true (usa template de chat padrao)
    }
}

TESTES = [
    {
        "id": "debug_codigo",
        "titulo": "REVIEW/DEBUG - Encontrar bug em codigo Lua",
        "config": "CERTA",
        "prompt": """Find the bug in this Lua function for an OTServ (Tibia server). The function is supposed to give a reward to a player when they kill a boss, but sometimes it gives the reward twice.

```lua
function onKillBoss(cid, bossName)
    local player = Player(cid)
    if not player then return false end
    
    local storage = 50001
    local killTime = player:getStorageValue(storage)
    
    if killTime > 0 and (os.time() - killTime) < 3600 then
        return false  -- Already killed in last hour
    end
    
    player:setStorageValue(storage, os.time())
    player:addItem(2152, 10)  -- 10 gold coins
    player:addItem(2491, 1)   -- Boss trophy
    
    if math.random(1, 100) <= 20 then
        player:addItem(2387, 1)  -- Rare item (20% chance)
    end
    
    player:sendTextMessage(MESSAGE_INFO_DESCR, "You killed " .. bossName .. "! Reward received.")
    return true
end
```

Analyze the code and tell me:
1. What is the bug?
2. Why does it happen?
3. How to fix it?
4. Show the corrected code."""
    },
    {
        "id": "raciocinio_logico",
        "titulo": "RACIOCINIO LOGICO - Otimizacao de spawn de mobs",
        "config": "CERTA",
        "prompt": """Problem: An OTServ has 500 monsters in a spawn area. Each monster has:
- A respawn time of 60 seconds after death
- 30% chance to drop a quest item when killed
- Players kill monsters at an average rate of 2 per second (total across all players)

The server uses a naive algorithm: every second, it checks each dead monster and respawns it if 60 seconds have passed.

Question 1: What is the Big-O complexity of this algorithm?
Question 2: How can we optimize this to O(1) or O(log n)?
Question 3: Propose a better data structure for managing respawns.
Question 4: Show pseudocode for the optimized version.

Think step by step. Show your reasoning before the answer."""
    },
    {
        "id": "planejamento",
        "titulo": "PLANEJAMENTO - Cache hierarchy design",
        "config": "CERTA",
        "prompt": """Design a cache hierarchy for an OTServ (Tibia MMO server) with these requirements:

- 2000 concurrent players
- Each player has inventory (50-200 items), stats, position, quest progress
- World data: 50000+ monsters, 10000+ items, 500+ NPCs, 100+ maps
- Operations: 5000 reads/sec, 500 writes/sec at peak
- Max response time: 50ms for player operations
- RAM limit: 16GB for cache

Consider:
1. What data should be cached vs persisted?
2. What cache layers (L1, L2, L3) make sense?
3. What invalidation strategy?
4. Redis vs in-memory vs disk?

Provide a concrete architecture with pros and cons of each decision.
Think through the trade-offs carefully."""
    },
    {
        "id": "ptbr_simples",
        "titulo": "PT-BR SIMPLES - Traducao de mensagens do jogo",
        "config": "CERTA",
        "prompt": "Traduza estas mensagens de jogo do ingles para o portugues brasileiro:\n\n1. 'You have found a secret passage!'\n2. 'Your equipment is too heavy.'\n3. 'This spell requires level 45.'\n4. 'The dragon lord casts a powerful fireball at you!'\n5. 'You cannot attack while in protection zone.'\n\nResponda APENAS com as traducoes, uma por linha."
    },
    {
        "id": "deep_vs_2048",
        "titulo": "CONTROLE - Mesmo teste de codigo que falhou antes (agora com config certa)",
        "config": "CERTA",
        "prompt": "Create a Python function to validate Brazilian CPF. The function should:\n1. Receive a CPF string (with or without punctuation)\n2. Remove non-numeric characters\n3. Validate check digits\n4. Return True/False\n5. Include usage examples\n\nRespond with ONLY the Python code, well commented."
    },
    {
        "id": "teste_2048_sem_raw",
        "titulo": "CONTROLE - Teste com config ERRADA (2048 tokens, sem raw)",
        "config": "ERRADA",
        "prompt": "Create a Python function to validate Brazilian CPF. The function should:\n1. Receive a CPF string (with or without punctuation)\n2. Remove non-numeric characters\n3. Validate check digits\n4. Return True/False\n5. Include usage examples"
    }
]


def consultar(config, prompt, timeout=300):
    """Chama o Ollama com config especifica."""
    payload = dict(config)  # copia
    payload["prompt"] = prompt
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    inicio = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            dados = json.loads(raw)
        elapsed = time.time() - inicio
        resposta = dados.get("response", "")
        tokens = dados.get("eval_count", 0)
        eval_dur = dados.get("eval_duration", 0) / 1e9
        tok_s = round(tokens / eval_dur, 1) if eval_dur > 0 else 0
        
        # Tentar extrair a resposta final (depois de <｜end▁of▁thinking｜>)
        resposta_final = resposta
        if "<THINKING>" in resposta:
            # Marcador de thinking pode variar
            pass
        
        # Deepseek coloca thinking entre  e 
        partes = resposta.split("")
        if len(partes) >= 3:
            thinking = partes[1]
            resposta_final = "".join(partes[2:])
        elif len(partes) == 2:
            resposta_final = partes[1]
        else:
            resposta_final = resposta
        
        return {
            "resposta_bruta": resposta,
            "resposta_final": resposta_final.strip() if resposta_final.strip() else "(vazio - apenas thinking tokens)",
            "thinking": partes[1] if len(partes) >= 3 else "(sem thinking visivel)",
            "tempo": round(elapsed, 1),
            "tokens": tokens,
            "tok_s": tok_s,
            "caracteres_bruto": len(resposta),
            "caracteres_final": len(resposta_final.strip()),
            "erro": None
        }
    except Exception as e:
        return {"resposta_bruta": "", "resposta_final": f"[ERRO] {e}",
                "thinking": "", "tempo": round(time.time()-inicio, 1),
                "tokens": 0, "tok_s": 0, "caracteres_bruto": 0,
                "caracteres_final": 0, "erro": str(e)}


def salvar(teste_info, resultado):
    """Salva resultado em arquivo."""
    cfg_tipo = teste_info["config"]
    nome = f"deepseek_{teste_info['id']}_{cfg_tipo.lower()}.txt"
    caminho = os.path.join(PASTA, nome)
    
    # Separa thinking da resposta para analise
    has_thinking = resultado["caracteres_final"] > 0 and resultado["caracteres_final"] < resultado["caracteres_bruto"]
    
    conteudo = f"""========================================
TESTE DEEPSEEK R1 - {teste_info['titulo']}
CONFIG: {teste_info['config']}
DATA: 27/06/2026
========================================

PROMPT:
{teste_info['prompt']}

----------------------------------------
THINKING TOKENS:
----------------------------------------
{resultado['thinking'] if has_thinking else "(sem thinking tokens detectados - resposta direta)"}

----------------------------------------
RESPOSTA FINAL ({resultado['caracteres_final']}c):
----------------------------------------
{resultado['resposta_final']}

----------------------------------------
RESPOSTA BRUTA COMPLETA ({resultado['caracteres_bruto']}c):
----------------------------------------
{resultado['resposta_bruta']}

----------------------------------------
METRICAS:
----------------------------------------
Tempo total: {resultado['tempo']}s
Tokens gerados: {resultado['tokens']}
Tokens/segundo: {resultado['tok_s']}
Caracteres (bruto): {resultado['caracteres_bruto']}
Caracteres (final): {resultado['caracteres_final']}
Thinking tokens: {resultado['caracteres_bruto'] - resultado['caracteres_final']}c
Resposta util: {'SIM' if resultado['caracteres_final'] > 50 else 'NAO'}
Erro: {resultado['erro'] if resultado['erro'] else 'Nenhum'}
"""
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"  [+] Salvo: {caminho}")
    return caminho


def main():
    print("=" * 70)
    print(" TESTE REAL DEEPSEEK R1")
    print(" Config: raw=true, num_predict=8192")
    print("=" * 70)
    print(f"\nTestes: {len(TESTES)}")
    
    for test in TESTES:
        cfg = CONFIG_CERTA if test["config"] == "CERTA" else CONFIG_ERRADA
        print(f"\n--- {test['titulo']} ({test['config']}) ---")
        print(f"  Modelo: {cfg['model']}, raw={cfg['options'].get('raw', False)}, num_predict={cfg['options']['num_predict']}")
        print(f"  Consultando...")
        
        resultado = consultar(cfg, test["prompt"])
        
        if resultado["erro"]:
            print(f"  [ERRO] {resultado['erro']}")
        else:
            print(f"  [OK] Bruto: {resultado['caracteres_bruto']}c | Util: {resultado['caracteres_final']}c | Tempo: {resultado['tempo']}s")
            print(f"  Thinking: {resultado['caracteres_bruto'] - resultado['caracteres_final']}c")
            
            if resultado["caracteres_final"] < 50:
                print(f"  ⚠️ Resposta util MUITO CURTA ou vazia!")
        
        salvar(test, resultado)
        
        # Preview da resposta util
        preview = resultado["resposta_final"][:200].replace("\n", " ")
        try:
            print(f"  Resposta: {preview}...")
        except:
            pass
    
    # Relatorio final
    print(f"\n\n{'='*70}")
    print(" RELATORIO FINAL")
    print(f"{'='*70}")
    
    for test in TESTES:
        nome = f"deepseek_{test['id']}_{test['config'].lower()}.txt"
        if os.path.exists(os.path.join(PASTA, nome)):
            # Le as metricas do arquivo
            with open(os.path.join(PASTA, nome), "r", encoding="utf-8") as f:
                conteudo = f.read()
            # Extrai metricas
            util = "NAO"
            for line in conteudo.split("\n"):
                if "Resposta util:" in line:
                    util = line.split(":")[1].strip()
                if "Caracteres (final):" in line:
                    try:
                        c_final = int(line.split(":")[1].strip())
                    except:
                        c_final = 0
                if "Tempo total:" in line:
                    try:
                        tempo = line.split(":")[1].strip().rstrip('s')
                    except:
                        tempo = "?"
            
            status = "✅ UTIL" if util == "SIM" else "❌ FALHOU"
            print(f"  {test['titulo']:<50} {status}")
    
    print(f"\nResultados salvos em: {PASTA}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
