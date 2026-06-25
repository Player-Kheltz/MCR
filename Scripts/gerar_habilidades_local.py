"""
    gerar_habilidades_local.py — Gera habilidades SHC usando IA local (Ollama)
    Uso: python gerar_habilidades_local.py <dominio> [num_habilidades]
    
    Exemplo:
      python gerar_habilidades_local.py arcos 20
      python gerar_habilidades_local.py lutador 30
    
    Requer: Ollama rodando com modelo (padrao: hermes3:8b)
    
    O script:
    1. Le o arquivo existente (se houver) para contexto
    2. Envia prompt para IA local com especificacoes SHC
    3. Valida a sintaxe Lua basica
    4. Salva o arquivo
"""
import sys, os, json, re, subprocess, argparse

BASE = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'
OLLAMA_API = 'http://localhost:11434/api/generate'

# Contexto SHC que a IA local precisa saber
SHC_CONTEXT = '''
Cada habilidade deve seguir o formato SHC com estas 5 camadas:

1. postura — [1]=Impeto, [2]=Equilibrio, [3]=Guarda (variacoes de dano/efeito)
2. niveis — melhorias nos marcos 5, 10, 15, 20 do dominio
3. sinergias — efeitos extras quando jogador tem nivel em OUTRO dominio
4. estados — vinculo (dano 1.5x) e lampejo (dano 2x, custo 0)
5. condicoes — cercado (3+ inimigos), vidaBaixa (<20% HP), fullHp, singleTarget

TIPOS DE EXECUCAO SUPORTADOS (usa estes nomes exatos):
  projectile, melee, cone, multi_hit, explosion_ring, area_target,
  storm, buff, debuff, heal, trap, field_aura, orbit, pulse, rain

ELEMENTOS (usa estes nomes exatos):
  COMBAT_PHYSICALDAMAGE, COMBAT_FIREDAMAGE, COMBAT_ICEDAMAGE,
  COMBAT_EARTHDAMAGE, COMBAT_ENERGYDAMAGE, COMBAT_HOLYDAMAGE, COMBAT_DEATHDAMAGE

CATEGORIAS: single, aoe, buff, debuff, finisher, defense

EXEMPLO DE HABILIDADE COMPLETA:
HABILIDADES[12001] = {
    nome = "Tiro Certeiro",
    tipo = "gatilho",
    dominio = {120},
    cooldown = 3,
    categoria = "single",
    descricao = "Disparo preciso de longa distancia.",
    efeitoConfig = {
        tipo = "projectile",
        dano = 1.6,
        percentual = 0.55,
        elemento = COMBAT_PHYSICALDAMAGE,
    },
    postura = {
        [1] = { efeitoConfig = { dano = 1.3 } },
        [3] = { efeitoConfig = { dano = 0.9 } },
    },
    niveis = {
        [5] = { { mod = "efeitoConfig", dano = "*1.15" } },
        [10] = { { mod = "efeitoConfig", distancia = 1 } },
    },
    sinergias = {
        [23] = {
            descricao = "Fogo: dano de fogo adicional.",
            nivelMin = 1,
            efeitoConfig = { elemento = COMBAT_FIREDAMAGE, danoAdicional = 0.3 },
        },
    },
    estados = {
        vinculo = { efeitoConfig = { dano = 2.4, damageType = "absolute" } },
        lampejo = { efeitoConfig = { dano = 3.2, custoMana = 0 } },
    },
    condicoes = {
        cercado = { efeitoConfig = { tipo = "explosion_ring", raio = 5, dano = 2.1 } },
    },
}
'''

def chamar_ollama(prompt, model='hermes3:8b'):
    """Chama a API da Ollama com o prompt."""
    payload = {
        'model': model,
        'prompt': prompt,
        'stream': False,
        'options': {
            'temperature': 0.7,
            'num_ctx': 4096,
        }
    }
    try:
        import urllib.request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(OLLAMA_API, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get('response', '')
    except Exception as e:
        print(f"Erro ao chamar Ollama: {e}", file=sys.stderr)
        return None

def validar_lua(conteudo):
    """Validacao basica de sintaxe Lua."""
    issues = []
    opens = conteudo.count('{')
    closes = conteudo.count('}')
    if opens != closes:
        issues.append(f"Chaves desbalanceadas: {opens} abertas, {closes} fechadas")
    
    # Verificar HABILIDADES[ numeros
    habilidades = re.findall(r'HABILIDADES\[\d+\]', conteudo)
    if not habilidades:
        issues.append("Nenhuma habilidade encontrada!")
    
    # Verificar se tem efeitoConfig com tipo
    tipos = re.findall(r'tipo\s*=\s*"(\w+)"', conteudo)
    tipos_validos = {'projectile','melee','cone','multi_hit','explosion_ring',
                     'area_target','storm','buff','debuff','heal','trap',
                     'field_aura','orbit','pulse','rain','toggle'}
    for t in tipos:
        if t not in tipos_validos and t not in ('gatilho','passiva','transformacao'):
            issues.append(f"Tipo de execucao desconhecido: '{t}'")
    
    return issues, len(habilidades)

def main():
    parser = argparse.ArgumentParser(description='Gera habilidades SHC via IA local')
    parser.add_argument('dominio', help='Nome do dominio (ex: arcos, lutador)')
    parser.add_argument('num', type=int, default=20, nargs='?', help='Numero de habilidades')
    parser.add_argument('--model', default='hermes3:8b', help='Modelo Ollama')
    parser.add_argument('--dry-run', action='store_true', help='So mostra o prompt, nao executa')
    
    args = parser.parse_args()
    
    filepath = os.path.join(BASE, args.dominio + '.lua')
    
    # Le arquivo existente para contexto
    contexto_existente = ''
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            contexto_existente = f.read()
    
    # Constroi prompt
    prompt = f"""VOCE E UM GERADOR DE HABILIDADES PARA O JOGO TIBIA (MCR SERVER).
Gere exatamente {args.num} habilidades SHC para o dominio "{args.dominio}".

{SHC_CONTEXT}

ARQUIVO EXISTENTE (substitua por versao melhorada):
```lua
{contexto_existente[:2000] if contexto_existente else "Nao existe arquivo anterior."}
```

REGRAS:
- Cada habilidade deve ter nome, tipo, dominio, cooldown, categoria, descricao, efeitoConfig
- Pelo menos 80% das habilidades devem ter sinergias
- Pelo menos 30% devem ter estados (vinculo/lampejo)
- Pelo menos 20% devem ter condicoes
- Varie os tipos de execucao (projectile, melee, cone, multi_hit, etc.)
- Nao use placeholders, comentarios ou "..."
- Use IDs de {args.dominio} (ex: para arcos: 12001-12020, lutador: 13001-13020, etc.)
- O header do arquivo deve ter: --[[ Projeto MCR -- SPA -- NOME_DOMINIO (ID) ]]
- A ultima linha deve ser: print(">> SPA: habilidades/{args.dominio}.lua carregado")

Gere APENAS o codigo Lua completo, sem explicacoes."""
    
    if args.dry_run:
        print(prompt)
        return 0
    
    print(f"Chamando Ollama ({args.model})...", file=sys.stderr)
    resposta = chamar_ollama(prompt, args.model)
    
    if not resposta:
        print("Falha ao gerar habilidades.", file=sys.stderr)
        return 1
    
    # Extrai apenas o codigo Lua (entre ```lua e ```)
    codigo = resposta
    m = re.search(r'```lua\n?(.*?)```', resposta, re.DOTALL)
    if m:
        codigo = m.group(1).strip()
    
    # Valida
    issues, hab_count = validar_lua(codigo)
    
    print(f"\nGeradas {hab_count} habilidades.", file=sys.stderr)
    if issues:
        for issue in issues:
            print(f"  AVISO: {issue}", file=sys.stderr)
    
    if not hab_count:
        print("ERRO: Nenhuma habilidade valida gerada!", file=sys.stderr)
        print("Resposta bruta da Ollama:", file=sys.stderr)
        print(resposta[:500], file=sys.stderr)
        return 1
    
    # Backup do original
    if os.path.exists(filepath):
        bak = filepath + '.bak_ia'
        if not os.path.exists(bak):
            import shutil
            shutil.copy2(filepath, bak)
            print(f"Backup salvo: {bak}", file=sys.stderr)
    
    # Salva
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(codigo)
    
    print(f"Salvo: {filepath}", file=sys.stderr)
    
    if issues:
        print("\nCORRIGA OS AVISOS ANTES DE USAR!", file=sys.stderr)
        return 2
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
