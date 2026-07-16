"""mcr.agente — MCRLoop: agente de software conversacional 100% MCR.

Ciclo:
  input → coupling.decidir() → ferramenta → executar → gerar resposta → aprender
"""
import os, sys, subprocess, json, re, time
from collections import defaultdict
from typing import List, Optional, Tuple

from mcr.coupling import MCRCoupling
from mcr.chat import MCRChat


class MCRLoop:

    def __init__(self, coupling_path: str = None):
        self._chat = MCRChat(temperatura=0.65)
        self._historico: List[dict] = []
        self._arquivo_atual: Optional[str] = None
        if coupling_path and os.path.exists(coupling_path):
            self._chat.coupling.load(coupling_path)
        self._seed_acoes()

    def _seed_acoes(self):
        c = self._chat.coupling
        seed = [
            ("ola tudo bem", "responder"),
            ("oi tudo bem", "responder"),
            ("bom dia", "responder"),
            ("boa tarde", "responder"),
            ("como vai", "responder"),
            ("o que voce acha", "responder"),
            ("me explique", "responder"),
            ("qual sua opiniao", "responder"),
            ("como funciona", "responder"),
            ("o que e", "responder"),
            ("quem e voce", "responder"),
            ("fale sobre", "responder"),
            ("edite o arquivo", "editar_arquivo"),
            ("modifique o codigo", "editar_arquivo"),
            ("altere a funcao", "editar_arquivo"),
            ("atualize o arquivo", "editar_arquivo"),
            ("leia o arquivo", "ler_arquivo"),
            ("mostre o conteudo", "ler_arquivo"),
            ("o que tem no arquivo", "ler_arquivo"),
            ("abra o arquivo", "ler_arquivo"),
            ("commite as mudancas", "git_commit"),
            ("git add e commit", "git_commit"),
            ("salve no git", "git_commit"),
            ("faca commit", "git_commit"),
            ("push", "git_push"),
            ("envie para o github", "git_push"),
            ("de push", "git_push"),
            ("rode os testes", "executar_teste"),
            ("teste o codigo", "executar_teste"),
            ("execute pytest", "executar_teste"),
            ("liste os arquivos", "listar_arquivos"),
            ("que arquivos tem", "listar_arquivos"),
            ("mostre a estrutura", "listar_arquivos"),
            ("procure por", "buscar_codigo"),
            ("encontre onde", "buscar_codigo"),
            ("pesquise no codigo", "buscar_codigo"),
            ("ache a funcao", "buscar_codigo"),
            ("crie um arquivo", "criar_arquivo"),
            ("crie o arquivo", "criar_arquivo"),
            ("delete o arquivo", "deletar_arquivo"),
            ("remova o arquivo", "deletar_arquivo"),
            ("obrigado", "responder"),
            ("valeu", "responder"),
            ("entendi", "responder"),
            ("certo", "responder"),
            ("show", "responder"),
            ("legal", "responder"),
            ("entao", "responder"),
            ("arquivos", "listar_arquivos"),
            ("lista de arquivos", "listar_arquivos"),
            ("mostre os arquivos", "listar_arquivos"),
            ("procure no codigo", "buscar_codigo"),
            ("buscar no codigo", "buscar_codigo"),
            ("encontre no codigo", "buscar_codigo"),
            ("procure a funcao", "buscar_codigo"),
            ("procure a classe", "buscar_codigo"),
            ("commit", "git_commit"),
            ("commitar", "git_commit"),
            ("faca um commit", "git_commit"),
            ("subir pro git", "git_push"),
            ("dar push", "git_push"),
            ("enviar", "git_push"),
            ("testar", "executar_teste"),
            ("executar os testes", "executar_teste"),
            ("roda os testes", "executar_teste"),
            ("teste unitario", "executar_teste"),
            ("pytest", "executar_teste"),
            ("editar", "editar_arquivo"),
            ("edicao", "editar_arquivo"),
            ("modificar", "editar_arquivo"),
            ("alterar", "editar_arquivo"),
            ("mude", "editar_arquivo"),
            ("adicione", "editar_arquivo"),
            ("criar", "criar_arquivo"),
            ("novo arquivo", "criar_arquivo"),
            ("deletar", "deletar_arquivo"),
            ("remover", "deletar_arquivo"),
            ("apagar", "deletar_arquivo"),
        ]
        for _ in range(3):
            c.alimentar_lote(seed)

    @property
    def coupling(self) -> MCRCoupling:
        return self._chat.coupling

    def _executar_ferramenta(self, acao: str, entrada: str) -> Tuple[str, dict]:
        resultado = ""
        params = {}

        def _buscar_arquivos(padrao, max_results=25):
            import glob as gb
            incluir = {'mcr', 'tests', 'docs', 'scripts', 'tools', 'prototypes', 'historia', '.'}
            excluir = {'site-packages', '__pycache__', '.git', 'cache', 'node_modules',
                       'ArquivosComplementares', 'Backup', 'vcpkg_installed', 'build',
                       'knowledge', 'generated', 'sandbox'}
            arquivos = []
            for f in sorted(gb.glob(padrao, recursive=True)):
                partes = f.replace('\\', '/').split('/')
                if any(e in partes for e in excluir):
                    continue
                if not any(e in partes for e in incluir):
                    continue
                arquivos.append(f)
                if len(arquivos) >= max_results:
                    return arquivos
            return arquivos

        if acao == "ler_arquivo":
            match = re.search(r'[\w/\\\.\-]+\.\w+', entrada)
            if match:
                path = match.group()
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read()
                    resultado = conteudo[:2000]
                    self._arquivo_atual = path
                    params['arquivo'] = path
                else:
                    resultado = f"Arquivo nao encontrado: {path}"
                    params['erro'] = True
            else:
                resultado = "Especifique o caminho do arquivo"

        elif acao == "listar_arquivos":
            arquivos = _buscar_arquivos("**/*.py")
            resultado = '\n'.join(arquivos) if arquivos else "Nenhum arquivo encontrado"
            params['arquivos'] = arquivos

        elif acao == "buscar_codigo":
            stop = ['procure', 'encontre', 'pesquise', 'onde', 'por', 'para', 'ache', 'buscar_codigo']
            termos = entrada.lower()
            for s in stop:
                termos = termos.replace(s, '')
            termos = termos.strip().strip(',.;:!?').strip()
            if not termos or len(termos) < 3:
                resultado = "Digite o que procurar"
            else:
                ocorrencias = []
                for py in _buscar_arquivos("**/*.py", max_results=40):
                    try:
                        with open(py, 'r', encoding='utf-8', errors='replace') as f:
                            for i, linha in enumerate(f, 1):
                                if termos in linha.lower():
                                    ocorrencias.append(f"{py}:{i}: {linha.rstrip()[:120]}")
                    except:
                        pass
                    if len(ocorrencias) >= 10:
                        break
                resultado = '\n'.join(ocorrencias) if ocorrencias else f"Nada encontrado para: {termos}"
                params['termo'] = termos

        elif acao == "executar_teste":
            import glob as gb
            tests = gb.glob("tests/**/test_*.py", root_dir='.', recursive=True)[:5]
            if tests:
                test_file = tests[0]
                try:
                    r = subprocess.run(
                        [sys.executable, '-m', 'pytest', test_file, '-q', '--tb=short'],
                        capture_output=True, text=True, timeout=30, cwd='.'
                    )
                    resultado = r.stdout[-1000:] + r.stderr[-500:]
                except subprocess.TimeoutExpired:
                    resultado = "Teste excedeu 30s"
                params['teste'] = test_file
            else:
                resultado = "Nenhum teste encontrado"

        elif acao == "git_commit":
            try:
                r = subprocess.run(['git', 'diff', '--stat'], capture_output=True, text=True, timeout=10, cwd='.')
                diff_stat = r.stdout.strip()
                if not diff_stat:
                    r = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, timeout=10, cwd='.')
                    diff_stat = r.stdout.strip()
                if diff_stat:
                    subprocess.run(['git', 'add', '-A'], capture_output=True, timeout=10, cwd='.')
                    msg = entrada.replace('commite', '').replace('commit', '').strip()[:80] or 'update'
                    r = subprocess.run(['git', 'commit', '-m', msg], capture_output=True, text=True, timeout=10, cwd='.')
                    resultado = r.stdout.strip() or r.stderr.strip()
                    params['mensagem'] = msg
                else:
                    resultado = "Nada para commitar"
            except Exception as e:
                resultado = f"Erro git: {e}"

        elif acao == "git_push":
            try:
                r = subprocess.run(['git', 'push'], capture_output=True, text=True, timeout=30, cwd='.')
                resultado = r.stdout.strip() or r.stderr.strip()
            except Exception as e:
                resultado = f"Erro push: {e}"

        elif acao == "responder":
            resultado = None

        elif acao in ("editar_arquivo", "criar_arquivo"):
            resultado = f"Use a ferramenta de edicao para {acao}"
            params['pendente'] = True

        else:
            resultado = None  # fallback: gera resposta mesmo sem acao especifica

        return resultado, params

    def perguntar(self, entrada: str) -> str:
        c = self._chat.coupling
        t0 = time.time()

        ultima_acao = self._historico[-1]['acao'] if self._historico else None
        peso_historico = 0.30 if ultima_acao else 0.0
        acao_intencao, conf = c.decidir(entrada, (ultima_acao, peso_historico))

        if conf < 0.35:
            acao = "responder"
        else:
            acao = acao_intencao

        resultado, params = self._executar_ferramenta(acao, entrada)

        if resultado is None:
            palavras_chave = re.findall(r'[a-zà-ÿ]{4,}', entrada.lower())
            seed = palavras_chave[-1] if palavras_chave else 'responder'
            resposta = self._chat._gerar_resposta(seed, max_tokens=12, modo='semantico')
            if len(resposta) < 5:
                resposta = self._chat._gerar_resposta(seed, max_tokens=12, modo='markov')
            if len(resposta) < 5:
                resposta = "Entendi. O que mais?"
        else:
            resposta = resultado[:500]

        c.alimentar(entrada, acao_intencao)

        self._historico.append({
            'entrada': entrada,
            'acao': acao,
            'conf': conf,
            'resposta': resposta,
            'params': params,
            'tempo': time.time() - t0,
        })

        return resposta

    def estado(self) -> dict:
        return {
            'interacoes': len(self._historico),
            'observacoes': self._chat.coupling.estatisticas()['total'],
            'ultima_acao': self._historico[-1]['acao'] if self._historico else None,
            'arquivo_atual': self._arquivo_atual,
        }
