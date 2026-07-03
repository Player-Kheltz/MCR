"""Self-Study — Auto-conhecimento do MCR-DevIA.
Extraido de master_agent.py para modularizacao.

Escaneia o proprio codigo fonte, extrai metricas, gera
insights de melhoria, e aprende no KG (ctx='self_knowledge').
"""
import os, time, json as _json
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class SelfStudyEngine:
    """Motor de auto-conhecimento — escaneia, mede, sugere."""
    
    def __init__(self, ia, kg, log_callback=None, execution_count_getter=None):
        self._ia = ia
        self._kg = kg
        self._log = log_callback or (lambda e, m: None)
        self._get_count = execution_count_getter or (lambda: 0)
        self._tools = None  # lazy load
    
    def escanear_projeto(self, max_arquivos=60):
        """Escaneia o projeto em ordem de prioridade, ignorando lixo."""
        DIRS = [
            ('modulos', os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos')),
            ('scripts', os.path.join(BASE, 'Scripts', 'mcr_devia')),
            ('docs', os.path.join(BASE, 'docs')),
        ]
        EXCLUIR_PASTAS = {'Legado', '.git', '__pycache__', 'node_modules', 'temp', 'Temp',
                          '.mcr_devia', 'comandos', 'hooks'}
        EXCLUIR_PREFIXOS = {'_v', 'gerador_shc_', 'mcr_crew_v', 'mcr_learning_scan',
                            'auto_fixer_', 'backup_', 'benchmark', 'corrida_', 'comparacao_'}
        EXTS = {'.py', '.html', '.md'}
        arquivos = []
        vistos = set()
        
        for nome, diretorio in DIRS:
            if not os.path.exists(diretorio):
                continue
            for raiz, pastas, fnames in os.walk(diretorio):
                pastas[:] = [p for p in pastas if p not in EXCLUIR_PASTAS and not p.startswith('.')]
                for fname in fnames:
                    if os.path.splitext(fname)[1].lower() not in EXTS:
                        continue
                    if any(fname.startswith(p) for p in EXCLUIR_PREFIXOS):
                        continue
                    caminho = os.path.join(raiz, fname)
                    if caminho in vistos:
                        continue
                    vistos.add(caminho)
                    try:
                        stat = os.stat(caminho)
                        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                            linhas = f.readlines()
                        classes = []
                        funcoes = []
                        for linha in linhas:
                            ls = linha.strip()
                            if ls.startswith('class '):
                                classes.append(ls.split('(')[0].split(':')[0].replace('class ','').strip())
                            elif ls.startswith('def '):
                                funcoes.append(ls.split('(')[0].replace('def ','').strip())
                        arquivos.append({
                            'nome': fname, 'caminho': caminho, 'dir_prio': nome,
                            'ext': os.path.splitext(fname)[1].lower(),
                            'linhas': len(linhas), 'bytes': stat.st_size,
                            'modificado': stat.st_mtime,
                            'classes': classes, 'funcoes': funcoes,
                            'imports': [],
                        })
                    except Exception:
                        pass
                    if len(arquivos) >= max_arquivos:
                        return arquivos
        
        # Prioridade 2: sandbox (limitado)
        sandbox_dir = os.path.join(BASE, 'sandbox')
        if os.path.exists(sandbox_dir) and len(arquivos) < max_arquivos:
            for fname in os.listdir(sandbox_dir):
                if len(arquivos) >= max_arquivos:
                    break
                if not fname.endswith(('.py', '.html', '.md')):
                    continue
                if fname.startswith('.') or fname.startswith('_'):
                    continue
                if any(fname.startswith(p) for p in EXCLUIR_PREFIXOS):
                    continue
                caminho = os.path.join(sandbox_dir, fname)
                if caminho in vistos:
                    continue
                vistos.add(caminho)
                try:
                    stat = os.stat(caminho)
                    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                        linhas = f.readlines()
                    classes = [l.strip().split('(')[0].replace('class ','') for l in linhas if l.strip().startswith('class ')]
                    funcoes = [l.strip().split('(')[0].replace('def ','') for l in linhas if l.strip().startswith('def ')]
                    arquivos.append({
                        'nome': fname, 'caminho': caminho, 'dir_prio': 'sandbox',
                        'ext': '.py' if fname.endswith('.py') else '.html' if fname.endswith('.html') else '.md',
                        'linhas': len(linhas), 'bytes': stat.st_size, 'modificado': stat.st_mtime,
                        'classes': classes, 'funcoes': funcoes, 'imports': [],
                    })
                except Exception:
                    pass
        return arquivos
    
    def extrair_metricas(self, arquivos):
        """Calcula metricas a partir dos arquivos escaneados."""
        modulos = [a for a in arquivos if a['ext'] == '.py' and a['dir_prio'] != 'sandbox']
        total_linhas = sum(a['linhas'] for a in arquivos)
        total_classes = sum(len(a['classes']) for a in modulos)
        total_funcoes = sum(len(a['funcoes']) for a in modulos)
        top5 = sorted(arquivos, key=lambda a: -a['linhas'])
        complexos = sorted(modulos, key=lambda a: -len(a['funcoes']))
        return {
            'total_arquivos': len(arquivos),
            'total_modulos': len(modulos),
            'total_linhas': total_linhas,
            'total_classes': total_classes,
            'total_funcoes': total_funcoes,
            'media_linhas_arquivo': round(total_linhas / max(len(arquivos), 1)),
            'top5_maiores': [{'nome': a['nome'], 'linhas': a['linhas'], 'caminho': a['caminho'],
                              'classes': len(a['classes']), 'funcoes': len(a['funcoes']),
                              'dir_prio': a['dir_prio'], 'ext': a.get('ext', '.py')} for a in top5],
            'top5_complexos': [{'nome': a['nome'], 'funcoes': len(a['funcoes']),
                                'classes': len(a['classes']), 'linhas': a['linhas']} for a in complexos],
        }
    
    def _analisar_anti_patterns(self, arquivos):
        """Analisa codigo fonte em busca de anti-patterns com categorizacao granular.
        
        Retorna dict: {nome_padrao: [(arquivo, linha, contexto, linha_try, severidade)]}
        Agora separa except: bare de except Exception e except (X,Y).
        Mostra contexto (linha do try) para cada except problematico.
        """
        import re as _re
        resultados = {}
        
        # Padroes com severidade: CRITICAL, HIGH, MEDIUM, LOW, INFO
        PADROES = [
            # 🔴 CRITICAL — erro engolido sem rastro
            ('except: pass',          r'^\s*except\s*:\s*pass\s*$',               'CRITICAL'),
            
            # 🔴 HIGH — captura SystemExit, KeyboardInterrupt
            ('except: bare',          r'^\s*except\s*:(?!\s*(?:pass|Exception|\())', 'HIGH'),
            
            # 🟡 MEDIUM — codigo incompleto
            ('FIXME',                 r'\bFIXME\b',                               'MEDIUM'),
            ('HACK',                  r'\bHACK\b',                                'MEDIUM'),
            ('blocos try (INFO)',      r'^\s*try\s*:',                               'INFO'),
            
            # 🟢 LOW — boas praticas
            ('TODO',                  r'\bTODO\b(?!\s*FIXME)',                    'LOW'),
            ('import *',              r'^\s*from\s+\S+\s+import\s+\*\s*$',        'LOW'),
            ('if len(...)',           r'if\s+len\(.*\)\s*[>!]=?\s*0',             'LOW'),
            ('# type: ignore s/justif', r'# type: ignore\s*$',                    'LOW'),
        ]
        
        for a in arquivos:
            if a.get('ext') != '.py':
                continue
            caminho = a['caminho']
            try:
                with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                    linhas = f.readlines()
            except Exception:
                continue
            
            for linha_num, linha in enumerate(linhas, 1):
                for nome_padrao, regex, severidade in PADROES:
                    if _re.search(regex, linha):
                        # Para except:bare, tenta achar a linha do try anterior
                        linha_try = ""
                        if 'bare' in nome_padrao or 'pass' in nome_padrao:
                            # Procura pra tras ate encontrar o try
                            for tr in range(linha_num - 2, max(0, linha_num - 10), -1):
                                if linhas[tr].strip().startswith('try:'):
                                    linha_try = linhas[tr].strip()
                                    break
                        
                        resultados.setdefault(nome_padrao, []).append({
                            'arquivo': a['nome'],
                            'linha': linha_num,
                            'codigo': linha.strip(),
                            'linha_try': linha_try,
                            'severidade': severidade,
                        })
        
        return resultados
    
    def _revisar_funcoes_suspeitas(self, arquivos):
        """Encontra funcoes mais complexas dos top arquivos e pede revisao LLM.
        
        Retorna string com revisoes das 3 funcoes mais suspeitas.
        """
        from modulos.sse_server import emit
        
        # Pega os .py e ordena por tamanho
        py_files = sorted([a for a in arquivos if a.get('ext') == '.py' and a['dir_prio'] != 'sandbox'],
                          key=lambda a: -a['linhas'])
        
        if not py_files:
            return ""
        
        resultados = []
        
        for a in py_files:
            caminho = a['caminho']
            nome = a['nome']
            try:
                with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                    linhas = f.readlines()
            except Exception:
                continue
            
            # Encontra funcoes e mede seus tamanhos (de def ate proximo def/fim)
            funcoes = []
            inicio_funcao = None
            nome_funcao = None
            for i, linha in enumerate(linhas):
                if linha.strip().startswith('def ') and '):' in linha:
                    if inicio_funcao is not None:
                        funcoes.append((nome_funcao, i - inicio_funcao, inicio_funcao, i))
                    nome_funcao = linha.strip().split('(')[0].replace('def ', '')
                    inicio_funcao = i
            if inicio_funcao is not None:
                funcoes.append((nome_funcao, len(linhas) - inicio_funcao, inicio_funcao, len(linhas)))
            
            # Funcao mais longa
            if funcoes:
                maior = max(funcoes, key=lambda x: x[1])
                f_nome, f_tam, f_ini, f_fim = maior
                
                if f_tam > 30:  # So revisa se tiver mais de 30 linhas
                    codigo = ''.join(linhas[f_ini:f_fim])
                    emit('narrator', f'Revisando funcao {f_nome} ({f_tam} linhas) em {nome}...')
                    
                    prompt = (f"[SISTEMA]\nVoce e um REVISOR DE CODIGO critico e detalhista.\n"
                              f"[ARQUIVO]\n{nome}\n[FUNCAO]\n{f_nome} ({f_tam} linhas)\n\n"
                              f"[CODIGO]\n{codigo}\n\n[PERGUNTA]\n"
                              f"Que problemas voce ve nesta funcao? (complexidade, bugs, performance, legibilidade)\n"
                              f"Seja ESPECIFICO: aponte linhas exatas e sugira correcoes.\n"
                              f"Se a funcao estiver OK, diga 'OK'.\nResponda em PT-BR.")
                    
                    resultado = self._ia.gerar(prompt, 0.2, 'leve') or ""
                    if resultado and 'OK' not in resultado:
                        resultados.append(f"### {nome}/{f_nome} ({f_tam} linhas)\n{resultado.strip()}")
        
        return '\n\n'.join(resultados) if resultados else ""

    # ===== AUTO-REPAIR INTELIGENTE =====

    def _encontrar_caminho(self, fname):
        """Procura o arquivo em modulos/, scripts/ ou sandbox/."""
        candidatos = [
            os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos', fname),
            os.path.join(BASE, 'Scripts', 'mcr_devia', fname),
            os.path.join(BASE, 'sandbox', fname),
        ]
        for c in candidatos:
            if os.path.exists(c):
                return c
        return None

    def _auto_repair(self, anti_patterns):
        """Auto-corrige except: usando IA para decidir a excecao certa.
        
        Para cada arquivo com except: problematico, le o contexto (try + 3 linhas),
        envia para IA decidir a excecao especifica, aplica e registra no KG.
        """
        from modulos.sse_server import emit
        import re as _re, shutil
        
        correcoes = {}
        alvos = {}
        for padrao in ('except: pass', 'except: bare'):
            for o in anti_patterns.get(padrao, []):
                if o.get('severidade') in ('CRITICAL', 'HIGH'):
                    alvos.setdefault(o['arquivo'], []).append(o)
        
        if not alvos:
            return correcoes
        
        for fname, ocorrencias in alvos.items():
            caminho = self._encontrar_caminho(fname)
            if not caminho:
                continue
            
            with open(caminho, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            # Filtra ocorrencias: se except ja tem corpo (pass/return/raise), pula
            ocorrencias_filtradas = []
            for o in ocorrencias:
                idx_linha = o['linha'] - 1
                if idx_linha + 1 < len(linhas):
                    prox_linha = linhas[idx_linha + 1].strip()
                    if prox_linha in ('pass',) or prox_linha.startswith(('return ', 'raise ', 'continue', 'break', '#')):
                        continue  # ja tem corpo, nao precisa reparar
                ocorrencias_filtradas.append(o)
            ocorrencias = ocorrencias_filtradas
            if not ocorrencias:
                continue
            
            # Monta prompt com contexto rico
            blocos = []
            for o in ocorrencias:
                ini = max(0, o['linha'] - 4)
                fim = min(len(linhas), o['linha'] + 2)
                trecho = ''.join(linhas[ini:fim])
                blocos.append(f"--- OCORRENCIA L{o['linha']} ---\n{trecho}")
            
            prompt = (
                f"[SISTEMA]\nVoce esta corrigindo seu proprio codigo.\n"
                f"Determine a excecao MAIS ADEQUADA para cada bloco try-except.\n\n"
                f"[ARQUIVO]\n{fname}\n\n"
                f"{chr(10).join(blocos)}\n\n"
                f"[REGRAS]\n"
                f"- Arquivo/JSON: FileNotFoundError, json.JSONDecodeError\n"
                f"- Rede/API/IO: Exception\n"
                f"- Matematica/valor: ValueError, TypeError\n"
                f"- Import: ImportError\n"
                f"- Se nao souber: Exception\n\n"
                f"[RESPONDA ASSIM]\n"
                f"L123: except FileNotFoundError:\n"
                f"L456: except Exception as e:\n"
                f"PRESERVE a indentacao original (espacos no inicio da linha).\n"
                f"Apenas as linhas corrigidas, nesse formato."
            )
            
            emit('narrator', f'IA reparando {fname} ({len(ocorrencias)} ocorrencias)...')
            resposta = self._ia.gerar(prompt, 0.2, 'leve') or ""
            
            # Aplica as correcoes
            for linha_resp in resposta.strip().split('\n'):
                m = _re.match(r'L(\d+):\s*(.*)', linha_resp.strip())
                if not m:
                    continue
                num_linha = int(m.group(1))
                novaLinha = m.group(2).rstrip()
                
                # Valida a resposta
                tipos_validos = r'Exception|ValueError|TypeError|KeyError|FileNotFoundError|PermissionError|JSONDecodeError|ImportError|ZeroDivisionError|\(.+\)'
                if not _re.match(r'^except\s+(?:' + tipos_validos + r')(?:\s+as\s+\w+)?:', novaLinha):
                    continue
                
                idx = num_linha - 1
                if 0 <= idx < len(linhas):
                    linha_antiga = linhas[idx].rstrip()
                    # PRESERVA indentacao original (bug fix critical)
                    indent_original = len(linhas[idx]) - len(linhas[idx].lstrip())
                    novaLinha = ' ' * indent_original + novaLinha.lstrip()
                    linhas[idx] = novaLinha + '\n' if not novaLinha.endswith('\n') else novaLinha
                    correcoes.setdefault(fname, []).append({
                        'linha': num_linha, 'antes': linha_antiga, 'depois': novaLinha
                    })
            
            if correcoes.get(fname):
                shutil.copy2(caminho, caminho + '.selfbak')
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.writelines(linhas)
                # VALIDA sintaxe do arquivo modificado (auto-revert se falhar)
                try:
                    compile(''.join(linhas), caminho, 'exec')
                except SyntaxError as e:
                    emit('narrator', f'Syntax ERROR em {fname} apos auto-repair! Revertendo...')
                    # Reverte do backup
                    import shutil as _sh
                    _sh.copy2(caminho + '.selfbak', caminho)
                    correcoes[fname] = []  # desfaz registro
                    # Registra falha no KG
                    try:
                        self._kg.aprender(
                            erro=f'auto-repair FALHOU: {fname}:L{num_linha}',
                            causa=f'Erro de sintaxe: {e}',
                            solucao='Backup restaurado. Usar except Exception como fallback.',
                            ctx='auto_repair_falha'
                        )
                    except Exception: pass
                    continue  # proximo arquivo
                emit('narrator', f'{fname}: {len(correcoes[fname])} correcoes (sintaxe OK)')
        
        return correcoes

    def _comparar_scans(self, anti_before, anti_after, correcoes):
        """Compara antes/depois e calcula melhoria no health score."""
        HEALTH = {'CRITICAL': -15, 'HIGH': -10, 'MEDIUM': -5, 'LOW': -3, 'INFO': 0}
        calc = lambda ap: max(0, 100 + sum(HEALTH.get(o.get('severidade', 'LOW'), -3)
                                          for _, ocs in ap.items() for o in ocs))
        
        hb = calc(anti_before) if anti_before else 0
        hd = calc(anti_after) if anti_after else 0
        
        partes = []
        total_fixes = sum(len(v) for v in correcoes.values())
        if total_fixes:
            partes.append(f'Auto-repair: {total_fixes} correcoes em {len(correcoes)} arquivos')
            for fname, cs in correcoes.items():
                partes.append(f'  {fname}: {len(cs)} correcoes')
        
        if hd > hb:
            partes.append(f'Saude do codigo: {hb} -> {hd} (+{hd-hb} pts)')
        
        return '\n'.join(partes)
    
    def gerar_auto_insight(self, metricas, deep_analysis=""):
        """Gera insight combinando metricas + deep analysis real de codigo."""
        from modulos.sse_server import emit
        import json as _json2
        
        top5 = metricas['top5_maiores']
        if len(top5) < 2:
            return
        
        emit('stage', {'name': 'auto_insight', 'label': 'Gerando insight + deep analysis...', 'progress': 0.6})
        emit('narrator', 'Analisando metricas + anti-patterns + revisoes...')
        
        scans_anteriores = [l for l in self._kg._get_licoes() if l.get('ctx') == 'self_knowledge']
        metricas_anteriores = None
        if scans_anteriores:
            sol_anterior = scans_anteriores[-1].get('solucao', '{}')
            if isinstance(sol_anterior, str):
                try: metricas_anteriores = _json2.loads(sol_anterior)
                except (json.JSONDecodeError, TypeError):
                    pass
            else: metricas_anteriores = sol_anterior
        
        linhas_anteriores = {}
        if metricas_anteriores:
            for a in metricas_anteriores.get('top5_maiores', []):
                linhas_anteriores[a['nome']] = a['linhas']
        
        arquivos_melhorados = []
        arquivos_pendentes = []
        for a in top5:
            nome = a['nome']
            linhas_atuais = a['linhas']
            linhas_antigas = linhas_anteriores.get(nome, linhas_atuais)
            if linhas_antigas > linhas_atuais * 1.05:
                arquivos_melhorados.append((nome, linhas_antigas, linhas_atuais))
            else:
                arquivos_pendentes.append(a)
        
        pendentes_py = [a for a in arquivos_pendentes if a.get('ext') == '.py']
        pendentes_md = [a for a in arquivos_pendentes if a.get('ext') != '.py']
        # Remove arquivos legados da lista de candidatos a refatoracao
        ARQUIVOS_LEGADO = {'mcr_devia.py'}
        pendentes_py = [a for a in pendentes_py if a['nome'] not in ARQUIVOS_LEGADO]
        alvos = (pendentes_py + pendentes_md)
        if len(alvos) < 2:
            alvos = top5
        
        hist = ""
        if arquivos_melhorados:
            hist = "Melhorias detectadas:\n"
            for nome, antes, depois in arquivos_melhorados:
                hist += f"- {nome}: {antes} -> {depois} linhas ✅\n"
        else:
            hist = "Nenhuma melhoria significativa.\n"
        
        desc = '\n'.join(f'- {a["nome"]}: {a["linhas"]} linhas, {a["classes"]} classes, {a["funcoes"]} funcoes' for a in alvos)
        
        prompt = (f"[SISTEMA]\nVoce e um ARQUITETO DE SOFTWARE com dados REAIS.\n"
                  f"MCR = servidor Tibia.\n\n[EVOLUCAO]\n{hist}\n[ARQUIVOS]\n{desc}\n\n")
        if deep_analysis:
            prompt += f"[PROBLEMAS REAIS ENCONTRADOS]\n{deep_analysis}\n\n"
        prompt += (f"[PERGUNTA]\nQual melhoria MAIS IMPORTANTE fazer agora?\n"
                   f"Considere TANTO as metricas quanto os problemas reais.\n"
                   f"Sugira UMA acao ESPECIFICA. Responda em PT-BR.")
        
        resultado = self._ia.gerar(prompt, 0.4, 'analisar') or ""
        if resultado and len(resultado) > 100:
            try:
                self._kg.aprender(
                    erro=f'Sugestao de melhoria: scan #{self._get_count()}',
                    causa=f'Deep analysis + pendentes: {", ".join(a["nome"] for a in alvos)}',
                    solucao=resultado, ctx='sugestao_melhoria'
                )
                emit('narrator', f'Sugestao registrada! {len(resultado)} chars')
            except Exception:
                pass
    
    def executar(self):
        """Pipeline completo de auto-conhecimento com deep analysis."""
        from modulos.sse_server import emit
        t0 = time.time()
        emit('stage', {'name': 'self_study', 'label': 'Auto-conhecimento...', 'progress': 0.01})
        emit('narrator', 'Escaneando o proprio codigo fonte...')
        
        arquivos = self.escanear_projeto(max_arquivos=60)
        metricas = self.extrair_metricas(arquivos)
        emit('narrator', f'Encontrei {metricas["total_arquivos"]} arquivos, {metricas["total_linhas"]} linhas.')
        
        # 1. SCAN BEFORE: anti-patterns
        emit('narrator', 'Analisando anti-patterns no codigo...')
        anti_before = self._analisar_anti_patterns(arquivos)
        emit('narrator', f'Anti-patterns: HIGH={len(anti_before.get("except: bare",[]))}, CRITICAL={len(anti_before.get("except: pass",[]))}')
        
        # 2. AUTO-REPAIR: IA decide e aplica correcoes
        correcoes = {}
        if anti_before.get('except: pass') or anti_before.get('except: bare'):
            emit('narrator', 'Aplicando auto-repair inteligente via IA...')
            correcoes = self._auto_repair(anti_before)
        
        # 3. SCAN AFTER: re-escaneia se houve correcoes
        if correcoes:
            emit('narrator', 'Re-escanendo apos auto-repair...')
            arquivos = self.escanear_projeto(max_arquivos=60)
            metricas = self.extrair_metricas(arquivos)
            anti_after = self._analisar_anti_patterns(arquivos)
            relatorio_repair = self._comparar_scans(anti_before, anti_after, correcoes)
            emit('narrator', f'Repair concluido: {relatorio_repair}')
        else:
            anti_after = anti_before
            relatorio_repair = ''
        
        # 4. Revisao de funcoes complexas
        emit('narrator', 'Revisando funcoes complexas via LLM...')
        revisoes = self._revisar_funcoes_suspeitas(arquivos)
        
        # Monta relatorio de deep analysis com categorias e health score
        deep_parts = []
        
        if relatorio_repair:
            deep_parts.append(f'=== AUTO-REPAIR ===\n{relatorio_repair}')
        
        HEALTH_SCORE = {'CRITICAL': -15, 'HIGH': -10, 'MEDIUM': -5, 'LOW': -3, 'INFO': 0}
        health_penalty = 0
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        
        if anti_after:
            deep_parts.append('=== ANTI-PATTERNS ENCONTRADOS ===')
            # Ordena por severidade (CRITICAL primeiro)
            todos_items = []
            for padrao, ocorrencias in anti_after.items():
                for o in ocorrencias:
                    sev = o.get('severidade', 'LOW')
                    health_penalty += HEALTH_SCORE.get(sev, -3)
                    ordem = severity_order.get(sev, 9)
                    todos_items.append((ordem, sev, padrao, o['arquivo'], o['linha'], o))
            todos_items.sort()
            
            # Agrupa por severidade pra exibicao
            vistos = set()
            for ordem, sev, padrao, arq_nome, arq_linha, o in todos_items:
                if (padrao, arq_nome) in vistos:
                    continue
                vistos.add((padrao, arq_nome))
                linha_try = o.get('linha_try', '')
                ctx_extra = f" | try: {linha_try}" if linha_try else ""
                icone = {'CRITICAL': '🔴', 'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢', 'INFO': '⚪'}.get(sev, '⚪')
                msg = f"  {icone} [{sev}] {arq_nome}:L{arq_linha}  {o['codigo']}{ctx_extra}"
                if msg not in deep_parts:
                    deep_parts.append(msg)
            
            # Resumo por severidade
            deep_parts.append('')
            for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                count = sum(1 for o in todos_items if o[1] == sev)
                if count:
                    deep_parts.append(f"  {sev}: {count} ocorrencias")
        
        if revisoes:
            deep_parts.append(f'\n=== REVISOES DE FUNCOES ===\n{revisoes}')
        
        # Health score
        health_score = max(0, 100 + health_penalty)
        deep_parts.append(f'\n=== SAUDE DO CODIGO ===\n  Score: {health_score}/100 ({health_penalty} pts de penalidade)')
        
        deep_analysis = '\n'.join(deep_parts)
        
        if deep_analysis:
            emit('narrator', f'Deep analysis concluida: {len(deep_analysis)} chars')
        
        try:
            self._kg.aprender(
                erro=f'Auto-conhecimento: scan #{self._get_count()}',
                causa=f'Escaneei {metricas["total_arquivos"]} arquivos, {metricas["total_linhas"]} linhas',
                solucao=_json.dumps(metricas, ensure_ascii=False, default=str),
                ctx='self_knowledge'
            )
        except Exception:
            pass
        
        if metricas['top5_maiores']:
            self.gerar_auto_insight(metricas, deep_analysis)
        
        emit('narrator', f'Auto-conhecimento concluido em {round(time.time()-t0, 1)}s')
        emit('stage', {'name': 'self_study_fim', 'label': 'Auto-conhecimento OK', 'progress': 1.0})
        emit('result', {'chars': metricas['total_linhas'], 'arquivos': metricas['total_arquivos'], 'sucesso': True})


# Funcao de modulo para compatibilidade com kernel.py
_INSTANCIA = None

def executar(ia=None, kg=None, log_callback=None, execution_count_getter=None):
    """Wrapper de modulo para SelfStudyEngine.executar()."""
    global _INSTANCIA
    if _INSTANCIA is None:
        _INSTANCIA = SelfStudyEngine(
            ia=ia, kg=kg,
            log_callback=log_callback,
            execution_count_getter=execution_count_getter
        )
    try:
        _INSTANCIA.executar()
    except Exception as _e_ss:
        if log_callback:
            log_callback('error', f'SelfStudy: {_e_ss}')
