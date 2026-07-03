"""Fix reconstruir_com_blocos return."""
with open('E:/Projeto MCR/Scripts/mcr_devia/modulos/aprendiz_de_padroes.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = "        resultado = fragmento.replace('**', '')\n\n\n\n"
new = "        resultado = fragmento.replace('**', '')\n        resultado = resultado.strip()\n        return resultado[:500] if len(resultado) > 10 else None\n"

if old in content:
    content = content.replace(old, new, 1)
    with open('E:/Projeto MCR/Scripts/mcr_devia/modulos/aprendiz_de_padroes.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK')
else:
    print('NOT FOUND')
    print(repr(old))
