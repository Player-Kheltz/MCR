#!/usr/bin/env python3
"""MCR estuda Modelos IA — otimizado: assinatura agrupa, MetaNivel em 1 por grupo."""
import sys, os, time as _time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCR, MCRSignature, MCRMetaNivel, MCRFingerprint, _get_kg

T0 = _time.time()
def log(msg):
    print(f'[{_time.time()-T0:.1f}s] {msg}', flush=True)

log('MCR estudando Modelos IA (otimizado)...')

raiz = r'E:\Modelos IA'

# PASSO 1: Descobre arquivos e extrai assinatura RAPIDA de cada um
log('Passo 1: Descobrindo arquivos e extraindo assinaturas...')
arquivos_com_sig = []  # [(caminho, nome, tamanho, fingerprint, entropia, estados)]
ja_vistos = set()  # cache de checksum para evitar re-estudo

for pasta, subpastas, arquivos in os.walk(raiz):
    for arq in arquivos:
        caminho = os.path.join(pasta, arq)
        try:
            tam = os.path.getsize(caminho)
            if tam < 50: continue
            
            with open(caminho, 'rb') as f:
                dados = f.read(2000)
            
            # Extrai assinatura rapida (8 buckets de tipo de byte)
            sig = MCRSignature.extrair(dados, rapido=True)
            fp = sig.get('fingerprint', [])
            ent = sig.get('entropia', 0)
            est = sig.get('estados', 0)
            
            arquivos_com_sig.append((caminho, arq, tam, fp, ent, est))
        except:
            pass

log(f'  {len(arquivos_com_sig)} arquivos com assinatura extraida')

# PASSO 2: Agrupa por fingerprint similar (MCR, nao hardcode)
log('Passo 2: Agrupando por similaridade de assinatura...')
grupos = {}  # {fingerprint_chave: [(caminho, nome, tam, ent, est)]}
atribuidos = 0

for caminho, nome, tam, fp, ent, est in arquivos_com_sig:
    # Chave do grupo: fingerprint arredondado (2 buckets principais)
    if fp and len(fp) >= 8:
        # Usa os 2 buckets MAIORES como chave do grupo
        bucket1 = max(range(8), key=lambda i: fp[i])
        fp2 = list(fp)
        fp2[bucket1] = 0
        bucket2 = max(range(8), key=lambda i: fp2[i])
        chave = f'{bucket1}_{bucket2}'
    else:
        chave = 'outros'
    
    if chave not in grupos:
        grupos[chave] = []
    grupos[chave].append((caminho, nome, tam, ent, est))
    atribuidos += 1

log(f'  {len(grupos)} grupos formados')

# PASSO 3: Estuda cada grupo — MetaNivel no representante
log('Passo 3: Estudando grupos (MetaNivel em 1 por grupo)...')
kg = _get_kg()
total_estudados = 0
total_lessons = 0

for chave, membros in sorted(grupos.items(), key=lambda x: -len(x[1])):
    if not membros:
        continue
    
    # Representante do grupo (primeiro arquivo)
    rep_path, rep_nome, rep_tam, rep_ent, rep_est = membros[0]
    
    # Le o representante completo
    try:
        with open(rep_path, 'rb') as f:
            dados_rep = f.read(5000)
    except:
        continue
    
    # MCR aprende transicoes de bytes do representante
    mk_rep = MCR(f'grupo_{chave}')
    mk_rep.aprender_sequencia(list(dados_rep[:2000]))
    
    # MCRMetaNivel descobre niveis (UMA vez por grupo)
    meta = MCRMetaNivel()
    meta.alimentar(dados_rep[:2000])
    diag = meta.diagnosticar()
    niveis = diag.get('n_niveis', 0)
    
    # Alimenta o KG com TODOS os membros do grupo
    for caminho, nome, tam, ent, est in membros:
        try:
            with open(caminho, 'rb') as f:
                dados_arquivo = f.read(500)
            
            # Decodifica como texto (tentativa)
            try:
                texto_preview = dados_arquivo.decode('utf-8', errors='replace')[:300]
            except:
                texto_preview = f'[Dados binarios] {tam} bytes'
            
            if kg:
                kg.aprender_conceito(
                    f'estudo_modelos:{nome}',
                    f'[Grupo {chave}] {nome}: '
                    f'{tam} bytes, ent={ent:.2f}, '
                    f'est={est}, niveis={niveis}'
                    f'\n---\n{texto_preview}',
                    ctx='estudo_modelos'
                )
                total_lessons += 1
        except:
            pass
    
    total_estudados += len(membros)

# PASSO 4: Relatorio final
log(f'Estudo concluido!')
log(f'  Arquivos estudados: {total_estudados}/{len(arquivos_com_sig)}')
log(f'  Grupos formados: {len(grupos)}')
log(f'  Lessons no KG: {total_lessons}')
log(f'  MetaNivel executado: {len(grupos)}x (em vez de {total_estudados}x)')
log(f'  Economia: {(total_estudados - len(grupos)) * 100 / total_estudados:.0f}% de MetaNivel')

# Top 10 grupos
print()
log('Top 10 grupos (mais populosos):')
for chave, membros in sorted(grupos.items(), key=lambda x: -len(x[1]))[:10]:
    ex = os.path.basename(membros[0][0])
    if len(ex) > 40:
        ex = ex[:37] + '...'
    log(f'  Grupo {chave}: {len(membros)} arquivos (ex: {ex})')
