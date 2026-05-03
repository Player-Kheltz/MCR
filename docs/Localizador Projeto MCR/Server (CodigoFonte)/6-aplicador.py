#!/usr/bin/env python3
import os
import shutil
import sys

def carregar_mapa(filepath):
    dados = {}
    arquivo_atual = None
    if not os.path.exists(filepath):
        return dados

    with open(filepath, 'r', encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip('\n')
            if linha.startswith('[') and linha.endswith(']'):
                arquivo_atual = linha[1:-1]
                dados[arquivo_atual] = {}
            elif '=' in linha and arquivo_atual:
                partes = linha.split('=', 1)
                dados[arquivo_atual][partes[0]] = partes[1]
    return dados

def escape_for_cpp(text):
    """Converte caracteres acentuados para escapes octais seguros para C++"""
    result = []
    for ch in text:
        if ord(ch) > 127:
            try:
                byte_val = ch.encode('latin-1')[0]
                result.append(f"\\{oct(byte_val)[2:].zfill(3)}")
            except:
                result.append('?')
        else:
            result.append(ch)
    return ''.join(result)

def main():
    if len(sys.argv) < 3:
        print("Uso: python 4_aplicador.py extraido.txt reparado.txt")
        return

    arq_original = sys.argv[1]
    arq_reparado = sys.argv[2]

    originais = carregar_mapa(arq_original)
    reparados = carregar_mapa(arq_reparado)

    print("🚀 Iniciando injeção no código-fonte...")

    ficheiros_modificados = []

    for filepath, strings_originais in originais.items():
        if not os.path.exists(filepath) or filepath not in reparados:
            continue

        # Cria backup da versão em inglês
        backup_path = filepath + '.bak'
        if not os.path.exists(backup_path):
            shutil.copy2(filepath, backup_path)

        # Lê arquivo fonte (detecta encoding)
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                lines = f.readlines()

        alteracoes = 0
        ext = os.path.splitext(filepath)[1].lower()
        is_cpp = ext in ['.cpp', '.h']

        for chave, txt_original in strings_originais.items():
            txt_novo = reparados[filepath].get(chave)
            if not txt_novo or txt_original == txt_novo:
                continue

            # Recupera a linha (ex: "145_15" → linha 144)
            line_idx = int(chave.split('_')[0]) - 1
            if line_idx >= len(lines):
                continue

            # Proteção extra: ignora includes
            if lines[line_idx].strip().startswith('#include'):
                continue

            target = f'"{txt_original}"'

            # Escapa aspas internas
            safe_new = txt_novo.replace('"', '\\"')
            
            # Aplica proteção Octal apenas se o arquivo for C++
            if is_cpp:
                safe_new = escape_for_cpp(safe_new)
                
            replacement = f'"{safe_new}"'

            if target in lines[line_idx]:
                lines[line_idx] = lines[line_idx].replace(target, replacement)
                alteracoes += 1

        if alteracoes > 0:
            encoding_out = 'utf-8-sig' if is_cpp else 'latin-1'

            with open(filepath, 'w', encoding=encoding_out) as f:
                f.writelines(lines)
            print(f"✔ {filepath}: {alteracoes} strings aplicadas e protegidas.")
            ficheiros_modificados.append(filepath)

    # Guardar a lista de ficheiros alterados
    with open("ficheiros_modificados.txt", 'w', encoding='utf-8') as lst:
        for fp in ficheiros_modificados:
            lst.write(fp + '\n')

    print("🎉 Aplicação finalizada! Pode fazer o Rebuild no Visual Studio.")

if __name__ == '__main__':
    main()