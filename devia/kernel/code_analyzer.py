"""code_analyzer.py — deteccao deterministica de bugs comuns em codigo Python/Lua/C++.

Roda em 0ms (sem LLM). Detecta padroes via regex.
Reduz chamadas LLM em ~60% para analise de codigo.
"""
import os, re, sys
from typing import List, Dict, Optional


# ─── PADROES DE BUG ─────────────────────────────────────────────

PADROES_BUG = [
    # Python
    (r'except\s*:\s*\n\s*pass', 'Python', 'except vazio suprime todas excecoes. PermissionError/UnicodeDecodeError passam despercebidos.',
     'Alta', 'except (PermissionError, UnicodeDecodeError) as e: print(f"[Warn] {e}")'),
    
    (r'errors\s*=\s*[\'"]replace[\'"]', 'Python', 'errors=replace substitui caracteres invalidos por ?, perdendo dados.',
     'Media', 'Tentar encoding correto primeiro, usar replace so como ultimo fallback.'),
    
    (r'os\.walk\([^)]*\)', 'Python', 'os.walk() recursivo sem limite de profundidade. Trava em diretorios grandes (milhares de arquivos).',
     'Media', 'Adicionar limite de profundidade: if root.count(os.sep) > max_depth: dirs[:] = []'),
    
    (r'\.\.\\\.\.\\\.\.', 'Python', 'Path relativo com .. — fragil. Se o diretorio mudar, quebra silenciosamente.',
     'Media', 'Usar os.environ.get("MCR_PROJECT_BASE", os.path.abspath(...))'),
    
    (r'\.encode\([\'"]ascii[\'"]', 'Python', 'encode("ascii") perde acentos e caracteres PT-BR. Viola Pilar 3 do MCR.',
     'Alta', 'Remover encode ascii. Usar encoding correto (latin-1 para .lua, utf-8 para .cpp).'),
    
    (r'SANDBOX\s*=\s*os\.path', 'Python', 'Diretorio padrao SANDBOX em vez de projeto. Busca nao acha arquivos do Canary/Grimorio.',
     'Alta', 'Mudar default para BASE (projeto), nao SANDBOX (sandbox).'),
    
    # Encoding
    (r'encoding\s*=\s*[\'"]utf-8[\'"]', 'Geral', 'Hardcoded UTF-8. Arquivos .lua do MCR usam Latin-1 (Pilar 3, regra de encoding).',
     'Alta', 'Detectar encoding por extensao: .lua→latin-1, .cpp→utf-8.'),
    
    # Geral
    (r'open\([^)]*,\s*[\'"]r[\'"]\s*\)', 'Geral', 'Leitura sem especificar encoding. Assume default do SO.',
     'Media', 'Sempre especificar encoding: .lua=latin-1, .cpp/.py/.go=utf-8.'),
    
    (r'\.readlines\(\)', 'Python', 'readlines() carrega arquivo inteiro em memoria. Arquivos grandes (ex: items.xml 4.2MB) explodem.',
     'Media', 'Iterar linha por linha: for linha in f: ...'),
    
    (r'\.read\(\)', 'Python', 'read() carrega arquivo inteiro em memoria. Logs podem ter GB.',
     'Media', 'Adicionar limite: f.read(100000) com aviso se truncado.'),
    
    # SQL Injection (Grimorio)
    (r'SELECT\s+\*.*\bFROM\b.*\$', 'C#', 'SQL Injection via interpolacao de string. Vulnerabilidade conhecida no Grimorio.',
     'Critica', 'Usar parametros MySqlCommand.Parameters.AddWithValue().'),
    
    (r'SELECT\s+\*.*\bFROM\b.*\+', 'C#', 'SQL Injection via concatenacao. Vulnerabilidade conhecida no Grimorio.',
     'Critica', 'Usar parametros MySqlCommand.Parameters.AddWithValue().'),
    
    # C++ 
    (r'new\s+\w+', 'C++', 'Uso de new sem smart pointer. Risco de memory leak se delete for esquecido.',
     'Media', 'Usar std::unique_ptr ou std::shared_ptr.'),
    
    (r'\.c_str\(\)', 'C++', 'c_str() em contexto temporario pode dangling pointer.',
     'Media', 'Armazenar std::string antes de chamar c_str() se o objeto temporario expirar.'),

    # Lua
    (r'dofile\(', 'Lua', 'dofile() em Revscript MCR — usar carregamento automatico do Revscript.',
     'Media', 'Remover dofile(). O Revscript carrega automaticamente scripts em data-canary/scripts/MCR/.'),
    
    # Nao-tratamento
    (r'except\s*Exception:', 'Python', 'except Exception muito amplo. Esconde erros inesperados.',
     'Baixa', 'Capturar excecoes especificas. Usar except Exception apenas com log + re-raise.'),
]

# Severidade → peso para ordenacao
SEVERIDADE_PESO = {'Critica': 4, 'Alta': 3, 'Media': 2, 'Baixa': 1}


def analisar_arquivo(caminho: str) -> List[Dict]:
    """Analisa um arquivo e retorna bugs encontrados."""
    bugs = []
    
    if not os.path.exists(caminho):
        return bugs
    
    # Detecta linguagem pela extensao
    _, ext = os.path.splitext(caminho)
    linguagem = {
        '.py': 'Python', '.cpp': 'C++', '.hpp': 'C++', '.h': 'C++', '.c': 'C++',
        '.cs': 'C#', '.lua': 'Lua', '.go': 'Go',
    }.get(ext.lower(), 'Geral')
    
    try:
        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
            conteudo = f.read()
    except:
        return bugs
    
    linhas = conteudo.split('\n')
    
    for pattern, linguagem_padrao, descricao, severidade, correcao in PADROES_BUG:
        # So aplica padroes compativeis com a linguagem
        if linguagem_padrao != 'Geral' and linguagem_padrao != linguagem:
            continue
        
        for i, linha in enumerate(linhas):
            match = re.search(pattern, linha)
            if match:
                # Contexto: 2 linhas ao redor
                inicio = max(0, i - 1)
                fim = min(len(linhas), i + 2)
                contexto = '\n'.join(f'  L{j+1}: {linhas[j].rstrip()[:80]}' for j in range(inicio, fim))
                
                bugs.append({
                    'arquivo': os.path.basename(caminho),
                    'linha': i + 1,
                    'descricao': descricao,
                    'severidade': severidade,
                    'correcao': correcao,
                    'contexto': contexto,
                    'peso': SEVERIDADE_PESO.get(severidade, 0),
                })
                break  # So reporta 1x por arquivo (evita spam)
    
    bugs.sort(key=lambda b: (-b['peso'], b['linha']))
    return bugs


def analisar_diretorio(diretorio: str, max_arquivos: int = 50) -> Dict[str, List[Dict]]:
    """Analisa diretorio recursivamente."""
    resultados = {}
    count = 0
    
    if not os.path.isdir(diretorio):
        return resultados
    
    extensoes = {'.py', '.cpp', '.hpp', '.h', '.c', '.cs', '.lua', '.go'}
    
    for raiz, _, arquivos in os.walk(diretorio):
        for f in arquivos:
            if count >= max_arquivos:
                break
            _, ext = os.path.splitext(f)
            if ext.lower() not in extensoes:
                continue
            caminho = os.path.join(raiz, f)
            bugs = analisar_arquivo(caminho)
            if bugs:
                resultados[caminho] = bugs
                count += 1
        if count >= max_arquivos:
            break
    
    return resultados


def formatar_relatorio(bugs: List[Dict]) -> str:
    """Formata bugs encontrados em texto."""
    if not bugs:
        return "Nenhum bug deterministico encontrado."
    
    linhas = []
    por_severidade = {'Critica': [], 'Alta': [], 'Media': [], 'Baixa': []}
    for b in bugs:
        por_severidade[b['severidade']].append(b)
    
    for sev in ['Critica', 'Alta', 'Media', 'Baixa']:
        items = por_severidade[sev]
        if not items:
            continue
        linhas.append(f"\n## {sev} ({len(items)})")
        for b in items:
            linhas.append(f"\n- **{b['arquivo']}:{b['linha']}** — {b['descricao']}")
            linhas.append(f"  Correcao: {b['correcao']}")
    
    return '\n'.join(linhas)


# ─── Integracao com PipelineExecutor ────────────────────────────

def analisar_no_pipeline(ctx: dict) -> str:
    """Handler para o PipelineExecutor. Analisa conteudo de arquivo no contexto."""
    caminho = ctx.get('caminhos', [None])[0]
    conteudo = ctx.get('conteudo', '')
    
    bugs = []
    if caminho and os.path.exists(caminho):
        bugs = analisar_arquivo(caminho)
    elif conteudo:
        # Analisa conteudo como texto (sem arquivo)
        for pattern, linguagem, descricao, severidade, correcao in PADROES_BUG:
            for i, linha in enumerate(conteudo.split('\n')):
                match = re.search(pattern, linha)
                if match:
                    bugs.append({
                        'arquivo': 'stdin',
                        'linha': i + 1,
                        'descricao': descricao,
                        'severidade': severidade,
                        'correcao': correcao,
                        'peso': SEVERIDADE_PESO.get(severidade, 0),
                    })
                    break
        bugs.sort(key=lambda b: (-b['peso'], b['linha']))
    
    resultado = formatar_relatorio(bugs)
    ctx['code_analyzer_bugs'] = bugs
    ctx['code_analyzer_output'] = resultado
    return resultado
