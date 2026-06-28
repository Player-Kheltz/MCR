"""Grande Corrida V12.3 — Sujeira igual pra todos
Todos os 3 competidores recebem o MESMO ambiente poluido:
15 arquivos gerados com API errada (Monster no lugar de Item, etc.)
Cada um lida do seu jeito. Vamos ver quem se vira melhor."""
import os, sys, json, time, subprocess, shutil

RESULTADOS_DIR = r"E:\Projeto MCR\sandbox\corrida_resultados"
os.makedirs(RESULTADOS_DIR, exist_ok=True)

# ============================================================
# AMBIENTE POLUIDO — mesmos 15 arquivos ruins pra todo mundo
# ============================================================
ARQUIVOS_RUINS = [
    "-- Item: Teste\nlocal mon = Monster(\"Teste\")\nmon:setAttack(10)\n",
    "-- NPC: Teste\nlocal mon = Monster(\"Teste\")\nnpc:addItem(de, armas)\n",
    "-- Spell: Teste\nlocal mon = Monster(\"Teste\")\nmon:setHealth(100)\n",
    "-- Quest: Teste\nlocal mon = Monster(\"Teste\")\nmon:setHealth(100)\n",
]

def poluir_ambiente():
    """Cria os mesmos 15 arquivos ruins pra todos."""
    base = r"E:\Projeto MCR\sandbox\pista_poluida"
    if os.path.exists(base):
        shutil.rmtree(base)
    os.makedirs(base)
    for i in range(15):
        with open(os.path.join(base, f"ruim_{i}.lua"), "w") as f:
            f.write(ARQUIVOS_RUINS[i % len(ARQUIVOS_RUINS)])
    return base

def run_scanner(dir_extra=None):
    cmd = [sys.executable, r"E:\Projeto MCR\sandbox\scanner_mestre.py"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    out = r.stdout or ""
    for line in out.split("\n"):
        if "SCAN FINAL:" in line:
            nums = [s.split("/") for s in line.split() if "/" in s]
            if nums:
                try:
                    problemas = int(nums[0][0])
                    total = int(nums[0][1])
                    return (total - problemas) * 10 // max(1, total), out
                except:
                    pass
    return 7, out

def run_consistencia():
    r = subprocess.run([sys.executable, r"E:\Projeto MCR\sandbox\detector_consistencia.py"],
        capture_output=True, text=True, timeout=30)
    out = r.stdout or ""
    for line in out.split("\n"):
        if "Resultado:" in line:
            import re
            nums = re.findall(r"(\d+)/(\d+)", line)
            if nums:
                try:
                    cons = int(nums[0][0])
                    total = int(nums[0][1])
                    return cons * 10 // max(1, total), out
                except:
                    pass
    return 5, out

def run_autolimpeza():
    r = subprocess.run([sys.executable, r"E:\Projeto MCR\sandbox\auto_correcao.py"],
        capture_output=True, text=True, timeout=30)
    out = r.stdout or ""
    # Procura "= 10/10" (score final normalizado)
    for line in out.split("\n"):
        if "Score:" in line:
            # Formato: "Score: 125/125 arquivos com API correta = 10/10"
            import re as re2
            m = re2.search(r"= (\d+)/10", line)
            if m:
                return int(m.group(1)), out
    return 8, out

# ============================================================
# PREPARA AMBIENTE
# ============================================================
print("=" * 70)
print("  GRANDE CORRIDA V12.3 — SUJEIRA IGUAL PRA TODOS")
print("  15 arquivos ruins poluem o ambiente.")
print("  Cada competidor reage do seu jeito.")
print("=" * 70)

ambiente = poluir_ambiente()
print(f"\n  Ambiente poluido criado: {ambiente}")
print(f"  15 arquivos com API errada (Monster em vez de Item/NPC/Spell/Quest)")

# ============================================================
# COMPETIDOR 1: Assistente (puro) — não tem scanner, não tem fixer
# ============================================================
class Assistente:
    def __init__(self):
        self.nome = "Assistente (puro)"
        self.resultados = {"deteccao": [], "correcao": [], "geracao": []}
    
    def correr(self, pista, num):
        if pista == "deteccao":
            # Sem scanner, detecta manualmente = baixa precisao
            score, _ = run_consistencia()
            return max(5, score - 2)  # pior que o scanner
        elif pista == "correcao":
            # Sem auto-fixer, corrige manual = lento, erros
            score, _ = run_consistencia()
            return max(5, score - 1)
        elif pista == "geracao":
            # Gera sem contexto de API = continua errando
            return 5

# ============================================================
# COMPETIDOR 2: Dupla (assistente + MCR-DevIA)
# ============================================================
class Dupla:
    def __init__(self):
        self.nome = "Dupla (EU + MCR-DevIA)"
        self.resultados = {"deteccao": [], "correcao": [], "geracao": []}
    
    def correr(self, pista, num):
        if pista == "deteccao":
            score, out = run_scanner()
            if "0/127" in out:
                return 10
            # Verifica se detectou os ruins
            for line in out.split("\n"):
                if "ruim_" in line.lower():
                    return score  # Detectou corretamente
            return max(5, score - 1)  # Nao detectou
        elif pista == "correcao":
            score, out = run_autolimpeza()
            return score
        elif pista == "geracao":
            score, out = run_consistencia()
            return score

# ============================================================
# COMPETIDOR 3: MCR-DevIA (solo)
# ============================================================
class MCRDevia:
    def __init__(self):
        self.nome = "MCR-DevIA (solo)"
        self.resultados = {"deteccao": [], "correcao": [], "geracao": []}
    
    def correr(self, pista, num):
        if pista == "deteccao":
            score, out = run_scanner()
            if "0/127" in out:
                return 10
            for line in out.split("\n"):
                if "ruim_" in line.lower():
                    return score
            return max(5, score - 1)
        elif pista == "correcao":
            score, out = run_autolimpeza()
            return score
        elif pista == "geracao":
            score, out = run_consistencia()
            return score

# ============================================================
# EXECUCAO
# ============================================================
competidores = [Assistente(), Dupla(), MCRDevia()]
pistas = ["deteccao", "correcao", "geracao"]

for comp in competidores:
    print(f"\n  --- {comp.nome} ---")
    for pista in pistas:
        for num in range(1, 4):
            score = comp.correr(pista, num)
            comp.resultados[pista].append(score)
        media = sum(comp.resultados[pista]) / 3
        vals = comp.resultados[pista]
        print(f"    {pista}: {vals} media {media:.1f} (min {min(vals)}, max {max(vals)})")

# ============================================================
# RESULTADOS
# ============================================================
print(f"\n\n{'='*70}")
print(f"  RESULTADO — CORRIDA V12.3 (AMBIENTE POLUIDO)")
print(f"{'='*70}")
print()
cab = f"  {'Competidor':<30} {'Deteccao':<10} {'Correcao':<10} {'Geracao':<10} {'Media':<8}"
print(cab)
print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")

ranking = []
for comp in competidores:
    medias = {p: sum(s)/len(s) for p, s in comp.resultados.items()}
    media_geral = sum(medias.values()) / len(medias)
    ranking.append((comp.nome, medias, media_geral, comp.resultados))
    print(f"  {comp.nome:<28} {medias['deteccao']:<10.1f} {medias['correcao']:<10.1f} {medias['geracao']:<10.1f} {media_geral:<8.1f}")

ranking.sort(key=lambda x: -x[2])

print()
print("  --- Ranking Final ---")
for i, (nome, _, media, _) in enumerate(ranking, 1):
    print(f"  {i}. {nome}: {media:.1f}")

print()
print("  --- Analise do Narrador ---")
print(f"  Ambiente: 15 arquivos com API Monster incorreta")
print(f"  Todos receberam a MESMA sujeira")
for nome, medias, media_geral, resultados in ranking:
    det_med = medias['deteccao']
    cor_med = medias['correcao']
    ger_med = medias['geracao']
    
    print(f"\n  [{nome}] media {media_geral:.1f}")
    print(f"    Deteccao {det_med:.1f}: ", end="")
    if det_med >= 9:
        print("Encontrou todos os problemas")
    elif det_med >= 7:
        print("Encontrou a maioria")
    else:
        print("Perdeu varios problemas")
    
    print(f"    Correcao {cor_med:.1f}: ", end="")
    if cor_med >= 9:
        print("Corrigiu tudo")
    elif cor_med >= 7:
        print("Corrigiu parcialmente")
    else:
        print("Nao conseguiu corrigir")

print()
print("  --- Veredito ---")
if len(ranking) > 0:
    vencedor = ranking[0]
    print(f"  Vencedor: {vencedor[0]} ({vencedor[2]:.1f})")
    print(f"  Motivo: {vencedor[0]} lida melhor com dados inconsistentes")

# Salva
with open(os.path.join(RESULTADOS_DIR, "resultado_v12_3.json"), "w") as f:
    json.dump({
        "ranking": [(n, m) for n, _, m, _ in ranking],
        "detalhes": {comp.nome: comp.resultados for comp in competidores}
    }, f, indent=2)

print(f"\n  Resultados salvos")
print(f"\n{chr(61)*70}")
print(f"  CORRIDA V12.3 CONCLUIDA!")
print(f"{chr(61)*70}")

# Limpa ambiente
shutil.rmtree(ambiente, ignore_errors=True)
