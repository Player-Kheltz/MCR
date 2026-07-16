"""empacotar_mcr.py — Gera pacote portátil do ecossistema MCR.

Remove: cache, dados temporários, bins, dependências externas.
Mantém: código fonte, testes, docs, configs, scripts.
"""
import os, shutil, zipfile, re, json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / 'MCR_PORTAVEL'
EXCLUIR_DIRS = {
    # Nao-MCR (dominio Tibia/jogo)
    'client', 'server', 'nichos', 'ArquivosComplementares',
    'golden_examples', 'legacy', 'tools',
    # Experimentos / prototipos nao-nucleo
    'devia', 'sandbox', 'sandbox_criativo', 'poc_output', 'prototypes',
    # Gerados / cache
    'cache', 'data', 'Backup',
    # Config local
    '.opencode', '.git', '.pytest_cache', '__pycache__',
    'node_modules', '.vscode', 'venv', '.env',
    # O proprio destino (evita copiar dentro de si mesmo)
    'MCR_PORTAVEL',
}
EXCLUIR_ARQS = {
    '*.db', '*.sqlite3', '*.pyc', '*.pyo', '*.log', '*.rar', '*.zip',
    '*.7z', '*.tar', '*.gz', '*.exe', '*.dll', '*.so', '*.pyd',
    'coupling_*.json', 'markov_*.json',
    'patterns_*.json', 'mcr_*.json',
    'resultado_*.json', 'batch_*.json', 'relatorio_*.json',
}
EXCLUIR_PASTAS_POR_NOME = {
    '__pycache__', '.git', 'node_modules', 'site-packages',
    'vcpkg_installed', 'build', 'dist', '.egg-info',
}

def _deve_excluir(rel_path: str) -> bool:
    normalizado = rel_path.replace('\\', '/')
    partes = normalizado.split('/')
    for p in partes:
        if p in EXCLUIR_PASTAS_POR_NOME:
            return True
    for nome in EXCLUIR_DIRS:
        nm = nome.replace('\\', '/')
        if nm in partes:
            return True
    for padrao in EXCLUIR_ARQS:
        if padrao.startswith('*'):
            if rel_path.endswith(padrao[1:]):
                return True
    return False

def _tamanho_legivel(b):
    for u in ('B', 'KB', 'MB', 'GB'):
        if b < 1024:
            return f'{b:.1f} {u}'
        b /= 1024
    return f'{b:.1f} TB'

def empacotar():
    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True)

    total_arquivos = 0
    total_bytes = 0

    print('Empacotando MCR...')
    print()

    for root, dirs, files in os.walk(RAIZ):
        rel = os.path.relpath(root, RAIZ)
        if rel == '.':
            rel = ''

        if _deve_excluir(rel):
            continue

        # Poda dirs desnecessários no walk
        dirs[:] = [d for d in dirs if not _deve_excluir(os.path.join(rel, d))]

        for arquivo in files:
            rel_path = os.path.join(rel, arquivo) if rel else arquivo
            if _deve_excluir(rel_path):
                continue

            src = os.path.join(root, arquivo)
            dst = DESTINO / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)

            try:
                sz = os.path.getsize(src)
                if sz < 1 * 1024 * 1024:  # max 1MB por arquivo
                    shutil.copy2(src, dst)
                    total_arquivos += 1
                    total_bytes += sz
            except:
                pass

    # Gerar manifesto
    manifesto = {
        'nome': 'MCR - Motor Cognitivo Universal',
        'versao': '2.0',
        'arquivos': total_arquivos,
        'tamanho': _tamanho_legivel(total_bytes),
        'componentes': sorted(set(
            p.split('/')[0] for p in os.listdir(DESTINO)
            if os.path.isdir(DESTINO / p)
        )),
    }
    with open(DESTINO / 'MANIFESTO.json', 'w', encoding='utf-8') as f:
        json.dump(manifesto, f, indent=2, ensure_ascii=False)

    print(f'  {total_arquivos} arquivos')
    print(f'  {_tamanho_legivel(total_bytes)}')
    print(f'  Destino: {DESTINO}')
    print()

    # Criar .rar via PowerShell (se disponível)
    rar_path = RAIZ / 'MCR_PORTAVEL.rar'
    print('Criando arquivo .rar...')
    ps_cmd = (
        f'$src = "{DESTINO}"; '
        f'$dst = "{rar_path}"; '
        f'if (Test-Path $dst) {{ Remove-Item $dst }}; '
        f'if (Get-Command Compress-Archive -ErrorAction SilentlyContinue) {{'
        f'  Compress-Archive -Path $src\\* -DestinationPath "$dst" -CompressionLevel Optimal -Force;'
        f'  Write-Host " ZIP criado: $dst";'
        f'}} else {{'
        f'  Write-Host " Compress-Archive nao disponivel";'
        f'}}'
    )
    os.system(f'powershell -Command "{ps_cmd}"')

    print()
    print('Para criar .rar manualmente:')
    print(f'  1. Abra {DESTINO}')
    print(f'  2. Adicione os arquivos ao WinRAR/7zip')
    print(f'  3. Salve como MCR_PORTAVEL.rar')

if __name__ == '__main__':
    empacotar()
