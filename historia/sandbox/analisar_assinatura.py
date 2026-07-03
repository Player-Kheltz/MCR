#!/usr/bin/env python3
"""Analisa banco de assinaturas para extrair padrao do usuario."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

# Carrega banco
with open(os.path.join(os.path.dirname(__file__), '..', 'sandbox', '.mcr_assinaturas.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== AUTORES NO BANCO ===")
for autor in sorted(data.keys()):
    n = len(data[autor])
    print(f"  {autor}: {n} assinaturas")

# Se existe 'usuario' ou 'Kheltz', mostra detalhes
for autor_alvo in ['usuario', 'Kheltz', 'autor_0']:
    if autor_alvo in data:
        ass = data[autor_alvo]
        print(f"\n=== {autor_alvo} ({len(ass)} assinaturas) ===")
        for i, a in enumerate(ass[-5:]):  # ultimas 5
            fp = a.get('fingerprint', [])
            print(f"  [{i}] ent={a.get('entropia',0):.3f} fp_len={len(fp)} fp_primeiros={fp[:5]}")

# Agora extrai a assinatura de mensagens REAIS do usuario desta conversa
# Vou usar as mensagens que o usuario digitou neste historico
mensagens_reais_usuario = [
    "Continue if you have next steps, or stop and ask for clarification if you are unsure how to proceed.",
    "Filtro lore vs técnico no MCRPergunta — prioriza conteúdo narrativo > ERRADO! MCR deve prioriar a ASSINATURA correta, Ex: já provamos que sabemos criar nomes novos, isso significa que: MCR é CAPAZ DE CRIAR! você não esta percebendo isso, devemos usar o mesmo conceito aqui! analisar o MCR (Markov, Padrão, intenção, a ASSINATURA) para PREDIZER o que deve vir depois, se o próprio MCR PERCEBER que NÃO SABE OU ENTRA EM LOOP ele DEVE IR ESTUDAR SOBRE O QUE FALTA, A ASSINATURA QUE FALTA QUE SE TRADUZ EM UMA PALAVRA OU FRASE DE WEBSEACH OU ESTUDO LOCAL, ENTENDE? ELE BUSCA PADRÕES NA ASSINATURA, JÁ TEMOS O RADAR PARA ISSO TAMBÉM!          releia o que falei acima ,entenda os conceitos, analise o MCR.py POR COMPLETO e reflita, O que ainda não esta MCR? o que ainda não segue padrões, intenções e etc, a ASSINATURA, o que ainda é Harcoded? o que precisa ser alterado de Hardcoded para Conceito MCR? o MCR sabe decidir melhor que ninguém o que fazer por que ele sabe analisar padrões, TODOS OS ERROS QUE ELE APRESENTA GAP E ETC SÃO HARDCODES QUE LIMITAM SEU POTENCIAL!            SOBRE O BANCO DE ASSINATURAS: NÃO FALSIFIQUE MINHA ASSINATURA, USE EXEMPLOS REAIS DA MINHA CONVERSA! VOCÊ SABE O PADRÃO TAMBÉM!",
    "TODOS, resolva TODOS, conecte TODOS!",
    "sobre o \"Banco de assinaturas → usuario aprendido com textos REAIS seus, conf=1.00\" os documentos todos foram escritos por IA, quem sabe como eu escrevo é você, cloud!, não sei se você tem dados suficientes MAS você pode olhar os históricos de nossas sessões para me ver digitando, entender meu padrão e adicionar a assinatura no MCR para ele sempre saber que eu sou eu. eu quero que isso seja A UNICA COISA HARDCODED NO MCR, ele deve SEMPRE SABER QUEM SOU EU, isso deve ser uma regra absoluta! (se você tiver dúvidas da minha assinatura, pode pedir pro MCR falar para você entregue para ele exemplos peça a assinatura, ou use as ferramentas dele para descobrir)"
]

from modulos.MCR import MCRSignature, MCRAssinatura

print("\n\n=== ASSINATURA DO USUARIO (textos REAIS) ===")
banco = MCRAssinatura()
for i, msg in enumerate(mensagens_reais_usuario):
    sig = MCRSignature.extrair(msg)
    banco.aprender(msg, 'usuario')
    print(f"\n  Mensagem {i+1}:")
    print(f"    entropia={sig['entropia']:.3f}")
    print(f"    estados={sig['estados']}")
    print(f"    transicoes={sig['transicoes']}")
    print(f"    fingerprint={sig['fingerprint'][:8]}")
    print(f"    primeiros_bytes={list(msg.encode('utf-8')[:10])}")

# Testa identificacao
print("\n\n=== TESTE DE IDENTIFICACAO ===")
testes = [
    "releia o que falei acima, entenda os conceitos, analise o MCR.py POR COMPLETO",
    "isso e um teste generico qualquer sem o padrao do usuario",
]
for teste in testes:
    autor, conf, det = banco.identificar(teste)
    print(f"  '{teste[:40]}...' -> {autor} (conf={conf:.2f})")
    # Filtra so os mais provaveis
    tops = sorted(det.items(), key=lambda x: -x[1])[:5]
    print(f"    tops: {tops}")

# NOTA: Nao salvar em Plan Mode — a implementacao fara isso depois
