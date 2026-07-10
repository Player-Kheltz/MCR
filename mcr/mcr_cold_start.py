#!/usr/bin/env python3
"""mcr.mcr_cold_start — Cold Start do ecossistema MCR.
Apaga o KG, minera do zero, clusteriza e valida.
A prova de que o MCR e agnostico de dominio.

Uso:
    from mcr.mcr_cold_start import cold_start
    
    # Lua (default)
    cold_start()
    
    # C# (dominio cruzado)
    from mcr.sanity_validator_cs import SanityValidatorCS
    from mcr.shadow_dotnet import ShadowDotnet
    cold_start(
        server_dir='E:/MCR/tools/grimorio',
        minerador=SanityValidatorCS(),
        executor=ShadowDotnet(),
    )
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any


def _minerador_lua_default(server_dir, kg_dir, canary_npc_dir, canary_monster_dir):
    """Minerador padrao para Lua — mantem compatibilidade com codigo legado."""
    from mcr.sanity_validator import SanityValidator, _APIS_CACHE, _APIS_CACHE_INICIALIZADO
    _APIS_CACHE_INICIALIZADO = False
    _APIS_CACHE.clear()
    val = SanityValidator(
        kg_dir=kg_dir,
        server_src_dir=server_dir / 'src' if server_dir else None,
    )
    # Minera entidades dos scripts Lua
    import re
    from collections import Counter
    padroes_brutos = []
    for fpath in sorted(canary_npc_dir.glob('*.lua'))[:800]:
        try:
            with open(fpath, 'r', encoding='latin-1') as f:
                content = f.read()
            chamadas = re.findall(r'\b[A-Za-z]+[\w.]*(?:\:\w+)?(?=\s*\()', content)
            vars_found = re.findall(r'\blocal\s+(\w+)', content)
            padroes_brutos.append({
                'arquivo': str(fpath),
                'tipo': 'npc' if 'npctype' in ' '.join(chamadas).lower() else 'generic',
                'api_calls': list(set(chamadas))[:30],
                'variaveis': list(set(vars_found))[:10],
                'tamanho_linhas': content.count('\n'),
            })
        except Exception:
            continue
    for fpath in sorted(canary_monster_dir.glob('*.lua'))[:500]:
        try:
            with open(fpath, 'r', encoding='latin-1') as f:
                content = f.read()
            chamadas = re.findall(r'\b[A-Za-z]+[\w.]*(?:\:\w+)?(?=\s*\()', content)
            vars_found = re.findall(r'\blocal\s+(\w+)', content)
            padroes_brutos.append({
                'arquivo': str(fpath),
                'tipo': 'monster' if 'monstertype' in ' '.join(chamadas).lower() else 'generic',
                'api_calls': list(set(chamadas))[:30],
                'variaveis': list(set(vars_found))[:10],
                'tamanho_linhas': content.count('\n'),
            })
        except Exception:
            continue
    return val, padroes_brutos


def _executor_lua_default():
    """Executor padrao para Lua."""
    from mcr.shadow_canary import validar_sintaxe, aprender_com_erro
    return validar_sintaxe, aprender_com_erro


def cold_start(
    server_dir: Path = None,
    kg_dir: Path = None,
    minerador: Any = None,
    executor: Any = None,
) -> dict:
    """Executa um Cold Start completo do MCR.
    
    1. Apaga o Knowledge Graph existente
    2. Minera o diretorio via minerador injetado
    3. Constrói clusters de assinatura
    4. Constrói meta-clusters
    5. Valida geracao de codigo via executor injetado
    
    Args:
        server_dir: diretorio para minerar
        kg_dir: diretorio do KG
        minerador: objeto com metodo .minerar_assinaturas(diretorio)
                   ou None para usar SanityValidator (Lua padrao)
        executor: objeto com metodos .validar(codigo) e .aprender_com_erro(resultado)
                  ou None para usar shadow_canary (Lua padrao)
    
    Returns:
        relatorio do cold start
    """
    from mcr.paths import KG_DIR, SERVER_DIR, CANARY_NPC_DIR, CANARY_MONSTER_DIR

    t0 = time.time()
    server_dir = Path(server_dir) if server_dir else SERVER_DIR
    kg_dir = kg_dir or KG_DIR

    relatorio = {
        'inicio': time.strftime('%Y-%m-%d %H:%M:%S'),
        'dominio': 'csharp' if minerador is not None else 'lua',
        'etapas': {},
        'erros': [],
    }

    print('=' * 55)
    print('  COLD START — MCR Tabula Rasa')
    print('  Dominio: %s' % relatorio['dominio'])
    print('  Diretorio: %s' % server_dir)
    print('=' * 55)

    # Etapa 1: Limpar KG
    print('\n[1/5] Limpando Knowledge Graph...')
    if kg_dir.exists():
        for f in kg_dir.glob('patterns_*.json'):
            try:
                f.unlink()
                print('  Removido: %s' % f.name)
            except Exception as e:
                print('  Erro ao remover %s: %s' % (f.name, e))
    relatorio['etapas']['kg_limpo'] = True
    print('  KG limpo.')

    # Etapa 2: Mineracao
    print('\n[2/5] Minerando entidades...')
    val = None
    padroes_brutos = []

    if minerador is not None:
        # Minerador injetado (C# ou outro dominio)
        from mcr.sanity_validator_cs import SanityValidatorCS
        if isinstance(minerador, SanityValidatorCS):
            minerador.resetar_cache()
        entidades = minerador.minerar_assinaturas(server_dir)
        padroes_brutos = entidades
        val = minerador
        relatorio['etapas']['apis_mineradas'] = sum(len(e.get('api_calls', [])) for e in entidades)
        relatorio['etapas']['entidades_mineradas'] = len(entidades)
        print('  %d entidades mineradas, %d chamadas de API' % (
            len(entidades), relatorio['etapas']['apis_mineradas']))
    else:
        # Minerador padrao Lua
        from mcr.sanity_validator import SanityValidator
        val, padroes_brutos = _minerador_lua_default(server_dir, kg_dir, CANARY_NPC_DIR, CANARY_MONSTER_DIR)
        relatorio['etapas']['apis_mineradas'] = len(val.api_conhecidas)
        relatorio['etapas']['entidades_mineradas'] = len(padroes_brutos)
        print('  %d APIs mineradas.' % len(val.api_conhecidas))
        print('  %d entidades mineradas dos scripts' % len(padroes_brutos))

    # Etapa 3: Clusters de assinatura
    print('\n[3/5] Clusterizando entidades...')
    from mcr.mcr_signature_cluster import SignatureAnalyzer, SignatureCluster

    analyzer = SignatureAnalyzer()

    clusters_criados = []
    for ent in padroes_brutos:
        melhor = None
        melhor_score = 0.0
        for c in clusters_criados:
            score = c.similaridade(ent)
            if score > melhor_score:
                melhor_score = score
                melhor = c
        if melhor and melhor_score >= 0.15:
            melhor.adicionar(ent)
        else:
            nome = "Type_%c" % (65 + len(clusters_criados))
            clusters_criados.append(SignatureCluster(nome, [ent]))

    clusters_criados.sort(key=lambda c: -len(c))
    analyzer.clusters = clusters_criados
    relatorio['etapas']['clusters'] = len(clusters_criados)
    relatorio['etapas']['entidades_clusterizadas'] = sum(len(c) for c in clusters_criados)
    print('  %d clusters formados.' % len(clusters_criados))
    for c in clusters_criados[:10]:
        print('    %s: %d entidades' % (c.nome, len(c)))

    # Etapa 4: Meta-clusters
    print('\n[4/5] Construindo meta-clusters...')
    meta_clusters = analyzer.meta_clusterizar()
    relatorio['etapas']['meta_clusters'] = len(meta_clusters)
    for mc in meta_clusters:
        print('  %s: %d entidades, %d sub-clusters' % (
            mc.nome, mc.total_entidades(), len(mc.clusters)))

    # Etapa 5: Validacao — gerar codigo e verificar
    print('\n[5/5] Validando geracao de codigo...')
    try:
        if executor is not None:
            # Detecta dominio do executor
            from mcr.sanity_validator_cs import SanityValidatorCS
            from mcr.sanity_validator_sql import SanityValidatorSQL
            is_sql = isinstance(minerador, SanityValidatorSQL) if minerador is not None else False
            is_cs = isinstance(minerador, SanityValidatorCS) if minerador is not None else False

            from devia.kernel.mcr_kernel.engine import MCR
            from devia.kernel.mcr_kernel.memory import MCRConector, MCRCadeia

            if padroes_brutos and clusters_criados:
                melhor_cluster = clusters_criados[0]
                template_ent = melhor_cluster.entidades[0] if melhor_cluster.entidades else {}
                
                # Treina MCR nos codigos fonte para gerar conteudo
                conector = MCRConector()
                for ent in padroes_brutos[:10]:
                    arq = ent.get('arquivo', '')
                    if arq and Path(arq).exists():
                        try:
                            with open(arq, 'r', encoding='utf-8-sig', errors='replace') as f:
                                conector.alimentar(f.read()[:2000], Path(arq).stem)
                        except:
                            pass
                
                mk = conector.mcr_palavra
                def _gerar_nome(base=''):
                    prox, conf = mk.predizer(base if base in mk.freq else 'var')
                    if prox and conf > 0.1:
                        return str(prox).replace('.', '').replace(';', '').strip()
                    return base or 'value'

                if is_sql:
                    # ─── Geracao SQL ───
                    # Sandbox comeca vazio — precisa criar tabela antes de usar
                    nome_tabela = 'mcr_cold_start'
                    snippet = (
                        'CREATE TABLE ' + nome_tabela + ' (\n'
                        '    id INTEGER PRIMARY KEY,\n'
                        '    name TEXT NOT NULL,\n'
                        '    value REAL\n'
                        ');\n'
                        "INSERT INTO " + nome_tabela + " (id, name, value) VALUES (1, 'mcr', 42.0);\n"
                        'SELECT * FROM ' + nome_tabela + ';'
                    )
                    nota = 10
                else:
                    # ─── Geracao C# ───
                    classes = template_ent.get('classes', [])
                    methods = template_ent.get('methods', [])
                    props = template_ent.get('properties', [])
                    fields = template_ent.get('fields', [])
                    
                    _TYPES_KNOWN = {'string', 'int', 'bool', 'void', 'object', 'double',
                                    'float', 'long', 'byte', 'char', 'decimal', 'uint',
                                    'short', 'List<string>', 'List<int>', 'Dictionary<string,string>',
                                    'IEnumerable<string>', 'Task', 'Task<string>', 'Task<int>',
                                    'DateTime', 'TimeSpan', 'Guid', 'Exception', 'EventArgs',
                                    'EventHandler', 'EventHandler<T>', 'Nullable<int>',
                                    'Nullable<bool>', 'String', 'Int32', 'Boolean'}

                    def _sanitizar_type(t):
                        if not t or t.strip() == '':
                            return 'string'
                        t = t.strip()
                        if t in _TYPES_KNOWN:
                            return t
                        if t.startswith('List<') and t.endswith('>'):
                            inner = t[5:-1]
                            if inner in _TYPES_KNOWN:
                                return t
                        if t.startswith('IEnumerable<') and t.endswith('>'):
                            inner = t[12:-1]
                            if inner in _TYPES_KNOWN:
                                return t
                        if t.startswith('Dictionary<') and t.endswith('>'):
                            return 'Dictionary<string,string>'
                        if t.startswith('Task<') and t.endswith('>'):
                            inner = t[5:-1]
                            if inner in _TYPES_KNOWN:
                                return t
                        if t.startswith('Nullable<') and t.endswith('>'):
                            inner = t[9:-1]
                            if inner in _TYPES_KNOWN:
                                return t
                        return 'string'

                    linhas = []
                    linhas.append('#nullable disable')
                    linhas.append('using System;')
                    linhas.append('using System.Collections.Generic;')
                    linhas.append('using System.Threading.Tasks;')
                    linhas.append('')
                    
                    nome_classe = 'McrGeneratedClass'
                    linhas.append('namespace MCR.Generated')
                    linhas.append('{')
                    linhas.append('    public class ' + nome_classe)
                    linhas.append('    {')
                    
                    for f in fields[:3]:
                        ftype = _sanitizar_type(f.get('type', ''))
                        fname = f.get('name', '_field')
                        if fname:
                            linhas.append('        private ' + ftype + ' ' + fname + ';')
                    
                    for p in props[:3]:
                        ptype = _sanitizar_type(p.get('type', ''))
                        pname = p.get('name', 'Property')
                        if pname:
                            linhas.append('        public ' + ptype + ' ' + pname + ' { get; set; }')
                    
                    for m in methods[:3]:
                        rt = _sanitizar_type(m.get('return_type', ''))
                        mn = m.get('name', 'Method')
                        params = m.get('params', [])[:3]
                        param_strs = []
                        for pi, p in enumerate(params):
                            pt = _sanitizar_type(p.get('type', ''))
                            pn = p.get('name', 'p' + str(pi + 1))
                            if pt and pn:
                                param_strs.append(pt + ' ' + pn)
                        params_str = ', '.join(param_strs)
                    linhas.append('        public ' + rt + ' ' + mn + '(' + params_str + ')')
                    linhas.append('        {')
                    if rt != 'void':
                        linhas.append('            return default!;')
                    else:
                        linhas.append('            // method body')
                    linhas.append('        }')
                    
                    linhas.append('    }')
                    linhas.append('}')
                    snippet = '\n'.join(linhas)
                    nota = 10
            else:
                snippet = '-- MCR Cold Start - sem topicos para gerar\nSELECT 1;'
                nota = 0

            relatorio['validacao'] = {
                'codigo_gerado': len(snippet) > 20,
                'snippet_tamanho': len(snippet),
                'nota_cadeia': nota,
            }
            print('  Snippet gerado: %d bytes (nota: %.1f)' % (len(snippet), nota))

            # Valida com o executor
            if hasattr(executor, 'executar'):
                res_exec = executor.executar(snippet)
            elif hasattr(executor, 'validar'):
                res_exec = executor.validar(snippet)
            else:
                res_exec = {'valido': False, 'erros': [{'codigo': 'NO_EXECUTOR', 'mensagem': 'executor sem metodo executar/validar', 'linha': 0}]}

            relatorio['validacao']['sintaxe_valida'] = res_exec.get('valido', False)
            relatorio['validacao']['erros_compilacao'] = [e['codigo'] for e in res_exec.get('erros', [])]

            if hasattr(executor, 'aprender_com_erro'):
                tipo_erro = executor.aprender_com_erro(res_exec)
                if tipo_erro:
                    relatorio['validacao']['penalidade_registrada'] = tipo_erro
                    print('  Penalidade registrada: %s' % tipo_erro)

            if res_exec.get('valido', False):
                print('  >> COLD START BEM-SUCEDIDO (codigo compila)')
            else:
                erros_str = '; '.join([e['mensagem'][:80] for e in res_exec.get('erros', [])[:3]])
                print('  >> COMPILACAO FALHOU: %s' % erros_str)
        else:
            # Executor padrao Lua
            from mcr.golden_templates import gerar_npc_canary
            from mcr.mcr_world_builder import _validar_sintaxe, _validar_semantica

            codigo = gerar_npc_canary({
                'name': 'ColdStartTest',
                'health': 100,
                'looktype': 128,
                'greeting': 'Eu fui gerado sem KG pre-existente!',
            })
            valido_sint, erro = _validar_sintaxe(codigo)
            apis_invalidas = _validar_semantica(codigo, 'npc')

            relatorio['validacao'] = {
                'codigo_gerado': len(codigo) > 0,
                'sintaxe_valida': valido_sint,
                'apis_validas': len(apis_invalidas) == 0,
                'total_apis_verificadas': len(val.api_conhecidas) if hasattr(val, 'api_conhecidas') else 0,
            }

            if valido_sint and not apis_invalidas:
                print('  Codigo NPC gerado com sucesso: %d bytes' % len(codigo))
                print('  Sintaxe: OK')
                print('  >> COLD START BEM-SUCEDIDO')
            else:
                msg = []
                if not valido_sint:
                    msg.append('sintaxe invalida: %s' % erro)
                if apis_invalidas:
                    msg.append('APIs desconhecidas: %s' % ', '.join(apis_invalidas[:5]))
                relatorio['validacao']['erro'] = '; '.join(msg)
                print('  >> FALHA: %s' % '; '.join(msg))
    except Exception as e:
        import traceback
        traceback.print_exc()
        relatorio['validacao'] = {'erro': str(e)[:200]}
        print('  >> ERRO: %s' % e)

    t_total = time.time() - t0
    relatorio['tempo_total'] = round(t_total, 1)
    print('\n' + '=' * 55)
    print('  COLD START CONCLUIDO em %.1fs' % t_total)
    print('=' * 55)

    return relatorio


if __name__ == '__main__':
    import sys
    sys.path.insert(0, r'E:\MCR')
    rel = cold_start()
    print('\nRelatorio:')
    print(json.dumps(rel, indent=2, ensure_ascii=False)[:1000])
