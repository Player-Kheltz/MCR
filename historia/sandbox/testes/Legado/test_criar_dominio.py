#!/usr/bin/env python3
"""
Simulacao completa de criacao de um novo dominio usando modelos locais.
Testa: plan (arquitetura) -> dev (habilidades) -> docs (identidade) -> review (revisao)
"""
import json, os, sys, time, urllib.request

BASE = r"E:\Projeto MCR"
SAIDA = os.path.join(BASE, "sandbox", "test_domain_simulation")
os.makedirs(SAIDA, exist_ok=True)
sys.path.insert(0, os.path.join(BASE, "scripts"))

HISTORICO = []

def chat(modelo, messages, max_tokens=1024, temp=0.1):
    payload = json.dumps({"model": modelo, "messages": messages, "stream": False,
        "options": {"temperature": temp, "max_tokens": max_tokens}}).encode()
    t0 = time.time()
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        dt = time.time() - t0
        return data["message"]["content"], dt
    except Exception as e:
        return f"[ERRO] {e}", time.time() - t0

def chamar(agente, modelo, system, prompt, max_tokens=1024, temp=0.1):
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    resp, tempo = chat(modelo, messages, max_tokens, temp)
    
    # Carrega o MCR_IDENTITY para contexto
    try:
        with open(os.path.join(BASE, "docs", "MCR_IDENTITY.md")) as f:
            ident = f.read()
    except:
        ident = ""
    
    HISTORICO.append({
        "agente": agente, "modelo": modelo,
        "system": system, "prompt": prompt,
        "resposta": resp, "tempo": round(tempo, 1),
        "tamanho": len(resp)
    })
    status = "OK" if len(resp) > 50 else "ERRO"
    print(f"\n  {'='*70}")
    print(f"  {agente.upper()} ({modelo}) - {tempo:.1f}s - {len(resp)} chars [{status}]")
    print(f"  {'='*70}")
    print(f"  >>> SOLICITACAO: {prompt[:200]}...")
    print(f"  >>> RESPOSTA:\n{resp[:500]}")
    return resp, tempo

# ============================================
# Carrega contexto MCR para injetar nos sistemas
# ============================================
try:
    with open(os.path.join(BASE, "docs", "MCR_IDENTITY.md")) as f:
        MCR_CTX = f.read()
except:
    MCR_CTX = ""

print("=" * 80)
print("  SIMULACAO: CRIACAO DE NOVO DOMINIO (CRISTAL - ID 27)")
print("  Pipeline: PLAN -> DEV -> DOCS -> REVIEW")
print("=" * 80)

# ============================================
# PASSO 1: PLAN - Arquitetar o dominio
# ============================================
print("\n\n" + "=" * 80)
print("  PASSO 1/4: PLAN - ARQUITETAR DOMINIO")
print(f"  Modelo: deepseek-r1:8b")
print("=" * 80)

SYS_PLAN = f"""Voce e um arquiteto de game design para o Projeto MCR.

{MCR_CTX}

Crie um novo dominio elemental para o SPA seguindo a estrutura existente (Fogo 23, Gelo 24, Terra 25, Energia 26).
O novo dominio sera CRISTAL (ID 27), sobre elementos cristalinos/gemas.

Defina:
1. Essencia (sentimento, 3 adjetivos, frase de assinatura)
2. Comportamento de combate (forca, fraqueza)
3. 4 pacotes tematicos de habilidades (2-3 habilidades cada)
4. Sinergias com outros dominios (Fogo, Gelo, Terra, Energia)
5. Identidade visual (efeitos CONST_ME_*)
6. Nicho principal (o que SOH CRISTAL faz, que outros nao fazem)"""

r_plan, t_plan = chamar("plan", "deepseek-r1:8b", SYS_PLAN,
    "Projete o dominio CRISTAL (ID 27) para o SPA do MCR. "
    "Siga a estrutura de identidade de dominios: essencia, combate, pacotes, sinergias, visuais, nicho.", 2048, 0.2)

with open(os.path.join(SAIDA, "01_plan_arquitetura.txt"), "w", encoding="utf-8") as f:
    f.write(f"# PLAN - Arquitetura do Dominio CRISTAL\n# Modelo: deepseek-r1:8b\n# Tempo: {t_plan}s\n\n{r_plan}")

# ============================================
# PASSO 2: DEV - Criar habilidades
# ============================================
print("\n\n" + "=" * 80)
print("  PASSO 2/4: DEV - CRIAR HABILIDADES")
print(f"  Modelo: qwen2.5-coder:7b")
print("=" * 80)

SYS_DEV = f"""Voce e um desenvolvedor de game design para o Projeto MCR.

{MCR_CTX}

Crie habilidades SHC (5 camadas) para o dominio CRISTAL.
Cada habilidade deve ter: efeitoConfig BASE, e opcionalmente postura, niveis, sinergias, estados, condicoes.

Use IDs: 27001-27020. Use COMBAT_ENERGYDAMAGE como elemento.
Formato Lua: HABILIDADES[27001] = {{ nome = "", tipo = "gatilho", dominio = {{27}}, ... }}"""

r_dev, t_dev = chamar("dev", "qwen2.5-coder:7b", SYS_DEV,
    "Crie 6 habilidades SHC para o dominio CRISTAL (ID 27). "
    "Siga o formato HABILIDADES[ID] = {nome, tipo, dominio, efeitoConfig} com 5 camadas (postura, niveis, sinergias, estados, condicoes). "
    "IDs: 27001 a 27006. Use COMBAT_ENERGYDAMAGE.", 2048, 0.1)

with open(os.path.join(SAIDA, "02_dev_habilidades.txt"), "w", encoding="utf-8") as f:
    f.write(f"# DEV - Habilidades CRISTAL\n# Modelo: qwen2.5-coder:7b\n# Tempo: {t_dev}s\n\n{r_dev}")

# ============================================
# PASSO 3: DOCS - Documentar identidade
# ============================================
print("\n\n" + "=" * 80)
print("  PASSO 3/4: DOCS - DOCUMENTAR IDENTIDADE")
print(f"  Modelo: qwen2.5-coder:7b")
print("=" * 80)

SYS_DOCS = f"""Voce e um designer narrativo para o Projeto MCR.

{MCR_CTX}

Crie o documento de identidade do dominio CRISTAL (ID 27) seguindo o formato dos dominios existentes.
Inclua: essencia, combate, percepcao do mundo, arquétipo do mestre, identidade visual, pacotes tematicos, sinergias."""

r_docs, t_docs = chamar("docs", "qwen2.5-coder:7b", SYS_DOCS,
    "Crie o documento de identidade completo para o dominio CRISTAL (ID 27) "
    "seguindo o formato usado nos documentos 23-FOGO.txt, 24-AGUA_GELO.txt do catalogo.", 1536, 0.1)

with open(os.path.join(SAIDA, "03_docs_identidade.txt"), "w", encoding="utf-8") as f:
    f.write(f"# DOCS - Identidade do Dominio CRISTAL\n# Modelo: qwen2.5-coder:7b\n# Tempo: {t_docs}s\n\n{r_docs}")

# ============================================
# PASSO 4: REVIEW - Revisar tudo
# ============================================
print("\n\n" + "=" * 80)
print("  PASSO 4/4: REVIEW - REVISAR PRODUCAO")
print(f"  Modelo: deepseek-r1:8b")
print("=" * 80)

SYS_REVIEW = f"""Voce e um revisor de game design para o Projeto MCR.

{MCR_CTX}

Revise o dominio CRISTAL recém-criado. Aponte:
1. O nicho dele e unico ou invade o de outro dominio?
2. As habilidades seguem o formato SHC?
3. As sinergias fazem sentido?
4. Recomendacoes para melhoria"""

r_review, t_review = chamar("review", "deepseek-r1:8b", SYS_REVIEW,
    f"Revise todo o dominio CRISTAL (ID 27). "
    f"Contexto planejado:\n{r_plan[:1500]}\n\n"
    f"Habilidades criadas:\n{r_dev[:1500]}\n\n"
    f"Documento de identidade:\n{r_docs[:1500]}", 2048, 0.2)

with open(os.path.join(SAIDA, "04_review_revisao.txt"), "w", encoding="utf-8") as f:
    f.write(f"# REVIEW - Revisao do Dominio CRISTAL\n# Modelo: deepseek-r1:8b\n# Tempo: {t_review}s\n\n{r_review}")

# ============================================
# RELATORIO FINAL
# ============================================
print("\n\n" + "=" * 80)
print("  RELATORIO FINAL - SIMULACAO DE CRIACAO DE DOMINIO")
print("  Dominio: CRISTAL (ID 27)")
print("=" * 80)

print(f"\n  {'Passo':<8} {'Agente':<12} {'Modelo':<20} {'Tempo':<8} {'Chars':<8}")
print(f"  {'-'*8} {'-'*12} {'-'*20} {'-'*8} {'-'*8}")
for h in HISTORICO:
    print(f"  {h['agente']:<8} {h['agente']:<12} {h['modelo']:<20} {h['tempo']:<8}s {h['tamanho']:<8}")

print(f"\n  Tempo total: {sum(h['tempo'] for h in HISTORICO):.1f}s")
print(f"  Total de saida: {sum(h['tamanho'] for h in HISTORICO)} chars")
print(f"  Arquivos salvos em: sandbox/test_domain_simulation/")

print(f"\n  {'='*80}")
print(f"  AVALIACAO:")
print(f"  {'='*80}")
for h in HISTORICO:
    util = "✅" if h['tamanho'] > 200 else "❌"
    print(f"\n  {util} {h['agente'].upper()} ({h['modelo']}):")
    print(f"     Gerou {h['tamanho']} chars em {h['tempo']}s")
    palavras_chave = {
        "plan": ["cristal", "gema", "nicho", "essencia", "sinergia"],
        "dev": ["27001", "HABILIDADES", "efeitoConfig", "COMBAT"],
        "docs": ["cristal", "essencia", "identidade", "visual"],
        "review": ["cristal", "nicho", "unico", "recomendac"]
    }
    ks = palavras_chave.get(h['agente'], [])
    encontradas = sum(1 for k in ks if k.lower() in h['resposta'].lower())
    if len(ks) > 0:
        print(f"     Palavras-chave esperadas: {encontradas}/{len(ks)}")

# Salva historico completo
with open(os.path.join(SAIDA, "00_historico_completo.json"), "w", encoding="utf-8") as f:
    json.dump(HISTORICO, f, ensure_ascii=False, indent=2)

print(f"\n\n  Resultado completo: sandbox/test_domain_simulation/")
print("=" * 80)
