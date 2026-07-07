#!/usr/bin/env python3
"""Teste completo do MCR-DevIA Revived."""
import sys, os
sys.path.insert(0, '.')
sys.path.insert(0, os.path.join('.', '..', 'Projeto MCR', 'historia', 'scripts', 'mcr_devia'))

print("=" * 60)
print("MCR-DevIA Revived — Teste Completo")
print("=" * 60)

# 1. Import
from fix_mcr_devia_v2 import MCRDevIARevived
print("\n[OK] Import da bridge")

# 2. Inicializacao
revived = MCRDevIARevived()
print(f"[OK] Inicializado: {revived.decider.total} seeds")

# 3. Teste MarkovDecider
testes = {
    "criar_habilidade_spa": [
        "crie uma habilidade de fogo",
        "cria um skill de gelo pro dominio punho",
    ],
    "analisar_bug": [
        "encontre um crash no servidor",
        "ache bugs no spawn_manager.cpp",
    ],
    "explicar_conceito": [
        "explique o que e SPA",
        "como funciona o sistema de multi-piso",
    ],
    "ler_arquivo": [
        "leia o progresso.md",
        "mostre o config.lua",
    ],
    "criar_codigo": [
        "implemente um npc ferreiro",
        "crie um sistema de crafting",
    ],
}
print("\n--- MarkovDecider ---")
acertos = 0
total = 0
for classe_esperada, exemplos in testes.items():
    for exemplo in exemplos:
        classe_prevista, conf = revived.decider.classificar(exemplo)
        total += 1
        # Verifica se a classe prevista comeca com a mesma raiz da esperada
        raiz_esperada = classe_esperada.split('_')[0]
        raiz_prevista = classe_prevista.split('_')[0] if classe_prevista else ""
        correto = raiz_esperada == raiz_prevista
        if correto:
            acertos += 1
        status = "OK" if correto else "X"
        print(f"  [{status}] \"{exemplo[:40]:40s}\" -> {classe_prevista} ({conf:.2f})")
print(f"\n  Acurácia: {acertos}/{total} ({acertos/total*100:.0f}%)")

# 4. Teste MarkovRouter
print("\n--- MarkovRouter ---")
rotas_testadas = {
    "criar_habilidade_spa": 1.0,
    "analisar_bug": 0.6,
    "explicar_conceito": 0.9,
    "ler_arquivo": 0.8,
}
for classe, conf in rotas_testadas.items():
    acoes = revived.router.decidir(classe, conf)
    print(f"  [{classe} conf={conf}] -> {' → '.join(acoes)}")

# 5. Teste Radar
print("\n--- Radar ---")
for i in range(5):
    revived.radar.alimentar("cmd_read")
print(f"  Em loop apos 5x cmd_read? {revived.radar.em_loop()}")
alt = revived.radar.forcar_alternativa(["cmd_read", "cmd_grep", "llm_gerar"])
print(f"  Alternativa forcada: {alt}")

# 6. Teste AutorevisaoTracker
print("\n--- AutorevisaoTracker ---")
revived.autorevisao.registrar_doc("PERSONALIDADE.md", "secoes 1-5")
revived.autorevisao.registrar_doc("mcr_devia_v2.py")
revived.autorevisao.verificar_pilar(3, True, "nomes em PT-BR")
revived.autorevisao.verificar_pilar(4, True, "narrativa presente")
revived.autorevisao.aplicar_criterio(15, True, "encoding UTF-8/latin1")
revived.autorevisao.marcar_hipotese("KG pode estar vazio")
revived.autorevisao.registrar_modificacao("teste.lua")
rev = revived.autorevisao.gerar()
print(f"  Geracao: {len(rev)} chars")

# 7. Teste FeedbackFilter
print("\n--- FeedbackFilter ---")
ff = revived.filter
print(f"  Resposta valida (tamanho): {ff.filtrar('pergunta', 'resposta com mais de 20 caracteres para teste', 0.8)}")
print(f"  Resposta invalida (curta):  {ff.filtrar('pergunta', 'sim', 0.8)}")
print(f"  Resposta invalida (vazia):  {ff.filtrar('pergunta', '', 0.8)}")
print(f"  Stats: {ff.stats()}")

# 8. Teste EncodingDetector
print("\n--- EncodingDetector ---")
from EncodingDetector import detectar_encoding
print(f"  habilidade.lua -> {detectar_encoding('habilidade.lua')}")
print(f"  server.cpp -> {detectar_encoding('server.cpp')}")
print(f"  main.cs -> {detectar_encoding('main.cs')}")
print(f"  script.go -> {detectar_encoding('script.go')}")
print(f"  README.md -> {detectar_encoding('README.md')}")

# 9. Teste TemplateExtractor
print("\n--- TemplateExtractor ---")
from TemplateExtractor import extrair_template
template, gaps = extrair_template('''HABILIDADES[1] = {
    nome = "Rajada de Fogo",
    tipo = "gatilho",
    cooldown = 6,
    categoria = "aoe",
    cor = COR.DOM_MAGIA_FOGO,
    efeitoConfig = {
        tipo = "rajada",
        percentual = 0.18,
        elemento = COMBAT_FIREDAMAGE,
    },
}''')
print(f"  Template extraido: {len(template)} chars, {len(gaps)} gaps: {gaps}")

# 10. Teste DeterministicFiller
print("\n--- DeterministicFiller ---")
from DeterministicFiller import preencher_gap, preencher_template
print(f"  Dominio 23 -> cor: {preencher_gap('cor_dominio', {'dominio_id': '23'})}")
print(f"  Tipo rajada -> categoria: {preencher_gap('categoria_habilidade', {'tipo_efeito': 'rajada'})}")
print(f"  Dominio 24 -> elemento: {preencher_gap('elemento_dano', {'dominio_id': '24'})}")

print("\n" + "=" * 60)
print("Teste concluido!")
print("=" * 60)
