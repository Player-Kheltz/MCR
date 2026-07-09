#!/usr/bin/env python3
"""mcr.sanity_validator_cs — Valida código C# contra APIs conhecidas.

Usa tree-sitter-c-sharp para extrair assinaturas estruturais.
MESMA interface do SanityValidator (Lua) para que o SignatureAnalyzer
opere sem adaptações — zero hardcode de domínio.
"""
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Set

from tree_sitter import Language, Parser
import tree_sitter_c_sharp

_CS_LANG = Language(tree_sitter_c_sharp.language())
_CS_PARSER = Parser(_CS_LANG)

_CS_APIS_CACHE: Set[str] = set()
_CS_CACHE_INICIALIZADO = False


class SanityValidatorCS:
    """Valida código C# contra APIs conhecidas.
    
    APIs descobertas dinamicamente de:
    1. Arquivos .cs do projeto — classes, métodos, propriedades, chamadas
    2. Namespaces e interfaces — tipos e contratos
    
    Zero APIs hardcoded. Tudo aprendido do ambiente.
    """

    def __init__(self):
        self.api_conhecidas: Set[str] = set()
        self.padroes: List[Dict] = []
        self._carregar()

    # ─── Mineração de APIs do C# ──────────────────────────

    @staticmethod
    def minerar_assinaturas(diretorio: Path) -> List[Dict]:
        """Extrai assinaturas de TODOS os arquivos .cs do diretório.
        
        Para cada arquivo, extrai:
        - classes: nome, tipos base, interfaces
        - methods: nome, tipo retorno, parâmetros
        - properties: nome, tipo
        - invocations: funções/métodos chamados
        - attributes: atributos declarativos
        - fields: campos declarados
        - namespaces: namespaces usados/declarados
        """
        entidades = []
        if not diretorio.exists():
            print(f'[SanityValidatorCS] Diretorio nao encontrado: {diretorio}')
            return entidades

        cs_files = sorted(diretorio.rglob('*.cs'))
        print(f'[SanityValidatorCS] Escaneando {len(cs_files)} arquivos .cs...')

        for fpath in cs_files:
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    codigo = f.read()
            except Exception:
                continue
            if not codigo or len(codigo) < 20:
                continue

            try:
                tree = _CS_PARSER.parse(bytes(codigo, 'utf-8'))
            except Exception:
                continue

            assinatura = SanityValidatorCS._extrair_assinatura(tree, fpath)
            if assinatura:
                entidades.append(assinatura)

        print(f'[SanityValidatorCS] {len(entidades)} entidades extraidas')
        return entidades

    @staticmethod
    def _extrair_assinatura(tree, fpath: Path) -> Optional[Dict]:
        """Extrai assinatura completa de uma AST C#."""
        root = tree.root_node
        
        # Coletores
        classes = []
        methods = []
        properties = []
        invocations = []
        attributes = []
        fields = []
        usings = []
        namespaces_decl = []
        interfaces = []
        structs = []
        events = []

        def _visitar(node, depth=0):
            if depth > 50:
                return

            # Usings
            if node.type == 'using_directive':
                for c in node.children:
                    if c.type in ('qualified_name', 'identifier'):
                        try:
                            usings.append(c.text.decode('utf-8').strip())
                        except:
                            pass

            # Namespace declaration
            if node.type == 'namespace_declaration':
                for c in node.children:
                    if c.type in ('qualified_name', 'identifier'):
                        try:
                            namespaces_decl.append(c.text.decode('utf-8').strip())
                        except:
                            pass

            # Class declaration
            if node.type == 'class_declaration':
                info = {'name': '', 'bases': [], 'modifiers': []}
                for c in node.children:
                    if c.type == 'identifier':
                        try:
                            info['name'] = c.text.decode('utf-8').strip()
                        except:
                            pass
                    elif c.type == 'modifier':
                        try:
                            info['modifiers'].append(c.text.decode('utf-8').strip())
                        except:
                            pass
                    elif c.type == 'base_list':
                        for bc in c.children:
                            if bc.type in ('identifier', 'generic_name', 'qualified_name'):
                                try:
                                    info['bases'].append(bc.text.decode('utf-8').strip())
                                except:
                                    pass
                if info['name']:
                    classes.append(info)

            # Interface declaration
            if node.type == 'interface_declaration':
                info = {'name': '', 'bases': [], 'modifiers': []}
                for c in node.children:
                    if c.type == 'identifier':
                        try:
                            info['name'] = c.text.decode('utf-8').strip()
                        except:
                            pass
                    elif c.type == 'modifier':
                        try:
                            info['modifiers'].append(c.text.decode('utf-8').strip())
                        except:
                            pass
                    elif c.type == 'base_list':
                        for bc in c.children:
                            if bc.type in ('identifier', 'generic_name'):
                                try:
                                    info['bases'].append(bc.text.decode('utf-8').strip())
                                except:
                                    pass
                if info['name']:
                    interfaces.append(info)

            # Struct declaration
            if node.type == 'struct_declaration':
                info = {'name': '', 'bases': [], 'modifiers': []}
                for c in node.children:
                    if c.type == 'identifier':
                        try:
                            info['name'] = c.text.decode('utf-8').strip()
                        except:
                            pass
                    elif c.type == 'modifier':
                        try:
                            info['modifiers'].append(c.text.decode('utf-8').strip())
                        except:
                            pass
                if info['name']:
                    structs.append(info)

            # Method declaration
            if node.type == 'method_declaration':
                info = {'name': '', 'return_type': '', 'params': [], 'modifiers': [],
                        'generic_params': []}
                for c in node.children:
                    if c.type == 'identifier':
                        try:
                            info['name'] = c.text.decode('utf-8').strip()
                        except:
                            pass
                    elif c.type == 'predefined_type':
                        try:
                            info['return_type'] = c.text.decode('utf-8').strip()
                        except:
                            pass
                    elif c.type == 'modifier':
                        try:
                            info['modifiers'].append(c.text.decode('utf-8').strip())
                        except:
                            pass
                    elif c.type == 'parameter_list':
                        for pc in c.children:
                            if pc.type == 'parameter':
                                param_info = SanityValidatorCS._extrair_parametro(pc)
                                if param_info:
                                    info['params'].append(param_info)
                    elif c.type == 'type_parameter_list':
                        for tc in c.children:
                            if tc.type == 'type_parameter':
                                try:
                                    info['generic_params'].append(tc.text.decode('utf-8').strip())
                                except:
                                    pass
                    elif c.type == 'generic_name':
                        try:
                            info['return_type'] = c.text.decode('utf-8').strip()
                        except:
                            pass
                if info['name']:
                    methods.append(info)

            # Constructor declaration
            if node.type == 'constructor_declaration':
                info = {'name': '', 'params': [], 'modifiers': []}
                for c in node.children:
                    if c.type == 'identifier':
                        try:
                            info['name'] = c.text.decode('utf-8').strip()
                        except:
                            pass
                    elif c.type == 'modifier':
                        try:
                            info['modifiers'].append(c.text.decode('utf-8').strip())
                        except:
                            pass
                    elif c.type == 'parameter_list':
                        for pc in c.children:
                            if pc.type == 'parameter':
                                param_info = SanityValidatorCS._extrair_parametro(pc)
                                if param_info:
                                    info['params'].append(param_info)
                if info['name']:
                    methods.append(info)

            # Property declaration
            if node.type == 'property_declaration':
                info = {'name': '', 'type': '', 'modifiers': []}
                for c in node.children:
                    if c.type == 'identifier':
                        try:
                            info['name'] = c.text.decode('utf-8').strip()
                        except:
                            pass
                    elif c.type in ('predefined_type', 'generic_name', 'nullable_type',
                                    'identifier'):
                        try:
                            info['type'] = c.text.decode('utf-8').strip()
                        except:
                            pass
                    elif c.type == 'modifier':
                        try:
                            info['modifiers'].append(c.text.decode('utf-8').strip())
                        except:
                            pass
                if info['name']:
                    properties.append(info)

            # Field declaration
            if node.type == 'field_declaration':
                info = {'name': '', 'type': '', 'modifiers': []}
                for c in node.children:
                    if c.type in ('predefined_type', 'generic_name', 'identifier',
                                  'nullable_type'):
                        try:
                            info['type'] = c.text.decode('utf-8').strip()
                        except:
                            pass
                    elif c.type == 'modifier':
                        try:
                            info['modifiers'].append(c.text.decode('utf-8').strip())
                        except:
                            pass
                    elif c.type == 'variable_declaration':
                        for vc in c.children:
                            if vc.type == 'variable_declarator':
                                for vdc in vc.children:
                                    if vdc.type == 'identifier':
                                        try:
                                            info['name'] = vdc.text.decode('utf-8').strip()
                                        except:
                                            pass
                if info['name']:
                    fields.append(info)

            # Event field declaration
            if node.type == 'event_field_declaration':
                info = {'name': '', 'type': '', 'modifiers': []}
                for c in node.children:
                    if c.type == 'modifier':
                        try:
                            info['modifiers'].append(c.text.decode('utf-8').strip())
                        except:
                            pass
                    elif c.type == 'variable_declaration':
                        for vc in c.children:
                            if vc.type == 'variable_declarator':
                                for vdc in vc.children:
                                    if vdc.type == 'identifier':
                                        try:
                                            info['name'] = vdc.text.decode('utf-8').strip()
                                        except:
                                            pass
                                    elif vdc.type == 'generic_name':
                                        try:
                                            info['type'] = vdc.text.decode('utf-8').strip()
                                        except:
                                            pass
                if info['name']:
                    events.append(info)

            # Invocation expression
            if node.type == 'invocation_expression':
                nome_chamada = SanityValidatorCS._extrair_nome_chamada(node)
                if nome_chamada:
                    invocations.append(nome_chamada)

            # Attribute
            if node.type == 'attribute':
                try:
                    attr_text = node.text.decode('utf-8').strip()
                    if attr_text:
                        attributes.append(attr_text)
                except:
                    pass

            # Object creation
            if node.type in ('object_creation_expression', 'implicit_object_creation_expression'):
                for c in node.children:
                    if c.type in ('identifier', 'generic_name', 'qualified_name'):
                        try:
                            invocations.append('new ' + c.text.decode('utf-8').strip())
                        except:
                            pass

            for child in node.children:
                _visitar(child, depth + 1)

        _visitar(root)

        if not classes and not methods and not properties:
            return None

        # Monta assinatura da entidade
        nome_arquivo = str(fpath)
        tipo = 'unknown'
        if classes:
            bases = [b for cls in classes for b in cls.get('bases', [])]
            if any('ViewModel' in b or 'ViewModelBase' in b for b in bases):
                tipo = 'viewmodel'
            elif any('INotifyPropertyChanged' in b for b in bases):
                tipo = 'notify'
            elif any('Service' in c['name'] for c in classes):
                tipo = 'service'
            elif any('Model' in c['name'] for c in classes):
                tipo = 'model'
            elif any(b.startswith('I') for b in bases):
                tipo = 'interface_impl'
            else:
                tipo = classes[0]['name'].lower().replace('view', '').replace('service', '') or 'class'

        # Coleta todas as strings de API para compatibilidade com SignatureAnalyzer
        api_calls = set(invocations)
        for m in methods:
            api_calls.add(f"method:{m['name']}")
            if m.get('return_type'):
                api_calls.add(f"type:{m['return_type']}")
            for p in m.get('params', []):
                if p.get('type'):
                    api_calls.add(f"type:{p['type']}")
        for p in properties:
            api_calls.add(f"prop:{p['name']}")
            if p['type']:
                api_calls.add(f"type:{p['type']}")
        for cls in classes:
            api_calls.add(f"class:{cls['name']}")
            for b in cls.get('bases', []):
                api_calls.add(f"base:{b}")
        for ns in namespaces_decl:
            api_calls.add(f"ns:{ns}")
        for u in usings:
            api_calls.add(f"using:{u}")
        for fld in fields:
            api_calls.add(f"field:{fld['name']}")
            if fld['type']:
                api_calls.add(f"type:{fld['type']}")
        for attr in attributes:
            api_calls.add(f"attr:{attr}")
        for evt in events:
            api_calls.add(f"event:{evt['name']}")

        return {
            'arquivo': nome_arquivo,
            'tipo': tipo,
            'api_calls': list(api_calls),
            'classes': classes,
            'methods': methods,
            'properties': properties,
            'invocations': invocations[:50],
            'attributes': attributes[:20],
            'fields': fields[:20],
            'namespaces': namespaces_decl,
            'usings': usings[:20],
            'interfaces': interfaces,
            'events': events[:10],
            'tamanho_linhas': len(open(fpath, 'r', encoding='utf-8', errors='replace').read().splitlines()) if fpath else 0,
        }

    @staticmethod
    def _extrair_parametro(node) -> Optional[Dict]:
        """Extrai nome e tipo de um parâmetro."""
        info = {}
        for c in node.children:
            if c.type in ('predefined_type', 'identifier', 'nullable_type',
                          'generic_name', 'qualified_name', 'array_type'):
                try:
                    info['type'] = c.text.decode('utf-8').strip()
                except:
                    pass
            elif c.type == 'identifier':
                try:
                    info['name'] = c.text.decode('utf-8').strip()
                except:
                    pass
        return info if info else None

    @staticmethod
    def _extrair_nome_chamada(node) -> Optional[str]:
        """De um invocation_expression, extrai o nome completo."""
        if node.type != 'invocation_expression':
            return None
        for child in node.children:
            if child.type in ('identifier', 'member_access_expression',
                              'member_binding_expression', 'generic_name',
                              'conditional_access_expression'):
                try:
                    return child.text.decode('utf-8', errors='replace').strip()
                except:
                    pass
        return None

    @staticmethod
    def _normalizar_api(nome: str) -> str:
        """Normaliza nome de API: remove generics, lowercase."""
        nome = nome.split('<')[0].strip()
        nome = nome.split('(')[0].strip()
        return nome.lower()

    def _carregar(self):
        """Inicializa o cache de APIs."""
        global _CS_APIS_CACHE, _CS_CACHE_INICIALIZADO
        if _CS_CACHE_INICIALIZADO:
            self.api_conhecidas = set(_CS_APIS_CACHE)
            return
        _CS_CACHE_INICIALIZADO = True
        self.api_conhecidas = set(_CS_APIS_CACHE)
        print(f'[SanityValidatorCS] Cache inicializado ({len(self.api_conhecidas)} APIs)')

    def extrair_chamadas(self, codigo: str) -> List[str]:
        """Extrai todas as chamadas de função de um código C# usando tree-sitter."""
        if not codigo or len(codigo) < 10:
            return []
        try:
            tree = _CS_PARSER.parse(bytes(codigo, 'utf-8'))
        except Exception:
            return []
        chamadas = []
        def _visitar(node):
            if node.type == 'invocation_expression':
                nome = self._extrair_nome_chamada(node)
                if nome:
                    chamadas.append(nome)
            for child in node.children:
                _visitar(child)
        _visitar(tree.root_node)
        return list(set(chamadas))

    def validar_codigo(self, codigo: str) -> Dict:
        """Valida uma string de código C# contra as APIs conhecidas."""
        chamadas = self.extrair_chamadas(codigo)
        if not chamadas:
            return {'valido': True, 'apis_conhecidas': [], 'apis_desconhecidas': [], 'total_chamadas': 0}
        conhecidas = []
        desconhecidas = []
        for ch in chamadas:
            ch_norm = self._normalizar_api(ch)
            if ch_norm in self.api_conhecidas:
                conhecidas.append(ch)
            else:
                desconhecidas.append(ch)
        return {
            'valido': len(desconhecidas) == 0,
            'apis_conhecidas': conhecidas,
            'apis_desconhecidas': desconhecidas,
            'total_chamadas': len(chamadas),
        }

    @staticmethod
    def resetar_cache():
        """Reseta o cache global de APIs."""
        global _CS_APIS_CACHE, _CS_CACHE_INICIALIZADO
        _CS_APIS_CACHE = set()
        _CS_CACHE_INICIALIZADO = False


if __name__ == '__main__':
    import sys
    sys.path.insert(0, r'E:\MCR')
    from pathlib import Path
    val = SanityValidatorCS()
    entidades = val.minerar_assinaturas(Path(r'E:\MCR\tools\grimorio'))
    print(f'\nTotal entidades: {len(entidades)}')
    # Mostra resumo
    tipos = {}
    for e in entidades:
        t = e.get('tipo', 'unknown')
        tipos[t] = tipos.get(t, 0) + 1
    print(f'Distribuicao de tipos: {tipos}')
    # Amostra 3 entidades
    for e in entidades[:3]:
        print(f'\n  --- {e["tipo"]}: {Path(e["arquivo"]).name} ---')
        print(f'    Classes: {[c["name"] for c in e.get("classes", [])]}')
        print(f'    Methods: {[m["name"] for m in e.get("methods", [])[:5]]}')
        print(f'    Properties: {[p["name"] for p in e.get("properties", [])[:5]]}')
        print(f'    Calls: {e.get("invocations", [])[:10]}')
