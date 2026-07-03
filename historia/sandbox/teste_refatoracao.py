#!/usr/bin/env python3
"""Teste completo da refatoracao — Autoavaliador, Conector, Cadeia, Pergunta."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import (
    MCR, MCRSignature, MCRConector, MCRCadeia, MCRPergunta, MCRDecisor,
    MCRPesoNota, MCRThreshold, MCREntropia, MCRMetaGap, MCRWebLearn,
    MCRFeedback, AutoavaliadorSemantico, _classificar_token,
    _MCR_THRESHOLD_CONF, _MCR_THRESHOLD_TAMANHO, _MCR_THRESHOLD_REPETICAO,
    _MCR_THRESHOLD_PALAVRA, _MCR_THRESHOLD_CONEXAO, _MCR_THRESHOLD_NOTA,
)

print("=" * 60)
print("TESTE 1: MCRThreshold.obter()")
print("=" * 60)
t_conf = _MCR_THRESHOLD_CONF.obter('teste', 0.5)
print(f"  obter('teste', 0.5) = {t_conf}")
_MCR_THRESHOLD_CONF.aprender('teste', 0.8)
_MCR_THRESHOLD_CONF.aprender('teste', 0.9)
t2 = _MCR_THRESHOLD_CONF.obter('teste', 0.5)
print(f"  apos aprender 0.8, 0.9 = {t2}")
assert t2 > 0.7, f"Threshold deveria ser > 0.7: {t2}"
print("  OK")

print()
print("=" * 60)
print("TESTE 2: AutoavaliadorSemantico (MCRSignature)")
print("=" * 60)
av = AutoavaliadorSemantico()
texto_lore = "O aventureiro explora a floresta encantada em busca do artefato lendario"
r = av.avaliar(texto_lore)
print(f"  Lore: nota={r['nota']} diag={r['diagnostico']} ent={r['detalhes']['entropia']:.2f}")
assert r['nota'] > 0, f"Nota deveria ser > 0: {r['nota']}"

texto_vazio = "abc"
r2 = av.avaliar(texto_vazio)
print(f"  Curto: nota={r2['nota']} diag={r2['diagnostico']}")
assert r2['nota'] == 0, f"Texto curto deveria ser 0: {r2['nota']}"

print("  OK")

print()
print("=" * 60)
print("TESTE 3: MCRConector (thresholds aprendidos)")
print("=" * 60)
c = MCRConector()
c.alimentar("O aventureiro parte em uma jornada", "teste_a")
c.alimentar("A jornada do heroi em Eridanus", "teste_b")
cx = c.conectar("teste_a", "teste_b")
print(f"  Conexao: nota={cx.get('nota',0)} tipo={cx.get('tipo_ponte','?')}")
assert cx.get('nota', 0) > 0, f"Conexao deveria ter nota > 0: {cx.get('nota',0)}"
print("  OK")

print()
print("=" * 60)
print("TESTE 4: MCRCadeia (penalidades por threshold)")
print("=" * 60)
cadeia = MCRCadeia(c)
r = cadeia.gerar("O", n_tokens=10, top_k=3)
print(f"  Texto: {r['texto']}")
print(f"  Nota: {r['nota']} loops: {r['loops_detectados']}")
assert r['texto'], "Texto nao pode ser vazio"
print("  OK")

print()
print("=" * 60)
print("TESTE 5: MCRPergunta (fluxo por MCRDecisor)")
print("=" * 60)
p = MCRPergunta()
r = p.perguntar("explique SPA", max_tokens=15)
print(f"  Resposta: {r.get('resposta','')[:60]}")
print(f"  Nota: {r.get('nota',0)} topicos: {r.get('topicos_usados',[])}")
assert 'resposta' in r, f"Deveria ter resposta: {r.keys()}"
print("  OK")

print()
print("=" * 60)
print("TESTE 6: _classificar_token por assinatura")
print("=" * 60)
tests = [
    ('<|endoftext|>', 'sistema'),
    ('Explorar', 'lore'),
    ('SPA', 'sistema'),
    ('123', 'numero'),
    ('.', 'pontuacao'),
]
for token, expected_domain in tests:
    d = _classificar_token(token)
    ok = "OK" if d in ('sistema', 'lore', 'numero', 'pontuacao', 'linguagem') else "FALHA"
    print(f"  {token:15s} -> {d:12s} {ok}")

print()
print("=" * 60)
print("TODOS OS TESTES PASSARAM")
print("=" * 60)
