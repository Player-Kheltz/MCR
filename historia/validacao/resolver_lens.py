#!/usr/bin/env python3
"""Substitui hardcodes len >= N no MCR.py por _limiar universal."""
with open(r'E:\Projeto MCR\MCR.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add _limiar method after MCRDecisorUniversal
insert_marker = 'class MCRDecisorUniversal:'
insert_pos = content.find(insert_marker)
if insert_pos >= 0:
    # Find where the class ends (next class definition)
    end_pos = content.find('\nclass ', insert_pos + 100)
    if end_pos < 0:
        end_pos = len(content)
    class_content = content[insert_pos:end_pos]
    
    # Add _limiar static method at the end of the class
    limiar_method = '''
    @staticmethod
    def _limiar(contexto, entidade=''):
        if not entidade:
            return 2
        h = MCRByteUtils.entropia_bytes(entidade.encode('utf-8')[:200])
        return max(1, min(6, int(h + 1)))
'''
    # Find the last method in the class
    # Insert before the class ends
    new_class = class_content.rstrip() + '\n' + limiar_method.strip()
    content = content[:insert_pos] + new_class + content[end_pos:]

# Direct string replacements
substituicoes = [
    ('if len(pal) >= 4:', 'if len(pal) >= MCRDecisorUniversal._limiar("palavra", pal):'),
    ('if len(p) >= 2},', 'if len(p) >= MCRDecisorUniversal._limiar("token", p)},'),
    ('if len(p) >= 2}', 'if len(p) >= MCRDecisorUniversal._limiar("token", p)}'),
    ('if len(pal) < 2:', 'if len(pal) < MCRDecisorUniversal._limiar("palavra_min", pal):'),
    ('if len(nomes) < 4:', 'if len(nomes) < MCRDecisorUniversal._limiar("topicos", " ".join(nomes[:5]) if nomes else ""):'),
    ('if len(conteudo) > 50:', 'if len(conteudo) > MCRDecisorUniversal._limiar("conteudo", conteudo[:100]) * 10:'),
    ('if len(resposta) > 100:', 'if len(resposta) > MCRDecisorUniversal._limiar("resposta", resposta[:100]) * 20:'),
    ('if len(palavras) < 4:', 'if len(palavras) < MCRDecisorUniversal._limiar("palavras", " ".join(palavras)):'),
    ('if len(texto) > 100:', 'if len(texto) > MCRDecisorUniversal._limiar("texto", texto[:100]) * 10:'),
]

count = 0
for old, new in substituicoes:
    if old in content:
        content = content.replace(old, new)
        count += 1
        print(f'  Substituto: {old[:50]}...')

with open(r'E:\Projeto MCR\MCR.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n{count} hardcodes de len resolvidos. _limiar universal adicionado.')
