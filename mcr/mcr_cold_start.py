#!/usr/bin/env python3
"""mcr.mcr_cold_start — Cold Start do ecossistema MCR.
Apaga o KG, minera do zero, clusteriza e valida.
A prova de que o MCR e agnostico de dominio."""
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from mcr.paths import KG_DIR, SERVER_DIR, CANARY_NPC_DIR, CANARY_MONSTER_DIR


def cold_start(server_dir: Path = None, kg_dir: Path = None) -> dict:
    """Executa um Cold Start completo do MCR.
    
    1. Apaga o Knowledge Graph existente
    2. Minera o servidor (Lua scripts + C++ source)
    3. Constrói clusters de assinatura
    4. Constrói meta-clusters
    5. Valida que consegue gerar um NPC canonico
    
    Args:
        server_dir: diretorio do servidor Canary
        kg_dir: diretorio do KG (sera limpo e recriado)
    
    Returns:
        relatorio do cold start
    """
    t0 = time.time()
    server_dir = server_dir or SERVER_DIR
    kg_dir = kg_dir or KG_DIR

    relatorio = {
        'inicio': time.strftime('%Y-%m-%d %H:%M:%S'),
        'etapas': {},
        'erros': [],
    }

    print('=' * 55)
    print('  COLD START — MCR Tabula Rasa')
    print('=' * 55)

    # Etapa 1: Limpar KG
    print('\n[1/5] Limpando Knowledge Graph...')
    if kg_dir.exists():
        for f in kg_dir.glob('patterns_*.json'):
            try:
                f.unlink()
                print('  Removido: %s' % f.name)
            except Exception as e:
                print('  Erro ao remover %s: %s' % (f.name, e))
    relatorio['etapas']['kg_limpo'] = True
    print('  KG limpo.')

    # Etapa 2: SanityValidator sem cache (força re-mineracao)
    print('\n[2/5] Minerando APIs (C++ + Lua)...')
    from mcr.sanity_validator import SanityValidator, _APIS_CACHE, _APIS_CACHE_INICIALIZADO
    _APIS_CACHE_INICIALIZADO = False
    _APIS_CACHE.clear()
    val = SanityValidator(
        kg_dir=kg_dir,
        server_src_dir=server_dir / 'src' if server_dir else None,
    )
    relatorio['etapas']['apis_mineradas'] = len(val.api_conhecidas)
    print('  %d APIs mineradas.' % len(val.api_conhecidas))

    # Etapa 3: Clusters de assinatura (minera direto dos scripts Lua)
    print('\n[3/5] Clusterizando entidades (minerando scripts Lua)...')
    from mcr.mcr_signature_cluster import SignatureAnalyzer, SignatureCluster, _assinatura_entidade, _jaccard
    from mcr.encoding import read_file
    import re
    from collections import Counter

    analyzer = SignatureAnalyzer()

    # Minerar padroes direto dos scripts Lua (sem depender do KG)
    padroes_brutos = []
    for fpath in sorted(CANARY_NPC_DIR.glob('*.lua'))[:800]:  # amostra
        try:
            with open(fpath, 'r', encoding='latin-1') as f:
                content = f.read()
            # Extrai chamadas simples para criar padroes
            import re
            chamadas = re.findall(r'\b[A-Za-z]+[\w.]*(?:\:\w+)?(?=\s*\()', content)
            vars_found = re.findall(r'\blocal\s+(\w+)', content)
            padroes_brutos.append({
                'arquivo': str(fpath),
                'tipo': 'npc' if 'npctype' in ' '.join(chamadas).lower() else 'generic',
                'api_calls': list(set(chamadas))[:30],
                'variaveis': list(set(vars_found))[:10],
                'tamanho_linhas': content.count('\n'),
            })
        except Exception:
            continue
    # Adiciona monstros
    for fpath in sorted(CANARY_MONSTER_DIR.glob('*.lua'))[:500]:
        try:
            with open(fpath, 'r', encoding='latin-1') as f:
                content = f.read()
            chamadas = re.findall(r'\b[A-Za-z]+[\w.]*(?:\:\w+)?(?=\s*\()', content)
            vars_found = re.findall(r'\blocal\s+(\w+)', content)
            padroes_brutos.append({
                'arquivo': str(fpath),
                'tipo': 'monster' if 'monstertype' in ' '.join(chamadas).lower() else 'generic',
                'api_calls': list(set(chamadas))[:30],
                'variaveis': list(set(vars_found))[:10],
                'tamanho_linhas': content.count('\n'),
            })
        except Exception:
            continue

    print('  %d entidades mineradas dos scripts' % len(padroes_brutos))

    # Converte padroes em SignatureClusters
    from collections import Counter
    from mcr.mcr_signature_cluster import _assinatura_entidade, _jaccard
    clusters_criados = []
    for ent in padroes_brutos:
        melhor = None
        melhor_score = 0.0
        for c in clusters_criados:
            score = c.similaridade(ent)
            if score > melhor_score:
                melhor_score = score
                melhor = c
        if melhor and melhor_score >= 0.15:
            melhor.adicionar(ent)
        else:
            nome = "Type_%c" % (65 + len(clusters_criados))
            clusters_criados.append(SignatureCluster(nome, [ent]))

    clusters_criados.sort(key=lambda c: -len(c))
    analyzer.clusters = clusters_criados
    relatorio['etapas']['clusters'] = len(clusters_criados)
    relatorio['etapas']['entidades_clusterizadas'] = sum(len(c) for c in clusters_criados)
    print('  %d clusters formados.' % len(clusters_criados))
    for c in clusters_criados[:5]:
        print('    %s: %d entidades' % (c.nome, len(c)))

    # Etapa 4: Meta-clusters
    print('\n[4/5] Construindo meta-clusters...')
    meta_clusters = analyzer.meta_clusterizar()
    relatorio['etapas']['meta_clusters'] = len(meta_clusters)
    for mc in meta_clusters:
        print('  %s: %d entidades, %d sub-clusters' % (
            mc.nome, mc.total_entidades(), len(mc.clusters)))

    # Etapa 5: Validacao — gerar um NPC e verificar se e valido
    print('\n[5/5] Validando geracao de codigo...')
    try:
        from mcr.golden_templates import gerar_npc_canary
        from mcr.mcr_world_builder import _validar_sintaxe, _validar_semantica

        codigo = gerar_npc_canary({
            'name': 'ColdStartTest',
            'health': 100,
            'looktype': 128,
            'greeting': 'Eu fui gerado sem KG pre-existente!',
        })
        valido_sint, erro = _validar_sintaxe(codigo)
        apis_invalidas = _validar_semantica(codigo, 'npc')

        relatorio['validacao'] = {
            'codigo_gerado': len(codigo) > 0,
            'sintaxe_valida': valido_sint,
            'apis_validas': len(apis_invalidas) == 0,
            'total_apis_verificadas': len(val.api_conhecidas),
        }

        if valido_sint and not apis_invalidas:
            print('  Codigo NPC gerado com sucesso: %d bytes' % len(codigo))
            print('  Sintaxe: OK')
            print('  APIs: %d conhecidas, 0 desconhecidas' % len(val.api_conhecidas))
            print('  >> COLD START BEM-SUCEDIDO')
        else:
            msg = []
            if not valido_sint:
                msg.append('sintaxe invalida: %s' % erro)
            if apis_invalidas:
                msg.append('APIs desconhecidas: %s' % ', '.join(apis_invalidas[:5]))
            relatorio['validacao']['erro'] = '; '.join(msg)
            print('  >> FALHA: %s' % '; '.join(msg))
    except Exception as e:
        relatorio['validacao'] = {'erro': str(e)}
        print('  >> ERRO: %s' % e)

    t_total = time.time() - t0
    relatorio['tempo_total'] = round(t_total, 1)
    print('\n' + '=' * 55)
    print('  COLD START CONCLUIDO em %.1fs' % t_total)
    print('=' * 55)

    return relatorio


if __name__ == '__main__':
    import sys
    sys.path.insert(0, r'E:\MCR')
    rel = cold_start()
    print('\nRelatorio:')
    print(json.dumps(rel, indent=2, ensure_ascii=False)[:1000])
