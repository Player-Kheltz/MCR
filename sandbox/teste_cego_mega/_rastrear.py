import re

txt = open("E:/Projeto MCR/sandbox/teste_cego_mega/respostas_mcr/mega_1.txt", "r", encoding="utf-8-sig").read()

ALUCINACOES = ["DataTransformer", "DataLoader", "DataProcessor", "Caching",
               "Seguranca", "Sistema", "Monitoramento", "SecurityManager",
               "DataStream", "ErrorHandler", "DataNormalizer"]

print("ALUCINACOES RASTREADAS:")
for c in ALUCINACOES:
    pos = txt.find(c)
    if pos >= 0:
        ctx = txt[max(0,pos-80):pos+len(c)+80].replace("\n"," | ")
        print(f"\n  {c} na posicao {pos}:")
        print(f"  ...{ctx}...")

# Separa por secoes
secoes = re.split(r"(\[ \] [^\n]+)", txt)
secao = "INTRO"
print("\n\nPOR SECAO:")
for parte in secoes:
    if parte.startswith("[ ]"):
        secao = parte.strip()[:60]
    else:
        for c in ALUCINACOES:
            if c in parte:
                print(f"  {c} esta em: {secao}")

# Codigo ou texto?
blocos = list(re.finditer(r"```", txt))
dentro = False
ultimo_fim = 0
for m in blocos:
    dentro = not dentro
print("\n\nDENTRO DE CODIGO?:")
for c in ALUCINACOES:
    pos = txt.find(c)
    if pos >= 0:
        # Conta quantos ``` antes desta posicao
        antes = txt[:pos].count("```")
        em_codigo = antes % 2 == 1
        print(f"  {c}: {'CODIGO' if em_codigo else 'TEXTO'}")
