#!/usr/bin/env python3
"""teste_codigo_final.py — Valida a cascata simbolica (SanityValidator + ShadowCanary).
5 prompts de codigo, mede rota, ensemble, validacao."""
import sys, os, json, time
from pathlib import Path
_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
sys.path.insert(0, str(_PROJ))
sys.path.insert(0, str(_PROJ / 'devia' / 'kernel'))

PROMPTS = [
    ("Gere codigo Lua para um NPC ferreiro que vende espadas e pocoes", "criar_codigo"),
    ("Gere codigo Lua para um NPC guarda que patrulha o porto de Thais", "criar_codigo"),
    ("Crie uma habilidade SPA de cura em area para paladinos", "criar_habilidade_spa"),
    ("Crie um sistema de combate com esquiva e bloqueio", "criar_sistema"),
    ("Gere codigo Lua para um evento global que spawna monstros ao amanhecer", "criar_codigo"),
]

from mcr.pipeline_completo import PipelineCompleto
pipeline = PipelineCompleto()

print(f'{"="*60}')
print(f'  TESTE CASCATA SIMBOLICA — 5 prompts de codigo')
print(f'{"="*60}')
print(f'  Valida: roteamento, ensemble, SanityValidator, ShadowCanary\n')

resultados = []
for i, (prompt, esperado) in enumerate(PROMPTS):
    t0 = time.time()
    try:
        res = pipeline.processar(prompt)
        lat = round(time.time() - t0, 2)
        rota = res.get("rota", "?")
        classe = res.get("classe", "?")
        conf = res.get("confianca", 0)
        vc = res.get("validacao_codigo", {})
        validacoes = vc.get("validacoes", [])
        valido = vc.get("valido", False)
        erro = None
    except Exception as e:
        lat = round(time.time() - t0, 2)
        rota = "erro"
        classe = "?"
        conf = 0
        validacoes = []
        valido = False
        erro = str(e)[:120]

    ok_classe = "OK" if classe == esperado else f"ESPERAVA {esperado}"
    resultados.append({
        "prompt": prompt[:55],
        "classe": classe,
        "conf": round(conf, 3),
        "rota": rota,
        "tempo": lat,
        "valido_simbolico": valido,
        "validacoes": validacoes,
        "erro": erro,
    })
    print(f'  #{i} [{rota}] {classe} (conf={conf:.2f}) {ok_classe} | {lat}s')
    for v in validacoes:
        status_v = "OK" if v.get("valido") else "FALHA"
        et = v.get("etapa", "?")
        print(f'       {status_v}: {et}')
    if erro:
        print(f'       ERRO: {erro}')
    print()

print(f'{"="*60}')
print(f'  RESUMO')
print(f'{"="*60}')
acertos = 0
for idx, r in enumerate(resultados):
    if idx < len(PROMPTS) and r["classe"] == PROMPTS[idx][1]:
        acertos += 1
print(f'  Roteamento: {acertos}/{len(PROMPTS)} classes corretas')
print(f'  Rotas: {json.dumps(list({r["rota"] for r in resultados}))}')
print(f'  Ensemble usado: {sum(1 for r in resultados if r["rota"] == "ensemble")}/{len(PROMPTS)}')
sv_count = sum(1 for r in resultados for v in r.get("validacoes", []) if v.get("etapa") == "SanityValidator")
sc_count = sum(1 for r in resultados for v in r.get("validacoes", []) if v.get("etapa") == "ShadowCanary")
sv_falhas = sum(1 for r in resultados for v in r.get("validacoes", []) if v.get("etapa") == "SanityValidator" and not v.get("valido"))
sc_falhas = sum(1 for r in resultados for v in r.get("validacoes", []) if v.get("etapa") == "ShadowCanary" and not v.get("valido"))
print(f'  SanityValidator: {sv_count}/{len(PROMPTS)} requests ({sv_falhas} com APIs desconhecidas)')
print(f'  ShadowCanary: {sc_count}/{len(PROMPTS)} requests ({sc_falhas} com crash)')
print(f'  Tempo medio: {sum(r["tempo"] for r in resultados)/len(resultados):.1f}s')
print(f'  Erros: {sum(1 for r in resultados if r["erro"])}')
