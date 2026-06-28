import json, subprocess, sys
cmd = {
    'cmd': 'ensinar',
    'args': [
        '4 residuos de hardcoded corrigidos: fragmentador.py, lessons_buffer.py, cmd_aprender_conceito.py, mcr_devia.py (router duplicado). Todos agora usam router padrao de ia.py/util.py. Nao ha mais chamadas diretas ao Ollama com modelos fixos.',
        'Correcao de 4 residuos hardcoded',
        'fragmentador.py: _ia() usa util.gerar(). lessons_buffer.py: _fast() usa util.fast(). cmd_aprender_conceito.py: OrquestradorContexto usa router. mcr_devia.py: router duplicado substituido por import de ia.py.MODELOS.',
        'arquitetura'
    ]
}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)
subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py', '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=60)
print('OK')
