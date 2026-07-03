#!/usr/bin/env python3
"""Teste do MCRKGAuto._classificar_qualidade."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRKGAuto

testes = [
    ('JSON puro', '{"n": "t", "v": 1}', 0.1),
    ('_flush', '_flush_20260101_000000', 0.0),
    ('JSON com texto', '{"solucao": "SPA e o sistema de progressao do aventureiro"}', 0.5),
    ('Texto lore', 'O aventureiro explora a floresta encantada em busca do artefato lendario', 0.85),
    ('Texto curto', 'abc', 0.0),
    ('Hash', '{"sha256-970aa74c0a90ef7482477cf803618e776e173c007bf957f635f1015bfcfef0e6"}', 0.1),
    ('Texto tecnico', 'O MCR implementa transicoes markovianas entre estados consecutivos', 0.85),
    ('Historia', 'A cidade de Eridanus guarda segredos antigos', 0.85),
]

print('=== MCRKGAuto._classificar_qualidade() ===')
for nome, texto, esperado in testes:
    q = MCRKGAuto._classificar_qualidade(texto)
    status = 'OK' if abs(q - esperado) <= 0.2 else f'FALHA (esperado ~{esperado})'
    print(f'  {nome:15s}: {q:.1f} {status}')
