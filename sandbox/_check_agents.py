#!/usr/bin/env python
with open(r'E:\Projeto MCR\AGENTS.md', 'r', encoding='utf-8') as f:
    content = f.read()
checks = [
    ('Regra de ouro com SUPERVISIONA', 'SUPERVISIONA' in content),
    ('Menciona auto-repara', 'auto-repara' in content),
    ('Menciona 3 falhas consecutivas', '3 falhas consecutivas' in content),
    ('Secao SUPERVISIONE', 'SUPERVISIONE' in content),
    ('Nova coluna supervisiona na tabela', False),  # placeholder
]
for label, ok in checks:
    print(f'  {"OK" if ok else "MISSING"}: {label}')
