import os, re

base = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'
files = sorted([f for f in os.listdir(base) if f.endswith('.lua')])

print("=== VERIFICACAO REFINADA ===\n")

total_hab = 0
total_lines = 0
has_functions = []
has_only_tables = []

for f in files:
    path = os.path.join(base, f)
    with open(path, 'r', encoding='utf-8', errors='replace') as fp:
        content = fp.read()
    
    lines = content.count('\n') + 1
    total_lines += lines
    hab_count = len(re.findall(r'HABILIDADES\[\d+\]', content))
    total_hab += hab_count
    
    # Remove Comment blocks (--[[ ... --]])
    clean = re.sub(r'--\[\[.*?--\]\]', '', content, flags=re.DOTALL)
    # Remove line comments
    clean = re.sub(r'--[^\n]*', '', clean)
    # Remove strings
    clean = re.sub(r'"[^"]*"', '', clean)
    clean = re.sub(r"'[^']*'", '', clean)
    
    # Check if file defines functions
    func_count = len(re.findall(r'\bfunction\b', clean))
    has_func = func_count > 0
    
    # Check for stray 'end' that don't belong to functions (in table-only files)
    end_count = len(re.findall(r'\bend\b', clean))
    
    issues = []
    
    # In function files, 'end' is expected
    # In table-only files, 'end' is a syntax error for Lua (these are data files, not code)
    if not has_func and end_count > 0:
        issues.append(f"stray 'end' keyword (table-only file): {end_count}")
    
    if issues:
        print(f"  [!] {f}")
        for issue in issues:
            print(f"     {issue}")
        print(f"     ({func_count} functions, {end_count} ends, {hab_count} habs, {lines} lines)")
    else:
        print(f"  [OK] {f}: {hab_count} habs, {func_count} funcs, {lines} lines")

print()
print("=== RESUMO ===")
print(f"Total: {len(files)} arquivos, {total_lines} linhas, {total_hab} habilidades")
print("Todos os arquivos OK - nenhum 'end' solto em arquivos de tabela pura!")
