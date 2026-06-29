#!/usr/bin/env python
"""Teste Comparativo de Performance — NPCGenerator com e sem exemplos reais.

Testa 4 cenários de NPC rodando o pipeline com e sem dados do CanaryIndexer.
Métricas: tempo, placeholders lixo, nome real vs genérico, validação Lua.

Uso:
    python sandbox/test_performance.py [--fast]
"""

import os, sys, json, time, re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos'))

from npc_generator import NPCGenerator
from canary_indexer import CanaryIndexer
from lua_validator import LuaValidator


# ============================================================
# PLACEHOLDERS LIXO — padrões que indicam geração genérica
# ============================================================
PLACEHOLDERS_LIXO = re.compile(
    r'\b(example item|another item|third item|generic item|placeholder|some item)\b',
    re.IGNORECASE
)

ITEM_IDS_LIXO = {3003, 3457, 2920, 3031}  # IDs placeholders comuns


def detectar_lixo(codigo: str) -> int:
    """Conta quantos placeholders lixo existem no código."""
    return len(PLACEHOLDERS_LIXO.findall(codigo))


def detectar_ids_lixo(codigo: str) -> int:
    """Conta quantos IDs de placeholder aparecem no código."""
    count = 0
    for id_val in ITEM_IDS_LIXO:
        if str(id_val) in codigo:
            count += 1
    return count


def extrair_nome_arquivo(codigo: str) -> str:
    """Extrai o nome do arquivo do código Lua."""
    m = re.search(r"fileName\s*=\s*['\"]([^'\"]+)['\"]", codigo)
    return m.group(1) if m else 'unknown'


def extrair_itens_gerados(codigo: str) -> list:
    """Extrai lista de itens do shop gerados no código."""
    itens = []
    for m in re.finditer(
        r'\{\s*itemName\s*=\s*"([^"]*)"\s*,\s*clientId\s*=\s*(\d+)[^}]*\}',
        codigo
    ):
        itens.append({
            'nome': m.group(1),
            'client_id': int(m.group(2)),
            'lixo': m.group(1).lower() in ['example item', 'another item', 'third item']
        })
    return itens


# ============================================================
# CENARIOS DE TESTE
# ============================================================
CENARIOS = [
    {
        'descricao': 'Ferreiro em Eridanus que vende armas',
        'tipo': 'shop',
        'tags': ['ferreiro', 'arma', 'eridanus'],
    },
    {
        'descricao': 'Vendedor de pocoes magicas em Venore',
        'tipo': 'shop',
        'tags': ['pocao', 'potions', 'venore'],
    },
    {
        'descricao': 'Banco central de Thais',
        'tipo': 'bank',
        'tags': ['banco', 'bank', 'thais'],
    },
    {
        'descricao': 'Guarda do portao de Carlin',
        'tipo': 'gate',
        'tags': ['guarda', 'gate', 'carlin'],
    },
]


def testar_sem_exemplos(gen, cenario):
    """Testa NPCGenerator sem exemplos (comportamento ANTIGO)."""
    t0 = time.time()
    resultado = gen.gerar(cenario['descricao'], cenario['tipo'], exemplos=None)
    tempo = time.time() - t0
    codigo = resultado.get('codigo', '')
    itens = extrair_itens_gerados(codigo)
    return {
        'tempo': round(tempo, 2),
        'codigo': codigo,
        'nome': resultado.get('nome', ''),
        'itens_lixo': detectar_lixo(codigo),
        'ids_lixo': detectar_ids_lixo(codigo),
        'itens': itens,
        'total_itens_lixo': sum(1 for i in itens if i['lixo']),
        'erro': resultado.get('erro', ''),
    }


def testar_com_exemplos(gen, indexer, cenario):
    """Testa NPCGenerator com exemplos reais do CanaryIndexer."""
    # Buscar exemplos reais
    exemplos = indexer.buscar(cenario['descricao'], limite=3)
    
    t0 = time.time()
    resultado = gen.gerar(cenario['descricao'], cenario['tipo'], exemplos=exemplos)
    tempo = time.time() - t0
    codigo = resultado.get('codigo', '')
    itens = extrair_itens_gerados(codigo)
    
    return {
        'tempo': round(tempo, 2),
        'codigo': codigo,
        'nome': resultado.get('nome', ''),
        'itens_lixo': detectar_lixo(codigo),
        'ids_lixo': detectar_ids_lixo(codigo),
        'itens': itens,
        'total_itens_lixo': sum(1 for i in itens if i['lixo']),
        'erro': resultado.get('erro', ''),
        'exemplos_encontrados': len(exemplos),
        'exemplos_nomes': [e.get('nome', '?') for e in exemplos],
    }


def main():
    fast = '--fast' in sys.argv
    
    gen = NPCGenerator()
    indexer = CanaryIndexer()
    validator = LuaValidator()
    
    print('=' * 70)
    print('TESTE COMPARATIVO — NPCGenerator com vs sem exemplos')
    print('=' * 70)
    
    resultados = []
    
    for i, cenario in enumerate(CENARIOS, 1):
        print('\n%s Cenário %d: %s' % ('=' * 40, i, cenario['descricao']))
        
        # Teste SEM exemplos (comportamento antigo)
        r_old = testar_sem_exemplos(gen, cenario)
        
        # Teste COM exemplos (comportamento novo)
        r_new = testar_com_exemplos(gen, indexer, cenario)
        
        # Validacao Lua
        valid_old = validator.validar(r_old['codigo'])
        valid_new = validator.validar(r_new['codigo'])
        
        print('  [SEM exemplos]  tempo=%ss  itens_lixo=%d  ids_lixo=%d  valido=%s' % (
            r_old['tempo'], r_old['itens_lixo'], r_old['ids_lixo'],
            valid_old['valido']
        ))
        print('    Itens: %s' % [i['nome'] for i in r_old['itens']])
        
        print('  [COM exemplos]  tempo=%ss  itens_lixo=%d  ids_lixo=%d  valido=%s  exemplos=%d' % (
            r_new['tempo'], r_new['itens_lixo'], r_new['ids_lixo'],
            valid_new['valido'], r_new['exemplos_encontrados']
        ))
        print('    Exemplos: %s' % ', '.join(r_new['exemplos_nomes']))
        print('    Itens: %s' % [i['nome'] for i in r_new['itens']])
        
        # Diferenca
        diff_lixo = r_old['itens_lixo'] - r_new['itens_lixo']
        diff_tempo = r_old['tempo'] - r_new['tempo']
        if diff_lixo > 0 or diff_tempo > 0:
            print('  >> GANHO: -%d itens lixo, -%ss tempo' % (diff_lixo, round(abs(diff_tempo), 2)))
        elif diff_lixo < 0:
            print('  >> PIORA: +%d itens lixo' % abs(diff_lixo))
        else:
            print('  >> Neutro (mesma quantidade de lixo)')
        
        resultados.append({
            'cenario': cenario['descricao'],
            'tipo': cenario['tipo'],
            'sem_exemplos': {
                'tempo': r_old['tempo'],
                'itens_lixo': r_old['itens_lixo'],
                'ids_lixo': r_old['ids_lixo'],
                'valido': valid_old['valido'],
            },
            'com_exemplos': {
                'tempo': r_new['tempo'],
                'itens_lixo': r_new['itens_lixo'],
                'ids_lixo': r_new['ids_lixo'],
                'valido': valid_new['valido'],
                'exemplos_encontrados': r_new['exemplos_encontrados'],
            },
        })
        
        # Se tiver --fast, testa so o primeiro
        if fast and i >= 2:
            print('\n  (modo fast: pulando cenarios restantes)')
            break
    
    # Resumo
    print('\n%s' % ('=' * 70))
    print('RESUMO')
    print('%s' % ('=' * 70))
    
    total_lixo_old = sum(r['sem_exemplos']['itens_lixo'] for r in resultados)
    total_lixo_new = sum(r['com_exemplos']['itens_lixo'] for r in resultados)
    total_tempo_old = sum(r['sem_exemplos']['tempo'] for r in resultados)
    total_tempo_new = sum(r['com_exemplos']['tempo'] for r in resultados)
    
    print('Total itens lixo (sem exemplos):  %d' % total_lixo_old)
    print('Total itens lixo (com exemplos):  %d' % total_lixo_new)
    print('Reducao de lixo:                  %d (%d%%)' % (
        total_lixo_old - total_lixo_new,
        (total_lixo_old - total_lixo_new) / max(total_lixo_old, 1) * 100
    ))
    print('Total tempo (sem exemplos):       %.2fs' % total_tempo_old)
    print('Total tempo (com exemplos):       %.2fs' % total_tempo_new)
    
    # Salva resultados
    output = os.path.join(os.path.dirname(__file__), '.teste_performance.json')
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print('\nResultados salvos em: %s' % output)
    
    # Verdict
    if total_lixo_new < total_lixo_old:
        print('\nVEREDITO: [OK] Melhoria confirmada!')
    elif total_lixo_new == total_lixo_old:
        print('\nVEREDITO: [-] Neutro (mesmo lixo) — verificar se indexer tem dados')
    else:
        print('\nVEREDITO: [FALHA] Piorou — algo errado na implementacao')
    
    return resultados


if __name__ == '__main__':
    main()
