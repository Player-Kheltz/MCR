"""Fix V5 for real - escape braces in f-string JSON templates"""
with open(r'E:\Projeto MCR\sandbox\gerador_shc_v5.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The problem: inside f-strings, JSON templates like [{"nome":...}] 
# have unescaped braces. Fix: {{ and }} for literal braces.
import re

def fix_fstring_braces(match):
    """Escape braces inside an f-string block, preserving format variables."""
    block = match.group(0)
    prefix = match.group(1) or ''
    suffix = match.group(3) or ''
    inner = match.group(2) or ''
    
    result = []
    i = 0
    while i < len(inner):
        if inner[i] == '{':
            # Check if it's a format variable (has valid python ident inside)
            j = i + 1
            while j < len(inner) and inner[j] not in '}':
                j += 1
            if j < len(inner):
                var_content = inner[i+1:j]
                # If it looks like a variable: alphanumeric, dots, brackets, digits
                if var_content and (var_content[0].isalpha() or var_content[0] == '_') or (var_content.isdigit()):
                    # It's a format variable - keep as is
                    result.append(inner[i:j+1])
                    i = j + 1
                    continue
            # Not a format variable - escape it
            result.append('{{')
            i += 1
        elif inner[i] == '}':
            result.append('}}')
            i += 1
        else:
            result.append(inner[i])
            i += 1
    
    return prefix + ''.join(result) + suffix

# Apply fix to all f""" blocks
content = re.sub(r'(f"""?)(.*?)(""")', fix_fstring_braces, content, flags=re.DOTALL)

# But DON'T double-escape already escaped braces {{ 
# Fix: revert any {{{{ back to {{
content = content.replace('{{{{', '{{')
content = content.replace('}}}}', '}}')

with open(r'E:\Projeto MCR\sandbox\gerador_shc_v5.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Test compile
try:
    compile(content, 'gerador_shc_v5.py', 'exec')
    print('V5 COMPILES OK!')
except SyntaxError as e:
    print(f'Syntax error: {e}')
    # Print the problematic line
    lines = content.split('\n')
    if e.lineno:
        for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
            marker = '>>>' if i == e.lineno-1 else '   '
            print(f'{marker} {i+1}: {lines[i]}')
