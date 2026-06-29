"""Teste do tech stack universal via IA."""
import sys, json
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.task_planner import TaskPlanner
from modulos.ia import IA

ia = IA()
planner = TaskPlanner(ia=ia)

print("=== Teste Tech Stack Universal ===\n")

testes = [
    "Cria um jogo de plataforma em Python com 3 fases",
    "Cria um jogo em JavaScript com Phaser",
    "Cria um jogo em Lua com Love2D",
    "Cria um jogo em Rust usando Bevy",
    "Cria um jogo em C++ com SDL2",
    "Cria um jogo em Go com Ebitengine",
    "Cria um jogo em C# com MonoGame",
    "Cria um jogo em Kotlin com LibGDX",
]

for req in testes:
    stack = planner._extrair_tech_stack(req)
    print(f"  Request: {req[:50]}...")
    print(f"    -> {stack.get('linguagem','?')} | {stack.get('ext','?')} | deps: {stack.get('deps','?')} | cmd: {stack.get('comando_run','?')}")
    
    # Testa se os params refletem a linguagem
    params = planner._extrair_params('gerar_modulo_main', req)
    desc = params.get('descricao', '')
    if stack.get('ext', '.py') not in desc:
        print(f"    [AVISO] Extensao {stack.get('ext')} nao encontrada na descricao")
    print()

print("=== TESTE CONCLUIDO ===")
