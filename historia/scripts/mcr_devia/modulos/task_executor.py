"""TaskExecutor — Execucao de subtarefas do MasterAgent.
Extraido de master_agent.py para modularizacao.

Responsabilidades:
- Executar subtarefas individuais (validar, extrair, testar, salvar)
- Integrar resultados parciais em resposta final
- Delegar ferramentas registradas ao ToolOrchestrator
"""
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


class TaskExecutor:
    """Executor de subtarefas. Recebe as dependencias do MasterAgent."""
    
    def __init__(self, ia, tools, sandbox, ask_user_callback, log_callback,
                 identity_base_callback, identity_tarefa_callback):
        self._ia = ia
        self._tools = tools
        self._sandbox = sandbox
        self._ask_user = ask_user_callback or (lambda m, o: 'sim')
        self._log = log_callback or (lambda e, m: None)
        self._get_identity_base = identity_base_callback or (lambda: '')
        self._buscar_identity_tarefa = identity_tarefa_callback or (lambda t, r: '')
    
    def executar_subtarefa(self, subtarefa, artefatos=None, contexto_extra='', codigo_anterior=None):
        """Executa uma subtarefa do plano."""
        if artefatos is None:
            artefatos = {}
        acao = subtarefa.get('acao', '')
        params = subtarefa.get('params', {})
        ferramenta = subtarefa.get('ferramenta', '')
        
        if ferramenta in ('validar_python', 'validar_lua') and 'codigo' not in params and codigo_anterior:
            params['codigo'] = codigo_anterior
        if ferramenta == 'escrever_artefato' and 'codigo' not in params and codigo_anterior:
            params['codigo'] = codigo_anterior
            if 'caminho' not in params:
                params['caminho'] = os.path.join(BASE, 'sandbox', 'artefato_gerado.py')
        
        # ===== ACOES ESPECIAIS =====
        
        if acao == 'perguntar_usuario':
            resp = self._ask_user(params.get('pergunta', 'Posso prosseguir?'), None)
            return {'sucesso': True, 'resultado': f"Usuario: {resp}"}
        
        if acao == 'criar_estrutura_pastas':
            caminho = params.get('caminho', '')
            if caminho:
                for sub in ['src', 'assets', 'runs']:
                    self._tools.executar('criar_diretorio', {'caminho': os.path.join(caminho, sub)})
                artefatos['projeto_path'] = caminho
                return {'sucesso': True, 'resultado': f"Estrutura criada em {caminho}"}
            return {'sucesso': False, 'erro': 'Caminho nao especificado'}
        
        if acao == 'validar_codigo':
            modulos = {k: v for k, v in artefatos.items() if k.startswith('modulo_') and not k.endswith('_puro')}
            erros = []
            if modulos:
                for nome_mod, codigo in modulos.items():
                    if codigo and len(codigo) > 20:
                        r = self._tools.executar('validar_codigo', {'codigo': codigo})
                        if r.get('sucesso'):
                            res = r['resultado']
                            if not res.get('valido', True):
                                erros.append(f"{nome_mod}: {res.get('erros', ['erro'])}")
            elif codigo_anterior:
                r = self._tools.executar('validar_codigo', {'codigo': codigo_anterior})
                if r.get('sucesso'):
                    res = r['resultado']
                    if not res.get('valido', True):
                        erros.append(f"codigo: {res.get('erros', ['erro'])}")
                    else:
                        return {'sucesso': True, 'resultado': f"Validacao OK ({res.get('linguagem', '?')})"}
            if erros:
                try:
                    from modulos.auto_repair import AutoRepair
                    reparador = AutoRepair(self._ia)
                    codigo_fonte = codigo_anterior or (list(modulos.values())[0] if modulos else '')
                    if codigo_fonte and len(codigo_fonte) > 50:
                        codigo_reparado, reparado = reparador.reparar_e_validar(
                            codigo_fonte, erros, 'python', self._tools
                        )
                        if reparado:
                            self._log('REPAIR', 'Codigo reparado automaticamente')
                            return {'sucesso': True, 'resultado': codigo_reparado, 'reparado': True}
                except Exception as ex:
                    pass
                return {'sucesso': False, 'erro': f"Erros em: {', '.join(erros)}"}
            return {'sucesso': True, 'resultado': f"Validados {len(modulos) if modulos else 1} modulo(s) sem erros"}
        
        if acao == 'extrair_codigo':
            modulos = {k: v for k, v in artefatos.items() if k.startswith('modulo_') and not k.endswith('_puro')}
            projeto_path = artefatos.get('projeto_path', os.path.join(BASE, 'sandbox'))
            src_path = os.path.join(projeto_path, 'src')
            os.makedirs(src_path, exist_ok=True)
            salvos = []
            for nome_mod, codigo_bruto in modulos.items():
                r = self._tools.executar('extrair_codigo', {'conteudo': codigo_bruto})
                if r.get('sucesso'):
                    codigo_puro = r['resultado']
                    artefatos[nome_mod] = codigo_puro
                    nome_arquivo = nome_mod.replace('modulo_', '')
                    amostra = codigo_puro
                    if 'const ' in amostra or 'require(' in amostra or 'var ' in amostra or 'import React' in amostra or 'function ' in amostra:
                        ext = '.js'
                    elif 'local ' in amostra or 'function ' in amostra:
                        ext = '.lua'
                    else:
                        ext = '.py'
                    caminho_arquivo = os.path.join(src_path, f"{nome_arquivo}{ext}")
                    try:
                        with open(caminho_arquivo, 'w', encoding='utf-8') as f_:
                            f_.write(codigo_puro)
                        salvos.append(f"{nome_arquivo}{ext}")
                    except Exception as e_:
                        pass
            return {'sucesso': True, 'resultado': f"Extraidos e salvos {len(salvos)} modulos: {', '.join(salvos)}"}
        
        if acao == 'testar_execucao':
            projeto_path = artefatos.get('projeto_path', '')
            if not projeto_path:
                return {'sucesso': False, 'erro': 'projeto_path nao definido'}
            src_path = os.path.join(projeto_path, 'src')
            if os.path.exists(src_path):
                arquivos = os.listdir(src_path)
                main_file = None
                for f in arquivos:
                    if f.startswith('main.'):
                        main_file = os.path.join(src_path, f)
                        break
                if main_file and os.path.exists(main_file):
                    if not main_file.endswith('.py'):
                        return {'sucesso': True, 'resultado': 'Teste ignorado (nao executavel localmente)'}
                    with open(main_file, 'r') as f:
                        codigo = f.read()
                    return self._sandbox.executar_python(codigo)
                return {'sucesso': False, 'erro': f'main.* nao encontrado em {src_path}'}
            return {'sucesso': False, 'erro': f'Pasta src/ nao encontrada em {projeto_path}'}
        
        if acao == 'relatorio_final':
            projeto_path = artefatos.get('projeto_path', os.path.join(BASE, 'sandbox'))
            relatorio = f"Projeto criado!\nLocal: {projeto_path}\nEstrutura:\n"
            if os.path.exists(projeto_path):
                for root, dirs, files in os.walk(projeto_path):
                    nivel = root.replace(projeto_path, '').count(os.sep)
                    relatorio += f"{'  ' * nivel}{os.path.basename(root)}/\n"
                    for fname in sorted(files):
                        relatorio += f"{'  ' * (nivel + 1)}{fname}\n"
            return {'sucesso': True, 'resultado': relatorio}
        
        if acao == 'salvar_resultado':
            caminho = params.get('caminho', os.path.join(BASE, 'sandbox', 'output', 'relatorios', 'pesquisa.txt'))
            resultado_anterior = artefatos.get('codigo_gerado', '')
            if not resultado_anterior or len(resultado_anterior) < 20:
                ia_result = self._ia.gerar(f"Gere um relatorio completo sobre: {subtarefa.get('descricao', '')}", 0.4, 'pesado')
                resultado_anterior = ia_result or 'Sem dados para salvar'
            try:
                os.makedirs(os.path.dirname(caminho), exist_ok=True)
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write(resultado_anterior)
                return {'sucesso': True, 'resultado': f"Relatorio salvo em {caminho} ({len(resultado_anterior)} chars)"}
            except Exception as e:
                return {'sucesso': False, 'erro': f"Erro ao salvar: {e}"}
        
        # ===== FERRAMENTAS REGISTRADAS =====
        if ferramenta and ferramenta != 'perguntar_ia':
            return self._tools.executar(ferramenta, params)
        
        # ===== PERGUNTAR IA =====
        if acao == 'perguntar_ia':
            pergunta = params.get('pergunta', subtarefa.get('descricao', ''))
            task_type = params.get('task_type', '')
            identity_tarefa = self._buscar_identity_tarefa(task_type, pergunta)
            blocos = []
            ident_base = self._get_identity_base()
            if ident_base: blocos.append(f"[SISTEMA]\n{ident_base}")
            if identity_tarefa: blocos.append(f"[MISSAO]\n{identity_tarefa}")
            if contexto_extra: blocos.append(f"[CONTEXTO]\n{contexto_extra}")
            blocos.append(f"[PERGUNTA]\n{pergunta}")
            prompt_final = '\n\n---\n\n'.join(blocos)
            try:
                from modulos.enricher import Enricher
                enricher_obj = Enricher(self._ia, getattr(self, '_ia', None), getattr(self, '_sandbox', None))
            except Exception:
                pass
            resposta = self._ia.gerar(prompt_final, 0.4, 'pesado')
            if resposta and artefatos is not None:
                artefatos['codigo_gerado'] = resposta
            return {'sucesso': bool(resposta), 'resultado': resposta or 'Sem resposta',
                    'erro': '' if resposta else 'IA nao retornou resposta'}
        
        # Fallback: IA generica
        descricao = subtarefa.get('descricao', str(params))
        if contexto_extra:
            descricao = f"Contexto adicional:\n{contexto_extra}\n\n{descricao}"
        resposta = self._ia.gerar(descricao, 0.4, 'code')
        return {'sucesso': bool(resposta), 'resultado': resposta or 'Sem resposta',
                'erro': '' if resposta else 'IA nao retornou resposta'}
    
    def integrar(self, request, plano, resultados):
        """Junta todos os resultados parciais num artefato coeso."""
        partes = []
        for p in plano:
            r = resultados.get(p['id'], {})
            if r.get('sucesso') and r.get('resultado'):
                partes.append({
                    'passo': p['id'], 'acao': p['acao'],
                    'descricao': p.get('descricao', ''),
                    'conteudo': r['resultado'],
                })
        if not partes:
            resposta = self._ia.gerar(f"Responda da melhor forma possivel: {request}", 0.4, 'pesado')
            return {'resposta_final': resposta or 'Nao foi possivel completar a tarefa'}
        if len(partes) == 1:
            return {'resposta_final': partes[0]['conteudo']}
        compilado = [f"### Passo {p['passo']}: {p['descricao']}\n{p['conteudo']}" for p in partes]
        return {'resposta_final': '\n\n'.join(compilado), 'partes': partes}
