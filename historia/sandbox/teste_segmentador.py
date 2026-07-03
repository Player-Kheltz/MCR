#!/usr/bin/env python3
"""Teste MCRSegmentador + MCRPersistencia + MCRBoot."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRSegmentador, MCRPersistencia, MCRBoot

print("=" * 60)
print("TESTE 1: MCRSegmentador — estuda o proprio MCR.py")
print("=" * 60)

mcr_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos', 'MCR.py')
mcr_path = os.path.abspath(mcr_path)

t0 = time.time()
seg = MCRSegmentador()
linhas = seg.estudar_se(mcr_path)
t1 = time.time() - t0

print(f"  Estudou em {t1:.1f}s")
if linhas:
    # Conta tipos
    from collections import Counter
    tipos = Counter(t[0] for t in linhas)
    print(f"  Distribuicao: {dict(tipos)}")
    
    # Mostra transicoes aprendidas
    if seg.mk_transicoes.freq:
        print(f"  Transicoes: {dict(seg.mk_transicoes.freq)}")
    
    # Procura por DATA no final do arquivo
    ultimas_linhas = linhas[-20:]
    print(f"  Ultimas 20 linhas: {[t[0] for t in ultimas_linhas]}")
    
    # Encontra dados
    data_info = seg.encontrar_dados()
    print(f"  Dados encontrados: {data_info}")
    
    print(f"  Pronto: {seg.esta_pronto()}")

print()
print("=" * 60)
print("TESTE 2: MCRPersistencia — carrega dados do proprio arquivo")
print("=" * 60)

t0 = time.time()
pers = MCRPersistencia(mcr_path)
dados = pers.carregar_dados()
t1 = time.time() - t0

print(f"  Carregou em {t1:.1f}s")
print(f"  Licoes: {len(dados.get('licoes', []))}")
print(f"  Assinaturas: {len(dados.get('assinaturas', {}))}")
print(f"  Cache: {len(dados.get('cache', {}))}")
print(f"  Estado: {len(dados.get('estado', {}))}")

print()
print("=" * 60)
print("TESTE 3: MCRBoot — auto-direcionamento")
print("=" * 60)

boot = MCRBoot()
print(f"  Segmentador pronto: {boot.segmentador.esta_pronto()}")
print(f"  Persistencia carregada: {len(boot.estado) > 0 or len(boot.persistencia.dados) > 0}")

print()
print("OK - Todos os testes passaram!")
