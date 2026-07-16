"""Filtra resultados brutos da varredura e separa uteis de ruido."""
import sys, os, re, json
from collections import defaultdict

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

sys.path.insert(0, _BASE)
from code_analyzer import analisar_arquivo, PADROES_BUG, SEVERIDADE_PESO

PROJETO = r"E:\Projeto MCR"
IGNORAR = {'vcpkg', 'node_modules', '__pycache__', '.git', 'build', 'bin', 'obj', 'Backup', '.mcr_devia'}
extensoes = {'.py', '.cpp', '.hpp', '.h', '.c', '.cs', '.lua', '.go'}

diretorios = [
    ("Canary src", os.path.join(PROJETO, "Canary", "src")),
    ("Canary data", os.path.join(PROJETO, "Canary", "data-canary")),
    ("Grimorio", os.path.join(PROJETO, "MCR.Grimorio")),
    ("LoginServer", os.path.join(PROJETO, "LoginServer", "src")),
    ("DevIA", os.path.join(PROJETO, "historia", "scripts", "mcr_devia")),
    ("MCR engine", _BASE),
]

# ─── CLASSIFICA CADA PADRAO ────────────────────────────────
# Utilidade: ALTA = bug real, MEDIA = precisa revisao, BAIXA = contexto-dependente, INFO = registro
UTILIDADE_PADRAO = {
    'except vazio': 'ALTA',
    'SANDBOX padrao': 'ALTA',
    'encode ascii': 'ALTA',
    'sql injection': 'CRITICA',
    'dofile em lua': 'ALTA',
    'new sem smart pointer': 'MEDIA',
    'c_str temporario': 'MEDIA',
    'errors replace': 'MEDIA',
    'os walk sem limite': 'MEDIA',
    'readlines sem limite': 'MEDIA',
    'read sem limite': 'MEDIA',
    'encoding utf8 hardcoded': 'BAIXA',
    'leitura sem encoding': 'BAIXA',
    'except Exception amplo': 'BAIXA',
    'open() sem encoding': 'INFO',
    'readlines()': 'INFO',
}

# Mapeia primeiras palavras do padrao pra classificar
def classificar_utilidade(descricao):
    if 'SANDBOX' in descricao or 'sandbox' in descricao:
        return 'ALTA', 'Caminho padrao SANDBOX em vez do projeto'
    if 'ascii' in descricao:
        return 'ALTA', 'encode ascii perde acentos PT-BR'
    if 'except vazio' in descricao or 'except:' in descricao.lower():
        return 'ALTA', 'except vazio suprime excecoes'
    if 'sql' in descricao.lower() and ('injection' in descricao.lower() or 'interpol' in descricao.lower()):
        return 'CRITICA', 'SQL Injection potencial'
    if 'dofile' in descricao.lower():
        return 'ALTA', 'dofile() em Revscript — usar carregamento automatico'
    if 'smart pointer' in descricao:
        return 'MEDIA', 'new sem smart pointer — memory leak'
    if 'c_str' in descricao.lower():
        return 'MEDIA', 'c_str temporario — dangling pointer'
    if 'errors=replace' in descricao:
        return 'MEDIA', 'errors=replace perde dados encoding'
    if 'os.walk' in descricao or 'os_walk' in descricao:
        return 'MEDIA', 'os.walk sem limite de profundidade'
    if 'readlines()' in descricao:
        return 'MEDIA', 'readlines carrega tudo em memoria'
    if 'read()' in descricao and 'readlines' not in descricao:
        return 'MEDIA', 'read() sem limite'
    if 'utf-8' in descricao.lower() or 'utf8' in descricao.lower():
        return 'BAIXA', 'encoding=utf-8 pode ser incorreto para .lua'
    if 'except Exception' in descricao:
        return 'BAIXA', 'except Exception muito amplo'
    if 'encoding' in descricao.lower() and 'utf' not in descricao.lower():
        return 'BAIXA', 'leitura sem encoding explicito'
    return 'INFO', 'outro'

# ─── VARRE E CLASSIFICA ──────────────────────────────────────
por_utilidade = defaultdict(lambda: defaultdict(int))
por_diretorio = defaultdict(lambda: defaultdict(int))
por_padrao = defaultdict(int)
detalhes_uteis = []

for nome, base_dir in diretorios:
    if not os.path.isdir(base_dir):
        continue
    
    for raiz, dirs, arquivos in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in IGNORAR and not d.startswith('.')]
        for f in arquivos:
            _, ext = os.path.splitext(f)
            if ext.lower() not in extensoes:
                continue
            caminho = os.path.join(raiz, f)
            if any(ign in caminho for ign in IGNORAR):
                continue
            
            bugs = analisar_arquivo(caminho)
            if not bugs:
                continue
            
            for b in bugs:
                util, label = classificar_utilidade(b['descricao'])
                por_utilidade[util][nome] += 1
                por_diretorio[nome][util] += 1
                por_padrao[label] += 1
                
                # Guarda detalhes de bugs uteis (ALTA, CRITICA)
                if util in ('CRITICA', 'ALTA'):
                    rel = os.path.relpath(caminho, PROJETO)[:60]
                    detalhes_uteis.append({
                        'util': util,
                        'componente': nome,
                        'arquivo': rel,
                        'linha': b['linha'],
                        'descricao': b['descricao'][:100],
                        'correcao': b.get('correcao', '')[:100],
                    })

# ─── RELATORIO ───────────────────────────────────────────────
print("=" * 65)
print("  FILTRAGEM: 1.353 bugs brutos → classificados")
print("=" * 65)

print(f"\n--- POR UTILIDADE ---")
for util in ['CRITICA', 'ALTA', 'MEDIA', 'BAIXA', 'INFO']:
    total = sum(por_utilidade[util].values())
    if total == 0:
        continue
    pct = total / 1353 * 100
    print(f"  {util:10s}: {total:4d} bugs ({pct:4.1f}%)")
    for comp, qtd in sorted(por_utilidade[util].items()):
        if qtd > 0:
            print(f"           {comp:20s}: {qtd}")

print(f"\n--- POR PADRAO ---")
for padrao, qtd in sorted(por_padrao.items(), key=lambda x: -x[1]):
    print(f"  {padrao:45s}: {qtd}")

# Mostra detalhes dos bugs uteis
total_uteis = sum(por_utilidade['ALTA'].values()) + sum(por_utilidade['CRITICA'].values())
if detalhes_uteis:
    print(f"\n--- BUGS UTEIS (CRITICA + ALTA = {total_uteis}) ---")
    for b in detalhes_uteis:
        print(f"  [{b['util'][0]}] {b['componente'][:20]:20s} {b['arquivo']}:{b['linha']}")
        print(f"       {b['descricao']}")
        print(f"       Correcao: {b['correcao']}")

print(f"\n{'='*65}")
print(f"  RESUMO FILTRADO")
print(f"{'='*65}")
totais = {}
for util in ['CRITICA', 'ALTA', 'MEDIA', 'BAIXA', 'INFO']:
    totais[util] = sum(por_utilidade[util].values())

print(f"  1.353 bugs brutos")
print(f"  ─────────────────────────────────────")
print(f"  Util (CRITICA+ALTA): {totais.get('CRITICA',0)+totais.get('ALTA',0)} ({((totais.get('CRITICA',0)+totais.get('ALTA',0))/1353*100):.0f}%)")
print(f"  Revisar (MEDIA):     {totais.get('MEDIA',0)} ({(totais['MEDIA']/1353*100):.0f}%)")
print(f"  Contextual (BAIXA):  {totais.get('BAIXA',0)} ({(totais['BAIXA']/1353*100):.0f}%)")
print(f"  Ruido (INFO):        {totais.get('INFO',0)} ({(totais['INFO']/1353*100):.0f}%)")
print(f"  ─────────────────────────────────────")
print(f"  Acoes reais: {totais.get('CRITICA',0)+totais.get('ALTA',0)} bugs para corrigir AGORA")
print(f"  {totais.get('MEDIA',0)} bugs para revisar")
print(f"  {totais.get('BAIXA',0)+totais.get('INFO',0)} ignoraveis (falso positivo ou contexto-dependente)")
print(f"{'='*65}")
