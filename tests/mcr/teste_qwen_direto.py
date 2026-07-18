#!/usr/bin/env python3
"""teste_qwen_direto.py — Testa Qwen Coder com prompt de codigo puro."""
import sys, os, time, json
from pathlib import Path
_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
sys.path.insert(0, str(_PROJ))
sys.path.insert(0, str(_PROJ / 'devia' / 'kernel'))

from mcr.pipeline_completo import PipelineCompleto
p = PipelineCompleto()

PROMPTS = [
    'Gere codigo Lua para um NPC ferreiro que vende espadas e pocoes',
    'Gere codigo Lua para um NPC guarda que patrulha o porto de Thais',
    'Gere codigo Lua para um evento global que spawna monstros ao amanhecer',
    'Crie uma habilidade SPA de cura em area para paladinos',
    'Crie um sistema de combate com esquiva e bloqueio',
]

for i, prompt in enumerate(PROMPTS):
    t0 = time.time()
    res = p.processar(prompt)
    lat = round(time.time() - t0, 2)
    rota = res.get('rota', '?')
    classe = res.get('classe', '?')
    modelo = res.get('modelo', '?')
    vc = res.get('validacao_codigo', {})
    resposta = res.get('resposta', '')[:500]
    print(f'  #{i} [{rota}] {classe} modelo={modelo} {lat}s')
    for v in vc.get('validacoes', []):
        print(f'  {v.get("etapa","?")}: valido={v.get("valido")} status={v.get("status","?")} chamadas_desc={v.get("chamadas_desconhecidas", [])[:3]}')
    print(f'  Resposta[500]:\n{resposta}\n')
