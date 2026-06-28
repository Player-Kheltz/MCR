"""Salvar lessons finais da sessao"""
import json

path = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
kg = json.load(open(path, "r", encoding="utf-8"))

novas = [
    {
        "id": f"L{len(kg['licoes'])+1:03d}",
        "erro": "Fast alucinava genero PT-BR (dizia SIM para article='um' em 'Flecha')",
        "causa": "Modelo 1.5b nao entende genero de palavras em portugues",
        "solucao": "V12: Validador de genero PT-BR aprende palavras no KG. 10/10 acertos. 0 chamadas de IA para palavras conhecidas. Regra: -a feminino, -o masculino, excecoes aprendidas sob demanda.",
        "ctx": "v12_genero"
    },
    {
        "id": f"L{len(kg['licoes'])+2:03d}",
        "erro": "Modelo ignorava contexto do KG e alucinava (SHC = Smart Hunter Client)",
        "causa": "Modelos de chat tendem a ignorar contexto fornecido e usar conhecimento proprio",
        "solucao": "Context Infinity + V12: se KG tem resposta direta, Python entrega sem chamar IA. So chama IA quando KG nao tem a resposta. Zero alucinacao.",
        "ctx": "context_infinity"
    },
    {
        "id": f"L{len(kg['licoes'])+3:03d}",
        "erro": "Contexto 4K insuficiente para analise global de codigo",
        "causa": "Modelo local 7B limitado por VRAM",
        "solucao": "Context Infinity: Orquestrador gerencia fragmentos no contexto ativo. Adicionador/Removedor/Supervisor/Indexador mantem apenas o relevante. Super Fragmentador + AST pre-analysis compensam limite de contexto.",
        "ctx": "context_infinity"
    },
]

for l in novas:
    kg["licoes"].append(l)
    print(f"  [OK] {l['id']}: {l['erro'][:60]}...")

json.dump(kg, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"\n[KG] {len(novas)} lessons adicionadas ({len(kg['licoes'])} total)")
