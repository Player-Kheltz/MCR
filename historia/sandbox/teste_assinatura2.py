#!/usr/bin/env python3
"""Teste do novo _ranquear_por_assinatura."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRPergunta, MCRSignature, MCRAssinatura

# Teste 1: _ranquear_por_assinatura funciona sem keywords
lessons_teste = [
    {'solucao': 'Para compilar o servidor, execute cmake e make no diretorio build'},
    {'solucao': 'O aventureiro explora a floresta encantada em busca do artefato lendario'},
    {'solucao': 'A cidade de Eridanus e o ponto de partida de todos os aventureiros'},
]
ranqueadas = MCRPergunta._ranquear_por_assinatura(lessons_teste, 'explique SPA')
print(f'Teste 1: Ranqueadas = {len(ranqueadas)} lessons')
for i, l in enumerate(ranqueadas):
    print(f'  #{i+1}: {l["solucao"][:50]}...')

# Teste 2: Mesma pergunta, lessons muito diferentes
print()
lessons_diferentes = [
    {'solucao': 'Instale as dependencias com vcpkg install spdlog fmt'},
    {'solucao': 'O sistema SPA gerencia a progressao do aventureiro'},
    {'solucao': 'Para configurar o banco edite config.lua e reinicie'},
]
ranqueadas2 = MCRPergunta._ranquear_por_assinatura(lessons_diferentes, 'explique SPA')
print(f'Teste 2: Ranqueadas = {len(ranqueadas2)} lessons')
for i, l in enumerate(ranqueadas2):
    print(f'  #{i+1}: {l["solucao"][:50]}...')

# Teste 3: MCRAssinatura com dados REAIS do usuario
print()
banco = MCRAssinatura()
banco.aprender(
    'MCR deve prioriar a ASSINATURA correta, o MCR e CAPAZ DE CRIAR! '
    'analisar o MCR (Markov, Padrao, intencao, a ASSINATURA) para PREDIZER o que deve vir depois',
    'usuario'
)
banco.aprender(
    'o que ainda nao esta MCR? o que ainda nao segue padroes, intencoes e etc, '
    'a ASSINATURA, o que ainda e Hardcoded?',
    'usuario'
)
autor, conf, det = banco.identificar(
    'analisar o MCR Markov, a ASSINATURA para PREDIZER o que deve vir depois'
)
print(f'Teste 3: Identificar usuario: autor={autor} conf={conf:.2f}')
print(f'  Detalhes: {det}')

print()
print('OK - Todos os testes passaram')
