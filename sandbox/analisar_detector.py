"""MCR-DevIA: Descubra e corrija o detector de variavel global"""
import subprocess, sys

# Pergunta 1: Analisar o problema
prompt = """O detector de variavel global esta quebrado. Ele usa regex que pega TUDO que parece "nome = valor" identado.

Mas em Lua, isso e normal dentro de tabelas:
HABILIDADES[1] = {
    nome = "x",  -- ISSO e chave de tabela, NAO variavel global
    tipo = "y",
}

O detector precisa IGNORAR linhas que estao dentro de { } (tabelas).

Analise o problema e sugira uma correcao para o regex."""

cmd1 = ['python', 'E:/Projeto MCR/scripts/mcr_devia/mcr_devia.py', 'perguntar', prompt]
r1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=60)
print('=== ANALISE DO MCR-DevIA ===')
print(r1.stdout[:600])
