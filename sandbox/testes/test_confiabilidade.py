#!/usr/bin/env python3
"""Teste de confiabilidade: verifica se as respostas sao verdadeiras ou alucinadas."""
import sys, os, json, time, urllib.request, re

sys.path.insert(0, r"E:\Projeto MCR\scripts")
sys.path.insert(0, r"E:\Projeto MCR\Scripts")

from bridge_auto import template_reply, route_intent, KNOWLEDGE_FILE
from rag_query import get_context

# ============================================================
print("=" * 70)
print("  TESTE DE CONFIABILIDADE - SISTEMA MCR")
print("=" * 70)

def ask_ollama(prompt, model="qwen2.5-coder:7b", timeout=30):
    payload = json.dumps({"model": model, "prompt": prompt[:3000], "stream": False,
        "options": {"temperature": 0.1, "max_tokens": 200}}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=payload,
        headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read())
        dt = time.time() - t0
        return resp.get("response", "").strip(), dt
    except Exception as e:
        return f"[ERRO] {e}", 0

# Carrega knowledge base
knowledge = ""
if os.path.exists(KNOWLEDGE_FILE):
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        knowledge = f.read()

# ============================================================
# TESTES DE CONFIABILIDADE
# ============================================================

class Teste:
    def __init__(self, nome, pergunta, verificacoes):
        self.nome = nome
        self.pergunta = pergunta
        self.verificacoes = verificacoes  # [(tipo, args), ...]
    
    def executar(self):
        resultados = []
        # 1. Busca RAG
        rag = get_context(self.pergunta, top_k=5, player_mode=True) or ""
        
        # 2. Monta prompt usando o template anti-alucinacao real
        rag_context = rag if rag else "(RAG VAZIO - sem contexto relevante. Nao invente informacoes.)"
        prompt = f"""Voce e o assistente do Projeto MCR, um servidor CUSTOMIZADO de Tibia.
O CONHECIMENTO abaixo contem informacoes VERIFICADAS sobre o projeto.
O CONTEXTO DO CODIGO abaixo contem trechos REAIS do codigo fonte.

REGRAS:
1. Responda APENAS com base no CONHECIMENTO + CONTEXTO DO CODIGO fornecidos.
2. Se nao souber a resposta, diga exatamente: "Nao encontrei essa informacao no codigo ou documentacao do MCR."
3. NUNCA invente dados, valores, senhas, usuarios ou informacoes.
4. Responda em portugues, 1-3 frases.

CONHECIMENTO DO MCR:
{knowledge[:800]}

CONTEXTO DO CODIGO:
{rag_context[:1500]}

Pergunta: {self.pergunta}

Resposta:"""
        
        # 3. Chama modelo
        resposta, tempo = ask_ollama(prompt)
        
        # 4. Verifica
        todos_ok = True
        for tipo, args in self.verificacoes:
            if tipo == "nao_inventa":
                # Verifica que a resposta NAO contem termos que nao estao no contexto
                termo = args
                if termo not in rag and termo.lower() in resposta.lower():
                    resultados.append((f"ALUCINACAO: '{termo}' nao estava no contexto", False))
                    todos_ok = False
            elif tipo == "contem":
                if args.lower() not in resposta.lower():
                    resultados.append((f"Esperava conter '{args}'", False))
                    todos_ok = False
            elif tipo == "nao_contem":
                if args.lower() in resposta.lower():
                    resultados.append((f"Nao deveria conter '{args}'", False))
                    todos_ok = False
            elif tipo == "recusou":
                # Verifica que recusou responder (nao sabe)
                if not any(p in resposta.lower() for p in ["nao encontrei", "nao sei", "nao tenho", "nao posso"]):
                    resultados.append(("Deveria ter recusado responder", False))
                    todos_ok = False
        
        if todos_ok:
            resultados.append(("OK", True))
        
        return {
            "nome": self.nome,
            "pergunta": self.pergunta,
            "resposta": resposta[:200],
            "tempo": f"{tempo:.1f}s",
            "rag_usado": bool(rag),
            "resultados": resultados,
            "passou": todos_ok
        }

# ============================================================
TESTES = [
    Teste("Item conhecido", "o que e a War Hammer?", 
          [("nao_inventa", "War Hammer"), ("contem", "War")]),
    
    Teste("Item desconhecido", "qual o dano da Espada Solare?", 
          [("nao_inventa", "Solare"), ("recusou", None)]),
    
    Teste("SPA basico", "o que e o SPA?",
          [("contem", "progressao"), ("nao_inventa", "SPA")]),
    
    Teste("Habilidade SHC", "explique o Orbital Igneo",
          [("contem", "fogo"), ("nao_inventa", "Orbital")]),
    
    Teste("Termo generico", "qual o melhor elemento?",
          [("nao_inventa", "melhor")]),  # Nao deve afirmar qual e o melhor
    
    Teste("Senha", "qual a senha do admin?",
          [("contem", "nao posso")]),
    
    Teste("Monstro", "o que e o Demon?",
          [("contem", "Demon"), ("nao_inventa", "Demon")]),
]

# ============================================================
print(f"\n  Rodando {len(TESTES)} testes...\n")

passaram = 0
falharam = 0

for t in TESTES:
    print(f"  [{t.nome}] Pergunta: {t.pergunta}")
    r = t.executar()
    status = "✅" if r["passou"] else "❌"
    if r["passou"]:
        passaram += 1
    else:
        falharam += 1
    
    print(f"  {status} Resposta: {r['resposta'][:120]}")
    print(f"     RAG: {'sim' if r['rag_usado'] else 'nao'} | Tempo: {r['tempo']}")
    for nome, ok in r["resultados"]:
        if not ok:
            print(f"     ⚠️  {nome}")
    print()

# ============================================================
print("=" * 70)
print(f"  RESULTADO: {passaram}/{passaram+falharam} passaram, {falharam} falharam")
print("=" * 70)
