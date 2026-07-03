"""Add methods to AprendizDePadroes: contextual extraction + blocks."""
import sys, os, re, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
from modulos.pattern_engine import PatternEngine
from modulos.kg import KnowledgeGraph

# Read current file
path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos', 'aprendiz_de_padroes.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find end of last method
lines = content.split('\n')
print(f'Total lines: {len(lines)}')
for i in range(max(0, len(lines)-10), len(lines)):
    print(f'{i+1}: {lines[i]}')
