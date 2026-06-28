"""Comando: master - Executa o MasterAgent (AGI local hibrida).

Uso:
    python MCR_DevIA-Kernel.py master "<request>"
    python MCR_DevIA-Kernel.py master "<request>" --type npc_shop

Tipos de tarefa (opcional):
    npc_shop, pergunta_simples, criar_codigo, analisar_codigo
"""
import os, sys, json, time


def executar(kg, ia, args):
    """Executa o comando master."""
    if not args or len(args) < 1:
        return "Uso: master <request> [--type <tipo>]\n\nTipos: npc_shop, pergunta_simples, criar_codigo, analisar_codigo"

    request = args[0]
    task_type = ''

    # Parse --type
    if '--type' in args:
        idx = args.index('--type')
        if idx + 1 < len(args):
            task_type = args[idx + 1]

    # Importa MasterAgent
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from modulos.master_agent import MasterAgent
    except ImportError as e:
        return f"Erro ao carregar MasterAgent: {e}"

    agent = MasterAgent()
    t0 = time.time()

    print(f"\n{'='*60}")
    print(f"  MASTER AGENT")
    print(f"  Request: {request[:80]}{'...' if len(request) > 80 else ''}")
    if task_type:
        print(f"  Tipo: {task_type}")
    print(f"{'='*60}\n")

    resultado = agent.executar(request, task_type)

    tempo = round(time.time() - t0, 1)
    artefato = resultado.get('artefato', {})
    resposta_final = artefato.get('resposta_final', '')

    print(f"\n{'='*60}")
    print(f"  RESULTADO FINAL")
    print(f"  Sucesso: {resultado['sucesso']}")
    print(f"  Subtarefas: {resultado['n_sucesso']}/{resultado['n_subtarefas']}")
    print(f"  Tempo: {resultado['tempo']}s")
    print(f"{'='*60}\n")

    if resposta_final:
        # Trunca se muito longa (print completo vai pra .mcr_resposta.txt)
        max_print = 2000
        print(resposta_final[:max_print])
        if len(resposta_final) > max_print:
            print(f"\n... [resposta truncada, {len(resposta_final)} chars total]")

    # Salva resposta completa
    try:
        sandbox = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'sandbox')
        resp_path = os.path.join(sandbox, '.mcr_resposta.txt')
        with open(resp_path, 'w', encoding='utf-8') as f:
            f.write(resposta_final or 'Sem resposta')
        print(f"\n[Resposta completa salva em .mcr_resposta.txt]")
    except Exception as e:
        print(f"\n[Erro ao salvar resposta: {e}]")

    return f"MasterAgent concluido em {tempo}s. {resultado['n_sucesso']}/{resultado['n_subtarefas']} subtarefas OK."


COMANDO = {
    "name": "master",
    "handler": executar,
    "desc": "Executa o MasterAgent para fazer QUALQUER coisa",
    "uso": "master <request> [--type <tipo>]",
    "exemplos": [
        'master "Cria um jogo de plataforma em Python"',
        'master "O que e SPA no MCR?"',
        'master "Cria um ferreiro em Eridanus" --type npc_shop',
    ],
}


def register():
    return COMANDO


def init_module(contexto):
    contexto['cmd_master'] = executar
    return 'cmd_master', executar
