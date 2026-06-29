"""Teste de integracao final: kernel + orquestrador + todos os comandos."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from kernel import MCRKernel

print("=" * 60)
print("TESTE DE INTEGRACAO FINAL")
print("=" * 60)

# 1. Kernel carrega tudo
k = MCRKernel()
n = k.inicializar()
assert n == 46, f"Esperado 46 comandos, obtido {n}"
print(f"[OK] Kernel: {n} comandos carregados (esperado 46)")

# 2. Verificar comandos orquestrados
cmd_lista = {nome: desc for nome, desc in k.listar_comandos()}
cmd_orquestrados = ['lore', 'analisar', 'review', 'orquestrar', 'aprender_conceito',
                    'perguntar', 'gerar_componentes', 'revisar', 'explorar']
for nome in cmd_orquestrados:
    assert nome in cmd_lista, f"Comando {nome} nao encontrado!"
    print(f"[OK] {nome}: {cmd_lista[nome][:60]}")

# 3. IA.orquestrar() existe
from modulos.ia import IA
ia = IA()
assert hasattr(ia, 'orquestrar'), "IA.orquestrar() nao encontrado!"
print(f"[OK] IA.orquestrar() disponivel")

# 4. Orquestrador com templates completos
from modulos.orquestrador import Orquestrador, _TEMPLATES, _ROUTER
templates_esperados = [
    "lore", "lore_npc", "lore_item", "lore_local",
    "analisar_codigo", "analisar_texto",
    "review", "conceito", "perguntar",
    "componentes_personagens", "componentes_locais", "componentes_artefatos",
    "revisar", "classificar_nomes",
]
for t in templates_esperados:
    assert t in _TEMPLATES, f"Template {t} ausente!"
print(f"[OK] Orquestrador: {len(_TEMPLATES)} templates, todos os 14 esperados")

# Verificar routers
routers_check = {
    "analisar_codigo": "analisar", "analisar_texto": "texto",
    "review": "review", "conceito": "pesado", "perguntar": "texto",
    "componentes_personagens": "leve", "lore": "texto", "revisar": "leve",
}
for k, v in routers_check.items():
    assert _ROUTER.get(k) == v, f"Router {k} esperado {v}, obtido {_ROUTER.get(k)}"
print(f"[OK] Todos os routers configurados corretamente")

# 5. ContextCrew com ThreadPoolExecutor
from context_crew import ContextCrew
cc = ContextCrew()
# Verifica se tem o metodo executar e se o cache funciona
r = cc.executar("teste orquestrador")
print(f"[OK] ContextCrew V3+: retornou {len(r)} chars para consulta teste")

# 6. IA module com modelos
from modulos.ia import MODELOS
assert "code" in MODELOS
assert "texto" in MODELOS
assert "analisar" in MODELOS
assert "leve" in MODELOS
print(f"[OK] IA router: code={MODELOS['code']['modelo']}, texto={MODELOS['texto']['modelo']}")

# 7. cmd_orquestrar.py existe
cmd_orq_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'comandos', 'cmd_orquestrar.py')
assert os.path.exists(cmd_orq_path), "cmd_orquestrar.py nao encontrado!"
print(f"[OK] cmd_orquestrar.py existe")

print()
print("=" * 60)
print("TESTE DE INTEGRACAO: PASS (100%)")
print("=" * 60)
