#!/usr/bin/env python3
"""Analisador de QUALIDADE real - verifica se a resposta MCR menciona classes reais do DataLake,
identifica alucinacoes, e conta cobertura real de bugs."""
import re

# Termos REAIS do DataLake que DEVEM aparecer
TERMOS_REAIS = [
    'datalake', 'streamsimulator', 'processar_stream', '_transformar',
    '_aplicar_filtro', 'salvar_resultados', 'processar_lote', 'estatisticas',
    'historico', '_cache_global', '_contador', 'stream_id', 'gerar_leitura',
    'memory leak', 'race condition', 'eval', 'cache', 'divisao por zero',
    'path traversal', 'loop infinito', 'arquivo nao fechado',
    'variavel de classe', 'efeito colateral',
]

# Termos ALUCINADOS (classes que NAO existem no datalake.py)
TERMOS_ALUCINACAO = [
    'datastream', 'datacollector', 'datatransformer', 'dataloader',
    'realtimeanalyzer', 'errorhandler', 'caching',
    'dataprocessor', 'datamanager', 'streamcontroller', 'dataservice',
    'datanormalizer', 'dataanalyzer', 'securitymanager', 'cachesystem',
    'abstract_factory', 'api_rest', 'singleton_pattern',
]

def analisar_qualidade(texto, nome="MCR"):
    """Analisa a qualidade real de uma resposta."""
    t = texto.lower()
    
    # 1. Termos reais encontrados
    reais_encontrados = [t for t in TERMOS_REAIS if t.lower() in t]
    
    # 2. Alucinacoes
    alucinacoes = [a for a in TERMOS_ALUCINACAO if a.lower() in t]
    
    # 3. Secoes com [ ] markers
    markers = re.findall(r'\[\s*\]([^\[]+)', texto)
    markers = [m.strip().split(':')[0].strip().upper() for m in markers if m.strip()]
    
    # 4. Bugs mencionados (procura numeros de linha)
    linhas_bug = re.findall(r'(?:BUG|LINHA|linha)\s*:?\s*(\d+)', texto, re.IGNORECASE)
    linhas_bug = list(set(linhas_bug))
    
    # 5. Codigo Python
    blocos_codigo = re.findall(r'```(?:python)?\s*\n(.*?)```', texto, re.DOTALL)
    linhas_codigo = sum(len(b.split('\n')) for b in blocos_codigo)
    
    # 6. Erros de sintaxe
    erros = 0
    for bloco in blocos_codigo:
        try:
            compile(bloco.strip(), '<test>', 'exec')
        except:
            erros += 1
    
    return {
        'nome': nome,
        'termos_reais': len(reais_encontrados),
        'termos_reais_lista': reais_encontrados[:15],
        'alucinacoes': alucinacoes,
        'total_alucinacoes': len(alucinacoes),
        'markers': markers,
        'total_markers': len(markers),
        'linhas_bug_unicas': len(linhas_bug),
        'linhas_codigo': linhas_codigo,
        'erros_sintaxe': erros,
        'chars': len(texto),
    }

def comparar_qualidade(mcr_txt, cloud_txt):
    """Compara a qualidade entre MCR e Cloud."""
    mcr_q = analisar_qualidade(mcr_txt, "MCR")
    cloud_q = analisar_qualidade(cloud_txt, "Cloud")
    
    print("=" * 70)
    print("  ANALISE DE QUALIDADE REAL")
    print("=" * 70)
    print(f"\n{'Metrica':<35} {'MCR':<15} {'Cloud':<15}")
    print("-" * 65)
    
    metricas = [
        ('Termos reais do DataLake', 'termos_reais', '{}'),
        ('Alucinacoes (classes inexistentes)', 'total_alucinacoes', '{} (X)'),
        ('Seções com marcador [ ]', 'total_markers', '{}'),
        ('Linhas de código Python', 'linhas_codigo', '{}'),
        ('Bugs mencionados (linhas)', 'linhas_bug_unicas', '{}'),
        ('Erros de sintaxe em código', 'erros_sintaxe', '{} (X)'),
        ('Total de caracteres', 'chars', '{}'),
    ]
    
    for nome, chave, fmt in metricas:
        m_val = mcr_q[chave]
        c_val = cloud_q[chave]
        m_str = fmt.format(m_val)
        c_str = fmt.format(c_val)
        # Destaque visual para quem ganha
        if isinstance(m_val, int) and isinstance(c_val, int):
            if chave in ('total_alucinacoes', 'erros_sintaxe'):
                # Menor é melhor
                m_str += " (+)" if m_val < c_val else ""
                c_str += " (+)" if c_val < m_val else ""
            else:
                # Maior é melhor
                m_str += " (+)" if m_val > c_val else ""
                c_str += " (+)" if c_val > m_val else ""
        
        print(f'  {nome:<35} {m_str:<15} {c_str:<15}')
    
    print(f"\n  TERMOS REAIS ENCONTRADOS:")
    print(f"  MCR: {', '.join(mcr_q['termos_reais_lista'][:10])}")
    print(f"  Cloud: {', '.join(cloud_q['termos_reais_lista'][:10])}")
    
    if mcr_q['alucinacoes']:
        print(f"\n   ALUCINACOES MCR: {', '.join(mcr_q['alucinacoes'][:5])}")
    if cloud_q['alucinacoes']:
        print(f"   ALUCINACOES Cloud: {', '.join(cloud_q['alucinacoes'][:5])}")
    
    print(f"\n  SECOES MCR: {mcr_q['markers']}")
    print(f"  SECOES Cloud: {cloud_q['markers']}")
    
    # Score de qualidade
    mcr_score = mcr_q['termos_reais'] * 5 + mcr_q['total_markers'] * 10 + mcr_q['linhas_codigo']
    mcr_score -= mcr_q['total_alucinacoes'] * 20 + mcr_q['erros_sintaxe'] * 10
    
    cloud_score = cloud_q['termos_reais'] * 5 + cloud_q['total_markers'] * 10 + cloud_q['linhas_codigo']
    cloud_score -= cloud_q['total_alucinacoes'] * 20 + cloud_q['erros_sintaxe'] * 10
    
    print(f"\n  {'SCORE DE QUALIDADE':<35} {mcr_score:<15} {cloud_score:<15}")
    if mcr_score > cloud_score:
        print(f"\n  (+) VENCEDOR: MCR-DevIA (qualidade superior)")
    elif cloud_score > mcr_score:
        print(f"  (+) VENCEDOR: Cloud (qualidade superior)")
    else:
        print(f"  🤝 EMPATE TECNICO")
    print("=" * 70)
    
    return mcr_score, cloud_score

if __name__ == "__main__":
    import sys
    
    mcr_path = "E:/Projeto MCR/sandbox/teste_cego_mega/respostas_mcr/mega_1.txt"
    cloud_path = "E:/Projeto MCR/sandbox/teste_cego_mega/respostas_cloud/mega_1.txt"
    
    mcr_txt = open(mcr_path, "r", encoding="utf-8-sig", errors="replace").read() if __import__("os").path.exists(mcr_path) else ""
    cloud_txt = open(cloud_path, "r", encoding="utf-8-sig", errors="replace").read() if __import__("os").path.exists(cloud_path) else ""
    
    if not mcr_txt or not cloud_txt:
        print("Respostas nao encontradas")
        sys.exit(1)
    
    comparar_qualidade(mcr_txt, cloud_txt)
