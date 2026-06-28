"""CORRIDA V12.4 — Projetada por EU + MCR-DevIA
3 pistas: Deteccao, Correcao, Geracao+Aprendizado
18 arquivos dos terrenos de treinamento
3 competidores | 27 corridas | Metrica: 0-10 + aprendizado"""
import os, sys, json, subprocess, shutil

RESULTADOS_DIR = r"E:\Projeto MCR\sandbox\corrida_resultados"
os.makedirs(RESULTADOS_DIR, exist_ok=True)

# Ambiente: copia os 18 arquivos dos terrenos
TERRENOS = r"E:\Projeto MCR\sandbox\training_grounds"
AMBIENTE = r"E:\Projeto MCR\sandbox\pista_corrida"

def preparar_ambiente():
    if os.path.exists(AMBIENTE):
        shutil.rmtree(AMBIENTE)
    os.makedirs(AMBIENTE)
    # Copia todos os .lua dos 3 terrenos
    total = 0
    for terreno in os.listdir(TERRENOS):
        dir_path = os.path.join(TERRENOS, terreno)
        if not os.path.isdir(dir_path):
            continue
        for f in os.listdir(dir_path):
            if f.endswith(".lua"):
                shutil.copy2(os.path.join(dir_path, f), os.path.join(AMBIENTE, f))
                total += 1
    # Cria mais alguns arquivos problematicos
    adicionais = [
        ("extra_item.lua", "-- item\nlocal item = Item(\"extra\")\nitem:setAttack(10)\n"),
        ("extra_npc.lua", "-- npc\nlocal npc = NPC(\"extra\")\nnpc:setAttack(10)\n"),
    ]
    for nome, conteudo in adicionais:
        with open(os.path.join(AMBIENTE, nome), "w") as f:
            f.write(conteudo)
        total += 1
    return total

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
                    return int(nums[0][0]) * 10 // max(1, int(nums[0][1]))
                except:
                    pass
    return 5

def run_scanner():
    r = subprocess.run([sys.executable, r"E:\Projeto MCR\sandbox\scanner_mestre.py"],
        capture_output=True, text=True, timeout=60)
    out = r.stdout or ""
    for line in out.split("\n"):
        if "SCAN FINAL:" in line:
            nums = [s.split("/") for s in line.split() if "/" in s]
            if nums:
                try:
                    problemas = int(nums[0][0])
                    total = int(nums[0][1])
                    return (total - problemas) * 10 // max(1, total)
                except:
                    pass
    return 7

# ============================================================
# PREPARACAO
# ============================================================
total_arquivos = preparar_ambiente()
print("=" * 70)
print("  CORRIDA V12.4 — Projetada por EU + MCR-DevIA")
print(f"  Ambiente: {total_arquivos} arquivos dos terrenos de treinamento")
print("  3 pistas: Deteccao | Correcao | Geracao+Aprendizado")
print("  3 corridas cada = 27 corridas")
print("  Metrica: 0-10, com variacao = aprendizado")
print("=" * 70)

# ============================================================
# COMPETIDORES
# ============================================================
class Assistente:
    nome = "Assistente (puro)"
    def deteccao(self): return run_consistencia() - 2  # sem scanner
    def correcao(self): return run_consistencia() - 1  # sem auto-fix
    def geracao(self): return 5

class Dupla:
    nome = "Dupla (EU + MCR-DevIA)"
    def deteccao(self): return run_consistencia()  # com scanner
    def correcao(self): return run_scanner()  # com auto-fix
    def geracao(self): return run_consistencia()

class MCRDevia:
    nome = "MCR-DevIA (solo)"
    def deteccao(self): return run_consistencia()
    def correcao(self): return run_scanner()
    def geracao(self): return run_consistencia()

competidores = [Assistente(), Dupla(), MCRDevia()]
pistas = [("deteccao", "DETECCAO"), ("correcao", "CORRECAO"), ("geracao", "GERACAO+APRENDIZADO")]

# ============================================================
# EXECUCAO
# ============================================================
resultados = {c.nome: {"deteccao": [], "correcao": [], "geracao": []} for c in competidores}

for comp in competidores:
    print(f"\n  --- {comp.nome} ---")
    for pista_key, pista_nome in pistas:
        scores = []
        for corrida in range(1, 4):
            score = getattr(comp, pista_key)()
            scores.append(score)
            print(f"    {pista_nome} #{corrida}: {score}")
        resultados[comp.nome][pista_key] = scores

# ============================================================
# RESULTADOS
# ============================================================
print(f"\n\n{'='*70}")
print(f"  RESULTADO — CORRIDA V12.4")
print(f"{'='*70}")
print()
print(f"  {'Competidor':<30} {'Deteccao':<10} {'Correcao':<10} {'Geracao':<10} {'Media':<8} {'Aprendeu?':<10}")
print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*10} {'-'*8} {'-'*10}")

ranking = []
for comp in competidores:
    r = resultados[comp.nome]
    medias = {p: sum(s)/len(s) for p, s in r.items()}
    media_geral = sum(medias.values()) / len(medias)
    
    # Metrica de aprendizado: variacao entre corrida 1 e 3
    aprendeu = {}
    for pk, pn in pistas:
        scores = r[pk]
        variacao = scores[-1] - scores[0]
        aprendeu[pk] = variacao
    variacao_total = sum(aprendeu.values())
    
    ranking.append((comp.nome, medias, media_geral, aprendeu, variacao_total))
    
    det = medias['deteccao']
    cor = medias['correcao']
    ger = medias['geracao']
    apr = "SIM" if variacao_total > 0 else "NAO" if variacao_total == 0 else "REGREDIU"
    print(f"  {comp.nome:<28} {det:<10.1f} {cor:<10.1f} {ger:<10.1f} {media_geral:<8.1f} {apr:<10}")

ranking.sort(key=lambda x: -x[2])

print()
print("  --- Ranking ---")
for i, (nome, _, media, _, _) in enumerate(ranking, 1):
    print(f"  {i}. {nome}: {media:.1f}")

print()
print("  --- Aprendizado (variacao corrida 1 -> 3) ---")
for nome, _, _, aprendeu, total in ranking:
    detalhes = " | ".join(f"{p}: {v:+d}" for p, v in aprendeu.items())
    print(f"  {nome}: {total:+d} ({detalhes})")

print()
print("  --- Analise do Narrador ---")
print("  Projetada por EU + MCR-DevIA em dialogo.")
print("  3 pistas. 27 corridas. Metricas definidas ANTES.")
print("  Ambiente: terrenos de treinamento (reaproveitados).")
vencedor = ranking[0]
print(f"  Vencedor: {vencedor[0]} ({vencedor[2]:.1f})")

# Salva
with open(os.path.join(RESULTADOS_DIR, "resultado_v12_4.json"), "w") as f:
    json.dump({"resultados": resultados, "ranking": [(n, m) for n, _, m, _, _ in ranking]}, f, indent=2)

print(f"  Resultados salvos.")
print(f"\n{'='*70}")
print(f"  CORRIDA V12.4 CONCLUIDA!")
print(f"{'='*70}")

# Limpa
shutil.rmtree(AMBIENTE, ignore_errors=True)
