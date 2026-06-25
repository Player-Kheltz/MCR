"""Fix V13 - move versoes into meta"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v13.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix _carregar: move 'versoes' into meta
old = """        return {
            'versoes': 0,
            'modulos': {},
            'cache': {},
            'meta': {"""
new = """        return {
            'modulos': {},
            'cache': {},
            'meta': {
                'versoes': 0,"""
c = c.replace(old, new)

# Fix salvar to use meta
# Already fixed: self.data['meta']['versoes'] += 1

with open(r'E:\Projeto MCR\sandbox\mcr_crew_v13.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'v13.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
