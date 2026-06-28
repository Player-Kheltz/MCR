"""Fix syntax error in resolver_ultra.py"""
with open(r'E:\Projeto MCR\sandbox\resolver_ultra.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix corrupted line 195
c = c.replace(
    "print(f'\\n{\"=\"*6print(f'\\n{\"=\"*60}')",
    "print(f'\\n{\"=\"*60}')"
)

# Fix the broken print line
c = c.replace(
    "print(f'{'='*60}')",
    "print(f'{\"=\"*60}')"
)

with open(r'E:\Projeto MCR\sandbox\resolver_ultra.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'fix.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
    # Show the problematic area
    lines = c.split('\n')
    if e.lineno:
        for i in range(max(0,e.lineno-3), min(len(lines),e.lineno+2)):
            print(f'  {i+1}: {lines[i]}')
