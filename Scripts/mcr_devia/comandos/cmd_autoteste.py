"""Comando: autoteste - Auto-Teste Definitivo do MCR-DevIA.
Gera perguntas via FAST, executa, coleta auto-critica, avalia, salva historico.

Uso (JSON IPC):
  {"cmd": "autoteste", "args": ["--ciclo", "1"]}
  {"cmd": "autoteste", "args": ["--gerar"]}        # So gera perguntas
  {"cmd": "autoteste", "args": ["--relatorio"]}    # Mostra historico
  {"cmd": "autoteste", "args": ["--status"]}        # Estado atual
"""
import os, sys, json, time, hashlib
from datetime import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')

REGRAS_PATH = os.path.join(SANDBOX, 'autoteste_regras.json')
HISTORICO_PATH = os.path.join(SANDBOX, 'autoteste_historico.json')

# ============================================================
# CARGA DE REGRAS
# ============================================================

def _carregar_regras():
    if os.path.exists(REGRAS_PATH):
        with open(REGRAS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def _carregar_historico():
    if os.path.exists(HISTORICO_PATH):
        with open(HISTORICO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"ciclos": [], "perguntas_usadas": [], "ultimo_ciclo": 0}

def _salvar_historico(data):
    with open(HISTORICO_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# GERADOR DE PERGUNTAS (FAST)
# ============================================================

def _fast(prompt):
    try:
        from modulos.util import fast as _util_fast
        return _util_fast(prompt, 0.15, "fast") or ""
    except:
        return ""

def _gerar_perguntas(regras, historico):
    """FAST gera perguntas para este ciclo baseado em regras + historico."""
    categorias = regras.get('categorias', {})
    regras_ger = regras.get('regras_gerador', {})
    
    # Calcula estatisticas do historico
    ultimos_ciclos = historico.get('ciclos', [])[-3:]
    gaps_por_categoria = {}
    notas_por_categoria = {}
    for ciclo in ultimos_ciclos:
        for teste in ciclo.get('testes', []):
            cat = teste.get('categoria', '?')
            gap = teste.get('gap', 0)
            gaps_por_categoria[cat] = gaps_por_categoria.get(cat, 0) + gap
            if 'cloud_nota' in teste:
                notas_por_categoria[cat] = notas_por_categoria.get(cat, []) + [teste['cloud_nota']]
    
    piores_notas = sorted(
        [(cat, sum(notas)/len(notas)) for cat, notas in notas_por_categoria.items()],
        key=lambda x: x[1]
    )[:3] if notas_por_categoria else []
    
    # Categorias nao testadas ainda
    testadas = set()
    for ciclo in historico.get('ciclos', []):
        for teste in ciclo.get('testes', []):
            testadas.add(teste.get('categoria', ''))
    nao_testadas = [c for c in categorias if c not in testadas]
    
    prompt = (
        "VOCE E O GERADOR DE TESTES DO MCR-DevIA.\n"
        "Regras:\n"
        f"- Maximo {regras_ger.get('max_perguntas_por_ciclo', 5)} perguntas\n"
        f"- Minimo {regras_ger.get('min_codigo_por_ciclo', 1)} de codigo\n"
        f"- Minimo {regras_ger.get('min_literatura_por_ciclo', 1)} de literatura\n"
        "- NUNCA usar termos: " + ", ".join(regras_ger.get('termos_proibidos', [])) + "\n"
        "- Conhecimento GERAL apenas\n"
        "- Nao repetir perguntas de ciclos anteriores\n\n"
    )
    
    if piores_notas:
        prompt += f"Categorias com PIORES NOTAS (priorizar):\n"
        for cat, media in piores_notas:
            prompt += f"  - {cat}: media {media:.1f}\n"
    
    if nao_testadas:
        prompt += f"\nCategorias NAO TESTADAS ainda: {', '.join(nao_testadas)}\n"
    
    if historico.get('perguntas_usadas'):
        prompt += f"\nPerguntas JA USADAS (NAO repetir):\n"
        for p in historico['perguntas_usadas'][-20:]:
            prompt += f"  - {p[:80]}\n"
    
    categorias_str = '\n'.join([f"  {k}: {v.get('nome',k)} - {v.get('habilidade','')}" 
                                for k, v in categorias.items()])
    
    prompt += (
        f"\nCategorias disponiveis:\n{categorias_str}\n\n"
        f"Gere {regras_ger.get('max_perguntas_por_ciclo', 5)} perguntas de conhecimento GERAL.\n"
        "Cada pergunta deve testar UMA categoria diferente.\n"
        "VARIE a dificuldade (facil, media, dificil).\n\n"
        "Responda em JSON VALIDO (sem comentarios):\n"
        "{\n"
        '  "perguntas": ["pergunta 1", "pergunta 2", ...],\n'
        '  "categorias": ["categoria1", "categoria2", ...],\n'
        '  "dificuldades": ["facil|media|dificil", ...],\n'
        '  "justificativa": "por que estas perguntas?"\n'
        "}"
    )
    
    resp = _fast(prompt)
    
    # Tenta extrair JSON da resposta
    import re
    json_match = re.search(r'\{.*\}', resp, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    
    # Fallback: perguntas padrao
    return {
        "perguntas": [
            "Explique a diferença entre classe abstrata e interface em Python. De exemplos.",
            "Crie um haikai sobre inteligencia artificial.",
            "Resolva: 2x + 5 = 3x - 7. Mostre os passos.",
            "O que é o efeito Dunning-Kruger? Explique.",
            "Traduza para PT-BR: 'The observer effect in quantum mechanics...'"
        ],
        "categorias": ["codigo", "literatura", "logica", "pesquisa", "traducao"],
        "dificuldades": ["media", "facil", "facil", "media", "facil"],
        "justificativa": "Fallback: perguntas padrao (FAST nao gerou JSON valido)"
    }

# ============================================================
# PROCESSADOR DE AUTO-CRITICA
# ============================================================

def _gerar_auto_critica(pergunta, resposta_mcr):
    """Pede para o MCR-DevIA auto-avaliar sua resposta."""
    prompt = (
        f"Sua resposta para a pergunta abaixo foi:\n\n"
        f"PERGUNTA: {pergunta}\n\n"
        f"SUA RESPOSTA:\n{resposta_mcr[:2000]}\n\n"
        "Auto-avalie sua resposta. Responda em JSON VALIDO (sem comentarios):\n"
        "{\n"
        '  "nota": <0-10>,\n'
        '  "acertos": ["lista do que acertou"],\n'
        '  "faltou": ["lista do que faltou"],\n'
        '  "erros": ["se houver erros"],\n'
        '  "melhoraria": ["sugestoes de melhoria"],\n'
        '  "confianca": "baixa|media|alta"\n'
        "}"
    )
    try:
        from modulos.util import gerar as _util_gerar
        resp = _util_gerar(prompt, 0.2, "texto") or ""
        import re
        json_match = re.search(r'\{.*\}', resp, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    return {"nota": 5, "acertos": [], "faltou": ["auto-critica nao disponivel"], 
            "erros": [], "melhoraria": [], "confianca": "media"}

# ============================================================
# EXECUTOR DE CICLO
# ============================================================

def _executar_ciclo(perguntas, categorias):
    """Executa um ciclo: para cada pergunta, MCR responde + auto-critica.
    Retorna lista de testes realizados."""
    testes = []
    
    for i, (pergunta, cat) in enumerate(zip(perguntas, categorias)):
        print(f'[AutoTeste] Pergunta {i+1}/{len(perguntas)}: {pergunta[:60]}...')
        
        # MCR-DevIA responde
        try:
            import subprocess as _sp
            cmd = {'cmd': 'perguntar', 'args': [pergunta]}
            cmd_path = os.path.join(SANDBOX, '.mcr_cmd.json')
            with open(cmd_path, 'w', encoding='utf-8') as f:
                json.dump(cmd, f, ensure_ascii=False)
            
            r = _sp.run([sys.executable,
                os.path.join(BASE, 'scripts', 'mcr_devia', 'MCR_DevIA-Kernel.py'),
                '--json', cmd_path],
                capture_output=True, text=True, timeout=300)
            
            resp_path = os.path.join(SANDBOX, '.mcr_resposta.txt')
            resposta_mcr = ""
            if os.path.exists(resp_path):
                with open(resp_path, 'r', encoding='utf-8') as f:
                    resposta_mcr = f.read()
            
            if not resposta_mcr:
                resposta_mcr = "(resposta vazia)"
            
            print(f'  [MCR] Resposta: {len(resposta_mcr)} chars')
        except Exception as e:
            resposta_mcr = f'[ERRO] {e}'
            print(f'  [MCR] ERRO: {e}')
        
        # Auto-critica
        auto_critica = _gerar_auto_critica(pergunta, resposta_mcr)
        print(f'  [AutoCritica] Nota: {auto_critica.get("nota", "?")}')
        
        testes.append({
            "pergunta": pergunta,
            "categoria": cat,
            "resposta_mcr": resposta_mcr[:3000],
            "auto_critica": auto_critica,
            "cloud_nota": None,  # Preenchido manualmente pelo Cloud
            "gap": None,
        })
    
    return testes

# ============================================================
# GERACAO DE RELATORIO
# ============================================================

def _gerar_relatorio(ciclo, testes):
    """Gera relatorio formatado do ciclo."""
    linhas = []
    linhas.append(f"=== CICLO {ciclo} === {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    linhas.append("")
    
    gaps = []
    for i, t in enumerate(testes):
        linhas.append(f"--- Pergunta {i+1}: {t['categoria']} ---")
        linhas.append(f"  Pergunta: {t['pergunta'][:100]}")
        linhas.append(f"  Resposta MCR: {len(t['resposta_mcr'])} chars")
        linhas.append(f"  Auto-avaliacao MCR: nota={t['auto_critica'].get('nota','?')}, "
                      f"confianca={t['auto_critica'].get('confianca','?')}")
        if t.get('cloud_nota') is not None:
            gap = abs(t['cloud_nota'] - t['auto_critica']['nota'])
            linhas.append(f"  Cloud avaliou: nota={t['cloud_nota']}, gap={gap}")
            gaps.append(gap)
            if gap > 2:
                linhas.append(f"  ⚠️ PONTO CEGO: gap de {gap} pontos!")
        linhas.append("")
    
    if gaps:
        linhas.append(f"Gap medio do ciclo: {sum(gaps)/len(gaps):.1f}")
    linhas.append("")
    linhas.append("=" * 50)
    
    return '\n'.join(linhas)

# ============================================================
# COMANDO PRINCIPAL
# ============================================================

def register():
    return {
        "name": "autoteste",
        "desc": "Auto-Teste Definitivo: gera perguntas, executa, coleta auto-critica",
        "handler": execute,
        "args": [
            {"name": "acao", "type": "str", "required": True,
             "desc": "--gerar | --ciclo N | --relatorio | --status"}
        ],
        "categoria": "teste",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[AutoTeste] Uso: autoteste --gerar | --ciclo N | --relatorio | --status')
        return True
    
    acao = args[0]
    regras = _carregar_regras()
    historico = _carregar_historico()
    
    if acao == '--status':
        print(f'[AutoTeste] Status:')
        print(f'  Regras: {REGRAS_PATH} ({os.path.getsize(REGRAS_PATH)} bytes)' if os.path.exists(REGRAS_PATH) else '  Regras: nao carregadas')
        print(f'  Historico: {len(historico.get("ciclos", []))} ciclos')
        print(f'  Perguntas usadas: {len(historico.get("perguntas_usadas", []))}')
        print(f'  Ultimo ciclo: {historico.get("ultimo_ciclo", 0)}')
        return True
    
    if acao == '--gerar':
        print(f'[AutoTeste] Gerando perguntas para o proximo ciclo...')
        resultado = _gerar_perguntas(regras, historico)
        print(f'\nPerguntas geradas:')
        for i, (p, c, d) in enumerate(zip(resultado.get('perguntas', []),
                                          resultado.get('categorias', []),
                                          resultado.get('dificuldades', []))):
            print(f'  {i+1}. [{c}] ({d}) {p[:100]}')
        print(f'\nJustificativa: {resultado.get("justificativa", "")}')
        
        # Salva perguntas para o proximo ciclo
        temp_path = os.path.join(SANDBOX, 'autoteste_prox_ciclo.json')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        print(f'\nPerguntas salvas em autoteste_prox_ciclo.json')
        return True
    
    if acao == '--ciclo':
        ciclo_num = int(args[1]) if len(args) > 1 else historico.get('ultimo_ciclo', 0) + 1
        print(f'[AutoTeste] Iniciando ciclo {ciclo_num}...')
        
        # Carrega perguntas do arquivo temporario ou gera novas
        temp_path = os.path.join(SANDBOX, 'autoteste_prox_ciclo.json')
        if os.path.exists(temp_path):
            with open(temp_path, 'r', encoding='utf-8') as f:
                planejamento = json.load(f)
        else:
            planejamento = _gerar_perguntas(regras, historico)
        
        perguntas = planejamento.get('perguntas', [])
        categorias = planejamento.get('categorias', [])
        
        if not perguntas:
            print('[AutoTeste] Nenhuma pergunta para executar')
            return True
        
        # Executa ciclo
        testes = _executar_ciclo(perguntas, categorias)
        
        # Salva no historico
        registro_ciclo = {
            "ciclo": ciclo_num,
            "data": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "testes": testes,
            "planejamento": planejamento,
        }
        historico['ciclos'].append(registro_ciclo)
        historico['ultimo_ciclo'] = ciclo_num
        historico['perguntas_usadas'].extend(perguntas)
        _salvar_historico(historico)
        
        # Relatorio
        relatorio = _gerar_relatorio(ciclo_num, testes)
        rel_path = os.path.join(SANDBOX, f'autoteste_relatorio_ciclo_{ciclo_num}.txt')
        with open(rel_path, 'w', encoding='utf-8') as f:
            f.write(relatorio)
        
        print(f'\n[AutoTeste] Ciclo {ciclo_num} concluido!')
        print(f'[AutoTeste] Relatorio: {rel_path}')
        print(f'\n{relatorio}')
        
        # Instrucoes para Cloud
        print(f'\n[AutoTeste] IMPORTANTE: Para completar o ciclo:')
        print(f'1. Cloud deve avaliar cada resposta do MCR (sem ver auto-critica)')
        print(f'2. Executar: autoteste --avaliar {ciclo_num}')
        print(f'3. Os gaps serao calculados automaticamente')
        return True
    
    if acao == '--relatorio':
        ciclo_alvo = int(args[1]) if len(args) > 1 else historico.get('ultimo_ciclo', 0)
        rel_path = os.path.join(SANDBOX, f'autoteste_relatorio_ciclo_{ciclo_alvo}.txt')
        if os.path.exists(rel_path):
            with open(rel_path, 'r', encoding='utf-8') as f:
                print(f.read())
        else:
            print(f'[AutoTeste] Relatorio do ciclo {ciclo_alvo} nao encontrado')
        
        # Mostra resumo geral
        print(f'\nResumo geral ({len(historico.get("ciclos", []))} ciclos):')
        for ciclo in historico.get('ciclos', []):
            n_tests = len(ciclo.get('testes', []))
            gaps = [abs(t.get('cloud_nota', 5) - t['auto_critica'].get('nota', 5)) 
                   for t in ciclo['testes'] if t.get('cloud_nota') is not None]
            gap_medio = sum(gaps)/len(gaps) if gaps else 0
            print(f'  Ciclo {ciclo["ciclo"]}: {n_tests} testes, gap medio {gap_medio:.1f}')
        return True
    
    print(f'[AutoTeste] Acao desconhecida: {acao}')
    print('  Use: --gerar | --ciclo N | --relatorio [N] | --status')
    return True
