import os, re, sys

sys.stdout.reconfigure(encoding='utf-8')

base = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'
files = sorted([f for f in os.listdir(base) if f.endswith('.lua')])

print("=== VERIFICACAO DETALHADA ===\n")

total_hab = 0
total_lines = 0
issues_found = False

for f in files:
    path = os.path.join(base, f)
    with open(path, 'r', encoding='utf-8', errors='replace') as fp:
        content = fp.read()
    
    lines = content.count('\n') + 1
    total_lines += lines
    hab_count = len(re.findall(r'HABILIDADES\[\d+\]', content))
    total_hab += hab_count
    
    file_issues = []
    
    # Check for stray 'end' keyword outside strings
    clean = re.sub(r'"[^"]*"', '', content)
    clean = re.sub(r"'[^']*'", '', clean)
    real_ends = re.findall(r'\bend\b', clean)
    if real_ends:
        file_issues.append(f"stray 'end' keyword: {len(real_ends)} ocorrencias")
    
    # Check for nil comparison patterns
    nil_patterns = re.findall(r'(if\s+\w+\s*==\s*nil|if\s+\w+\s*!=\s*nil|==\s*nil\b|~=\s*nil\b)', content)
    if nil_patterns:
        file_issues.append(f"nil comparisons: {len(nil_patterns)}")
    
    if file_issues:
        issues_found = True
        print(f"  [!] {f}")
        for issue in file_issues:
            print(f"     {issue}")
    else:
        print(f"  [OK] {f}: {lines} linhas, {hab_count} habs")

print()
print("=== RESUMO ===")
print(f"Total: {len(files)} arquivos, {total_lines} linhas, {total_hab} habilidades")
if not issues_found:
    print("Nenhum problema encontrado!")
else:
    print("Problemas encontrados - veja acima")
