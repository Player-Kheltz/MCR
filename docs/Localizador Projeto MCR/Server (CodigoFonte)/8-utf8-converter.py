#!/usr/bin/env python3
r"""
Converte escapes octais \ooo (Latin-1) para caracteres UTF-8 reais em:
  - .cpp / .hpp / .h  (Código-fonte do servidor)
  - .lua               (Scripts do servidor e cliente)
  - .xml               (Arquivos de dados)

Também garante que o arquivo seja salvo como UTF-8 sem BOM.

Uso:
  python 8-utf8-converter.py                          # Processa diretórios padrão
  python 8-utf8-converter.py --dry-run                # Apenas mostra o que seria alterado
  python 8-utf8-converter.py --path "E:\Projeto MCR\Canary\src"  # Escopo específico
"""

import os
import re
import sys

# Mapeamento de octal → caractere Latin-1
OCTAL_TO_LATIN1 = {}
for codepoint in range(0x80, 0x100):
    octal = f"\\{oct(codepoint)[2:].zfill(3)}"
    OCTAL_TO_LATIN1[octal] = bytes([codepoint])

# Padrão: \ seguido de exatamente 3 dígitos octais vÃ¡lidos (0-7)
OCTAL_PATTERN = re.compile(r'\\([0-7]{3})')

def octal_to_utf8(text: str) -> str:
    """Converte escapes octais Latin-1 para caracteres UTF-8."""
    def replace_match(m):
        octal_str = '\\' + m.group(1)
        # Converte \ooo → bytes Latin-1 → decode como Latin-1 → encode como UTF-8
        codepoint = int(m.group(1), 8)
        if codepoint < 0x80:
            return chr(codepoint)  # ASCII, mantém
        try:
            # Converte para caractere Latin-1 e depois para UTF-8
            latin1_bytes = bytes([codepoint])
            return latin1_bytes.decode('latin-1')
        except (ValueError, UnicodeDecodeError):
            return octal_str  # Mantém original se falhar
    return OCTAL_PATTERN.sub(replace_match, text)

def process_file(filepath: str, dry_run: bool = False) -> bool:
    """Processa um arquivo: converte octais e salva como UTF-8."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ('.cpp', '.hpp', '.h', '.lua', '.xml'):
        return False

    # Detecta codificação
    encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    content = None
    used_encoding = None
    for enc in encodings_to_try:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            used_encoding = enc
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print(f"  ⚠  Não foi possível ler: {filepath}")
        return False

    # Converte octais
    new_content = octal_to_utf8(content)
    if new_content == content:
        return False  # Nada mudou

    non_ascii_new = len(re.findall(r'[^\x00-\x7F]', new_content))
    non_ascii_old = len(re.findall(r'[^\x00-\x7F]', content))
    changes = non_ascii_new - non_ascii_old
    
    if dry_run:
        print(f"  [DRY] {filepath} ({changes} chars alterados)")
        return True  # Conta como modificado mesmo em dry-run

    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(new_content)
    print(f"  [OK] {os.path.basename(filepath)} ({changes} chars, era {used_encoding})")
    return True

def scan_directory(root: str, dry_run: bool = False) -> tuple:
    """Varre um diretório recursivamente processando arquivos."""
    total = 0
    modified = 0
    skipped_dirs = {'.git', 'build', 'vcpkg_installed', 'node_modules', 
                    '__pycache__', '.github', 'vcproj', '.vs', 'generated',
                    'Backup', 'docker', 'tests'}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skipped_dirs]
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ('.cpp', '.hpp', '.h', '.lua', '.xml'):
                total += 1
                filepath = os.path.join(dirpath, filename)
                if process_file(filepath, dry_run):
                    modified += 1

    return total, modified

def main():
    dry_run = '--dry-run' in sys.argv

    # Diretórios padrão
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    
    # Verifica se --path foi passado
    paths = []
    for i, arg in enumerate(sys.argv[1:]):
        if arg.startswith('--path='):
            paths.append(arg.split('=', 1)[1])
    
    if not paths:
        # Diretórios padrão do projeto MCR
        project_root = r'E:\Projeto MCR'
        if os.path.exists(project_root):
            paths = [
                os.path.join(project_root, 'Canary', 'src'),
                os.path.join(project_root, 'Canary', 'data-canary'),
                os.path.join(project_root, 'Canary', 'data-otservbr-global'),
            ]
            # Verifica se OTClient modules existe
            otclient_modules = os.path.join(project_root, 'OTClient', 'modules')
            if os.path.exists(otclient_modules):
                paths.append(otclient_modules)
        else:
            paths = ['.']

    print(f"{'MODO DRY-RUN' if dry_run else 'CONVERTENDO'} escapes octais para UTF-8")
    print(f"{'─' * 60}")
    
    total_all = 0
    modified_all = 0
    for path in paths:
        if os.path.exists(path):
            rel = os.path.relpath(path, base)
            print(f"\n[{rel}]")
            t, m = scan_directory(path, dry_run)
            total_all += t
            modified_all += m
        else:
            print(f"\n[WARN] Caminho nao encontrado: {path}")
    
    print(f"\n{'─' * 60}")
    print(f"Total: {total_all} arquivos, {modified_all} modificados")
    
    if dry_run:
        print("\nRemova --dry-run para aplicar as alteracoes.")

if __name__ == '__main__':
    main()
