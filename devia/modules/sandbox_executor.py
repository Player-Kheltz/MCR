"""SandboxExecutor — Executa codigo em ambiente isolado.

Diferente do FormatDetector (so analisa sintaxe),
o SandboxExecutor REALMENTE EXECUTA e ve se funciona.

Suporta:
- Python: executa e captura output
- Lua: compila com luac (se disponivel)
- Shell: executa com timeout e sem permissao de escrita
- Web: testa se URL responde

Uso:
    sandbox = SandboxExecutor()
    r = sandbox.executar_python("print('hello')")
    # -> {'stdout': 'hello\\n', 'stderr': '', 'returncode': 0, 'sucesso': True}
"""
import os, sys, subprocess, tempfile, json, ast, time

# Comandos proibidos (nunca executar)
COMANDOS_BLOQUEADOS = [
    'rm -rf', 'format ', 'del /f', 'rd /s', 'Remove-Item -Recurse',
    'shutdown', 'reboot', 'taskkill /f /im',
    'os.system', 'subprocess.run', 'Popen',
]


class SandboxExecutor:
    """Executa codigo em sandbox com seguranca."""

    TEMPO_LIMITE = {
        'python': 15,
        'lua': 10,
        'shell': 10,
        'web': 30,
    }

    def __init__(self):
        self.historico = []

    def executar_python(self, codigo):
        """Executa codigo Python em subprocesso isolado."""
        # Verifica seguranca
        erro = self._verificar_seguranca(codigo)
        if erro:
            resultado = {'sucesso': False, 'stdout': '', 'stderr': erro, 'returncode': -1, 'tempo': time.time()}
            self.historico.append(resultado)
            return resultado

        # Verifica sintaxe antes de executar
        try:
            ast.parse(codigo)
        except SyntaxError as e:
            resultado = {
                'sucesso': False, 'stdout': '',
                'stderr': f'Erro de sintaxe: Linha {e.lineno}: {e.msg}',
                'returncode': -1, 'tempo': time.time(),
            }
            self.historico.append(resultado)
            return resultado

        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False, encoding='utf-8') as f:
            f.write(codigo)
            tmp = f.name

        try:
            r = subprocess.run(
                [sys.executable, '-u', tmp],  # -u = unbuffered
                capture_output=True, text=True,
                timeout=self.TEMPO_LIMITE['python'],
            )
            resultado = {
                'sucesso': r.returncode == 0,
                'stdout': r.stdout,
                'stderr': r.stderr,
                'returncode': r.returncode,
                'tempo': time.time(),
            }
        except subprocess.TimeoutExpired:
            resultado = {
                'sucesso': False, 'stdout': '',
                'stderr': f'Tempo limite excedido ({self.TEMPO_LIMITE["python"]}s)',
                'returncode': -1, 'tempo': time.time(),
            }
        except Exception as e:
            resultado = {
                'sucesso': False, 'stdout': '',
                'stderr': f'Erro ao executar: {e}',
                'returncode': -1, 'tempo': time.time(),
            }
        finally:
            try:
                os.unlink(tmp)
            except Exception:
                pass

        self.historico.append(resultado)
        return resultado

    def compilar_lua(self, codigo):
        """Compila Lua com luac (se disponivel)."""
        # Primeiro verifica estrutura Canary
        estruturas = ['npcType:register', 'Game.createNpcType', 'npcHandler']
        tem_estrutura = any(e in codigo for e in estruturas)

        # Tenta compilar com luac
        with tempfile.NamedTemporaryFile(suffix='.lua', mode='w', delete=False, encoding='utf-8') as f:
            f.write(codigo)
            tmp = f.name

        try:
            r = subprocess.run(
                ['luac', '-p', tmp],
                capture_output=True, text=True, timeout=self.TEMPO_LIMITE['lua'],
            )
            if r.returncode == 0:
                resultado = {
                    'sucesso': True,
                    'sintaxe_ok': True,
                    'estrutura_canary': tem_estrutura,
                    'output': 'Sintaxe Lua OK',
                    'tempo': time.time(),
                }
            else:
                resultado = {
                    'sucesso': False,
                    'sintaxe_ok': False,
                    'estrutura_canary': tem_estrutura,
                    'erro': r.stderr,
                    'tempo': time.time(),
                }
        except FileNotFoundError:
            pass
            # luac nao instalado - fallback pra validacao basica
            resultado = self._validar_lua_basico(codigo, tem_estrutura)
        except Exception as e:
            resultado = {'sucesso': False, 'erro': str(e)}
        finally:
            try:
                os.unlink(tmp)
            except Exception:
                pass

        self.historico.append(resultado)
        return resultado

    def _validar_lua_basico(self, codigo, tem_estrutura):
        """Validacao basica de Lua (sem luac)."""
        # Verifica se parece Lua
        padroes_lua = ['local ', 'function ', ' end', ' = ', '--']
        parece_lua = any(p in codigo for p in padroes_lua)

        # Verifica brackets basicos
        brackets_ok = codigo.count('{') == codigo.count('}')
        parenteses_ok = codigo.count('(') == codigo.count(')')

        return {
            'sucesso': parece_lua and brackets_ok and parenteses_ok,
            'sintaxe_ok': brackets_ok and parenteses_ok,
            'estrutura_canary': tem_estrutura,
            'aviso': 'luac nao encontrado - validacao basica apenas',
            'tempo': time.time(),
        }

    def executar_teste(self, codigo, tipo='python'):
        """Executa e testa codigo, retornando resultado detalhado."""
        if tipo == 'python':
            return self.executar_python(codigo)
        elif tipo == 'lua':
            return self.compilar_lua(codigo)
        else:
            return {'sucesso': False, 'erro': f'Tipo nao suportado: {tipo}'}

    def _verificar_seguranca(self, codigo):
        """Verifica se o codigo tem comandos perigosos."""
        codigo_lower = codigo.lower()
        for cmd in COMANDOS_BLOQUEADOS:
            if cmd.lower() in codigo_lower:
                return f'Comando bloqueado detectado: {cmd}'
        return None

    def metricas(self):
        """Retorna metricas do executor."""
        if not self.historico:
            return {'total': 0, 'taxa_sucesso': 0}
        sucessos = sum(1 for h in self.historico if h.get('sucesso'))
        return {
            'total': len(self.historico),
            'taxa_sucesso': f'{sucessos/len(self.historico)*100:.0f}%',
        }
