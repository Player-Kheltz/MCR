#!/usr/bin/env python3
"""MCR Adaptativo — SQLite backend, Markov N=1..5 c/ identidade.

Alimenta NPCs + Monstros, gera com entropia como criterio de parada.
"""

import sys, os, re, time, math, sqlite3, random

os.chdir(r"E:\MCR")
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

OUT_DIR = r"E:\MCR\nichos\tibia\gerados"
os.makedirs(OUT_DIR, exist_ok=True)

# ─── SQLITE BACKEND ─────────────────────────────────────
class SQLiteMarkov:
    """Armazena transicoes Markov N=1..N_MAX em SQLite.
    
    Tabelas:
      trans(key, next, count) — transicoes
      freq(key, total) — total de ocorrencias por chave
    
    key formato: "identidade|tok1|tok2|...|tokN"
    """
    
    def __init__(self, db_path, n_max=30):
        self.db_path = db_path
        self.n_max = n_max
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA cache_size=-8000")  # 8MB cache
        self.conn.execute("PRAGMA synchronous=OFF")   # bulk insert speed
        self._init_tables()
        self._stats = {'trans': 0, 'freq': 0}
    
    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS trans (
                key TEXT NOT NULL,
                next TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (key, next)
            ) WITHOUT ROWID
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS freq (
                key TEXT PRIMARY KEY,
                total INTEGER DEFAULT 0
            ) WITHOUT ROWID
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_trans_key ON trans(key)
        """)
        self.conn.commit()
    
    def alimentar(self, identity, tokens):
        """N adaptativo: guarda N=1 sempre, N+1 só quando N colide (>1 next possível).
        
        Ex: 'ident|)' → {local, end} (2 nexts) → precisa N+1
            'ident|message|)' → {local, end} (2 nexts) → precisa N+1
            'ident|:|onSay|(|npc' → {,} (1 next) → OK, N=7 basta
        """
        nome_limpo = re.sub(r'[^\w\s\u00C0-\u00FF-]', '', identity).strip()[:30]
        if not nome_limpo or len(tokens) < 3:
            return 0
        
        # Fase 1: conta em memória para esta identidade
        # counts[(n, tok1..tokN)] → {next: count}
        counts = {}
        for n in range(1, self.n_max + 1):
            for i in range(len(tokens) - n):
                chave = (n,) + tuple(tokens[i:i+n])
                prox = tokens[i+n]
                if chave not in counts:
                    counts[chave] = {}
                counts[chave][prox] = counts[chave].get(prox, 0) + 1
        
        # Fase 2: dedup — guarda N=1..N_KEEP sempre (cadeia completa);
        # para N > N_KEEP, guarda só quando distribuição difere do backoff.
        N_KEEP = 5
        batch_trans = []
        batch_freq = {}
        for (n, *ctx), nexts in counts.items():
            keep = n <= N_KEEP
            if not keep:
                sufixo = tuple(ctx[1:])
                parent_key = (n-1,) + sufixo
                parent = counts.get(parent_key)
                if parent is None or set(nexts.keys()) != set(parent.keys()):
                    keep = True
            
            if keep:
                chave = f"{nome_limpo}|{'|'.join(ctx)}"
                for prox, cnt in nexts.items():
                    batch_trans.append((chave, prox))
                    batch_freq[chave] = batch_freq.get(chave, 0) + cnt
        
        if identity == 'Ahmet':
            pass  # debug placeholder
        
        # Fase 3: batch insert
        self.conn.executemany(
            "INSERT INTO trans(key, next, count) VALUES (?, ?, 1) "
            "ON CONFLICT(key, next) DO UPDATE SET count = count + 1",
            batch_trans)
        
        for chave, delta in batch_freq.items():
            self.conn.execute(
                "INSERT INTO freq(key, total) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET total = total + ?",
                (chave, delta, delta))
        
        self._stats['trans'] += len(batch_trans)
        self._stats['freq'] += len(batch_freq)
        return len(batch_trans)
    
    def commit(self):
        self.conn.commit()
    
    def obter_distribuicao(self, identity, contexto, n_max=None):
        """Pega distribuicao (next, count) para identidade + contexto.
        
        Tenta N=n_max, n_max-1, ..., 1 ate encontrar dados.
        Retorna lista de (next, count, total).
        """
        n_max = n_max or self.n_max
        for n in range(min(n_max, len(contexto)), 0, -1):
            chave = f"{identity}|{'|'.join(contexto[-n:])}"
            cur = self.conn.execute(
                "SELECT t.next, t.count, COALESCE(f.total, 0) "
                "FROM trans t "
                "LEFT JOIN freq f ON t.key = f.key "
                "WHERE t.key = ? "
                "ORDER BY t.count DESC LIMIT 20",
                (chave,))
            rows = cur.fetchall()
            if rows:
                return rows, n  # (distribuicao, ordem_utilizada)
        return [], 0
    
    def entropia(self, rows, total):
        """Calcula entropia de uma distribuicao."""
        if not rows or total == 0:
            return 1.0
        return -sum((c/total) * math.log2(c/total) for _, c, _ in rows if c > 0)
    
    def predizer_adaptativo(self, identity, contexto, entropia_max=0.3, fallback_fn=None, deterministico=False):
        """Prediz expandindo contexto ate entropia < threshold.
        
        deterministico=True: escolhe moda (mais frequente), ignora entropia.
        Se entropia > threshold para todos N, usa fallback_fn.
        """
        max_n = min(self.n_max, len(contexto))
        for n in range(max_n, 0, -1):  # N maior primeiro
            chave = f"{identity}|{'|'.join(contexto[-n:])}"
            cur = self.conn.execute(
                "SELECT t.next, t.count, COALESCE(f.total, 0) "
                "FROM trans t "
                "LEFT JOIN freq f ON t.key = f.key "
                "WHERE t.key = ? "
                "ORDER BY t.count DESC LIMIT 15",
                (chave,))
            rows = cur.fetchall()
            if not rows:
                continue
            total = rows[0][2]
            
            # Moda: sempre aceita na primeira tentativa
            if deterministico:
                return rows[0][0], rows[0][1] / max(total, 1), n
            
            # Para poucos exemplares, aceita mesmo com entropia alta
            # (identidade tem dados esparsos — melhor usar o que tem
            #  do que cair no fallback global que ignora identidade)
            if total < 8:
                # Escolha ponderada entre todos
                total_counts = sum(r[1] for r in rows)
                r = random.random() * total_counts
                acc = 0
                for next_tok, cnt, _ in rows:
                    acc += cnt
                    if r <= acc:
                        return next_tok, 1.0 - (entropia_max / 2), n
                return rows[0][0], 1.0 - (entropia_max / 2), n
            
            ent = self.entropia(rows, total)
            if ent < entropia_max:
                top5 = rows[:5]
                total_top5 = sum(r[1] for r in top5)
                r = random.random() * total_top5
                acc = 0
                for next_tok, cnt, _ in top5:
                    acc += cnt
                    if r <= acc:
                        return next_tok, 1.0 - ent, n
                return top5[0][0], 1.0 - ent, n
        
        # Fallback
        if fallback_fn:
            pred, conf = fallback_fn(contexto[-1] if contexto else '')
            return pred, conf, 0
        return None, 0.0, 0
    
    def stats(self):
        cur = self.conn.execute("SELECT COUNT(*) FROM trans")
        n_trans = cur.fetchone()[0]
        cur = self.conn.execute("SELECT COUNT(*) FROM freq")
        n_freq = cur.fetchone()[0]
        return n_trans, n_freq
    
    def close(self):
        self.conn.commit()
        self.conn.close()

# ─── TOKENIZACAO ─────────────────────────────────────────
def tokenizar(texto):
    """Tokeniza: strings quoted como bloco, todo o resto como antes.
    
    Diferenca do split original: "Sapo Azul" vira 1 token, nao 4.
    () {} . : continuam separados para flexibilidade Markov.
    """
    tokens = []
    i = 0
    while i < len(texto):
        c = texto[i]
        
        if c.isspace():
            i += 1
            continue
            
        # String quoted como bloco unico
        if c in ('"', "'"):
            quote = c
            j = i + 1
            while j < len(texto) and texto[j] != quote:
                j += 1
            if j < len(texto):
                tokens.append(texto[i:j+1])
                i = j + 1
            else:
                tokens.append(texto[i:])
                i = len(texto)
            continue
            
        # Palavra normal (inclui pontos para nomes como Game.createMonsterType)
        if c.isalnum() or c in '_.':
            j = i
            while j < len(texto) and (texto[j].isalnum() or texto[j] in '_.'):
                j += 1
            tokens.append(texto[i:j])
            i = j
            continue
            
        # Operadores e pontuacao como tokens separados
        if c in ',;:+-*/<>~|&#@%^=':
            tokens.append(c)
            i += 1
            continue
            
        # Parenteses e chaves como tokens separados
        if c in '()[]{}':
            tokens.append(c)
            i += 1
            continue
            
        # Qualquer outro caractere
        tokens.append(c)
        i += 1
        
    return tokens

def extrair_identidade(texto):
    nome = ""
    for linha in texto.split('\n'):
        linha = linha.strip()
        if 'internalNpcName' in linha or 'Game.createNpcType' in linha or 'Game.createMonsterType' in linha:
            m = re.search(r'"(.*?)"', linha)
            if m:
                nome = m.group(1).strip()
                break
    return nome

# ─── ALIMENTACAO ─────────────────────────────────────────
DB_PATH = r"E:\MCR\cache\mcr_adapt.db"

# Remove db anterior se existir
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"DB anterior removido")

mk = SQLiteMarkov(DB_PATH, n_max=30)
print(f"SQLite criado: {DB_PATH}")

t0 = time.perf_counter()
total_arqs = 0

# NPCs
RAIZ_NPC = r"E:\Projeto MCR\Canary\data-otservbr-global\npc"
for raiz, dirs, files in os.walk(RAIZ_NPC):
    for f in files:
        if not f.endswith('.lua'): continue
        fp = os.path.join(raiz, f)
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                texto = fh.read()
            nome = extrair_identidade(texto)
            if not nome:
                nome = os.path.splitext(f)[0]
            tokens = tokenizar(texto)
            if len(tokens) >= 5:
                mk.alimentar(nome, tokens)
                total_arqs += 1
                if total_arqs % 200 == 0:
                    mk.commit()
                    print(f"  [{total_arqs}] NPCs...")
        except: pass
mk.commit()

# Monstros
RAIZ_MON = r"E:\Projeto MCR\Canary\data-otservbr-global\monster"
for raiz, dirs, files in os.walk(RAIZ_MON):
    for f in files:
        if not f.endswith('.lua'): continue
        fp = os.path.join(raiz, f)
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                texto = fh.read()
            nome = extrair_identidade(texto)
            if not nome:
                nome = os.path.splitext(f)[0]
            tokens = tokenizar(texto)
            if len(tokens) >= 5:
                mk.alimentar(nome, tokens)
                total_arqs += 1
                if total_arqs % 200 == 0:
                    mk.commit()
                    print(f"  [{total_arqs}] Total...")
        except: pass
mk.commit()

t1 = time.perf_counter()
n_trans, n_freq = mk.stats()
print(f"\nAlimentado: {total_arqs} arquivos em {t1-t0:.1f}s")
print(f"Transicoes: {n_trans:,}")
print(f"Chaves: {n_freq:,}")
print(f"Tamanho DB: {os.path.getsize(DB_PATH)/1024/1024:.0f} MB")

# ─── GERADOR ────────────────────────────────────────────
def gerar_com_identidade(mk, identity, seed='local', passos=120, entropia_max=0.3):
    """Gera sequencia usando mk_id adaptativo + mk_palavra fallback.
    
    5 primeiros passos deterministicos (moda) para garantir o caminho
    da identidade; depois entropia adaptativa para variedade.
    """
    c = CerebroAGI()
    c.carregar(os.path.join(CACHE_DIR, "cerebro.json"))
    mk_palavra = c.mk_palavra
    
    def fallback(atual):
        return mk_palavra.predizer_com_entropia(atual)
    
    seq = [seed]
    for i in range(passos):
        det = i < 5  # 5 passos deterministicos para firmar identidade
        pred, conf, n = mk.predizer_adaptativo(identity, seq, entropia_max, fallback, det)
        if pred is None or conf < 0.01:
            break
        if len(seq) >= 3 and all(t == pred for t in seq[-3:]):
            break
        seq.append(pred)
    return seq

def pos_processar(seq):
    """Tokens já vêm formatados (strings quoted, function calls). Apenas junta com espaços apropriados."""
    if not seq:
        return ''
    
    # Filtra tokens de controle
    tokens = [t for t in seq if not t.startswith('B:') and t != '<UNK>' and len(t) < 200]
    
    # Junta tokens com espaços inteligentes
    resultado = []
    for i, tok in enumerate(tokens):
        if i == 0:
            resultado.append(tok)
        else:
            prev = tokens[i-1]
            # Não adiciona espaço antes de ) ] } , ;
            if tok in ')}],;':
                resultado.append(tok)
            # Não adiciona espaço depois de ( [ {
            elif prev in '([{':
                resultado.append(tok)
            # Adiciona espaço antes de = se anterior não for (
            elif tok == '=' and prev not in '([{':
                resultado.append(' ' + tok)
            # Adiciona espaço depois de = se próximo não for string/number/(
            elif prev == '=' and tok not in '([{' and not tok.startswith('"') and not tok.startswith("'") and not tok[0].isdigit():
                resultado.append(' ' + tok)
            # Vírgula: sem espaço antes, espaço depois
            elif prev == ',':
                resultado.append(' ' + tok)
            elif tok == ',':
                resultado.append(tok)
            else:
                resultado.append(' ' + tok)
    
    texto = ''.join(resultado)
    
    # Correções finais
    texto = re.sub(r'\s+', ' ', texto)  # múltiplos espaços
    texto = re.sub(r'\(\s+', '(', texto)  # espaço após (
    texto = re.sub(r'\s+\)', ')', texto)  # espaço antes de )
    texto = re.sub(r'\{\s+', '{', texto)  # espaço após {
    texto = re.sub(r'\s+\}', '}', texto)  # espaço antes de }
    texto = re.sub(r',\s+', ', ', texto)  # vírgula + espaço
    texto = re.sub(r'=\s+', '= ', texto)  # = + espaço
    texto = re.sub(r'\s+;', ';', texto)   # ; sem espaço antes
    texto = re.sub(r';', '; ', texto)     # ; + espaço
    
    return texto.strip()

# ─── TESTES ─────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  TESTES DE GERACAO COM IDENTIDADE")
print(f"{'='*60}")

nomes_teste = ["Adrenius", "Ahmet", "Sapo Azul", "Sapo Coral"]

for nome in nomes_teste:
    print(f"\n{'─'*60}")
    print(f"  IDENTIDADE: {nome}")
    print(f"{'─'*60}")
    
    seq = gerar_com_identidade(mk, nome, 'local', passos=60)
    texto = pos_processar(seq)
    tokens_filtrados = len([t for t in seq if not t.startswith('B:')])
    
    print(f"  Tokens gerados: {len(seq)} ({tokens_filtrados} filtrados)")
    print(f"  Saida:\n    {texto[:400]}")
    
    if nome in ["Adrenius", "Ahmet"]:
        acertos = ['internalNpcName', 'Game.createNpcType', 'npcConfig', 'npcHandler',
                   'FocusModule', 'npcType:register', 'keywordHandler']
    else:
        acertos = ['Game.createMonsterType', 'monster.description', 'monster.experience',
                   'monster.health', 'monster.outfit', 'mType:register']
    
    encontrados = [p for p in acertos if p in texto]
    print(f"  Estrutura: {len(encontrados)}/{len(acertos)} acertos")
    if encontrados:
        print(f"    ✓ " + ', '.join(encontrados))

# ─── NOME NOVO ──────────────────────────────────────────
print(f"\n{'─'*60}")
print(f"  IDENTIDADE NOVA: Eldrin (fallback mk_palavra)")
print(f"{'─'*60}")

seq_eldrin = gerar_com_identidade(mk, 'Eldrin', 'local', passos=60)
texto_eldrin = pos_processar(seq_eldrin)
print(f"  Tokens: {len(seq_eldrin)}")
print(f"  Saida:\n    {texto_eldrin[:400]}")

# ─── MONSTER COMPLETO ──────────────────────────────────
print(f"\n{'─'*60}")
print(f"  MONSTER COMPLETO: Sapo Azul (120 passos)")
print(f"{'─'*60}")

seq_mon = gerar_com_identidade(mk, 'Sapo Azul', 'local', passos=120)
texto_mon = pos_processar(seq_mon)

fp = os.path.join(OUT_DIR, "monster_adapt_sapo.lua")
with open(fp, 'w', encoding='utf-8') as f:
    f.write(f"-- MCR ADAPTATIVO (SQLite) — {time.strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"-- Identidade: Sapo Azul, {len(seq_mon)} tokens\n\n")
    f.write(texto_mon + '\n')

print(f"  {len(seq_mon)} tokens -> {os.path.basename(fp)}")
for p in ['monster.description', 'monster.experience', 'monster.health', 
          'monster.outfit', 'monster.loot', 'monster.attacks', 'monster.defenses',
          'monster.elements', 'monster.flags', 'mType:register', 'Game.createMonsterType']:
    if p in texto_mon:
        idx = texto_mon.find(p)
        print(f"  ✓ {p}...{texto_mon[idx+len(p):idx+len(p)+40]}")

# ─── NPC COMPLETO ──────────────────────────────────────
print(f"\n{'─'*60}")
print(f"  NPC COMPLETO: Adrenius (120 passos)")
print(f"{'─'*60}")

seq_npc = gerar_com_identidade(mk, 'Adrenius', 'local', passos=120)
texto_npc = pos_processar(seq_npc)

fp = os.path.join(OUT_DIR, "npc_adapt_adrenius.lua")
with open(fp, 'w', encoding='utf-8') as f:
    f.write(f"-- MCR ADAPTATIVO (SQLite) — {time.strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"-- Identidade: Adrenius, {len(seq_npc)} tokens\n\n")
    f.write(texto_npc + '\n')

print(f"  {len(seq_npc)} tokens -> {os.path.basename(fp)}")
for p in ['internalNpcName', 'Game.createNpcType', 'npcConfig', 'npcHandler',
          'npcType.onThink', 'npcType.onAppear', 'FocusModule', 'npcType:register']:
    if p in texto_npc:
        idx = texto_npc.find(p)
        print(f"  ✓ {p}...{texto_npc[idx+len(p):idx+len(p)+40]}")

# ─── COMPARACAO MK_ID JSON vs SQLITE ───────────────────
print(f"\n{'─'*60}")
print(f"  COMPARACAO: JSON vs SQLITE")
print(f"{'─'*60}")

# JSON anterior
json_path = r"E:\MCR\cache\mk_id.json"
tamanho_json = os.path.getsize(json_path) / 1024 / 1024 if os.path.exists(json_path) else 0
tamanho_db = os.path.getsize(DB_PATH) / 1024 / 1024

print(f"  JSON anterior:   {tamanho_json:.0f} MB (carrega tudo na RAM)")
print(f"  SQLite atual:    {tamanho_db:.0f} MB (cache 8MB RAM)")
print(f"  Reducao RAM:    {max(0, tamanho_json - 8):.0f} MB liberados")

n_trans_json = 4364173
print(f"  JSON trans:      {n_trans_json:,}")
print(f"  SQLite trans:    {n_trans:,}")
print(f"  SQLite freq:     {n_freq:,}")

# ─── CLEANUP ────────────────────────────────────────────
mk.close()
print(f"\n{'='*60}")
print(f"  DB em: {DB_PATH}")
print(f"  OK!")
print(f"{'='*60}")
