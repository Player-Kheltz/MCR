#!/usr/bin/env python3
"""
MCR MetaObserver v2 — Prova de Conceito REFINADA
==================================================
Versao 2 baseada nos aprendizados da v1:
  - Usa MCRMotor (byte + palavra + token) em vez de MCR puro
  - Feed de mensagens REAIS dos commits, nao tokens artificiais
  - Sobrevivencia: verifica se commit foi revertido/corrigido
  - Assinatura: fingerprint das mensagens, nao dimensionalidade artificial
  - Deteccao de padroes: MCR conecta commits similares, nao preve individualmente

4 Provas:
  1. CONEXAO: MCR conecta commits que deram certo vs errado?
  2. ASSINATURA: Fingerprint distingue fases reais?
  3. PADRAO: Ha ciclos de "feat → fix → feat → fix"?
  4. AUTO-SIMILARIDADE: O projeto e consistente na propria trajetoria?
"""
import sys, os, json, subprocess, math, random, re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from MCR import MCR, MCRMotor, MCRByteUtils, MCRSignatureExpansiva, MCREntropia
from MCR import MCRConexao

REPO_PATH = r"E:\Projeto MCR"
OUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'cache', 'meta_observer_v2_resultados.json')

def git(cmd: str) -> str:
    return subprocess.check_output(cmd, shell=True, cwd=REPO_PATH, encoding='utf-8', errors='replace')

def extrair_commits() -> List[Dict]:
    """Extrai commits com mensagens COMPLETAS."""
    log = git('git log --all --format="HASH:%H|AUTHOR:%an|DATE:%ai|MSG:%s" --shortstat')
    commits_raw = []
    current = {}
    for line in log.strip().split('\n'):
        line = line.strip()
        if line.startswith('HASH:'):
            if current:
                commits_raw.append(current)
            parts = line.split('|')
            msg = parts[3].replace('MSG:', '', 1) if len(parts) > 3 else ''
            current = {
                'hash': parts[0].replace('HASH:', ''),
                'author': parts[1].replace('AUTHOR:', ''),
                'date': parts[2].replace('DATE:', ''),
                'msg': msg,
                'files_changed': 0, 'lines_added': 0, 'lines_deleted': 0,
            }
        elif 'file' in line or 'files' in line:
            m = re.search(r'(\d+) files? changed', line)
            if m: current['files_changed'] = int(m.group(1))
            m = re.search(r'(\d+) insertions?\(\+\)', line)
            if m: current['lines_added'] = int(m.group(1))
            m = re.search(r'(\d+) deletions?\(-\)', line)
            if m: current['lines_deleted'] = int(m.group(1))
    if current:
        commits_raw.append(current)
    print(f"  Extraidos {len(commits_raw)} commits")
    return commits_raw

def detectar_tipo(msg: str) -> str:
    msg_lower = msg.lower()
    if msg_lower.startswith('feat') or 'feat:' in msg_lower:
        return 'feat'
    if msg_lower.startswith('fix') or 'fix:' in msg_lower:
        return 'fix'
    if msg_lower.startswith('refactor') or 'refactor:' in msg_lower:
        return 'refactor'
    if msg_lower.startswith('docs') or 'docs:' in msg_lower:
        return 'docs'
    if msg_lower.startswith('test') or 'teste:' in msg_lower:
        return 'test'
    if msg_lower.startswith('chore') or 'chore:' in msg_lower:
        return 'chore'
    return 'other'

def verificar_reversao(commits, max_lookahead=20):
    """Verifica se commit foi revertido por commits futuros."""
    commits_dict = {c['hash']: c for c in commits}
    for i, c in enumerate(commits):
        c['revertido'] = False
        # Olha ate max_lookahead commits a frente
        for j in range(i + 1, min(len(commits), i + max_lookahead)):
            futuro = commits[j]
            # Se o commit futuro menciona explicitamente o hash
            if c['hash'][:8] in futuro['msg'] or c['hash'] in futuro['msg']:
                c['revertido'] = True
                break
            # Se e um fix do mesmo escopo (mesmo tipo de arquivo)
            if 'revert' in futuro['msg'].lower() and detectar_tipo(futuro['msg']) == 'fix':
                # Verifica se tocam os mesmos arquivos
                if c.get('files_changed', 0) > 0 and futuro.get('files_changed', 0) > 0:
                    if abs(c['files_changed'] - futuro['files_changed']) <= 2:
                        c['revertido'] = True
                        break

def detectar_fases_data(commits):
    """Detecta fases baseado nas DATAS reais e marcos do projeto."""
    # Marcos conhecidos do projeto
    marcos = {
        '06-19': 'spa',           # SPA inicial
        '06-24': 'mcr_devia',     # MCR-DevIA
        '06-28': 'agi_hibrido',   # AGI hibrido com LLM
        '06-30': 'mcr_puro_inicio', # MCR.py unificado
        '07-01': 'mcr_puro',      # MCR.py como centro
    }
    for c in commits:
        data = c['date'][5:10]  # MM-DD
        fase_encontrada = 'inicio'
        for marco_data, nome_fase in sorted(marcos.items()):
            if data >= marco_data:
                fase_encontrada = nome_fase
        c['fase'] = fase_encontrada

def alimentar_commits_no_motor(commits, motor):
    """Alimenta mensagens de commits no MCRMotor."""
    for c in commits:
        # Texto completo do commit para aprendizado multi-nivel
        texto = f"{c['author']} {c['msg']} tipo:{detectar_tipo(c['msg'])} fase:{c.get('fase', '?')}"
        if c.get('revertido'):
            texto += " REVERTIDO"
        else:
            texto += " OK"
        motor.alimentar(texto, f"commit:{c['hash'][:8]}")

def analisar_sequencia_tipos(commits):
    """Analisa a sequencia de tipos de commit."""
    mk = MCR("tipos_commits")
    tipos = [detectar_tipo(c['msg']) for c in commits]
    
    # Alimenta bigramas de tipos
    for i in range(len(tipos) - 1):
        mk.aprender(tipos[i], tipos[i + 1])
    
    # Encontra padroes de 3-gramas mais comuns
    trigramas = Counter()
    for i in range(len(tipos) - 2):
        trigramas[f"{tipos[i]} -> {tipos[i+1]} -> {tipos[i+2]}"] += 1
    
    # Detecta ciclos: feat -> fix -> feat -> fix
    ciclos = mk.entropia('fix' if 'fix' in mk.freq else 'feat')
    # Se a entropia e baixa, ha pouca variacao = ciclo
    
    return {
        'mk': mk,
        'tipos': tipos,
        'trigramas_mais_comuns': trigramas.most_common(10),
        'transicoes_mais_provaveis': [
            {'de': t, 'para': mk.predizer(t)[0], 'conf': round(mk.predizer(t)[1], 3)}
            for t in sorted(set(tipos)) if mk.predizer(t)[0]
        ],
    }

# ─── PROVA 1: CONEXAO ENTRE COMMITS SIMILARES ────────────────

def prova_conexao(commits):
    """MCR consegue conectar commits que deram certo vs errado?"""
    print("\n" + "=" * 60)
    print("PROVA 1: CONEXAO — MCR conecta commits similares?")
    print("=" * 60)
    
    motor = MCRMotor()
    
    # Separa commits bem-sucedidos (nao revertidos) e mal-sucedidos (revertidos)
    bons = [c for c in commits if not c.get('revertido')]
    ruins = [c for c in commits if c.get('revertido')]
    
    print(f"  Commits OK: {len(bons)}")
    print(f"  Commits REVERTIDOS: {len(ruins)}")
    
    if len(ruins) < 2:
        print("  Poucos commits revertidos para conectar.")
        return {'prova': 'conexao', 'status': 'dados_insuficientes'}
    
    # Alimenta bons e ruins como topicos separados
    for c in bons[:50]:
        motor.alimentar(c['msg'], f"ok:{c['hash'][:8]}")
    for c in ruins[:20]:
        motor.alimentar(c['msg'], f"ruim:{c['hash'][:8]}")
    
    # Tenta conectar ruins entre si
    conexoes_ruins = []
    hashes_ruins = [f"ruim:{c['hash'][:8]}" for c in ruins[:10]]
    for i in range(min(10, len(hashes_ruins))):
        for j in range(i + 1, min(10, len(hashes_ruins))):
            try:
                conn = motor.conectar(hashes_ruins[i], hashes_ruins[j])
                if conn and conn.get('nota', 0) > 0:
                    conexoes_ruins.append((hashes_ruins[i], hashes_ruins[j], conn['nota']))
            except:
                pass
    
    print(f"  Conexoes entre commits RUINS: {len(conexoes_ruins)}")
    
    # Tenta conectar bons entre si para comparacao
    hashes_bons = [f"ok:{c['hash'][:8]}" for c in bons[:50]]
    conexoes_bons = 0
    total_pares = 0
    for i in range(min(30, len(hashes_bons))):
        for j in range(i + 1, min(30, len(hashes_bons))):
            try:
                conn = motor.conectar(hashes_bons[i], hashes_bons[j])
                if conn and conn.get('nota', 0) > 0:
                    conexoes_bons += 1
                total_pares += 1
            except:
                pass
    
    densidade_bons = conexoes_bons / max(total_pares, 1)
    densidade_ruins = len(conexoes_ruins) / max(len(hashes_ruins) * (len(hashes_ruins) - 1) / 2, 1)
    
    print(f"  Densidade de conexoes BONS: {densidade_bons:.2%}")
    print(f"  Densidade de conexoes RUINS: {densidade_ruins:.2%}")
    
    if densidade_ruins > densidade_bons * 2:
        print("  RESULTADO: Commits ruins sao MAIS conectados entre si — ha padrao!")
        conclusao = "ha_padrao"
    elif densidade_bons > densidade_ruins * 2:
        print("  RESULTADO: Commits bons sao MAIS conectados entre si — ha padrao!")
        conclusao = "ha_padrao_ok"
    else:
        print("  RESULTADO: Nao ha diferenca significativa nas conexoes.")
        conclusao = "sem_diferenca"
    
    return {
        'prova': 'conexao',
        'bons': len(bons),
        'ruins': len(ruins),
        'densidade_bons': round(densidade_bons, 4),
        'densidade_ruins': round(densidade_ruins, 4),
        'conexoes_ruins': len(conexoes_ruins),
        'conclusao': conclusao,
    }

# ─── PROVA 2: FINGERPRINT DAS FASES ──────────────────────────

def prova_assinatura_fases(commits):
    """Fingerprint da mensagem dos commits por fase."""
    print("\n" + "=" * 60)
    print("PROVA 2: ASSINATURA — Fingerprint distingue fases?")
    print("=" * 60)
    
    fases = defaultdict(list)
    for c in commits:
        fases[c.get('fase', '?')].append(c)
    
    if not fases or len(fases) < 2:
        print("  Menos de 2 fases detectadas.")
        return {'prova': 'assinatura_fases', 'status': 'dados_insuficientes'}
    
    fingerprints = {}
    for nome, fase_commits in sorted(fases.items()):
        if len(fase_commits) < 3:
            continue
        # Texto consolidado da fase: mensagens concatenadas
        texto = ' '.join([c['msg'][:100] for c in fase_commits[:50]])
        fp = MCRByteUtils.fingerprint(texto, 16)
        h = MCRByteUtils.entropia_bytes(texto)
        fingerprints[nome] = {
            'commits': len(fase_commits),
            'fingerprint': fp,
            'entropia': round(h, 3),
        }
        print(f"  {nome:20s}: {len(fase_commits):3d} commits, H={h:.2f}, fp={[round(f,1) for f in fp[:4]]}...")
    
    # Similaridade entre fases consecutivas
    fases_ordenadas = sorted(fingerprints.keys())
    similaridades = []
    for i in range(len(fases_ordenadas) - 1):
        a, b = fases_ordenadas[i], fases_ordenadas[i + 1]
        fp_a = fingerprints[a]['fingerprint']
        fp_b = fingerprints[b]['fingerprint']
        sim = MCRSignatureExpansiva.similaridade(fp_a, fp_b)
        similaridades.append({'de': a, 'para': b, 'similaridade': round(sim, 3)})
        print(f"  Similaridade {a} -> {b}: {sim:.3f}")
    
    # Se a similaridade entre fases consecutivas > 0.8, as fases sao indistinguiveis
    # Se < 0.5, ha clara distincao
    similaridade_media = sum(s['similaridade'] for s in similaridades) / max(len(similaridades), 1)
    
    if similaridade_media < 0.5:
        print(f"\n  RESULTADO: Fases DISTINGUIVEIS (sim_media={similaridade_media:.3f})")
        conclusao = "fases_distinguiveis"
    elif similaridade_media < 0.8:
        print(f"\n  RESULTADO: Fases PARCIALMENTE DISTINGUIVEIS (sim_media={similaridade_media:.3f})")
        conclusao = "fases_parciais"
    else:
        print(f"\n  RESULTADO: Fases INDISTINGUIVEIS (sim_media={similaridade_media:.3f})")
        conclusao = "fases_indistinguiveis"
    
    return {
        'prova': 'assinatura_fases',
        'fases': fingerprints,
        'similaridades': similaridades,
        'similaridade_media': round(similaridade_media, 3),
        'conclusao': conclusao,
    }

# ─── PROVA 3: CICLOS NA SEQUENCIA ────────────────────────────

def prova_padroes_temporais(commits):
    """Detecta padroes temporais na sequencia de commits."""
    print("\n" + "=" * 60)
    print("PROVA 3: PADROES — Ha ciclos na sequencia?")
    print("=" * 60)
    
    # Analisa sequencia de tipos
    result_tipos = analisar_sequencia_tipos(commits)
    mk = result_tipos['mk']
    tipos = result_tipos['tipos']
    
    print(f"  Sequencia de {len(tipos)} commits")
    print(f"  Top 10 trigramas:")
    for t, count in result_tipos['trigramas_mais_comuns'][:10]:
        print(f"    {t}: {count}x")
    
    print(f"  Transicoes mais provaveis:")
    for t in result_tipos['transicoes_mais_provaveis']:
        print(f"    {t['de']} -> {t['para']} (conf={t['conf']})")
    
    # Entropia media da sequencia — baixa = repetitivo (ciclo)
    entropias = []
    for i in range(5, len(tipos)):
        janela = tipos[i-5:i]
        freq = Counter(janela)
        h = -sum((c/5) * math.log2(c/5) for c in freq.values())
        entropias.append(h)
    
    h_media = sum(entropias) / max(len(entropias), 1) if entropias else 0
    h_min = min(entropias) if entropias else 0
    h_max = max(entropias) if entropias else 0
    
    print(f"  Entropia da sequencia: media={h_media:.2f}, min={h_min:.2f}, max={h_max:.2f}")
    
    # Se h_media < 1.5, a sequencia e muito repetitiva (ciclo)
    # Se h_media > 2.5, e diversa
    if h_media < 1.5:
        print(f"  RESULTADO: Sequencia REPETITIVA (H={h_media:.2f}) — possivel ciclo")
        conclusao = "sequencia_repetitiva"
    elif h_media < 2.5:
        print(f"  RESULTADO: Sequencia MODERADA (H={h_media:.2f})")
        conclusao = "sequencia_moderada"
    else:
        print(f"  RESULTADO: Sequencia DIVERSA (H={h_media:.2f})")
        conclusao = "sequencia_diversa"
    
    return {
        'prova': 'padroes_temporais',
        'total_commits': len(tipos),
        'entropia_media': round(h_media, 3),
        'entropia_min': round(h_min, 3),
        'entropia_max': round(h_max, 3),
        'trigramas': result_tipos['trigramas_mais_comuns'],
        'transicoes': result_tipos['transicoes_mais_provaveis'],
        'conclusao': conclusao,
    }

# ─── PROVA 4: AUTO-SIMILARIDADE DO PROJETO ───────────────────

def prova_auto_similaridade(commits):
    """O projeto e consistente na propria trajetoria?"""
    print("\n" + "=" * 60)
    print("PROVA 4: AUTO-SIMILARIDADE — Consistencia interna do projeto")
    print("=" * 60)
    
    # Divide em 2 metades: inicio e fim do projeto
    meio = len(commits) // 2
    inicio = commits[:meio]
    fim = commits[meio:]
    
    # Texto consolidado de cada metade
    texto_inicio = ' '.join([c['msg'][:80] for c in inicio[:100]])
    texto_fim = ' '.join([c['msg'][:80] for c in fim[:100]])
    
    # Similaridade entre inicio e fim
    j = MCRByteUtils.jaccard_bytes(texto_inicio, texto_fim)
    fp_i = MCRByteUtils.fingerprint(texto_inicio, 16)
    fp_f = MCRByteUtils.fingerprint(texto_fim, 16)
    cos = MCRSignatureExpansiva.similaridade(fp_i, fp_f)
    h_i = MCRByteUtils.entropia_bytes(texto_inicio)
    h_f = MCRByteUtils.entropia_bytes(texto_fim)
    
    print(f"  Inicio do projeto: {len(inicio)} commits, H={h_i:.2f}")
    print(f"  Fim do projeto:    {len(fim)} commits, H={h_f:.2f}")
    print(f"  Jaccard (byte):    {j:.3f}")
    print(f"  Cosseno (fp):      {cos:.3f}")
    
    # Se jaccard > 0.2 e cosseno > 0.6, o projeto e auto-consistente
    if j > 0.2 and cos > 0.6:
        print(f"  RESULTADO: Projeto AUTO-CONSISTENTE (j={j:.3f}, cos={cos:.3f})")
        conclusao = "auto_consistente"
    elif j > 0.1 and cos > 0.4:
        print(f"  RESULTADO: Projeto PARCIALMENTE CONSISTENTE (j={j:.3f}, cos={cos:.3f})")
        conclusao = "parcialmente_consistente"
    else:
        print(f"  RESULTADO: Projeto DIVERGENTE (j={j:.3f}, cos={cos:.3f})")
        conclusao = "divergente"
    
    # Diagnostico: qual fase tem a identidade mais forte?
    fases = defaultdict(list)
    for c in commits:
        fases[c.get('fase', '?')].append(c)
    
    fp_global = MCRByteUtils.fingerprint(texto_inicio + ' ' + texto_fim, 16)
    identidade_fases = {}
    for nome, fase_commits in fases.items():
        if len(fase_commits) < 3: continue
        texto_fase = ' '.join([c['msg'][:80] for c in fase_commits[:50]])
        fp_fase = MCRByteUtils.fingerprint(texto_fase, 16)
        sim = MCRSignatureExpansiva.similaridade(fp_fase, fp_global)
        identidade_fases[nome] = round(sim, 3)
    
    mais_identitaria = max(identidade_fases, key=identidade_fases.get) if identidade_fases else '?'
    print(f"  Fase mais identitaria: {mais_identitaria} (sim={identidade_fases.get(mais_identitaria, 0):.3f})")
    
    return {
        'prova': 'auto_similaridade',
        'commits_inicio': len(inicio),
        'commits_fim': len(fim),
        'jaccard': round(j, 3),
        'cosseno': round(cos, 3),
        'entropia_inicio': round(h_i, 3),
        'entropia_fim': round(h_f, 3),
        'identidade_fases': identidade_fases,
        'fase_mais_identitaria': mais_identitaria,
        'conclusao': conclusao,
    }

# ─── MAIN ──────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  MCR MetaObserver v2")
    print("  Provas refinadas apos licoes da v1")
    print("=" * 60)
    
    commits = extrair_commits()
    verificar_reversao(commits)
    detectar_fases_data(commits)
    
    revertidos = sum(1 for c in commits if c.get('revertido'))
    print(f"\n  Revertidos/corrigidos: {revertidos}")
    
    r1 = prova_conexao(commits)
    r2 = prova_assinatura_fases(commits)
    r3 = prova_padroes_temporais(commits)
    r4 = prova_auto_similaridade(commits)
    
    resultados = {'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4}
    
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("  RESUMO FINAL")
    print("=" * 60)
    for nome, r in [('Prova 1 — Conexao', r1), ('Prova 2 — Assinatura', r2),
                     ('Prova 3 — Padroes', r3), ('Prova 4 — Auto-similaridade', r4)]:
        conclusao = r.get('conclusao', r.get('status', '?'))
        print(f"  {nome}: {conclusao}")

if __name__ == '__main__':
    main()
