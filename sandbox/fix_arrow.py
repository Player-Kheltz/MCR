"""Fix - remove unicode arrow"""
with open(r'E:\Projeto MCR\sandbox\auto_template_v2.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('\u2192', '->')
with open(r'E:\Projeto MCR\sandbox\auto_template_v2.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Fixed!')
