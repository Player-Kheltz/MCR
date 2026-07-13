import sys, os, re, random, sqlite3, math

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
_MCR_ROOT = _BASE
os.chdir(_MCR_ROOT)
sys.path.insert(0, '.')
try:
    from MCR import CerebroAGI
except ImportError:
    CerebroAGI = None

class SQLiteMarkov:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
    def predizer(self, identity, contexto, det=False):
        # Tenta N maior primeiro (mais especifico)
        max_n = min(5, len(contexto))
        for n in range(max_n, 0, -1):
            chave = identity + "|" + "|".join(contexto[-n:])
            cur = self.conn.execute(
                "SELECT t.next, t.count, COALESCE(f.total,0) FROM trans t "
                "LEFT JOIN freq f ON t.key=f.key WHERE t.key=? ORDER BY t.count DESC LIMIT 15",
                (chave,))
            rows = cur.fetchall()
            if not rows:
                continue
            total = rows[0][2]
            if det or total < 5:
                return rows[0][0], rows[0][1] / max(total, 1), n
            ent = -sum((c/total)*math.log2(c/total) for _, c, _ in rows if c > 0)
            if ent < 0.3:
                top5 = rows[:5]
                t5 = sum(r[1] for r in top5)
                r2 = random.random() * t5
                acc = 0
                for nt, c, _ in top5:
                    acc += c
                    if r2 <= acc:
                        return nt, 1.0 - ent, n
                return top5[0][0], 1.0 - ent, n
        return None, 0.0, 0

mk = SQLiteMarkov(os.path.join(_BASE, "cache", "mcr_adapt.db"))
c = CerebroAGI()
c.carregar(os.path.join(CACHE_DIR, "cerebro.json"))
mk_palavra = c.mk_palavra

def gerar(identity, seed="local", passos=80):
    seq = [seed]
    for i in range(passos):
        det = i < 5
        pred, conf, n = mk.predizer(identity, seq, det)
        if pred is None or conf < 0.01:
            if det:
                p2, c2 = mk_palavra.predizer_com_entropia(seq[-1])
                if p2 and c2 > 0.01:
                    pred = p2
        if pred is None:
            break
        if len(seq) >= 3 and all(t == pred for t in seq[-3:]):
            break
        seq.append(pred)
    return seq

def clean(seq):
    tokens = [t for t in seq if not t.startswith("B:") and t != "<UNK>" and len(t) < 80]
    i = 0
    merged = []
    while i < len(tokens):
        if tokens[i] in ('"', "'"):
            open_q = tokens[i]
            for j in range(i + 1, len(tokens)):
                if tokens[j] == open_q:
                    inner = " ".join(tokens[i+1:j])
                    merged.append(open_q + inner + open_q)
                    i = j + 1
                    break
            else:
                merged.append(tokens[i])
                i += 1
        else:
            merged.append(tokens[i])
            i += 1
    texto = " ".join(merged)
    texto = texto.replace("= ,", "=")
    texto = texto.replace(",}", "}")
    texto = texto.replace(",)", ")")
    texto = texto.replace("= {", "= {")
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

# Test
for nome in ["Sapo Azul", "Adrenius", "Ahmet"]:
    seq = gerar(nome, "local", 80)
    saida = clean(seq)
    fp = os.path.join(_BASE, "nichos", "tibia", "gerados", "test_" + nome.replace(" ", "_") + ".txt")
    with open(fp, "w") as f:
        f.write(saida)
    print(f"=== {nome} ({len(seq)} tokens) ===")
    print(saida[:300])
    print()
