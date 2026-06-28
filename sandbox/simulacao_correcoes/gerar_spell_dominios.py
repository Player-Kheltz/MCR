"""
Script: extrair_spells_para_dominios_v2.py
Objetivo:
  1. Extrair os nomes de todas as spells do Canary.
  2. Para cada spell nova, inferir automaticamente o domínio mais provável
     (Fogo, Água, Terra, Ar, Luz, Sombra, Lâminas, etc.).
  3. Atualizar o arquivo config_dominios.lua com as novas entradas,
     preservando as já existentes.
"""

import os
import re
import sys

# ------------------- CONFIGURAÇÕES ------------------
CANARY_ROOT = r"E:\Projeto MCR\Canary"
CONFIG_FILE = os.path.join(CANARY_ROOT, "data", "MCR Scripts", "config_dominios.lua")

# Mapeamento tipo de dano (nome da constante) → domínio
DAMAGE_TYPE_TO_DOMAIN = {
    "COMBAT_FIREDAMAGE":    "DOMINIO_FOGO",
    "COMBAT_ENERGYDAMAGE":  "DOMINIO_AR",
    "COMBAT_EARTHDAMAGE":   "DOMINIO_TERRA",
    "COMBAT_ICEDAMAGE":     "DOMINIO_AGUA",
    "COMBAT_HOLYDAMAGE":    "DOMINIO_LUZ",
    "COMBAT_DEATHDAMAGE":   "DOMINIO_SOMBRA",
    "COMBAT_PHYSICALDAMAGE": "DOMINIO_LAMINAS",  # suposição genérica
    "COMBAT_HEALING":       "DOMINIO_LUZ",
    "COMBAT_MANADRAIN":     "DOMINIO_SOMBRA",
    "COMBAT_LIFEDRAIN":     "DOMINIO_SOMBRA",
}

# Palavras-chave no nome da spell → domínio
NAME_KEYWORDS = [
    # Fogo
    (r"(fire|flame|magma|burn|inferno|blaze|ash|ember)", "DOMINIO_FOGO"),
    # Água / Gelo
    (r"(ice|frost|glacier|frozen|shiver|arctic|hail|snow)", "DOMINIO_AGUA"),
    # Terra
    (r"(earth|stone|stalagmite|rock|mud|sand|boulder|soil)", "DOMINIO_TERRA"),
    # Ar / Energia
    (r"(energy|lightning|thunder|storm|spark|zap|volt|shock)", "DOMINIO_AR"),
    # Luz / Cura
    (r"(holy|divine|sacred|bless|grace|light|cure|heal|recovery|regenerat)", "DOMINIO_LUZ"),
    # Sombra / Morte
    (r"(death|necro|soul|undead|dark|shadow|curse|wither|decay)", "DOMINIO_SOMBRA"),
    # Lâminas (corte, sangramento)
    (r"(blade|slash|cut|bleed|wound|stab)", "DOMINIO_LAMINAS"),
    # Impacto (martelo, esmagamento)
    (r"(smash|crush|hammer|bash|impact|maul)", "DOMINIO_IMPACTO"),
    # Precisão / distância (flecha, projétil)
    (r"(arrow|bolt|projectile|snipe|shoot)", "DOMINIO_PRECISAO"),
]

# Palavras-chave no grupo da spell
GROUP_KEYWORDS = {
    "healing": "DOMINIO_LUZ",
    "support": "DOMINIO_LUZ",
}

# Padrões regex
SPELL_NAME_RE = re.compile(r'spell:name\("([^"]+)"\)')
DAMAGE_TYPE_RE = re.compile(r'COMBAT_PARAM_TYPE\s*,\s*(COMBAT_\w+)')
SPELL_GROUP_RE = re.compile(r'spell:group\(([^)]+)\)')

# ----------------------------------------------------------------------

def find_spell_files(root):
    """Retorna uma lista com os caminhos de todos os .lua que contêm spell:name."""
    spell_files = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if not fname.endswith('.lua'):
                continue
            fullpath = os.path.join(dirpath, fname)
            # Evita processar diretórios de libs que possam ter falsos positivos
            if any(part in fullpath.lower() for part in ['lib', 'modules', 'compat']):
                continue
            spell_files.append(fullpath)
    return spell_files

def read_file_content(filepath):
    """Lê um arquivo tentando UTF-8 e depois Latin-1, retorna string."""
    for enc in ('utf-8', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception:
            break
    raise IOError(f"Não foi possível ler {filepath}")

def extract_spell_info(content):
    """
    Extrai nome da spell, tipo de dano e grupos de um script Lua.
    Retorna (nome, damage_type_constant, groups_list)
    """
    nome = None
    damage_const = None
    groups = []

    # Nome
    m = SPELL_NAME_RE.search(content)
    if m:
        nome = m.group(1)
    else:
        return None, None, []

    # Tipo de dano (primeira ocorrência)
    m = DAMAGE_TYPE_RE.search(content)
    if m:
        damage_const = m.group(1)

    # Grupos
    m = SPELL_GROUP_RE.search(content)
    if m:
        groups_str = m.group(1)
        # Extrai strings entre aspas
        groups = re.findall(r'"([^"]+)"', groups_str)

    return nome, damage_const, groups

def guess_domain(nome, damage_const, groups):
    """
    Com base no tipo de dano, nome e grupo, retorna uma string de domínio,
    ou DOMINIO_INDEFINIDO se não for possível determinar.
    """
    # Prioridade: tipo de dano
    if damage_const and damage_const in DAMAGE_TYPE_TO_DOMAIN:
        return DAMAGE_TYPE_TO_DOMAIN[damage_const]

    # Verifica grupos
    for group in groups:
        if group in GROUP_KEYWORDS:
            return GROUP_KEYWORDS[group]

    # Verifica palavras-chave no nome
    nome_lower = nome.lower()
    for pattern, domain in NAME_KEYWORDS:
        if re.search(pattern, nome_lower):
            return domain

    # Fallback: se contiver "attack" ou "strike", associa a LÂMINAS ou AR?
    # Deixamos como INDEFINIDO para revisão.
    return "DOMINIO_INDEFINIDO"

def parse_existing_config(config_path):
    """Retorna um conjunto com os nomes de spells já mapeados."""
    existing = set()
    if not os.path.exists(config_path):
        return existing
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Coleta todas as chaves ["Nome"] dentro da tabela spellDomain
    for m in re.finditer(r'\["([^"]+)"\]\s*=', content):
        existing.add(m.group(1))
    return existing

def update_config(config_path, new_spells):
    """
    Adiciona as novas entradas (nome -> domínio) ao final da tabela spellDomain,
    logo antes da chave '}' que fecha a tabela.
    """
    if not os.path.exists(config_path):
        # Cria arquivo novo com a tabela
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("-- Gerado automaticamente por extrair_spells_para_dominios_v2.py\n")
            f.write("spellDomain = {\n")
            for nome, domain in sorted(new_spells.items()):
                f.write(f'    ["{nome}"] = {domain},  -- adicionado automaticamente\n')
            f.write("}\n")
        print(f"✅ Arquivo {config_path} criado com {len(new_spells)} magias.")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    # Localiza a linha que fecha a tabela spellDomain
    fecho_index = None
    profundidade = 0
    dentro = False
    for i, linha in enumerate(linhas):
        if re.search(r'spellDomain\s*=\s*\{', linha):
            dentro = True
            profundidade = linha.count('{') - linha.count('}')
            continue
        if dentro:
            profundidade += linha.count('{') - linha.count('}')
            if profundidade == 0:
                fecho_index = i
                break

    if fecho_index is None:
        print("❌ Erro: não foi possível localizar o fechamento da tabela spellDomain no arquivo.")
        return

    # Monta as novas linhas ordenadas alfabeticamente
    novas_linhas = []
    for nome in sorted(new_spells):
        # Escapa aspas duplas se necessário (nomes de spell não devem ter aspas)
        safe_name = nome.replace('"', '\\"')
        novas_linhas.append(f'    ["{safe_name}"] = {new_spells[nome]},  -- adicionado automaticamente\n')

    # Insere as novas linhas logo antes do fechamento
    for _ in range(len(novas_linhas)):
        linhas.insert(fecho_index, novas_linhas.pop(0))  # insere uma a uma no local correto
        fecho_index += 1

    # Reescreve o arquivo
    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(linhas)

    print(f"✅ Adicionadas {len(new_spells)} novas magias ao arquivo {config_path}.")

def main():
    print("🔍 Procurando arquivos de spell...")
    spell_files = find_spell_files(CANARY_ROOT)
    print(f"📁 {len(spell_files)} arquivos .lua encontrados (excluindo pastas de lib).")

    all_spells = {}
    for filepath in spell_files:
        try:
            content = read_file_content(filepath)
        except Exception as e:
            print(f"⚠️ Ignorando {filepath}: {e}", file=sys.stderr)
            continue

        nome, damage_const, groups = extract_spell_info(content)
        if not nome:
            continue  # não é uma spell

        domain = guess_domain(nome, damage_const, groups)
        all_spells[nome] = domain
        print(f"  🧪 {nome:40s} → {domain}")

    print(f"\n✨ Total de spells detectadas: {len(all_spells)}")

    # Lê spells já existentes na config
    existing = parse_existing_config(CONFIG_FILE)

    # Filtra apenas as que ainda não estão mapeadas
    new_spells = {nome: dom for nome, dom in all_spells.items() if nome not in existing}

    if not new_spells:
        print("✅ Nenhuma spell nova para adicionar. O arquivo já está completo.")
        return

    print(f"\n➕ Spells a adicionar: {len(new_spells)}")
    update_config(CONFIG_FILE, new_spells)

if __name__ == "__main__":
    main()