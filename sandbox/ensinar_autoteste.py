import json, subprocess, sys

cmd = {
    'cmd': 'ensinar',
    'args': [
        'Auto-Teste Definitivo implementado. Sistema de auto-teste com gerador FAST, execucao de ciclo, auto-critica MCR, avaliacao cega Cloud, calculo de gaps e feedback arquitetural. Documentacao em docs/AUTO_TESTE.md. Comando: cmd_autoteste.py. Regras: autoteste_regras.json.',
        'Auto-Teste Definitivo implementado',
        'Teste universal que se adapta via FAST com regras. Gera perguntas de conhecimento geral (nunca MCR). Ciclo: gerar -> executar MCR -> auto-critica -> avaliacao Cloud -> gaps -> feedback. Historico persistido. Planos de teste antigos arquivados.',
        'teste'
    ]
}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)
subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py', '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=60)
print('OK')
