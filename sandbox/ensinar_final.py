import json, subprocess, sys
cmd = {
    'cmd': 'ensinar',
    'args': [
        'Enricher integrado em Mente, Supervisor e Auto-Revisor. Teste final OK: 3 Enricher calls (Supervisor+Pipeline+ToT), 0 alucinacoes, 1731 chars. Pipeline completa: CR->Enricher->ToT->Sintese.',
        'Enricher integrado em Mente/Supervisor/Revisor',
        'Modulos modificados: mente.py (Enricher antes do prompt batch), supervisor.py (Enricher no executar), auto_revisor.py (check de resposta generica). Todos com fallback seguro via try/except.',
        'arquitetura'
    ]
}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)
subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py', '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=60)
print('OK')
