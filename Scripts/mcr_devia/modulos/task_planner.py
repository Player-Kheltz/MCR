"""TaskPlanner — Decompoe requests complexos em subtarefas executaveis.

Entrada: "Cria um jogo de plataforma em Python com 3 fases"
Saida: [
    {'id': 1, 'acao': 'criar_estrutura', 'params': {...}, 'depende_de': []},
    {'id': 2, 'acao': 'criar_fase1', 'params': {...}, 'depende_de': [1]},
    {'id': 3, 'acao': 'criar_fase2', 'params': {...}, 'depende_de': [1]},
    ...
]

Cada subtarefa e executavel pelo ToolOrchestrator ou por IA direta.
Inclui PlanValidator para verificar sanidade do plano ANTES de executar.
"""
import json, os, re
from typing import List, Dict, Optional

# Paths
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')


# Cache de tech stack para evitar chamadas repetidas ao LLM
_tech_stack_cache = {}


# Templates de plano para tarefas comuns (evita chamar LLM)
PLANOS_CONHECIDOS = {
    'npc_shop': [
        {'acao': 'buscar_exemplos', 'desc': 'Busca NPCs similares no CanaryIndexer'},
        {'acao': 'buscar_licoes', 'desc': 'Busca licoes no KG sobre NPCs'},
        {'acao': 'gerar_npc', 'desc': 'Gera o NPC com NPCGenerator'},
        {'acao': 'validar_npc', 'desc': 'Valida com LuaValidator'},
        {'acao': 'registrar_licao', 'desc': 'Aprende licao no KG'},
    ],
    'pergunta_simples': [
        {'acao': 'buscar_contexto', 'desc': 'Busca contexto no ContextCrew'},
        {'acao': 'perguntar_ia', 'desc': 'Pergunta a IA com contexto'},
    ],
    'criar_codigo': [
        {'acao': 'buscar_exemplos_similares', 'desc': 'Busca exemplos no codigo/context_crew'},
        {'acao': 'gerar_codigo', 'desc': 'Gera codigo via IA'},
        {'acao': 'validar_codigo', 'desc': 'Valida sintaxe'},
        {'acao': 'salvar_arquivo', 'desc': 'Salva em arquivo'},
    ],
    'analisar_codigo': [
        {'acao': 'analisar_codigo', 'desc': 'Analisa codigo com IA'},
        {'acao': 'registrar_licao', 'desc': 'Registra licoes aprendidas'},
    ],
    'projeto_jogo': [
        {'acao': 'perguntar_usuario', 'desc': 'Pergunta preferencias (engine, nome do projeto)'},
        {'acao': 'buscar_exemplos_similares', 'desc': 'Busca exemplos similares na memoria'},
        {'acao': 'criar_estrutura_pastas', 'desc': 'Cria pastas src/, assets/, runs/'},
        {'acao': 'gerar_modulo_main', 'desc': 'Gera main.py com loop principal e init'},
        {'acao': 'gerar_modulo_entidades', 'desc': 'Gera entities.py (jogador, inimigos)'},
        {'acao': 'gerar_modulo_fases', 'desc': 'Gera phases.py (fases 1, 2, 3)'},
        {'acao': 'gerar_modulo_utils', 'desc': 'Gera utils.py (colisao, pontuacao, game over)'},
        {'acao': 'extrair_codigo', 'desc': 'Extrai codigo puro de todos os modulos'},
        {'acao': 'validar_codigo', 'desc': 'Valida sintaxe de todos os .py'},
        {'acao': 'gerar_requirements', 'desc': 'Cria requirements.txt com pygame'},
        {'acao': 'criar_atalho', 'desc': 'Cria run.bat para executar o jogo'},
        {'acao': 'instalar_dependencias', 'desc': 'pip install -r requirements.txt'},
        {'acao': 'testar_execucao', 'desc': 'Tenta executar e captura erros'},
        {'acao': 'relatorio_final', 'desc': 'Mostra estrutura criada e instrucoes'},
    ],
}

# Mapa de acao -> ferramenta ToolOrchestrator
_ACAO_PARA_FERRAMENTA = {
    'buscar_exemplos': 'buscar_kg',
    'buscar_licoes': 'buscar_kg',
    'buscar_contexto': 'buscar_kg',
    'gerar_npc': 'gerar_npc',
    'validar_npc': 'validar_lua',
    'validar_codigo': 'validar_codigo',
    'validar_projeto': 'executar_python',
    'registrar_licao': 'buscar_kg',
    'perguntar_ia': 'perguntar_ia',
    'gerar_codigo': 'gerar_codigo',
    'salvar_arquivo': 'escrever_artefato',
    'buscar_exemplos_similares': 'buscar_memoria',
    'analisar_codigo': 'analisar_codigo',
    'criar_estrutura': 'gerar_codigo',
    'criar_fase': 'gerar_codigo',
    'criar_main': 'gerar_codigo',
    'executar_teste': 'executar_python',
    'perguntar_usuario': 'perguntar_ia',
    'criar_estrutura_pastas': 'criar_diretorio',
    'gerar_modulo_main': 'gerar_codigo',
    'gerar_modulo_entidades': 'gerar_codigo',
    'gerar_modulo_fases': 'gerar_codigo',
    'gerar_modulo_utils': 'gerar_codigo',
    'extrair_codigo': 'extrair_codigo',
    'gerar_requirements': 'gerar_requirements',
    'criar_atalho': 'criar_atalho',
    'instalar_dependencias': 'instalar_dependencias',
    'testar_execucao': 'executar_python',
    'relatorio_final': 'perguntar_ia',
}


class PlanValidator:
    """Validador de planos — verifica sanidade ANTES de executar.

    Verifica 6 condicoes:
    1. Nao vazio
    2. IDs sao unicos
    3. Ferramentas existem no ToolOrchestrator
    4. IDs de dependencia existem
    5. Nao tem loops (ordem topologica)
    6. Max 50% dos passos sem ferramenta
    """

    def __init__(self, tools=None):
        self.tools = tools

    def validar(self, plano):
        """Valida um plano. Retorna (valido, erros)."""
        erros = []

        # 1. Nao vazio
        if not plano or len(plano) == 0:
            return False, ['Plano vazio']

        # 2. IDs unicos
        ids = [p['id'] for p in plano]
        if len(ids) != len(set(ids)):
            erros.append(f'IDs duplicados: {ids}')

        # 3. Ferramentas existem
        if self.tools:
            for p in plano:
                ferramenta = p.get('ferramenta', '')
                if ferramenta and not self.tools.obter(ferramenta):
                    erros.append(f"Ferramenta '{ferramenta}' nao encontrada (passo {p['id']})")

        # 4. IDs de dependencia existem
        for p in plano:
            for dep in p.get('depende_de', []):
                if dep not in ids:
                    erros.append(f"Passo {p['id']} depende de ID {dep} que nao existe")

        # 5. Nao tem loops (ordem topologica)
        visitados = set()
        for p in sorted(plano, key=lambda x: x['id']):
            for dep in p.get('depende_de', []):
                if dep in visitados:
                    continue
                # Verifica se dep ja foi processado (deve ser ID menor)
                if dep >= p['id']:
                    erros.append(f'Possivel loop: passo {p["id"]} depende de {dep}')
                    break
            visitados.add(p['id'])

        # 6. Max 50% sem ferramenta
        if self.tools:
            sem_ferramenta = sum(1 for p in plano if not p.get('ferramenta'))
            if sem_ferramenta > len(plano) * 0.5:
                erros.append(f'{sem_ferramenta}/{len(plano)} passos sem ferramenta')

        return len(erros) == 0, erros


class TaskPlanner:
    """Planejador de tarefas usando LLM + templates."""

    def __init__(self, tools_orchestrator=None, ia=None):
        self.tools = tools_orchestrator
        self.ia = ia
        self.validator = PlanValidator(tools_orchestrator)
        self._decider = None

    def _get_decider(self):
        """Retorna Decider (lazy load)."""
        if self._decider is None:
            from modulos.decider import Decider
            self._decider = Decider(self.ia)
        return self._decider

    def planejar(self, request, task_type=''):
        """Planeja as subtarefas para executar um request.

        Args:
            request: Descricao completa do que fazer
            task_type: Tipo conhecido (se disponivel)

        Returns:
            Lista de subtarefas com id, acao, params, depende_de, ferramenta
        """
        # Se e tipo conhecido, usa template
        if task_type and task_type in PLANOS_CONHECIDOS:
            return self._adaptar_template(request, task_type)

        # Se e tipo que podemos inferir, usa template inferido
        tipo_inferido = self._inferir_tipo(request)
        if tipo_inferido:
            return self._adaptar_template(request, tipo_inferido)

        # Se e complexo, usa LLM para planejar
        return self._planejar_com_llm(request)

    def _adaptar_template(self, request, task_type):
        """Adapta um template conhecido para o request especifico.
        
        Descricoes sao dinamicas baseadas no tech stack detectado.
        Dependencias sao inteligentes (nao lineares) para isolar falhas.
        """
        template = PLANOS_CONHECIDOS[task_type]
        stack = self._extrair_tech_stack(request)
        ext = stack.get('ext', '.py')
        lang = stack.get('linguagem', 'python')
        deps = stack.get('deps', 'pygame')

        # Mapeamento de acoes que geram modulos
        acoes_modulo = {i+1: p['acao'] for i, p in enumerate(template)
                        if p['acao'].startswith('gerar_modulo_')}

        plano = []
        for i, passo in enumerate(template):
            params = self._extrair_params(passo['acao'], request)
            id_passo = i + 1

            # Descricao dinamica
            desc = passo['desc']
            desc = desc.replace('.py', ext).replace('python', lang).replace('pygame', deps)

            # Dependencias inteligentes por tipo de acao
            depende_de = []
            if passo['acao'] == 'validar_codigo' or passo['acao'] == 'extrair_codigo':
                depende_de = list(acoes_modulo.keys())  # depende dos modulos, nao de tudo
            elif passo['acao'] == 'criar_atalho':
                # Depende apenas de criar_estrutura_pastas (passo 3)
                for j, p in enumerate(template):
                    if p['acao'] == 'criar_estrutura_pastas':
                        depende_de = [j + 1]
                        break
            elif passo['acao'] == 'gerar_requirements':
                depende_de = []  # Pode rodar independente

            elif passo['acao'] == 'instalar_dependencias':
                # Depende apenas de gerar_requirements
                for j, p in enumerate(template):
                    if p['acao'] == 'gerar_requirements':
                        depende_de = [j + 1]
                        break
            elif passo['acao'] == 'testar_execucao':
                # Depende de validar_codigo
                for j, p in enumerate(template):
                    if p['acao'] == 'validar_codigo':
                        depende_de = [j + 1]
                        break
            elif passo['acao'] == 'relatorio_final':
                depende_de = list(range(1, id_passo))  # depende de todos anteriores
            elif i > 0:
                depende_de = [i]  # depende apenas do anterior imediato

            plano.append({
                'id': id_passo,
                'acao': passo['acao'],
                'descricao': desc,
                'params': params,
                'depende_de': depende_de,
                'ferramenta': _ACAO_PARA_FERRAMENTA.get(passo['acao'], 'perguntar_ia'),
            })
        return plano

    def _inferir_tipo(self, request):
        """Infere o tipo de tarefa pelo request.
        
        Usa Decider.classificar() como metodo principal (FAST).
        Fallback para regex se Decider falhar ou nao estiver disponivel.
        """
        # Tenta Decider primeiro
        try:
            decider = self._get_decider()
            exemplos_tipos = [
                ("Cria um ferreiro em Eridanus", "npc_shop"),
                ("Cria um vendedor de pocoes", "npc_shop"),
                ("Cria um jogo de plataforma em Python", "projeto_jogo"),
                ("Cria um site em HTML", "criar_codigo"),
                ("Cria um script python", "criar_codigo"),
                ("O que e SPA no MCR?", "pergunta_simples"),
                ("Como funciona um loop?", "pergunta_simples"),
                ("Analisa este codigo", "analisar_codigo"),
                ("Revisa este arquivo", "analisar_codigo"),
            ]
            tipo = decider.classificar(
                request,
                list(PLANOS_CONHECIDOS.keys()),
                exemplos=exemplos_tipos,
                instrucao="Classifique o request em um tipo de tarefa"
            )
            if tipo in PLANOS_CONHECIDOS:
                return tipo
        except Exception:
            pass

        # Fallback: regex
        r = request.lower()
        if any(p in r for p in ['cria', 'criar', 'faz', 'fazer', 'gera', 'gerar']):
            if any(p in r for p in ['npc', 'ferreiro', 'vendedor', 'loja', 'shop']):
                return 'npc_shop'
            if any(p in r for p in ['jogo', 'game', 'plataforma', 'fases']):
                return 'projeto_jogo'
            if any(p in r for p in ['projeto', 'multi-arquivo', 'modular']):
                return 'projeto_jogo'
            if any(p in r for p in ['python', 'script', 'codigo', 'programa']):
                if any(p in r for p in ['jogo', 'game', 'site', 'app']):
                    return 'projeto_jogo'
                return 'criar_codigo'
            if any(p in r for p in ['site', 'pagina', 'html']):
                return 'criar_codigo'
            return 'criar_codigo'

        if any(p in r for p in ['o que', 'o que e', 'como funciona', 'explique', 'quem']):
            return 'pergunta_simples'

        if any(p in r for p in ['analisa', 'revisa', 'verifica', 'testa']):
            return 'analisar_codigo'

        return None

    def _planejar_com_llm(self, request):
        """Usa LLM para planejar a execucao de um request complexo."""
        if not self.ia:
            return self._plano_fallback(request)

        ferramentas_disponiveis = self.tools.listar() if self.tools else {}

        prompt = (
            f"Voce e um planejador de tarefas. Dado um request do usuario, "
            f"decomponha em subtarefas executaveis.\n\n"
            f"Ferramentas disponiveis:\n{json.dumps(ferramentas_disponiveis, indent=2, ensure_ascii=False)}\n\n"
            f"Request: {request}\n\n"
            f"responda APENAS com JSON no formato:\n"
            f'[{{"id": 1, "acao": "nome_da_acao", "descricao": "...", '
            f'"params": {{...}}, "depende_de": []}}]'
        )

        try:
            resposta = self.ia.gerar(prompt, 0.2, "planejador")
            plano = json.loads(resposta)
            if not isinstance(plano, list):
                return self._plano_fallback(request)
            # Validar estrutura basica
            for item in plano:
                item.setdefault('depende_de', [])
                item.setdefault('params', {})
                item['ferramenta'] = _ACAO_PARA_FERRAMENTA.get(item.get('acao', ''), 'perguntar_ia')

            # Validar com PlanValidator
            valido, erros = self.validator.validar(plano)
            if not valido:
                print(f"[TaskPlanner] Plano LLM rejeitado: {erros}")
                # Fallback: adapta pra 1 passo
                return self._plano_fallback(request)

            return plano
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            print(f"[TaskPlanner] Erro no planejamento LLM: {e}")
            return self._plano_fallback(request)

    def _plano_fallback(self, request):
        """Plano de fallback: 1 passo (perguntar_ia)."""
        return [{
            'id': 1,
            'acao': 'perguntar_ia',
            'descricao': f'Processar: {request[:100]}',
            'params': {'pergunta': request, 'tarefa': 'pesado'},
            'depende_de': [],
            'ferramenta': 'perguntar_ia',
        }]

    def _extrair_tech_stack(self, request):
        """Extrai tech stack (linguagem, extensao, deps, comando).
        
        Usa Decider.extrair_json() como metodo principal para deteccao universal.
        Fallback para regex se Decider falhar.
        Cache global para evitar chamadas repetidas.
        """
        global _tech_stack_cache
        cache_key = request[:100]
        if cache_key in _tech_stack_cache:
            return _tech_stack_cache[cache_key]

        # Fallback padrao
        fallback = {
            'linguagem': 'python', 'ext': '.py', 'deps': 'pygame',
            'comando_run': 'python src/main.py',
            'desc_modulos': {
                'main': 'loop principal e init (python)',
                'entidades': 'entidades do jogo (python)',
                'fases': 'fases do jogo (python)',
                'utils': 'utilitarios (python)',
            },
        }

        # Tenta Decider primeiro
        try:
            decider = self._get_decider()
            exemplos = [
                ("Cria um jogo em Python com pygame", {"linguagem": "python", "ext": ".py", "deps": "pygame", "comando_run": "python src/main.py"}),
                ("Cria um jogo em JavaScript com Phaser", {"linguagem": "javascript", "ext": ".js", "deps": "phaser", "comando_run": "node src/main.js"}),
                ("Cria um jogo em Lua com Love2D", {"linguagem": "lua", "ext": ".lua", "deps": "love", "comando_run": "love src"}),
            ]
            dados = decider.extrair_json(
                request,
                {'linguagem': '', 'ext': '', 'deps': '', 'comando_run': ''},
                exemplos=exemplos,
                instrucao="Extraia a tecnologia principal do projeto"
            )
            if dados.get('linguagem'):
                dados['desc_modulos'] = {
                    'main': f'loop principal, init ({dados["linguagem"]})',
                    'entidades': f'entidades do jogo ({dados["linguagem"]})',
                    'fases': f'fases do jogo ({dados["linguagem"]})',
                    'utils': f'utilitarios ({dados["linguagem"]})',
                }
                _tech_stack_cache[cache_key] = dados
                return dados
        except Exception:
            pass

        # Fallback: regex + comandos padrao
        r = request.lower()
        deteccoes = [
            (r'\bpython\b|\bpygame\b', 'python', '.py'),
            (r'\bjavascript\b|\bjs\b|\bnode\b|\bphaser\b|\breact\b', 'javascript', '.js'),
            (r'\blua\b|\blove2d\b|\blove\b', 'lua', '.lua'),
            (r'\brust\b|\bbevy\b', 'rust', '.rs'),
            (r'\bc\+\+\b|\bcpp\b|\bsdl2\b|\bsfml\b', 'cpp', '.cpp'),
            (r'\bc#\b|\bcsharp\b|\bmonogame\b|\bunity\b', 'csharp', '.cs'),
            (r'\bgo\b|\begolang\b|\bebitengine\b', 'go', '.go'),
            (r'\bkotlin\b|\blibgdx\b', 'kotlin', '.kt'),
            (r'\bjava\b|\blwjgl\b', 'java', '.java'),
            (r'\btypescript\b|\bts\b', 'typescript', '.ts'),
            (r'\bruby\b', 'ruby', '.rb'),
            (r'\bphp\b', 'php', '.php'),
            (r'\bdart\b|\bflutter\b', 'dart', '.dart'),
            (r'\bswift\b|\bspritekit\b', 'swift', '.swift'),
        ]
        linguagem = 'python'
        ext = '.py'
        for padrao, lang, ext_lang in deteccoes:
            if re.search(padrao, r):
                linguagem = lang
                ext = ext_lang
                break

        comandos_padrao = {
            'python': f'python src/main{ext}',
            'javascript': f'node src/main{ext}',
            'typescript': f'npx ts-node src/main{ext}',
            'lua': f'lua src/main{ext}',
            'rust': 'cargo run',
            'cpp': f'g++ src/main{ext} -o game && game',
            'csharp': 'dotnet run',
            'go': f'go run src/main{ext}',
            'java': 'javac src/main.java && java Main',
            'kotlin': 'kotlinc src/main.kt -include-runtime -d game.jar && java -jar game.jar',
        }

        fallback['linguagem'] = linguagem
        fallback['ext'] = ext
        fallback['comando_run'] = comandos_padrao.get(linguagem, f'python src/main{ext}')
        _tech_stack_cache[cache_key] = fallback
        return fallback

    def _extrair_params(self, acao, request):
        """Extrai parametros relevantes para a acao."""
        if acao == 'gerar_npc':
            tipo = 'shop'
            for t in ['shop', 'quest', 'bank', 'gate', 'trainer', 'dialogue']:
                if t in request.lower():
                    tipo = t
                    break
            return {'descricao': request, 'tipo': tipo}

        if acao == 'perguntar_ia':
            return {'pergunta': request}

        if acao == 'gerar_codigo':
            return {'descricao': request}

        if acao in ('buscar_exemplos', 'buscar_contexto'):
            return {'texto': request}

        if acao == 'buscar_exemplos_similares':
            return {'request': request}

        if acao == 'analisar_codigo':
            return {'codigo': request}

        if acao == 'salvar_arquivo':
            caminho = None
            for padrao in [r'sandbox[/\\][\w\.]+', r'[\w]+\.py', r'[\w]+\.lua', r'[\w]+\.txt']:
                m = re.search(padrao, request)
                if m:
                    caminho = m.group(0)
                    break
            if caminho and not caminho.startswith('sandbox'):
                caminho = os.path.join('sandbox', caminho)
            return {'caminho': caminho or 'sandbox/artefato_gerado.py'}

        if acao == 'perguntar_usuario':
            stack = self._extrair_tech_stack(request)
            return {'pergunta': f"Vou criar um projeto {stack.get('linguagem','?')} ({stack.get('deps','?')}). "
                               f"Posso prosseguir?", 'tarefa': 'leve'}

        if acao.startswith('gerar_modulo_'):
            stack = self._extrair_tech_stack(request)
            nome_modulo = acao.replace('gerar_modulo_', '')
            ext = stack.get('ext', '.py')
            desc_modulo = stack.get('desc_modulos', {}).get(nome_modulo, nome_modulo)
            return {
                'descricao': f"Crie o modulo {nome_modulo}{ext} do jogo em {stack.get('linguagem','?')}. "
                            f"{desc_modulo}. Contexto: {request[:200]}",
                'linguagem': stack.get('linguagem', 'python'),
            }

        if acao == 'criar_estrutura_pastas':
            from modulos.util import extrair_nome_projeto
            nome = extrair_nome_projeto(request)
            return {'caminho': os.path.join(BASE, 'sandbox', nome)}

        if acao == 'gerar_requirements':
            stack = self._extrair_tech_stack(request)
            from modulos.util import extrair_nome_projeto
            nome_proj = extrair_nome_projeto(request)
            caminho_req = os.path.join(BASE, 'sandbox', nome_proj, 'requirements.txt')
            return {'dependencias': stack.get('deps', 'pygame'), 'caminho': caminho_req}

        if acao == 'criar_atalho':
            stack = self._extrair_tech_stack(request)
            from modulos.util import extrair_nome_projeto
            nome = extrair_nome_projeto(request)
            return {'comando': stack.get('comando_run', 'python src/main.py'),
                    'caminho': os.path.join(BASE, 'sandbox', nome)}

        if acao == 'instalar_dependencias':
            from modulos.util import extrair_nome_projeto
            nome = extrair_nome_projeto(request)
            return {'requirements_path': os.path.join(BASE, 'sandbox', nome, 'requirements.txt')}

        if acao == 'testar_execucao':
            return {'codigo': ''}

        if acao == 'relatorio_final':
            return {'pergunta': 'Gere um relatorio final do projeto criado', 'tarefa': 'texto'}

        return {}
