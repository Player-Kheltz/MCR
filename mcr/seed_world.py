#!/usr/bin/env python3
"""seed_world.py — Canonizacao do Conteudo Gerado.

Registra no MCRWorldState e no KG as entidades criadas
durante os testes de qualidade. Este e o Genesis do mundo.

Uso:
    python mcr/seed_world.py              # Canoniza tudo
    python mcr/seed_world.py --dry-run     # Mostra o que faria sem alterar
"""
import sys, os, json, argparse, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'devia', 'kernel'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from mcr.mcr_world_state import registrar_entidade, _carregar, _salvar, salvar_foundation, carregar_foundation
from mcr.mcr_world_chronicle import append_chronicle


# ─── Entidades para canonizar ─────────────────────────────

ENTIDADES = {
    'npcs': {
        'Eldon Oakheart': {
            'file': 'npc_eldon_oakheart.lua',
            'role': 'Ferreiro Mistico',
            'raca': 'Elfo',
            'sexo': 'Masculino',
            'idade': 400,
            'local': 'Vesperia (floresta de Yalahar)',
            'personalidade': 'Intuitivo, inquieto, solitario',
            'traco_secreto': 'Medo de borboletas',
            'tier': 'canon',
            'relacoes': ['reside_em:Yalahar', 'frequenta:Vesperia'],
        },
        'Grimgor Fangshield': {
            'file': 'npc_grimgor_fangshield.lua',
            'role': 'Guarda da Ponte',
            'raca': 'Orc',
            'sexo': 'Masculino',
            'idade': 400,
            'local': 'Ponte Ebonshard',
            'personalidade': 'Determinado, timido, obcecado por colecionar',
            'traco_secreto': 'Medo irracional de passaros',
            'tier': 'canon',
            'relacoes': ['guarda:Ponte Ebonshard'],
        },
        'Aelindor': {
            'file': 'quest_npc_aelindor.lua',
            'role': 'Ferreiro de Thais (entregador de quest)',
            'raca': 'Elfo',
            'sexo': 'Masculino',
            'local': 'Thais',
            'personalidade': 'Sabio, dedicado, misterioso',
            'tier': 'canon',
            'quests': ['A Forja Perdida'],
            'relacoes': ['reside_em:Thais', 'oferece_quest:A Forja Perdida'],
        },
    },
    'lores': {
        'Fundacao de Eridanus': {
            'tipo': 'mito_de_criacao',
            'resumo': 'Eridanus foi fundada apos um arco-iris divino sobre o rio Eridanos,'
                      ' unindo o mar de Ardor ao mar de Serpentes.',
            'lugares_mencionados': ['Erenor', 'Eridanos', 'Ardor', 'Serpentes', 'Telara', 'Thais'],
            'tier': 'canon',
        },
        'Origem do SPA': {
            'tipo': 'mito_de_sistema',
            'resumo': 'O Sistema de Progressao do Aventureiro (SPA) originou-se de um '
                      'caminho oculto guardado pelo misterioso Conjurador do Caminho Escondido.',
            'lugares_mencionados': ['Valdoria', 'Tibia'],
            'tier': 'canon',
        },
    },
}


def listar_entidades_atuais():
    """Lista entidades ja registradas no mundo."""
    estado = _carregar()
    total = sum(len(v) for v in estado.values() if isinstance(v, dict))
    print(f'Mundo atual: {total} entidades')
    for chave in ('npcs', 'monstros', 'lores'):
        items = list(estado.get(chave, {}).keys())
        if items:
            print(f'  {chave}: {", ".join(items[:10])}')
    return estado


def executar(dry_run: bool = False):
    """Executa a canonizacao completa."""
    print('=' * 55)
    print('  SEED DO MUNDO — Canonizacao Inicial')
    print('=' * 55)
    print()

    # 1. Mostra estado atual
    estado_atual = listar_entidades_atuais()
    print()

    if not dry_run:
        # 2. Registra NPCs
        print('Registrando NPCs...')
        for nome, dados in ENTIDADES['npcs'].items():
            registrar_entidade('npc', nome, dados)
            print(f'  + {nome} ({dados["role"]})')

        # 3. Registra Lores
        print('Registrando Lores...')
        for nome, dados in ENTIDADES['lores'].items():
            registrar_entidade('lore', nome, dados)
            print(f'  + {nome}')

        # 4. Adiciona entradas na Cronica
        print('Atualizando Cronica do Mundo...')
        append_chronicle(
            'Eldon Oakheart, ferreiro elfco mistico, abriu sua forja em Vesperia. '
            'Dizem que ele tem um medo peculiar de borboletas, mas suas armas '
            'encantadas sao as melhores da regiao.',
            {'type': 'npc_arrival', 'entity': 'Eldon Oakheart', 'location': 'Vesperia'}
        )
        append_chronicle(
            'Grimgor Fangshield, um orc de linhagem real capturado em batalha, '
            'foi designado para guardar a Ponte Ebonshard. Coleciona objetos exoticos '
            'e tem panico de passaros.',
            {'type': 'npc_assignment', 'entity': 'Grimgor Fangshield', 'location': 'Ponte Ebonshard'}
        )
        append_chronicle(
            'A Forja Perdida: Aelindor, ferreiro de Thais, procura um aventureiro '
            'corajoso para recuperar suas ferramentas roubadas por goblins em um '
            'antigo vulcao abandonado.',
            {'type': 'quest_offered', 'entity': 'Aelindor', 'quest': 'A Forja Perdida'}
        )

        # 5. Verifica resultado
        estado_final = _carregar()
        total_npcs = len(estado_final.get('npcs', {}))
        total_lores = len(estado_final.get('lores', {}))
        print()
        print('=' * 55)
        print(f'  CANONIZACAO CONCLUIDA')
        print(f'  NPCs: {total_npcs} | Lores: {total_lores}')
        print(f'  Cronicas adicionadas: 3')
        print('=' * 55)

    else:
        print('MODO DRY-RUN — Nenhuma alteracao feita.')
        print(f'  Seriam registrados: {len(ENTIDADES["npcs"])} NPCs, {len(ENTIDADES["lores"])} Lores')
        print(f'  Seriam adicionadas: 3 cronicas')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Mostra o que faria sem alterar')
    args = parser.parse_args()
    executar(dry_run=args.dry_run)
