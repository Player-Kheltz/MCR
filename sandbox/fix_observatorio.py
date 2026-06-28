"""Tornar o observatorio TECNICO de novo"""
with open(r'E:\Projeto MCR\sandbox\mcr_observatory_v2.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Substitui o prompt fantasioso por um tecnico
c = c.replace(
    'Responda de forma TECNICA e DIRETA sobre o estado do MCR-DevIA.',
    'Responda de forma OBJETIVA: numeros de licoes, detectores ativos, taxa de deteccao, ultimos reparos. Nada de historias.'
)

with open(r'E:\Projeto MCR\sandbox\mcr_observatory_v2.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Observatorio agora e tecnico.')
