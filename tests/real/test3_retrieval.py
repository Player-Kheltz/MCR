"""
TESTE 3 — Qualidade do RETRIEVAL com Radar (sem geracao, so busca)
Testa: dado uma pergunta, o Radar encontra resposta similar nos 13.751 dialogos?
"""
import sys, os, json, re, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from mcr.mcr_radar import RadarMCR

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

def carregar_dialogos():
    with open(os.path.join(_BASE, 'cache', 'npc_knowledge.json'), 'r', encoding='utf-8') as f:
        dados = json.load(f)
    dialogos = dados.get('dialogos', {})
    candidatos = []
    for keyword, respostas in dialogos.items():
        for resp in respostas:
            if isinstance(resp, list) and len(resp) >= 1:
                texto = resp[0]
                if isinstance(texto, str) and len(texto) > 10:
                    candidatos.append({'id': f'{keyword[:20]}_{len(candidatos)}',
                                       'texto': texto})
    return candidatos

def main():
    print('=' * 60)
    print('TESTE 3 — RETRIEVAL com Radar (busca em 13.751 dialogos)')
    print('=' * 60)

    t0 = time.time()
    print('Carregando dialogos...')
    candidatos = carregar_dialogos()
    print(f'  {len(candidatos)} dialogos carregados em {time.time()-t0:.1f}s')

    radar = RadarMCR()

    perguntas = [
        "I need a sword",
        "Can you help me find the dragon?",
        "What do you sell here?",
        "How much does this armor cost?",
        "Tell me about the quest",
        "I want to buy potions",
        "Where can I find orcs?",
        "Do you have a mission for me?",
        "I lost my shield in battle",
        "Welcome to the forge, traveler!",
    ]

    print('\nBUSCA POR ONDAS:')
    total_score = 0
    melhores = 0

    for pergunta in perguntas:
        t1 = time.time()
        resultados = radar.buscar(pergunta, candidatos)
        tempo = (time.time() - t1) * 1000

        if resultados:
            best = resultados[0]
            score = best['score']
            onda = best['onda']
            texto = best['texto'][:80]

            total_score += score
            if score > 0.3:
                melhores += 1
                marker = '✓'
            elif score > 0.1:
                marker = '~'
            else:
                marker = '✗'

            print(f'  {marker} [{onda:12s}] score={score:.3f} | "{pergunta[:40]:40s}"')
            print(f'     -> "{texto}"')
        else:
            print(f'  ✗ [SEM RESULTADO] "{pergunta[:40]}"')

    print(f'\n  Score medio: {total_score/len(perguntas):.3f}')
    print(f'  Resultados com score > 0.3: {melhores}/{len(perguntas)}')
    print(f'  Total candidatos indexados: {len(candidatos)}')

if __name__ == '__main__':
    main()
