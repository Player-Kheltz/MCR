#!/usr/bin/env python3
r"""
Converte caracteres acentuados de arquivos .cpp/.h em escapes octais \ooo (Latin-1).
Elimina erros C2022 ("muito grande para caractere") no Visual Studio.
Se for passado um ficheiro com a lista de ficheiros modificados, apenas esses são processados.
"""
import sys
from pathlib import Path

def escape_non_ascii(text):
    """Substitui caracteres > 127 por escapes em octal \\ooo"""
    result = []
    for ch in text:
        if ord(ch) > 127:
            try:
                # Converte para Latin-1 (padrão do Client) e pega o valor do byte
                byte_val = ch.encode('latin-1')[0]
                # Formata em octal e garante exatamente 3 dígitos (ex: \347)
                result.append(f"\\{oct(byte_val)[2:].zfill(3)}")
            except UnicodeEncodeError:
                result.append('?') # Fallback seguro
        else:
            result.append(ch)
    return ''.join(result)

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler {filepath}: {e}")
        return False

    escaped = escape_non_ascii(content)
    if escaped == content:
        return False

    with open(filepath, 'w', encoding='ascii', errors='xmlcharrefreplace') as f:
        f.write(escaped)
    return True

def main():
    if len(sys.argv) < 2:
        print("Uso: python acentos.py <pasta_src> [ficheiros_modificados.txt]")
        return

    src_dir = Path(sys.argv[1])
    if not src_dir.is_dir():
        print(f"❌ O diretório {src_dir} não existe.")
        return

    # Se foi passado um ficheiro de lista, carrega os caminhos permitidos
    ficheiros_permitidos = None
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            ficheiros_permitidos = {line.strip() for line in f if line.strip()}

    processed = 0
    changed = 0
    for ext in ['.cpp', '.h']:
        for fp in src_dir.rglob(f'*{ext}'):
            # Se existe lista, ignora ficheiros não listados
            if ficheiros_permitidos is not None and str(fp) not in ficheiros_permitidos:
                continue

            processed += 1
            if process_file(fp):
                changed += 1
                print(f"✔ {fp.name} – acentos escapados (Octal)")

    print(f"\n📊 Ficheiros verificados: {processed}")
    print(f"🎉 Ficheiros alterados: {changed}")
    if changed > 0:
        print("Recompile o servidor. Os erros C2022 desaparecerão!")

if __name__ == '__main__':
    main()