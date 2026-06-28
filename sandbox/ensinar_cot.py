import json, subprocess, sys
cmd = {
    'cmd': 'ensinar',
    'args': [
        'Pendencia adicionada: Chain-of-Thought (CoT) no MCR-DevIA. O qwen2.5-coder:14b nao tem CoT nativo como o deepseek-r1. CoT pode ser implementado via prompt com instrucao de raciocinio passo a passo, ou usando deepseek-r1 como modelo de pensamento antes do qwen14b gerar a resposta final.',
        'CoT pendente no MCR-DevIA',
        'Implementacao possivel: (1) Prompt engineering adicionando raciocinio passo a passo nos templates. (2) Usar deepseek-r1:7b para pensar e qwen14b para gerar. (3) Arvore de pensamento com multiplas chamadas.',
        'pendencia'
    ]
}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)
subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py', '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=60)
print('OK')
