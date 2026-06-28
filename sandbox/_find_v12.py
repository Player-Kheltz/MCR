#!/usr/bin/env python
"""Find all V12 match blocks in mcr_devia.py"""
import re

with open(r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'matches >= 3' in line:
        # Print line numbers
        print(f'BLOCK at L{i+1}')
        for j in range(i, min(i+8, len(lines))):
            txt = lines[j].rstrip().encode('ascii', errors='replace').decode('ascii')
            print(f'  L{j+1}: {txt[:120]}')
        print()
