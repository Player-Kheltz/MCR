"""mcr.lua_validator — Validador de scripts Lua para Canary.
Verifica: SQL injection, boas praticas Canary, estrutura obrigatoria.
Sem dependencias externas (MCR opcional removido — funcional sem ele)."""
import os, re, subprocess, tempfile
from typing import Dict, List, Optional
from mcr.paths import ROOT_DIR

BASE = ROOT_DIR

PADROES_SQL_INJECTION = [
    (r'db\.(?:query|storeQuery|asyncQuery)\s*\(\s*["\'](?:\s*\.\.\s*[^,])', 'Query com concatenacao de string'),
    (r'string\.format\s*\([^)]*["\'].*SELECT', 'string.format em query SQL'),
    (r'\.\.\s*(?:player:?)?\.?\s*getName\s*\(\s*\)', 'Nome de jogador concatenado em query'),
    (r'\.\.\s*player:?\.?getGuid\s*\(\s*\)', 'GUID concatenado em query'),
    (r'db\.query\s*\(\s*["\'][^"\']*%s', 'Placeholder %s sem escape em query'),
    (r'db\.storeQuery\s*\(\s*["\'][^"\']*\.\.', 'Concatenação em storeQuery'),
]

PADROES_BOAS_PRATICAS = [
    ('npcType:register', 'NPC registrado'),
    ('Game.createNpcType', 'NPC criado via factory'),
    ('NpcHandler:new', 'NpcHandler instanciado'),
    ('KeywordHandler:new', 'KeywordHandler instanciado'),
    ('FocusModule:new', 'FocusModule adicionado'),
    ('CALLBACK_MESSAGE_DEFAULT', 'Callback padrao definido'),
    ('setMessage(MESSAGE_GREET', 'Mensagem de saudacao definida'),
]

PADROES_ESTRUTURA_OBRIGATORIA = [
    ('local internalNpcName', 'Variavel internalNpcName'),
    ('npcType:register(npcConfig)', 'Registro do NPC'),
    ('npcConfig.name', 'Configuracao de nome'),
    ('npcConfig.outfit', 'Configuracao de outfit'),
    ('npcHandler:addModule', 'Modulo adicionado'),
]


class LuaValidator:
    def __init__(self, caminho_luac: Optional[str] = None):
        self.caminho_luac = caminho_luac or self._encontrar_luac()

    def validar(self, codigo: str) -> Dict:
        resultado = {
            'valido': True,
            'erros': [],
            'avisos': [],
            'sql_injection': [],
            'boas_praticas': [],
            'estrutura': [],
            'sintaxe': '',
        }
        self._verificar_sql_injection(codigo, resultado)
        self._verificar_boas_praticas(codigo, resultado)
        self._verificar_estrutura(codigo, resultado)
        if self.caminho_luac:
            resultado['sintaxe'] = self._verificar_sintaxe(codigo)
            if 'error' in resultado['sintaxe'].lower() or 'syntax' in resultado['sintaxe'].lower():
                resultado['valido'] = False
                resultado['erros'].append('Erro de sintaxe Lua: %s' % resultado['sintaxe'])
        self._validacoes_extras(codigo, resultado)
        estrutura_ok = all('OK:' in e for e in resultado['estrutura'])
        if not estrutura_ok:
            resultado['valido'] = False
        resultado['valido'] = (len(resultado['erros']) == 0 and
                               len(resultado['sql_injection']) == 0 and
                               estrutura_ok)
        return resultado

    def _verificar_sql_injection(self, codigo: str, resultado: Dict):
        for padrao, descricao in PADROES_SQL_INJECTION:
            matches = re.findall(padrao, codigo, re.IGNORECASE)
            if matches:
                resultado['sql_injection'].append({
                    'tipo': descricao,
                    'ocorrencias': len(matches),
                    'exemplo': matches[0] if isinstance(matches[0], str) else str(matches[0]),
                })
                resultado['erros'].append('SQL injection detectado: %s' % descricao)

    def _verificar_boas_praticas(self, codigo: str, resultado: Dict):
        for padrao, descricao in PADROES_BOAS_PRATICAS:
            if padrao in codigo:
                resultado['boas_praticas'].append(descricao)

    def _verificar_estrutura(self, codigo: str, resultado: Dict):
        for padrao, descricao in PADROES_ESTRUTURA_OBRIGATORIA:
            if padrao in codigo:
                resultado['estrutura'].append('OK: %s' % descricao)
            else:
                resultado['estrutura'].append('FALTANDO: %s' % descricao)
                resultado['avisos'].append('Estrutura ausente: %s' % descricao)

    def _verificar_sintaxe(self, codigo: str) -> str:
        if self.caminho_luac and os.path.exists(self.caminho_luac):
            try:
                with tempfile.NamedTemporaryFile(suffix='.lua', delete=False, mode='w', encoding='utf-8') as f:
                    f.write(codigo)
                    tmp = f.name
                r = subprocess.run(
                    [self.caminho_luac, '-p', tmp],
                    capture_output=True, text=True, timeout=30
                )
                os.unlink(tmp)
                if r.returncode == 0:
                    return 'OK'
                return r.stderr or r.stdout
            except Exception:
                return 'luac check failed'
        return 'luac nao disponivel'

    def _validacoes_extras(self, codigo: str, resultado: Dict):
        if 'onBuyItem' in codigo and 'npcConfig.shop' not in codigo:
            resultado['avisos'].append('NPC com onBuyItem mas sem npcConfig.shop')
        for m in re.finditer(r'(?:local\s+)?function\s+(\w+)', codigo):
            nome_func = m.group(1)
            pos = m.start()
            conteudo = codigo[pos:]
            count_end = 0
            for i, linha in enumerate(conteudo.split('\n')):
                if linha.strip().startswith('end'):
                    count_end += 1
                if count_end >= 2:
                    if i > 50:
                        resultado['avisos'].append('Funcao longa: %s (~%d linhas)' % (nome_func, i))
                    break

    def _encontrar_luac(self) -> Optional[str]:
        # Busca recursiva (filesystem discovery, zero hardcode)
        try:
            for path in Path(BASE).glob('**/luac*'):
                if path.is_file() and os.access(path, os.X_OK):
                    return str(path)
        except Exception:
            pass
        try:
            r = subprocess.run(['where', 'luac'], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip().split('\n')[0].strip()
        except Exception:
            pass
        return None
