#!/usr/bin/env python3
"""Remove wrapper classes that were replaced by aliases."""
import sys, os

mcr_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia', 'modulos', 'MCR.py'))

with open(mcr_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the orphaned MCREntropia body after the alias replacement
idx = content.find('MCREntropia = MCR  # alias')
if idx > 0:
    # Find next class definition
    end = content.find('\nclass ', idx)
    if end > 0:
        # Keep the alias line, remove the orphaned body
        alias_line_end = content.find('\n', idx) + 1  # end of first line
        content = content[:alias_line_end] + content[end:]
        print(f'Removed MCREntropia body ({end - alias_line_end} chars)', flush=True)

# Remove 'MCRSwarm = MCRSpawner' if it exists (alias, no body to remove)
content = content.replace('MCRSwarm = MCRSpawner\n', '')
content = content.replace('MCRSwarm = MCRSpawner', '')

# Replace MCRPeso class with alias  
# (it's a simple class, keep it for now)

with open(mcr_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done', flush=True)
