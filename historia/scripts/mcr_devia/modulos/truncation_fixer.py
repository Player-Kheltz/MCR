"""Truncation Fixer Universal — Remove TODO truncamento  do codigo ativo.
Nova politica: TUDO que trunca deve ser removido. Sem excecao.
- Conteudo: resposta, prompt, texto → REMOVER
- Logs: print(..., var), log(... var) → REMOVER
- Hash/ID: hexdigest(), md5(...) → REMOVER
- Colecao: lista, split() → REMOVER
- Controle: for x in lista → REMOVER (substituir por iteracao completa)

Excecoes ABSOLUTAS (essenciais para o codigo funcionar):
- sys.path[:N] - slicing de path do sistema
- string[:0] - slicing vazio para copia
"""
import os, re, sys, json

# Regex UNIVERSAL: captura QUALQUER [:\d+] ou [:\w+] (slicing de lista/string)
# Nao captura: sys.path[:N], string[:0]
_PADRAO_UNIVERSAL = re.compile(r'(?<!sys\.path)\[\s*\:[\s\w\d]+\]')

# Excecoes: padroes que DEVEM ser preservados
_PADRAO_EXCECOES = re.compile(
    r'(sys\.path\[:\d+\]|\[\:\d*\]\[:|\[\:0\]|\[\:len\(|str\(.*?\)\[:\d+\])'
)


def escanear(diretorio, recursivo=True):
    """Escaneia diretorio em busca de QUALQUER  slicing.
    
    Returns:
        list[dict]: {arquivo, linha, texto, match, seguro_remover}
    """
    ocorrencias = []
    for root, dirs, files in os.walk(diretorio):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'Legado')]
        for f in files:
            if not f.endswith('.py'):
                continue
            # Pula mcr_devia.py (legado de 2854 linhas, quebra sintaxe ao corrigir)
            if f == 'mcr_devia.py':
                continue
            fpath = os.path.join(root, f)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                    linhas = fh.readlines()
                for i, linha in enumerate(linhas, 1):
                    # Pula linhas de comentario
                    if linha.strip().startswith('#'):
                        continue
                    for match in _PADRAO_UNIVERSAL.finditer(linha):
                        # Verifica se e excecao
                        if _PADRAO_EXCECOES.search(linha):
                            continue
                        ocorrencias.append({
                            'arquivo': os.path.relpath(fpath, diretorio),
                            'linha': i,
                            'texto': linha.strip(),
                            'match': match.group(),
                            'seguro_remover': True,  # TUDO removido!
                        })
            except Exception:
                pass
    return ocorrencias


def _corrigir_linha(linha, match):
    """Remove o slicing  da linha, mantendo o resto."""
    slicing = match.group()
    # Se for .split()[:N] ou metodo()[:N], remove so o slicing
    # Se for var[:N], remove so o slicing
    # Se for for x in lista[:N], remove [:N]
    return linha.replace(slicing, '')


def _corrigir_for_loop(linha, match):
    """Para for x in lista, remove  da lista."""
    # for l in lessons[:5]: → for l in lessons:
    return linha.replace(match.group(), '')


def corrigir(ocorrencias, base_dir):
    """Aplica correcoes em arquivos. Remove TODOS os slicing encontrados."""
    resultados = {}
    modificados = {}
    
    for occ in ocorrencias:
        if not occ['seguro_remover']:
            continue
        
        fpath = os.path.join(base_dir, occ['arquivo'])
        if fpath not in modificados:
            with open(fpath, 'r', encoding='utf-8') as f:
                modificados[fpath] = {'linhas': f.readlines(), 'alteradas': 0}
        
        dados = modificados[fpath]
        idx = occ['linha'] - 1
        if 0 <= idx < len(dados['linhas']):
            match = re.search(_PADRAO_UNIVERSAL, dados['linhas'][idx])
            if match and not _PADRAO_EXCECOES.search(dados['linhas'][idx]):
                nova = _corrigir_linha(dados['linhas'][idx], match)
                if nova != dados['linhas'][idx]:
                    dados['linhas'][idx] = nova
                    dados['alteradas'] += 1
    
    for fpath, dados in modificados.items():
        if dados['alteradas'] > 0:
            try:
                conteudo = ''.join(dados['linhas'])
                compile(conteudo, fpath, 'exec')
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
                rel = os.path.relpath(fpath, base_dir)
                resultados[rel] = {'corrigidas': dados['alteradas'], 'status': 'OK'}
            except SyntaxError as e:
                rel = os.path.relpath(fpath, base_dir)
                resultados[rel] = {'corrigidas': 0, 'status': f'SYNTAX ERROR: {e}'}
    
    return resultados


def executar():
    """Executa o truncation fixer completo."""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    devia_dir = os.path.join(base, 'Scripts', 'mcr_devia')
    
    if not os.path.exists(devia_dir):
        return {'erro': 'diretorio_nao_encontrado'}
    
    print('[TruncationFixer] Escaneando TODOS os truncamentos...')
    ocorrencias = escanear(devia_dir)
    
    if not ocorrencias:
        print('[TruncationFixer] Nenhum truncamento encontrado.')
        return {'total_encontradas': 0, 'total_corrigidas': 0}
    
    print(f'[TruncationFixer] {len(ocorrencias)} truncamentos encontrados.')
    
    print(f'[TruncationFixer] Corrigindo {len(ocorrencias)} ocorrencias...')
    resultados = corrigir(ocorrencias, devia_dir)
    total_corrigidas = sum(r['corrigidas'] for r in resultados.values())
    arquivos_ok = sum(1 for r in resultados.values() if r['status'] == 'OK')
    arquivos_erro = sum(1 for r in resultados.values() if r['status'] != 'OK')
    
    print(f'[TruncationFixer] {total_corrigidas} truncamentos removidos em {arquivos_ok} arquivos')
    if arquivos_erro:
        print(f'[TruncationFixer] {arquivos_erro} arquivos com erro:')
        for fpath, r in resultados.items():
            if r['status'] != 'OK':
                print(f'  {fpath}: {r["status"]}')
    
    return {
        'total_encontradas': len(ocorrencias),
        'total_corrigidas': total_corrigidas,
        'arquivos_ok': arquivos_ok,
        'arquivos_erro': arquivos_erro,
    }


if __name__ == '__main__':
    resultado = executar()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

