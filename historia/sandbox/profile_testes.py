#!/usr/bin/env python3
"""Identifica qual teste esta demorando no autoteste."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import *

t_global = time.time()

# Testes a partir do MCRFeedback (o que vem depois de MCRMetaNivel)
testes = [
    ("MCRFeedback", lambda: MCRFeedback().processar_com_feedback("Explique SPA", max_tentativas=1)),
    ("MCRAutoStart", lambda: MCRAutoStart.iniciar()),
    ("MCRSelfIndex", lambda: (_ := MCRSelfIndex(), _.indexar(), _)),
    ("MCRSelfHeal", lambda: MCRSelfHeal.verificar()),
    ("MCRSignature.extrair", lambda: MCRSignature.extrair("Explique SPA do projeto MCR")),
    ("MCRSignature.comparar", lambda: MCRSignature.comparar(
        MCRSignature.extrair("SPA = Sistema"), MCRSignature.extrair("SPA = Progressao"))),
    ("MCRSignature.metaniveis", lambda: MCRSignature.metaniveis("Explique SPA")),
    ("MCRSession", lambda: (_ := MCRSession(), _.registrar("teste", "resposta", "autor"),
                             _.salvar_estado(), _.carregar_estado(), _)),
    ("MCRAssinatura.aprender", lambda: (_ := MCRAssinatura(),
        _.aprender("Explique SPA", "Kheltz"), _.aprender("Crie NPC", "Kheltz"), _)),
    ("MCRAssinatura.identificar", lambda: MCRAssinatura().identificar("Explique o SPA")),
    ("MCRAssinatura.confirmar", lambda: MCRAssinatura().confirmar("Explique o SPA", "Kheltz")),
    ("MCRWebLearn.estudar_gaps", lambda: MCRWebLearn().estudar_gaps(1)),
    ("MCRGeracao", lambda: (_ := MCRGeracao(), _.gerar("Explique SPA"), _)),
]

for nome, fn in testes:
    t0 = time.time()
    try:
        resultado = fn()
        if isinstance(resultado, dict):
            chaves = list(resultado.keys())[:3]
        elif hasattr(resultado, '__class__'):
            chaves = str(type(resultado).__name__)
        else:
            chaves = str(resultado)[:40]
    except Exception as e:
        chaves = f"ERRO: {e}"
    dt = time.time() - t0
    status = "LENTO" if dt > 10 else "OK"
    print(f'[{time.time()-t_global:.1f}s] {nome:30s} {dt:6.1f}s {status} -> {chaves}', flush=True)

print(f'\nTotal: {time.time()-t_global:.1f}s', flush=True)
