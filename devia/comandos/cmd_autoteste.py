"""Comando: autoteste - Auto-Teste Definitivo do MCR-DevIA.
Gera perguntas via FAST, executa, coleta auto-critica, avalia, salva historico.

Uso (JSON IPC):
  {"cmd": "autoteste", "args": ["--ciclo", "1"]}
  {"cmd": "autoteste", "args": ["--ciclo", "1", "--fast"]}       # Skip ToT
  {"cmd": "autoteste", "args": ["--ciclo", "1", "--fast", "--parallel"]}  # Paralelo
  {"cmd": "autoteste", "args": ["--gerar"]}        # So gera perguntas
  {"cmd": "autoteste", "args": ["--relatorio"]}    # Mostra historico
  {"cmd": "autoteste", "args": ["--status"]}        # Estado atual
"""
import os, sys, json, time, hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    return {"ciclos": [], "perguntas_usadas": [], "perguntas_fingerprints": [], "ultimo_ciclo": 0}

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
    except Exception:
        return ""

# Dominios de conhecimento por categoria (para forcar diversidade de topicos)
DOMINIOS_POR_CATEGORIA = {
    "logica": ["matematica", "raciocinio logico", "quebra-cabeca", "probabilidade", "geometria"],
    "codigo": ["algoritmos", "estruturas de dados", "design patterns", "boas praticas", "debug"],
    "literatura": ["poesia", "prosa", "figuras de linguagem", "analise literaria", "redacao"],
    "explicacao": ["ciencia", "tecnologia", "filosofia", "natureza", "sociedade"],
    "analise": ["comparacao", "critica de codigo", "detecao de erros", "otimizacao", "seguranca"],
    "pesquisa": ["historia", "biografias", "descobertas", "curiosidades", "atualidades"],
    "traducao": ["tecnico", "literario", "cientifico", "juridico", "poetico"],
    "critica": ["comparacao teorias", "etica", "impacto social", "metodo cientifico", "paradigmas"],
}


def _gerar_fingerprint_perguntas(perguntas):
    """Gera fingerprints para uma lista de perguntas."""
    return [_gerar_fingerprint(p) for p in perguntas]


def _extrair_topicos_usados(historico, max_por_cat=3):
    """Extrai topicos de perguntas anteriores para evitar repeticoes."""
    topicos_por_categoria = {}
    for ciclo in historico.get('ciclos', []):
        for teste in ciclo.get('testes', []):
            cat = teste.get('categoria', '?')
            p = teste.get('pergunta', '')
            # Extrai palavras-chave (substantivos, conceitos)
            palavras = [w for w in p.lower().split() if len(w) > 4]
            topicos = topicos_por_categoria.setdefault(cat, [])
            if len(topicos) < max_por_cat:
                topicos.append(' '.join(palavras))
    return topicos_por_categoria


def _validar_diversidade(perguntas, categorias, historico):
    """Valida se as perguntas sao diversas o suficiente.
    Retorna (valido, motivo)"""
    # 1. Fingerprint: nenhuma pergunta pode ter fingerprint igual a usada antes
    fp_usadas = set(historico.get('perguntas_fingerprints', []))
    fp_novas = _gerar_fingerprint_perguntas(perguntas)
    for fp in fp_novas:
        if fp in fp_usadas:
            return False, f"fingerprint repetido: {fp}"
    
    # 2. Nenhuma similar > 70% com perguntas usadas
    import difflib
    usadas = historico.get('perguntas_usadas', [])
    for p_nova in perguntas:
        for p_usada in usadas[-30:]:
            ratio = difflib.SequenceMatcher(None, p_nova.lower(), p_usada.lower()).ratio()
            if ratio > 0.7:
                return False, f"similaridade {ratio:.0%} com pergunta anterior: {p_usada}"
    
    # 3. Pelo menos 60% das categorias devem ser diferentes entre si
    cats_unicas = len(set(categorias))
    if len(perguntas) >= 4 and cats_unicas < len(perguntas) * 0.6:
        return False, f"pouca variedade de categorias ({cats_unicas}/{len(perguntas)})"
    
    return True, ""


def _gerar_perguntas(regras, historico):
    """FAST gera perguntas para este ciclo baseado em regras + historico."""
    categorias = regras.get('categorias', {})
    regras_ger = regras.get('regras_gerador', {})
    
    n_perguntas = regras_ger.get('max_perguntas_por_ciclo', 5)
    max_tentativas = 3
    ultimo_erro = ""
    
    # Calcula estatisticas do historico
    ultimos_ciclos = historico.get('ciclos', [])[-3:]
    gaps_por_categoria = {}
    notas_por_categoria = {}
    for ciclo in ultimos_ciclos:
        for teste in ciclo.get('testes', []):
            cat = teste.get('categoria', '?')
            gap = teste.get('gap')
            if gap is not None:
                gaps_por_categoria[cat] = gaps_por_categoria.get(cat, 0) + gap
            if 'cloud_nota' in teste and teste.get('cloud_nota') is not None:
                notas_por_categoria[cat] = notas_por_categoria.get(cat, []) + [teste['cloud_nota']]
    
    piores_notas = sorted(
        [(cat, sum(notas)/len(notas)) for cat, notas in notas_por_categoria.items()],
        key=lambda x: x[1]
    ) if notas_por_categoria else []
    
    # Categorias nao testadas ainda
    testadas = set()
    for ciclo in historico.get('ciclos', []):
        for teste in ciclo.get('testes', []):
            testadas.add(teste.get('categoria', ''))
    nao_testadas = [c for c in categorias if c not in testadas]
    
    # Topicos usados em ciclos anteriores
    topicos_usados = _extrair_topicos_usados(historico)
    
    for tentativa in range(max_tentativas):
        prompt = (
            "VOCE E O GERADOR DE TESTES DO MCR-DevIA.\n"
            "VOCE DEVE CRIAR PERGUNTAS DIVERSIFICADAS E ORIGINAIS.\n\n"
            "Regras:\n"
            f"- EXATAMENTE {n_perguntas} perguntas\n"
            f"- Minimo {regras_ger.get('min_codigo_por_ciclo', 1)} de codigo\n"
            f"- Minimo {regras_ger.get('min_literatura_por_ciclo', 1)} de literatura\n"
            "- NUNCA usar termos: " + ", ".join(regras_ger.get('termos_proibidos', [])) + "\n"
            "- Conhecimento GERAL apenas (sem termos tecnicos de MCR/Tibia)\n"
            "- Nao repetir perguntas de ciclos anteriores\n"
            "- VARIE OS TOPICOS: cada pergunta deve explorar um dominio DIFERENTE\n"
            "- VARIE AS DIFICULDADES: pelo menos uma facil, uma media, uma dificil\n\n"
        )
        
        if piores_notas:
            prompt += f"Categorias com PIORES NOTAS (priorizar):\n"
            for cat, media in piores_notas:
                prompt += f"  - {cat}: media {media:.1f}\n"
        
        if nao_testadas:
            prompt += f"\nCategorias NAO TESTADAS ainda (priorizar): {', '.join(nao_testadas)}\n"
        
        if historico.get('perguntas_usadas'):
            prompt += f"\nPerguntas de ciclos ANTERIORES (NAO repetir o assunto):\n"
            for p in historico['perguntas_usadas'][-15:]:
                prompt += f"  - {p}\n"
        
        # Adiciona topicos usados por categoria para evitar repeticoes
        if topicos_usados:
            prompt += f"\nTopicos JA COBERTOS (evitar repeticao de assunto):\n"
            for cat, topicos in topicos_usados.items():
                prompt += f"  {cat}: {' | '.join(topicos)}\n"
        
        # Dominios disponiveis por categoria
        prompt += "\nCategorias e dominios disponiveis:\n"
        for cat_key, cat_info in categorias.items():
            dominios = DOMINIOS_POR_CATEGORIA.get(cat_key, ["geral"])
            prompt += f"  {cat_key} ({cat_info['nome']}): dominios = {', '.join(dominios)}\n"
        
        prompt += (
            f"\nEscolha UMA categoria e UM dominio DIFERENTE para cada pergunta.\n"
            f"Nenhuma pergunta pode repetir o mesmo dominio ou assunto de ciclos anteriores.\n\n"
            "Responda em JSON VALIDO (sem comentarios, sem markdown):\n"
            "{\n"
            '  "perguntas": ["pergunta 1", "pergunta 2", ...],\n'
            '  "categorias": ["categoria1", "categoria2", ...],\n'
            '  "dificuldades": ["facil|media|dificil", ...],\n'
            '  "justificativa": "por que estas perguntas sao diversas?"\n'
            "}"
        )
        
        resp = _fast(prompt)
        
        # Tenta extrair JSON da resposta
        import re
        json_match = re.search(r'\{.*\}', resp, re.DOTALL)
        if not json_match:
            ultimo_erro = "FAST nao retornou JSON valido"
            continue
        
        try:
            resultado = json.loads(json_match.group())
        except Exception:
            ultimo_erro = "FAST retornou JSON mal formatado"
            continue
        
        perguntas = resultado.get('perguntas', [])
        cats = resultado.get('categorias', [])
        
        # Valida quantidade
        if len(perguntas) != n_perguntas:
            ultimo_erro = f"FAST gerou {len(perguntas)} perguntas, esperado {n_perguntas}"
            continue
        
        if len(cats) != len(perguntas):
            ultimo_erro = f"FAST gerou {len(cats)} categorias para {len(perguntas)} perguntas"
            continue
        
        # Valida diversidade
        valido, motivo = _validar_diversidade(perguntas, cats, historico)
        if not valido:
            ultimo_erro = motivo
            continue  # Sempre continua, nunca cai no return se falhou
        
        # Sucesso
        return resultado
    
    # Se todas as tentativas falharam, usa fallback variado
    print(f'[AutoTeste] Apos {max_tentativas} tentativas, todas falharam na validacao.')
    print(f'[AutoTeste] Gerador FAST falhou ({ultimo_erro}). Usando fallback variado.')
    
    # Fallback com variacao baseada no historico (20 opcoes para evitar repeticoes)
    usadas = set(historico.get('perguntas_fingerprints', []))
    fallbacks = [
        ("Explique o principio de funcionamento de um motor de combustao interna.", "explicacao", "media"),
        ("Escreva um algoritmo em pseudocodigo para ordenar uma lista de numeros.", "codigo", "media"),
        ("O que e a teoria da deriva continental? Quem a propos?", "pesquisa", "facil"),
        ("Crie uma metafora poetica sobre o ciclo da agua na natureza.", "literatura", "facil"),
        ("Analise o impacto dos microplasticos nos oceanos.", "critica", "dificil"),
        ("Qual a diferenca entre IPv4 e IPv6? Explique em termos simples.", "explicacao", "facil"),
        ("Escreva uma funcao Python que valide se uma string e um palindromo.", "codigo", "facil"),
        ("Resolva o problema: Se 3 gatos pegam 3 ratos em 3 minutos, quantos gatos pegam 100 ratos em 100 minutos?", "logica", "dificil"),
        ("Explique o que e a computacao em nuvem (cloud computing) com exemplos.", "explicacao", "facil"),
        ("Traduza para portugues: 'The only way to do great work is to love what you do.'", "traducao", "facil"),
        ("Compare e contraste a energia solar com a energia eolica.", "critica", "media"),
        ("O que e um banco de dados relacional? Diferencie de NoSQL.", "pesquisa", "media"),
        ("Crie um dialogo entre um atomo de hidrogenio e um de oxigenio.", "literatura", "dificil"),
        ("Analise o codigo: x = 10; y = x + '5'. Qual o erro e por que?", "analise", "media"),
        ("Explique a diferenca entre HTTP e HTTPS.", "explicacao", "facil"),
        ("Implemente uma pilha (stack) usando uma lista em Python.", "codigo", "dificil"),
        ("Qual a probabilidade de sair cara 3 vezes seguidas em uma moeda honesta?", "logica", "media"),
        ("O que foi o Projeto Genoma Humano e qual sua importancia?", "pesquisa", "facil"),
        ("Crie um haikai sobre inteligencia artificial.", "literatura", "facil"),
        ("Traduza mantendo o tom formal: 'Dear Sir, we hereby confirm your appointment.'", "traducao", "media"),
    ]
    
    # Pega as primeiras N que nao foram usadas
    selecionadas = []
    for p, c, d in fallbacks:
        fp = _gerar_fingerprint(p)
        if fp not in usadas:
            selecionadas.append((p, c, d))
        if len(selecionadas) >= n_perguntas:
            break
    
    if len(selecionadas) < n_perguntas:
        selecionadas = fallbacks
    
    return {
        "perguntas": [s[0] for s in selecionadas],
        "categorias": [s[1] for s in selecionadas],
        "dificuldades": [s[2] for s in selecionadas],
        "justificativa": f"Fallback variado ({ultimo_erro})"
    }

# ============================================================
# PROCESSADOR DE AUTO-CRITICA (individual e batch)
# ============================================================

def _gerar_auto_critica(pergunta, resposta_mcr):
    """Pede para o MCR-DevIA auto-avaliar sua resposta."""
    prompt = (
        f"Sua resposta para a pergunta abaixo foi:\n\n"
        f"PERGUNTA: {pergunta}\n\n"
        f"SUA RESPOSTA:\n{resposta_mcr}\n\n"
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
    except Exception:
        pass
    return {"nota": 5, "acertos": [], "faltou": ["auto-critica nao disponivel"], 
            "erros": [], "melhoraria": [], "confianca": "media"}


def _gerar_auto_critica_batch(perguntas_respostas):
    """Batch auto-critica: avalia TODAS as respostas em UMA chamada LLM.
    
    Args:
        perguntas_respostas: lista de (pergunta, resposta) tuples
    
    Returns:
        lista de dicts de auto-critica (mesmo formato que _gerar_auto_critica)
    """
    if not perguntas_respostas:
        return []
    
    # Monta o prompt com todas as perguntas + respostas
    blocos = []
    for i, (pergunta, resposta) in enumerate(perguntas_respostas):
        blocos.append(
            f"--- PERGUNTA {i+1} ---\n"
            f"Pergunta: {pergunta}\n"
            f"Resposta: {resposta}\n"
        )
    
    prompt = (
        "Voce e o AUTO-AVALIADOR do MCR-DevIA.\n"
        "Avalie as respostas abaixo. Para CADA pergunta, retorne:\n"
        '  "nota": <0-10>,\n'
        '  "acertos": ["lista"],\n'
        '  "faltou": ["lista"],\n'
        '  "erros": ["se houver"],\n'
        '  "melhoraria": ["sugestoes"],\n'
        '  "confianca": "baixa|media|alta"\n\n'
        f"{chr(10).join(blocos)}\n"
        "Responda em JSON VALIDO (array de objetos, um por pergunta):\n"
        "[\n"
        '  {"pergunta": 1, "nota": ..., "acertos": [...], "faltou": [...], "erros": [...], "melhoraria": [...], "confianca": "..."},\n'
        "  ...\n"
        "]"
    )
    
    try:
        from modulos.util import gerar as _util_gerar
        resp = _util_gerar(prompt, 0.2, "texto") or ""
        import re
        json_match = re.search(r'\[.*\]', resp, re.DOTALL)
        if json_match:
            resultados = json.loads(json_match.group())
            # Reorganiza por indice
            avaliacoes = {}
            for r in resultados:
                idx = r.get('pergunta', 0) - 1
                avaliacoes[idx] = {
                    "nota": r.get('nota', 5),
                    "acertos": r.get('acertos', []),
                    "faltou": r.get('faltou', []),
                    "erros": r.get('erros', []),
                    "melhoraria": r.get('melhoraria', []),
                    "confianca": r.get('confianca', 'media'),
                }
            # Preenche indices faltantes
            resultado_final = []
            for i in range(len(perguntas_respostas)):
                resultado_final.append(avaliacoes.get(i, {
                    "nota": 5, "acertos": [], "faltou": ["auto-critica batch falhou"],
                    "erros": [], "melhoraria": [], "confianca": "media"
                }))
            return resultado_final
    except Exception:
        pass
    
    # Fallback: individual
    return [_gerar_auto_critica(p, r) for p, r in perguntas_respostas]


# ============================================================
# EXECUTOR DE PERGUNTA INDIVIDUAL
# ============================================================

def _gerar_fingerprint(texto):
    """Gera uma fingerprint unica para uma pergunta (normalizada)."""
    import re
    t = texto.lower().strip()
    t = re.sub(r'[^a-záéíóúâêôãõç0-9\s]', '', t)
    # Ordena palavras para capturar sinonimos de mesma essencia
    palavras = sorted(t.split())
    return hashlib.md5(' '.join(palavras).encode()).hexdigest()


def _detectar_resposta_lixo(resposta):
    """Detecta se resposta e lixo (timestamp, vazia, muito curta).
    
    Returns:
        (bool, str): (eh_lixo, motivo)
    """
    if not resposta or len(resposta.strip()) < 50:
        return True, f"muito curta ({len(resposta)} chars)"
    
    # Padrao de timestamp: "Sao 09:11:06 do dia 28/06/2026"
    import re
    if re.match(r'^S[ãa]o?\s+\d{2}:\d{2}:\d{2}\s+do\s+dia\s+\d{2}/\d{2}/\d{4}', resposta.strip()):
        return True, "timestamp em vez de resposta"
    if re.match(r'^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}', resposta.strip()):
        return True, "data/hora em vez de resposta"
    
    return False, ""


def _executar_pergunta(pergunta, modo_fast=False, timeout=180, tentativa=1):
    """Executa UMA pergunta no MCR-DevIA via subprocess.
    
    Args:
        pergunta: texto da pergunta
        modo_fast: se True, adiciona flag para pular ToT
        timeout: timeout em segundos
        tentativa: numero da tentativa (1-based)
    
    Returns:
        (resposta_str, erro_str)
    """
    import subprocess as _sp
    import re as _re
    
    max_tentativas = 3
    
    # Prepara comando
    pergunta_mod = pergunta
    env = os.environ.copy()
    if modo_fast:
        env['MCR_SKIP_TOT'] = '1'
        timeout = min(timeout, 120)
    
    # Se e retentativa, reforca para ser detalhado
    if tentativa > 1:
        pergunta_mod = (
            f"{pergunta}\n\n"
            f"IMPORTANTE: Seja DETALHADO e COMPLETO. Forneca exemplos, explicacoes "
            f"e contextos. Nao responda apenas com data/hora ou uma frase curta. "
            f"Sua resposta deve ter NO MINIMO 200 caracteres."
        )
    
    cmd = {'cmd': 'perguntar', 'args': [pergunta_mod]}
    cmd_path = os.path.join(SANDBOX, '.mcr_cmd.json')
    with open(cmd_path, 'w', encoding='utf-8') as f:
        json.dump(cmd, f, ensure_ascii=False)
    
    resposta_mcr = ""
    erro = None
    
    try:
        r = _sp.run([sys.executable,
            os.path.join(BASE, 'scripts', 'mcr_devia', 'MCR_DevIA-Kernel.py'),
            '--json', cmd_path],
            capture_output=True, text=True, timeout=timeout, env=env)
        
        resp_path = os.path.join(SANDBOX, '.mcr_resposta.txt')
        if os.path.exists(resp_path):
            with open(resp_path, 'r', encoding='utf-8') as f:
                resposta_mcr = f.read()
        
        if not resposta_mcr:
            resposta_mcr = "(resposta vazia)"
    except _sp.TimeoutExpired:
        resposta_mcr = ""
        erro = f"TIMEOUT ({timeout}s)"
    except Exception as e:
        resposta_mcr = ""
        erro = str(e)
    
    # Detecta lixo e faz retry
    if not erro:
        eh_lixo, motivo = _detectar_resposta_lixo(resposta_mcr)
        if eh_lixo and tentativa < max_tentativas:
            print(f'  [Retry {tentativa}/{max_tentativas-1}] Resposta {motivo}. Re-executando...')
            return _executar_pergunta(pergunta, modo_fast, timeout, tentativa + 1)
    
    if erro:
        return resposta_mcr, erro
    return resposta_mcr, None


# ============================================================
# EXECUTOR DE CICLO
# ============================================================

def _executar_ciclo(perguntas, categorias, modo_fast=False, paralelo=False):
    """Executa um ciclo: para cada pergunta, MCR responde + auto-critica.
    
    Args:
        perguntas: lista de perguntas
        categorias: lista de categorias correspondentes
        modo_fast: se True, pula ToT (mais rapido, qualidade similar)
        paralelo: se True, executa perguntas em paralelo (so modo_fast)
    
    Returns:
        lista de testes realizados
    """
    from modulos.progress_tracker import iniciar as _trk_iniciar, reportar as _trk_report, concluir as _trk_concluir
    
    n_perguntas = len(perguntas)
    testes = []
    
    _trk_iniciar(pipeline='autoteste', question_total=n_perguntas)
    print(f'[AutoTeste] Modo: {"FAST" if modo_fast else "COMPLETO"}{" + PARALELO" if paralelo else ""}')
    print(f'[AutoTeste] Executando {n_perguntas} perguntas...')
    
    if paralelo and modo_fast:
        # ====================================================
        # MODO PARALELO (so fast): executa perguntas em threads
        # ====================================================
        timeout = 120
        with ThreadPoolExecutor(max_workers=min(3, n_perguntas)) as executor:
            futuros = {}
            for i, (pergunta, cat) in enumerate(zip(perguntas, categorias)):
                _trk_report('AutoTeste', f'submetendo pergunta {i+1}', i / n_perguntas, i+1)
                futuros[executor.submit(_executar_pergunta, pergunta, modo_fast, timeout)] = (i, pergunta, cat)
            
            # Coleta resultados conforme terminam
            resultados_parciais = {}
            for futuro in as_completed(futuros):
                idx, pergunta, cat = futuros[futuro]
                resposta, erro = futuro.result()
                resultados_parciais[idx] = (resposta, erro, pergunta, cat)
                _trk_report('AutoTeste', f'pergunta {idx+1} concluida', (idx + 1) / n_perguntas, idx+1)
                print(f'  [Pergunta {idx+1}] {"ERRO: "+erro if erro else f"OK ({len(resposta)} chars)"}')
            
            # Monta lista na ordem original
            for i in range(n_perguntas):
                if i in resultados_parciais:
                    resposta, erro, pergunta, cat = resultados_parciais[i]
                else:
                    resposta, erro, pergunta, cat = "", "PERDIDA", perguntas[i], categorias[i]
                
                if erro:
                    resposta_mcr = f'[ERRO] {erro}'
                else:
                    resposta_mcr = resposta
                
                testes.append({
                    "pergunta": pergunta,
                    "categoria": cat,
                    "resposta_mcr": resposta_mcr,
                    "auto_critica": None,  # Sera preenchido no batch
                    "cloud_nota": None,
                    "gap": None,
                    "erro": erro if erro else None,
                })
    else:
        # ====================================================
        # MODO SEQUENCIAL: executa uma pergunta de cada vez
        # ====================================================
        timeout = 120 if modo_fast else 180
        for i, (pergunta, cat) in enumerate(zip(perguntas, categorias)):
            _trk_report('AutoTeste', f'pergunta {i+1}/{n_perguntas}', i / n_perguntas, i+1)
            print(f'\n[AutoTeste] Pergunta {i+1}/{n_perguntas}: {pergunta}...')
            
            resposta, erro = _executar_pergunta(pergunta, modo_fast, timeout)
            
            if erro:
                resposta_mcr = f'[ERRO] {erro}'
                print(f'  [MCR] ERRO: {erro}')
            else:
                resposta_mcr = resposta
                print(f'  [MCR] Resposta: {len(resposta_mcr)} chars')
            
            testes.append({
                "pergunta": pergunta,
                "categoria": cat,
                "resposta_mcr": resposta_mcr,
                "auto_critica": None,  # Sera preenchido no batch
                "cloud_nota": None,
                "gap": None,
                "erro": erro if erro else None,
            })
    
    # ====================================================
    # AUTO-CRITICA EM BATCH (1 LLM call para todas)
    # ====================================================
    _trk_report('AutoCritica', 'avaliando respostas em batch', 0.85)
    print(f'\n[AutoTeste] Gerando auto-critica em batch...')
    
    perguntas_respostas = [(t['pergunta'], t['resposta_mcr']) for t in testes]
    auto_criticas = _gerar_auto_critica_batch(perguntas_respostas)
    
    for i, ac in enumerate(auto_criticas):
        testes[i]['auto_critica'] = ac
        print(f'  [Pergunta {i+1}] Auto-critica: nota={ac.get("nota", "?")}, confianca={ac.get("confianca", "?")}')
    
    # Se batch produziu menos resultados que perguntas, preenche com individuais
    for i, t in enumerate(testes):
        if t.get('auto_critica') is None:
            _trk_report('AutoCritica', f'fallback individual {i+1}', 0.9 + (i * 0.02))
            t['auto_critica'] = _gerar_auto_critica(t['pergunta'], t['resposta_mcr'])
    
    _trk_concluir()
    print()
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
        linhas.append(f"  Pergunta: {t['pergunta']}")
        linhas.append(f"  Resposta MCR: {len(t['resposta_mcr'])} chars")
        erro = t.get('erro')
        if erro:
            linhas.append(f"  ERRO: {erro}")
        ac = t.get('auto_critica', {})
        linhas.append(f"  Auto-avaliacao MCR: nota={ac.get('nota','?')}, "
                      f"confianca={ac.get('confianca','?')}")
        if t.get('cloud_nota') is not None:
            gap = abs(t['cloud_nota'] - ac.get('nota', 5))
            linhas.append(f"  Cloud avaliou: nota={t['cloud_nota']}, gap={gap}")
            gaps.append(gap)
            if gap > 2:
                linhas.append(f"  PONTO CEGO: gap de {gap} pontos!")
        linhas.append("")
    
    if gaps:
        linhas.append(f"Gap medio do ciclo: {sum(gaps)/len(gaps):.1f}")
        pct_cego = sum(1 for g in gaps if g > 2) / len(gaps) * 100 if gaps else 0
        linhas.append(f"Pontos cegos: {pct_cego:.0f}% das questoes")
    linhas.append("")
    linhas.append("=" * 50)
    
    return '\n'.join(linhas)


# ============================================================
# WATCH - DASHBOARD TERMINAL
# ============================================================

def _watch():
    """Exibe dashboard textual do progresso, atualizando a cada 2s."""
    import time as _time
    try:
        while True:
            estado = None
            if os.path.exists(os.path.join(SANDBOX, '.mcr_progress.json')):
                with open(os.path.join(SANDBOX, '.mcr_progress.json'), 'r', encoding='utf-8') as f:
                    estado = json.load(f)
            
            if not estado:
                print("[Watch] Nenhum progresso detectado. Aguardando...")
            else:
                status = estado.get('status', 'idle')
                stage = estado.get('stage', '?')
                progress = estado.get('progress', 0)
                pct = int(progress * 100)
                elapsed = estado.get('elapsed', 0)
                eta = estado.get('eta')
                q_current = estado.get('question_current', 0)
                q_total = estado.get('question_total', 0)
                q_info = f"  Pergunta {q_current}/{q_total}" if q_total else ""
                eta_info = f"  ETA: {eta}s" if eta else ""
                pipeline = estado.get('pipeline', '')
                
                # Barra
                bar_len = 20
                filled = int(bar_len * progress)
                bar = '#' * filled + '-' * (bar_len - filled)
                
                # Historia de stages
                history = estado.get('stages_history', [])
                hist_lines = []
                for h in history[-5:]:  # Ultimos 5
                    h_stage = h.get('stage', '?')
                    h_elapsed = h.get('elapsed', 0)
                    hist_lines.append(f"    {h_stage}: {h_elapsed}s")
                
                print(f"\r[{bar}] {pct:3d}% | {stage}{q_info}{eta_info}  ", end="")
                if status == 'completed':
                    print(f"\n[Watch] Pipeline concluido em {elapsed:.1f}s")
                    break
                elif status == 'error':
                    print(f"\n[Watch] ERRO: {estado.get('error', 'desconhecido')}")
                    break
            _time.sleep(2)
    except KeyboardInterrupt:
        print("\n[Watch] Interrompido")


# ============================================================
# COMANDO PRINCIPAL
# ============================================================

def register():
    return {
        "name": "autoteste",
        "desc": "Auto-Teste Definitivo: gera perguntas, executa, coleta auto-critica. Use --fast para skip ToT, --parallel para execucao paralela.",
        "handler": execute,
        "args": [
            {"name": "acao", "type": "str", "required": True,
             "desc": "--gerar | --ciclo N [--fast] [--parallel] | --relatorio | --status | --watch"}
        ],
        "categoria": "teste",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[AutoTeste] Uso: autoteste --gerar | --ciclo N [--fast] [--parallel] | --relatorio [N] | --status | --watch')
        return True
    
    # Extrai flags
    acao = args[0]
    modo_fast = '--fast' in args
    paralelo = '--parallel' in args
    
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
            print(f'  {i+1}. [{c}] ({d}) {p}')
        print(f'\nJustificativa: {resultado.get("justificativa", "")}')
        
        # Salva perguntas para o proximo ciclo
        temp_path = os.path.join(SANDBOX, 'autoteste_prox_ciclo.json')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        print(f'\nPerguntas salvas em autoteste_prox_ciclo.json')
        return True
    
    if acao == '--watch':
        _watch()
        return True
    
    if acao == '--ciclo':
        # Extrai numero do ciclo (primeiro argumento não-flag)
        ciclo_num = None
        for a in args[1:]:
            if a.startswith('--'):
                continue
            try:
                ciclo_num = int(a)
                break
            except Exception:
                continue
        if ciclo_num is None:
            ciclo_num = historico.get('ultimo_ciclo', 0) + 1
        
        print(f'[AutoTeste] Iniciando ciclo {ciclo_num}...')
        print(f'[AutoTeste] Flags: {"--fast" if modo_fast else ""} {"--parallel" if paralelo else ""}')
        
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
        
        # Executa ciclo (com as flags)
        testes = _executar_ciclo(perguntas, categorias, modo_fast=modo_fast, paralelo=paralelo)
        
        # Salva no historico
        registro_ciclo = {
            "ciclo": ciclo_num,
            "data": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "testes": testes,
            "planejamento": planejamento,
            "modo": "fast" if modo_fast else "completo",
            "paralelo": paralelo,
        }
        historico['ciclos'].append(registro_ciclo)
        historico['ultimo_ciclo'] = ciclo_num
        historico['perguntas_usadas'].extend(perguntas)
        # Salva fingerprints para deteccao de repeticoes futuras
        if 'perguntas_fingerprints' not in historico:
            historico['perguntas_fingerprints'] = []
        historico['perguntas_fingerprints'].extend(_gerar_fingerprint_perguntas(perguntas))
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
        ciclo_alvo = None
        for a in args[1:]:
            if a.startswith('--'):
                continue
            try:
                ciclo_alvo = int(a)
                break
            except Exception:
                continue
        if ciclo_alvo is None:
            ciclo_alvo = historico.get('ultimo_ciclo', 0)
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
            modo = ciclo.get('modo', 'completo')
            paralelo = ciclo.get('paralelo', False)
            gaps = [abs(t.get('cloud_nota', 5) - t['auto_critica'].get('nota', 5)) 
                   for t in ciclo['testes'] if t.get('cloud_nota') is not None]
            gap_medio = sum(gaps)/len(gaps) if gaps else 0
            print(f'  Ciclo {ciclo["ciclo"]}: {n_tests} testes, gap medio {gap_medio:.1f} [{modo}{"+paralelo" if paralelo else ""}]')
        return True
    
    print(f'[AutoTeste] Acao desconhecida: {acao}')
    print('  Use: --gerar | --ciclo N [--fast] [--parallel] | --relatorio [N] | --status | --watch')
    return True
