"""Testar PatternEngine com codigo real."""
import sys
sys.path.insert(0, r'E:\Projeto MCR\Scripts\mcr_devia')
from modulos.pattern_engine import PatternEngine

pe = PatternEngine()

# Codigo BOM (kg.py refatorado)
with open(r'E:\Projeto MCR\scripts\mcr_devia\modulos\kg.py') as f:
    codigo_bom = f.read()
r1 = pe.analisar(codigo_bom, 'codigo')
print('KG.PY (refatorado):')
print('  Eixo:', r1['eixo_nirvana_caos'], '(0=Caos, 1=Nirvana)')
print('  Tokens:', r1['tokens'])
print('  Entropia:', r1['padroes']['entropia'])

# Codigo RUIM
codigo_ruim = 'def f():\n    try:\n        pass\n    except:\n        pass\n    try:\n        x = 1\n    except:\n        pass\n'
r2 = pe.analisar(codigo_ruim, 'codigo')
print()
print('CODIGO RUIM:')
print('  Eixo:', r2['eixo_nirvana_caos'])
print('  Tokens:', r2['tokens'])

# Fingerprint
fp_ruim = pe.fingerprint(pe.tokenizar(codigo_ruim, 'codigo'))
fp_bom = pe.fingerprint(pe.tokenizar(codigo_bom, 'codigo'))
print('  Similaridade com kg.py:', pe.similaridade(fp_ruim, fp_bom))

# Comando --pattern via kernel
print()
print('Testando comando --pattern...')
print('  -> python kernel.py --pattern "Precisamos criar um sistema universal"')
