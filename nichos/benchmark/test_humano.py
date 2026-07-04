#!/usr/bin/env python3
import sys, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(BASE_DIR, "..", ".."))
sys.path.insert(0, os.getcwd())
exec(compile(open("MCR_AGI.py", encoding="utf-8").read().split("def main():")[0], "MCR_AGI.py", "exec"))
ARQUIVO = r"C:\Windows\Logs\CBS\FilterList.log"
PONTOS = 0
def check(n, c):
    global PONTOS
    if c: PONTOS += 1; print(f"  OK {n}")
    else: print(f"  FAIL {n}")
with open(ARQUIVO, errors="replace") as f: C = f.read()
L = C.strip().split(chr(10))
print(f"  Linhas: {len(L)}")
mk = MCR("h")
met = len(L) // 2
for i in range(met - 1): mk.aprender(L[i].strip(), L[i+1].strip())
print(f"  Entropia: {mk.entropia_media():.3f}")
ac = 0; tt = 0
for i in range(met - 1, min(len(L) - 1, met + 100)):
    mk.aprender(L[i].strip(), L[i+1].strip())
    p, c = mk.predizer(L[i].strip()); tt += 1
    if p == L[i+1].strip(): ac += 1
print(f"  Pred: {ac}/{tt} = {ac/max(tt,1):.0%}")
check("aprende", ac/max(tt,1) > 0.3)
g = mk.gerar(L[met-1].strip(), 10)
print(f"  Gerado: {len(g)}")
check("gera", len(g) >= 2)
e1 = mk.entropia_media()
for i in range(met, len(L) - 1): mk.aprender(L[i].strip(), L[i+1].strip())
e2 = mk.entropia_media()
print(f"  Ent: {e1:.3f} -> {e2:.3f}")
check("entropia", e2 <= e1 + 0.1)
print(f"  PTS: {PONTOS}/4")
