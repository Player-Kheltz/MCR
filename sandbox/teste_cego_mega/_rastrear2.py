#!/usr/bin/env python3
"""Rastreia exatamente onde e como as 5 'alucinacoes' aparecem na resposta MCR.
Verifica se sao usadas como CLASSES (CamelCase, dentro de codigo) ou como palavras comuns (texto)."""
import re

txt = open("E:/Projeto MCR/sandbox/teste_cego_mega/respostas_mcr/mega_1.txt", "r", encoding="utf-8-sig").read()

TERMOS = ["monitoramento", "seguranca", "sistema", "usuario", "interface"]

print("=" * 70)
print("  RASTREIO DAS 5 'ALUCINACOES'")
print("=" * 70)

for termo in TERMOS:
    # Procura variacoes: maiusculo/minusculo, com acento sem acento
    padroes = [termo, termo.capitalize(), termo.upper()]
    if "a" in termo:
        padroes.append(termo.replace("a", "a"))
    
    print(f"\n--- {termo} ---")
    for i, linha in enumerate(txt.split("\n")):
        linha_lower = linha.lower()
        if termo in linha_lower or termo.capitalize().lower() in linha_lower:
            # Verifica se esta dentro de bloco de codigo
            antes = txt[:txt.find(linha)]
            em_codigo = antes.count("```") % 2 == 1
            
            # Verifica se parece nome de classe (CamelCase)
            classe_match = re.search(r'\b[Ss]istema\b', linha)
            
            print(f"  Linha {i+1}: {'[CODIGO]' if em_codigo else '[TEXTO]'}")
            print(f"  Conteudo: {linha.strip()[:120]}")
            break
    else:
        print(f"  (nao encontrado no texto)")

print("\n" + "=" * 70)
print("  ANALISE: estas sao CLASSES inventadas ou palavras comuns?")
print("=" * 70)

# Conta: se a palavra aparece como classe (depois de 'class ') ou como CamelCase
for termo in TERMOS:
    classes = re.findall(r'class\s+' + termo.capitalize(), txt, re.IGNORECASE)
    camel = re.findall(r'\b' + termo.capitalize() + r'\b', txt)
    print(f"  {termo}: class={len(classes)}, ocorrencias={len(camel)}")
    if len(classes) == 0 and len(camel) <= 1:
        print(f"    -> NAO e uma classe inventada. E palavra comum.")
    else:
        print(f"    -> PODE ser classe inventada.")
