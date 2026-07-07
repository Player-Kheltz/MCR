#!/usr/bin/env python3
"""mk_id — identidade como contexto persistente para geracao Markov.

Alimenta mk_id com `f"{nome}|{token_i}" → token_{i+1}`.
Gerador usa mk_id como primario, mk_palavra como fallback.
Compara comprimento de cadeia com/sem identidade.
"""

import sys, os, re, time, json, math, random

os.chdir(r"E:\MCR")
sys.path.insert(0, ".")
__file__ = os.path.join(os.getcwd(), "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

OUT_DIR = r"E:\MCR\nichos\tibia\gerados"
CACHE_DIR_NAME = r"E:\MCR\cache"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR_NAME, exist_ok=True)

# Carrega cerebro principal (monster data)
c = CerebroAGI()
c.carregar(os.path.join(CACHE_DIR, "cerebro.json"))
mk_palavra = c.mk_palavra
print(f"Cerebro principal: {mk_palavra.total} transicoes, {len(mk_palavra.freq)} vocab")

# ─── MK_ID ───────────────────────────────────────────────
mk_id = MCR("identidade")

def tokenizar(texto):
    """Tokeniza igual o MCR.tokenizar()."""
    tokens = []
    for palavra in texto.split():
        while palavra and palavra[-1] in ',;:!?)]}"\'': tokens.append(palavra[-1]); palavra = palavra[:-1]
        while palavra and palavra[0] in '([{"\'': tokens.append(palavra[0]); palavra = palavra[1:]
        if palavra:
            tokens.append(palavra)
    return tokens

def extrair_identidade(arquivo, texto):
    """Extrai identidade de arquivo NPC ou Monster."""
    nome = ""
    for linha in texto.split('\n'):
        linha = linha.strip()
        if 'internalNpcName' in linha or 'Game.createNpcType' in linha or 'Game.createMonsterType' in linha:
            m = re.search(r'"(.*?)"', linha)
            if m:
                nome = m.group(1).strip()
                break
    return nome or os.path.splitext(os.path.basename(arquivo))[0]

def alimentar_identidade(arquivo, nome):
    """Alimenta mk_id com identidade."""
    with open(arquivo, 'r', encoding='utf-8', errors='replace') as f:
        texto = f.read()
    tokens = tokenizar(texto)
    if len(tokens) < 5:
        return 0
    nome_limpo = re.sub(r'[^\w\s\u00C0-\u00FF-]', '', nome).strip()[:30]
    if not nome_limpo:
        return 0
    # Markov-2: f"{id}|{token_n}" → token_{n+1}
    for i in range(len(tokens)-1):
        mk_id.aprender(f"{nome_limpo}|{tokens[i]}", tokens[i+1])
    # Markov-3: f"{id}|{token_n-1}|{token_n}" → token_{n+1}
    for i in range(len(tokens)-2):
        mk_id.aprender(f"{nome_limpo}|{tokens[i]}|{tokens[i+1]}", tokens[i+2])
    return len(tokens)

# ─── ALIMENTAR NPCs ─────────────────────────────────────
RAIZ_NPC = r"E:\Projeto MCR\Canary\data-otservbr-global\npc"
t0 = time.perf_counter()
n_arqs = 0
n_tokens = 0
for raiz, dirs, files in os.walk(RAIZ_NPC):
    for f in files:
        if not f.endswith('.lua'):
            continue
        fp = os.path.join(raiz, f)
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                texto = fh.read()
            nome = extrair_identidade(fp, texto)
            tok_count = alimentar_identidade(fp, nome)
            if tok_count:
                n_arqs += 1
                n_tokens += tok_count
        except: pass

t1 = time.perf_counter()
print(f"NPCs alimentados: {n_arqs} arquivos, {n_tokens} tokens em {t1-t0:.1f}s")
print(f"mk_id: {mk_id.total} transicoes, {len(mk_id.freq)} estados")

# ─── ALIMENTAR MONSTROS ─────────────────────────────────
RAIZ_MON = r"E:\Projeto MCR\Canary\data-otservbr-global\monster"
t0 = time.perf_counter()
n_arqs_m = 0
n_tokens_m = 0
for raiz, dirs, files in os.walk(RAIZ_MON):
    for f in files:
        if not f.endswith('.lua'):
            continue
        fp = os.path.join(raiz, f)
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                texto = fh.read()
            nome = extrair_identidade(fp, texto)
            tok_count = alimentar_identidade(fp, nome)
            if tok_count:
                n_arqs_m += 1
                n_tokens_m += tok_count
        except: pass

t1 = time.perf_counter()
total_arqs = n_arqs + n_arqs_m
print(f"Monstros alimentados: {n_arqs_m} arquivos, {n_tokens_m} tokens em {t1-t0:.1f}s")
print(f"mk_id total: {mk_id.total} transicoes, {len(mk_id.freq)} estados")
print(f"Total de entidades: {total_arqs}")

# Salva mk_id
mk_id_path = os.path.join(CACHE_DIR_NAME, "mk_id.json")
dados_id = {
    'transicoes': {str(k): {str(kk): vv for kk, vv in v.items()} for k, v in mk_id.transicoes.items()},
    'freq': {str(k): v for k, v in mk_id.freq.items()},
    'total': mk_id.total,
}
with open(mk_id_path, 'w', encoding='utf-8') as f:
    json.dump(dados_id, f)
print(f"\nmk_id salvo em: {mk_id_path} ({os.path.getsize(mk_id_path)/1024:.0f} KB)")

# ─── TESTE: GERACAO COM IDENTIDADE ──────────────────────
print(f"\n{'='*60}")
print(f"  TESTE: GERACAO COM vs SEM IDENTIDADE")
print(f"{'='*60}")

def gerar_com_identidade(mk_id, mk_palavra, identity, seed, passos=120):
    """Gera usando mk_id (Markov-2/3 c/ identidade) + mk_palavra (entropico).
    
    Estrategia:
      1. mk_id Markov-3: f"{id}|{a}|{b}" → c (se existir)
      2. mk_id Markov-2: f"{id}|{b}" → c (se existir)
      3. mk_palavra: predizer_com_entropia(b) (fallback)
    """
    seq = [seed]
    for _ in range(passos):
        b = seq[-1]
        pred, conf = None, 0.0
        
        # 1. mk_id Markov-3
        if len(seq) >= 2:
            a = seq[-2]
            chave_m3 = f"{identity}|{a}|{b}"
            if chave_m3 in mk_id.transicoes and mk_id.transicoes[chave_m3]:
                pred, conf = mk_id.predizer(chave_m3)
        
        # 2. mk_id Markov-2
        if pred is None:
            chave_m2 = f"{identity}|{b}"
            if chave_m2 in mk_id.transicoes and mk_id.transicoes[chave_m2]:
                pred, conf = mk_id.predizer(chave_m2)
        
        # 3. mk_palavra fallback
        if pred is None:
            pred, conf = mk_palavra.predizer_com_entropia(b)
        
        if pred is None or conf < 0.01:
            break
        if len(seq) >= 3 and all(t == pred for t in seq[-3:]):
            break
        seq.append(pred)
    return seq

def gerar_sem_identidade(mk_palavra, seed, passos=60):
    """Gera usando apenas mk_palavra."""
    seq = [seed]
    for _ in range(passos):
        pred, conf = mk_palavra.predizer_com_entropia(seq[-1])
        if pred is None or conf < 0.01:
            break
        if len(seq) >= 3 and all(t == pred for t in seq[-3:]):
            break
        seq.append(pred)
    return seq

def limpar_tokens(seq):
    return [t for t in seq if not t.startswith('B:') and t != '<UNK>' and len(t) < 80]

# Nomes conhecidos do treino
nomes_teste = []
# Pega nomes do proprio mk_id (amostra)
count = 0
for chave in mk_id.transicoes:
    ident = chave.split('|')[0]
    if ident and ident not in nomes_teste and len(ident) > 2:
        nomes_teste.append(ident)
        count += 1
        if count >= 6:
            break

print(f"\n  Nomes de teste: {nomes_teste}")

for nome in nomes_teste:
    print(f"\n{'─'*60}")
    print(f"  IDENTIDADE: {nome}")
    print(f"{'─'*60}")
    
    # Verifica se existe no mk_id
    chaves_encontradas = []
    for chave in mk_id.transicoes:
        if chave.startswith(f"{nome}|"):
            chaves_encontradas.append(chave)
    print(f"  Chaves mk_id: {len(chaves_encontradas)}")
    
    # Gera com identidade
    seq_id = gerar_com_identidade(mk_id, mk_palavra, nome, 'local', passos=60)
    tokens_id = limpar_tokens(seq_id)
    texto_id = ' '.join(tokens_id)
    
    # Gera sem identidade
    seq_sem = gerar_sem_identidade(mk_palavra, 'local', passos=60)
    tokens_sem = limpar_tokens(seq_sem)
    texto_sem = ' '.join(tokens_sem)
    
    print(f"  COM identidade:  {len(tokens_id)} tokens")
    print(f"  SEM identidade:  {len(tokens_sem)} tokens")
    print(f"  Diferenca: +{len(tokens_id)-len(tokens_sem)} tokens")
    print(f"\n  COM:\n    {texto_id[:200]}")
    print(f"\n  SEM:\n    {texto_sem[:200]}")

# ─── NOME NOVO (nao existente no treino) ────────────────
print(f"\n{'─'*60}")
print(f"  IDENTIDADE NOVA: Eldrin (nao existe no treino)")
print(f"{'─'*60}")

seq_eldrin_id = gerar_com_identidade(mk_id, mk_palavra, "Eldrin", 'local', passos=60)
tokens_eldrin = limpar_tokens(seq_eldrin_id)
texto_eldrin = ' '.join(tokens_eldrin)
print(f"  COM (fallback): {len(tokens_eldrin)} tokens")
print(f"  {texto_eldrin[:200]}")

# ─── GERAR NPC COMPLETO ─────────────────────────────────
print(f"\n{'─'*60}")
print(f"  GERANDO NPC COMPLETO via IDENTIDADE")
print(f"{'─'*60}")

nome_npc = "Ahmet"  # NPC conhecido
seq_completo = gerar_com_identidade(mk_id, mk_palavra, nome_npc, 'local', passos=120)
tokens_limpos = limpar_tokens(seq_completo)
texto_completo = ' '.join(tokens_limpos)

fp = os.path.join(OUT_DIR, "npc_mkid_ahmet.lua")
with open(fp, 'w', encoding='utf-8') as f:
    f.write(f"-- GERADO VIA mk_id (identidade={nome_npc}, {len(tokens_limpos)} tokens)\n")
    f.write(f"-- {time.strftime('%Y-%m-%d %H:%M')}\n\n")
    for i in range(0, len(tokens_limpos), 10):
        f.write(' '.join(tokens_limpos[i:i+10]) + '\n')

print(f"  {len(tokens_limpos)} tokens gerados")
print(f"  Salvo: {fp}")
print(f"  Amostra:\n    {' '.join(tokens_limpos[:30])}")

# ─── MONSTER ─────────────────────────────────────────────
print(f"\n{'─'*60}")
print(f"  GERANDO MONSTER COMPLETO via IDENTIDADE")
print(f"{'─'*60}")

nome_mon = "Sapo Azul"
seq_mon = gerar_com_identidade(mk_id, mk_palavra, nome_mon, 'local', passos=120)
tokens_mon = limpar_tokens(seq_mon)

fp = os.path.join(OUT_DIR, "monster_mkid_sapo.lua")
with open(fp, 'w', encoding='utf-8') as f:
    f.write(f"-- GERADO VIA mk_id (identidade={nome_mon}, {len(tokens_mon)} tokens)\n")
    f.write(f"-- {time.strftime('%Y-%m-%d %H:%M')}\n\n")
    for i in range(0, len(tokens_mon), 10):
        f.write(' '.join(tokens_mon[i:i+10]) + '\n')

print(f"  {len(tokens_mon)} tokens gerados")
print(f"  Salvo: {fp}")
print(f"  Amostra:\n    {' '.join(tokens_mon[:30])}")

# ─── RESUMO ─────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  RESUMO")
print(f"{'='*60}")
print(f"  NPCs no mk_id: {n_arqs}")
print(f"  Monstros no mk_id: {n_arqs_m}")
print(f"  Transicoes mk_id: {mk_id.total}")
print(f"  Estados mk_id: {len(mk_id.freq)}")
print(f"  Melhoria media de tokens: +{len(tokens_id)-len(tokens_sem) if 'tokens_id' in dir() else '?'}")
print(f"  Arquivo: {mk_id_path}")
print(f"{'='*60}")
