import sys, io
sys.path.insert(0, r'E:\MCR')
from tree_sitter import Parser
from tree_sitter_lua import language as lua_lang

# Try creating parser with language
try:
    p = Parser(lua_lang())
    print('Parser criado com lang no construtor')
except TypeError as e:
    print(f'Construtor falhou: {e}')
    try:
        p = Parser()
        p.set_language(lua_lang())
        print('set_language funciona')
    except AttributeError:
        p = Parser()
        p.language = lua_lang()
        print('Atribuicao direta funciona')

# Try parsing
with open(r'E:\Projeto MCR\historia\scripts\mcr_devia\comandos\cmd_grep.py', 'r') as f:
    codigo = f.read()

tree = p.parse(bytes(codigo, 'utf-8'))
root = tree.root_node
print(f'Parse OK: {root.type} com {len(root.children)} filhos')

# List node types
types = set()
def collect(node):
    types.add(node.type)
    for c in node.children:
        collect(c)
collect(root)
print(f'Tipos encontrados: {len(types)}')
for t in sorted(types)[:20]:
    print(f'  {t}')
