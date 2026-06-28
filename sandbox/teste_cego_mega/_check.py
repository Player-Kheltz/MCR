import re
txt = open("E:/Projeto MCR/sandbox/teste_cego_mega/respostas_mcr/mega_1.txt", "r", encoding="utf-8-sig").read()

markers = re.findall(r"\[\s*\][^[]+", txt)
print(f"Total markers found: {len(markers)}")
for m in markers:
    print(f"  -> {m.strip()[:80]}")

# Check for specific terms
for term in ["REVISAO", "GERACAO", "geracao", "revisao"]:
    if term in txt:
        print(f"Termo '{term}' ENCONTRADO")
    else:
        print(f"Termo '{term}' AUSENTE")

# Check positions
pos_revisao = txt.find("[ ] REVISAO")
pos_geracao = txt.find("[ ] GERACAO")
print(f"\n[ ] REVISAO at position: {pos_revisao}")
print(f"[ ] GERACAO at position: {pos_geracao}")

# What's between chars 24000-28000?
print(f"\nChars 22000-25000: ...{txt[22000:25000]}...")
print(f"\nChars 25000-28750: ...{txt[25000:]}...")
