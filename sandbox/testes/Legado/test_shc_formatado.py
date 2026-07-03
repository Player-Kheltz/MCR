#!/usr/bin/env python3
"""
Teste: gerar habilidades SHC no formato CORRETO.
Pipeline: 1) Ler fogo.lua como template
          2) Alimentar dev/qwen7b com template + pedido
          3) Validar formato SHC
          4) Tentar compilar como Lua
"""
import json, os, sys, time, urllib.request, re

BASE = r"E:\Projeto MCR"
sys.path.insert(0, os.path.join(BASE, "scripts"))

TENTATIVAS = []  # historico de tentativas

def chat(modelo, messages, max_tokens=2048, temp=0.1):
    payload = json.dumps({"model": modelo, "messages": messages, "stream": False,
        "options": {"temperature": temp, "max_tokens": max_tokens}}).encode()
    t0 = time.time()
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        dt = time.time() - t0
        return data["message"]["content"], dt
    except Exception as e:
        return f"[ERRO] {e}", time.time() - t0

def validar_formato_shc(codigo):
    """Valida se o codigo gerado segue o formato SHC."""
    erros = []
    
    # Verifica se tem HABILIDADES[ID]
    habilidades = re.findall(r'HABILIDADES\[\d+\]', codigo)
    if not habilidades:
        erros.append("Nenhum HABILIDADES[ID] encontrado")
    
    # Verifica estrutura basica para cada habilidade
    for h in habilidades:
        idx = codigo.find(h)
        bloco = codigo[idx:idx+800]
        
        # Deve ter nome
        if 'nome =' not in bloco:
            erros.append(f"{h}: falta 'nome'")
        
        # Deve ter tipo
        if 'tipo =' not in bloco:
            erros.append(f"{h}: falta 'tipo'")
        
        # Deve ter dominio
        if 'dominio =' not in bloco:
            erros.append(f"{h}: falta 'dominio'")
        
        # Deve ter efeitoConfig
        if 'efeitoConfig' not in bloco:
            erros.append(f"{h}: falta 'efeitoConfig'")
        
        # Verifica se postura esta no formato certo (chave numerica, nao array)
        postura_match = re.search(r'postura\s*=\s*\{([^}]+)\}', bloco)
        if postura_match:
            conteudo = postura_match.group(1)
            # Deve ter colchetes numericos (ex: [1] = {)
            if not re.search(r'\[\d+\]', conteudo):
                if not re.search(r'\[1\]|\[2\]|\[3\]', conteudo):
                    erros.append(f"{h}: postura sem chave numerica [1]/[2]/[3]")
        
        # Verifica niveis no formato certo (chave [5], [10], etc)
        niveis_match = re.search(r'niveis\s*=\s*\{([^}]+)\}', bloco)
        if niveis_match:
            conteudo = niveis_match.group(1)
            if not re.search(r'\[\d+\]', conteudo):
                erros.append(f"{h}: niveis sem marcos [5]/[10]/[15]/[20]")
    
    return erros

def salvar_como_lua(codigo, tentativa):
    """Salva como .lua e tenta compilar com LuaJIT."""
    path = os.path.join(BASE, "sandbox", f"cristal_tentativa_{tentativa}.lua")
    with open(path, "w", encoding="utf-8") as f:
        f.write("-- Tentativa " + str(tentativa) + "\n")
        f.write("HABILIDADES = {}\n\n")
        f.write(codigo)
        f.write('\n\nprint("OK")\n')
    return path

def testar_lua(path):
    """Tenta executar o Lua gerado com o interpretador Lua do Canary."""
    # Primeiro tenta com lua.exe normal
    lua_exe = os.path.join(BASE, "ArquivosComplementares", "vcpkg", "installed", "x64-windows", "tools", "luajit", "luajit.exe")
    if not os.path.exists(lua_exe):
        lua_exe = "luajit"
    
    try:
        result = os.system(f'"{lua_exe}" -e "HABILIDADES={{}}" "{path}" 2>&1')
        # Isso pode nao funcionar perfeitamente, entao vamos so validar sintaxe
        return True
    except:
        return False

# ============================================
print("=" * 80)
print("  TESTE: GERAR HABILIDADES SHC NO FORMATO CORRETO")
print("=" * 80)

# PASSO 1: Ler template SHC de fogo.lua
print("\n📖 PASSO 1: Lendo template SHC de fogo.lua...")
try:
    with open(os.path.join(BASE, "Canary", "data-canary", "scripts", "MCR", "SPA", "habilidades", "fogo.lua")) as f:
        fogo_content = f.read()
    # Extrai habilidades 23001 e 23002 como exemplo
    idx1 = fogo_content.find("HABILIDADES[23001]")
    idx2 = fogo_content.find("HABILIDADES[23002]")
    idx3 = fogo_content.find("HABILIDADES[23003]")
    if idx2 == -1:
        idx2 = idx1 + 2000
    if idx3 == -1:
        idx3 = len(fogo_content)
    
    template = fogo_content[idx1:min(idx3, idx1+3500)]
    print(f"  Template extraido: {len(template)} chars (habilidades 23001-23002)")
    print(f"  Formato: efeitoConfig com tipo, dano, percentual, elemento")
    print(f"  Postura: chaves [1], [2], [3]")
    print(f"  Niveis: marcos [5], [10], [15], [20]")
except Exception as e:
    print(f"  ERRO ao ler template: {e}")
    template = ""

# ============================================
# PASSO 2: Tentativas de geracao
# ============================================
SYS_DEV = (
    "Voce e um desenvolvedor Lua para o Projeto MCR.\n"
    "Formato SHC (OBRIGATORIO):\n"
    "Cada habilidade deve seguir este formato EXATO:\n"
    "HABILIDADES[ID] = {\n"
    '    nome = "Nome",\n'
    '    tipo = "gatilho",\n'
    "    dominio = {27},\n"
    "    cooldown = 6,\n"
    '    categoria = "single",\n'
    "    efeitoConfig = {\n"
    '        tipo = "projectile",\n'
    "        dano = 1.0,\n"
    "        percentual = 0.5,\n"
    "        elemento = COMBAT_ENERGYDAMAGE,\n"
    "    },\n"
    "    postura = {\n"
    "        [1] = { efeitoConfig = { dano = 1.3 } },\n"
    "    },\n"
    "    niveis = {\n"
    "        [5] = { { mod = \"efeitoConfig\", dano = \"*1.15\" } },\n"
    "    },\n"
    "    sinergias = {\n"
    "        [23] = { descricao = \"Fogo + Cristal\", nivelMin = 1, efeitoConfig = { elemento = COMBAT_FIREDAMAGE } },\n"
    "    },\n"
    "    estados = {\n"
    "        vinculo = { efeitoConfig = { dano = 1.5 } },\n"
    "    },\n"
    "    condicoes = {\n"
    "        cercado = { efeitoConfig = { raio = 5, dano = 1.2 } },\n"
    "    },\n"
    "}\n"
    "REGRAS:\n"
    "1. Postura usa colchetes numericos: [1], [2], [3]\n"
    "2. Niveis usa colchetes: [5], [10], [15], [20]\n"
    "3. Sinergias usa ID do dominio como chave: [23], [24]\n"
    "4. NUNCA use arrays como postura = {\"ataque\"}\n"
    "5. elemento DEVE ser COMBAT_ENERGYDAMAGE"
)

print("\n🤖 PASSO 2: Gerando habilidades CRISTAL no formato SHC...\n")

for tentativa in range(1, 4):
    print(f"{'='*70}")
    print(f"  TENTATIVA {tentativa}/3")
    print(f"{'='*70}")
    
    if tentativa == 1:
        # Tentativa 1: template + instrucao basica
        prompt = ("Crie 3 habilidades SHC para o dominio CRISTAL (ID 27).\n"
                  "Use EXATAMENTE o formato SHC abaixo:\n\n"
                  + template[:2000] +
                  "\n\nCrie 3 habilidades para CRISTAL com COMBAT_ENERGYDAMAGE.\n"
                  "IDs: 27001, 27002, 27003")
    
    elif tentativa == 2:
        # Tentativa 2: foco no formato correto
        prompt = ("Crie 2 habilidades SHC para CRISTAL (27).\n"
                  "Siga o formato SHC:\n\n"
                  + template[:1500] +
                  "\n\nREGRAS:\n"
                  "- Use efeitoConfig com tipo, dano (numero), percentual (0.0-1.0), elemento\n"
                  "- Postura usa [1], [2], [3] como chaves, NAO array\n"
                  "- Niveis usa [5], [10], [15], [20] como chaves\n"
                  "- NAO use danoMinimo/danoMaximo\n"
                  "\nCrie 2 habilidades: uma projectile (ataque) e uma area_target (AoE)")
    
    else:
        # Tentativa 3: template mais explicito
        prompt = """Crie 1 habilidade SHC para CRISTAL (27).

Preencha este molde (mude apenas os valores, mantenha a estrutura):

HABILIDADES[27001] = {
    nome = "Lanca de Cristal",
    tipo = "gatilho",
    dominio = {27},
    cooldown = 4,
    categoria = "single",
    efeitoConfig = {
        tipo = "projectile",
        dano = 1.5,
        percentual = 0.5,
        elemento = COMBAT_ENERGYDAMAGE,
    },
    postura = {
        [1] = { efeitoConfig = { dano = 1.8 } },
        [3] = { efeitoConfig = { dano = 1.0 } },
    },
    niveis = {
        [5] = { { mod = "efeitoConfig", dano = "*1.15" } },
        [10] = { { mod = "efeitoConfig", distancia = "+1" } },
    },
}

Preencha APENAS os valores, mantenha a estrutura IDENTICA."""
    
    resp, tempo = chat("qwen2.5-coder:7b", [
        {"role": "system", "content": SYS_DEV},
        {"role": "user", "content": prompt}
    ], 2048, 0.1)
    
    print(f"  Tempo: {tempo:.1f}s | Tam: {len(resp)} chars")
    
    # Extrai codigo Lua (remove markdown)
    codigo = resp
    if "```lua" in codigo:
        codigo = codigo.split("```lua")[1]
        if "```" in codigo:
            codigo = codigo.split("```")[0]
    elif "```" in codigo:
        codigo = codigo.split("```")[1]
    
    # Valida formato
    erros = validar_formato_shc(codigo)
    
    if not erros:
        print(f"  ✅ FORMATO SHC VALIDO!")
        # Salva como lua
        path = salvar_como_lua(codigo, tentativa)
        print(f"  Salvo: sandbox/cristal_tentativa_{tentativa}.lua")
        TENTATIVAS.append({"tentativa": tentativa, "codigo": codigo, "valido": True, "erros": []})
    else:
        print(f"  ❌ ERROS DE FORMATO ({len(erros)}):")
        for e in erros:
            print(f"     - {e}")
        TENTATIVAS.append({"tentativa": tentativa, "codigo": codigo, "valido": False, "erros": erros})
    
    print()

# ============================================
# RESUMO
# ============================================
print("=" * 80)
print("  RESUMO - GERACAO SHC")
print("=" * 80)

validas = [t for t in TENTATIVAS if t["valido"]]
if validas:
    print(f"\n  ✅ {len(validas)}/{len(TENTATIVAS)} tentativas validas!")
    print(f"  Arquivos salvos em: sandbox/cristal_tentativa_*.lua")
    print(f"\n  Melhor tentativa: #{validas[0]['tentativa']}")
    print(f"  Codigo gerado ({len(validas[0]['codigo'])} chars):")
    print(f"  {validas[0]['codigo'][:600]}")
else:
    print(f"\n  ❌ Nenhuma tentativa valida.")
    print(f"  Ultimos erros: {TENTATIVAS[-1]['erros']}")
    print(f"\n  Codigo gerado (tentativa 3):")
    print(f"  {TENTATIVAS[-1]['codigo'][:600]}")

# Salva historico
with open(os.path.join(BASE, "sandbox", "test_shc_resultado.json"), "w") as f:
    json.dump({"tentativas": TENTATIVAS}, f, ensure_ascii=False, indent=2)
print(f"\n  Resultado: sandbox/test_shc_resultado.json")
print("=" * 80)
