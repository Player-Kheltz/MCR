"""Fix V13 status"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v13.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix 1: versoes increment should be in meta
c = c.replace("self.data['versoes'] += 1", "self.data['meta']['versoes'] += 1")

# Fix 2: status should also use meta for 'versoes'
# Currently: m["versoes"] where m = data['meta'] - this is correct already

with open(r'E:\Projeto MCR\sandbox\mcr_crew_v13.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'v13.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
