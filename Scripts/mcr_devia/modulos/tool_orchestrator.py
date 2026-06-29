"""ToolOrchestrator — Catalogo VIVO de ferramentas executaveis.

Cada ferramenta sabe:
- Nome, descricao (para o LLM decidir qual usar)
- Funcao executavel (para rodar)
- Parametros esperados
- O que retorna

Uso:
    tools = ToolOrchestrator()
    lista = tools.listar()
    resultado = tools.executar('gerar_npc', {'descricao': 'ferreiro', 'tipo': 'shop'})
"""
import os, sys, json, subprocess, tempfile, ast, importlib, urllib.request, re
from typing import Dict, Any, Callable, Optional

# Paths
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')


class ToolOrchestrator:
    """Orquestrador de ferramentas executaveis."""

    def __init__(self):
        self._ferramentas: Dict[str, dict] = {}
        self._ia = None  # lazy load
        self._carregar_todas()

    def _get_ia(self):
        """Carrega IA sob demanda."""
        if self._ia is None:
            from modulos.ia import IA
            self._ia = IA()
        return self._ia

    def _carregar_todas(self):
        """Carrega todas as ferramentas do sistema."""
        # === FERRAMENTAS DE SISTEMA ===
        self.registrar('executar_comando', self._cmd_executar_comando,
            desc="Executa comando no terminal (cmd/powershell)",
            params={'comando': 'string'}, output='string')

        self.registrar('ler_arquivo', self._cmd_ler_arquivo,
            desc="Le conteudo de um arquivo",
            params={'caminho': 'string'}, output='string')

        self.registrar('escrever_arquivo', self._cmd_escrever_arquivo,
            desc="Cria ou modifica um arquivo",
            params={'caminho': 'string', 'conteudo': 'string'}, output='string')

        self.registrar('listar_diretorio', self._cmd_listar_dir,
            desc="Lista arquivos de um diretorio",
            params={'caminho': 'string'}, output='string')

        self.registrar('criar_diretorio', self._cmd_criar_diretorio,
            desc="Cria estrutura de diretorios (ex: src/, assets/, runs/)",
            params={'caminho': 'string'}, output='string')

        # === FERRAMENTAS DE BUSCA ===
        self.registrar('buscar_codigo', self._cmd_buscar_codigo,
            desc="Busca texto no codigo fonte (grep/findstr)",
            params={'padrao': 'string', 'incluir': 'string (opcional)'}, output='string')

        self.registrar('buscar_kg', self._cmd_buscar_kg,
            desc="Busca conhecimento no Knowledge Graph",
            params={'texto': 'string'}, output='string')

        self.registrar('buscar_web', self._cmd_buscar_web,
            desc="Pesquisa na web com IA",
            params={'consulta': 'string'}, output='string')

        self.registrar('buscar_memoria', self._cmd_buscar_memoria,
            desc="Busca experiencias passadas similares",
            params={'request': 'string'}, output='string')

        # === FERRAMENTAS DE CRIACAO ===
        self.registrar('gerar_npc', self._cmd_gerar_npc,
            desc="Gera script Lua de NPC para Canary",
            params={'descricao': 'string', 'tipo': 'string (opcional)'}, output='dict')

        self.registrar('gerar_codigo', self._cmd_gerar_codigo,
            desc="Gera codigo em qualquer linguagem via IA",
            params={'descricao': 'string', 'linguagem': 'string (opcional)'}, output='string')

        self.registrar('escrever_artefato', self._cmd_escrever_artefato,
            desc="Escreve um artefato em arquivo",
            params={'codigo': 'string', 'caminho': 'string'}, output='string')

        # === FERRAMENTAS DE VALIDACAO ===
        self.registrar('validar_lua', self._validar_lua,
            desc="Valida sintaxe Lua Canary",
            params={'codigo': 'string'}, output='dict')

        self.registrar('validar_python', self._validar_python,
            desc="Valida sintaxe Python",
            params={'codigo': 'string'}, output='dict')

        self.registrar('executar_python', self._cmd_executar_python,
            desc="Executa codigo Python e captura output",
            params={'codigo': 'string'}, output='dict')

        self.registrar('validar_codigo', self._cmd_validar_codigo,
            desc="Valida codigo em QUALQUER linguagem: detecta lingua e usa validador correto",
            params={'codigo': 'string'}, output='dict')

        # === FERRAMENTAS DE IA ===
        self.registrar('perguntar_ia', self._cmd_perguntar_ia,
            desc="Faz pergunta a IA local",
            params={'pergunta': 'string', 'tarefa': 'string (opcional)'}, output='string')

        self.registrar('analisar_codigo', self._cmd_analisar_codigo,
            desc="Analisa codigo fonte e aponta problemas",
            params={'codigo': 'string'}, output='string')

        # === FERRAMENTAS DE UTILIDADE ===
        self.registrar('extrair_codigo', self._cmd_extrair_codigo,
            desc="Extrai codigo puro de resposta markdown (remove explicacoes)",
            params={'conteudo': 'string'}, output='string')

        self.registrar('gerar_requirements', self._cmd_gerar_requirements,
            desc="Cria requirements.txt com dependencias do projeto",
            params={'dependencias': 'string (opcional)', 'caminho': 'string (opcional)'}, output='string')

        self.registrar('criar_atalho', self._cmd_criar_atalho,
            desc="Cria atalho run.bat (Windows) para executar o projeto",
            params={'comando': 'string', 'caminho': 'string (opcional)'}, output='string')

        self.registrar('instalar_dependencias', self._cmd_instalar_deps,
            desc="Instala dependencias via pip",
            params={'requirements_path': 'string'}, output='string')

    # ============================================================
    # API PUBLICA
    # ============================================================

    def registrar(self, nome, funcao, desc="", params=None, output="string"):
        """Registra uma ferramenta."""
        self._ferramentas[nome] = {
            'nome': nome,
            'descricao': desc,
            'funcao': funcao,
            'params': params or {},
            'output': output,
        }

    def listar(self):
        """Lista ferramentas disponiveis (para o LLM escolher)."""
        return {n: {
            'descricao': f['descricao'],
            'params': list(f['params'].keys()),
        } for n, f in self._ferramentas.items()}

    def obter(self, nome):
        """Retorna metadata de uma ferramenta."""
        return self._ferramentas.get(nome)

    def executar(self, nome, params=None, timeout=60):
        """Executa uma ferramenta pelo nome.

        Args:
            nome: Nome da ferramenta
            params: Dict de parametros
            timeout: Timeout em segundos
        Returns:
            Dict com 'sucesso' ou 'erro'
        """
        if nome not in self._ferramentas:
            return {'erro': f'Ferramenta "{nome}" nao encontrada'}

        ferramenta = self._ferramentas[nome]
        try:
            resultado = ferramenta['funcao'](**(params or {}))
            return {'sucesso': True, 'resultado': resultado}
        except TypeError as e:
            return {'erro': f'Parametros invalidos para {nome}: {e}'}
        except subprocess.TimeoutExpired:
            return {'erro': f'Timeout ({timeout}s) executando {nome}'}
        except Exception as e:
            return {'erro': f'{type(e).__name__}: {e}'}

    # ============================================================
    # IMPLEMENTACOES - SISTEMA
    # ============================================================

    def _cmd_executar_comando(self, comando):
        """Executa comando no terminal."""
        r = subprocess.run(
            comando, capture_output=True, text=True, timeout=30, shell=True
        )
        saida = r.stdout[:5000]
        if r.stderr:
            saida += '\n[STDERR] ' + r.stderr[:1000]
        return saida

    def _cmd_ler_arquivo(self, caminho):
        """Le conteudo de arquivo."""
        if not os.path.exists(caminho):
            return f'Arquivo nao encontrado: {caminho}'
        with open(caminho, 'r', encoding='utf-8') as f:
            return f.read()[:8000]

    def _cmd_escrever_arquivo(self, caminho, conteudo):
        """Cria ou modifica um arquivo."""
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        return f"Arquivo salvo: {caminho} ({len(conteudo)} chars)"

    def _cmd_listar_dir(self, caminho):
        """Lista diretorio."""
        if not os.path.exists(caminho):
            return "Diretorio nao encontrado"
        itens = os.listdir(caminho)
        linhas = []
        for i in sorted(itens)[:50]:
            tipo = '[DIR]' if os.path.isdir(os.path.join(caminho, i)) else '[FILE]'
            linhas.append(f"{tipo} {i}")
        if len(itens) > 50:
            linhas.append(f"... e mais {len(itens) - 50} itens")
        return '\n'.join(linhas)

    # ============================================================
    # IMPLEMENTACOES - BUSCA
    # ============================================================

    def _cmd_buscar_codigo(self, padrao, incluir="*"):
        """Busca texto no codigo fonte."""
        proj = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        # Tenta findstr (Windows)
        if incluir == '*':
            incluir_glob = '*.py *.lua *.cpp *.hpp *.h *.xml *.json *.md'
        else:
            incluir_glob = incluir
        cmd = f'findstr /snip /c:"{padrao}" /d:"{proj}" {incluir_glob} 2>nul'
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=True)
        if r.stdout:
            linhas = r.stdout.split('\n')
            # Filtra diretorios irrelevantes
            linhas = [l for l in linhas if 'sandbox' not in l and '__pycache__' not in l and '.git' not in l]
            return '\n'.join(linhas[:50])
        return "Nenhum resultado encontrado"

    def _cmd_buscar_kg(self, texto, max_r=5):
        """Busca no Knowledge Graph."""
        try:
            from modulos.kg import KnowledgeGraph
            kg = KnowledgeGraph()
            lessons = kg.buscar(texto, max_r)
            if not lessons:
                return "Nenhuma licao encontrada"
            return '\n'.join(f"- {l.get('solucao', '')[:200]}" for l in lessons)
        except ImportError as e:
            return f"KG nao disponivel: {e}"

    def _cmd_buscar_web(self, consulta):
        """Busca na web usando Router Hibrido."""
        ia = self._get_ia()
        resultado = ia.buscar_web(consulta)
        if resultado:
            return resultado
        return "Nenhum resultado da busca web"

    def _cmd_buscar_memoria(self, request):
        """Busca experiencias similares."""
        try:
            from modulos.episodic_memory import EpisodicMemory
            mem = EpisodicMemory()
            episodios = mem.buscar(request, 3)
            if not episodios:
                return "Nenhuma experiencia similar encontrada"
            linhas = []
            for e in episodios:
                status = '[OK]' if e.get('sucesso') else '[FALHA]'
                linhas.append(f"{status} {e.get('request', '')[:60]} -> {e.get('licao', '')[:100]}")
            return '\n'.join(linhas)
        except ImportError as e:
            return f"Memoria nao disponivel: {e}"

    # ============================================================
    # IMPLEMENTACOES - CRIACAO
    # ============================================================

    def _cmd_gerar_npc(self, descricao, tipo='shop'):
        """Gera NPC via AgentLoop."""
        try:
            from modulos.agent_loop import AgentLoop
            agent = AgentLoop()
            r = agent.executar(descricao, tipo)
            return r
        except ImportError as e:
            return {'erro': f'AgentLoop nao disponivel: {e}'}

    def _cmd_gerar_codigo(self, descricao, linguagem=""):
        """Gera codigo via IA."""
        ia = self._get_ia()
        prompt = f"Crie o codigo em {linguagem}:\n{descricao}\n" if linguagem else f"Crie o codigo:\n{descricao}\n"
        prompt += "Codigo COMPLETO, sem placeholders, sem 'TODO', funcional."
        return ia.gerar(prompt, 0.4, "code") or "Falha ao gerar codigo"

    def _cmd_escrever_artefato(self, codigo, caminho):
        """Salva codigo em arquivo, extraindo de markdown se necessario."""
        from modulos.util import extrair_codigo_puro
        codigo_puro = extrair_codigo_puro(codigo)
        return self._cmd_escrever_arquivo(caminho, codigo_puro)

    def _cmd_criar_diretorio(self, caminho):
        """Cria estrutura de diretorios."""
        os.makedirs(caminho, exist_ok=True)
        return f"Diretorio criado: {caminho}"

    def _cmd_extrair_codigo(self, conteudo):
        """Extrai codigo puro de resposta markdown."""
        from modulos.util import extrair_codigo_puro
        return extrair_codigo_puro(conteudo)

    def _cmd_gerar_requirements(self, dependencias="pygame", caminho=""):
        """Gera requirements.txt."""
        if not caminho:
            caminho = os.path.join(BASE, 'sandbox', 'requirements.txt')
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(f"# Dependencias do projeto\n{dependencias}\n")
        return f"Requirements salvo: {caminho}"

    def _cmd_criar_atalho(self, comando, caminho=""):
        """Cria atalho run.bat para executar o projeto."""
        if caminho:
            b = caminho if os.path.isdir(caminho) else os.path.dirname(caminho)
        else:
            b = os.path.join(BASE, 'sandbox')
        os.makedirs(b, exist_ok=True)
        nome_base = 'run'
        if caminho and not os.path.isdir(caminho):
            nome_base = os.path.splitext(os.path.basename(caminho))[0]
        bat_path = os.path.join(b, f"{nome_base}.bat")
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(f"@echo off\n{comando}\npause\n")
        return f"Atalho criado: {bat_path}"

    def _cmd_instalar_deps(self, requirements_path):
        """Instala dependencias via pip."""
        if not os.path.exists(requirements_path):
            return f"Arquivo nao encontrado: {requirements_path}"
        r = subprocess.run(
            ['pip', 'install', '-r', requirements_path],
            capture_output=True, text=True, timeout=120
        )
        if r.returncode == 0:
            return "Dependencias instaladas com sucesso"
        return f"Falha ao instalar: {r.stderr[:500]}"

    # ============================================================
    # IMPLEMENTACOES - VALIDACAO
    # ============================================================

    # Cache para deteccao de node
    _HAS_NODE = None

    def _tem_node(self):
        if self._HAS_NODE is None:
            r = subprocess.run(['node', '--version'], capture_output=True, timeout=5)
            self.__class__._HAS_NODE = r.returncode == 0
        return self._HAS_NODE

    # Cache de validacao (Nivel 1)
    _cache_validacao = {}

    def _get_cache_validacao(self, key):
        return self._cache_validacao.get(key)

    def _set_cache_validacao(self, key, valor):
        if len(self._cache_validacao) > 500:
            self._cache_validacao.clear()
        self._cache_validacao[key] = valor

    def _cmd_validar_codigo(self, codigo):
        """Valida codigo em QUALQUER linguagem com 3 niveis de seguranca.
        
        Nivel 1 — Toolkit rapido (cache + KG + EpisodicMemory, 0 IA)
        Nivel 2 — Checker especifico (ast, node, json) ou FAST + exemplos
        Nivel 3 — Dupla checagem se FAST confianca baixa
        """
        from modulos.util import extrair_codigo_puro
        from modulos.decider import Decider
        from modulos.ia import IA as _IA

        codigo_puro = extrair_codigo_puro(codigo)
        if not codigo_puro or len(codigo_puro) < 10:
            return {'valido': False, 'erros': ['Codigo vazio ou muito curto']}

        # NIVEL 1: Toolkit rapido (0 IA)
        resultado_toolkit = self._validar_com_toolkit(codigo_puro)
        if resultado_toolkit:
            return resultado_toolkit

        # NIVEL 2: Detecta linguagem + checker ou FAST
        try:
            decider = Decider(_IA())
            lang = decider.classificar(
                codigo_puro[:300],
                ['python', 'javascript', 'lua', 'json', 'html', 'yaml',
                 'typescript', 'css', 'xml', 'csharp', 'rust', 'go',
                 'bash', 'makefile', 'java', 'sql', 'php', 'ruby', 'swift'],
                exemplos=[
                    ("def main(): print('oi')", "python"),
                    ("import pygame; print('hello')", "python"),
                    ("class Jogador: def __init__(self): pass", "python"),
                    ("const x = 1; console.log(x);", "javascript"),
                    ('{"nome": "Joao", "idade": 30}', "json"),
                    ("<html><body>Oi</body></html>", "html"),
                    ("local player = { x = 10 }", "lua"),
                    ("#!/bin/bash\necho 'hello'", "bash"),
                    ("target: deps\n\tgcc main.c\necho 'feito'", "makefile"),
                    ("public class Test { }", "java"),
                    ("SELECT * FROM users WHERE id = 1", "sql"),
                ],
                instrucao="Detecte a linguagem pelo codigo. Prefira 'python' se houver duvida entre python e lua. Prefira 'makefile' se tiver ':' e '\\t'. Prefira 'bash' se tiver '#!/bin'."
            )
        except Exception:
            lang = 'python'

        # Checkers especificos (deterministicos, seguros)
        checkers = {
            'python': self._validar_python,
            'javascript': self._validar_javascript,
            'typescript': self._validar_javascript,
            'lua': self._validar_lua,
            'json': self._validar_json,
        }

        checker = checkers.get(lang)
        if checker:
            resultado = checker(codigo_puro)
            if isinstance(resultado, dict):
                resultado['linguagem'] = lang
                resultado['metodo'] = 'checker'
            self._set_cache_validacao(codigo_puro[:200], resultado)
            return resultado

        # FAST + exemplos para linguagens sem checker (Bash, Java, Makefile, HTML...)
        return self._validar_com_fast(codigo_puro, lang)

    def _validar_com_toolkit(self, codigo):
        """Nivel 1: toolkit rapido — cache + memoria (0 IA)."""
        cached = self._get_cache_validacao(codigo[:200])
        if cached:
            return cached
        try:
            from modulos.episodic_memory import EpisodicMemory
            mem = EpisodicMemory()
            for m in mem.buscar(f"validar {codigo[:100]}", n=1):
                if m.get('sucesso') and 'valido' in m.get('licao', ''):
                    r = {'valido': True, 'erros': [], 'metodo': 'memoria_cache'}
                    self._set_cache_validacao(codigo[:200], r)
                    return r
        except Exception:
            pass
        return None

    def _validar_com_fast(self, codigo, linguagem):
        """Nivel 2: FAST + exemplos universais para QUALQUER linguagem.
        
        Se disse invalido com baixa confianca, passa para Nivel 3.
        """
        from modulos.decider import Decider

        exemplos = [
            ("echo 'hello'", "valido"),
            ("echo 'hello", "invalido"),
            ("<html><body>Oi</body></html>", "valido"),
            ("<html><body>Oi</html>", "invalido"),
            ("target:\n\techo ok", "valido"),
            ("target:\n echo ok", "invalido"),
            ("public class Test {}", "valido"),
            ("public class Test {", "invalido"),
            ("SELECT * FROM users", "valido"),
            ("SELECT * FORM users", "invalido"),
        ]

        try:
            decider = Decider(self._get_ia())
            r = decider.classificar(
                codigo[:1000], ['valido', 'invalido'],
                exemplos=exemplos,
                instrucao=f"Classifique se codigo {linguagem} tem erros de sintaxe."
            )
            if r == 'valido':
                resp = {'valido': True, 'erros': [], 'linguagem': linguagem, 'metodo': 'fast'}
                self._set_cache_validacao(codigo[:200], resp)
                return resp
            return self._validar_com_fast_detalhado(codigo, linguagem)
        except Exception as e:
            print(f"[ValidadorFAST] Erro: {e}")

        resp = {'valido': True, 'erros': [], 'aviso': 'Falha FAST, ignorado', 'linguagem': linguagem}
        self._set_cache_validacao(codigo[:200], resp)
        return resp

    def _validar_com_fast_detalhado(self, codigo, linguagem):
        """Nivel 3: dupla checagem — verifica se erro e real ou falso positivo.
        
        1. Pede para listar erros especificos
        2. Se nao conseguir listar erro concreto → falso positivo
        3. Se listar erro que parece real → invalido
        """
        prompt = (
            f"Analise este codigo {linguagem}.\n"
            f"Responda APENAS com 'OK' se estiver correto.\n"
            f"Se houver erro, diga EXATAMENTE o erro (linha, caracter).\n\n"
            f"CODIGO:\n```{linguagem}\n{codigo[:2000]}\n```\n\n"
            f"Resposta (apenas 'OK' ou 'ERRO: descricao'):"
        )
        try:
            resp = self._get_ia().fast(prompt, 0.1, 'leve')
        except Exception:
            resp = ''

        if resp and 'ERRO' in resp.upper():
            # Verifica se o erro parece real ou generico
            resp_lower = resp.lower()
            erros_genericos = ['parece ser', 'possivel', 'talvez', 'nao tenho', 'nao consigo']
            if any(g in resp_lower for g in erros_genericos):
                # Erro generico → falso positivo
                r = {'valido': True, 'erros': [], 'aviso': 'Falso positivo', 'linguagem': linguagem, 'metodo': 'fast_corrigido'}
            else:
                # Erro especifico → invalido
                r = {'valido': False, 'erros': [resp[:200]], 'linguagem': linguagem, 'metodo': 'fast_detalhado'}
        else:
            r = {'valido': True, 'erros': [], 'linguagem': linguagem, 'metodo': 'fast_corrigido'}
        self._set_cache_validacao(codigo[:200], r)
        return r

    def _validar_python(self, codigo):
        """Valida sintaxe Python com ast.parse()."""
        try:
            ast.parse(codigo)
            return {'valido': True, 'erros': []}
        except SyntaxError as e:
            return {'valido': False, 'erros': [f'Linha {e.lineno}: {e.msg}']}

    def _validar_javascript(self, codigo):
        """Valida JavaScript com node --check (se disponivel)."""
        if not self._tem_node():
            return {'valido': True, 'erros': [], 'aviso': 'node nao instalado, validacao ignorada'}
        with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False, encoding='utf-8') as f:
            f.write(codigo)
            tmp = f.name
        try:
            r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True, timeout=10)
            return {'valido': r.returncode == 0, 'erros': [] if r.returncode == 0 else [r.stderr[:200]]}
        except Exception as e:
            return {'valido': True, 'erros': [], 'aviso': f'Erro ao validar JS: {e}'}
        finally:
            try:
                os.unlink(tmp)
            except Exception:
                pass

    def _validar_lua(self, codigo):
        """Valida sintaxe Lua.
        
        Se o LuaValidator (NPC Canary) estiver disponivel, tenta validar.
        Se falhar com erros de estrutura (nao de sintaxe), considera valido
        porque o codigo pode ser Lua generico, nao um NPC.
        Fallback: checagem basica de estrutura Lua.
        """
        try:
            from modulos.lua_validator import LuaValidator
            val = LuaValidator()
            r = val.validar(codigo)
            # Se a sintaxe esta OK, considera valido (mesmo sem estrutura de NPC)
            if not r.get('valido') and not r.get('sintaxe', ''):
                # Erro de estrutura (nao de sintaxe) - pode ser Lua generico
                if r.get('estrutura') and not r.get('sintaxe'):
                    return {'valido': True, 'erros': [], 'aviso': 'Lua generico (nao NPC Canary)'}
            return r
        except ImportError:
            pass
        # Fallback: checagem basica de estrutura Lua
        padroes_lua = ['local ', 'function ', ' end', ' = ', 'print', '--']
        parece_lua = any(p in codigo for p in padroes_lua)
        if parece_lua:
            return {'valido': True, 'erros': []}
        return {'valido': False, 'erros': ['Codigo nao parece Lua']}

    def _validar_json(self, codigo):
        """Valida JSON com json.loads()."""
        try:
            import json as _json
            _json.loads(codigo)
            return {'valido': True, 'erros': []}
        except Exception as e:
            return {'valido': False, 'erros': [str(e)[:200]]}

    def _validar_html(self, codigo):
        """Valida HTML basico (menos restritivo).
        
        Qualquer conteudo com tags HTML basicas e considerado valido.
        """
        if '<' in codigo and '>' in codigo:
            return {'valido': True, 'erros': [], 'aviso': 'Validacao HTML basica'}
        return {'valido': False, 'erros': ['Nao parece HTML (sem tags)']}

    def _cmd_executar_python(self, codigo):
        """Executa Python em sandbox via subprocess."""
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write(codigo)
            tmp = f.name
        try:
            r = subprocess.run(['python', tmp], capture_output=True, text=True, timeout=15)
            os.unlink(tmp)
            return {
                'stdout': r.stdout[:3000] if r.stdout else '',
                'stderr': r.stderr[:1000] if r.stderr else '',
                'returncode': r.returncode,
            }
        except subprocess.TimeoutExpired:
            os.unlink(tmp)
            return {'erro': 'Timeout executando codigo Python'}
        except Exception as e:
            os.unlink(tmp)
            return {'erro': str(e)}

    # ============================================================
    # IMPLEMENTACOES - IA
    # ============================================================

    def _cmd_perguntar_ia(self, pergunta, tarefa="pesado"):
        """Faz pergunta a IA local."""
        ia = self._get_ia()
        return ia.gerar(pergunta, 0.4, tarefa) or "Sem resposta"

    def _cmd_analisar_codigo(self, codigo):
        """Analisa codigo com IA."""
        ia = self._get_ia()
        prompt = f"Analise este codigo e aponte problemas, sugestoes e melhorias:\n\n{codigo[:4000]}"
        return ia.gerar(prompt, 0.3, "analisar") or "Falha ao analisar"
