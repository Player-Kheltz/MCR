"""VEREDITO FINAL - MCR-DevIA vs Cloud 70B"""
import json

veredito = """
╔══════════════════════════════════════════════════════════════════╗
║              VEREDITO FINAL: MCR-DevIA vs Cloud 70B            ║
╚══════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────┐
│ RESULTADO CARGO A CARGO                                         │
├─────────────────────────────────────────────────────────────────┤

 CARGO: fast (classificacao SIM/NAO) ── modelo: qwen2.5-coder:1.5b
   Pergunta: "Runa de Energia article='um' esta correto?"
   
   MCR-DevIA: "SIM"  ❌ (errado, deveria ser NAO)
   Cloud 70B: "SIM"  ❌ (errado, mesmo modelo)
   
   ▶ EMPATE. Ambos erraram. Modelo 1.5b nao entende genero PT-BR.
   │
   │ SOLUCAO: Para PT-BR, usar llama3.1:8b em vez de 1.5b
   │

 CARGO: analisar (codigo c/ linha numerada) ── modelo: qwen2.5-coder:7b + AST
   Arquivo: main.lua (68 linhas, 3 problemas + 2 falsas pistas)
   
   MCR-DevIA: "LINHA 17: runa nao consumida"
              "LINHA 45: linha comentada"
              "LINHA 64: getArtigo() com param extra"  ✅ 3/3
   
   Cloud 70B: "LINHA 20: runa nao consumida"
              "LINHA 34: getArtigo() com param extra"  ✅ 2/3 (menos detalhado)
   
   ▶ MCR-DevIA GANHA. AST + linha numerada > resposta generica.
   │
   │ O comando 'analisar' foi o grande acerto desta sessao.
   │ Com AST pre-analysis, encontrou mais problemas que Cloud.
   │

 CARGO: contexto (pergunta projeto) ── modelo: llama3.1:8b + KG
   Pergunta: "O que e SHC no projeto MCR?"
   
   MCR-DevIA: "Server Handler Class"  ❌ ALUCINOU!
   Cloud 70B: "Sistema de Habilidades Contextuais"  ✅ Correto
   
   ▶ Cloud GANHA. MCR-DevIA alucinou porque KG nao tinha lesson sobre SHC.
   │
   │ GAP CRITICO: Filtro de genericidade nota 62/100 (passou!)
   │ mas resposta estava ERRADA. Precisamos de filtro de VERACIDADE.
   │

 CARGO: raciocinio (debug) ── modelo: deepseek-r1:7b + KG
   Problema: items[3] nil value (for i=1,3 so tem 2 itens)
   
   MCR-DevIA: "Nao pode usar chaves {} em Lua"  ❌ ALUCINOU!
   Cloud 70B: "items[3] nao existe, loop vai ate 3"  ✅ Correto
   
   ▶ Cloud GANHA. deepseek-r1:7b gerou thinking tokens errados.
   │
   │ GAP: deepseek-r1:7b e imprevisivel. Thinking mode pode
   │ levar a conclusoes ERRADAS mas confiantes.
   │

├─────────────────────────────────────────────────────────────────┤
│ PLACAR FINAL                                                     │
├─────────────────────────────────────────────────────────────────┤

   Cargo              |  MCR-DevIA     |  Cloud 70B      | Vencedor
   -------------------|----------------|-----------------|---------
   fast (1.5b)        |  ERROU         |  ERROU          | EMPATE
   analisar (coder7b) |  3/3 + linha   |  2/3 generico   | MCR 🏆
   contexto (llama8b) |  ALUCINOU      |  ACERTOU        | Cloud 🏆
   raciocinio (ds7b)  |  ALUCINOU      |  ACERTOU        | Cloud 🏆
   
   PLACAR: Cloud 2 x 1 MCR-DevIA (1 empate)

├─────────────────────────────────────────────────────────────────┤
│ DIAGNOSTICO                                                      │
├─────────────────────────────────────────────────────────────────┤

 [+] ONDE MCR-DevIA VENCE:
    -> analisar com AST + linha numerada (comando novo)
    -> Pipeline de extracao/revisao/aplicacao (extract + review)
    -> Super Fragmentador para dados grandes
    -> Cache de decisoes (52x mais rapido na 2a vez)

 [-] ONDE MCR-DevIA PERDE (gaps):
    -> Filtro de genericidade NAO verifica VERACIDADE
       ("Server Handler Class" passou com nota 62!)
    -> deepseek-r1:7b e imprevisivel (pode alucinar mesmo pensando)
    -> KG sem contexto de dominio = alucinacao garantida
       (se nao tem lesson sobre SHC, inventa)

 [!] PROBLEMA CRITICO DESCOBERTO:
    O filtro de genericidade so avalia se a resposta parece
    especifica, nao se ela e VERDADEIRA. Precisamos de um
    filtro de VERACIDADE que cruze a resposta com o KG.
    
    Ex: Resposta disse "Server Handler Class"
    -> Verificar no KG: tem lesson sobre SHC?
    -> Se nao tem: resposta e INVENTADA -> NOTA 0

├─────────────────────────────────────────────────────────────────┤
│ RECOMENDACOES                                                     │
├─────────────────────────────────────────────────────────────────┤

 1. ADICIONAR filtro de VERACIDADE (nao so genericidade)
    - Antes de aceitar resposta, verificar se o conteudo
      existe no KG ou no codigo do projeto
    - Se IA inventou termo que nao existe -> NOTA 0

 2. deepseek-r1:7b para RACIOCINIO e ARRISCADO
    - Thinking mode pode gerar raciocinios errados
    - Usar apenas para tarefas com verificacao via AST/codigo
    - Nunca para perguntas conceituais (contexto)

 3. Alimentar KG com dominio do projeto MCR
    - SHC, SPA, Dominios, Eridanus, etc.
    - Extrair de docs/MCR para lessons no KG

└─────────────────────────────────────────────────────────────────┘
"""

print(veredito)

# Salvar
kg_path = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
kg = json.load(open(kg_path, "r", encoding="utf-8"))
kg["licoes"].append({
    "id": f"L{len(kg['licoes'])+1:03d}",
    "erro": "Filtro de genericidade nao verifica veracidade - SHC alucinado",
    "causa": "deepseek-r1:7b inventou 'Server Handler Class' e filtro aprovou (nota 62)",
    "solucao": "Adicionar filtro de VERACIDADE que cruza resposta com KG antes de aceitar. Exercito: se IA menciona termo que nao existe no KG, nota 0.",
    "ctx": "alucinacao"
})
json.dump(kg, open(kg_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"[OK] Lesson salva ({len(kg['licoes'])} total)")
