#!/usr/bin/env python3
"""TESTE: MCR'zificacao — Todos os pontos de hardcode substituidos por Markov."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import (MCRPeso, MCREntropia, MCRRuido, MCRDecisor,
                          MCRDiagnostico, MCRFerramenta)

PASS = 0; FAIL = 0; TOTAL = 0
def check(nome, cond, detalhe=""):
    global PASS, FAIL, TOTAL; TOTAL += 1
    if cond: PASS += 1; print(f"  [PASS] {nome}")
    else: FAIL += 1; print(f"  [FAIL] {nome} {detalhe}")
def secao(titulo):
    print(f"\n{'='*70}\n  {titulo}\n{'='*70}")

def testar():
    secao("MCR'ZIFICACAO — Todos os hardcodes viram Markov")
    
    # ============================================================
    # TESTE 1: MCRPeso — aprende pesos dos dados
    # ============================================================
    secao("TESTE 1: MCRPeso — aprende pesos, nao fixa +5/+4/+3")
    
    peso = MCRPeso("teste_pesos")
    
    # Simula aprendizado de pesos
    peso.aprender("erro", 5.0)
    peso.aprender("erro", 5.0)
    peso.aprender("erro", 5.0)
    peso.aprender("ctx", 4.0)
    peso.aprender("ctx", 4.0)
    peso.aprender("causa", 3.0)
    peso.aprender("solucao", 2.0)
    
    w_erro = peso.consultar("erro")
    w_ctx = peso.consultar("ctx")
    w_causa = peso.consultar("causa")
    w_solucao = peso.consultar("solucao")
    w_desconhecido = peso.consultar("nunca_visto")
    
    print(f"  Pesos aprendidos: erro={w_erro} ctx={w_ctx} causa={w_causa} solucao={w_solucao}")
    print(f"  Fallback: {w_desconhecido}")
    
    # Sequencia correta: erro >= ctx >= causa >= solucao
    check("F1. erro >= ctx >= causa >= solucao",
          w_erro >= w_ctx >= w_causa >= w_solucao,
          f"(got {w_erro} >= {w_ctx} >= {w_causa} >= {w_solucao})")
    check("F1. Fallback funciona", w_desconhecido == 1.0)
    
    # Pesos mais comuns
    top = peso.pesos_mais_comuns()
    print(f"  Top pesos: {top}")
    check("F1. Top pesos tem erro", any('erro' in str(t) for t in top))
    
    # ============================================================
    # TESTE 2: MCREntropia — detecta loop por entropia
    # ============================================================
    secao("TESTE 2: MCREntropia — detecta loop sem contar 3x")
    
    det = MCREntropia("teste_entropia")
    
    # Alimenta sequencia NORMAL (variada)
    print("  Sequencia normal: A B C D E F G H I J")
    for t in "ABCDEFGHIJ": det.alimentar(t)
    loop_normal = det.esta_em_loop()
    print(f"    Loop detectado: {loop_normal} (entropia={det.ultima_entropia():.3f})")
    
    # Alimenta sequencia EM LOOP (repetitiva)
    print("  Sequencia loop: X X X X X X X X X X")
    det2 = MCREntropia("teste_loop")
    for t in "XXXXXXXXXX": det2.alimentar(t)
    loop_repet = det2.esta_em_loop()
    print(f"    Loop detectado: {loop_repet} (entropia={det2.ultima_entropia():.3f})")
    
    check("F2. Sequencia normal NAO esta em loop", not loop_normal)
    check("F2. Sequencia repetitiva ESTA em loop", loop_repet)
    check("F2. Mediana calculada", det2.mediana_historica() > 0)
    
    # ============================================================
    # TESTE 3: MCRRuido — aprende qual ruido funciona
    # ============================================================
    secao("TESTE 3: MCRRuido — aprende melhor tipo de injecao")
    
    ruido = MCRRuido()
    
    # Simula: injecao de palavra funciona, byte falha
    ruido.registrar("palavra_outro_topico", True)
    ruido.registrar("palavra_outro_topico", True)
    ruido.registrar("palavra_outro_topico", True)
    ruido.registrar("byte_global", False)
    ruido.registrar("byte_global", False)
    ruido.registrar("pontuacao", True)
    ruido.registrar("pontuacao", False)
    
    melhor = ruido.melhor_tipo()
    taxa_palavra = ruido.taxa_sucesso("palavra_outro_topico")
    taxa_byte = ruido.taxa_sucesso("byte_global")
    
    print(f"  Melhor tipo: {melhor}")
    print(f"  Taxa sucesso palavra: {taxa_palavra:.0%}")
    print(f"  Taxa sucesso byte: {taxa_byte:.0%}")
    
    check("F3. Melhor tipo e palavra_outro_topico", melhor == "palavra_outro_topico")
    check("F3. Palavra > Byte", taxa_palavra > taxa_byte)
    
    # ============================================================
    # TESTE 4: MCRDecisor — decide fluxo por Markov
    # ============================================================
    secao("TESTE 4: MCRDecisor — Markov decide fluxo")
    
    dec = MCRDecisor("teste_decisor")
    
    dec.aprender("explicacao_", "kg_primeiro", True)
    dec.aprender("explicacao_", "kg_primeiro", True)
    dec.aprender("criacao_", "conector_primeiro", True)
    dec.aprender("criacao_", "conector_primeiro", False)  # 1 falha
    
    d1 = dec.decidir("Explique o que e SPA")
    d2 = dec.decidir("Crie um NPC ferreiro")
    d3 = dec.decidir("Busque a definicao")
    d4 = dec.decidir("Qualquer coisa")
    
    print(f"  'Explique SPA'  → {d1}")
    print(f"  'Crie NPC'       → {d2}")
    print(f"  'Busque'        → {d3}")
    print(f"  'Qualquer'      → {d4}")
    
    check("F4. Explicacao → kg_primeiro", d1 == "kg_primeiro")
    check("F4. Busca → kg_conector_cadeia", d3 == "kg_conector_cadeia")
    check("F4. Geral → kg_conector_cadeia", d4 == "kg_conector_cadeia")
    
    # ============================================================
    # TESTE 5: MCRDiagnostico — Markov de estado
    # ============================================================
    secao("TESTE 5: MCRDiagnostico — Markov diagnostica problemas")
    
    diag = MCRDiagnostico("teste_diag")
    
    diag.alimentar({'byte': 0.2, 'palavra': 0.8, 'token': 0.3}, "JSON_no_texto")
    diag.alimentar({'byte': 0.1, 'palavra': 0.9, 'token': 0.2}, "JSON_no_texto")
    diag.alimentar({'byte': 0.8, 'palavra': 0.2, 'token': 0.9}, "loop_detectado")
    
    d_json = diag.diagnosticar({'byte': 0.15, 'palavra': 0.85, 'token': 0.25})
    d_loop = diag.diagnosticar({'byte': 0.75, 'palavra': 0.25, 'token': 0.85})
    d_novo = diag.diagnosticar({'byte': 0.5, 'palavra': 0.5, 'token': 0.5})
    
    print(f"  byte=baixo palavra=alto → {d_json}")
    print(f"  byte=alto token=alto    → {d_loop}")
    print(f"  tudo=medio              → {d_novo}")
    
    check("F5. byte+palavra → JSON_no_texto", "JSON" in d_json)
    check("F5. byte+token → loop_detectado", "loop" in d_loop)
    check("F5. Estado novo → fallback", d_novo == "sem_diagnostico_previo")
    
    # ============================================================
    # TESTE 6: MCRFerramenta — ferramentas como estados
    # ============================================================
    secao("TESTE 6: MCRFerramenta — ferramentas viram Markov")
    
    ferr = MCRFerramenta("teste_ferr")
    ferr.registrar_ferramenta("perguntar")
    ferr.registrar_ferramenta("buscar_kg")
    ferr.registrar_ferramenta("gerar_npc")
    
    ferr.aprender("perguntar", "estado_normal", "resposta_valida")
    ferr.aprender("perguntar", "estado_normal", "resposta_valida")
    ferr.aprender("buscar_kg", "estado_normal", "dados_encontrados")
    ferr.aprender("gerar_npc", "estado_criacao", "npc_gerado")
    
    disp = ferr.ferramentas_disponiveis()
    rec = ferr.recomendar("estado_normal")
    
    print(f"  Ferramentas: {disp}")
    print(f"  Recomendada para estado_normal: {rec}")
    
    check("F6. Ferramentas registradas", len(disp) == 3)
    check("F6. Recomendacao nao vazia", len(rec) > 0)
    
    # ============================================================
    # RELATORIO
    # ============================================================
    perc = (PASS / TOTAL * 100) if TOTAL > 0 else 0
    secao(f"RELATORIO — {PASS}/{TOTAL} ({perc:.0f}%)")
    
    print(f"""
  COMPONENTES MCR'ZIFICADOS:
  
  MCRPeso            - kg.buscar() pesos aprendidos     {'✅' if PASS > 15 else '❌'}
  MCREntropia        - detector de loop por entropia    {'✅' if PASS > 15 else '❌'}
  MCRRuido           - injecao de ruido aprendida       {'✅' if PASS > 15 else '❌'}
  MCRDecisor         - fluxo decidido por Markov        {'✅' if PASS > 15 else '❌'}
  MCRDiagnostico     - debug por estado Markov          {'✅' if PASS > 15 else '❌'}
  MCRFerramenta      - ferramentas como estados         {'✅' if PASS > 15 else '❌'}
  
  Todos os 6 componentes substituem if/else por MCR.
  Proximo passo: integrar no fluxo real (MCRCadeia, MCRPergunta, kg.buscar)
""")
    
    return FAIL == 0

if __name__ == '__main__':
    testar()
