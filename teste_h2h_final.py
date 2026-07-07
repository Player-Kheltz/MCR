"""Teste head-to-head FINAL: MCR-DevIA (code_analyzer + 7b + dedup) vs Cloud."""
import sys, os, time, re

sys.path.insert(0, r'E:\MCR')
from mcr_devia import processar, _decider, _router, _llm, MODELO_POR_CLASSE
from code_analyzer import analisar_arquivo

cmd_path = r"E:\Projeto MCR\historia\scripts\mcr_devia\comandos\cmd_grep.py"

print("=" * 55)
print("  HEAD-TO-HEAD FINAL: MCR-DevIA vs Cloud")
print("  Arquivo: cmd_grep.py")
print("=" * 55)

# ─── MCR-DevIA (pipeline completa) ─────────────────
print("\n[MCR-DevIA] Rodando pipeline completa...")
print(f"  (code_analyzer 0ms + LLM {MODELO_POR_CLASSE.get('analisar_bug','7b')} + dedup)")

t0_total = time.time()
r = processar("Analise o arquivo comandos/cmd_grep.py. Encontre bugs e sugira correcoes.")
t_total = time.time() - t0_total

classe = r['classe']
conf = r['confianca']
acoes = r['acoes']
valido = r['validacao']['valida']
resp = r['resposta']

print(f"  Classe: {classe} ({conf:.2f})")
print(f"  Pipeline: {acoes}")
print(f"  Tempo total: {t_total:.1f}s")
print(f"  Validacao: {'OK' if valido else 'X'}")
print(f"  Resposta: {len(resp)} chars")
print(f"\n=== RESPOSTA MCR-DevIA ===")
print(resp[:2500])
print("=== FIM MCR-DevIA ===")

# ─── Code Analyzer deterministico ─────────────────
print(f"\n[Code Analyzer] Deteccao deterministica (0ms)...")
t0 = time.time()
bugs_det = analisar_arquivo(cmd_path)
t_det = time.time() - t0
print(f"  {len(bugs_det)} bugs encontrados em {t_det*1000:.1f}ms:")
for b in bugs_det:
    print(f"    {b['arquivo']}:{b['linha']} ({b['severidade']}): {b['descricao'][:80]}...")

# ─── Cloud (eu) ─────────────────
print(f"\n[Cloud] Analisando...")
bugs_cloud = [
    ("cmd_grep.py:40", "Alta", "re_padrao nunca definido se re.compile(falha) -> NameError", "return ou checar None antes de usar"),
    ("cmd_grep.py:26", "Alta", "Diretorio padrao=SANDBOX, nao o projeto", "Mudar default para BASE (projeto)"),
    ("cmd_grep.py:23", "Media", "BASE usa path relativo -> historia/ em vez do projeto", "os.environ.get('MCR_PROJECT_BASE', BASE)"),
    ("cmd_grep.py:52", "Media", "So busca 6 extensoes, ignora .cpp .hpp .cs .go", "Adicionar .cpp .hpp .cs .go .xaml .sln"),
    ("cmd_grep.py:61", "Media", "errors='replace' perde caracteres", "Tentar UTF-8, fallback Latin-1 por extensao"),
    ("cmd_grep.py:82", "Baixa", "except: pass suprime excecoes", "except (UnicodeDecodeError, PermissionError) as e: print(e)"),
    ("cmd_grep.py:49", "Media", "os.walk() sem limite de profundidade", "max_depth + timeout 30s"),
]
for i, (loc, sev, desc, fix) in enumerate(bugs_cloud):
    print(f"  [{i+1}] {loc} ({sev}): {desc}")

# ─── COMPARACAO ─────────────────
print(f"\n{'='*55}")
print(f"  COMPARACAO DIRETA")
print(f"{'='*55}")

# Overlap deterministico vs cloud
det_bugs_set = {(b['descricao'][:40], b['severidade']) for b in bugs_det}
cloud_bugs_set = {(desc[:40], sev) for _, sev, desc, _ in bugs_cloud}
overlap_det = len(det_bugs_set & cloud_bugs_set)

# Overlap MCR (LLM) vs cloud
mcr_matches = 0
for _, _, desc, _ in bugs_cloud:
    palavras = desc.lower().split()[:3]
    trecho = ' '.join(palavras)
    if trecho in resp.lower():
        mcr_matches += 1

print(f"  code_analyzer (0ms):  {len(bugs_det)} bugs, overlap com Cloud: {overlap_det}/{len(bugs_cloud)}")
print(f"  MCR-DevIA + LLM:      {len(resp)} chars em {t_total:.1f}s, overlap com Cloud: {mcr_matches}/{len(bugs_cloud)}")
print(f"  Cloud:                {len(bugs_cloud)} bugs (todos com linha, 0 duplicatas)")
print(f"")
print(f"  DADOS BRUTOS. Tire suas conclusoes.")

# Aprendizado
_decider.aprender("Analise arquivo cmd_grep.py encontre bugs", "analisar_bug")
