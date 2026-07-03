#!/usr/bin/env python3
"""
MCR-DevIA — AUTO-DIAGNÓSTICO v1.0
====================================
Escaneia a si mesmo e produz um relatório estruturado de saúde:
  - KG: qualidade, duplicatas, lixo, cobertura
  - Código: subprocess, elif, complexidade
  - Performance: V12 coverage, gargalos
  - ContextCrew: uso, stats
  - Sandbox: scripts órfãos

Saída em JSON (parseável) + relatório legível.

Uso:
    python mcr_auto_diagnostico.py              # diagnóstico completo
    python mcr_auto_diagnostico.py --json        # só JSON
    python mcr_auto_diagnostico.py --resumo      # só resumo
"""

import json, os, re, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SANDBOX = os.path.dirname(__file__)
DEVIA_DIR = os.path.join(BASE, 'scripts', 'mcr_devia')
MCR_DEVIA_PATH = os.path.join(DEVIA_DIR, 'mcr_devia.py')
KG_PATH = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')
RELATORIO_BATERIA = os.path.join(SANDBOX, 'testes_extensivos', 'relatorio_bateria.json')
BATERIA_SCRIPT = os.path.join(SANDBOX, 'testes_extensivos', 'bateria_completa.py')
ANALISE_PERF = os.path.join(SANDBOX, 'testes_extensivos', 'analise_perf.py')

# ============================================================
# 1. DIAGNÓSTICO DO KNOWLEDGE GRAPH
# ============================================================

def diagnosticar_kg() -> dict:
    """Analisa qualidade do Knowledge Graph."""
    resultado = {
        "status": "ok",
        "issues": [],
        "metricas": {}
    }
    
    if not os.path.exists(KG_PATH):
        resultado["status"] = "erro"
        resultado["issues"].append({"tipo": "arquivo_ausente", "severidade": "critico", "descricao": "KG nao encontrado"})
        return resultado
    
    with open(KG_PATH, encoding='utf-8') as f:
        kg = json.load(f)
    
    licoes = kg.get('licoes', [])
    total = len(licoes)
    ativas = [l for l in licoes if not l.get('inactive', False)]
    inativas = [l for l in licoes if l.get('inactive', False)]
    
    resultado["metricas"] = {
        "total_lessons": total,
        "ativas": len(ativas),
        "inativas": len(inativas),
        "pct_inativas": round(len(inativas) * 100 / max(1, total), 1),
        "tamanho_bytes": os.path.getsize(KG_PATH),
        "tamanho_kb": round(os.path.getsize(KG_PATH) / 1024, 1)
    }
    
    # Issues: % inativas alta
    pct_inativas = resultado["metricas"]["pct_inativas"]
    if pct_inativas > 50:
        resultado["issues"].append({
            "tipo": "kg_inativas_excesso",
            "severidade": "medio",
            "descricao": f"{pct_inativas}% das lessons estao inativas. O arquivo ainda contem {len(inativas)} lessons mortas."
        })
    
    # Issues: duplicatas
    corpos = {}
    dups = 0
    for l in ativas:
        chave = l.get('solucao', '')[:100].strip().lower()
        if chave in corpos:
            dups += 1
        else:
            corpos[chave] = l
    resultado["metricas"]["duplicatas"] = dups
    if dups > 0:
        resultado["issues"].append({
            "tipo": "kg_duplicatas",
            "severidade": "baixo",
            "descricao": f"{dups} lessons duplicadas encontradas (mesma solucao)."
        })
    
    # Issues: campos vazios
    sem_ctx = sum(1 for l in ativas if not l.get('ctx', '').strip())
    if sem_ctx > 0:
        resultado["issues"].append({
            "tipo": "kg_sem_contexto",
            "severidade": "baixo",
            "descricao": f"{sem_ctx} lessons ativas sem contexto definido."
        })
    
    # Issues: lessons de teste
    teste = [l for l in ativas if 'teste' in l.get('erro', '').lower()]
    resultado["metricas"]["lessons_teste"] = len(teste)
    if teste:
        resultado["issues"].append({
            "tipo": "kg_lessons_teste",
            "severidade": "baixo",
            "descricao": f"{len(teste)} lessons de teste ainda ativas."
        })
    
    # Contextos mais comuns
    ctx_dist = Counter(l.get('ctx', 'sem_ctx') for l in ativas)
    resultado["metricas"]["distribuicao_contextos"] = dict(ctx_dist.most_common(10))
    
    # Score de saude do KG (0-100)
    score_kg = 100
    score_kg -= min(30, int(pct_inativas * 0.3))  # -1 ponto por 3% inativo
    score_kg -= min(20, dups * 3)  # -3 por duplicata
    score_kg -= min(10, len(teste) * 2)  # -2 por lesson de teste
    resultado["metricas"]["saude_kg"] = max(0, score_kg)
    
    return resultado


# ============================================================
# 2. DIAGNÓSTICO DO CÓDIGO (mcr_devia.py)
# ============================================================

def diagnosticar_codigo() -> dict:
    """Analisa estrutura do codigo do MCR-DevIA."""
    resultado = {
        "status": "ok",
        "issues": [],
        "metricas": {}
    }
    
    if not os.path.exists(MCR_DEVIA_PATH):
        resultado["status"] = "erro"
        resultado["issues"].append({"tipo": "arquivo_ausente", "severidade": "critico"})
        return resultado
    
    with open(MCR_DEVIA_PATH, encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    n_lines = len(lines)
    
    # Contar subprocess.run e subprocess.Popen
    n_subprocess = len(re.findall(r'subprocess\.(?:run|Popen)\(', content))
    
    # Contar elif cmd
    n_elif = len(re.findall(r'elif cmd\s*==', content))
    
    # Contar if statements
    n_if = content.count('if ')
    
    # Contar funcoes
    n_funcoes = len(re.findall(r'^def\s+\w+', content, re.MULTILINE))
    
    # Contar imports
    n_imports = len(re.findall(r'^(?:import|from)\s+', content, re.MULTILINE))
    
    resultado["metricas"] = {
        "linhas": n_lines,
        "subprocess_run": n_subprocess,
        "elif_commands": n_elif,
        "if_statements": n_if,
        "funcoes": n_funcoes,
        "imports": n_imports,
        "tamanho_kb": round(os.path.getsize(MCR_DEVIA_PATH) / 1024, 1)
    }
    
    # Issues
    if n_subprocess > 10:
        resultado["issues"].append({
            "tipo": "subprocess_excesso",
            "severidade": "medio",
            "descricao": f"{n_subprocess} chamadas subprocess.run. Ideal: < 10."
        })
    
    if n_lines > 2000:
        resultado["issues"].append({
            "tipo": "arquivo_grande",
            "severidade": "baixo",
            "descricao": f"mcr_devia.py tem {n_lines} linhas. Ideal: < 1500."
        })
    
    return resultado


# ============================================================
# 3. DIAGNÓSTICO DE PERFORMANCE (via relatório da bateria)
# ============================================================

def diagnosticar_performance() -> dict:
    """Analisa performance dos testes."""
    resultado = {
        "status": "nao_executado",
        "issues": [],
        "metricas": {}
    }
    
    # Tenta ler relatório existente
    if os.path.exists(RELATORIO_BATERIA):
        with open(RELATORIO_BATERIA, encoding='utf-8') as f:
            relatorio = json.load(f)
        
        total = relatorio.get('total', 0)
        passed = relatorio.get('pass', 0)
        resultados = relatorio.get('resultados', [])
        
        # Calcular V12 coverage
        v12_count = sum(1 for r in resultados if r.get('tempo', 999) <= 1.0)
        ia_count = total - v12_count
        
        # Top 5 mais lentos
        sorted_by_time = sorted(resultados, key=lambda x: x.get('tempo', 0), reverse=True)
        top5_lentos = [{"nome": r['nome'], "tempo": r['tempo'], "cmd": r['cmd']} for r in sorted_by_time[:5]]
        
        resultado["metricas"] = {
            "total_testes": total,
            "pass": passed,
            "fail": total - passed,
            "pct_pass": round(passed * 100 / max(1, total), 1),
            "v12_count": v12_count,
            "ia_count": ia_count,
            "pct_v12": round(v12_count * 100 / max(1, total), 1),
            "top5_lentos": top5_lentos,
            "timestamp": relatorio.get('timestamp', '?')
        }
        
        resultado["status"] = "ok" if passed == total else "falhas"
        
        # Issues
        if passed < total:
            resultado["issues"].append({
                "tipo": "testes_falhando",
                "severidade": "critico",
                "descricao": f"{total - passed} testes falhando de {total}."
            })
        
        if v12_count / max(1, total) < 0.5:
            resultado["issues"].append({
                "tipo": "v12_baixo",
                "severidade": "medio",
                "descricao": f"Apenas {v12_count}/{total} testes sao V12 ({round(v12_count*100/max(1,total),1)}%). Ideal: >70%."
            })
        
        if top5_lentos:
            total_top5 = sum(t['tempo'] for t in top5_lentos)
            resultado["issues"].append({
                "tipo": "gargalos_performance",
                "severidade": "informacao",
                "descricao": f"Top 5 lentos: {total_top5:.1f}s. {top5_lentos[0]['nome']}: {top5_lentos[0]['tempo']}s."
            })
    
    return resultado


# ============================================================
# 4. DIAGNÓSTICO DO SANDBOX
# ============================================================

def diagnosticar_sandbox() -> dict:
    """Analisa o sandbox."""
    resultado = {
        "status": "ok",
        "issues": [],
        "metricas": {}
    }
    
    scripts_py = [f for f in os.listdir(SANDBOX) if f.endswith('.py') and os.path.isfile(os.path.join(SANDBOX, f))]
    resultado["metricas"]["total_scripts"] = len(scripts_py)
    
    # Tamanho total
    tamanho_total = sum(os.path.getsize(os.path.join(SANDBOX, f)) for f in scripts_py)
    resultado["metricas"]["tamanho_total_kb"] = round(tamanho_total / 1024, 1)
    
    # Scripts que nao sao atalhos e nem estao em ATALHOS_DIRETOS
    # (potenciais orfaos)
    if len(scripts_py) > 50:
        resultado["issues"].append({
            "tipo": "sandbox_muitos_scripts",
            "severidade": "informacao",
            "descricao": f"{len(scripts_py)} scripts .py no sandbox ({round(tamanho_total/1024,1)} KB)."
        })
    
    return resultado


# ============================================================
# 5. DIAGNÓSTICO DO CONTEXTCREW
# ============================================================

def diagnosticar_contextcrew() -> dict:
    """Analisa o ContextCrew."""
    resultado = {
        "status": "ok",
        "issues": [],
        "metricas": {}
    }
    
    cc_path = os.path.join(DEVIA_DIR, 'context_crew.py')
    if os.path.exists(cc_path):
        with open(cc_path, encoding='utf-8') as f:
            cc_content = f.read()
        resultado["metricas"]["linhas"] = len(cc_content.split('\n'))
        
        # Verifica se Weblearn é usado
        weblearn_dir = r'E:\Modelos IA\weblearn\fragments'
        if os.path.isdir(weblearn_dir):
            wl_count = sum(len(files) for _, _, files in os.walk(weblearn_dir))
            resultado["metricas"]["weblearn_fragments"] = wl_count
            if wl_count > 0:
                resultado["issues"].append({
                    "tipo": "weblearn_nao_testado",
                    "severidade": "informacao",
                    "descricao": f"{wl_count} fragmentos Weblearn disponiveis mas nao cobertos por testes."
                })
    
    return resultado


# ============================================================
# ============================================================
# 6. DIAGNÓSTICO DE DOCUMENTAÇÃO
# ============================================================

def diagnosticar_docs() -> dict:
    """Escaneia docs/rules/ e AGENTS.md em busca de inconsistencias.
    
    Verifica:
    - Referencias a arquivos/scripts que nao existem
    - Referencias cruzadas entre docs (links quebrados)
    - Mencoes a comandos desconhecidos
    - Docs desalinhados com o estado real
    """
    resultado = {
        "status": "ok",
        "issues": [],
        "metricas": {}
    }
    
    DOCS_RULES = os.path.join(BASE, 'docs', 'rules')
    AGENTS_PATH = os.path.join(BASE, 'AGENTS.md')
    
    # Coleta todos os .md a serem analisados
    docs_para_analisar = []
    if os.path.exists(AGENTS_PATH):
        docs_para_analisar.append(('AGENTS.md', AGENTS_PATH))
    if os.path.exists(DOCS_RULES):
        for f in sorted(os.listdir(DOCS_RULES)):
            if f.endswith('.md'):
                docs_para_analisar.append((f'docs/rules/{f}', os.path.join(DOCS_RULES, f)))
    
    resultado['metricas']['total_docs'] = len(docs_para_analisar)
    
    # Comandos validos - DINAMICO (extrai do MCR-DevIA + KG + projeto)
    COMANDOS_VALIDOS = set()
    # 1. Comandos do MCR-DevIA (parseia elif cmd)
    try:
        with open(MCR_DEVIA_PATH, 'r', encoding='utf-8') as f_cmds:
            for linha in f_cmds:
                m = re.search(r"elif cmd == '([a-z_]+)'", linha)
                if m: COMANDOS_VALIDOS.add(m.group(1))
    except: pass
    # 2. Atalhos do sandbox
    for script in os.listdir(SANDBOX):
        nome = os.path.splitext(script)[0]
        if nome and not script.startswith(('_', '.')):
            COMANDOS_VALIDOS.add(nome)
    # 3. Categorias do KG
    try:
        with open(KG_PATH, 'r', encoding='utf-8') as f_kg:
            kg_data = json.load(f_kg)
        for l in kg_data.get('licoes', []):
            ctx = l.get('ctx', '')
            if ctx: COMANDOS_VALIDOS.add(ctx)
    except: pass
    # 4. Cloud tools e comandos de sistema
    COMANDOS_VALIDOS.update(['python', 'pip', 'git', 'cd', 'dir', 'echo',
        'cmd', 'powershell', 'opencode', 'ollama', 'taskkill', 'rm',
        'write', 'read', 'edit', 'grep', 'glob', 'webfetch', 'question',
        'skill', 'task', 'todowrite', 'bash', 'netstat', 'where'])
    
    # Cache de arquivos .py/.md/.bat/.ps1 existentes
    arquivos_existentes = set()
    for root, dirs, files in os.walk(BASE):
        skip = {'.git', '__pycache__', 'node_modules', '.vcpkg', 'vcpkg',
                '.mcr_devia', 'autogerados', 'raw', 'fragments', 'narratives',
                'localStorage', 'bin', 'build', '.cmake'}
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if f.endswith(('.py', '.md', '.bat', '.ps1', '.sh')):
                rp = os.path.relpath(os.path.join(root, f), BASE).replace('\\', '/')
                arquivos_existentes.add(rp.lower())
    
    # Referencias a scripts: `scripts/foo.py` ou `sandbox/bar.py` ou `python algo.py`
    ref_script = re.compile(r'`([^`]+\.(?:py|bat|ps1|sh))`')
    ref_doc = re.compile(r'`(docs/[^`]+\.md)`')
    ref_comando = re.compile(r'`(\w+)`')
    
    for nome_doc, caminho_doc in docs_para_analisar:
        with open(caminho_doc, 'r', encoding='utf-8', errors='replace') as f:
            conteudo = f.read()
        
        # 1. Verificar referencias a scripts/arquivos
        for match in ref_script.finditer(conteudo):
            ref = match.group(1)
            if ref.lower() not in arquivos_existentes:
                resultado['issues'].append({
                    "tipo": "arquivo_ausente",
                    "severidade": "medio",
                    "descricao": f"{nome_doc}: arquivo nao encontrado '{ref}'"
                })
        
        # 2. Verificar referencias a outros docs
        for match in ref_doc.finditer(conteudo):
            ref = match.group(1)
            if not os.path.exists(os.path.join(BASE, ref)):
                resultado['issues'].append({
                    "tipo": "doc_ausente",
                    "severidade": "medio",
                    "descricao": f"{nome_doc}: doc nao encontrado '{ref}'"
                })
        
        # 3. Verificar comandos entre backticks (possiveis comandos MCR)
        for match in ref_comando.finditer(conteudo):
            cmd = match.group(1)
            if cmd in COMANDOS_VALIDOS:
                continue
            if len(cmd) < 4 or cmd.startswith(('http', '{', '<', '-')):
                continue
            if cmd in ('python', 'pip', 'git', 'cd', 'dir', 'where', 'echo',
                       'cmd', 'powershell', 'opencode', 'ollama'):
                continue
            resultado['issues'].append({
                "tipo": "comando_suspeito",
                "severidade": "informacao",
                "descricao": f"{nome_doc}: comando entre backticks nao reconhecido: '{cmd}'"
            })
    
    # 4. Consistencia: AGENTS.md referencia todos os docs/rules/ ?
    if os.path.exists(AGENTS_PATH) and os.path.exists(DOCS_RULES):
        with open(AGENTS_PATH, 'r', encoding='utf-8') as f:
            agents = f.read()
        for rf in sorted(os.listdir(DOCS_RULES)):
            if rf.endswith('.md') and f'docs/rules/{rf}' not in agents:
                resultado['issues'].append({
                    "tipo": "doc_nao_referenciado",
                    "severidade": "informacao",
                    "descricao": f"AGENTS.md nao referencia docs/rules/{rf}"
                })
    
    # 5. Cada rule doc referencia AGENTS.md?
    for nome_doc, caminho_doc in docs_para_analisar:
        if nome_doc == 'AGENTS.md':
            continue
        with open(caminho_doc, 'r', encoding='utf-8', errors='replace') as f:
            conteudo = f.read()
        if 'AGENTS.md' not in conteudo:
            resultado['issues'].append({
                "tipo": "sem_referencia_agentes",
                "severidade": "informacao",
                "descricao": f"{nome_doc}: nao referencia AGENTS.md"
            })
    
    # 6. Pendencias.md tem data?
    pend_path = os.path.join(BASE, 'docs', 'MCR - Instruções', 'DevLog', 'Pendências.md')
    if os.path.exists(pend_path):
        with open(pend_path, 'r', encoding='utf-8') as f:
            pend = f.read()
        dt = re.search(r'\((\d{2}/\d{2}/\d{4})\)', pend)
        resultado['metricas']['pendencias_data'] = dt.group(1) if dt else 'sem_data'
        if not dt:
            resultado['issues'].append({
                "tipo": "pendencias_sem_data",
                "severidade": "informacao",
                "descricao": "Pendencias.md sem data no titulo"
            })
    
    resultado['metricas']['total_issues_docs'] = len(resultado['issues'])
    if resultado['issues']:
        resultado['status'] = 'inconsistencias_encontradas'
    
    return resultado


# MONTAR RELATÓRIO
# ============================================================

def gerar_relatorio(modo="completo") -> dict:
    """Gera relatório completo de diagnóstico."""
    t0 = time.time()
    
    relatorio = {
        "ferramenta": "MCR-DevIA Auto-Diagnóstico v1.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duracao_segundos": 0,
        "modo": modo,
        "resumo": {},
        "kg": {},
        "codigo": {},
        "performance": {},
        "sandbox": {},
        "contextcrew": {},
        "docs": {}
    }
    
    # Executa cada diagnóstico
    relatorio["kg"] = diagnosticar_kg()
    relatorio["codigo"] = diagnosticar_codigo()
    relatorio["performance"] = diagnosticar_performance()
    relatorio["sandbox"] = diagnosticar_sandbox()
    relatorio["contextcrew"] = diagnosticar_contextcrew()
    relatorio["docs"] = diagnosticar_docs()
    
    # Compila resumo
    todas_issues = []
    for area in ['kg', 'codigo', 'performance', 'sandbox', 'contextcrew', 'docs']:
        for iss in relatorio[area].get('issues', []):
            todas_issues.append(iss)
    
    sev_count = {"critico": 0, "alto": 0, "medio": 0, "baixo": 0, "informacao": 0}
    for iss in todas_issues:
        s = iss.get('severidade', 'informacao')
        if s in sev_count:
            sev_count[s] += 1
    
    # Score geral (0-100)
    score = 100
    score -= sev_count["critico"] * 15
    score -= sev_count["alto"] * 8
    score -= sev_count["medio"] * 4
    score -= sev_count["baixo"] * 2
    score -= sev_count["informacao"] * 1
    score = max(0, min(100, score))
    
    relatorio["resumo"] = {
        "score_geral": score,
        "total_issues": len(todas_issues),
        "criticos": sev_count["critico"],
        "altos": sev_count["alto"],
        "medios": sev_count["medio"],
        "baixos": sev_count["baixo"],
        "informacoes": sev_count["informacao"]
    }
    
    relatorio["duracao_segundos"] = round(time.time() - t0, 2)
    return relatorio


def imprimir_relatorio(rel: dict, modo="completo"):
    """Imprime relatório formatado."""
    print("=" * 65)
    print(f"  {rel['ferramenta']}")
    print(f"  {rel['timestamp']}  |  {rel['duracao_segundos']}s")
    print("=" * 65)
    
    r = rel['resumo']
    print(f"\nRESUMO:")
    print(f"  Score geral: {r['score_geral']}/100")
    print(f"  Issues: {r['total_issues']} total")
    if r['criticos']: print(f"    [CRITICO] {r['criticos']}")
    if r['altos']:    print(f"    [ALTO] {r['altos']}")
    if r['medios']:   print(f"    [MEDIO] {r['medios']}")
    if r['baixos']:   print(f"    [BAIXO] {r['baixos']}")
    if r['informacoes']: print(f"    [INFO] {r['informacoes']}")
    
    if modo == "resumo":
        return
    
    # KG
    print(f"\n--- KNOWLEDGE GRAPH (saude: {rel['kg']['metricas'].get('saude_kg',0)}/100) ---")
    m = rel['kg']['metricas']
    print(f"  Lessons: {m.get('total_lessons',0)} total | {m.get('ativas',0)} ativas | {m.get('inativas',0)} inativas ({m.get('pct_inativas',0)}%)")
    print(f"  Tamanho: {m.get('tamanho_kb',0)} KB | Duplicatas: {m.get('duplicatas',0)}")
    if m.get('lessons_teste'):
        print(f"  Lessons de teste: {m['lessons_teste']}")
    for iss in rel['kg'].get('issues', []):
        print(f"  [{iss['severidade']}] {iss['descricao']}")
    
    # Código
    print(f"\n--- CODIGO ({rel['codigo']['metricas'].get('linhas',0)} linhas) ---")
    m = rel['codigo']['metricas']
    print(f"  subprocess.run: {m.get('subprocess_run',0)} | elif cmd: {m.get('elif_commands',0)} | funcoes: {m.get('funcoes',0)}")
    for iss in rel['codigo'].get('issues', []):
        print(f"  [{iss['severidade']}] {iss['descricao']}")
    
    # Performance
    print(f"\n--- PERFORMANCE ---")
    m = rel['performance']['metricas']
    if m:
        print(f"  Testes: {m.get('total_testes',0)} total | {m.get('pct_pass',0)}% pass | V12: {m.get('pct_v12',0)}%")
        if m.get('top5_lentos'):
            print(f"  Top 5 lentos:")
            for t in m['top5_lentos']:
                print(f"    {t['tempo']:>7.1f}s  {t['nome']}")
    else:
        print(f"  Sem dados de performance. Execute a bateria de testes primeiro.")
    for iss in rel['performance'].get('issues', []):
        print(f"  [{iss['severidade']}] {iss['descricao']}")
    
    # Sandbox
    print(f"\n--- SANDBOX ---")
    m = rel['sandbox']['metricas']
    print(f"  Scripts: {m.get('total_scripts',0)} | Tamanho: {m.get('tamanho_total_kb',0)} KB")
    for iss in rel['sandbox'].get('issues', []):
        print(f"  [{iss['severidade']}] {iss['descricao']}")
    
    # Docs
    print(f"\n--- DOCUMENTACAO ---")
    m = rel['docs']['metricas']
    print(f"  Docs analisados: {m.get('total_docs',0)} | Issues: {m.get('total_issues_docs',0)}")
    if m.get('pendencias_data'):
        print(f"  Pendencias.md data: {m['pendencias_data']}")
    for iss in rel['docs'].get('issues', []):
        print(f"  [{iss['severidade']}] {iss['descricao']}")
    
    print("\n" + "=" * 65)
    
    # Recomendacoes
    print(f"\nRECOMENDACOES:")
    todas_issues = []
    for area in ['kg', 'codigo', 'performance', 'sandbox', 'contextcrew', 'docs']:
        for iss in rel[area].get('issues', []):
            todas_issues.append((iss['severidade'], iss.get('descricao', '')))
    
    sev_order = {'critico': 0, 'alto': 1, 'medio': 2, 'baixo': 3, 'informacao': 4}
    todas_issues.sort(key=lambda x: sev_order.get(x[0], 5))
    
    for sev, desc in todas_issues[:10]:
        print(f"  [{sev}] {desc[:120]}")
    
    if not todas_issues:
        print("  Nenhuma melhoria necessaria. Sistema saudavel!")
    
    print()


if __name__ == '__main__':
    modo = "completo"
    if '--json' in sys.argv:
        rel = gerar_relatorio()
        print(json.dumps(rel, indent=2, ensure_ascii=False))
    elif '--resumo' in sys.argv:
        rel = gerar_relatorio()
        imprimir_relatorio(rel, "resumo")
    else:
        rel = gerar_relatorio()
        imprimir_relatorio(rel, "completo")
