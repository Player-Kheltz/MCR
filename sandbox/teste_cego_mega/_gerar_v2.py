#!/usr/bin/env python3
"""Gera nova versao do MEGA_TESTE.json apontando para datalake.py"""
import json

prompt = """VOCE E UM ENGENHEIRO DE SOFTWARE SENIOR. UMA EMERGENCIA ACABOU DE CHEGAR.

A startup DataLake Industries processa streams de dados industriais em tempo real. O sistema DELES, escrito em Python (arquivo datalake.py), esta em producao e ACABOU DE QUEBRAR. O desenvolvedor original pediu demissao. O CTO esta desesperado.

SUA MISSAO: Resolver a crise. O sistema tem MULTIPLOS problemas que voce precisa encontrar, explicar e corrigir. Sua resposta deve ser UM UNICO DOCUMENTO TECNICO cobrindo TUDO abaixo.

PROBLEMAS CONHECIDOS (suspeitos):
- O sistema fica cada vez mais lento ate travar (memory leak)
- As vezes os contadores parecem pular numeros (race condition)
- Alguem conseguiu invadir o sistema pelos dados do sensor (security hole)
- O cache cresce sem parar
- Resultados inconsistentes em certas condicoes
- Arquivos de resultado estao sendo salvos em lugares estranhos

[ ] ANALISE DE CODIGO: Explique o proposito das classes DataLake e StreamSimulator, seus metodos principais e como se relacionam. Aponte a estrutura geral.

[ ] CORRECAO DE BUGS: Liste CADA bug com: LINHA X, nome do bug, explicacao tecnica, impacto, e codigo corrigido. Minimamente 7 bugs.

[ ] GERACAO DE CODIGO: Crie um modulo validador_stream.py que valide streams antes do processamento. Classe ValidadorStream com metodo validar(stream) que retorna (valido, erros[], alertas[]). Regras: temperatura 0-100, pressao 0.5-30, vibracao 0-60. Streams invalidos vao para uma fila de rejeicao. Codigo COMPLETO.

[ ] ARQUITETURA: Proponha nova arquitetura em 3 camadas (ingestao, processamento, armazenamento) que substitua a classe DataLake atual. Inclua diagrama textual com CLASSES, METODOS e FLUXO.

[ ] REVISAO: Liste TOP 5 problemas de SEGURANCA, PERFORMANCE e MANUTENCAO priorizados por gravidade. Linhas exatas.

[ ] CRIACAO: Crie uma LENDA curta sobre a origem do nome "DataLake" — uma historia de um LAGO DE DADOS magico guardado por um guardiao digital.

[ ] DIAGNOSTICO: Diagnostico completo de CAUSA RAIZ: por que o sistema fica lento e trava? Quais linhas contribuem? Como reproduzir? Como confirmar? Solucoes para cada causa.

[ ] REFATORACAO: Refatore o metodo processar_stream que faz 5 coisas ao mesmo tempo em metodos separados (um para validacao, um para transformacao, um para filtro, um para contador, um para registro). Codigo COMPLETO.

[ ] PLANEJAMENTO: Plano de acao em 3 etapas (hoje, esta semana, este mes) com tarefas especificas, responsaveis e metricas de sucesso.

[ ] SINTESE: Escreva UM PARAGRAFO final com as 3 licoes mais importantes para o novo desenvolvedor que vai assumir o DataLake.

REGRAS ABSOLUTAS:
- CADA secao DEVE comecar com [ ] NOME DA SECAO: (exato)
- Codigo Python valido dentro de ```python ... ```
- Linhas exatas, nomes de variaveis, explicacoes tecnicas
- Nada generico. Seja EXTREMAMENTE ESPECIFICO.
- Responda em portugues brasileiro tecnico"""

data = {
    "meta": {
        "nome": "MEGA TESTE CEGO v2 - DataLake",
        "data": "2026-06-27",
        "descricao": "Problema complexo com datalake.py - 10 bugs intencionais"
    },
    "teste": {
        "id": 1,
        "titulo": "Crise no DataLake v2",
        "arquivos": ["datalake.py"],
        "prompt": prompt
    }
}

path = "E:/Projeto MCR/sandbox/teste_cego_mega/MEGA_TESTE.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Verify
with open(path, "r", encoding="utf-8") as f:
    v = json.load(f)
print(f"JSON valido! Prompt: {len(v['teste']['prompt'])} chars, Arquivo: {v['teste']['arquivos'][0]}")
