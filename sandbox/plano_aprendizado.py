"""
Plano de Aprendizado Massivo para MCR-DevIA
Fontes: documentacao, GitHub, referencias tecnicas
Meta: "20 anos de experiencia" em codigo
"""
import json, time, os

fontes = {
    "python": [
        {"url": "https://docs.python.org/3/tutorial/index.html", "tipo": "tutorial", "peso": 10},
        {"url": "https://docs.python.org/3/library/index.html", "tipo": "referencia", "peso": 10},
        {"url": "https://github.com/vinta/awesome-python", "tipo": "awesome_list", "peso": 5},
    ],
    "lua": [
        {"url": "https://www.lua.org/manual/5.4/", "tipo": "referencia", "peso": 10},
        {"url": "https://github.com/LewisJEllis/awesome-lua", "tipo": "awesome_list", "peso": 5},
    ],
    "cpp": [
        {"url": "https://en.cppreference.com/w/", "tipo": "referencia", "peso": 10},
        {"url": "https://github.com/fffaraz/awesome-cpp", "tipo": "awesome_list", "peso": 5},
    ],
    "canary_tfs": [
        {"url": "https://github.com/opentibiabr/canary", "tipo": "github_repo", "peso": 10},
    ],
    "javascript": [
        {"url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "tipo": "guia", "peso": 8},
        {"url": "https://github.com/sorrycc/awesome-javascript", "tipo": "awesome_list", "peso": 5},
    ],
}

# Ordem de prioridade (mais importante primeiro)
prioridade = ["python", "lua", "cpp", "canary_tfs", "javascript"]

print("=" * 70)
print("PLANO DE APRENDIZADO MASSIVO — MCR-DevIA")
print("=" * 70)
print(f"""
Total de fontes: {sum(len(v) for v in fontes.values())}
Linguagens: {', '.join(fontes.keys())}

Fases:
  1. Python (biblioteca padrao + awesome list)
  2. Lua (manual oficial 5.4 + awesome list)
  3. C++ (cppreference + awesome list)
  4. Canary TFS (codigo fonte do servidor)
  5. JavaScript (MDN + awesome list)

Cada fase:
  1. webfetch <url> → baixa e filtra
  2. Context Infinity → fragmenta e indexa
  3. ensinar → registra no KG
  4. Repete para proxima pagina

Beneficio esperado:
  - Python: conhecer TODA a biblioteca padrao
  - Lua: dominar a linguagem do servidor
  - C++: entender o codigo fonte do Canary
  - Canary: conhecer o projeto que ele trabalha
  - JS: frontend do OTClient
""")

for lang in prioridade:
    print(f"\n{'─'*50}")
    print(f"Linguagem: {lang.upper()} ({len(fontes[lang])} fontes)")
    print(f"{'─'*50}")
    for f in fontes[lang]:
        print(f"  [{f['peso']}/10] {f['tipo']:<15} {f['url'][:60]}...")
        print(f"         Comando: python mcr_devia.py webfetch \"{f['url']}\"")

print(f"\n\nPara comecar: python mcr_devia.py webfetch \"{fontes['python'][0]['url']}\"")
