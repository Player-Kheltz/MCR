"""Varredura real do Projeto MCR com code_analyzer."""
import sys, os, time

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

sys.path.insert(0, _BASE)
from code_analyzer import analisar_arquivo, PADROES_BUG

PROJETO = r"E:\Projeto MCR"
IGNORAR = {'vcpkg', 'node_modules', '__pycache__', '.git', 'build', 'bin', 'obj', 'Backup', '.mcr_devia'}

extensoes = {'.py', '.cpp', '.hpp', '.h', '.c', '.cs', '.lua', '.go'}

total_bugs_global = 0
total_arquivos_global = 0
t_global = time.time()

print("=" * 60)
print("  VARREDURA MCR-DevIA — Projeto MCR")
print(f"  Patterns: {len(PADROES_BUG)} bugs detectaveis")
print("=" * 60)

diretorios = [
    ("Canary src (C++)", os.path.join(PROJETO, "Canary", "src")),
    ("Canary data (Lua)", os.path.join(PROJETO, "Canary", "data-canary")),
    ("Grimorio (C#)", os.path.join(PROJETO, "MCR.Grimorio")),
    ("LoginServer (Go)", os.path.join(PROJETO, "LoginServer", "src")),
    ("DevIA (Python)", os.path.join(PROJETO, "historia", "scripts", "mcr_devia")),
    ("MCR engine (Python)", _BASE),
]

for nome, base_dir in diretorios:
    if not os.path.isdir(base_dir):
        print(f"\n--- {nome} --- DIRETORIO NAO ENCONTRADO: {base_dir}")
        continue
    
    arquivos = 0
    bugs = 0
    t0 = time.time()
    
    for raiz, dirs, arquivos_lista in os.walk(base_dir):
        # Pula diretorios ignorados
        dirs[:] = [d for d in dirs if d not in IGNORAR]
        for f in arquivos_lista:
            _, ext = os.path.splitext(f)
            if ext.lower() not in extensoes:
                continue
            caminho = os.path.join(raiz, f)
            if any(ign in caminho for ign in IGNORAR):
                continue
            
            encontrados = analisar_arquivo(caminho)
            arquivos += 1
            if encontrados:
                bugs += len(encontrados)
                total_bugs_global += len(encontrados)
                # Mostra ate 2 bugs por diretorio
                if bugs <= len(encontrados) * 2:
                    for b in encontrados:
                        rel = os.path.relpath(caminho, PROJETO)[:55]
                        print(f"  [{b['severidade'][0]}] {rel}:{b['linha']}")
                        print(f"       {b['descricao'][:90]}")
    
    t = time.time() - t0
    total_arquivos_global += arquivos
    print(f"\n--- {nome}: {arquivos} arquivos varridos, {bugs} bugs em {t:.1f}s ---\n")

t_total = time.time() - t_global
print("=" * 60)
print("  RESUMO")
print("=" * 60)
print(f"  Total arquivos: {total_arquivos_global}")
print(f"  Total bugs:     {total_bugs_global}")
print(f"  Tempo:          {t_total:.1f}s")
print(f"  Ms/arquivo:     {t_total/max(total_arquivos_global,1)*1000:.2f}ms")
print("=" * 60)
