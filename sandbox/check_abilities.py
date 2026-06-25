import os, re

base = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'
files = os.listdir(base)
files.sort()

print("=== VERIFICACAO DE ARQUIVOS DE HABILIDADE ===\n")

for f in files:
    if not f.endswith('.lua'):
        continue
    path = os.path.join(base, f)
    with open(path, 'r', encoding='utf-8', errors='replace') as fp:
        content = fp.read()
    
    lines = content.count('\n') + 1
    
    # Count braces
    opens = content.count('{')
    closes = content.count('}')
    balanced = opens == closes
    
    # Check for obvious issues
    issues = []
    if not balanced:
        issues.append(f"chaves desbalanceadas: {opens} abertas, {closes} fechadas")
    
    # Check for nil comparisons in conditions
    nil_comparisons = re.findall(r'if\s+\w+\s*==\s*nil|if\s+\w+\s*!=\s*nil', content)
    if nil_comparisons:
        issues.append(f"comparacao com nil: {len(nil_comparisons)} ocorrencias")
    
    # Check each ability has valid structure
    hab_count = len(re.findall(r'HABILIDADES\[\d+\]', content))
    
    icon = 'OK' if balanced else 'ISSUE'
    status = f"[{icon}]" if not issues else f"[{icon}] " + "; ".join(issues)
    print(f"  {status} {f}: {lines} linhas, {hab_count} habilidades")

print("\n=== VERIFICACAO CONCLUIDA ===")
