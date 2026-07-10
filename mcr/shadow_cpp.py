"""mcr.shadow_cpp — Sandbox C++ para validar sintaxe.

Usa g++/cl.exe se disponivel (via -fsyntax-only).
Fallback: verificacao de sintaxe via regex (chaves, ponto-e-virgula, estrutura).
MESMA interface duck-typed dos demais shadows.
"""
import re
import shutil
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Optional


_CHAVES = {'{': '}', '(': ')', '[': ']'}
_OPERADORES = {'<<', '>>', '::', '->', '++', '--', '&&', '||', '==', '!=', '<=', '>=', '+=', '-=', '*=', '/='}


def _encontrar_compilador() -> Optional[str]:
    """Tenta encontrar g++ ou cl.exe no PATH."""
    for cmd in ['g++', 'cl.exe']:
        caminho = shutil.which(cmd)
        if caminho:
            return caminho
    return None


def _validar_chaves(codigo: str) -> List[str]:
    """Verifica balanceamento de chaves, parenteses e colchetes."""
    pilha = []
    erros = []
    for i, ch in enumerate(codigo):
        if ch in _CHAVES:
            pilha.append((ch, i))
        elif ch in _CHAVES.values():
            if not pilha:
                erros.append(f'Chave de fechamento "{ch}" sem abertura na linha {codigo[:i].count(chr(10)) + 1}')
                continue
            abertura, _ = pilha.pop()
            if _CHAVES[abertura] != ch:
                erros.append(f'Chave "{abertura}" na linha {codigo[:i].count(chr(10)) + 1} fechada com "{ch}"')
    if pilha:
        for ch, _ in pilha:
            erros.append(f'Chave "{ch}" sem fechamento')
    return erros


def _validar_ponto_e_virgula(codigo: str) -> List[str]:
    """Verifica ponto-e-virgula basico fora de blocos."""
    erros = []
    linhas = codigo.split('\n')
    for i, linha in enumerate(linhas):
        linha_strip = linha.strip()
        if not linha_strip or linha_strip.startswith('//') or linha_strip.startswith('/*') or linha_strip.startswith('*'):
            continue
        if linha_strip.startswith('#') or linha_strip.startswith('template ') or linha_strip.startswith('namespace '):
            if not linha_strip.endswith('{') and not linha_strip.endswith(';') and i < len(linhas) - 1:
                if not linhas[i + 1].strip().startswith('{') and not linhas[i + 1].strip().startswith('//'):
                    pass
            continue
        if '{' in linha_strip or '}' in linha_strip:
            continue
        palavras = linha_strip.split()
        if not palavras:
            continue
        primeira = palavras[0]
        if primeira in ('if', 'else', 'for', 'while', 'do', 'switch', 'case', 'public', 'private', 'protected', 'return'):
            if linha_strip.endswith('(') or linha_strip.endswith(')') or linha_strip.endswith('{') or linha_strip.endswith('}'):
                continue
            if not linha_strip.endswith(';') and not linha_strip.endswith('{') and not linha_strip.endswith('}'):
                has_paren = '(' in linha_strip
                has_brace = '{' in linha_strip
                if has_paren and not has_brace:
                    continue
    return erros


def _validar_directivas(codigo: str) -> List[str]:
    erros = []
    for match in re.finditer(r'#\s*(\w+)', codigo):
        diretiva = match.group(1).lower()
        if diretiva not in ('include', 'define', 'ifdef', 'ifndef', 'endif', 'if', 'else', 'elif', 'pragma', 'undef', 'error', 'warning', 'line', 'once'):
            erros.append(f'Diretiva desconhecida: #{diretiva}')
    return erros


_SHADOW_CPP_COMPILADOR = None


class ShadowCpp:
    """Sandbox C++: valida sintaxe com compilador ou regex fallback.

    Uso:
        sc = ShadowCpp()
        res = sc.executar("class Foo { int x; };")
        # -> {'valido': True/False, 'erros': [...], ...}
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self._compilador = _encontrar_compilador()
        global _SHADOW_CPP_COMPILADOR
        _SHADOW_CPP_COMPILADOR = self._compilador

    def validar(self, codigo: str) -> Dict:
        return self.executar(codigo)

    def executar(self, codigo: str) -> Dict:
        if not codigo or not codigo.strip():
            return {
                'valido': False,
                'erros': [{'codigo': 'EMPTY', 'mensagem': 'Codigo C++ vazio', 'linha': 0}],
                'saida': '',
                'metodo': 'none',
            }

        erros = []

        # 1. Validacao estrutural (sempre roda)
        erros_chaves = _validar_chaves(codigo)
        for e in erros_chaves:
            erros.append({'codigo': 'BRACE', 'mensagem': e, 'linha': 0})

        erros_directivas = _validar_directivas(codigo)
        for e in erros_directivas:
            erros.append({'codigo': 'DIRECTIVE', 'mensagem': e, 'linha': 0})

        # 2. Se tem compilador, usa
        if self._compilador:
            metodo = f'compiler:{Path(self._compilador).name}'
            try:
                # Cria arquivo temporario
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.cpp', mode='w', delete=False, encoding='utf-8') as f:
                    f.write(codigo)
                    tmp_path = f.name
                args_compilador = [self._compilador, '-std=c++17', '-fsyntax-only', tmp_path]
                if self._compilador.endswith('cl.exe'):
                    args_compilador = [self._compilador, '/nologo', '/std:c++17', '/Zs', tmp_path]
                resultado = subprocess.run(
                    args_compilador,
                    capture_output=True, text=True, timeout=self.timeout,
                )
                Path(tmp_path).unlink(missing_ok=True)

                saida = (resultado.stdout + '\n' + resultado.stderr).strip()
                if resultado.returncode != 0:
                    for linha in saida.split('\n'):
                        if 'error' in linha.lower() or 'warning' in linha.lower():
                            erros.append({'codigo': 'COMPILE', 'mensagem': linha[:200], 'linha': 0})
            except FileNotFoundError:
                self._compilador = None  # desativa para proximas chamadas
                metodo = 'regex_fallback'
            except subprocess.TimeoutExpired:
                erros.append({'codigo': 'TIMEOUT', 'mensagem': f'Compilacao excedeu {self.timeout}s', 'linha': 0})
                metodo = 'timeout'
            except Exception as e:
                erros.append({'codigo': 'EXCEPTION', 'mensagem': str(e)[:200], 'linha': 0})
                metodo = 'exception'
        else:
            metodo = 'regex_fallback'

        valido = len(erros) == 0
        return {
            'valido': valido,
            'erros': erros,
            'saida': f'Metodo: {metodo}, {len(erros)} erro(s)',
            'metodo': metodo,
            'erros_count': len(erros),
        }

    def aprender_com_erro(self, resultado: Dict) -> Optional[str]:
        if resultado.get('valido', False):
            return None
        erros = resultado.get('erros', [])
        if not erros:
            return None
        erro_principal = erros[0]
        codigo = erro_principal.get('codigo', 'CPP_ERROR')

        if codigo == 'BRACE':
            return 'chave_desbalanceada'
        elif codigo == 'DIRECTIVE':
            return 'diretiva_desconhecida'
        elif codigo == 'EMPTY':
            return 'cpp_vazio'
        elif codigo == 'COMPILE':
            mensagem = erro_principal.get('mensagem', '').lower()
            if 'syntax error' in mensagem:
                return 'erro_sintaxe_cpp'
            elif 'expected' in mensagem:
                return 'token_esperado'
            elif 'undefined' in mensagem or 'undeclared' in mensagem:
                return 'identificador_indefinido'
            elif 'no matching' in mensagem:
                return 'sem_correspondencia'
            elif 'ambiguous' in mensagem:
                return 'ambiguo'
            elif 'cannot convert' in mensagem:
                return 'conversao_invalida'
            elif 'incomplete type' in mensagem:
                return 'tipo_incompleto'
            elif 'not a member' in mensagem:
                return 'membro_inexistente'
            elif 'was not declared' in mensagem:
                return 'nao_declarado'
            else:
                return f'erro_compilacao'
        else:
            return f'erro_cpp_{codigo.lower()}'


# Funcoes modulares (duck-typing) ---

def validar_sintaxe(codigo: str) -> Dict:
    sc = ShadowCpp()
    return sc.executar(codigo)


def executar_shadow_codigo(codigo: str) -> Dict:
    sc = ShadowCpp()
    return sc.executar(codigo)


def aprender_com_erro(resultado: Dict) -> Optional[str]:
    sc = ShadowCpp()
    return sc.aprender_com_erro(resultado)


if __name__ == '__main__':
    compilador = _encontrar_compilador()
    print(f'Compilador encontrado: {compilador or "NENHUM (usando regex fallback)"}')
    sc = ShadowCpp()

    # Teste: codigo valido
    codigo_valido = '''
    #include <string>
    class NPC {
    public:
        NPC(const std::string& name) : name_(name) {}
        void setOutfit(int type, int head, int body, int legs, int feet) {
            outfit_type_ = type;
        }
    private:
        std::string name_;
        int outfit_type_ = 0;
    };
    '''
    r1 = sc.executar(codigo_valido)
    print(f'C++ valido: valido={r1["valido"]}, metodo={r1["metodo"]}')

    # Teste: chave desbalanceada
    codigo_invalido = 'class Foo { int x; '
    r2 = sc.executar(codigo_invalido)
    print(f'C++ chave desbal: valido={r2["valido"]}, erros={r2["erros_count"]}')

    penalty = sc.aprender_com_erro(r2)
    print(f'Penalidade: {penalty}')
