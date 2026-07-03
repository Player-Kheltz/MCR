#!/usr/bin/env python3
"""Teste de migracao: KG externo -> MCR.py."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRPersistencia

mcr_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos', 'MCR.py'))

print("1. Migrando KG externo para dentro do MCR.py...", flush=True)

# Crie uma copia de seguranca primeiro
import shutil
bak_path = mcr_path + '.bak'
if not os.path.exists(bak_path):
    shutil.copy2(mcr_path, bak_path)
    print("   Backup feito.", flush=True)

# Carrega KG externo
from modulos.kg import KnowledgeGraph
kg = KnowledgeGraph()
licoes = kg._get_licoes()
print(f"   KG externo: {len(licoes)} lessons", flush=True)

# Filtra lessons uteis
uteis = [l for l in licoes 
         if l.get('solucao', '') and len(l.get('solucao', '')) > 30 
         and not l.get('solucao', '').startswith('{')]
print(f"   Uteis: {len(uteis)}", flush=True)

# Prepara dados
dados = {'licoes': [], 'assinaturas': {}, 'cache': {}, 'estado': {}}
for l in uteis[:500]:  # max 500 pra nao inflar muito
    dados['licoes'].append({
        'erro': l.get('erro', '')[:200],
        'solucao': l.get('solucao', '')[:500],
        'ctx': l.get('ctx', 'geral'),
        'timestamp': l.get('timestamp', time.time()),
    })

# Carrega assinaturas
ass_path = os.path.join(os.path.dirname(__file__), '..', 'sandbox', '.mcr_assinaturas.json')
ass_path = os.path.normpath(ass_path)
if os.path.exists(ass_path):
    import json
    with open(ass_path, 'r', encoding='utf-8') as f:
        ass_data = json.load(f)
    for autor, ass_list in ass_data.items():
        for a in ass_list[:5]:  # max 5 por autor
            a_copy = dict(a)
            a_copy['autor'] = autor
            dados['assinaturas'].setdefault(autor, []).append(a_copy)
    print(f"   Assinaturas: {sum(len(v) for v in dados['assinaturas'].values())}", flush=True)

# Estado
dados['estado']['ultima_migracao'] = time.time()
dados['estado']['licoes_originais'] = len(licoes)

# Salva no MCR.py
pers = MCRPersistencia(mcr_path)
pers.dados = dados
pers.marcar_mudanca()

print(f"2. Salvando {len(dados['licoes'])} lessons no MCR.py...", flush=True)
t0 = time.time()
ok = pers.salvar_se_precisar('forcado')
t1 = time.time() - t0
print(f"   Salvou em {t1:.1f}s: {ok}", flush=True)

print(f"3. Verificando tamanho...", flush=True)
tam = os.path.getsize(mcr_path)
print(f"   MCR.py: {tam/1024:.0f} KB", flush=True)

print(f"\nOK - Migracao concluida!")
print(f"   Backup em: {bak_path}")
