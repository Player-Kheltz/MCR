"""Alimentar KG com dominio MCR + corrigir perguntar + filtro veracidade"""
import json, re, os

# ================================================================
# PASSO 1: Alimentar KG com definicoes do MCR_IDENTITY.md
# ================================================================
kg_path = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
kg = json.load(open(kg_path, "r", encoding="utf-8"))

novas_licoes = [
    {
        "id": f"L{len(kg['licoes'])+1:03d}",
        "erro": "MCR = Projeto MCR, servidor de Tibia baseado em Canary",
        "causa": "Confusao com Minecraft ou outros projetos",
        "solucao": "MCR e um servidor CUSTOMIZADO de Tibia (OTServ), nao Minecraft. Canary e o servidor, OTClient e o cliente.",
        "ctx": "identidade"
    },
    {
        "id": f"L{len(kg['licoes'])+2:03d}",
        "erro": "SPA = Sistema de Progressao do Aventureiro",
        "causa": "Confusao com Single Page Application",
        "solucao": "SPA no MCR significa Sistema de Progressao do Aventureiro. Sistema de niveis, habilidades e dominios do jogador.",
        "ctx": "identidade"
    },
    {
        "id": f"L{len(kg['licoes'])+3:03d}",
        "erro": "SHC = Sistema de Habilidades Contextuais",
        "causa": "Confusao com Server Handler Class ou outros termos",
        "solucao": "SHC = Sistema de Habilidades Contextuais. 5 camadas: postura (Impeto/Equilibrio/Guarda), nivel do dominio, sinergias, estados de alma (Vinculo/Lampejo), condicoes situacionais.",
        "ctx": "identidade"
    },
    {
        "id": f"L{len(kg['licoes'])+4:03d}",
        "erro": "Dominios = areas de conhecimento do SPA",
        "causa": "Termo generico sem contexto",
        "solucao": "Dominios sao as areas de conhecimento do SPA: Fogo (ID 23), Gelo (24), Terra (25), Energia (26). Cada dominio tem 30 habilidades e identidade propria.",
        "ctx": "identidade"
    },
    {
        "id": f"L{len(kg['licoes'])+5:03d}",
        "erro": "Eridanus = cidade inicial do projeto MCR",
        "causa": "Cidade desconhecida para novos jogadores/IA",
        "solucao": "Eridanus e a cidade inicial do MCR, no continente de Lorentia. Possui NPCs, missoes iniciais e tutoriais.",
        "ctx": "identidade"
    },
    {
        "id": f"L{len(kg['licoes'])+6:03d}",
        "erro": "Canary = servidor OTServ de Tibia",
        "causa": "Confusao com ferramenta CI/CD de mesmo nome",
        "solucao": "Canary no MCR e um servidor personalizado de Tibia (OTServ), baseado no TFS (The Forgotten Server). Nao e ferramenta CI/CD.",
        "ctx": "identidade"
    },
]

for l in novas_licoes:
    kg["licoes"].append(l)
    print(f"  [OK] {l['id']}: {l['erro'][:50]}...")

json.dump(kg, open(kg_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"\n[KG] {len(novas_licoes)} lessons adicionadas ({len(kg['licoes'])} total)")

# ================================================================
# PASSO 2: Corrigir perguntar() para usar modelo contexto
# + Filtro de Veracidade
# ================================================================
mcr_path = "E:\\Projeto MCR\\scripts\\mcr_devia\\mcr_devia.py"
code = open(mcr_path, "r", encoding="utf-8").read()

# 2.1 - Fazer perguntar() usar modelo "contexto" em vez de "code"
# O IA.gerar() dentro de perguntar() usa tarefa="code" (padrao)
# Mudar a chamada para usar tarefa="contexto" quando for pergunta conceitual
old_perguntar = """r = self.ia.gerar(prompt)"""
new_perguntar = """r = self.ia.gerar(prompt, tarefa="contexto")"""

if old_perguntar.strip()[:30] in code:
    code = code.replace(old_perguntar, new_perguntar)
    print("[OK] perguntar() agora usa modelo contexto")
else:
    print("[AVISO] Nao encontrou padrao para substituir")

# 2.2 - Adicionar filtro de VERACIDADE apos o filtro de genericidade
# Procurar a secao de avaliacao e nota
old_nota = 'avaliacao = self.ia.gerar(prompt_avaliacao, 0.2) or ""'
new_nota = """avaliacao = self.ia.gerar(prompt_avaliacao, 0.2) or ""
                eh_generico = "GENERICA" in avaliacao.upper() and "ESPECIFICA" not in avaliacao.upper()
                nota = 0 if eh_generico else min(100, len(r.split()) * 2 + (10 if ":" in r else 0) + (20 if len(r) > 200 else 0))

                # FILTRO DE VERACIDADE
                termos_resposta = set(re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*", r))
                termos_suspeitos = []
                for termo in termos_resposta:
                    if len(termo.split()) > 3: continue
                    tl = termo.lower().strip()
                    existe = any(tl in (l.get("erro","")+l.get("solucao","")+l.get("ctx","")).lower() for l in kg["licoes"])
                    if not existe and len(termo) > 3:
                        termos_suspeitos.append(termo)
                if termos_suspeitos:
                    penalty = min(40, len(termos_suspeitos) * 15)
                    nota = max(0, nota - penalty)
                    print(f"  [Veracidade] Termos nao encontrados: {termos_suspeitos} (-{penalty})")

                print(f"  Nota: {nota}/100")
                if nota >= 60:
                    print(f"\\n{r[:500]}")
                    return r"""

if old_nota.strip()[:30] in code:
    code = code.replace(old_nota, new_nota)
    print("[OK] Filtro de veracidade adicionado")
else:
    print("[AVISO] Nao encontrou padrao para filtro de veracidade")

# Salvar mcr_devia.py atualizado
open(mcr_path, "w", encoding="utf-8").write(code)
print(f"\n[MCR] mcr_devia.py atualizado!")
