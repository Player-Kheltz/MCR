#!/usr/bin/env python3
"""Restaura __main__ no final do MCR.py."""
import sys, os, re

mcr_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos', 'MCR.py'))

with open(mcr_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove _MCR_DATA block
content = re.sub(r'\n_MCR_DATA\s*=\s*""".*?"""\s*\n', '\n', content, flags=re.DOTALL)

# Strip trailing blank lines and JSON remnants
while content.endswith('\n'):
    content = content[:-1]

# Add _MCR_DATA placeholder + __main__
tail = '''

_MCR_DATA = """..."""

if __name__ == '__main__':
    import sys, os
    _base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if _base not in sys.path:
        sys.path.insert(0, _base)
    _autotestar()
'''

with open(mcr_path, 'w', encoding='utf-8') as f:
    f.write(content + tail)

# Verify
with open(mcr_path, 'r', encoding='utf-8') as f:
    new = f.read()
print(f'Linhas: {len(new.splitlines())}')
print(f'Tem __main__: {"__main__" in new}')
print(f'Tem _autotestar: {"_autotestar" in new}')

# Quick syntax check
import subprocess
r = subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, r"scripts/mcr_devia"); import modulos.MCR'], 
                   capture_output=True, text=True, timeout=10, cwd=os.path.dirname(mcr_path)+'/../../..')
print(f'Import: {r.returncode} {"OK" if r.returncode==0 else r.stderr[:200]}')
