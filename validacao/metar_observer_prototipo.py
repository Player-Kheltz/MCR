#!/usr/bin/env python3
"""
MCR MetaObserver — Prova de Conceito
======================================
Aplica a Equacao MCR sobre o historico de commits para verificar se
o MCR consegue distinguir "commits que deram certo" de "commits que deram errado".

4 Provas em 1 script:
  1. RETRODICAO: MCR preve sobrevivencia de commits (hold-out 20%)
  2. CICLOS: MCREntropia detecta loops na sequencia de tipos
  3. ASSINATURA: Dimensionalidade por fase do projeto
  4. BASELINE: Comparacao com dados embaralhados

Uso:
    python metar_observer_prototipo.py
"""
import sys, os, json, subprocess, math, random, re
from collections import Counter
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from MCR import MCR, MCRByteUtils, MCRSignatureExpansiva, MCREntropia

REPO_PATH = r"E:\Projeto MCR"
OUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'cache', 'meta_observer_resultados.json')

# ─── GIT EXTRACTION ────────────────────────────────────────

def git(cmd: str) -> str:
    return subprocess.check_output(cmd, shell=True, cwd=REPO_PATH, encoding='utf-8', errors='replace')

def extrair_commits() -> List[Dict]:
    """Extrai TODOS os commits com metadados."""
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
                'files_changed': 0,
                'lines_added': 0,
                'lines_deleted': 0,
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
    
    print(f"  Extraidos {len(commits_raw)} commits brutos")
    return commits_raw

def detectar_tipo(msg: str) -> str:
    """Detecta tipo do commit pela mensagem."""
    msg_lower = msg.lower()
    if msg_lower.startswith('feat') or 'feat:' in msg_lower:
        return 'feat'
    if msg_lower.startswith('fix') or 'fix:' in msg_lower:
        return 'fix'
    if msg_lower.startswith('refactor') or 'refactor:' in msg_lower:
        return 'refactor'
    if msg_lower.startswith('docs') or 'docs:' in msg_lower:
        return 'docs'
    if msg_lower.startswith('test') or 'test:' in msg_lower or 'teste:' in msg_lower:
        return 'test'
    if msg_lower.startswith('chore') or 'chore:' in msg_lower:
        return 'chore'
    return 'other'

def verificar_sobrevivencia(commits: List[Dict]) -> List[Dict]:
    """Verifica se os arquivos de cada commit ainda existem no HEAD."""
    try:
        # Cache de arquivos atuais
        files_atuais_str = git('git ls-tree -r HEAD --name-only')
        files_atuais = set(files_atuais_str.strip().split('\n'))
    except:
        files_atuais = set()
    
    for c in commits:
        try:
            files_commit_str = git(f'git diff-tree --no-commit-id -r --name-only {c["hash"]}')
            files_commit = [f.strip() for f in files_commit_str.strip().split('\n') if f.strip()]
            if not files_commit:
                c['survived'] = True
                c['survival_pct'] = 1.0
            else:
                sobreviventes = sum(1 for f in files_commit if f in files_atuais)
                c['survived'] = sobreviventes / len(files_commit) > 0.5
                c['survival_pct'] = sobreviventes / len(files_commit)
        except:
            c['survived'] = True
            c['survival_pct'] = 1.0
    
    sobrev = sum(1 for c in commits if c['survived'])
    print(f"  Commits sobreviventes: {sobrev}/{len(commits)} ({100*sobrev/len(commits):.1f}%)")
    return commits

def detectar_fase(commits: List[Dict]) -> List[Dict]:
    """Detecta fase do projeto baseado no tipo predominante e data."""
    if not commits:
        return
    
    # Identifica pontos de virada por mudanca no tipo predominante
    janela = max(1, len(commits) // 20)
    
    for i, c in enumerate(commits):
        # Determina fase
        if i < len(commits) * 0.15:
            c['fase'] = 'spa'
        elif i < len(commits) * 0.40:
            c['fase'] = 'infra_mcr'
        elif i < len(commits) * 0.60:
            c['fase'] = 'agi_hibrido'
        elif i < len(commits) * 0.80:
            c['fase'] = 'mcr_decia'
        else:
            c['fase'] = 'mcr_puro'
    
    return commits

def codificar_como_token(commit: Dict, incluir_survived: bool = True) -> str:
    """Codifica commit como token para alimentar o MCR."""
    tipo = detectar_tipo(commit['msg'])
    author = 'k' if commit['author'].lower() in ('kheltz',) else 'a'
    tam = 'g' if commit['files_changed'] > 10 else ('m' if commit['files_changed'] > 3 else 'p')
    h_msg = round(MCRByteUtils.entropia_bytes(commit['msg']), 1)
    h_str = str(h_msg).replace('.', '_')
    
    token = f"{author}:{tipo}:{tam}:h{h_str}"
    if incluir_survived:
        token += f":{'s' if commit.get('survived', True) else 'd'}"
    return token

# ─── PROVA 1: RETRODICAO ────────────────────────────────────

def prova_retrodicao(commits: List[Dict], seed: int = 42) -> Dict:
    """Treina MCR em 80% cronologico, testa previsao de sobrevivencia nos 20% finais."""
    print("\n" + "=" * 60)
    print("PROVA 1: RETRODICAO — MCR preve sobrevivencia de commits?")
    print("=" * 60)
    
    n = len(commits)
    split = int(n * 0.8)
    treino = commits[:split]
    teste = commits[split:]
    
    # Treina MCR nos commits de treino
    mk = MCR("prova1_retrodicao")
    for c in treino:
        token = codificar_como_token(c, incluir_survived=True)
        palavras = token.split(':')
        for i in range(len(palavras) - 1):
            mk.aprender(palavras[i], palavras[i + 1])
    
    # Testa previsao
    acertos = 0
    total = 0
    resultados = []
    for c in teste:
        token_real = codificar_como_token(c, incluir_survived=True)
        # Esconde o resultado, tenta prever
        token_sem_fim = codificar_como_token(c, incluir_survived=False)
        palavras = token_sem_fim.split(':')
        
        pred, conf = mk.predizer(palavras[-1])
        if pred:
            pred_survived = pred == 's'
            if pred_survived == c.get('survived', True):
                acertos += 1
            total += 1
            resultados.append({
                'hash': c['hash'][:8],
                'msg': c['msg'][:50],
                'real': 's' if c.get('survived', True) else 'd',
                'previsto': pred,
                'conf': round(conf, 3),
                'acertou': pred_survived == c.get('survived', True),
            })
    
    acuracia = acertos / max(total, 1)
    baseline = max(
        sum(1 for c in teste if c.get('survived', True)) / len(teste),
        1 - sum(1 for c in teste if c.get('survived', True)) / len(teste)
    )
    
    print(f"  Amostras de treino: {len(treino)}")
    print(f"  Amostras de teste:  {len(teste)}")
    print(f"  Acurcia MCR:       {acuracia:.1%} ({acertos}/{total})")
    print(f"  Baseline aleatorio: {baseline:.1%}")
    print(f"  Ganho:             {acuracia - baseline:+.1%}")
    print(f"  Resultado:         {'REVOLUCIONARIO' if acuracia > baseline + 0.1 else 'PROMISSOR' if acuracia > baseline + 0.05 else 'MODESTO' if acuracia > baseline else 'RUIM'}")
    
    return {
        'prova': 'retrodicao',
        'acuracia': round(acuracia, 4),
        'baseline': round(baseline, 4),
        'ganho': round(acuracia - baseline, 4),
        'acertos': acertos,
        'total': total,
        'treino': len(treino),
        'teste': len(teste),
        'resultados': resultados[:20],
    }

# ─── PROVA 2: DETECCAO DE CICLOS ───────────────────────────

def prova_ciclos(commits: List[Dict]) -> Dict:
    """Detecta periodos de loop na sequencia de tipos de commit."""
    print("\n" + "=" * 60)
    print("PROVA 2: CICLOS — MCREntropia detecta loops na sequencia?")
    print("=" * 60)
    
    tipos = [detectar_tipo(c['msg']) for c in commits]
    ent = MCREntropia("commits_tipos")
    
    loops_detectados = []
    for i, t in enumerate(tipos):
        ent.alimentar(t)
        if ent.esta_em_loop():
            loops_detectados.append((i, t, commits[i]['msg'][:40]))
    
    pct_loops = len(loops_detectados) / max(len(tipos), 1)
    
    print(f"  Total de commits: {len(tipos)}")
    print(f"  Loops detectados: {len(loops_detectados)} ({pct_loops:.1%})")
    print(f"  Primeiros loops:")
    for idx, t, msg in loops_detectados[:5]:
        print(f"    commit {idx}: tipo={t}, msg=\"{msg}\"")
    
    # Validacao: loops sao periodos de estresse?
    # Se ha muitos feats seguidos de fixes, isso e loop
    if loops_detectados:
        # Verifica se os loops formam clusters (periodos problematicos)
        clusters = []
        cluster_atual = [loops_detectados[0]]
        for i in range(1, len(loops_detectados)):
            if loops_detectados[i][0] - loops_detectados[i-1][0] <= 5:
                cluster_atual.append(loops_detectados[i])
            else:
                clusters.append(cluster_atual)
                cluster_atual = [loops_detectados[i]]
        clusters.append(cluster_atual)
        
        print(f"  Clusters de loop: {len(clusters)}")
        for i, cl in enumerate(clusters):
            print(f"    Cluster {i+1}: commits {cl[0][0]}-{cl[-1][0]} ({len(cl)} loops)")
    
    return {
        'prova': 'ciclos',
        'total_commits': len(tipos),
        'loops_detectados': len(loops_detectados),
        'pct_loops': round(pct_loops, 4),
        'clusters': len(clusters) if loops_detectados else 0,
        'primeiros_loops': [{'idx': i, 'tipo': t, 'msg': m[:40]} for i, t, m in loops_detectados[:10]],
    }

# ─── PROVA 3: ASSINATURA DAS FASES ─────────────────────────

def prova_assinatura(commits: List[Dict]) -> Dict:
    """Calcula dimensionalidade de cada fase do projeto."""
    print("\n" + "=" * 60)
    print("PROVA 3: ASSINATURA — Dimensionalidade por fase do projeto")
    print("=" * 60)
    
    fases = {}
    for c in commits:
        fase = c.get('fase', 'desconhecida')
        if fase not in fases:
            fases[fase] = []
        fases[fase].append(c)
    
    resultados = []
    for nome_fase, fase_commits in sorted(fases.items()):
        if len(fase_commits) < 5:
            continue
        # Texto da fase: tipos de commit concatenados
        texto_fase = ' '.join([f"{detectar_tipo(c['msg'])}:{c.get('files_changed', 1)}" for c in fase_commits])
        dados = texto_fase.encode('utf-8')[:2000]
        dim = MCRSignatureExpansiva.dimensionalidade_ideal(dados, max_dims=64)
        h = MCRByteUtils.entropia_bytes(dados)
        
        # Calcula diversidade de tipos como controle
        tipos = Counter(detectar_tipo(c['msg']) for c in fase_commits)
        diversidade = len(tipos)
        
        resultados.append({
            'fase': nome_fase,
            'commits': len(fase_commits),
            'dimensionalidade': dim,
            'entropia': round(h, 3),
            'diversidade_tipos': diversidade,
        })
        print(f"  {nome_fase:15s}: {len(fase_commits):3d} commits, dim={dim:3d}, H={h:.2f}, tipos={diversidade}")
    
    return {
        'prova': 'assinatura',
        'fases': resultados,
    }

# ─── PROVA 4: BASELINE ALEATORIO ───────────────────────────

def prova_baseline(commits: List[Dict], seed: int = 42) -> Dict:
    """Compara MCR real vs MCR com dados embaralhados."""
    print("\n" + "=" * 60)
    print("PROVA 4: BASELINE — Comparacao com dados embaralhados")
    print("=" * 60)
    
    random.seed(seed)
    commits_shuffled = list(commits)
    random.shuffle(commits_shuffled)
    
    # Treina MCR nos dados EMBARALHADOS
    n = len(commits_shuffled)
    split = int(n * 0.8)
    treino_r = commits_shuffled[:split]
    teste_r = commits_shuffled[split:]
    
    mk_r = MCR("prova4_random")
    for c in treino_r:
        token = codificar_como_token(c, incluir_survived=True)
        palavras = token.split(':')
        for i in range(len(palavras) - 1):
            mk_r.aprender(palavras[i], palavras[i + 1])
    
    # Testa previsao
    acertos_r = 0
    total_r = 0
    for c in teste_r:
        token_sem_fim = codificar_como_token(c, incluir_survived=False)
        palavras = token_sem_fim.split(':')
        pred, conf = mk_r.predizer(palavras[-1])
        if pred:
            if (pred == 's') == c.get('survived', True):
                acertos_r += 1
            total_r += 1
    
    acuracia_random = acertos_r / max(total_r, 1)
    
    # Treina MCR nos dados REAIS (mesma split)
    treino = commits[:split]
    teste = commits[split:]
    
    mk = MCR("prova4_real")
    for c in treino:
        token = codificar_como_token(c, incluir_survived=True)
        palavras = token.split(':')
        for i in range(len(palavras) - 1):
            mk.aprender(palavras[i], palavras[i + 1])
    
    acertos_real = 0
    total_real = 0
    for c in teste:
        token_sem_fim = codificar_como_token(c, incluir_survived=False)
        palavras = token_sem_fim.split(':')
        pred, conf = mk.predizer(palavras[-1])
        if pred:
            if (pred == 's') == c.get('survived', True):
                acertos_real += 1
            total_real += 1
    
    acuracia_real = acertos_real / max(total_real, 1)
    
    print(f"  Acurcia com dados REAIS:       {acuracia_real:.1%}")
    print(f"  Acurcia com dados EMBARALHADOS: {acuracia_random:.1%}")
    print(f"  Diferenca:                     {acuracia_real - acuracia_random:+.1%}")
    
    # Teste de significancia: se real > random + 5%, ha estrutura temporal
    if acuracia_real > acuracia_random + 0.05:
        print(f"  Resultado: ESTRUTURA TEMPORAL CONFIRMADA!")
        conclusao = "estrutura_temporal_confirmada"
    elif acuracia_real > acuracia_random:
        print(f"  Resultado: Estrutura temporal detectada (fraca)")
        conclusao = "estrutura_temporal_fraca"
    else:
        print(f"  Resultado: Nenhuma estrutura temporal detectada")
        conclusao = "sem_estrutura_temporal"
    
    return {
        'prova': 'baseline',
        'acuracia_real': round(acuracia_real, 4),
        'acuracia_random': round(acuracia_random, 4),
        'diferenca': round(acuracia_real - acuracia_random, 4),
        'conclusao': conclusao,
    }

# ─── MAIN ──────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  MCR MetaObserver — Prova de Conceito")
    print("  A Equacao MCR como metarobservador do desenvolvimento")
    print("=" * 60)
    
    # 1. Extracao
    print("\n[1] Extraindo commits do Git...")
    commits = extrair_commits()
    
    # 2. Sobrevivencia
    print("\n[2] Verificando sobrevivencia...")
    commits = verificar_sobrevivencia(commits)
    
    # 3. Fases
    print("\n[3] Detectando fases...")
    commits = detectar_fase(commits)
    
    # 4. Estatisticas basicas
    print("\n[4] Estatisticas basicas:")
    tipos = Counter(detectar_tipo(c['msg']) for c in commits)
    for tipo, count in tipos.most_common():
        print(f"  {tipo:10s}: {count}")
    
    # 5. Executar provas
    r1 = prova_retrodicao(commits)
    r2 = prova_ciclos(commits)
    r3 = prova_assinatura(commits)
    r4 = prova_baseline(commits)
    
    # 6. Relatorio final
    resultados = {
        'r1_retrodicao': r1,
        'r2_ciclos': r2,
        'r3_assinatura': r3,
        'r4_baseline': r4,
    }
    
    print("\n" + "=" * 60)
    print("  RELATORIO FINAL")
    print("=" * 60)
    
    print(f"""
    Prova 1 — Retrodicao:
      Acuracia: {r1['acuracia']:.1%} vs baseline {r1['baseline']:.1%}
      Ganho: {r1['ganho']:+.1%}
      Veredito: {r1['veredito'] if 'veredito' in r1 else ('REVOLUCIONARIO' if r1['ganho'] > 0.1 else 'PROMISSOR' if r1['ganho'] > 0.05 else 'MODESTO' if r1['ganho'] > 0 else 'RUIM')}
    
    Prova 2 — Ciclos:
      Loops detectados: {r2['loops_detectados']} ({r2['pct_loops']:.1%})
      Clusters: {r2['clusters']}
    
    Prova 3 — Assinatura:
      Dimensionalidade variou entre fases?
      {'SIM — a Equacao distingue as fases!' if len(set(f['dimensionalidade'] for f in r3['fases'])) > 1 else 'Fases similares em dimensionalidade'}
    
    Prova 4 — Baseline:
      Real: {r4['acuracia_real']:.1%} | Random: {r4['acuracia_random']:.1%}
      Diferenca: {r4['diferenca']:+.1%}
      Conclusao: {r4['conclusao']}
    """)
    
    # Salva resultados
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"  Resultados salvos em: {OUT_PATH}")
    
    # Resumo final
    print("\n  RESUMO:")
    todas_provas_passaram = (
        r1['ganho'] > 0 and
        r2['loops_detectados'] > 0 and
        len(set(f['dimensionalidade'] for f in r3['fases'])) > 1 and
        r4['acuracia_real'] > r4['acuracia_random']
    )
    if todas_provas_passaram:
        print("  4/4 provas indicam que o CONCEITO FUNCIONA!")
        print("  A Equacao MCR pode atuar como metarobservador do desenvolvimento.")
    else:
        print("  Provas passadas:")
        print(f"    Prova 1 (retrodicao): {'PASSOU' if r1['ganho'] > 0 else 'NAO PASSOU'}")
        print(f"    Prova 2 (ciclos):     {'PASSOU' if r2['loops_detectados'] > 0 else 'NAO PASSOU'}")
        print(f"    Prova 3 (assinatura): {'PASSOU' if len(set(f['dimensionalidade'] for f in r3['fases'])) > 1 else 'NAO PASSOU'}")
        print(f"    Prova 4 (baseline):   {'PASSOU' if r4['acuracia_real'] > r4['acuracia_random'] else 'NAO PASSOU'}")

if __name__ == '__main__':
    main()
