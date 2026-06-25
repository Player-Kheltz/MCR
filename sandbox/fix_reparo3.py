"""Clean fix for auto_reparo.py"""
with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and remove the problematic f-string lines (lines 176-185)
new_lines = []
skip_block = False
for i, line in enumerate(lines):
    # Skip the entire f-string block
    if 'prompt = f"""O template de' in line:
        skip_block = True
    if skip_block:
        if '"""' in line and i > 175:  # End of f-string
            skip_block = False
            new_lines.append('            prompt = "O template de " + str(tipo) + " esta desatualizado. Faltam: " + ", ".join(faltando[:8]) + "\\n"\n')
            continue
        continue
    new_lines.append(line)

with open(r'E:\Projeto MCR\sandbox\mcr_auto_reparo.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

try:
    compile(''.join(new_lines), 'auto_reparo.py', 'exec')
    print('OK! Fixed!')
except SyntaxError as e:
    print(f'Error at line {e.lineno}: {e.msg}')
