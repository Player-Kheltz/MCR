#!/usr/bin/env python3
"""MCR estuda Modelos IA — zero hardcode de formato."""
import sys, os, time as _time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCR, MCRSignature, MCRFingerprint, MCRMetaNivel, MCRKGAuto, _get_kg

T0 = _time.time()
def log(msg):
    print(f'[{_time.time()-T0:.1f}s] {msg}', flush=True)

log('MCR estudando Modelos IA...')

# 1. MCR descobre os arquivos (sem hardcode de extensao)
raiz = r'E:\Modelos IA'
todos_arquivos = []
for pasta, subpastas, arquivos in os.walk(raiz):
    for arq in arquivos:
        caminho = os.path.join(pasta, arq)
        todos_arquivos.append(caminho)

log(f'Descobertos {len(todos_arquivos)} arquivos')

# 2. MCR estuda cada arquivo por ASSINATURA DE BYTES (universal)
#    Nao importa se e .txt, .html, .md, .bin — sao todos bytes
limite = min(50, len(todos_arquivos))  # 50 arquivos para comecar
estudados = 0
erros = 0

kg = _get_kg()

for caminho in todos_arquivos[:limite]:
    nome = os.path.basename(caminho)
    try:
        with open(caminho, 'rb') as f:
            dados_brutos = f.read(10000)  # primeiros 10KB
        if len(dados_brutos) < 50:
            continue
        
        # 2a. MCR aprende a SEQUENCIA DE BYTES do arquivo
        mk_arquivo = MCR(f'estudo_{nome[:20]}')
        mk_arquivo.aprender_sequencia(list(dados_brutos[:2000]))
        
        # 2b. MCRSignature extrai a ASSINATURA UNICA do arquivo
        sig = MCRSignature.extrair(dados_brutos[:2000], rapido=True)
        
        # 2c. MCRMetaNivel descobre QUANTOS NIVEIS existem
        meta = MCRMetaNivel()
        meta.alimentar(dados_brutos[:2000])
        diag = meta.diagnosticar()
        niveis = diag.get('n_niveis', 0)
        
        # 2d. Alimenta o KG com a descoberta
        if kg:
            # Tenta ler como texto
            try:
                texto = dados_brutos.decode('utf-8', errors='replace')[:500]
            except:
                texto = f'[Dados binarios] {len(dados_brutos)} bytes'
            
            kg.aprender_conceito(
                f'estudo_modelos:{nome}',
                f'MCR estudou {nome}: '
                f'{len(dados_brutos)} bytes, '
                f'entropia={sig.get("entropia",0):.2f}, '
                f'estados={sig.get("estados",0)}, '
                f'niveis={niveis}'
                f'\n---\n{texto[:300]}',
                ctx='estudo_modelos'
            )
        
        estudados += 1
        if estudados % 10 == 0:
            log(f'Estudados {estudados}/{limite}...')
            
    except Exception as e:
        erros += 1
        if erros < 3:
            log(f'Erro em {nome}: {e}')

# 3. Relatorio final
log(f'Estudo concluido: {estudados} arquivos estudados, {erros} erros')
if kg:
    licoes = kg._get_licoes()
    novas = [l for l in licoes if l.get('ctx') == 'estudo_modelos']
    log(f'Novas lessons no KG: {len(novas)}')
    if novas:
        for l in novas[:5]:
            log(f'  -> {l.get("erro","?")}: {l.get("solucao","")[:60]}')
