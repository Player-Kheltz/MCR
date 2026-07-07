#!/usr/bin/env python3
"""Testa geracao com DB existente — sem refeed."""
import sys, os, re, time, math, sqlite3, random

os.chdir(r"E:\MCR")
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

OUT_DIR = r"E:\MCR\nichos\tibia\gerados"
os.makedirs(OUT_DIR, exist_ok=True)

DB_PATH = r"E:\MCR\cache\mcr_adapt.db"
if not os.path.exists(DB_PATH):
    print("ERRO: DB nao encontrado. Rode mcr_adapt.py primeiro.")
    sys.exit(1)

class SQLiteMarkov:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.n_max = 5
    
    def predizer_adaptativo(self, identity, contexto, entropia_max=0.3, fallback_fn=None, deterministico=False):
        for n in range(min(self.n_max, len(contexto)), 0, -1):  # N maior PRIMEIRO
            chave = identity + "|" + "|".join(contexto[-n:])
            cur = self.conn.execute(
                "SELECT t.next, t.count, COALESCE(f.total,0) FROM trans t "
                "LEFT JOIN freq f ON t.key=f.key WHERE t.key=? "
                "ORDER BY t.count DESC LIMIT 15", (chave,))
            rows = cur.fetchall()
            if not rows: continue
            total = rows[0][2]
            if deterministico:
                return rows[0][0], rows[0][1]/max(total,1), n
            if total < 8:
                total_counts = sum(r[1] for r in rows)
                r = random.random() * total_counts
                acc = 0
                for nt, cnt, _ in rows:
                    acc += cnt
                    if r <= acc:
                        return nt, 1.0 - (entropia_max/2), n
                return rows[0][0], 1.0 - (entropia_max/2), n
            ent = -sum((c/total)*math.log2(c/total) for _,c,_ in rows if c>0)
            if ent < entropia_max:
                top5 = rows[:5]
                t5 = sum(r[1] for r in top5)
                r = random.random() * t5
                acc = 0
                for nt, cnt, _ in top5:
                    acc += cnt
                    if r <= acc:
                        return nt, 1.0-ent, n
                return top5[0][0], 1.0-ent, n
        if fallback_fn and contexto:
            pred, conf = fallback_fn(contexto[-1])
            return pred, conf, 0
        return None, 0.0, 0

mk = SQLiteMarkov(DB_PATH)
c = CerebroAGI()
c.carregar(os.path.join(CACHE_DIR, "cerebro.json"))
mk_palavra = c.mk_palavra

def fallback(atual):
    return mk_palavra.predizer_com_entropia(atual)

def gerar(identity, seed="local", passos=80):
    seq = [seed]
    for i in range(passos):
        det = i < 5
        pred, conf, n = mk.predizer_adaptativo(identity, seq, 0.3, fallback, det)
        if pred is None or conf < 0.01: break
        if len(seq) >= 3 and all(t == pred for t in seq[-3:]): break
        seq.append(pred)
    return seq

def pos_processar(seq):
    tokens = [t for t in seq if not t.startswith("B:") and t != "<UNK>" and len(t) < 200]
    resultado = []
    for i, tok in enumerate(tokens):
        if i == 0:
            resultado.append(tok)
        else:
            prev = tokens[i-1]
            if tok in ")}],;":
                resultado.append(tok)
            elif prev in "([{":
                resultado.append(tok)
            elif tok == "=" and prev not in '([{':
                resultado.append(" " + tok)
            elif prev == "=" and tok not in '([{' and not tok.startswith('"') and not tok[0].isdigit():
                resultado.append(" " + tok)
            elif prev == ",":
                resultado.append(" " + tok)
            elif tok == ",":
                resultado.append(tok)
            else:
                resultado.append(" " + tok)
    texto = "".join(resultado)
    texto = re.sub(r'\s+', ' ', texto)
    texto = re.sub(r'\(\s+', '(', texto)
    texto = re.sub(r'\s+\)', ')', texto)
    texto = re.sub(r'\{\s+', '{', texto)
    texto = re.sub(r'\s+\}', '}', texto)
    texto = re.sub(r',\s+', ', ', texto)
    texto = re.sub(r'=\s+', '= ', texto)
    texto = texto.replace('\ufffd', '?')  # remove replacement chars
    return texto.strip()

# TESTES
for nome in ["Adrenius", "Ahmet", "Sapo Azul"]:
    print(f"\n{'='*60}")
    print(f"  {nome}")
    print(f"{'='*60}")
    seq = gerar(nome, "local", 80)
    texto = pos_processar(seq)
    print(f"  Tokens: {len(seq)}")
    print(f"  Saida:")
    for linha in [texto[i:i+100] for i in range(0, len(texto), 100)]:
        print(f"    {linha}")
    
    fp = os.path.join(OUT_DIR, f"test_{nome.replace(' ', '_')}.txt")
    with open(fp, "w", encoding="utf-8", errors="replace") as f:
        f.write(texto + "\n")

# COMPARACAO com arquivos reais
print(f"\n{'='*60}")
print(f"  COMPARACAO COM ARQUIVOS REAIS")
print(f"{'='*60}")

comparacoes = {
    "Adrenius": r"E:\Projeto MCR\Canary\data-otservbr-global\npc\adrenius.lua",
    "Ahmet": r"E:\Projeto MCR\Canary\data-otservbr-global\npc\ahmet.lua",
    "Sapo Azul": r"E:\Projeto MCR\Canary\data-otservbr-global\monster\amphibics\azure_frog.lua",
}

for nome, real_path in comparacoes.items():
    seq = gerar(nome, "local", 120)
    texto = pos_processar(seq)
    
    with open(real_path, "r", encoding="utf-8", errors="replace") as f:
        real = f.read()
    
    # Extract key-value pairs from real
    if "MonsterType" in real:
        campos = [
            ("experience", r'monster\.experience\s*=\s*(\d+)'),
            ("raceId", r'monster\.raceId\s*=\s*(\d+)'),
            ("health", r'monster\.health\s*=\s*(\d+)'),
            ("lookType", r'lookType\s*=\s*(\d+)'),
            ("lookHead", r'lookHead\s*=\s*(\d+)'),
            ("lookBody", r'lookBody\s*=\s*(\d+)'),
            ("corpse", r'monster\.corpse\s*=\s*(\d+)'),
            ("speed", r'monster\.speed\s*=\s*(\d+)'),
        ]
    else:
        campos = [
            ("health", r'npcConfig\.health\s*=\s*(\d+)'),
            ("maxHealth", r'npcConfig\.maxHealth\s*=\s*(\d+)'),
            ("walkInterval", r'npcConfig\.walkInterval\s*=\s*(\d+)'),
            ("walkRadius", r'npcConfig\.walkRadius\s*=\s*(\d+)'),
            ("lookType", r'lookType\s*=\s*(\d+)'),
        ]
    
    print(f"\n  {nome}:")
    acertos = 0
    total = 0
    for campo, padrao in campos:
        m_real = re.search(padrao, real)
        m_ger = re.search(padrao, texto)
        if m_real:
            total += 1
            val_real = m_real.group(1)
            val_ger = m_ger.group(1) if m_ger else "(ausente)"
            ok = "OK" if val_real == val_ger else "DIF"
            if val_real == val_ger: acertos += 1
            print(f"    {campo}: real={val_real} gerado={val_ger} [{ok}]")
    
    print(f"  Acertos: {acertos}/{total}")

mk.conn.close()
print(f"\nOK!")
