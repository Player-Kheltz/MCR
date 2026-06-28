#!/usr/bin/env python3
"""Analisa a resposta do MCR no mega teste."""
import re

txt = open("E:/Projeto MCR/sandbox/teste_cego_mega/respostas_mcr/mega_1.txt", "r", encoding="utf-8-sig").read()

# Check sections
sections = re.findall(r'\[ \] [A-Z ]+:', txt)
print("Seções encontradas na resposta MCR:")
for s in sections:
    print(f"  - {s}")
print(f"\nTotal: {len(sections)} seções")
print(f"Total chars: {len(txt)}")

# Check code syntax
code_blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", txt, re.DOTALL)
errors = 0
for i, block in enumerate(code_blocks):
    try:
        compile(block.strip(), "<test>", "exec")
    except SyntaxError as e:
        errors += 1
        print(f"ERRO SINTATICO bloco {i}: {e.msg} linha {e.lineno}")
        print(f"  Primeiras linhas: {block.strip()[:200]}")

print(f"\nTotal blocos de codigo: {len(code_blocks)}, Erros: {errors}")
