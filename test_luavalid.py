import sys; sys.path.insert(0, r'E:\MCR')
from LuaSyntaxValidator import verificar_sintaxe

testes = [
    ("Lua valido (variaveis)", 'local x = 1; local y = 2; local z = x + y'),
    ("Lua invalido (string sem fechar)", "function foo() print('teste) end"),
    ("HABILIDADES valido", 'HABILIDADES[ID] = { nome = "Teste", tipo = "gatilho", cor = COR.DOM_MAGIA_FOGO, }'),
    ("NPC valido", 'npcType = Game.createNpcType("Teste")'),
    ("Lua invalido (end faltando)", 'function foo() print("teste")'),
]
for nome, codigo in testes:
    ok, erro = verificar_sintaxe(codigo)
    status = 'OK' if ok else 'X'
    err_msg = erro[:60] if erro else ''
    print(f'  [{status}] {nome}: {err_msg}')
