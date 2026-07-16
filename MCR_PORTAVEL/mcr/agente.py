"""mcr.agente — MCRLoop: agente de software conversacional 100% MCR.

Ciclo:
  input → coupling.decidir() → ferramenta → executar → gerar resposta → aprender

Principios:
  - Zero dicionario sinonimo hardcoded. Cada acao aparece UMA vez no seed.
  - Paths descobertos por entropia de diretorios, nao por nome de projeto.
  - Só aprende quando confianca >= threshold (evita feedback loop negativo).
  - Ferramentas funcionam de verdade (editar/criar/deletar executam).
"""
import os
import sys
import subprocess
import re
import time
from typing import List, Optional, Tuple, Set, Dict

from mcr.coupling import MCRCoupling
from mcr.chat import MCRChat


class MCRLoop:

    _EXCLUIR_DIRS = frozenset({
        '__pycache__', '.git', 'node_modules', 'site-packages',
        '.pytest_cache', 'cache', 'build', 'dist', '.egg-info',
        'venv', '.env', '.vscode', '.idea',
    })
    _EXTS_CODIGO = ('.py', '.js', '.ts', '.lua', '.cs', '.cpp', '.c', '.h',
                    '.go', '.rs', '.java')

    def __init__(self, coupling_path: str = None, raiz: str = None):
        self._chat = MCRChat(temperatura=0.65)
        self._historico: List[dict] = []
        self._arquivo_atual: Optional[str] = None
        self._dir_raiz: str = raiz or os.getcwd()
        self._dirs_incluir: Optional[Set[str]] = None
        self._conf_minima = 0.35
        if coupling_path and os.path.exists(coupling_path):
            self._chat.coupling.load(coupling_path)
        self._seed_canonico()

    def _seed_canonico(self):
        c = self._chat.coupling
        pares = [
            ('responder', 'responder'),
            ('ler arquivo', 'ler_arquivo'),
            ('listar arquivos', 'listar_arquivos'),
            ('buscar codigo', 'buscar_codigo'),
            ('executar teste', 'executar_teste'),
            ('commit git', 'git_commit'),
            ('push git', 'git_push'),
            ('editar arquivo', 'editar_arquivo'),
            ('criar arquivo', 'criar_arquivo'),
            ('deletar arquivo', 'deletar_arquivo'),
            ('ola', 'responder'),
            ('obrigado', 'responder'),
        ]
        c.alimentar_lote(pares)

    @property
    def coupling(self) -> MCRCoupling:
        return self._chat.coupling

    def _dirs_relevantes(self) -> Set[str]:
        from math import log2
        if self._dirs_incluir is not None:
            return self._dirs_incluir
        relevantes = {'.'}
        try:
            for root, dirs, files in os.walk(self._dir_raiz):
                partes = root.replace('\\', '/').split('/')
                if any(p in self._EXCLUIR_DIRS for p in partes):
                    dirs[:] = []
                    continue
                rel = os.path.relpath(root, self._dir_raiz).replace('\\', '/')
                if rel == '.':
                    continue
                depth = rel.count('/')
                if depth > 2:
                    dirs[:] = []
                    continue
                stems = {os.path.splitext(f)[0].lower() for f in files
                         if len(os.path.splitext(f)[0]) > 2}
                if len(stems) >= 3:
                    h = log2(len(stems))
                    if h > 1.5:
                        relevantes.add(rel.split('/')[0])
        except Exception:
            pass
        self._dirs_incluir = relevantes
        return relevantes

    def _buscar_arquivos(self, padrao: str, max_results: int = 25) -> List[str]:
        import glob as gb
        incluir = self._dirs_relevantes()
        inclui_tudo = '.' in incluir
        arquivos = []
        for f in sorted(gb.glob(padrao, recursive=True)):
            partes = f.replace('\\', '/').split('/')
            if any(e in self._EXCLUIR_DIRS for e in partes):
                continue
            if not inclui_tudo:
                raiz_path = partes[0] if len(partes) > 1 else '.'
                if raiz_path not in incluir:
                    continue
            arquivos.append(f)
            if len(arquivos) >= max_results:
                break
        return arquivos

    def _executar_ferramenta(self, acao: str, entrada: str) -> Tuple[Optional[str], dict]:
        resultado: Optional[str] = None
        params: Dict = {}

        if acao == "ler_arquivo":
            match = re.search(r'[\w/\\\.\-]+\.\w+', entrada)
            if match:
                path = match.group()
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as f:
                            conteudo = f.read()
                        resultado = conteudo[:2000]
                        self._arquivo_atual = path
                        params['arquivo'] = path
                    except Exception as e:
                        resultado = f"Erro ao ler: {e}"
                        params['erro'] = True
                else:
                    resultado = f"Arquivo nao encontrado: {path}"
                    params['erro'] = True
            else:
                resultado = "Especifique o caminho do arquivo"

        elif acao == "listar_arquivos":
            arquivos = self._buscar_arquivos("**/*.*")
            arquivos = [a for a in arquivos
                        if any(a.endswith(ext) for ext in self._EXTS_CODIGO)]
            resultado = '\n'.join(arquivos) if arquivos else "Nenhum arquivo encontrado"
            params['arquivos'] = arquivos
            params['total'] = len(arquivos)

        elif acao == "buscar_codigo":
            m = re.search(
                r'\b(?:procure|encontre|pesquise|ache|buscar?|onde)\b\s+(.+)',
                entrada, re.IGNORECASE)
            if m:
                termos = m.group(1).strip().strip(',.;:!?').strip()
            else:
                termos = entrada.strip()
            if not termos or len(termos) < 3:
                resultado = "Digite o que procurar"
            else:
                ocorrencias = []
                for py in self._buscar_arquivos("**/*.*", max_results=40):
                    if not any(py.endswith(ext) for ext in self._EXTS_CODIGO):
                        continue
                    try:
                        with open(py, 'r', encoding='utf-8', errors='replace') as f:
                            for i, linha in enumerate(f, 1):
                                if termos.lower() in linha.lower():
                                    ocorrencias.append(
                                        f"{py}:{i}: {linha.rstrip()[:120]}")
                    except Exception:
                        pass
                    if len(ocorrencias) >= 10:
                        break
                resultado = ('\n'.join(ocorrencias)
                             if ocorrencias else f"Nada encontrado para: {termos}")
                params['termo'] = termos
                params['total'] = len(ocorrencias)

        elif acao == "executar_teste":
            import glob as gb
            tests = sorted(gb.glob("tests/**/test_*.py", recursive=True))[:10]
            if not tests:
                resultado = "Nenhum teste encontrado"
            else:
                try:
                    r = subprocess.run(
                        [sys.executable, '-m', 'pytest'] + tests + ['-q', '--tb=short'],
                        capture_output=True, text=True, timeout=60, cwd=self._dir_raiz
                    )
                    passou = r.returncode == 0
                    params['passou'] = passou
                    params['returncode'] = r.returncode
                    params['tests'] = len(tests)
                    tail = r.stdout[-1500:] + r.stderr[-500:]
                    resultado = f"{'PASS' if passou else 'FAIL'} ({len(tests)} arquivos)\n{tail}"
                except subprocess.TimeoutExpired:
                    resultado = f"Teste excedeu 60s ({len(tests)} arquivos)"
                except Exception as e:
                    resultado = f"Erro ao executar: {e}"

        elif acao == "git_commit":
            try:
                r = subprocess.run(['git', 'diff', '--stat'], capture_output=True,
                                   text=True, timeout=10, cwd=self._dir_raiz)
                diff_stat = r.stdout.strip()
                if not diff_stat:
                    r = subprocess.run(['git', 'status', '--short'],
                                       capture_output=True, text=True,
                                       timeout=10, cwd=self._dir_raiz)
                    diff_stat = r.stdout.strip()
                if not diff_stat:
                    resultado = "Nada para commitar"
                else:
                    r = subprocess.run(['git', 'status', '--porcelain'],
                                       capture_output=True, text=True,
                                       timeout=10, cwd=self._dir_raiz)
                    arqs = []
                    for linha in r.stdout.splitlines():
                        if not linha.strip():
                            continue
                        status = linha[:2]
                        path_arq = linha[3:].strip()
                        if '?' in status:
                            continue
                        arqs.append(path_arq)
                    if arqs:
                        subprocess.run(['git', 'add'] + arqs, capture_output=True,
                                       timeout=10, cwd=self._dir_raiz)
                    msg_match = re.search(r'(?:commit|commite)\s+(.+)',
                                          entrada, re.IGNORECASE)
                    msg = msg_match.group(1).strip()[:80] if msg_match else 'update'
                    r = subprocess.run(['git', 'commit', '-m', msg],
                                       capture_output=True, text=True,
                                       timeout=10, cwd=self._dir_raiz)
                    resultado = (r.stdout.strip() or r.stderr.strip() or "commitado")
                    params['mensagem'] = msg
                    params['arquivos'] = arqs
            except Exception as e:
                resultado = f"Erro git: {e}"

        elif acao == "git_push":
            try:
                r = subprocess.run(['git', 'push'], capture_output=True,
                                   text=True, timeout=30, cwd=self._dir_raiz)
                resultado = (r.stdout.strip() or r.stderr.strip() or "push enviado")
                params['returncode'] = r.returncode
            except Exception as e:
                resultado = f"Erro push: {e}"

        elif acao == "editar_arquivo":
            match = re.search(r'[\w/\\\.\-]+\.\w+', entrada)
            path = match.group() if match else self._arquivo_atual
            if not path:
                resultado = "Especifique o caminho do arquivo"
            elif not os.path.exists(path):
                resultado = f"Arquivo nao encontrado: {path}"
                params['erro'] = True
            else:
                m = re.search(
                    r'[\w/\\\.\-]+\.\w+\s+(?:para|com|conteudo|=>|:)\s+(.+)',
                    entrada, re.IGNORECASE | re.DOTALL)
                novo = m.group(1).strip() if m else ''
                if novo:
                    try:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(novo)
                        resultado = f"Arquivo editado: {path} ({len(novo)} bytes)"
                        params['arquivo'] = path
                        params['bytes'] = len(novo)
                    except Exception as e:
                        resultado = f"Erro ao editar: {e}"
                        params['erro'] = True
                else:
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as f:
                            resultado = f"Conteudo atual de {path}:\n{f.read()[:1500]}"
                        params['arquivo'] = path
                    except Exception as e:
                        resultado = f"Erro: {e}"

        elif acao == "criar_arquivo":
            match = re.search(r'[\w/\\\.\-]+\.\w+', entrada)
            if not match:
                resultado = "Especifique o caminho do arquivo"
            else:
                path = match.group()
                m = re.search(
                    r'[\w/\\\.\-]+\.\w+\s+(?:com|conteudo|=>|:)\s+(.+)',
                    entrada, re.IGNORECASE | re.DOTALL)
                conteudo = m.group(1).strip() if m else ''
                try:
                    dir_path = os.path.dirname(path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(conteudo)
                    resultado = f"Arquivo criado: {path} ({len(conteudo)} bytes)"
                    params['arquivo'] = path
                    params['bytes'] = len(conteudo)
                except Exception as e:
                    resultado = f"Erro ao criar: {e}"
                    params['erro'] = True

        elif acao == "deletar_arquivo":
            match = re.search(r'[\w/\\\.\-]+\.\w+', entrada)
            if not match:
                resultado = "Especifique o caminho do arquivo"
            else:
                path = match.group()
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        resultado = f"Arquivo deletado: {path}"
                        params['arquivo'] = path
                    except Exception as e:
                        resultado = f"Erro ao deletar: {e}"
                        params['erro'] = True
                else:
                    resultado = f"Arquivo nao encontrado: {path}"
                    params['erro'] = True

        elif acao == "responder":
            resultado = None

        else:
            resultado = None

        return resultado, params

    def _seed_resposta(self, entrada: str) -> str:
        c = self._chat.coupling
        palavras = re.findall(r'[a-zà-ÿ]{3,}', entrada.lower())
        if not palavras:
            return 'responder'
        for p in (palavras[0], palavras[-1]):
            if p in c._transicao_palavra:
                return p
        melhor_p, melhor_n = palavras[0], 0
        for p in set(palavras):
            n = sum(c._palavra_acao.get(p, {}).values())
            if n > melhor_n:
                melhor_n, melhor_p = n, p
        return melhor_p

    def perguntar(self, entrada: str) -> str:
        c = self._chat.coupling
        t0 = time.time()

        ultima_acao = self._historico[-1]['acao'] if self._historico else None
        peso_historico = 0.30 if ultima_acao else 0.0
        acao_intencao, conf = c.decidir(entrada, (ultima_acao, peso_historico))

        if conf < self._conf_minima:
            acao = "responder"
        else:
            acao = acao_intencao

        resultado, params = self._executar_ferramenta(acao, entrada)

        if resultado is None:
            seed = self._seed_resposta(entrada)
            resposta = self._chat._gerar_resposta(seed, max_tokens=12, modo='semantico')
            if len(resposta) < 5:
                resposta = self._chat._gerar_resposta(seed, max_tokens=12, modo='markov')
            if len(resposta) < 5:
                resposta = "Entendi. O que mais?"
        else:
            resposta = resultado[:500]

        if conf >= self._conf_minima:
            c.alimentar(entrada, acao_intencao)

        self._historico.append({
            'entrada': entrada,
            'acao': acao,
            'conf': conf,
            'resposta': resposta,
            'params': params,
            'tempo': round(time.time() - t0, 3),
        })

        return resposta

    def estado(self) -> dict:
        return {
            'interacoes': len(self._historico),
            'observacoes': self._chat.coupling.estatisticas()['total'],
            'ultima_acao': self._historico[-1]['acao'] if self._historico else None,
            'arquivo_atual': self._arquivo_atual,
            'dirs_relevantes': len(self._dirs_relevantes()),
        }
