"""Feedback arquitetural baseado nos gaps do ciclo 1."""
import json, subprocess, sys

gaps_texto = (
    '- codigo: auto-nota 8, cloud-nota 5, gap 3. Resposta correta mas forcou contexto MCR em pergunta geral.\n'
    '- logica: auto-nota 8, cloud-nota 5, gap 3. Mesmo problema: contextualizou no MCR quando nao devia.\n'
    '- literatura: auto-nota 7, cloud-nota 3, gap 4. Resposta inventou relacoes com arquivos MCR que nao existem.\n'
    '- explicacao: auto-nota 0, cloud-nota 0, gap 0. Resposta foi data/hora (erro no pipeline).\n'
    '- analise: auto-nota 0, cloud-nota 0, gap 0. Resposta ignorou pergunta e falou do MCR.\n'
)

prompt = (
    'Voce e o MCR-DevIA. Considere os gaps do ultimo ciclo de teste:\n\n'
    + gaps_texto +
    '\n'
    'O principal problema identificado: O pipeline forcou contexto MCR em perguntas GERAIS '
    'que nao tinham nada a ver com o MCR. O CR e o Enricher assumem que TUDO e sobre o MCR.\n\n'
    'Que mudancas voce faria na sua propria arquitetura (pipeline, CR, Enricher, ToT, etc) '
    'para resolver este problema?\n'
    'Responda em JSON:\n'
    '{\n'
    '  "diagnostico": "causa raiz do problema",\n'
    '  "mudancas": [\n'
    '    {"oque": "descricao", "onde": "modulo", "prioridade": "alta ou media ou baixa"}\n'
    '  ]\n'
    '}'
)

cmd = {'cmd': 'perguntar', 'args': [prompt]}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)

r = subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py',
    '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=300)

try:
    resp = open('E:/Projeto MCR/sandbox/.mcr_resposta.txt', 'r').read()
    print(resp[:2000])
except:
    print(r.stdout[-2000:])
