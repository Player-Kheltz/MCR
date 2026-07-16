"""code_parser.py — parse de .lua/.cpp/.cs usando tree-sitter."""
import os, sys
from tree_sitter_lua import language as lua_lang
from tree_sitter_cpp import language as cpp_lang
from tree_sitter_c_sharp import language as cs_lang

try:
    from tree_sitter import Parser, Language
    _HAS_TS = True
except Exception:
    _HAS_TS = False
    Parser = Language = None

# ─── Inicializacao ──────────────────────────────────────────────

class CodeParser:
    """Parser de codigo usando tree-sitter. Entende estrutura, nao so texto."""
    
    def __init__(self):
        self.parsers = {}
        if not _HAS_TS:
            return
        
        linguagens = {
            '.lua': 'lua', '.cpp': 'cpp', '.hpp': 'cpp', '.h': 'cpp',
            '.cs': 'c_sharp',
        }
        lang_funcs = {
            'lua': lua_lang(),
            'cpp': cpp_lang(),
            'c_sharp': cs_lang(),
        }
        
        for ext, nome in linguagens.items():
            try:
                lang = Language(lang_funcs.get(nome, lua_lang()))
                p = Parser(lang)
                self.parsers[ext] = p
            except Exception as e:
                print(f"[Parser] Erro {ext}: {e}")
    
    def parse(self, caminho):
        """Parseia arquivo e retorna estrutura."""
        if not _HAS_TS:
            return self._fallback(caminho)
        
        _, ext = os.path.splitext(caminho)
        if ext.lower() not in self.parsers:
            return self._fallback(caminho)
        
        try:
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                codigo = f.read()
        except Exception:
            return self._fallback(caminho)
        
        parser = self.parsers[ext.lower()]
        tree = parser.parse(bytes(codigo, 'utf-8'))
        root = tree.root_node
        
        # Extrai estrutura basica
        estrutura = {
            'arquivo': caminho,
            'tamanho': len(codigo),
            'linguagem': ext,
            'funcoes': [],
            'classes': [],
            'chamadas': [],
        }
        
        self._extrair_no(root, estrutura, codigo)
        return estrutura
    
    def _extrair_no(self, no, estrutura, codigo):
        """Extrai informacao recursivamente da AST."""
        tipo = no.type
        texto = codigo[no.start_byte:no.end_byte] if codigo else ""
        
        if tipo in ('function_definition', 'function_declaration'):
            nome = self._extrair_nome(no, codigo)
            estrutura['funcoes'].append({
                'nome': nome or '?',
                'inicio': no.start_point[0] + 1,
                'fim': no.end_point[0] + 1,
                'linhas': no.end_point[0] - no.start_point[0] + 1,
            })
        
        elif tipo in ('class_specifier', 'class_declaration', 'record_declaration'):
            nome = self._extrair_nome(no, codigo)
            estrutura['classes'].append({
                'nome': nome or '?',
                'inicio': no.start_point[0] + 1,
            })
        
        elif tipo in ('call_expression', 'function_call'):
            nome = self._extrair_nome(no, codigo)
            if nome and len(nome) < 50:
                estrutura['chamadas'].append({
                    'funcao': nome,
                    'linha': no.start_point[0] + 1,
                })
        
        for filho in no.children:
            self._extrair_no(filho, estrutura, codigo)
    
    def _extrair_nome(self, no, codigo):
        """Tenta extrair o nome de um noh da AST."""
        for filho in no.children:
            if filho.type in ('name', 'identifier', 'field_identifier', 
                             'method_name', 'function_name', 'type_identifier'):
                return codigo[filho.start_byte:filho.end_byte]
        return None
    
    def _fallback(self, caminho):
        """Fallback simples quando tree-sitter nao disponivel."""
        try:
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                linhas = f.readlines()
        except Exception:
            return {'arquivo': caminho, 'erro': 'nao foi possivel ler'}
        
        return {
            'arquivo': caminho,
            'tamanho': sum(len(l) for l in linhas),
            'linguagem': os.path.splitext(caminho)[1],
            'funcoes': [],
            'classes': [],
            'chamadas': [],
            'fallback': True,
        }

# ─── Instancia global ───────────────────────────────────────────
_parser = None

def get_parser():
    global _parser
    if _parser is None:
        _parser = CodeParser()
    return _parser
