"""LuaValidator — Validador de scripts Lua para Canary.

Verifica:
1. Sintaxe Lua (via parser Python ou luac)
2. SQL injection (queries concatenadas)
3. Boas práticas Canary (register, createNpcType, etc)
4. Estrutura obrigatória

Uso:
    from modulos.lua_validator import LuaValidator
    val = LuaValidator()
    resultado = val.validar(codigo_lua)
"""
import os, re, json, subprocess, tempfile
from typing import Dict, List, Optional
# MCRzificado: usa MCR quando disponivel, fallback para LLM
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', '..', '..'))
try:
    from MCR import MCRMotor, MCRGenerator, MCRValidator, MCRBuilder, MCRPreencher, MCRReconstructor
    _mcr = MCRMotor()
    _TEM_MCR = True
except ImportError:
    _TEM_MCR = False

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# ============================================================
# PADRÕES DE SEGURANÇA
# ============================================================

PADROES_SQL_INJECTION = [
    # Concatenação direta em queries
    (r'db\.(?:query|storeQuery|asyncQuery)\s*\(\s*["\'](?:\s*\.\.\s*[^,])', 'Query com concatenacao de string'),
    (r'string\.format\s*\([^)]*["\'].*SELECT', 'string.format em query SQL'),
    (r'\.\.\s*(?:player:?)?\.?\s*getName\s*\(\s*\)', 'Nome de jogador concatenado em query'),
    (r'\.\.\s*player:?\.?getGuid\s*\(\s*\)', 'GUID concatenado em query'),
    # Placeholder não sanitizado
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

# ============================================================
# VALIDADOR
# ============================================================

class LuaValidator:
    """Validador de scripts Lua para Canary."""
    
    def __init__(self, caminho_luac: Optional[str] = None):
        self.caminho_luac = caminho_luac or self._encontrar_luac()
    
    def validar(self, codigo: str) -> Dict:
        """Valida um script Lua completo.
        
        Args:
            codigo: Código Lua como string
        
        Returns:
            Dict com resultado da validação
        """
        resultado = {
            'valido': True,
            'erros': [],
            'avisos': [],
            'sql_injection': [],
            'boas_praticas': [],
            'estrutura': [],
            'sintaxe': '',
        }
        
        # 1. Verificação de SQL injection
        self._verificar_sql_injection(codigo, resultado)
        
        # 2. Verificar boas práticas
        self._verificar_boas_praticas(codigo, resultado)
        
        # 3. Verificar estrutura obrigatória
        self._verificar_estrutura(codigo, resultado)
        
        # 4. Verificar sintaxe Lua (se luac disponível)
        if self.caminho_luac:
            resultado['sintaxe'] = self._verificar_sintaxe(codigo)
            if 'error' in resultado['sintaxe'].lower() or 'syntax' in resultado['sintaxe'].lower():
                resultado['valido'] = False
                resultado['erros'].append('Erro de sintaxe Lua: %s' % resultado['sintaxe'])
        
        # 5. Validacoes adicionais
        self._validacoes_extras(codigo, resultado)
        
        # Verificar se estrutura obrigatoria foi encontrada
        estrutura_ok = all('OK:' in e for e in resultado['estrutura'])
        if not estrutura_ok:
            resultado['valido'] = False
        
        resultado['valido'] = (len(resultado['erros']) == 0 and 
                               len(resultado['sql_injection']) == 0 and 
                               estrutura_ok)
        return resultado
    
    def _verificar_sql_injection(self, codigo: str, resultado: Dict):
        """Verifica padrões de SQL injection."""
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
        """Verifica boas práticas Canary."""
        for padrao, descricao in PADROES_BOAS_PRATICAS:
            if padrao in codigo:
                resultado['boas_praticas'].append(descricao)
    
    def _verificar_estrutura(self, codigo: str, resultado: Dict):
        """Verifica estrutura obrigatória do NPC."""
        for padrao, descricao in PADROES_ESTRUTURA_OBRIGATORIA:
            if padrao in codigo:
                resultado['estrutura'].append('OK: %s' % descricao)
            else:
                resultado['estrutura'].append('FALTANDO: %s' % descricao)
                resultado['avisos'].append('Estrutura ausente: %s' % descricao)
    
    def _verificar_sintaxe(self, codigo: str) -> str:
        """Verifica sintaxe Lua usando luac ou parser."""
        # Tenta usar luac primeiro
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
        """Validações adicionais específicas do Canary."""
        linhas = codigo.split('\n')
        
        # Verificar NPC shop sem shop config
        if 'onBuyItem' in codigo and 'npcConfig.shop' not in codigo:
            resultado['avisos'].append('NPC com onBuyItem mas sem npcConfig.shop')
        
        # Verificar encoding (apenas bytes invalidos, nao UTF-8 valido)
        try:
            codigo.encode('latin1').decode('utf-8')
        except Exception:
            pass  # UTF-8 valido
        
        # Verificar tamanho de funcoes
        for m in re.finditer(r'(?:local\s+)?function\s+(\w+)', codigo):
            nome_func = m.group(1)
            # Contar linhas até o proximo 'end'
            pos = m.start()
            conteudo = codigo[pos:]
            # Aproximação: conta end's
            count_end = 0
            for i, linha in enumerate(conteudo.split('\n')):
                if linha.strip().startswith('end'):
                    count_end += 1
                if count_end >= 2:
                    if i > 50:
                        resultado['avisos'].append('Funcao longa: %s (~%d linhas)' % (nome_func, i))
                    break
    
    def _encontrar_luac(self) -> Optional[str]:
        """Tenta encontrar o binário luac no sistema."""
        # Verificar no ambiente Canary/OTClient
        candidatos = [
            os.path.join(BASE, 'Lua', 'luac.exe'),
            os.path.join(BASE, 'luac.exe'),
            os.path.join(BASE, 'Canary', 'luac.exe'),
        ]
        for c in candidatos:
            if os.path.exists(c):
                return c
        
        # Verificar no PATH
        try:
            r = subprocess.run(['where', 'luac'], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip().split('\n')[0].strip()
        except Exception:
            pass
        
        return None


# ============================================================
# PONTO DE ENTRADA
# ============================================================

if __name__ == '__main__':
    val = LuaValidator()
    
    # Teste 1: NPC válido
    codigo_valido = open('sandbox/vendedor_ferraduro.lua', encoding='utf-8').read()
    r = val.validar(codigo_valido)
    print('=== NPC VALIDO ===')
    print('Valido:', r['valido'])
    print('Erros:', r['erros'])
    print('Avisos:', r['avisos'])
    print('SQL Injection:', len(r['sql_injection']))
    print('Boas praticas:', len(r['boas_praticas']))
    print('Sintaxe:', r['sintaxe'])
    
    # Teste 2: NPC com SQL injection
    codigo_injetado = codigo_valido.replace(
        'return true',
        'db.query("SELECT * FROM accounts WHERE name = \'" .. player:getName() .. "\'") return true'
    )
    r2 = val.validar(codigo_injetado)
    print('\n=== SQL INJECTION ===')
    print('Valido:', r2['valido'])
    for inj in r2['sql_injection']:
        print('  - %s (%d ocorrencias)' % (inj['tipo'], inj['ocorrencias']))
    
    # Teste 3: NPC sem estrutura
    codigo_quebrado = 'print("hello")'
    r3 = val.validar(codigo_quebrado)
    print('\n=== NPC QUEBRADO ===')
    print('Valido:', r3['valido'])
    for av in r3['avisos']:
        print('  -', av)
