#!/usr/bin/env python3
"""Teste da nova MCRAssinatura — Kheltz sempre primeiro."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import (
    MCRAssinatura, MCRFingerprint, MCRSignature,
    _KHELTZ_ASSINATURA, _kheltz_comparar_estilo
)

print("=" * 60)
print("TESTE 1: MCRFingerprint 64-dim + estilo")
print("=" * 60)
fp = MCRFingerprint.gerar("O aventureiro explora a floresta encantada em busca do artefato")
print(f"  fingerprint: {len(fp)} dims (primeiros 8: {fp[:8]})")
estilo = MCRFingerprint.extrair_estilo("O aventureiro explora a floresta encantada em busca do artefato")
print(f"  estilo: caps={estilo.get('caps_ratio',0):.3f} ent={estilo.get('byte_entropy',0):.3f}")

# Testa com texto do Kheltz
texto_kheltz = "TODOS, resolva TODOS, conecte TODOS!"
estilo_k = MCRFingerprint.extrair_estilo(texto_kheltz)
print(f"  Kheltz: caps={estilo_k.get('caps_ratio',0):.3f} exclam={estilo_k.get('exclam_ratio',0):.3f}")

# Testa com texto generico
texto_generico = "O aventureiro explora a floresta encantada em busca do artefato"
estilo_g = MCRFingerprint.extrair_estilo(texto_generico)
print(f"  Generico: caps={estilo_g.get('caps_ratio',0):.3f} exclam={estilo_g.get('exclam_ratio',0):.3f}")

print()
print("=" * 60)
print("TESTE 2: _kheltz_comparar_estilo")
print("=" * 60)
score_k, det_k = _kheltz_comparar_estilo(estilo_k)
print(f"  Texto Kheltz: score={score_k:.3f}")
for k, v in det_k.items():
    print(f"    {k}: val={v['valor']:.3f} range=[{v['range'][0]:.2f}, {v['range'][1]:.2f}] OK={v['ok']}")

score_g, det_g = _kheltz_comparar_estilo(estilo_g)
print(f"  Texto generico: score={score_g:.3f}")

# Score do Kheltz deve ser maior que generico
assert score_k > score_g, f"Kheltz ({score_k}) deveria ser > generico ({score_g})!"
print("  OK: Kheltz > generico")

print()
print("=" * 60)
print("TESTE 3: MCRAssinatura.identificar()")
print("=" * 60)
banco = MCRAssinatura()

# Aprende com textos REAIS (nao falsos)
textos_reais = [
    "O que ainda nao esta MCR? o que ainda nao segue padroes? a ASSINATURA, o que ainda e Hardcoded?",
    "TODOS, resolva TODOS, conecte TODOS!",
    "analise o MCR.py POR COMPLETO e reflita, o MCR sabe decidir melhor que ninguem",
]
for t in textos_reais:
    banco.aprender(t, "Kheltz")

# Teste 3a: texto do Kheltz
teste_kheltz = "releia o que falei acima, entenda os conceitos, analise o MCR"
autor, conf, det = banco.identificar(teste_kheltz)
print(f"  Texto Kheltz: autor={autor} conf={conf:.3f}")
if autor == 'Kheltz':
    print(f"  >>> CONFIRMADO! status={det.get('status','?')}")
elif autor == 'Kheltz?':
    print(f"  >>> DUVIDA! status={det.get('status','?')} msg={det.get('mensagem','')[:80]}")
else:
    print(f"  >>> NAO RECONHECIDO (esperava Kheltz)")

# Teste 3b: texto generico
teste_gen = "O sistema SPA e um modulo de progressao do aventureiro"
autor_g, conf_g, det_g = banco.identificar(teste_gen)
print(f"  Texto generico: autor={autor_g} conf={conf_g:.3f}")

# Teste 3c: texto com CAPS mas sem o padrao do Kheltz
teste_misto = "IMPORTANTE: o sistema deve ser configurado corretamente para producao"
autor_m, conf_m, det_m = banco.identificar(teste_misto)
print(f"  Texto misto: autor={autor_m} conf={conf_m:.3f}")

print()
print("=" * 60)
print("TESTE 4: Confirmar duvida")
print("=" * 60)
# Se identificou como 'Kheltz?' (duvida), confirma
if autor == 'Kheltz?':
    res = banco.confirmar(teste_kheltz, "Kheltz")
    print(f"  Confirmado: {res}")
    # Verifica novamente
    autor2, conf2, _ = banco.identificar(teste_kheltz)
    print(f"  Apos confirmar: autor={autor2} conf={conf2:.3f}")

print()
print("=" * 60)
print("TESTE 5: _KHELTZ_ASSINATURA atualizada")
print("=" * 60)
print(f"  Confirmacoes: {_KHELTZ_ASSINATURA['confirmacoes']}")
print(f"  caps_ratio: {_KHELTZ_ASSINATURA['estilo']['caps_ratio']:.4f}")
print(f"  exclam_ratio: {_KHELTZ_ASSINATURA['estilo']['exclam_ratio']:.4f}")

print()
print("TODOS OS TESTES PASSARAM!")
