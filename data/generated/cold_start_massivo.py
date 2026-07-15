#!/usr/bin/env python3
"""Cold Start Massivo — minera o ecossistema MCR por partes.

Processa cada diretorio como um mini cold start independente,
depois consolida as metricas. Evita O(n²) global.
"""
import sys, json, time, math, os
from pathlib import Path
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from mcr.signature import raw_token_set
from mcr.mcr_signature_cluster import SignatureCluster

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')


_EXT_ACEITAS = {'.py', '.lua', '.cpp', '.hpp', '.h', '.cs', '.md', '.sql', '.json', '.yaml', '.yml', '.xml', '.txt', '.cfg', '.conf'}
MAX_POR_DIR = 150

DIRS = [
    ('devia/kernel', 'Python (kernel)'),
    ('devia/modules', 'Python (modulos)'),
    ('mcr', 'Python (ecossistema)'),
    ('server/data/scripts', 'Lua (scripts)'),
    ('server/src', 'C++ (servidor)'),
    ('tools/grimorio', 'C# (ferramentas)'),
    ('docs', 'Markdown (documentacao)'),
    ('data/generated/sql_corpus', 'SQL (corpus)'),
]


def _extrair_entidade(caminho: Path) -> dict:
    try:
        codigo = caminho.read_text(encoding='utf-8', errors='replace')
    except Exception:
        try:
            codigo = caminho.read_text(encoding='latin-1', errors='replace')
        except Exception:
            return None
    if not codigo or len(codigo) < 30:
        return None
    tokens = raw_token_set(codigo)
    ext = caminho.suffix.lower()
    return {
        'arquivo': str(caminho),
        'tipo': ext,
        'api_calls': list(tokens),
        'tamanho_linhas': codigo.count('\n'),
        'extensao': ext,
        'tokens_count': len(tokens),
    }


def _clusterizar(entidades, threshold=0.15):
    clusters = []
    for ent in entidades:
        melhor = None
        melhor_score = 0.0
        for c in clusters:
            score = c.similaridade(ent)
            if score > melhor_score:
                melhor_score = score
                melhor = c
        if melhor and melhor_score >= threshold:
            melhor.adicionar(ent)
        else:
            nome = "C_%c" % (65 + len(clusters) % 26)
            if any(c.nome == nome for c in clusters):
                nome = "C_%d" % len(clusters)
            clusters.append(SignatureCluster(nome, [ent]))
    clusters.sort(key=lambda c: -len(c))
    return clusters


def main():
    print('=' * 65)
    print('  COLD START MASSIVO — Ecossistema MCR (por partes)')
    print('=' * 65)

    resultados = {}

    for rel_dir, rotulo in DIRS:
        path = Path(_BASE) / rel_dir.replace('/', '\\')
        if not path.exists():
            print(f'\n  [SKIP] {rotulo} -> nao encontrado')
            continue

        print(f'\n  [{rotulo}]')
        print(f'  Diretorio: {path}')

        t_dir = time.time()
        entidades = []
        for fpath in path.rglob('*'):
            if len(entidades) >= MAX_POR_DIR:
                break
            if fpath.suffix.lower() not in _EXT_ACEITAS:
                continue
            if any(p.startswith('.') or p in ('__pycache__', 'node_modules') for p in fpath.parts):
                continue
            if fpath.stat().st_size > 500 * 1024:
                continue
            ent = _extrair_entidade(fpath)
            if ent:
                entidades.append(ent)

        t_miner = time.time() - t_dir
        print(f'  Mineracao: {len(entidades)} entidades em {t_miner:.1f}s')

        if not entidades:
            continue

        t_clust = time.time()
        clusters = _clusterizar(entidades)
        t_clust = time.time() - t_clust

        # Linguagem dominante (por extensao)
        ext_counts = Counter(e.get('extensao', '?') for e in entidades)
        lang_dominante = ext_counts.most_common(1)[0][0] if ext_counts else '?'

        # Entropia media dos clusters
        entropias = [c.calcular_entropia() for c in clusters if len(c) > 1]
        entropia_media = sum(entropias) / max(len(entropias), 1)

        ext_str = ', '.join(f'{e}={c}' for e, c in ext_counts.most_common(5))
        print(f'  Clusterizacao: {len(clusters)} clusters em {t_clust:.1f}s')
        print(f'  Extensoes: {ext_str}')
        print(f'  Entropia media: {entropia_media:.2f}')
        print(f'  Top cluster: {clusters[0].nome} ({len(clusters[0])} entidades)')
        print(f'  Tempo total: {time.time()-t_dir:.1f}s')

        resultados[rotulo] = {
            'diretorio': rel_dir,
            'entidades': len(entidades),
            'clusters': len(clusters),
            'tempo_mineracao': round(t_miner, 1),
            'tempo_clusterizacao': round(t_clust, 1),
            'tempo_total': round(time.time() - t_dir, 1),
            'entropia_media': round(entropia_media, 3),
            'extensoes': dict(ext_counts.most_common(8)),
            'top_cluster_tamanho': len(clusters[0]),
            'top_cluster_nome': clusters[0].nome,
        }

    # Relatorio consolidado
    print('\n' + '=' * 65)
    print('  RELATORIO CONSOLIDADO')
    print('=' * 65)
    header = f"{'Dominio':<25} {'Entidades':<12} {'Clusters':<12} {'Entropia':<12} {'Tempo':<10}"
    print(header)
    print('-' * len(header))
    total_ents = 0
    total_clusters = 0
    for rotulo, r in sorted(resultados.items(), key=lambda x: -x[1]['entidades']):
        print(f"{rotulo:<25} {r['entidades']:<12} {r['clusters']:<12} {r['entropia_media']:<12} {r['tempo_total']}s")
        total_ents += r['entidades']
        total_clusters += r['clusters']
    print('-' * len(header))
    print(f"{'TOTAL':<25} {total_ents:<12} {total_clusters:<12}")
    print(f"\n  Kernel modificado: NAO")
    print(f"  Tokenizador: raw_token_set (universal)")
    print(f"  Dominios processados: {len(resultados)}/{len(DIRS)}")
    print('=' * 65)


if __name__ == '__main__':
    main()
