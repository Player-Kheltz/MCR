"""Fix Lore Engine parser"""
with open(r'E:\Projeto MCR\sandbox\mcr_crew_v16_lore.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Replace the _parse_resposta function with a more flexible version
old_func = """    def _parse_resposta(self, texto, campos):
        \"\"\"Extrai campos da resposta da IA.\"\"\"
        resultado = {}
        if not texto: return resultado
        
        for campo in campos:
            padrao = re.compile(rf'{campo}:\\s*(.+?)(?=\\n[A-Z]+:|\\Z)', re.DOTALL | re.IGNORECASE)
            m = padrao.search(texto)
            if m:
                resultado[campo] = m.group(1).strip()
        
        return resultado"""

new_func = """    def _parse_resposta(self, texto, campos):
        \"\"\"Extrai campos - parser flexivel.\"\"\"
        resultado = {}
        if not texto: return resultado
        
        for campo in campos:
            # Tenta varios padroes
            for padrao in [
                rf'{campo}:\\s*(.+?)(?=\\n[A-Z][A-Z ]+:|\\Z)',
                rf'{campo}:\\s*(.+?)(?=\\n\\d|\\Z)',
                rf'\\*\\*{campo}\\*\\*:?\\s*(.+?)(?=\\n\\*\\*|\\Z)',
            ]:
                try:
                    m = re.search(padrao, texto, re.DOTALL | re.IGNORECASE)
                    if m:
                        val = m.group(1).strip().strip('*\\n\\r ')
                        if len(val) > 15:
                            resultado[campo] = val[:500]
                            break
                except: pass
        
        return resultado"""

c = c.replace(old_func, new_func)

with open(r'E:\Projeto MCR\sandbox\mcr_crew_v16_lore.py', 'w', encoding='utf-8') as f:
    f.write(c)

try:
    compile(c, 'v16_lore.py', 'exec')
    print('OK!')
except SyntaxError as e:
    print(f'Error: {e}')
