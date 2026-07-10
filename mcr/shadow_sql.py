"""mcr.shadow_sql — Sandbox SQL para validar queries sem banco real.

Usa sqlite3 (stdlib) em memoria com whitelist restritiva de comandos.
MESMA interface duck-typed do shadow_canary e shadow_dotnet.

Comandos PERMITIDOS: SELECT, CREATE TABLE, INSERT, UPDATE, DELETE
Comandos BLOQUEADOS: DROP, ALTER, TRUNCATE, EXEC, ATTACH, DETACH, PRAGMA (perigoso)
"""
import sqlite3
import re
import traceback
from pathlib import Path
from typing import Dict, List, Optional


_COMANDOS_BLOQUEADOS = re.compile(
    r'\b(drop|alter|truncate|exec|attach|detach|pragma|vacuum|reindex)\b',
    re.IGNORECASE,
)

_COMANDOS_PERMITIDOS = re.compile(
    r'\b(select|create\s+table|insert|update|delete)\b',
    re.IGNORECASE,
)


class ShadowSQL:
    """Sandbox SQL: executa queries em SQLite em memoria com whitelist.

    Uso:
        ss = ShadowSQL()
        res = ss.executar("SELECT 1")
        # -> {'valido': True, 'resultados': [(1,)], 'erros': []}

        res = ss.executar("DROP TABLE users")
        # -> {'valido': False, 'erros': [...], 'comando_bloqueado': True}
    """

    def __init__(self, timeout: float = 0.5):
        self.timeout = timeout

    def validar(self, codigo: str) -> Dict:
        """Valida SQL — executa no sandbox e retorna resultado.

        Retorna: {'valido': bool, 'erros': list, 'saida': str, 'comando_bloqueado': bool}
        """
        return self.executar(codigo)

    def executar(self, codigo: str) -> Dict:
        """Executa uma ou mais queries SQL no sandbox SQLite em memoria.

        Args:
            codigo: string com uma ou mais queries SQL

        Returns:
            dict com valido, erros, resultados
        """
        if not codigo or not codigo.strip():
            return {
                'valido': False,
                'erros': [{'codigo': 'EMPTY', 'mensagem': 'Codigo SQL vazio', 'linha': 0}],
                'saida': '',
                'resultados': [],
                'comando_bloqueado': False,
            }

        codigo = codigo.strip()

        whitelist_match = _COMANDOS_PERMITIDOS.search(codigo)
        blacklist_match = _COMANDOS_BLOQUEADOS.search(codigo)

        if blacklist_match and (not whitelist_match or blacklist_match.start() < whitelist_match.start()):
            comando = blacklist_match.group(1)
            return {
                'valido': False,
                'erros': [{'codigo': 'BLOCKED', 'mensagem': f'Comando bloqueado: {comando}', 'linha': 0}],
                'saida': f'Comando "{comando}" nao permitido no sandbox',
                'resultados': [],
                'comando_bloqueado': True,
            }

        try:
            conn = sqlite3.connect(':memory:')
            conn.execute('PRAGMA journal_mode=OFF')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            resultados = []
            erros = []
            linhas_afetadas = 0

            statements = self._split_statements(codigo)

            for stmt in statements:
                if not stmt.strip():
                    continue

                bloqueado = _COMANDOS_BLOQUEADOS.search(stmt)
                if bloqueado:
                    erros.append({
                        'codigo': 'BLOCKED',
                        'mensagem': f'Comando bloqueado: {bloqueado.group(1)}',
                        'linha': 0,
                    })
                    continue

                try:
                    cursor.execute(stmt)
                    if stmt.strip().upper().startswith('SELECT'):
                        rows = cursor.fetchall()
                        resultados.append([dict(row) for row in rows])
                    else:
                        linhas_afetadas += cursor.rowcount
                        resultados.append({'affected_rows': cursor.rowcount})
                except sqlite3.Error as e:
                    erros.append({
                        'codigo': 'SQL_ERROR',
                        'mensagem': str(e),
                        'linha': 0,
                        'stmt': stmt[:100],
                    })

            conn.commit()
            conn.close()

            valido = len(erros) == 0 and len(resultados) > 0

            saida_parts = []
            if resultados:
                saida_parts.append(f'{len(resultados)} statement(s) executados')
                if linhas_afetadas:
                    saida_parts.append(f'{linhas_afetadas} linhas afetadas')
            if erros:
                saida_parts.append(f'{len(erros)} erro(s)')

            return {
                'valido': valido,
                'erros': erros,
                'saida': '; '.join(saida_parts),
                'resultados': resultados[:10],
                'resultados_count': len(resultados),
                'erros_count': len(erros),
                'comando_bloqueado': False,
            }

        except Exception as e:
            return {
                'valido': False,
                'erros': [{'codigo': 'EXCEPTION', 'mensagem': str(e)[:200], 'linha': 0}],
                'saida': traceback.format_exc()[:500],
                'resultados': [],
                'comando_bloqueado': False,
            }

    @staticmethod
    def _split_statements(codigo: str) -> List[str]:
        """Divide codigo SQL em statements individuais por ';'."""
        statements = []
        for stmt in codigo.split(';'):
            stmt = stmt.strip()
            if stmt:
                statements.append(stmt)
        return statements

    def aprender_com_erro(self, resultado: Dict) -> Optional[str]:
        """Aprende com erros SQL — registra penalidade.

        Retorna: tipo de erro registrado, ou None se sem erros.
        """
        if resultado.get('valido', False):
            return None
        erros = resultado.get('erros', [])
        if not erros:
            return None

        erro_principal = erros[0]
        codigo = erro_principal.get('codigo', 'SQL_ERROR')

        if codigo == 'BLOCKED':
            return 'comando_bloqueado'
        elif codigo == 'EMPTY':
            return 'sql_vazio'
        elif codigo == 'EXCEPTION':
            return 'excecao_sql'
        else:
            mensagem = erro_principal.get('mensagem', '').lower()
            if 'syntax error' in mensagem:
                return 'erro_sintaxe_sql'
            elif 'no such table' in mensagem:
                return 'tabela_inexistente'
            elif 'no such column' in mensagem:
                return 'coluna_inexistente'
            elif 'ambiguous column' in mensagem:
                return 'coluna_ambigua'
            elif 'already exists' in mensagem:
                return 'tabela_ja_existe'
            elif 'constraint failed' in mensagem:
                return 'restricao_violada'
            elif 'unique constraint' in mensagem:
                return 'unicidade_violada'
            elif 'foreign key constraint' in mensagem:
                return 'chave_estrangeira'
            elif 'not null constraint' in mensagem:
                return 'nulo_nao_permitido'
            elif 'parse error' in mensagem:
                return 'erro_parse_sql'
            else:
                return f'erro_sql_{codigo.lower()}'


# Funcoes modulares (interface duck-typing) ---

def validar_sintaxe(codigo: str) -> Dict:
    ss = ShadowSQL()
    return ss.executar(codigo)


def executar_shadow_codigo(codigo: str) -> Dict:
    ss = ShadowSQL()
    return ss.executar(codigo)


def aprender_com_erro(resultado: Dict) -> Optional[str]:
    ss = ShadowSQL()
    return ss.aprender_com_erro(resultado)


if __name__ == '__main__':
    # Auto-teste
    ss = ShadowSQL()

    # Teste SELECT valido
    res = ss.executar("SELECT 1 AS test; SELECT 'hello' AS greeting")
    print(f'SELECT valido: {res["valido"]}')
    for r in res.get('resultados', []):
        print(f'  -> {r}')

    # Teste CREATE TABLE + INSERT
    res2 = ss.executar("CREATE TABLE test (id INTEGER, name TEXT); INSERT INTO test VALUES (1, 'hello'); SELECT * FROM test")
    print(f'\nDDL+DML valido: {res2["valido"]}')
    for r in res2.get('resultados', []):
        print(f'  -> {r}')

    # Teste comando bloqueado
    res3 = ss.executar("DROP TABLE users")
    print(f'\nDROP bloqueado: {not res3["valido"]}, blocked={res3["comando_bloqueado"]}')

    # Teste erro de sintaxe
    res4 = ss.executar("SELECTT 1")
    print(f'\nErro sintaxe: {not res4["valido"]}, erros={len(res4["erros"])}')
