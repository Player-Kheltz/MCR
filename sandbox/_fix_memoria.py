#!/usr/bin/env python3
"""Corrige memoria.py: compactar mas NUNCA deletar."""
path = r'E:\Projeto MCR\scripts\mcr_devia\modulos\memoria.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find function _limpar_antigos
start = None
end = None
for i, line in enumerate(lines):
    if 'def _limpar_antigos' in line:
        start = i
    elif start is not None and i > start + 1:
        if line.startswith('    def ') or i == len(lines) - 1:
            end = i if i < len(lines) - 1 else i + 1
            break

if start is None:
    print('ERRO: funcao nao encontrada')
else:
    new_code = [
        '    def _limpar_antigos(self):\n',
        '        """Compacta dias antigos. NUNCA deleta. Memoria infinita."""\n',
        '        hoje = datetime.now()\n',
        '        for f in os.listdir(MEMORIA_DIR):\n',
        '            if not f.endswith(".jsonl") and not f.endswith(".jsonl.gz"):\n',
        '                continue\n',
        '            fpath = os.path.join(MEMORIA_DIR, f)\n',
        '            data_str = f.split(".")[0]\n',
        '            try:\n',
        '                data = datetime.strptime(data_str, "%Y-%m-%d")\n',
        '            except:\n',
        '                continue\n',
        '            dias_atras = (hoje - data).days\n',
        '            # So compacta se mais de 7 dias. NUNCA deleta.\n',
        '            if dias_atras > 7 and f.endswith(".jsonl"):\n',
        '                try:\n',
        '                    with open(fpath, "r", encoding="utf-8") as f_in:\n',
        '                        with gzip.open(fpath + ".gz", "wt", encoding="utf-8") as f_out:\n',
        '                            f_out.write(f_in.read())\n',
        '                    os.remove(fpath)\n',
        '                except: pass\n',
    ]
    lines[start:end] = new_code
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    try:
        compile(''.join(lines), path, 'exec')
        print(f'OK - _limpar_antigos NUNCA deleta (L{start+1})')
    except SyntaxError as e:
        print(f'ERRO: {e}')
