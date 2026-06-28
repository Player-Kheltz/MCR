import json, subprocess, sys
cmd = {
    'cmd': 'ensinar',
    'args': [
        'Tree of Thought implementado. 3 perspectivas paralelas (analitico, criativo, critico) + sintese final. Filtro de alucinacoes antes da sintese. Framing positivo no prompt de sintese. Resposta com 1976 chars, 0 alucinacoes, inclui exemplo de codigo Lua.',
        'Tree of Thought implementado',
        'Novo modulo tree_of_thought.py. Integrado no pipeline_executor. 3 threads paralelas chamando o Orquestrador com perspectivas diferentes. Sintese via model call separada. Fallback para Orquestrador direto se ToT falhar.',
        'arquitetura'
    ]
}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)
subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py', '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=60)
print('OK')
