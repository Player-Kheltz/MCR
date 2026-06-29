"""Fix ALL syntax errors in context_crew.py iteratively."""
import subprocess
path = r'E:\Projeto MCR\scripts\mcr_devia\context_crew.py'

for tentativa in range(20):
    r = subprocess.run(['python', '-c', f'compile(open(r"{path}","r",encoding="utf-8").read(),"ctx","exec")'],
                       capture_output=True, text=True, timeout=10)
    if not r.stderr:
        print(f'Syntax OK after {tentativa} iterations')
        break
    
    lines = open(path, 'r', encoding='utf-8').readlines()
    erro = r.stderr.split('\n')
    msg = ''
    lineno = 0
    for e in erro:
        if 'line ' in e:
            try:
                parts = e.strip().split()
                for i, p in enumerate(parts):
                    if p == 'line':
                        lineno = int(parts[i+1].rstrip(','))
                    if 'SyntaxError:' in p:
                        msg = ' '.join(parts[i:]).replace('SyntaxError: ', '')
            except: pass
    
    if not lineno or lineno < 1 or lineno > len(lines):
        print(f'Cant parse error: {r.stderr[:200]}')
        break
    
    line = lines[lineno - 1]
    stripped = line.strip()
    print(f'Iter {tentativa}: L{lineno}: {stripped[:60]}')
    
    if 'expected an indented block after' in r.stderr and 'except' in r.stderr:
        # Add pass after except
        indent = len(line) - len(line.lstrip())
        # Check if next line already has content
        if lineno < len(lines):
            next_stripped = lines[lineno].strip()
            if not next_stripped or next_stripped.startswith(('def ', 'class ', '#', '"""')):
                lines.insert(lineno, ' ' * (indent + 4) + 'pass\n')
                with open(path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                continue
    
    if 'expected' in msg and 'block' in msg:
        # try sem except - find try above
        for j in range(lineno - 2, -1, -1):
            if lines[j].strip() == 'try:':
                indent = len(lines[j]) - len(lines[j].lstrip())
                lines.insert(lineno, ' ' * indent + 'except Exception:\n')
                lines.insert(lineno + 1, ' ' * (indent + 4) + 'pass\n')
                with open(path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                break
        continue
    
    # Generic indent fix
    for j in range(lineno - 2, -1, -1):
        if lines[j].strip() == 'try:':
            indent = len(lines[j]) - len(lines[j].lstrip())
            if len(line) - len(line.lstrip()) < indent:
                lines[lineno - 1] = ' ' * indent + stripped + '\n'
                with open(path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                break
        if lines[j].strip().startswith(('def ', 'class ')):
            break
else:
    print(f'Failed to fix after {tentativa+1} attempts')
    if r.stderr:
        print(f'Last error: {r.stderr[:200]}')
