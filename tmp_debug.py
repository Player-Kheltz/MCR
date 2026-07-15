import sys; sys.path.insert(0, "E:/MCR")
from mcr.mcr import MCR
from mcr.extrator_features import get_extrator
mcr = MCR()

print("=== DEBUG _extrair_nome ===")
for test in ["Crie um NPC ferreiro", "Gere um monstro dragao", "Crie um NPC mago elfo", "Crie ferreiro anao", "Gere dragao vermelho"]:
    nome = mcr._extrair_nome(test)
    print(f'  "{test}" -> "{nome}"')

print()
print("=== DEBUG _decidir ===")
for test in ["Gere um monstro dragao", "Crie um monstro orc", "Gere um NPC ferreiro", "Gere um monstro", "Crie um NPC"]:
    estado = mcr._perceber(test)
    acao, conf = mcr._decidir(estado)
    print(f'  "{test}": estado={estado[:80]}, acao={acao}, conf={conf:.3f}')

print()
print("=== DEBUG ExtratorFeatures ===")
ext = get_extrator()
for test in ["Crie um NPC ferreiro", "Gere um monstro dragao", "Crie um NPC", "Gere um monstro"]:
    fp = ext.extrair(test)
    print(f'  "{test}" -> fp={fp[:60]}')

print()
print("=== Extrator diagnostic ===")
print(ext.diagnosticar())
