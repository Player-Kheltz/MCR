import sys
sys.path.insert(0, r'E:\MCR')
from tree_sitter import Language, Parser
from tree_sitter_lua import language as lua_lang

# Create Language
lang = Language(lua_lang())
print(f'Language: {type(lang).__name__}')

# Create Parser
try:
    p = Parser(lang)
    print('Parser OK')
except TypeError as e:
    print(f'Parser TypeError: {e}')
    # Try no-arg
    p = Parser()
    print('Parser no-arg OK')

# Parse
with open(r'E:\Projeto MCR\historia\scripts\mcr_devia\comandos\cmd_grep.py', 'r') as f:
    codigo = f.read()[:1000]

try:
    tree = p.parse(bytes(codigo, 'utf-8'))
    root = tree.root_node
    print(f'Parse OK: {root.type}')
    for child in root.children[:10]:
        print(f'  {child.type}')
except Exception as e:
    print(f'Parse erro: {e}')
    # Maybe Parser needs language set differently
    print(dir(p))
