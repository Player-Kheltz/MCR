"""Registra licoes do dia no KG."""
import json, subprocess, sys

licoes = [
    {
        'oque': 'Upgrade qwen14b com GPU forcing (main_gpu=0, num_gpu=99)',
        'contexto': 'qwen2.5-coder:14b rodava a 15% GPU sem forcing. Com main_gpu=0 e num_gpu=99, foi a 97%.',
        'solucao': 'Adicionar main_gpu e num_gpu nas configs dos modelos pesados em ia.py e util.py.',
        'categoria': 'otimizacao'
    },
    {
        'oque': 'Framing positivo vs negativo (efeito elefante rosa)',
        'contexto': 'MCR_IDENTITY.md tinha "NUNCA confunda MCR com Minecraft". Isso ativava o termo no modelo.',
        'solucao': 'NUNCA mencionar termos errados. Apenas afirmar o correto. Remover (NAO e X) de todo o codigo.',
        'categoria': 'prompt_engineering'
    },
    {
        'oque': 'Auto-Teste Definitivo com auto-critica MCR',
        'contexto': 'Teste comparativo Cloud vs MCR com geracao de perguntas via FAST, auto-critica e gaps.',
        'solucao': 'cmd_autoteste.py implementado. Gera perguntas, executa MCR, coleta auto-critica. repositorio em autoteste_historico.json.',
        'categoria': 'teste'
    },
    {
        'oque': 'Deteccao de escopo MCR vs Conhecimento Geral',
        'contexto': 'MCR-DevIA forcava contexto MCR em perguntas gerais (mudancas climaticas, relatividade).',
        'solucao': 'Pipeline detecta termos MCR. Se geral: pula CR, Enricher, ToT, KG, ContextInfinity. Escopo propagado via params.',
        'categoria': 'arquitetura'
    },
    {
        'oque': '14b nao vale upgrade para analise de codigo vs deepseek7b',
        'contexto': 'deepseek-r1:7b detectou SQL injection e foi mais rapido que qwen14b. qwen14b teve falso positivo.',
        'solucao': 'Manter deepseek-r1:7b para analisar/review. qwen14b para pesado (geracao de respostas).',
        'categoria': 'modelos'
    },
]

for l in licoes:
    cmd = {
        'cmd': 'ensinar',
        'args': [l['oque'], l['contexto'], l['solucao'], l['categoria']]
    }
    with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w', encoding='utf-8') as f:
        json.dump(cmd, f, ensure_ascii=False)
    r = subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py',
        '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
        capture_output=True, text=True, timeout=30)
    status = 'OK' if 'APRENDIDO' in r.stdout or 'ensinar' in r.stdout.lower() else 'FALHA'
    prefix = l['oque'][:60]
    print(f'  [{status}] {prefix}...')

print('Licoes registradas:', len(licoes))
