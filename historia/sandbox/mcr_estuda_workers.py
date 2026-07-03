#!/usr/bin/env python3
"""MCR estuda Modelos IA — Workers paralelos com MCRTarefa."""
import sys, os, time as _time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCR, MCRSignature, MCRTarefa, MCRSpawner, MCRMetaNivel, _get_kg

T0 = _time.time()
def log(msg):
    print(f'[{_time.time()-T0:.1f}s] {msg}', flush=True)

log('MCR estudando Modelos IA com workers...')

raiz = r'E:\Modelos IA'

def extrair_signature(arquivo):
    """Extrai MCRSignature de UM arquivo (callable para MCRTarefa)."""
    try:
        tam = os.path.getsize(arquivo)
        if tam < 50:
            return None
        with open(arquivo, 'rb') as f:
            dados = f.read(2000)
        sig = MCRSignature.extrair(dados, rapido=True)
        return {
            'caminho': arquivo,
            'nome': os.path.basename(arquivo),
            'tamanho': tam,
            'entropia': sig.get('entropia', 0),
            'estados': sig.get('estados', 0),
            'fingerprint': sig.get('fingerprint', []),
        }
    except:
        return None

def estudar_grupo(membros):
    """Estuda UM grupo de arquivos (callable para MCRTarefa).
    
    Le o representante, extrai MetaNivel, retorna resultados.
    """
    if not membros:
        return []
    rep = membros[0]
    try:
        with open(rep['caminho'], 'rb') as f:
            dados = f.read(5000)
    except:
        return []
    
    meta = MCRMetaNivel()
    meta.alimentar(dados[:2000])
    diag = meta.diagnosticar()
    niveis = diag.get('n_niveis', 0)
    
    for m in membros:
        m['niveis'] = niveis
    return membros

# PASSO 1: Descobre arquivos
log('Passo 1: Descobrindo arquivos...')
todos = []
for pasta, subpastas, arquivos in os.walk(raiz):
    for arq in arquivos:
        todos.append(os.path.join(pasta, arq))
log(f'  {len(todos)} arquivos encontrados')

# PASSO 2: MCRSpawner extrai signatures em PARALELO
log('Passo 2: Extraindo assinaturas (workers)...')
spawner = MCRSpawner()
# Cria UMA MCRTarefa por arquivo (workers sao criados internamente)
from modulos.MCR import MCRSpawner
tarefas_sig = [MCRTarefa(f"sig_{i}", extrair_signature, {'arquivo': arq})
               for i, arq in enumerate(todos[:200])]

workers = spawner.spawnar(tarefas_sig)
# Cada worker tem resultado de um lote = lista de resultados das subtarefas
resultados = []
for w in workers:
    if isinstance(w.resultado, list):
        resultados.extend([r for r in w.resultado if r is not None])
    elif w.resultado is not None:
        resultados.append(w.resultado)
log(f'  {len(resultados)} signatures extraidas')

# PASSO 3: MCR Decisor agrupa por fingerprint
log('Passo 3: Agrupando por similaridade...')
grupos = {}
for r in resultados:
    if not r or not r.get('fingerprint'):
        continue
    fp = r['fingerprint']
    if len(fp) >= 8:
        b1 = max(range(8), key=lambda i: fp[i])
        fp2 = list(fp)
        fp2[b1] = 0
        b2 = max(range(8), key=lambda i: fp2[i])
        chave = f'{b1}_{b2}'
    else:
        chave = 'outros'
    grupos.setdefault(chave, []).append(r)

log(f'  {len(grupos)} grupos formados')

# PASSO 4: MCRSpawner estuda grupos em PARALELO
log('Passo 4: Estudando grupos (MetaNivel paralelo)...')
tarefas_grupos = [MCRTarefa(f"grupo_{chave}", estudar_grupo, {'membros': membros})
                  for chave, membros in grupos.items()]

workers_g = spawner.spawnar(tarefas_grupos)
results_g = []
for w in workers_g:
    if w.resultado:
        for sub in w.resultado:
            if isinstance(sub, list):
                results_g.extend([s for s in sub if s])
            elif sub:
                results_g.append(sub)
log(f'  {len(results_g)} arquivos estudados em {len(grupos)} grupos')

# PASSO 5: Alimenta KG (tambem via workers, se quiser)
log('Passo 5: Alimentando KG...')
kg = _get_kg()
for r in results_g:
    try:
        with open(r['caminho'], 'rb') as f:
            preview = f.read(300).decode('utf-8', errors='replace')[:200]
    except:
        preview = f'[binario] {r["tamanho"]} bytes'
    
    if kg:
        kg.aprender_conceito(
            f'estudo_mcr:{r["nome"]}',
            f'[Grupo] {r["nome"]}: {r["tamanho"]}B '
            f'ent={r["entropia"]:.2f} est={r["estados"]} niv={r["niveis"]}\n{preview}',
            ctx='estudo_mcr'
        )

log(f'  KG alimentado com {len(results_g)} lessons')

# RELATORIO
log('=' * 50)
log('RELATORIO FINAL')
log(f'Arquivos descobertos: {len(todos)}')
log(f'Assinaturas extraidas: {len(resultados)}')
log(f'Grupos formados: {len(grupos)}')
log(f'Arquivos estudados: {len(results_g)}')
log(f'Tempo total: {_time.time()-T0:.1f}s')
log(f'Workers usados: Fase1={len(workers)}, Fase2={len(workers_g)}')
log('=' * 50)
