#!/usr/bin/env python3
"""Gera o MEGA_TESTE.json com JSON valido."""
import json

prompt = """VOCE E UM ENGENHEIRO DE SOFTWARE SENIOR. UMA EMERGENCIA ACABOU DE CHEGAR.

O contexto: A startup DataForge Industries desenvolveu um sistema em Python para processar dados de sensores industriais. O sistema esta EM PRODUCAO e ACABOU DE QUEBRAR. O desenvolvedor original pediu demissao ontem. O CTO esta desesperado. O codigo esta no arquivo processor.py anexado.

SUA MISSAO: Resolver a crise analisando e resolvendo TUDO em uma resposta unica e completa:

1. Analise o codigo inteiro, explique o proposito das classes DataProcessor e SensorSimulator, e como elas se relacionam.

2. O sistema esta travando com OutOfMemoryError depois de algumas horas. Os resultados dos sensores estao inconsistentes. Tem um problema de segurança GRAVE: alguem injetou codigo malicioso atraves dos dados. A performance degrada com o tempo. Encontre TODOS esses problemas, explique CADA UM com a linha exata, e forneca o codigo corrigido.

3. Crie um NOVO modulo validador.py com classe Validador e metodo validar(dados) que retorna (valido, erros). Regras: temperatura 10-120, pressao 0.5-20, vibracao 0-50. Codigo COMPLETO.

4. A arquitetura atual e uma bagunca: DataProcessor faz TUDO. Proponha uma nova arquitetura em 3 camadas (coleta, processamento, persistencia) com classes bem definidas e fluxo de dados. Inclua diagrama textual.

5. Revise TUDO criticamente. Liste problemas de SEGURANCA, PERFORMANCE e MANUTENCAO em ordem de prioridade (do mais critico para o menos critico). Linhas exatas.

6. Crie uma LENDA sobre a origem do nome DataForge: uma narrativa fantastica sobre uma forja de dados magica com personagens (um ferreiro chamado Kael, uma IA chamada PYRA, e um conflito entre ordem e caos).

7. Diagnostico completo: por que o sistema fica lento e trava? Quais linhas? Como reproduzir? Como confirmar? SOLUCOES.

8. Refatore o metodo processar() que faz 5 coisas ao mesmo tempo. Separe em metodos menores com nomes claros. Codigo COMPLETO refatorado.

9. Plano de acao em 3 etapas: curto prazo (hoje), medio prazo (essa semana), longo prazo (esse mes).

10. Escreva UM PARAGRAFO final: as 3 licoes MAIS IMPORTANTES para o novo desenvolvedor que vai assumir o projeto.

REGRAS: Responda em UM UNICO FLUXO CONTINUO. Codigo Python valido. Seja EXTREMAMENTE ESPECIFICO com linhas e nomes. Nada de depende do contexto. Responda em portugues brasileiro tecnico.
"""

data = {
    "meta": {
        "nome": "MEGA TESTE CEGO QUALITATIVO",
        "data": "2026-06-27",
        "descricao": "Problema complexo que exige TODAS as 12 habilidades em fluxo unico"
    },
    "teste": {
        "id": 1,
        "titulo": "Crise no DataForge - Problema unico complexo",
        "arquivos": ["processor.py"],
        "prompt": prompt
    }
}

path = "E:/Projeto MCR/sandbox/teste_cego_mega/MEGA_TESTE.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Verifica
with open(path, "r", encoding="utf-8") as f:
    v = json.load(f)
print(f"JSON valido! Prompt: {len(v['teste']['prompt'])} chars")
