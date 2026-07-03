"""Debug do MCRFerramentas."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from MCR import *

# Teste direto sem ferramentas
motor = MCRMotor()
# Alimenta alguns exemplos manuais
motor.alimentar("function onSay(player, words, param) local npc = Npc() npc:setName('Bruno') npc:setPosition(100, 200, 7) end", "npc_exemplo")
motor.alimentar("local npc = Game.createNpc('Ferreiro') npc:setOutfit(128) npc:setSpeech('Precisa de algo?')", "npc_ferreiro")
motor.alimentar("Eridanus e a cidade inicial do projeto MCR construida as margens do Lago Cristalino possui porto praca central templo forja e mercado", "eridanus")

# Testa geracao
r = motor.gerar_por_assinatura("Crie um NPC ferreiro", 10)
print('Geracao direta:', r[:120])

# Testa conexao
c = motor.conectar("npc_exemplo", "eridanus")
if c:
    print(f'Conexao: nota={c["nota"]} seq={c["sequencia"][:80]}')

# Agora testa ferramentas com motor pre-alimentado
ferr = MCRFerramentas(motor)
resultado = ferr.executar("Crie um NPC ferreiro em Eridanus no estilo Lua",
                          r'E:\Projeto MCR')
print()
print('Ferramentas resultado:')
print('  Resposta:', resultado['resposta'][:120])
print('  Nota:', resultado['nota'])
print('  Ferramentas:', resultado['ferramentas'])
print('  Ciclos:', resultado['ciclos'])
print('  Topicos finais:', resultado['topicos_finais'])
for h in resultado['historico']:
    r = h['resultado'][:60] if h['resultado'] else '(vazio)'
    print(f'  C{h["ciclo"]}: {h["ferramenta"]:15s} nota={h["nota"]:.2f} | {r}')
