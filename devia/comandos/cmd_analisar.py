"""Comando: analisar - Analisa arquivo usando Orquestrador Universal."""
import os, sys, json, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import fast, gerar, extrair_codigo, BASE as _BASE, SANDBOX as _SANDBOX, OLLAMA_URL

def register():
    return {
        "name": "analisar",
        "desc": "Analisa arquivo usando Orquestrador Universal (prompt sob demanda)",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Analisa arquivo com Orquestrador Universal.
    Uso: python mcr_devia.py analisar <arquivo> [descricao]
    
    O Orquestrador:
    1. Le o arquivo e extrai estrutura (AST p/ codigo, tags p/ XML, etc.)
    2. ContextCrew busca contexto relevante
    3. FAST gera o prompt de analise ideal para este arquivo + contexto
    4. Router escolhe o modelo ideal (deepseek p/ codigo, llama3.1 p/ texto)
    """
    path_analisar = args[0]
    desc_extra = " ".join(args[1:]) if len(args) > 1 else ""
    
    # Resolver caminho (igual ao original)
    path_real = os.path.join(_SANDBOX, path_analisar) if not os.path.exists(path_analisar) else path_analisar
    if not os.path.exists(path_real):
        for ext in ['', '.py', '.lua', '.ts', '.js', '.xml', '.json', '.txt', '.md', '.csv']:
            tentativa = path_analisar + ext
            if os.path.exists(tentativa):
                path_real = tentativa
                break
    
    if not os.path.exists(path_real):
        print(f'[Analisar] Arquivo nao encontrado: {path_analisar}')
        return True
    
    with open(path_real, encoding='utf-8') as f:
        linhas = f.readlines()
    
    codigo = ''.join(linhas)
    ext = os.path.splitext(path_real)[1].lower()
    print(f'[Analisar] {path_real} ({len(linhas)} linhas, {ext})')
    
    # Detectar tipo
    eh_codigo = ext in ['.py', '.lua', '.cpp', '.c', '.h', '.hpp', '.ts', '.js', '.java', '.cs', '.go', '.rs']
    eh_texto = ext in ['.xml', '.json', '.csv', '.txt', '.md', '.ini', '.cfg', '.yaml', '.yml', '.toml']
    
    if not eh_codigo and not eh_texto:
        eh_codigo = bool(re.search(r'(def |class |function |local |int |void |#include|import |from )', codigo))
        eh_texto = not eh_codigo
    
    # Pre-analise de estrutura (igual ao original para garantir qualidade)
    ctx_estrutura = []
    if eh_codigo:
        funcoes = []
        chamadas = []
        if ext == '.py':
            try:
                import ast as _ast
                tree = _ast.parse(codigo)
                for node in _ast.walk(tree):
                    if isinstance(node, _ast.FunctionDef):
                        func_params = [a.arg for a in node.args.args]
                        for sub in _ast.walk(node):
                            if isinstance(sub, _ast.Call) and hasattr(sub.func, 'id'):
                                chamadas.append((sub.lineno, node.name, sub.func.id))
                        funcoes.append((node.name, node.lineno, func_params))
                    elif isinstance(node, _ast.ClassDef):
                        for sub in node.body:
                            if isinstance(sub, _ast.FunctionDef):
                                fname = f"{node.name}.{sub.name}"
                                chamadas.append((sub.lineno, node.name, sub.name))
                                funcoes.append((fname, sub.lineno, [a.arg for a in sub.args.args]))
            except Exception:
                pass
        if not funcoes:
            for i, line in enumerate(linhas, 1):
                m = re.match(r'^\s*(?:local\s+)?function\s+(\w+(?:\.\w+)*)\s*\(', line)
                if m: funcoes.append((m.group(1), i, []))
                m = re.match(r'^\s*(?:def|class)\s+(\w+)\s*[\(:]', line)
                if m: funcoes.append((m.group(1), i, []))
        if funcoes:
            ctx_estrutura.append("=== MAPA DE FUNCOES ===")
            for fn, linha, params in sorted(funcoes, key=lambda x: x[1]):
                ctx_estrutura.append(f"  LINHA {linha}: {fn}({', '.join(params) if params else '...'})")
        if chamadas:
            ctx_estrutura.append("\n=== CHAMADAS ===")
            for linha, chamador, chamado in chamadas:
                ctx_estrutura.append(f"  LINHA {linha}: {chamador} -> {chamado}")
        ctx_estrutura.append(f"\n=== CODIGO ({len(linhas)} linhas) ===")
        ctx_estrutura.extend(f"  {i:4d}| {line.rstrip()}" for i, line in enumerate(linhas, 1))
    else:
        if ext == '.xml':
            tags = set(re.findall(r'<(\w+)[\s>]', codigo))
            attrs = set(re.findall(r'(\w+)=[\'"]', codigo))
            ctx_estrutura.append(f"Tags: {', '.join(sorted(tags))}")
            ctx_estrutura.append(f"Atributos: {', '.join(sorted(attrs))}")
        ctx_estrutura.append(f"\n=== CONTEUDO ({len(linhas)} linhas) ===")
        ctx_estrutura.extend(f"  {i:4d}| {line.rstrip()}" for i, line in enumerate(linhas, 1))
    
    ctx_str = '\n'.join(ctx_estrutura)
    
    # Usar Orquestrador para gerar o prompt de analise
    from modulos.orquestrador import Orquestrador
    orq = Orquestrador(kg=kg, ia=ia, ctx_crew=ctx_crew)
    
    params = {
        "arquivo": os.path.basename(path_real),
        "extensao": ext,
        "tipo": "codigo" if eh_codigo else "texto",
        "descricao": desc_extra or f"Analise este arquivo e encontre problemas",
        "estrutura": ctx_str,
    }
    
    intencao = "analisar_codigo" if eh_codigo else "analisar_texto"
    resultado = orq.executar(intencao, params, consulta=f"analisar {os.path.basename(path_real)}", temp=0.2)
    
    if resultado["sucesso"]:
        print(f'\n[Analisar] Resultados:')
        print(resultado["resposta"])
        # Salvar no KG
        for line in resultado["resposta"].split('\n'):
            if 'LINHA' in line:
                try:
                    kg.aprender(
                        f"{'Bug' if eh_codigo else 'Problema'} em {os.path.basename(path_real)}",
                        "Analise", line.strip(),
                        "analisar_codigo" if eh_codigo else "analisar_texto"
                    )
                except Exception:
                    pass
    else:
        print(f'[Analisar] Falhou: {resultado.get("erro", "desconhecido")}')
    return True
