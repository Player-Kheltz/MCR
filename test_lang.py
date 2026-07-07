import sys
sys.path.insert(0, r'E:\MCR')
from tree_sitter import Language, Parser
from tree_sitter_lua import language as lua_lang

print('Tentando Language(lua_lang())...')
try:
    lang = Language(lua_lang())
    print(f'OK: {type(lang).__name__}')
except Exception as e:
    print(f'Erro: {e}')

print('Tentando Language(lua_lang(), \"lua\")...')
try:
    lang = Language(lua_lang(), "lua")
    print(f'OK: {type(lang).__name__}')
except Exception as e:
    print(f'Erro: {e}')

print('Tentando Language.get_language...')
try:
    lang = Language.get_language(lua_lang())
    print(f'OK: {type(lang).__name__}')
except Exception as e:
    print(f'Erro: {e}')

# Check what Language.__new__ expects
print(f'\nLanguage.__new__: {Language.__new__.__doc__}')
