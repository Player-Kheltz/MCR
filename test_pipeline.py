#!/usr/bin/env python3
"""Teste do PipelineExecutor com pipeline real."""
import sys, os, time

sys.path.insert(0, '.')
sys.path.insert(0, os.path.join('.', '..', 'Projeto MCR', 'historia', 'scripts', 'mcr_devia'))

from PipelineExecutor import PipelineExecutor
from TemplateExtractor import extrair_template
from DeterministicFiller import preencher_template

# Simula uma pipeline completa
print("=" * 60)
print("TESTE: PipelineExecutor")
print("=" * 60)

# 1. Pipeline de criacao de habilidade (sem kernel, só Python)
print("\n[1] Pipeline: criar_habilidade_spa")
pipeline = ["template_extractor", "deterministic_filler"]

# Conteudo de exemplo (como se viesse de cmd_read)
codigo_exemplo = """
HABILIDADES[ID] = {
    nome = "Rajada de Gelo",
    tipo = "gatilho",
    dominio = {24},
    cooldown = 6,
    categoria = "aoe",
    descricaoEfeito = "Uma rajada congelante.",
    cor = COR.DOM_MAGIA_AGUA_GELO,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.18,
        numProjeteis = 4,
        elemento = COMBAT_ICEDAMAGE,
    },
}
"""

ctx = {
    "entrada": "crie uma habilidade de gelo pro dominio punho",
    "conteudo": codigo_exemplo,
    "task": {"dominio_id": 132, "tipo_efeito": "rajada", "nivel_min": 10},
    "caminhos": ["skills/punho.lua"],
}

pipe = PipelineExecutor()
t0 = time.time()
resultado = pipe.executar(pipeline, contexto=ctx)
t = time.time() - t0

print(f"  Template: {len(resultado.get('template',''))} chars")
print(f"  Gaps encontrados: {resultado.get('gaps', [])}")
print(f"  Gaps restantes (precisam LLM): {resultado.get('gaps_restantes', [])}")
print(f"  Tempo: {t*1000:.2f}ms")

# 2. Pipeline de busca + leitura (simulada)
print("\n[2] Pipeline: cmd_grep + cmd_read (simulado)")
ctx2 = {
    "entrada": "encontre skill de gelo",
    "caminhos": [],
}
pipe2 = PipelineExecutor()
# Simula o que cmd_grep + cmd_read produziriam
ctx2["stdout"] = "[Grep] 1 resultados\n  skills/gelo.lua:L1: HABILIDADES[ID] = {\n[Read] gelo.lua (15 linhas, L1-L15)"
ctx2["caminhos"] = ["skills/gelo.lua"]
ctx2["conteudo"] = "skills/gelo.lua contem habilidades de gelo"

resultado2 = pipe2.executar(["cmd_grep", "cmd_read"], contexto=ctx2)
print(f"  Caminhos: {resultado2.get('caminhos', [])}")
print(f"  Conteudo: {resultado2.get('conteudo', '')[:50]}...")

# 3. Pipeline completa (gaps -> LLM -> write)
print("\n[3] Pipeline: gaps -> LLM -> write")
gaps_restantes = resultado.get("gaps_restantes", [])
if gaps_restantes:
    # Simula LLM preenchendo gaps
    llm_output = f"LLM preencheria: {gaps_restantes}"
    print(f"  Gaps a preencher via LLM: {gaps_restantes}")
    print(f"  LLM output simulado: {llm_output}")
    
    # Simula cmd_write
    print(f"  cmd_write: salvaria arquivo com template preenchido")
    print(f"  Conteudo final seria:\n{resultado.get('preenchido', resultado.get('template',''))[:150]}...")

print("\n[OK] PipelineExecutor funcional")
print(f"  Pipeline 'template_extractor + deterministic_filler' em {t*1000:.1f}ms")
