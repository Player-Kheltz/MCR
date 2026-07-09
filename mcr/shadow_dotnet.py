"""mcr.shadow_dotnet — Sandbox C# para compilar e validar codigo sem servidor real.

Usa a CLI do .NET SDK (dotnet build) como executor isolado.
Parceia erros CSxxxx e os converte em penalidades Markov,
mesma interface do shadow_canary.py (duck typing).
"""
import os
import sys
import re
import json
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional, List


class ShadowDotnet:
    """Sandbox C#: compila codigo com dotnet build, captura erros.
    
    Uso:
        sd = ShadowDotnet()
        res = sd.executar("class C { void M() {} }")
        # → {'valido': True, 'erros': [], 'saida': '...'}
    """

    # Template minimo de console project
    PROJETO_TEMPLATE = '''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
</Project>'''

    def __init__(self, dotnet_path: str = 'dotnet', timeout: int = 30):
        self.dotnet_path = dotnet_path
        self.timeout = timeout
        self._temp_dir = None
        self._temp_proj = None

    def validar(self, codigo: str) -> Dict:
        """Valida codigo C# — compila com dotnet build.
        
        Retorna: {'valido': bool, 'erros': list, 'saida': str, 'codigos_erro': list}
        """
        return self.executar(codigo)

    def executar(self, codigo: str) -> Dict:
        """Compila codigo C# em um projeto temporario.
        
        Args:
            codigo: string de codigo C# valido (pode ser apenas classes, sem Main)
        
        Returns:
            dict com valido, erros (detalhados), saida (stdout+stderr)
        """
        # Cria projeto temporario
        temp_dir = Path(tempfile.mkdtemp(prefix='mcr_cs_'))
        try:
            # Cria .csproj
            proj_path = temp_dir / 'temp_cs.csproj'
            with open(proj_path, 'w', encoding='utf-8') as f:
                f.write(self.PROJETO_TEMPLATE)

            # Envolve o codigo em uma classe Program se nao tiver
            codigo_final = self._preparar_codigo(codigo)

            # Escreve o codigo
            cs_path = temp_dir / 'Program.cs'
            with open(cs_path, 'w', encoding='utf-8') as f:
                f.write(codigo_final)

            # Executa dotnet build
            resultado = subprocess.run(
                [self.dotnet_path, 'build', str(proj_path), '--nologo', '-v:q'],
                capture_output=True, text=True, timeout=self.timeout,
                cwd=str(temp_dir)
            )

            saida = resultado.stdout + '\n' + resultado.stderr
            erros = self._parsear_erros(saida)
            valido = resultado.returncode == 0

            return {
                'valido': valido,
                'erros': erros,
                'saida': saida[:2000],
                'codigos_erro': [e['codigo'] for e in erros],
                'returncode': resultado.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                'valido': False,
                'erros': [{'codigo': 'TIMEOUT', 'mensagem': f'Compilacao excedeu {self.timeout}s', 'linha': 0}],
                'saida': 'timeout',
                'codigos_erro': ['TIMEOUT'],
                'returncode': -1,
            }
        except FileNotFoundError:
            return {
                'valido': False,
                'erros': [{'codigo': 'DOTNET_NOT_FOUND', 'mensagem': f'Executavel "{self.dotnet_path}" nao encontrado', 'linha': 0}],
                'saida': '',
                'codigos_erro': ['DOTNET_NOT_FOUND'],
                'returncode': -2,
            }
        except Exception as e:
            return {
                'valido': False,
                'erros': [{'codigo': 'EXCEPTION', 'mensagem': str(e)[:200], 'linha': 0}],
                'saida': str(e)[:500],
                'codigos_erro': ['EXCEPTION'],
                'returncode': -3,
            }
        finally:
            # Limpa projeto temporario
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

    def _preparar_codigo(self, codigo: str) -> str:
        """Prepara codigo C# para compilacao.
        
        Se o codigo ja tem um ponto de entrada (Main explicito ou top-level statement),
        usa como esta. Caso contrario, envolve em uma classe Program com Main.
        """
        codigo = codigo.strip()
        if not codigo:
            return '// (vazio)'

        # Se ja tem Main ou top-level statements, usa direto
        if 'static void Main' in codigo or 'static Task Main' in codigo:
            return codigo

        # Top-level statements: se comeca com using ou class, pode ter statements
        # Detecta se tem pelo menos uma declaracao executavel
        if any(codigo.startswith(kw) for kw in ['using', 'namespace', 'class', 'struct',
                                                  'interface', 'record', 'public', 'internal',
                                                  'sealed', 'abstract', 'static', 'readonly',
                                                  '#']):
            return codigo

        # Se parece com um snippet de expressao, envolve em Program
        return f'''// Gerado pelo MCR-DevIA ShadowDotnet
Console.WriteLine("MCR C# Shadow Test");
{codigo}
'''

    def _parsear_erros(self, saida: str) -> List[Dict]:
        """Extrai erros de compilacao C# (CSxxxx) da saida do dotnet build.
        
        Formato tipico:
        Program.cs(line,col): error CS0103: The name 'X' does not exist...
        """
        erros = []
        # Padrao: arquivo.cs(line,col): error CSXXXX: mensagem
        padrao = re.compile(
            r'([\w\d_.]+\.cs)\((\d+)(?:,\d+)?\)\s*:\s*(error|warning)\s+(CS\d+)\s*:\s*(.*)',
            re.IGNORECASE
        )
        for match in padrao.finditer(saida):
            erros.append({
                'arquivo': match.group(1),
                'linha': int(match.group(2)),
                'tipo': match.group(3).lower(),
                'codigo': match.group(4).upper(),
                'mensagem': match.group(5).strip(),
            })

        # Se nao encontrou com o padrao, tenta parse generico
        if not erros:
            for linha in saida.split('\n'):
                linha = linha.strip()
                if 'error CS' in linha or 'error CS' in linha.upper():
                    erros.append({
                        'codigo': 'CS????',
                        'mensagem': linha[:200],
                        'linha': 0,
                    })

        return erros

    def aprender_com_erro(self, resultado: Dict) -> Optional[str]:
        """Aprende com erros de compilacao — registra penalidade.
        
        Retorna: tipo de erro registrado, ou None se sem erros.
        """
        if resultado.get('valido', False):
            return None
        erros = resultado.get('erros', [])
        if not erros:
            return None
        # Classifica o erro principal
        erro_principal = erros[0]
        codigo = erro_principal.get('codigo', 'CS????')
        # Categorias de erro C#
        if codigo.startswith('CS0103'):
            tipo = 'nome_indefinido'
        elif codigo.startswith('CS0117'):
            tipo = 'membro_inexistente'
        elif codigo.startswith('CS0246'):
            tipo = 'tipo_nao_encontrado'
        elif codigo.startswith('CS1061'):
            tipo = 'metodo_inexistente'
        elif codigo.startswith('CS1501'):
            tipo = 'sobrecarga_invalida'
        elif codigo.startswith('CS0029'):
            tipo = 'conversao_invalida'
        elif codigo.startswith('CS0165'):
            tipo = 'uso_variavel_nao_atribuida'
        elif codigo.startswith('CS0120'):
            tipo = 'referencia_objeto_requerida'
        elif codigo.startswith('CS1729'):
            tipo = 'construtor_inexistente'
        elif codigo.startswith('CS0305'):
            tipo = 'argumento_generico_invalido'
        else:
            tipo = f'erro_compilacao_{codigo.lower()}'
        return tipo


# Funcoes modulares (interface duck-typing com shadow_canary) ----

def validar_sintaxe(codigo: str) -> Dict:
    """Valida sintaxe C# (alias para compatibilidade)."""
    sd = ShadowDotnet()
    return sd.executar(codigo)


def executar_shadow_codigo(codigo: str) -> Dict:
    """Executa codigo C# no sandbox (compilacao, nao runtime)."""
    sd = ShadowDotnet()
    return sd.executar(codigo)


def aprender_com_erro(resultado: Dict) -> Optional[str]:
    """Aprende com erros de compilacao C#."""
    sd = ShadowDotnet()
    return sd.aprender_com_erro(resultado)


if __name__ == '__main__':
    # Auto-teste
    sd = ShadowDotnet()

    # Teste com codigo valido
    codigo_valido = '''
    using System;
    class Teste { static void Main() { Console.WriteLine("OK"); } }
    '''
    res = sd.executar(codigo_valido)
    print(f'Valido: {res["valido"]}')
    print(f'Erros: {res["erros"]}')
    print(f'Returncode: {res["returncode"]}')

    # Teste com codigo invalido
    codigo_invalido = 'class X { void Y() { Z(); } }'
    res2 = sd.executar(codigo_invalido)
    print(f'\nInvalido: {res2["valido"]}')
    print(f'Erros: {json.dumps(res2["erros"], indent=2)[:500]}')
