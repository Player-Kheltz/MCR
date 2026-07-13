"""
TESTE 3b — RETRIEVAL Rapido (amostra de 1000 dialogos)
"""
import sys, os, json, re, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from mcr.mcr_radar import RadarMCR

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')

def main():
    print('=' * 60)
    print('TESTE 3 — RETRIEVAL (amostra 1000 dialogos)')
    print('=' * 60)

    with open(os.path.join(_BASE, 'cache', 'npc_knowledge.json'), 'r', encoding='utf-8') as f:
        dados = json.load(f)
    dialogos = dados.get('dialogos', {})

    candidatos = []
    for keyword, respostas in dialogos.items():
        for resp in respostas[:1]:  # so primeira resposta por keyword
            if isinstance(resp, list) and len(resp) >= 1:
                texto = resp[0]
                if isinstance(texto, str) and len(texto) > 10:
                    candidatos.append({'id': str(len(candidatos)), 'texto': texto})
        if len(candidatos) >= 2000:
            break

    print(f'  Candidatos: {len(candidatos)}')

    radar = RadarMCR()

    perguntas = [
        "I need a sword",
        "What do you sell here?",
        "How much does armor cost?",
        "Tell me about the quest",
        "I want to buy potions",
        "Where can I find orcs?",
        "Do you have a mission?",
        "Welcome to the forge!",
    ]

    print('\nRESULTADOS:')
    scores = []
    for pergunta in perguntas:
        t1 = time.time()
        resultados = radar.buscar(pergunta, candidatos)
        tempo = (time.time() - t1) * 1000

        if resultados:
            best = resultados[0]
            scores.append(best['score'])
            print(f'  [{best["onda"]:12s}] score={best["score"]:.3f}  tempo={tempo:.0f}ms')
            print(f'    Q: "{pergunta}"')
            print(f'    R: "{best["texto"][:80]}"')
        else:
            scores.append(0)
            print(f'  [SEM RESULTADO] "{pergunta}"')

    media = sum(scores) / len(scores)
    acima = sum(1 for s in scores if s > 0.2)
    print(f'\n  Score medio: {media:.3f}')
    print(f'  Score > 0.2: {acima}/{len(scores)}')
    print(f'  Cobertura: {acima/len(scores)*100:.0f}% das perguntas tem resposta relevante')

if __name__ == '__main__':
    main()
