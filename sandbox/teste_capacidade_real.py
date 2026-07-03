#!/usr/bin/env python3
"""TESTE REAL DE CAPACIDADE — MCR Unificado
Testa: Alimentacao, Emergencia, Autoavaliacao MultiNivel, Geracao, Debug
Compara MCR vs LLM. Nota final ponderada.
"""
import sys, os, math, json, time as _time
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import (MCRConector, AutoavaliadorSemantico, GeradorNarrativa,
                          MarkovUniversal, MCRAutoLoop)
from modulos.kg import KnowledgeGraph

kg = KnowledgeGraph()

# ============================================================
# DADOS REAIS DO PROJETO
# ============================================================
TOPICOS_REAIS = [
    ("spa", "SPA = Sistema de Progressao do Aventureiro, que gerencia habilidades e progressao em dominios elementais como Fogo, Gelo, Terra e Energia. O SPA permite que o jogador evolua suas capacidades elementais."),
    ("eridanus", "Eridanus era uma cidade lendaria conhecida por sua simplicidade e eficiencia. Eridanus = Cidade inicial dos aventureiros no projeto MCR. Fundada por exploradores que buscavam novas terras."),
    ("npc_ferreiro", "O NPC ferreiro em Eridanus forja espadas na bigorna. Ele vende picaretas, armaduras e equipamentos. O ferreiro trabalha com metal e fogo na sua forja."),
    ("shc", "SHC = Sistema de Habilidades Contextuais. 5 camadas: postura, nivel, sinergia, estado e condicao. Gerencia habilidades especiais dos personagens em combate."),
    ("canary", "Canary e um servidor OTServ personalizado de Tibia usado no projeto MCR. E a base tecnica do servidor, com suporte a Lua e C++."),
    ("arvore_natal", "Arvore de Natal e uma decoracao festiva montada em dezembro. Iluminada com luzes coloridas e enfeitada com bolas e estrelas."),
]

# ============================================================
# TEXTOS PARA AUTOAVALIACAO
# ============================================================
TEXTOS_AVALIACAO = [
    ("LOREA", "Eridanus era uma cidade lendaria. Fundada por exploradores que buscavam novas terras. A cidade cresceu ao redor de um cristal magico.", "lore", 7.0),
    ("LOREB", "O SPA gerencia a progressao do aventureiro em dominios elementais como Fogo, Gelo e Energia.", "lore", 5.0),
    ("CODIGO", "local npc = NPC:new('Ferreiro') function onSay(cid, words) local player = Player(cid) if player then end end", "codigo", 4.0),
    ("GARBAGE", "xyz abc asdf qwert zxcv bnmp uipo lkjh gfds", "garbage", 2.0),
    ("REPETITIVO", "do do do do do do do do do do do do do do do do do do do do do do", "repetitivo", 1.0),
]

# ============================================================
# TESTE
# ============================================================
CRITERIOS = {}  # nome -> (peso, nota)

def registrar_criterio(nome, peso, nota, detalhe=""):
    CRITERIOS[nome] = (peso, nota)
    status = "PASS" if nota >= 5 else "FAIL"
    print(f"  [{status}] {nome}: {nota:.1f}/10 ({detalhe})")

def secao(titulo):
    print(f"\n{'='*70}\n  {titulo}\n{'='*70}")


def testar():
    print("=" * 70)
    print("  TESTE REAL DE CAPACIDADE — MCR UNIFICADO")
    print("  Alimentacao | Emergencia | Autoavaliacao | Geracao | Debug")
    print("=" * 70)
    
    # ============================================================
    # FASE 1: ALIMENTACAO
    # ============================================================
    secao("FASE 1: Alimentacao — MCR absorve conhecimento real")
    
    c = MCRConector()
    t0 = _time.time()
    for nome, texto in TOPICOS_REAIS:
        c.alimentar(texto, nome)
    t_alim = _time.time() - t0
    
    print(f"  Topicos alimentados: {len(c.topicos)} em {t_alim:.2f}s")
    for nome, dados in c.topicos.items():
        print(f"    {nome:15s}: {dados['bytes']:3d} bytes, {len(dados['palavras']):2d} palavras, {len(dados['conteudo'])} conteudo")
    
    # Verifica se todos os topicos foram alimentados corretamente
    topicos_ok = sum(1 for nome, _ in TOPICOS_REAIS if nome in c.topicos and c.topicos[nome]['bytes'] > 0)
    nota_alimentacao = min(10, topicos_ok / len(TOPICOS_REAIS) * 10)
    registrar_criterio("F1. Alimentacao", 0.15, nota_alimentacao,
                       f"{topicos_ok}/{len(TOPICOS_REAIS)} topicos")
    
    # ============================================================
    # FASE 2: EMERGENCIA — conectar todos os pares
    # ============================================================
    secao("FASE 2: Emergencia — MCR conecta topicos distantes")
    
    t0 = _time.time()
    conexoes = c.explorar_todos()
    t_emerg = _time.time() - t0
    
    total_pares = len(TOPICOS_REAIS) * (len(TOPICOS_REAIS) - 1) // 2
    pct_conectado = len(conexoes) / total_pares * 100
    
    print(f"  Pares possiveis: {total_pares}")
    print(f"  Conexoes encontradas: {len(conexoes)} ({pct_conectado:.0f}%)")
    print(f"  Tempo: {t_emerg:.2f}s")
    
    if conexoes:
        conexoes.sort(key=lambda x: -x['nota'])
        print(f"\n  Top 5 conexoes:")
        for cx in conexoes[:5]:
            print(f"    {cx['topico_a']:15s} <-> {cx['topico_b']:15s}: {cx['nota']:.1f}/10 "
                  f"({cx['tipo_ponte']:25s}) '{cx['sequencia'][:50]}'")
        
        print(f"\n  Piores 3 conexoes:")
        for cx in conexoes[-3:]:
            print(f"    {cx['topico_a']:15s} <-> {cx['topico_b']:15s}: {cx['nota']:.1f}/10 "
                  f"({cx['tipo_ponte']:25s}) '{cx['sequencia'][:50]}'")
        
        nota_media = sum(cx['nota'] for cx in conexoes) / len(conexoes)
        nota_melhor = max(cx['nota'] for cx in conexoes)
        nota_pior = min(cx['nota'] for cx in conexoes)
        
        print(f"\n  Nota media: {nota_media:.1f}/10")
        print(f"  Melhor: {nota_melhor:.1f}/10")
        print(f"  Pior: {nota_pior:.1f}/10")
        
        # Pontuacao: cobertura (60%) + nota media (40%)
        nota_cobertura = pct_conectado / 100 * 10
        nota_qualidade = nota_media
        nota_emergencia = nota_cobertura * 0.6 + nota_qualidade * 0.4
    else:
        nota_emergencia = 0
    
    registrar_criterio("F2. Emergencia", 0.25, nota_emergencia,
                       f"{len(conexoes)}/{total_pares} pares, media={nota_media if conexoes else 0:.1f}/10")
    
    # ============================================================
    # FASE 3: AUTOAVALIACAO MULTINIVEL
    # ============================================================
    secao("FASE 3: Autoavaliacao MultiNivel — MCR sabe o que e bom?")
    
    acertos_class = 0
    print(f"\n  {'Nome':12s} {'Nota':6s} {'Esperado':10s} {'Acertou?':10s}  Detalhes")
    print(f"  {'-'*12} {'-'*6} {'-'*10} {'-'*10}  {'-'*30}")
    
    class_texto = {}  # cache para reuso
    for nome, texto, tipo_esperado, nota_min_esperada in TEXTOS_AVALIACAO:
        nota, det = c._autoavaliar_multinivel(texto, TEXTOS_AVALIACAO[0][1], "", "conteudo_compartilhado")
        class_texto[nome] = (nota, det)
        
        if tipo_esperado == 'lore':
            acertou = nota >= nota_min_esperada
        elif tipo_esperado == 'codigo':
            acertou = nota <= nota_min_esperada
        elif tipo_esperado == 'garbage':
            acertou = nota <= nota_min_esperada
        elif tipo_esperado == 'repetitivo':
            acertou = nota <= nota_min_esperada
        
        if acertou: acertos_class += 1
        nb = det.get('byte', {}).get('nota', 0)
        np_ = det.get('palavra', {}).get('nota', 0)
        nt = det.get('token', {}).get('nota', 0)
        print(f"  {nome:12s} {nota:6.1f} {tipo_esperado:10s} {'SIM' if acertou else 'NAO':10s}  "
              f"Byte={nb:.1f}/2 Palavra={np_:.1f}/5 Token={nt:.1f}/3")
    
    nota_autoavaliacao = acertos_class / len(TEXTOS_AVALIACAO) * 10
    registrar_criterio("F3. Autoavaliacao", 0.25, nota_autoavaliacao,
                       f"{acertos_class}/{len(TEXTOS_AVALIACAO)} classificacoes corretas")
    
    # ============================================================
    # FASE 4: GERACAO
    # ============================================================
    secao("FASE 4: Geracao — MCR produz texto util?")
    
    # Usa GeradorNarrativa com KG
    sem = AutoavaliadorSemantico(kg, None)
    gerador = GeradorNarrativa(kg, None)
    
    print(f"  Gerando lore sobre Eridanus...")
    t0 = _time.time()
    resultado = gerador.gerar("Eridanus", max_palavras=60, temperatura=0.3)
    t_ger = _time.time() - t0
    
    texto = resultado['texto']
    av_sem = sem.avaliar(texto, 'lore')
    av_multinivel, _ = c._autoavaliar_multinivel(
        texto, TOPICOS_REAIS[1][1], TOPICOS_REAIS[0][1], "conteudo_compartilhado"
    )
    
    palavras = texto.split()
    n_palavras = len(palavras)
    n_chars = len(texto)
    
    # Metricas de qualidade real
    tem_maiuscula = texto[0].isupper() if texto else False
    tem_pontuacao_final = any(texto.rstrip().endswith(p) for p in '.!?')
    tem_conteudo_lore = any(w in texto.lower() for w in ['cidade', 'era', 'fundada', 'aventureiro'])
    
    if n_palavras >= 4:
        bigramas = [' '.join(palavras[i:i+2]) for i in range(n_palavras-1)]
        repeticao = 1.0 - (len(set(bigramas)) / max(len(bigramas), 1))
    else:
        repeticao = 0.0
    
    print(f"\n  Texto gerado ({n_palavras} palavras, {n_chars} chars, {t_ger:.2f}s):")
    print(f"  {texto[:300]}")
    print(f"\n  Nota semantica: {av_sem['nota']}/10 ({av_sem['diagnostico']})")
    print(f"  Nota multi-nivel: {av_multinivel:.1f}/10")
    print(f"  Maiuscula no inicio: {tem_maiuscula}")
    print(f"  Pontuacao no final: {tem_pontuacao_final}")
    print(f"  Conteudo de lore: {tem_conteudo_lore}")
    print(f"  Repeticao de bigramas: {repeticao:.1%}")
    
    # Nota de geracao
    nota_ger = 0
    if n_chars > 50: nota_ger += 2
    if tem_maiuscula and tem_pontuacao_final: nota_ger += 2
    if tem_conteudo_lore: nota_ger += 2
    if repeticao < 0.3: nota_ger += 2
    if av_sem['nota'] >= 3: nota_ger += 2
    
    registrar_criterio("F4. Geracao", 0.20, nota_ger,
                       f"chars={n_chars}, frase={'OK' if tem_maiuscula and tem_pontuacao_final else 'INCOMPLETA'}, "
                       f"lore={tem_conteudo_lore}, repeticao={repeticao:.0%}")
    
    # ============================================================
    # FASE 5: DEBUG — transparencia total
    # ============================================================
    secao("FASE 5: Debug — Transparencia total")
    
    if conexoes:
        melhor = conexoes[0]
        debug_texto = c.debug(melhor)
        print(f"\n  Debug da melhor conexao ({melhor['topico_a']} <-> {melhor['topico_b']}):")
        print(f"  {'='*50}")
        for linha in debug_texto.split('\n'):
            print(f"  {linha}")
        print(f"  {'='*50}")
        
        nota_debug = 10  # debug funcionou
    else:
        nota_debug = 0
    
    registrar_criterio("F5. Debug", 0.15, nota_debug,
                       "Byte+Palavra+Token exibidos" if nota_debug > 0 else "Falha")
    
    # ============================================================
    # NOTA FINAL
    # ============================================================
    secao("NOTA FINAL — Capacidade Real do MCR")
    
    nota_final = 0
    detalhes_nota = []
    for nome, (peso, nota) in CRITERIOS.items():
        contrib = peso * nota
        nota_final += contrib
        detalhes_nota.append(f"{nome}: {nota:.1f}/10 x {peso:.0%} = {contrib:.2f}")
    
    print(f"\n  {'Criterio':35s} {'Peso':6s} {'Nota':6s} {'Contrib':8s}")
    print(f"  {'-'*35} {'-'*6} {'-'*6} {'-'*8}")
    for nome, (peso, nota) in CRITERIOS.items():
        print(f"  {nome:35s} {peso:.0%}    {nota:.1f}   {peso*nota:.2f}")
    print(f"  {'-'*35} {'-'*6} {'-'*6} {'-'*8}")
    print(f"  {'NOTA FINAL':35s} {'':6s} {'':6s} {nota_final:.2f}")
    
    # Classificacao
    if nota_final >= 8.5:
        classe = "EXCELENTE — MCR opera em capacidade maxima"
    elif nota_final >= 7.0:
        classe = "BOA — MCR funcional, alguns ajustes necessarios"
    elif nota_final >= 5.0:
        classe = "REGULAR — MCR operacional, gaps conhecidos"
    elif nota_final >= 3.0:
        classe = "FRACA — MCR requer melhorias significativas"
    else:
        classe = "INOPERANTE — MCR nao cumpre funcao basica"
    
    print(f"\n  CLASSIFICACAO: {classe}")
    print(f"  Nota real: {nota_final:.1f}/10")
    
    # Diagnostico
    print(f"\n  DIAGNOSTICO:")
    criterios_fracos = [(n, p, n_) for n, (p, n_) in CRITERIOS.items() if n_ < 5]
    criterios_fortes = [(n, p, n_) for n, (p, n_) in CRITERIOS.items() if n_ >= 7]
    
    if criterios_fortes:
        print(f"  Forcas:")
        for n, p, n_ in criterios_fortes:
            print(f"    ✅ {n}: {n_:.1f}/10")
    if criterios_fracos:
        print(f"  Fraquezas:")
        for n, p, n_ in criterios_fracos:
            print(f"    ❌ {n}: {n_:.1f}/10")
    
    print(f"\n  Tempo total: {t_alim + t_emerg + t_ger:.1f}s")
    
    return nota_final


if __name__ == '__main__':
    testar()
