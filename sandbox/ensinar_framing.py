import json, subprocess, sys
cmd = {
    'cmd': 'ensinar',
    'args': [
        'MCR_IDENTITY.md corrigido: removidas TODAS as negacoes que mencionavam termos errados. Agora usa apenas afirmacoes positivas. CR.gerar_instrucao() e conselho.py validacao ajustados. Teste confirmou: 0 ocorrencias de Minecraft na resposta.',
        'Framing positivo no MCR-DevIA',
        'NUNCA mencionar o termo errado. Apenas afirmar o correto. Resolve o efeito elefante rosa (negacao ativa vies do modelo).',
        'otimizacao'
    ]
}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)
subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py', '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=60)
print('OK')
