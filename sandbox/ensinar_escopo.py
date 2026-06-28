import json, subprocess, sys
cmd = {
    'cmd': 'ensinar',
    'args': [
        'Correcao de escopo implementada e testada. Pipeline agora detecta se pergunta e geral ou MCR. Para perguntas gerais: pula CR, Enricher, ToT, KG, ContextInfinity. Resposta de teste (buraco de minhoca) saiu 100% limpa sem termos MCR.',
        'Correcao de escopo MCR vs geral',
        'pipeline_executor.py: deteccao de escopo + modo geral. orquestrador.py: escopo propagado para _obter_contexto, pulando KG, ContextCrew filtrado, ContextInfinity pulado para geral. Teste validado com wormhole.',
        'arquitetura'
    ]
}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)
subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py', '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=60)
print('OK')
