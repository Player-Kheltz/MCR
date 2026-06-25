"""Fix heartbeat merged method definition"""
with open(r'E:\Projeto MCR\sandbox\mcr_heartbeat.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'log(f\'Batida' in line and 'def _escanear_padroes' in line:
        # Split into two lines
        log_part = line.split('def _escanear_padroes')[0].rstrip()
        def_part = '    def _escanear_padroes(self):\n'
        lines[i] = log_part + '\n' + def_part
        print(f'Fixed line {i+1}')
        break

with open(r'E:\Projeto MCR\sandbox\mcr_heartbeat.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

try:
    compile(''.join(lines), 'heartbeat.py', 'exec')
    print('OK! Compilou!')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
