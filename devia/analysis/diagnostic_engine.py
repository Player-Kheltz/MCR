"""Diagnostic Engine — Auto-diagnóstico do MCR-DevIA.
Detecta problemas de código, I/O manual, compilação, anti-patterns.
"""
import os, sys, time, json, re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MODULOS_DIR = os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos')


class DiagnosticEngine:
    """Motor de auto-diagnóstico: detecta, prioriza, repara."""

    SEVERIDADE = {'BLOQUEANTE': 0, 'ALTA': 1, 'MEDIA': 2, 'BAIXA': 3}
    # Metodos essenciais que DEVEM existir apos auto-repair
    METODOS_ESSENCIAIS = ['diagnosticar', 'remediar', 'check_compilacao', 'check_io_manual',
                          'check_except_sem_corpo', 'check_backups_orfãos', 'gerar_relatorio']

    def __init__(self, ia, tools, kg, log_callback=None):
        self._ia = ia
        self._tools = tools
        self._kg = kg
        self._log = log_callback or (lambda e, m: None)

    def check_compilacao(self):
        problemas = []
        if not os.path.exists(MODULOS_DIR):
            return problemas
        for fname in sorted(os.listdir(MODULOS_DIR)):
            if not fname.endswith('.py') or fname.startswith('_') or fname.startswith('.'):
                continue
            caminho = os.path.join(MODULOS_DIR, fname)
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    codigo = f.read()
                compile(codigo, caminho, 'exec')
            except SyntaxError as e:
                problemas.append({'arquivo': fname, 'linha': e.lineno or 0,
                                  'tipo': 'erro_compilacao', 'msg': str(e),
                                  'severidade': 'BLOQUEANTE', 'auto_reparavel': True})
        return problemas

    def check_io_manual(self):
        problemas = []
        for fname in sorted(os.listdir(MODULOS_DIR)):
            if not fname.endswith('.py') or fname.startswith('_'):
                continue
            caminho = os.path.join(MODULOS_DIR, fname)
            try:
                linhas = open(caminho, 'r', encoding='utf-8').readlines()
            except Exception:
                continue
            for regex, nome_tool in [(r"open\(.*['\"]r['\"]", 'ler_arquivo'),
                                      (r"open\(.*['\"]w['\"]", 'escrever_arquivo')]:
                for n, linha in enumerate(linhas, 1):
                    if re.search(regex, linha):
                        problemas.append({
                            'arquivo': fname, 'linha': n, 'tipo': 'io_manual',
                            'msg': f"open() em vez de tools.executar('{nome_tool}')",
                            'severidade': 'MEDIA', 'auto_reparavel': False})
                        break
        return problemas

    def check_except_sem_corpo(self):
        problemas = []
        for fname in sorted(os.listdir(MODULOS_DIR)):
            if not fname.endswith('.py'):
                continue
            try:
                linhas = open(os.path.join(MODULOS_DIR, fname), 'r', encoding='utf-8').readlines()
            except Exception:
                continue
            for n, linha in enumerate(linhas, 1):
                s = linha.strip()
                if not s.startswith('except'):
                    continue
                if s.endswith(('return None', 'return ""', 'return 0', 'return []', ': pass', ': continue')):
                    continue
                prox = None
                for j in range(n, len(linhas)):
                    if linhas[j].strip():
                        prox = linhas[j].strip()
                        break
                if prox is None or prox.startswith(('except', 'def ', 'class ', '#', '"""', "'''")):
                    problemas.append({'arquivo': fname, 'linha': n, 'tipo': 'except_sem_corpo',
                                      'msg': f"except sem corpo: {s}",
                                      'severidade': 'ALTA', 'auto_reparavel': True})
        return problemas

    def check_backups_orfãos(self):
        problemas = []
        for root, dirs, files in os.walk(MODULOS_DIR):
            for f in files:
                if f.endswith(('.selfbak', '.bak', '.autobak', '.diagbak')):
                    problemas.append({'arquivo': os.path.join(root, f), 'linha': 0,
                                      'tipo': 'backup_orfao', 'msg': f"Backup orfao: {f}",
                                      'severidade': 'BAIXA', 'auto_reparavel': True})
        return problemas

    def diagnosticar(self):
        """Roda TODOS os checks + PatternEngine eixo Nirvana-Caos."""
        problemas = []
        problemas.extend(self.check_compilacao())
        problemas.extend(self.check_io_manual())
        problemas.extend(self.check_except_sem_corpo())
        problemas.extend(self.check_backups_orfãos())
        # Pattern Universal: eixo Nirvana-Caos
        try:
            from modulos.pattern_engine import PatternEngine
            pe = PatternEngine()
            for fname in sorted(os.listdir(MODULOS_DIR)):
                if not fname.endswith('.py') or fname.startswith('_'):
                    continue
                caminho = os.path.join(MODULOS_DIR, fname)
                try:
                    codigo = open(caminho, 'r', encoding='utf-8').read()
                    tokens = pe.tokenizar(codigo, 'codigo')
                    eixo = pe.eixo_nirvana_caos(tokens)
                    if eixo < 0.5:
                        problemas.append({
                            'arquivo': fname, 'linha': 0, 'tipo': 'eixo_caos',
                            'msg': f"Eixo: {eixo:.2f} (tendencia ao Caos)",
                            'severidade': 'BAIXA', 'auto_reparavel': False,
                        })
                except Exception: pass
        except ImportError:
            pass
        problemas.sort(key=lambda p: self.SEVERIDADE.get(p['severidade'], 99))
        return problemas

    def gerar_relatorio(self, problemas):
        if not problemas:
            return "Nenhum problema encontrado."
        partes = []
        for sev in ['BLOQUEANTE', 'ALTA', 'MEDIA', 'BAIXA']:
            items = [p for p in problemas if p['severidade'] == sev]
            if not items:
                continue
            partes.append(f"\n[!] {sev}: {len(items)} ocorrencia(s)")
            for p in items:
                r = " (auto-reparavel)" if p.get('auto_reparavel') else ""
                partes.append(f"  {p['arquivo']}:L{p['linha']}  {p['msg']}{r}")
        return '\n'.join(partes)

    def remediar(self, problemas):
        import shutil
        from modulos.util import reparar_com_validacao
        resultados = {}
        for p in problemas:
            if not p.get('auto_reparavel'):
                continue
            if p['tipo'] == 'erro_compilacao':
                caminho = os.path.join(MODULOS_DIR, p['arquivo'])
                if not os.path.exists(caminho):
                    continue
                try:
                    conteudo = open(caminho, 'r', encoding='utf-8').read()
                    prompt = (f"[SISTEMA]\nCorrija o erro de sintaxe no arquivo "
                              f"{p['arquivo']}.\n[ERRO]\n{p['msg']}\n\n"
                              f"[CODIGO]\n{conteudo}\n\n"
                              f"[INSTRUCAO]\nGere o ARQUIVO COMPLETO corrigido.\n"
                              f"PRESERVE todos os metodos e funcionalidades.\n"
                              f"Responda APENAS com o codigo.")
                    codigo = self._ia.gerar(prompt, 0.3, 'leve') or ''
                    m = re.search(r'```(?:python)?\s*\n(.*?)```', codigo, re.DOTALL)
                    if m:
                        codigo = m.group(1)
                    try:
                        compile(codigo, caminho, 'exec')
                        # Validacao SEMANTICA: verifica metodos essenciais
                        if p['arquivo'] == 'diagnostic_engine.py':
                            for metodo in self.METODOS_ESSENCIAIS:
                                if metodo not in codigo:
                                    raise SyntaxError(f'Metodo {metodo} ausente')
                        # PATTERN GATEKEEPER: compara com codigo original
                        codigo_final = reparar_com_validacao(
                            conteudo, lambda c: codigo, similaridade_min=0.7)
                        if codigo_final == conteudo:
                            raise ValueError("Gatekeeper rejeitou: similaridade/estrutura")
                        shutil.copy2(caminho, caminho + '.diagbak')
                        open(caminho, 'w', encoding='utf-8').write(codigo_final)
                        resultados[p['arquivo']] = True
                    except (SyntaxError, ValueError, Exception):
                        resultados[p['arquivo']] = False
                except Exception:
                    resultados[p['arquivo']] = False
            elif p['tipo'] == 'except_sem_corpo':
                caminho = os.path.join(MODULOS_DIR, p['arquivo'])
                if not os.path.exists(caminho):
                    continue
                try:
                    linhas = open(caminho, 'r', encoding='utf-8').readlines()
                    idx = p['linha'] - 1
                    if 0 <= idx < len(linhas):
                        # Verifica se o except ja tem corpo (return/pass/raise na prox linha)
                        if idx + 1 < len(linhas):
                            prox_linha = linhas[idx + 1].strip()
                            if prox_linha in ('pass',) or prox_linha.startswith(('return', 'raise', 'continue', 'break', '#')):
                                resultados[p['arquivo']] = True  # ja tem corpo, ok
                                continue
                        indent = len(linhas[idx]) - len(linhas[idx].lstrip())
                        codigo_original = ''.join(linhas)
                        def _inserir_pass(codigo):
                            l = codigo.split('\n')
                            l.insert(idx + 1, ' ' * (indent + 4) + 'pass')
                            return '\n'.join(l)
                        codigo_novo = reparar_com_validacao(
                            codigo_original, _inserir_pass)
                        if codigo_novo != codigo_original:
                            open(caminho, 'w', encoding='utf-8').write(codigo_novo)
                            resultados[p['arquivo']] = True
                        else:
                            resultados[p['arquivo']] = False
                except Exception:
                    resultados[p['arquivo']] = False
            elif p['tipo'] == 'backup_orfao':
                try:
                    os.remove(p['arquivo'])
                    resultados[p['arquivo']] = True
                except Exception:
                    resultados[p['arquivo']] = False
        return resultados

    def aprender(self, problemas, resultados):
        try:
            total = len(problemas)
            ok = sum(1 for v in resultados.values() if v)
            self._kg.aprender(
                erro=f'Diagnostico: {total} problemas, {ok} resolvidos',
                causa=", ".join(p['tipo'] for p in problemas) if problemas else 'Nenhum',
                solucao=json.dumps({'total': total, 'resolvidos': ok}, ensure_ascii=False),
                ctx='diagnostico')
        except Exception:
            pass

    def executar(self):
        from modulos.progress_tracker import salvar_checkpoint
        t0 = time.time()
        salvar_checkpoint('diagnostico', 0.01)
        problemas = self.diagnosticar()
        salvar_checkpoint('diagnosticado', 0.5, total=len(problemas))
        resultados = {}
        if problemas:
            auto = [p for p in problemas if p.get('auto_reparavel')]
            if auto:
                resultados = self.remediar(auto)
                ok = sum(1 for v in resultados.values() if v)
        salvar_checkpoint('remediado', 0.8)
        self.aprender(problemas, resultados)
        salvar_checkpoint('fim', 1.0)
