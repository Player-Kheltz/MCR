"""Bateria de Testes em Ciclo — 20 Cenarios Contexto-Agnosticos.

Gera requests UNICOS via Decider/FAST, executa em ciclo, e alimenta
o contexto do proximo cenario com o resultado do anterior.

Uso:
    python _test_bateria.py                    # 3 cenarios (rapido)
    python _test_bateria.py --completo         # 10 cenarios
    python _test_bateria.py --todos            # 20 cenarios (lento)
    python _test_bateria.py --semente 42       # Reprodutivel
"""
import sys, os, json, time, random

# Paths
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

from modulos.decider import Decider
from modulos.ia import IA
from modulos.master_agent import MasterAgent

# ============================================================
# EXEMPLOS MULTI-CONTEXTO PARA OS 20 CENARIOS
# ============================================================
# Cada cenario tem exemplos de contextos DIFERENTES para guiar o FAST.
# Contextos: jogo, api, site, cli, dashboard, script, ferramenta, bot, analise...

EXEMPLOS_CENARIO = {
    1: [  # Criar projeto principal
        ("Cria um jogo de plataforma em Python com 3 fases usando Pygame", "python/jogo"),
        ("Cria uma API REST em Flask com 3 endpoints: criar, listar, deletar", "python/api"),
        ("Cria uma ferramenta CLI em Python que processa CSV e gera JSON", "python/cli"),
    ],
    2: [  # Ferramenta complementar
        ("Cria um editor visual para as fases do jogo com tkinter. Salva em tools/", "ferramenta"),
        ("Cria um gerador de relatorios HTML para a API. Salva em tools/", "ferramenta"),
        ("Cria um validador de dados de entrada para o CLI tool. Salva em tools/", "ferramenta"),
    ],
    3: [  # Site sobre o projeto
        ("Cria landing page do jogo: homepage, download, contato. HTML+CSS+JS. Salva em site/", "site"),
        ("Cria portal de documentacao interativa da API com playground. Salva em site/", "site"),
        ("Cria dashboard de status do CLI tool com exemplos de uso. Salva em site/", "site"),
    ],
    4: [  # Auditoria de codigo
        ("analise a arquitetura de TUDO que foi criado: acoplamento, coesao, SRP. Mencione linhas especificas.", "auditoria"),
        ("audite seguranca de TUDO: injecao, path traversal, dados sensiveis. Sugira corrigir as 3 mais criticas.", "auditoria"),
        ("analise performance de TUDO: loops ineficientes, alocacao, I/O. Sugira 3 otimizacoes com linhas.", "auditoria"),
    ],
    5: [  # Aplicar melhorias
        ("aplique as 3 correcoes de bugs mais importantes sugeridas na auditoria. Mostre diff antes vs depois.", "melhoria"),
        ("aplique as 3 refatoracoes de arquitetura sugeridas. Valide com os testes existentes.", "melhoria"),
        ("aplique as 3 otimizacoes de performance sugeridas. Mostre metricas de antes vs depois.", "melhoria"),
    ],
    6: [  # Testes unitarios
        ("crie testes unitarios com pytest para os 3 modulos principais. Crie tests/ e execute os testes.", "testes"),
        ("crie testes com unittest para boundary conditions e edge cases. Crie tests/ e execute.", "testes"),
        ("adicione doctests nas docstrings das funcoes principais. Execute python -m doctest.", "testes"),
    ],
    7: [  # Refatorar com boas praticas
        ("refatore: crie config.py com constantes, adicione type hints em todas as funcoes, remova magic numbers.", "refatoracao"),
        ("refatore usando: Strategy pattern, Observer pattern, Factory pattern. Mantenha funcional.", "refatoracao"),
        ("refatore: separe em modulos menores (ate 200 linhas cada), use dataclasses, adicione enums.", "refatoracao"),
    ],
    8: [  # Otimizar performance
        ("implemente object pooling para objetos criados/destruidos frequentemente. Mostre reducao.", "otimizacao"),
        ("adicione cache LRU para resultados de funcoes custosas e lazy loading. Mostre comparativo.", "otimizacao"),
        ("otimize loops com numpy ou list comprehensions. Substitua loops aninhados. Mostre speedup.", "otimizacao"),
    ],
    9: [  # Empacotar projeto
        ("crie setup.py com metadados, Dockerfile two-stage, Makefile com targets, .gitignore completo.", "empacotamento"),
        ("crie pyproject.toml (poetry), Dockerfile multi-stage, docker-compose.yml, .gitignore.", "empacotamento"),
        ("crie Pipfile, Dockerfile, Makefile, .gitignore, .env.example. Pipenv deve funcionar.", "empacotamento"),
    ],
    10: [  # Documentar tudo
        ("gere README.md completo com descricao, instalacao, uso, estrutura. Adicione docstrings e CHANGELOG.md.", "documentacao"),
        ("crie documentacao Sphinx: conf.py, index.rst, api.rst. sphinx-build deve gerar HTML.", "documentacao"),
        ("crie documentacao MkDocs: mkdocs.yml, docs/index.md, docs/api.md. mkdocs build deve funcionar.", "documentacao"),
    ],
    11: [  # Auditoria de seguranca
        ("audite seguranca: injecao de codigo, path traversal, dados sensiveis. Corrija as 3 vulnerabilidades mais criticas.", "seguranca"),
        ("audite XSS, CSRF, e seguranca de headers. Implemente CSP e sanitizacao de inputs.", "seguranca"),
        ("audite vazamento de informacoes, erros expostos, e falta de autenticacao. Corrija.", "seguranca"),
    ],
    12: [  # Internacionalizacao
        ("adicione suporte a pt-BR e en-US com gettext. Extraia strings, crie .po, implemente seletor de idioma.", "i18n"),
        ("adicione suporte a 2 idiomas com JSON de traducoes. Implemente deteccao automatica de locale.", "i18n"),
        ("crie sistema de traducao com dicionarios. Adicione fallback para idioma padrao.", "i18n"),
    ],
    13: [  # CI/CD Pipeline
        ("crie GitHub Actions workflow com stages: lint, test, build, deploy. Inclua matrix Python 3.11-3.13.", "cicd"),
        ("crie GitLab CI com stages: validate, test, package, release. Inclua caching.", "cicd"),
        ("crie Jenkinsfile com pipeline declarativo: checkout, build, test, archive.", "cicd"),
    ],
    14: [  # Linting e pre-commit
        ("configure pylint + black + flake8. Crie .pre-commit-config.yaml com hooks. Execute e corrija erros.", "linting"),
        ("configure eslint + prettier para o site. Crie .eslintrc.js e .prettierrc. Execute e corrija.", "linting"),
        ("configure luacheck + stylua. Crie .luacheckrc. Execute e corrija problemas encontrados.", "linting"),
    ],
    15: [  # Monitoramento e logging
        ("adicione logging estruturado com loguru: niveis DEBUG, INFO, ERROR, rotacao, e endpoint /health.", "logging"),
        ("adicione sistema de logging com winston para o site: transporte para arquivo e console com cores.", "logging"),
        ("adicione logging com formatos JSON, rotacao diaria, e retencao de 30 dias.", "logging"),
    ],
    16: [  # UX/UI e acessibilidade
        ("melhore acessibilidade: ARIA labels, contraste de cores, navegacao por teclado, modo escuro.", "ux"),
        ("adicione suporte a leitores de tela, foco visivel, e reducao de movimento. Valide com axe-core.", "ux"),
        ("implemente design responsivo, suporte a temas (claro/escuro), e animacoes com prefers-reduced-motion.", "ux"),
    ],
    17: [  # API RESTful
        ("crie API REST com Flask: recursos CRUD, autenticacao basica, documentacao OpenAPI.", "api"),
        ("crie API REST com Express.js: rotas, middleware, validacao, documentacao Swagger.", "api"),
        ("crie API REST com FastAPI: endpoints async, validacao Pydantic, documentacao automatica.", "api"),
    ],
    18: [  # Backup e recovery
        ("crie script de backup .sh que compacta src/ com timestamp. Crie restore.sh. Crie cron semanal.", "backup"),
        ("crie sistema de backup incremental com Python: copia so arquivos modificados, agenda com schedule.", "backup"),
        ("crie script de export/import de dados: exporta para JSON, importa de JSON com validacao.", "backup"),
    ],
    19: [  # Migracao de dados
        ("migre armazenamento de JSON para SQLite com sqlite3. Crie script de migracao com rollback e teste.", "migracao"),
        ("migre de SQLite para PostgreSQL com SQLAlchemy. Script de migracao com alembic.", "migracao"),
        ("migre de arquivos texto para MongoDB com pymongo. Script ETL com validacao e relatorio.", "migracao"),
    ],
    20: [  # Feature flags
        ("implemente feature toggles: config.json, funcao is_enabled(), 3 features (dark_mode, beta, analytics).", "features"),
        ("implemente sistema de flags com gradual rollout: % de usuarios por flag, kill switch, A/B testing.", "features"),
        ("implemente flags com dependencias entre features e cache de decisoes para performance.", "features"),
    ],
}


def extrair_contexto(request):
    """Extrai contexto aproximado do request para o historico."""
    r = request.lower()
    if any(p in r for p in ['jogo', 'game', 'plataforma']):
        return 'jogo'
    if any(p in r for p in ['api', 'rest', 'flask', 'endpoint']):
        return 'api'
    if any(p in r for p in ['cli', 'tool', 'linha de comando']):
        return 'cli'
    if any(p in r for p in ['site', 'pagina', 'html', 'landing']):
        return 'site'
    if any(p in r for p in ['test', 'pytest', 'unittest']):
        return 'testes'
    if any(p in r for p in ['docker', 'setup', 'makefile']):
        return 'empacotamento'
    if any(p in r for p in ['audit', 'seguranca', 'vulnerab']):
        return 'auditoria'
    return 'outro'


def extrair_linguagem(request):
    """Extrai linguagem aproximada do request para o historico."""
    r = request.lower()
    if any(p in r for p in ['python', 'flask', 'pygame', 'django']):
        return 'python'
    if any(p in r for p in ['javascript', 'js', 'html', 'css', 'react', 'phaser']):
        return 'javascript'
    if any(p in r for p in ['lua', 'love2d']):
        return 'lua'
    if any(p in r for p in ['typescript', 'ts']):
        return 'typescript'
    if any(p in r for p in ['rust']):
        return 'rust'
    if any(p in r for p in ['go', 'golang']):
        return 'go'
    return '?'


class GeradorDeTestes:
    """Gera baterias de teste UNICAS via Decider/FAST.
    
    A cada chamada, gera combinacoes diferentes de:
    - linguagem (python, js, lua, rust, go...)
    - framework (pygame, flask, phaser, love2d...)
    - contexto (jogo, api, site, cli, dashboard, bot...)
    - features (save/load, auth, cache, logging...)
    """

    def __init__(self, ia=None):
        self.ia = ia or IA()
        self.decider = Decider(self.ia)
        self.historico = []

    def gerar_request(self, cenario_id, projetos_anteriores=None):
        """Gera request UNICO para o cenario, em contexto DIFERENTE.
        
        Args:
            cenario_id: 1-20
            projetos_anteriores: Lista de dicts com projetos ja criados
        
        Returns:
            String com request de teste
        """
        if projetos_anteriores is None:
            projetos_anteriores = []
        
        # Monta contexto do que ja foi gerado
        ctx_anterior = "Historico: "
        ctxs = [p.get('contexto', '?') for p in projetos_anteriores[-5:]]
        ctx_anterior += ', '.join(ctxs) if ctxs else 'nenhum'
        ctx_anterior += f" ({len(projetos_anteriores)} projetos)"
        
        exemplos = EXEMPLOS_CENARIO.get(cenario_id, [])
        
        # Salt aleatorio para evitar cache do Decider (garante variacao)
        salt = random.randint(0, 99999)
        
        try:
            dados = self.decider.extrair_json(
                f"Cenario {cenario_id} [{salt}]: gere request de teste em contexto NOVO",
                {'request': '', 'linguagem': '', 'contexto': ''},
                exemplos=exemplos[:3],
                instrucao=(
                    f"{ctx_anterior}\n"
                    f"NUNCA repita contexto, linguagem ou framework.\n"
                    f"NUNCA repita exemplos.\n"
                    f"Varie: jogo, api, site, cli, dashboard, bot, script...\n"
                    f"Se possivel, use linguagem DIFERENTE dos exemplos.\n"
                    f"Request deve ser detalhado (>15 palavras) e executavel."
                )
            )
            request = dados.get('request', '')
            if request and len(request) > 15:
                return request
        except Exception as e:
            print(f"[Gerador] Erro ao gerar request cenario {cenario_id}: {e}")
        
        # Fallback: sorteia um exemplo existente
        if exemplos:
            return random.choice(exemplos)[0]
        return f"Cenario {cenario_id}: cria um projeto exemplo"


def executar_bateria(n=3, semente=None):
    """Executa bateria de N cenarios em contextos variados.
    
    Args:
        n: Numero de cenarios (1-20, padrao 3 para testes rapidos)
        semente: Para reprodutibilidade (None = aleatorio)
    
    Retorna:
        Lista de resultados
    """
    if semente is not None:
        random.seed(semente)
    
    ia = IA()
    gerador = GeradorDeTestes(ia)
    agent = MasterAgent()
    
    projetos_anteriores = []
    resultados = []
    
    n = min(n, 20)
    cenarios_sorteados = random.sample(range(1, 21), n)
    
    for idx, cenario_id in enumerate(cenarios_sorteados, 1):
        request = gerador.gerar_request(cenario_id, projetos_anteriores)
        
        print(f"\n{'='*60}")
        print(f"  CENARIO {cenario_id}/20 ({idx}/{n})")
        print(f"{'='*60}")
        print(f"  Request: {request[:120]}...")
        
        t0 = time.time()
        r = agent.executar(request)
        tempo = time.time() - t0
        
        resultados.append(r)
        
        n_ok = r.get('n_sucesso', 0)
        n_total = r.get('n_subtarefas', 0)
        status = 'OK' if r.get('sucesso') else f'PARCIAL ({n_ok}/{n_total})'
        print(f"  -> {status} em {tempo:.0f}s")
        
        projetos_anteriores.append({
            'id': cenario_id,
            'request': request[:100],
            'contexto': extrair_contexto(request),
            'linguagem': extrair_linguagem(request),
            'sucesso': r.get('sucesso', False),
            'n_ok': n_ok,
        })
    
    # Relatorio final
    print(f"\n{'='*60}")
    total_ok = sum(1 for r in resultados if r.get('sucesso'))
    print(f"  BATERIA: {total_ok}/{n} CENARIOS OK")
    print(f"  Subtarefas: {sum(r.get('n_sucesso', 0) for r in resultados)}/"
          f"{sum(r.get('n_subtarefas', 0) for r in resultados)}")
    print(f"  Tempo total: {sum(r.get('tempo', 0) for r in resultados):.0f}s")
    print(f"{'='*60}")
    
    # Salva relatorio
    try:
        relatorio = {
            'data': time.strftime('%Y-%m-%d %H:%M:%S'),
            'n_cenarios': n,
            'semente': semente,
            'total_ok': total_ok,
            'resultados': [{
                'id': p['id'],
                'contexto': p['contexto'],
                'linguagem': p['linguagem'],
                'sucesso': p['sucesso'],
                'request': p['request'],
            } for p in projetos_anteriores],
        }
        path = os.path.join(BASE, 'sandbox', '.mcr_bateria_relatorio.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
        print(f"\n[Relatorio salvo em .mcr_bateria_relatorio.json]")
    except Exception as e:
        print(f"\n[Erro ao salvar relatorio: {e}]")
    
    return resultados


# ============================================================
# PONTO DE ENTRADA
# ============================================================

if __name__ == '__main__':
    import sys
    
    # Parse args
    args = sys.argv[1:]
    n = 3
    semente = None
    
    if '--completo' in args:
        n = 10
    if '--todos' in args:
        n = 20
    for a in args:
        if a.startswith('--semente'):
            try:
                semente = int(args[args.index(a) + 1])
            except (ValueError, IndexError):
                pass
    
    print(f"{'='*60}")
    print(f"  BATERIA DE TESTES - {n} CENARIOS")
    print(f"  Semente: {semente or 'aleatoria'}")
    print(f"{'='*60}")
    
    resultados = executar_bateria(n=n, semente=semente)
    
    print(f"\nFinalizado. {len(resultados)} cenarios executados.")
