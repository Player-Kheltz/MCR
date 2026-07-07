import sys; sys.path.insert(0, r'E:\MCR')
from tree_sitter import Language, Parser
from tree_sitter_lua import language as lua_lang

p = Parser()
p.set_language(lua_lang())

with open(r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades\arcos.lua', 'r') as f:
    codigo = f.read()[:2000]

tree = p.parse(bytes(codigo, 'utf-8'))
root = tree.root_node

def print_tree(node, depth=0):
    if depth > 4: return
    start = f'L{node.start_point[0]+1}'
    end = f'L{node.end_point[0]+1}'
    print('  ' * depth + f'{node.type} ({start}-{end})')
    for child in node.children[:15]:
        print_tree(child, depth + 1)

print_tree(root)
