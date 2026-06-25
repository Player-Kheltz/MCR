"""Fix ultimate path quoting"""
with open(r'E:\Projeto MCR\scripts\mcr_devia\mcr_ultimate.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('python {{DEVIA}}', 'python "{{DEVIA}}"')
with open(r'E:\Projeto MCR\scripts\mcr_devia\mcr_ultimate.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Fixed!')
