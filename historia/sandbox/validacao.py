#!/usr/bin/env python3
"""Validacao completa do sistema MCR."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

t0 = time.time()
print('=' * 60)
print('VALIDACAO 1: Integridade do MCR.py')
print('=' * 60)

import modulos.MCR as mcr
print(f'  Import OK: {time.time()-t0:.1f}s')

mcr_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos', 'MCR.py')
mcr_path = os.path.abspath(mcr_path)
with open(mcr_path, encoding='utf-8') as f:
    linhas = f.readlines()
print(f'  Linhas: {len(linhas)}')
print(f'  Tamanho: {os.path.getsize(mcr_path)/1024:.0f} KB')

essenciais = ['MCR', 'MCRSignature', 'MCRFingerprint', 'MCRDecisor', 'MCRPesoNota',
              'MCRThreshold', 'MCRConector', 'MCRCadeia', 'MCRPergunta',
              'MCRAssinatura', 'MCRKGAuto', 'MCRFuel', 'MCRMetaGap',
              'MCRWebLearn', 'MCRSession', 'MCRSegmentador', 'MCRPersistencia',
              'MCRBoot', 'MCRFilosofia', 'MCRFeedback', 'MCRMetaNivel',
              'MCRSelfIndex', 'MCRSelfHeal', 'MCRDocIndex', 'MCRGeracao']
presentes = [c for c in essenciais if getattr(mcr, c, None) is not None]
print(f'  Classes essenciais: {len(presentes)}/{len(essenciais)}')
if len(presentes) < len(essenciais):
    print(f'  FALTAM: {set(essenciais) - set(presentes)}')

print()
print('VALIDACAO 2: _KHELTZ_ASSINATURA')
print('=' * 60)
if hasattr(mcr, '_KHELTZ_ASSINATURA'):
    k = mcr._KHELTZ_ASSINATURA
    estilo = k.get('estilo', {})
    print(f'  Definida: True')
    print(f'  caps_ratio: {estilo.get("caps_ratio", "N/A")}')
    print(f'  exclam_ratio: {estilo.get("exclam_ratio", "N/A")}')
    print(f'  byte_entropy: {estilo.get("byte_entropy", "N/A")}')
    print(f'  Confirmacoes: {k.get("confirmacoes", 0)}')
else:
    print('  NAO DEFINIDA!')

print()
print('VALIDACAO 3: Cache _SIG_CACHE')
print('=' * 60)
if hasattr(mcr, '_SIG_CACHE'):
    print(f'  _SIG_CACHE: presente, {len(mcr._SIG_CACHE)} entradas')
else:
    print('  _SIG_CACHE: ausente')

print()
print('VALIDACAO 4: MCRAssinatura identifica Kheltz')
print('=' * 60)
banco = mcr.MCRAssinatura()
banco.aprender('MCR deve prioriar a ASSINATURA. o MCR e CAPAZ DE CRIAR!', 'Kheltz', rapido=True)
banco.aprender('TODOS resolva TODOS conecte TODOS!', 'Kheltz', rapido=True)
autor, conf, det = banco.identificar('analise o MCR a ASSINATURA o que ainda e Hardcoded?')
print(f'  Texto Kheltz -> autor={autor} conf={conf:.2f}')
status = 'CONFIRMADO' if autor == 'Kheltz' else 'DUVIDA' if '?' in str(autor) else 'OUTRO'
print(f'  Status: {status}')

autor2, conf2, _ = banco.identificar('O sistema SPA gerencia a progressao do aventureiro')
print(f'  Texto generico -> autor={autor2} conf={conf2:.2f}')

print()
print('VALIDACAO 5: Auto-Popular sem _salvar() no loop')
print('=' * 60)
t1 = time.time()
banco2 = mcr.MCRAssinatura()
for i in range(100):
    banco2.aprender('Mensagem de teste ' + str(i), 'teste', rapido=True)
print(f'  100x aprender(rapido) sem _salvar: {time.time()-t1:.1f}s')
print(f'  Banco tem {len(banco2.autores_conhecidos())} autores')

print()
print('VALIDACAO 6: _MCR_DATA nos dados internos')
print('=' * 60)
pers = mcr.MCRPersistencia(mcr_path)
dados = pers.carregar_dados()
nd = len(dados.get('licoes', []))
print(f'  Licoes internas: {nd}')
print(f'  Assinaturas: {sum(len(v) for v in dados.get("assinaturas", {}).values())}')
print(f'  Cache: {len(dados.get("cache", {}))}')

print()
print('VALIDACAO 7: KG Cache global')
print('=' * 60)
from modulos.kg import _KG_CACHE
cs = str(_KG_CACHE.get('checksum', 'None'))
print(f'  _KG_CACHE checksum: {cs[:16]}...' if cs != 'None' else '  _KG_CACHE checksum: None')
print(f'  _KG_CACHE licoes: {len(_KG_CACHE.get("licoes", []))}')

print()
print(f'Total: {time.time()-t0:.1f}s')
print('VALIDACAO COMPLETA')
