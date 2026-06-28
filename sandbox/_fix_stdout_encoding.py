#!/usr/bin/env python
"""Add sys.stdout.reconfigure at start of main() to prevent all Unicode crashes."""
import sys

path = r'E:\Projeto MCR\scripts\mcr_devia\mcr_devia.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 949 (0-indexed 948) currently has the reconfigure (from my bad edit)
# The original was '    kg = KnowledgeGraph()'
# I need line 949 to be reconfigure AND line 950 to be kg = KnowledgeGraph()

# Find the current line 949
idx = 948  # 0-indexed

# Set line 949 to reconfigure
lines[idx] = "    sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"

# Check if line 950 already has kg = KnowledgeGraph()
if idx + 1 < len(lines) and 'KnowledgeGraph' not in lines[idx + 1]:
    # Insert kg = KnowledgeGraph() at line 950
    lines.insert(idx + 1, '    kg = KnowledgeGraph()\n')

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

try:
    compile(''.join(lines), path, 'exec')
    print(f'OK - stdout encoding fix added')
except SyntaxError as e:
    print(f'ERRO: {e}')
    sys.exit(1)
