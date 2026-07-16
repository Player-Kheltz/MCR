#!/usr/bin/env python3
"""
mcr.gerador_codigo — Gerador de codigo multi-linguagem via MCRSQLite.

Suporta: Lua, Python, SQL, C#
Usa MCRSQLite treinado com corpus de codigo + golden templates.
Valida sintaxe para cada linguagem.

Uso:
    gerador = GeradorCodigo()
    lua = gerador.gerar('lua', 'function')
    python = gerador.gerar('python', 'def calculate')
    sql = gerador.gerar('sql', 'SELECT')
"""
import os, sys, os, re, ast
from typing import Dict, List, Optional, Tuple
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from mcr.mcr_sqlite import MCRSQLite
from mcr.paths import CACHE_DIR


class GeradorCodigo:
    """Gerador de codigo multi-linguagem baseado em MCRSQLite."""

    TEMPLATES = {
        'lua': {
            'npc': [
                'local internalNpcName = "NPC_NAME"',
                'local npcType = Game.createNpcType(internalNpcName)',
                'local npcConfig = {}',
                'npcConfig.name = internalNpcName',
                'npcConfig.description = "NPC_DESCRIPTION"',
                'npcConfig.maxHealth = 100',
            ],
            'monster': [
                'local internalMonsterName = "MONSTER_NAME"',
                'local monsterType = Game.createMonsterType(internalMonsterName)',
                'local monsterConfig = {}',
                'monsterConfig.name = internalMonsterName',
                'monsterConfig.maxHealth = 5000',
                'monsterConfig.experience = 2000',
            ],
            'quest': [
                'local questAction = Action()',
                'function questAction.onUse(player, item, fromPosition, target, toPosition, isHotkey)',
                '    if item:getId() == ITEM_ID then',
                '        player:sendTextMessage(MESSAGE_EVENT_ADVANCE, "QUEST_MESSAGE")',
                '        return true',
                '    end',
                '    return false',
                'end',
            ],
        },
        'python': {
            'function': [
                'def FUNCTION_NAME(PARAMS):',
                '    """DOCSTRING."""',
                '    pass',
            ],
            'class': [
                'class CLASS_NAME:',
                '    """DOCSTRING."""',
                '    def __init__(self):',
                '        pass',
            ],
        },
        'sql': {
            'select': ['SELECT * FROM TABLE_NAME'],
            'create': ['CREATE TABLE TABLE_NAME (id INTEGER PRIMARY KEY)'],
            'insert': ['INSERT INTO TABLE_NAME (COLUMNS) VALUES (VALUES)'],
        },
    }

    def __init__(self, db_path: str = None):
        db_codigo = db_path or str(CACHE_DIR / 'mcr_codigo.db')
        if os.path.exists(db_codigo):
            self.mcr = MCRSQLite(db_codigo, n_max=10, identidade='codigo')
        else:
            self.mcr = MCRSQLite(db_codigo, n_max=10, identidade='codigo')

        self._cache_geracoes: Dict[str, List[str]] = {}

    def gerar(self, linguagem: str, semente: str,
              passos: int = 20, tipo: str = None) -> str:
        """Gera codigo em uma linguagem especifica.

        Args:
            linguagem: 'lua', 'python', 'sql', 'csharp'
            semente: palavra ou frase inicial
            passos: comprimento da geracao
            tipo: tipo de codigo (npc, monster, function, etc.)

        Returns:
            string com codigo gerado
        """
        # 1. Template estrutural
        template = self._get_template(linguagem, tipo, semente)

        # 2. Geracao Markoviana para preencher gaps
        tokens_semente = self._tokenizar(semente, linguagem)
        gerado = self._gerar_sequencia(tokens_semente, passos)

        # 3. Montar codigo final
        codigo = self._montar_codigo(linguagem, template, gerado, semente)

        # 4. Validar
        valido, erro = self.validar(codigo, linguagem)

        return {
            'linguagem': linguagem,
            'codigo': codigo,
            'valido': valido,
            'erro': erro,
            'tokens_gerados': len(gerado),
            'template': bool(template),
        }

    def gerar_lua(self, tipo: str = None, semente: str = 'function') -> Dict:
        return self.gerar('lua', semente, passos=25, tipo=tipo)

    def gerar_python(self, tipo: str = 'function', semente: str = 'def') -> Dict:
        return self.gerar('python', semente, passos=20, tipo=tipo)

    def gerar_sql(self, tipo: str = 'select', semente: str = 'SELECT') -> Dict:
        return self.gerar('sql', semente, passos=15, tipo=tipo)

    # ═══════════════════════════════════════════════════
    # INTERNOS
    # ═══════════════════════════════════════════════════

    def _get_template(self, linguagem: str, tipo: str, semente: str) -> List[str]:
        """Retorna template estrutural se existir."""
        lang_templates = self.TEMPLATES.get(linguagem, {})
        if tipo and tipo in lang_templates:
            return lang_templates[tipo]

        # Match parcial
        semente_lower = semente.lower()
        for t_name, t_lines in lang_templates.items():
            if t_name in semente_lower:
                return t_lines

        return []

    def _tokenizar(self, texto: str, linguagem: str) -> List[str]:
        """Tokeniza preservando estrutura da linguagem."""
        if linguagem == 'sql':
            return re.findall(r'[A-Z_]+|[a-z_]\w*|\d+|[(),;*]', texto)
        elif linguagem == 'python':
            return re.findall(r'[a-zA-Z_]\w*|\d+|[^\s\w]|[()\[\]{}:,]', texto)
        else:
            return re.findall(r'[a-zA-Z_]\w*|\d+|[^\s\w]', texto)

    def _gerar_sequencia(self, tokens: List[str], passos: int) -> List[str]:
        """Gera sequencia de tokens via MCRSQLite."""
        if not tokens:
            return []

        semente = tokens[0]
        cadeia = self.mcr.gerar(semente, passos=passos)
        return cadeia if len(cadeia) > 1 else tokens

    def _montar_codigo(self, linguagem: str, template: List[str],
                       gerado: List[str], semente: str) -> str:
        """Monta o codigo final combinando template + geracao."""
        if template:
            # Usa template como estrutura, preenche gaps com geracao
            linhas = []
            for linha in template:
                if 'NAME' in linha or 'DESCRIPTION' in linha or 'PARAMS' in linha \
                   or 'TABLE_NAME' in linha or 'COLUMNS' in linha or 'VALUES' in linha \
                   or 'MESSAGE' in linha or 'ITEM_ID' in linha:
                    # Preencher gaps com tokens gerados
                    preenchimento = ' '.join(gerado[1:3]) if len(gerado) > 2 else 'placeholder'
                    linha = linha.replace('NPC_NAME', preenchimento[:20])
                    linha = linha.replace('MONSTER_NAME', preenchimento[:20])
                    linha = linha.replace('NPC_DESCRIPTION', ' '.join(gerado[3:8]) if len(gerado) > 5 else 'A mysterious figure')
                    linha = linha.replace('TABLE_NAME', ' '.join(gerado[2:4]) if len(gerado) > 3 else 'my_table')
                    linha = linha.replace('COLUMNS', ' '.join(gerado[2:4]) if len(gerado) > 3 else 'name, value')
                    linha = linha.replace('VALUES', ' '.join(gerado[2:4]) if len(gerado) > 3 else "'val'")
                    linha = linha.replace('QUEST_MESSAGE', ' '.join(gerado[2:6]) if len(gerado) > 4 else 'Quest complete!')
                    linha = linha.replace('ITEM_ID', gerado[1] if len(gerado) > 1 else '1234')
                    linha = linha.replace('FUNCTION_NAME', gerado[1] if len(gerado) > 1 else 'my_func')
                    linha = linha.replace('CLASS_NAME', gerado[1].capitalize() if len(gerado) > 1 else 'MyClass')
                    linha = linha.replace('PARAMS', 'self')
                    linha = linha.replace('DOCSTRING', ' '.join(gerado[2:6]) if len(gerado) > 4 else 'Does something.')
                    linha = re.sub(r'[=;]\s*--.*', '', linha)  # remove comments mid-statement
                linhas.append(linha)

            # Adicionar geracao extra apos o template
            if len(gerado) > 3 and linguagem != 'sql':
                linhas.append('    -- ' + ' '.join(gerado[5:]))
            return '\n'.join(linhas)

        # Sem template: usar so a geracao
        return ' '.join(gerado)

    # ═══════════════════════════════════════════════════
    # VALIDACAO
    # ═══════════════════════════════════════════════════

    def validar(self, codigo: str, linguagem: str) -> Tuple[bool, str]:
        """Valida sintaxe do codigo gerado."""
        if not codigo or len(codigo.strip()) < 5:
            return False, 'codigo vazio'

        if linguagem == 'python':
            return self._validar_python(codigo)
        elif linguagem == 'sql':
            return self._validar_sql(codigo)
        elif linguagem == 'lua':
            return self._validar_lua(codigo)
        else:
            return True, ''  # nao tem validador

    def _validar_python(self, codigo: str) -> Tuple[bool, str]:
        try:
            ast.parse(codigo)
            return True, ''
        except SyntaxError as e:
            return False, str(e)

    def _validar_sql(self, codigo: str) -> Tuple[bool, str]:
        import sqlite3
        try:
            conn = sqlite3.connect(':memory:')
            conn.execute(f"EXPLAIN {codigo}")
            conn.close()
            return True, ''
        except Exception as e:
            # Tenta so parse sem executar
            try:
                conn = sqlite3.connect(':memory:')
                conn.execute(f"SELECT sqlite_version()")
                conn.execute(f"EXPLAIN QUERY PLAN {codigo}")
                conn.close()
                return True, ''
            except Exception as e2:
                return False, str(e2)[:100]

    def _validar_lua(self, codigo: str) -> Tuple[bool, str]:
        # Validacao basica de estrutura Lua
        keywords = {'function', 'end', 'if', 'then', 'else', 'elseif',
                    'for', 'while', 'do', 'repeat', 'until', 'local',
                    'return', 'break', 'nil', 'true', 'false'}
        tokens = re.findall(r'[a-zA-Z_]\w*', codigo)
        # Verifica balanceamento de blocos (aproximado)
        opens = sum(1 for t in tokens if t in ('function', 'if', 'for', 'while', 'do', 'repeat'))
        closes = sum(1 for t in tokens if t == 'end')
        untils = sum(1 for t in tokens if t == 'until')

        if opens > closes + untils + 1:
            return False, f'blocos desbalanceados: {opens} abertos, {closes} fechados'
        return True, ''

    def stats(self) -> Dict:
        estados = self.mcr.conn.execute(
            'SELECT COUNT(DISTINCT key) FROM trans').fetchone()[0]
        trans = self.mcr.conn.execute(
            'SELECT COUNT(*) FROM trans').fetchone()[0]
        return {
            'estados': estados, 'transicoes': trans,
            'entropia': round(self.mcr.entropia_media(), 4),
        }

    def close(self):
        self.mcr.conn.close()


# ─── Teste ───────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 60)
    print('  GeradorCodigo — Teste')
    print('=' * 60)

    g = GeradorCodigo()
    print(f'  Backend: {g.stats()}')

    # Lua
    print('\n[Lua — NPC]')
    r = g.gerar_lua(tipo='npc', semente='local')
    print(f'  Valido: {r["valido"]}')
    print(r['codigo'][:300])

    # Lua Monster
    print('\n[Lua — Monster]')
    r = g.gerar_lua(tipo='monster', semente='local')
    print(f'  Valido: {r["valido"]}')
    print(r['codigo'][:300])

    # Python
    print('\n[Python — Function]')
    r = g.gerar_python(tipo='function', semente='def')
    print(f'  Valido: {r["valido"]}, Erro: {r["erro"]}')
    print(r['codigo'][:300])

    # SQL
    print('\n[SQL — SELECT]')
    r = g.gerar_sql(tipo='select', semente='SELECT')
    print(f'  Valido: {r["valido"]}, Erro: {r["erro"]}')
    print(r['codigo'][:200])

    # SQL Create
    print('\n[SQL — CREATE TABLE]')
    r = g.gerar_sql(tipo='create', semente='CREATE')
    print(f'  Valido: {r["valido"]}, Erro: {r["erro"]}')
    print(r['codigo'][:200])

    g.close()
    print('\nOK')
