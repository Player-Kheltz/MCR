"""Comando: patch - Edicao V12: Python estrutura, IA preenche blank."""
import os, sys, json, re, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "patch",
        "desc": "Edicao V12: Python estrutura, IA preenche blank.",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Edicao V12: Python estrutura, IA preenche blank.
    Uso: python mcr_devia.py patch <arquivo> <descricao>
    Ex:  python mcr_devia.py patch builder_x "adicionar logging no _gerar_bloco"""
    forca = '--force' in args or '-f' in args
    args = [a for a in args if a not in ('--force', '-f')]
    alvo = args[0]
    descricao = " ".join(args[1:])
    print(f'[Patch] Patch: {alvo} -> {descricao}...')
    
    # SAFETY: detecta intencao de CRIAR funcao (patch so substitui)
    palavras_criar = ['adicionar', 'criar', 'nova funcao', 'novo metodo', 'inserir', 'incluir']
    if any(p in descricao.lower() for p in palavras_criar):
        print(f'  [Patch] [BLOQUEADO] Descricao parece pedir CRIACAO de funcao.')
        print(f'  [Patch] Patch so SUBSTITUI funcoes existentes. Para criar, use:')
        print(f'    python mcr_devia.py build "criar {descricao}"')
        return
    
    # V12 FASE 1: Python encontra o arquivo (deterministico)
    import fnmatch as fn_patch
    candidatos = []
    from diretorio_analyzer import get_analyzer, filtrar_dirs_walk
    _da = get_analyzer()
    
    # Se for caminho absoluto que existe, usa direto (nao restrito a _SANDBOX)
    alvo_expandido = os.path.expanduser(alvo)
    if os.path.isabs(alvo_expandido) and os.path.exists(alvo_expandido):
        path = alvo_expandido
        print(f'  [Patch] Caminho absoluto: {path}')
    else:
        # Fallback: busca em _SANDBOX
        for root, dirs, files in os.walk(_SANDBOX):
            dirs[:] = filtrar_dirs_walk(dirs, root, _da)
            for f in files:
                if fn_patch.fnmatch(f, f'*{alvo}*') and f.endswith('.py'):
                    candidatos.append(os.path.join(root, f))
        if not candidatos:
            print(f'  [Patch] Arquivo "{alvo}" nao encontrado')
            return
        path = candidatos[0]
        print(f'  [Patch] Encontrado: {os.path.basename(path)}')
    
    with open(path, encoding='utf-8-sig') as f:
        linhas = f.readlines()
    # Remove BOM da primeira linha se presente (U+FEFF)
    if linhas and linhas[0].startswith('\ufeff'):
        linhas[0] = linhas[0][1:]
        print(f'  [Patch] BOM removido da primeira linha')
    
    # V12 FASE 2: Python extrai funcao alvo (deterministico)
    # Procura por def/class keywords
    funcoes = []
    for i, linha in enumerate(linhas):
        m = re.match(r'^(\s*)def\s+(\w+)\s*\(', linha)
        if m:
            indent = m.group(1)
            nome = m.group(2)
            nivel_indent = len(indent)  # nivel de indentacao em espacos
            # Extrai o corpo da funcao (ate encontrar outra funcao no mesmo nivel)
            corpo = []
            j = i
            while j < len(linhas):
                linha_atual = linhas[j]
                if j > i and linha_atual.strip():
                    # Conta espacos no inicio (sem expandir tabs)
                    espacos = len(linha_atual) - len(linha_atual.lstrip())
                    if espacos <= nivel_indent:
                        # Linha no mesmo nivel ou menor = fim da funcao
                        break
                corpo.append(linha_atual)
                j += 1
            funcoes.append({"nome": nome, "linha": i+1, "codigo": "".join(corpo), "indent": indent})
    
    if not funcoes:
        print(f'  [Patch] Nenhuma funcao encontrada em {os.path.basename(path)}')
        return
    
    print(f'  [Patch] Funcoes encontradas: {[f["nome"] for f in funcoes]}')
    
    # V12 FASE 3: IA descobre QUAL funcao modificar (blank controlado)
    prompt_funcs = "\n".join(f"  L{f['linha']}: def {f['nome']}(...) -> {f['codigo'].strip()}" for f in funcoes)
    # Prompt direto: IA responde APENAS o nome da funcao
    prompt_completo = (
        f"Arquivo: {os.path.basename(path)}\n"
        f"Descricao: {descricao}\n\n"
        f"Funcoes disponiveis:\n{prompt_funcs}\n\n"
        f"Responda APENAS o nome exato da funcao que deve ser modificada, sem explicacoes."
    )
    
    resp = fast(prompt_completo) or ""
    print(f'  [Patch] Resposta IA: {resp}')
    
    # Extrai o nome da funcao da resposta
    func_alvo = None
    linha_alvo = None
    
    # 1. Busca por linha: "L123" na resposta
    nums = re.findall(r'L(\d+)', resp)
    for n in nums:
        for f in funcoes:
            if f["linha"] == int(n):
                func_alvo = f
                linha_alvo = int(n)
                break
        if linha_alvo: break
    
    # 2. Fallback: nome da funcao aparece na resposta
    if not func_alvo:
        for f in funcoes:
            if f['nome'] in resp:
                func_alvo = f
                linha_alvo = f['linha']
                break
    
    # 3. Fallback: matching por similaridade (case insensitive)
    if not func_alvo:
        palavras_resp = resp.lower().split()
        for f in funcoes:
            nome_lower = f['nome'].lower()
            if nome_lower in resp.lower() or nome_lower in palavras_resp:
                func_alvo = f
                linha_alvo = f['linha']
                break
    
    # 4. Fallback: se tem UMA funcao no arquivo, assume ela
    if not func_alvo and len(funcoes) == 1:
        func_alvo = funcoes[0]
        linha_alvo = func_alvo['linha']
        print(f'  [Patch] Apenas uma funcao encontrada, assumindo: {func_alvo["nome"]}')
    
    if not linha_alvo:
        print(f'  [Patch] IA nao identificou a funcao. Opcoes:\n'
              f'    Opcao 1: Use edit manual.\n'
              f'    Opcao 2: Especifique o nome da funcao explicitamente:\n'
              f'      python mcr_devia.py patch {alvo} "na funcao X, {descricao}"')
        return
    
    print(f'  [Patch] Funcao alvo: {func_alvo["nome"]} (L{linha_alvo})')
    print(f'  [Patch] Codigo atual ({len(func_alvo["codigo"].splitlines())} linhas):')
    for l in func_alvo["codigo"].splitlines():
        print(f'    {l}')
    
    # V12 FASE 4: IA gera codigo novo (chamada direta ao Ollama, sem KG/veracidade)
    prompt_code = (
        f"Substitua a funcao abaixo para: {descricao}\n\n"
        f"{func_alvo['codigo']}\n\n"
        f"IMPORTANTE: Retorne APENAS o codigo da funcao. Nenhuma explicacao, nenhum texto antes ou depois, nenhum marcador de bloco. Apenas o codigo."
    )
    novo_codigo = fast(prompt_code) or ""
    novo_codigo = re.sub(r'```\w*\n?', '', novo_codigo).strip()
    # Remove linhas que nao comecam com def, espaco, tab ou } (protecao contra texto solto)
    linhas_code = []
    for linha in novo_codigo.split('\n'):
        if linha.strip() and not linha.startswith(('def ', '    ', '\t', '}', 'class ')):
            if any(kw in linha.lower() for kw in ['aqui est', 'aqui vai', 'segue', 'esta e', 'codigo:', '```']):
                continue
        linhas_code.append(linha)
    novo_codigo = '\n'.join(linhas_code).strip()
    
    if not novo_codigo:
        print(f'  [Patch] IA nao gerou codigo novo')
        return
    
    print(f'  [Patch] Codigo novo gerado ({len(novo_codigo.splitlines())} linhas):')
    for l in novo_codigo.splitlines():
        print(f'    {l}')
    
    # CONFIRMACAO: exibe diff e exige --force
    if not forca:
        print(f'  [Patch] [SEGURO] Para aplicar a edicao, execute com --force:')
        print(f'    python mcr_devia.py patch {alvo} "..." --force')
        print(f'  [Patch] ou use edit manual se preferir.')
        return
    
    # V12 FASE 5: Python faz backup + aplica edicao (deterministico)
    linha_orig = func_alvo["linha"] - 1
    fim_orig = linha_orig + len(func_alvo["codigo"].splitlines())
    
    # Backup automatico
    backup_path = path + '.bak'
    import shutil
    shutil.copy2(path, backup_path)
    print(f'  [Patch] Backup criado: {os.path.basename(backup_path)}')
    
    # Substitui as linhas
    novas_linhas = linhas + [novo_codigo + '\n'] + linhas[fim_orig:]
    
    # V12 FASE 6: Python valida compilacao
    try:
        compile("".join(novas_linhas), path, 'exec')
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(novas_linhas)
        print(f'  [Patch] [OK] Edit aplicado e compilacao verificada!')
        print(f'  [Patch] Backup em: {os.path.basename(backup_path)} (remova manualmente quando satisfeito)')
    except SyntaxError as e:
        print(f'  [Patch] [ERRO] Codigo gerado tem erro de sintaxe: {e}')
        # Restaura do backup
        shutil.copy2(backup_path, path)
        os.remove(backup_path)
        print(f'  [Patch] Backup restaurado. Arquivo original preservado.')
    return True
