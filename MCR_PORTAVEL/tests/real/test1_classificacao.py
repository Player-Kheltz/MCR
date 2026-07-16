"""
TESTE 1 — Qualidade da Classificacao Markoviana
Testa 50 frases reais de NPC, mede precisao da classificacao em 7 classes.
NENHUM RESULTADO HARDCODADO.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from mcr.mcr_unificado import MCRUnificado

# Frases de teste — TODAS sao frases reais de jogador/NPC
TESTES = [
    # saudacao
    ("Ola!", "saudacao"),
    ("Oi, tudo bem?", "saudacao"),
    ("Bom dia!", "saudacao"),
    ("Boa tarde, senhor!", "saudacao"),
    ("Hey!", "saudacao"),
    ("Salve, aventureiro!", "saudacao"),
    ("Hello there!", "saudacao"),
    # conversa
    ("Voce parece ocupado hoje", "conversa"),
    ("Que dia bonito para forjar", "conversa"),
    ("Ouvi falar que voce e o melhor ferreiro", "conversa"),
    ("Meu amigo recomendou sua forja", "conversa"),
    ("Estou so de passagem pela cidade", "conversa"),
    ("A cidade esta muito movimentada hoje", "conversa"),
    ("Vi um dragao ontem na floresta", "conversa"),
    ("Voce conhece bem essa regiao?", "conversa"),
    # criar_npc
    ("Crie um NPC ferreiro", "criar_npc"),
    ("Gere um guarda para a cidade", "criar_npc"),
    ("Preciso de um mercador novo", "criar_npc"),
    ("Crie um bibliotecario em Thais", "criar_npc"),
    ("Gere um NPC mago", "criar_npc"),
    ("Faca um NPC que vende pocoes", "criar_npc"),
    ("Crie um personagem ferreiro", "criar_npc"),
    # criar_codigo
    ("Crie um script Lua", "criar_codigo"),
    ("Gere codigo para teleporte", "criar_codigo"),
    ("Escreva uma funcao de cura", "criar_codigo"),
    ("Crie um sistema de loot", "criar_codigo"),
    ("Gere uma query SQL", "criar_codigo"),
    ("Crie um script de quest", "criar_codigo"),
    ("Implemente um comando de administrador", "criar_codigo"),
    # criar_ideia
    ("Crie uma ideia nova para o jogo", "criar_ideia"),
    ("E se existisse uma arma que falasse?", "criar_ideia"),
    ("Invente uma nova magia", "criar_ideia"),
    ("Pense em algo que nunca foi feito no Tibia", "criar_ideia"),
    ("Quero uma ideia para um evento", "criar_ideia"),
    ("Crie algo inovador", "criar_ideia"),
    # raciocinio
    ("Quanto e 15 + 27?", "raciocinio"),
    ("Qual e maior: 100 ou 50?", "raciocinio"),
    ("Quanto e 300 menos 75?", "raciocinio"),
    ("Se A > B e B > C, entao A > C?", "raciocinio"),
    ("Quanto e 5 vezes 8?", "raciocinio"),
    # analise
    ("Analise este texto: O MCR usa Markov", "analise"),
    ("Explique o que e SPA", "analise"),
    ("Resuma a historia de Eridanus", "analise"),
    ("Analise o sistema de progressao", "analise"),
    ("Me explique como funciona o KG", "analise"),
    ("O que significa entropia de Shannon?", "analise"),
    ("Analise a arquitetura do servidor", "analise"),
]

def main():
    mcr = MCRUnificado()
    acertos = 0
    erros = 0
    matriz = {}  # esperado -> {predito: count}

    for frase, esperado in TESTES:
        r = mcr.processar(frase)
        predito = r['intencao']

        if esperado not in matriz:
            matriz[esperado] = {}
        if predito not in matriz[esperado]:
            matriz[esperado][predito] = 0
        matriz[esperado][predito] += 1

        if predito == esperado:
            acertos += 1
        else:
            erros += 1
            print(f'  ERR: "{frase}" esperado={esperado} predito={predito}')

    mcr.close()

    # Resultados
    precisao = acertos / len(TESTES) * 100
    print(f'\n  TOTAL: {len(TESTES)} testes')
    print(f'  ACERTOS: {acertos}')
    print(f'  ERROS: {erros}')
    print(f'  PRECISAO: {precisao:.1f}%')

    # Por classe
    print('\n  POR CLASSE:')
    for classe in sorted(matriz.keys()):
        total = sum(matriz[classe].values())
        certos = matriz[classe].get(classe, 0)
        pct = certos / total * 100 if total > 0 else 0
        erros_classe = [(k, v) for k, v in matriz[classe].items() if k != classe]
        erros_str = ', '.join(f'{k}={v}' for k, v in sorted(erros_classe, key=lambda x: -x[1])[:3])
        print(f'    {classe}: {certos}/{total} = {pct:.0f}%' + (f'  (erros: {erros_str})' if erros_str else ''))

    print(f'\n  RESULTADO: {precisao:.1f}% de precisao em {len(TESTES)} frases de teste')

if __name__ == '__main__':
    main()
