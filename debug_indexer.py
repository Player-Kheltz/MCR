#!/usr/bin/env python3
import sys, os
sys.path.insert(0, r'E:\Projeto MCR\historia\Scripts\mcr_devia\knowledge')
from canary_indexer import CanaryIndexer, NPC_DIRS
for d in NPC_DIRS:
    exists = os.path.isdir(d)
    count = len(os.listdir(d)) if exists else 0
    print(f'{d}: existe={exists}, count={count}')
idx = CanaryIndexer()
stats = idx.indexar(forcar=True)
print(f'Total NPCs: {stats}')
if idx.npcs:
    print(f'Primeiro: {idx.npcs[0]}')
