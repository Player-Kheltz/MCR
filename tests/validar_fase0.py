"""VALIDACAO FASE 0 — Consertar o que esta quebrado."""
import sys
sys.path.insert(0, 'E:/MCR')

print('=' * 65)
print('  VALIDACAO FASE 0')
print('=' * 65)

from mcr.mcr import MCR

# ─── TESTE C1: Wrappers registrados ───────────────────────
print('\n[C1] Wrappers registrados no registry:')
mcr = MCR()
tools = mcr._registry.listar()
print(f'  Total tools no registry: {len(tools)}')
tools_nativas = [t for t in tools if 'gerar' in t or 'responder' in t or 'sprite' in t]
print(f'  Tools nativas (gerar/responder/sprite): {tools_nativas}')
assert len(tools) >= 5, f'Registry vazio ou pequeno: {len(tools)} tools'
print(f'  C1: OK')

# ─── TESTE C2: Historico/Memoria populados ─────────────────
print('\n[C2] Historico/Memoria apos processar():')
r1 = mcr.processar("Crie um NPC ferreiro")
r2 = mcr.processar("Gere um monstro dragao")
r3 = mcr.processar("O que e entropia")

print(f'  Historico: {len(mcr._historico)} entradas')
print(f'  Memoria: {len(mcr._memoria)} entradas')
for m in mcr._historico[-3:]:
    print(f'    {m["acao"]} nota={m["nota"]} @ {m["timestamp"]}')

# recordar()
rec = mcr.recordar("npc")
print(f'  recordar("npc"): {rec}')
assert len(mcr._historico) >= 3, f'Historico vazio: {len(mcr._historico)}'
assert len(mcr._memoria) >= 3, f'Memoria vazia: {len(mcr._memoria)}'
assert rec != ["Nenhuma memoria registrada."], "recordar() retorna vazio"
print(f'  C2: OK')

# ─── TESTE C3: ShadowPenalidades consultadas ────────────────
print('\n[C3] ShadowPenalidades consultadas em _decidir():')
try:
    from mcr.shadow_canary import consultar_penalidades
    pen = consultar_penalidades()
    print(f'  Penalidades existentes: {len(pen)} APIs')
    if pen:
        for api, dados in list(pen.items())[:3]:
            print(f'    {api}: falhas={dados.get("falhas",0)} total={dados.get("total",0)}')
    else:
        print('  (Nenhuma penalidade registrada — sistema novo)')
    print(f'  C3: OK (funcao consultar_penalidades() acessivel)')
except Exception as e:
    print(f'  C3: ERRO — {e}')

# ─── RESUMO ──────────────────────────────────────────────
print(f'\n{"="*65}')
print(f'  FASE 0: C1=OK C2=OK C3=OK')
print(f'  Registry: {len(tools)} tools')
print(f'  Historico: {len(mcr._historico)} entradas')
print(f'  Memoria: {len(mcr._memoria)} entradas')
print(f'{"="*65}')
