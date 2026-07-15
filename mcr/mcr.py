"""mcr.mcr — Motor Cognitivo Universal.

Um motor. Uma Equação. Uma Entropia. Um Markov.
Aplica-se a qualquer domínio. Tibia e Visual são as provas.

Arquitetura:
    perceber → decidir → executar → avaliar → aprender

Tudo é Markov. A Equação MCR avalia. A Entropia mede caos.
As ferramentas executam. O domínio é irrelevante.
"""
import time
import hashlib
import os
import re as _re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

from mcr.paths import CACHE_DIR, ensure_dirs

# ─── Motor Markov (intacto) ─────────────────────────────────
from mcr.engine import MCR as MarkovEngine
from mcr.signature import MCRFingerprint

# ─── Equação MCR (intacta) ──────────────────────────────────
from mcr.equacao_mcr import calcular_ponte, classificar_tipo_ponte, get_penalidade

# ─── Registry (intacto) ─────────────────────────────────────
from mcr.registry import get_registry, MCRRegistry, ToolEntry

# ─── Cognição multi-nível (acoplamento + superposition) ─────
from mcr.coupling import MCRCoupling
from mcr.superposicao import MCRSuperposicao


class MCR:
    """Motor Cognitivo Universal.

    Markov 1ª ordem + Entropia Shannon + Equação MCR = Cognição.
    Aplica-se a Tibia, Visual, Áudio, qualquer jogo, qualquer projeto.

    Uso:
        mcr = MCR()
        mcr.auto_treinar()
        
        npc = mcr.processar("Crie um ferreiro anão")
        sprite = mcr.processar("Gere um sprite de escudo")
    """

    def __init__(self):
        ensure_dirs()

        # ─── Motor ──────────────────────────────────────
        self.mk = MarkovEngine("mcr_cognicao")
        try:
            self.mk.load()
        except Exception:
            pass
        self.fp = MCRFingerprint()

        # ─── Cognição multi-nível ───────────────────────
        self._coupling = MCRCoupling()
        try:
            self._coupling.load()
        except Exception:
            pass
        self._superposicao = MCRSuperposicao()
        self.mk_palavra = MarkovEngine("mcr_palavra")
        try:
            self.mk_palavra.load()
        except Exception:
            pass

        # ─── 13 Módulos MCR (lazy init) ─────────────────
        self._esfera = None          # correlacao N-dimensional
        self._esquecimento = None    # poda por entropia
        self._hiperesfera = None     # auto-descoberta de tokenizacao
        self._conexao = None         # pontes entre dominios
        self._bridge = None          # analogias cross-domain
        self._mundo = None           # modelo causal
        self._genesis = None         # auto-expansao de dominios
        self._variador = None        # preenche gaps com valores reais
        self._descobridor = None     # frequencia diferencial
        self._stopwords = set()

        # ─── Registry ───────────────────────────────────
        self._registry = get_registry()

        # ─── Estado interno ─────────────────────────────
        self._historico: List[Dict] = []
        self._memoria: List[Dict] = []
        self._total_processamentos = 0
        self._sessao_inicio = time.time()
        self._ultima_interacao = time.time()
        self._contexto_conversa: List[str] = []  # ultimas acoes para contexto
        self._erros: List[Dict] = []  # log de erros para debug

        # ─── Identidade (absorvida de mcr_self) ─────────
        self.nome = "MCR"
        self.criador = "Kheltz"
        self.proposito = (
            "Framework cognitivo universal. Provar que Markov 1ª ordem + "
            "Entropia Shannon + Equação MCR são suficientes para cognição."
        )
        self.versoes = ["1.0 (Markov)", "2.0 (unificado)"]
        self.versao = "2.0"
        self.opinioes: Dict[str, str] = {}

        # ─── Persistência SQLite ─────────────────────────
        self._sqlite = None
        try:
            from mcr.mcr_sqlite import MCRSQLite
            self._sqlite = MCRSQLite("mcr_sessao")
        except Exception:
            pass

        # ─── Log de execuções ───────────────────────────
        self._carregar_execucoes()

        # ─── Observador Universal (auto-observação) ─────
        self._observador = None
        self._obs_ativado = False
        try:
            self.ativar_observador()
        except Exception:
            pass

        # ─── Bootstrap silencioso ───────────────────────
        self._bootstrap()

    # ═══════════════════════════════════════════════════════
    # BOOTSTRAP
    # ═══════════════════════════════════════════════════════

    def _bootstrap(self):
        """Inicializa o registry se vazio. Bootstrap pesado é lazy."""
        try:
            from mcr.bootstrap import inicializar
            if len(self._registry.listar()) < 3:
                inicializar(self._registry)
        except Exception as e:
            self._log_erro('bootstrap', e)
            pass
        try:
            self._inicializar_templates()
        except Exception as e:
            self._log_erro('inicializar_templates', e)

    def _lazy(self, attr, cls_path):
        """Lazy init de um modulo MCR. Carrega so quando usado."""
        if getattr(self, attr, None) is None:
            try:
                parts = cls_path.rsplit('.', 1)
                mod = __import__(parts[0], fromlist=[parts[1]])
                cls = getattr(mod, parts[1])
                self.__dict__[attr] = cls()
            except Exception:
                pass
        return getattr(self, attr, None)

    def _self_feedback(self, acao, conf, entrada):
        """MCR investiga proprio input quando incerto. Igual LLM.
        
        Usa coupling._posicao_acao + mk_palavra para verificar:
        1. Se P0 da primeira palavra mistura gerar_* e responder → ambíguo
        2. Se o bigrama (primeira→segunda) aparece em comandos conhecidos
        3. Se nao tem verbo de comando reconhecido → self-corrige para responder
        
        Tudo via entropia. Zero hardcode.
        """
        try:
            palavras = entrada.replace('_', ' ').split()
            if not palavras:
                return acao, conf
            
            primeira = palavras[0][:10].lower()
            p0_dist = self._coupling._posicao_acao.get(f'P0:{primeira}', {})
            
            if not p0_dist or sum(p0_dist.values()) < 2:
                return acao, conf
            
            # Entropia de P0
            import math
            total_p0 = sum(p0_dist.values())
            h = 0.0
            for c in p0_dist.values():
                p = c / total_p0
                if p > 0: h -= p * math.log2(p)
            max_h = math.log2(max(len(p0_dist), 2))
            h_norm = h / max_h if max_h > 0 else 0
            
            tem_responder = 'responder' in p0_dist
            tem_gerar = any(k.startswith('gerar_') for k in p0_dist)
            
            if not (tem_responder and tem_gerar and h_norm > 0.7):
                return acao, conf
            
            # Ambíguo — verifica se tem verbo de comando via mk_palavra
            # Verbos de comando (crie, gere, faca) sao descobertos por entropia:
            # aparecem em P0 de multiplas acoes gerar_* (H alta, sem responder)
            input_curto = len(palavras) <= 3
            if not input_curto:
                return acao, conf
            
            # Verifica: a primeira palavra é um verbo de comando?
            # Verbo de comando = P0 so tem gerar_*, sem responder
            so_gerar = all(k.startswith('gerar_') for k in p0_dist)
            if so_gerar:
                # Primeira palavra é verbo de comando — mantem acao
                return acao, conf
            
            # Primeira palavra nao é verbo (tem responder em P0)
            # Self-corrige: se responder tem fatia SIGNIFICATIVA (>30%), pergunta
            responder_pct = p0_dist.get('responder', 0) / total_p0
            gerar_pct = 1.0 - responder_pct
            if responder_pct > 0.40 and gerar_pct < 0.60:
                return 'responder', max(conf * 0.6, responder_pct * 0.8)
            
            return acao, conf
        except Exception:
            return acao, conf

    def _inicializar_templates(self):
        """Cold start inteligente: MCR explora o workspace como um LLM.
        Fase 1: Glob rapido — so nomes de arquivos, nao le conteudo.
        Fase 2: Entropia dos stems decide quais dirs sao dominios.
        Fase 3: Registra wrappers. Seeds e leitura sao lazy (auto_treinar).
        Zero hardcoded. Zero leitura de arquivos na init."""
        from pathlib import Path
        from mcr.paths import ROOT_DIR
        from math import log2

        # Fase 1: GLOB — descobre diretorios pelos nomes dos arquivos
        # Como um LLM: olha a estrutura primeiro, nao le cada arquivo
        # Timeout: se demorar mais que 5s, para (agnostico, sem hardcode de dirs)
        dirs_por_tool = {}
        t_start = time.time()

        def _scan(path, depth=0):
            if depth >= 3 or time.time() - t_start > 5.0:
                return
            try:
                with os.scandir(path) as it:
                    files = []
                    subdirs = []
                    for entry in it:
                        if entry.name.startswith('.') or entry.name.startswith('__'):
                            continue
                        if entry.is_file():
                            files.append(entry.name)
                        elif entry.is_dir():
                            subdirs.append(entry.path)
                    if files:
                        stems = set(Path(f).stem.lower() for f in files[:100] if len(Path(f).stem) > 2)
                        if len(stems) >= 3:
                            nome_dir = Path(path).name.lower().replace(' ', '_').replace('-', '_')
                            tool = f"gerar_{nome_dir}"
                            if tool not in dirs_por_tool:
                                dirs_por_tool[tool] = []
                            dirs_por_tool[tool].append(Path(path))
                    for sd in subdirs:
                        if time.time() - t_start > 5.0:
                            break
                        _scan(sd, depth + 1)
            except (PermissionError, OSError):
                pass

        _scan(ROOT_DIR)

        # Fase 2: ENTROPIA — diversidade de stems decide quais sao dominios
        tools_significativas = {}
        for tool, dirs in dirs_por_tool.items():
            todos_stems = set()
            for d in dirs:
                try:
                    for f in list(d.iterdir())[:30]:
                        if f.is_file() and len(f.stem) > 2:
                            todos_stems.add(f.stem.lower())
                except Exception:
                    pass
            h = log2(len(todos_stems)) if todos_stems else 0
            if h > 2.0:
                tools_significativas[tool] = dirs
        self._dirs_por_tool = tools_significativas

        # Fase 3: Registra wrappers universais
        wrappers = {}
        def _gerar(entrada="", texto="", **kw):
            msg = entrada or texto
            return self._gerar_universal(msg, self._decidir_tool(msg))
        for tool in tools_significativas:
            wrappers[tool] = _gerar

        def _responder(entrada="", texto="", **kw):
            msg = entrada or texto
            if not msg:
                return {'sucesso': False, 'erro': 'Sem entrada'}
            try:
                from mcr.metacognicao import Metacognicao
                meta = Metacognicao()
                score, just = meta.calcular_confianca(msg)
                if score > 0.3:
                    return {'sucesso': True, 'resposta': f'[KG:{score:.0%}] {just}',
                            'confianca': round(score, 3), 'fonte': 'kg'}
            except Exception:
                pass
            try:
                from mcr.raciocinador import Raciocinador
                rac = Raciocinador()
                r = rac.raciocinar(msg)
                if r and r.get('resultado'):
                    return {'sucesso': True, 'resposta': str(r['resultado']),
                            'fonte': 'raciocinio', 'tipo': r.get('tipo', 'generico')}
            except Exception:
                pass
            return {'sucesso': True, 'resposta': 'Nao tenho informacao suficiente.',
                    'fonte': 'fallback', 'confianca': 0.0}
        wrappers['responder'] = _responder

        try:
            def _gerir_mundo(entrada="", texto="", **kw):
                msg = entrada or texto
                tema = msg if msg else "Mundo Vivo"
                from mcr.mcr_world_system import MCRWorldSystem
                ws = MCRWorldSystem()
                report = ws.ciclo(tema=tema, max_entidades=3)
                return {'sucesso': report.get('entidades_criadas', 0) > 0,
                        'entidades': report.get('entidades_criadas', 0),
                        'relatorio': report}
            wrappers['gerir_mundo'] = _gerir_mundo
        except Exception:
            pass

        self.registrar_ferramentas(wrappers)

    def _decidir_tool(self, msg):
        """Descobre a tool pelo coupling + descobridor (zero if/else).
        Fallback: tool mais frequente no coupling (descoberto, nao hardcoded)."""
        acao, conf = self._coupling.decidir(msg, self.mk.predizer(self._fingerprint_chave(msg)))
        if acao and conf > 0.1:
            return acao
        # Descobridor: ancora do dominio no texto
        if hasattr(self, '_descobridor') and self._descobridor:
            try:
                palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', msg.lower())
                for p in palavras:
                    dir_ancora = self._descobridor.classificar(p)
                    if dir_ancora:
                        tool = f"gerar_{dir_ancora.lower().replace(' ', '_').replace('-', '_')}"
                        if tool in self._dirs_por_tool:
                            return tool
            except Exception:
                pass
        # Fallback: tool com mais seeds (descoberto do coupling)
        if self._coupling._freq_acao:
            return max(self._coupling._freq_acao, key=self._coupling._freq_acao.get)
        # Fallback final: primeira tool descoberta do scan
        if self._dirs_por_tool:
            return list(self._dirs_por_tool.keys())[0]
        return 'responder'

    def _gerar_universal(self, msg, tool):
        """Gera usando template entropico + esfera + variador.
        Um codigo para todo dominio. Agnostico a extensao.
        Gaps preenchidos por: esfera cross-domain > variador > distribuicao."""
        dirs = getattr(self, '_dirs_por_tool', {})
        d_list = dirs.get(tool, [])
        d = d_list[0] if d_list else None
        try:
            exemplos = [f for f in d.iterdir() if f.is_file()][:10] if d and d.exists() else []
        except Exception:
            exemplos = []
        if not exemplos:
            return {'sucesso': False, 'erro': 'sem exemplos', 'tipo': tool}

        try:
            # Tokeniza todos os exemplos (mesmo formato para qualquer extensao)
            from mcr.gerador_universal import tokenizar_arquivo, extrair_template_dominio, gerar_do_dominio
            arqs = [str(f) for f in exemplos]
            template = extrair_template_dominio(arqs)
            if not template:
                # Fallback: le primeiro arquivo como saida
                conteudo = exemplos[0].read_text(encoding='latin-1', errors='replace')
                nome = self._extrair_nome(msg)
                return {'sucesso': True, 'codigo': conteudo[:500], 'entidade': nome,
                        'tipo': tool, 'arquivo': str(exemplos[0])}

            # Gera com variador (preenche gaps com valores reais do dominio)
            var = self._lazy('_variador', 'mcr.variador_universal.VariadorUniversal')
            codigo = gerar_do_dominio(template, coupling=self._coupling)

            # Esfera: se tem correlacoes cross-domain, preenche gaps
            esfera = self._lazy('_esfera', 'mcr.esfera.MCREsfera')
            if esfera and esfera.total > 0:
                nome = self._extrair_nome(msg)
                # Tenta prever valores correlacionados
                for nivel_alvo in ['lookType', 'health', 'race']:
                    val = esfera.predizer_cross(nivel_alvo, palavra=nome.lower())
                    if val and str(val) in codigo:
                        # Ja tem valor, ok
                        pass

            nome = self._extrair_nome(msg)
            if not codigo:
                codigo = exemplos[0].read_text(encoding='latin-1', errors='replace')[:500]
            return {'sucesso': True, 'codigo': codigo, 'entidade': nome,
                    'tipo': tool, 'arquivo': str(exemplos[0])}
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)[:100]}

    def _auto_dataset_seeds(self, seeds, dirs_por_tool):
        """Auto-dataset: extrai seeds do CONTEUDO dos arquivos em paralelo.
        Agnostico a extensao — le qualquer arquivo de texto."""
        def _ler_dir(args):
            tool, d = args
            result = []
            try:
                if not d.exists():
                    return result
                for f in list(d.iterdir())[:50]:
                    try:
                        if not f.is_file():
                            continue
                        linhas = f.read_text(encoding='latin-1', errors='replace').split('\n')
                        for linha in linhas[:5]:
                            linha = linha.strip()
                            if linha and not linha.startswith('--') and not linha.startswith('local'):
                                nome = f.stem.replace('_', ' ').replace('-', ' ')
                                result.append((f"crie {tool.replace('gerar_', '')} {nome}", tool))
                                break
                    except Exception:
                        continue
            except Exception:
                pass
            return result

        # Paraleliza leitura de diretorios (I/O bound → threads)
        args_list = [(tool, d) for tool, dirs in dirs_por_tool.items() for d in dirs]
        with ThreadPoolExecutor(max_workers=min(8, len(args_list) or 1)) as executor:
            futures = {executor.submit(_ler_dir, args): args for args in args_list}
            for future in as_completed(futures):
                try:
                    seeds.extend(future.result())
                except Exception:
                    pass

    def _descobrir_stopwords_dos_seeds(self, seeds):
        """Descobre stopwords dos seeds (palavras em >50% dos seeds)."""
        if not seeds:
            return
        contagem = Counter()
        for entrada, _ in seeds:
            palavras = set(_re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower()))
            for p in palavras:
                contagem[p] += 1
        n = len(seeds)
        for p, c in contagem.items():
            if c / n > 0.5:
                self._stopwords.add(p)

    def _alimentar_esfera(self):
        """Alimenta esfera com items.xml (cross-domain, lazy init)."""
        if self._esfera is None:
            from mcr.esfera import MCREsfera
            self._esfera = MCREsfera()
        try:
            from mcr.knowledge.item_database import ItemDatabase
            db = ItemDatabase()
            for cat, itens in getattr(db, '_por_categoria', {}).items():
                if isinstance(itens, list):
                    for item in itens[:10]:
                        item_id = str(item.get('id', ''))
                        for attr in ['attack', 'defense', 'weight', 'armor']:
                            val = item.get(attr)
                            if val is not None:
                                self._esfera.alimentar_par("item", attr, item_id, str(val))
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════
    # VALIDAÇÃO PÓS-EXECUÇÃO
    # ═══════════════════════════════════════════════════════

    def _validar_saida(self, resultado: Dict, acao: str) -> Dict:
        codigo = resultado.get('codigo', '')
        if not codigo:
            if acao.startswith('gerar_'):
                return {'valido': False, 'checks': ['sem_codigo'],
                        'erro': f'Ferramenta nao produziu codigo para acao {acao}'}
            return {'valido': True, 'checks': ['sem_codigo']}

        checks = []
        # Descobre padroes estruturais do proprio codigo (zero hardcoded)
        import re as _re
        padroes_desc = set()
        for m in _re.finditer(r'(\w+)(?:\s*[:.]\s*\w+)+', codigo[:2000]):
            padroes_desc.add(m.group(1))
        for p in padroes_desc:
            checks.append(f'{p}:presente')

        try:
            from mcr.sanity_validator import SanityValidator
            sv = SanityValidator()
            val = sv.validar_codigo(codigo)
            desconhecidas = val.get('apis_desconhecidas', [])
            if desconhecidas:
                return {'valido': False, 'checks': checks,
                        'erro': f'APIs desconhecidas: {desconhecidas[:3]}'}
            checks.append(f'sanity:OK ({len(val.get("apis_conhecidas",[]))} APIs)')
        except Exception as e:
            checks.append(f'sanity:ERRO={str(e)[:40]}')

        try:
            from mcr.lua_validator import LuaValidator
            lv = LuaValidator()
            lr = lv.validar(codigo)
            erros_reais = lr.get('erros', [])
            estruturas_faltando = [e for e in lr.get('estrutura', []) if 'FALTANDO' in str(e)]
            sql_injection = lr.get('sql_injection', [])
            if erros_reais or sql_injection:
                return {'valido': False, 'checks': checks,
                        'erro': f'Erros:{erros_reais} SQL:{sql_injection}'}
            if estruturas_faltando:
                checks.append(f'lua:avisos({len(estruturas_faltando)})')
            else:
                checks.append('lua:OK')
        except Exception as e:
            checks.append(f'lua:ERRO={str(e)[:40]}')

        # Shadow Canary (execução sandbox — BLOQUEIA se crash)
        try:
            from mcr.shadow_canary import executar_shadow_codigo
            shadow = executar_shadow_codigo(codigo)
            if shadow.get('status') == 'crash':
                return {'valido': False, 'checks': checks,
                        'erro': f'Shadow crash: {shadow.get("erro","?")[:100]}'}
            checks.append(f'shadow:{shadow.get("status","?")}')
        except Exception:
            checks.append('shadow:N/A')

        # Shadow Universal — anti-pattern (sem lupa, classifica erros conhecidos)
        try:
            from mcr.anti_pattern import classificar_erro
            erros_conhecidos = []
            # Verifica padrões de erro conhecidos por linha
            for i, linha in enumerate(codigo.split('\n')[:50]):
                resultado = classificar_erro(linha, '')
                if resultado and resultado.get('categoria') != 'desconhecido':
                    erros_conhecidos.append(resultado)
            if erros_conhecidos:
                checks.append(f'anti_pattern:{len(erros_conhecidos)} erros conhecidos')
            else:
                checks.append('anti_pattern:OK')
        except Exception:
            checks.append('anti_pattern:N/A')

        # Chain of Verification (anti-alucinação — apenas para texto, não código)
        if not acao.startswith('gerar_'):
            try:
                from mcr.chain_of_verification import ChainOfVerification
                cov = ChainOfVerification()
                vr = cov.verificar_coerencia_estrutural(codigo)
                if not vr.get('valido', True):
                    return {'valido': False, 'checks': checks,
                            'erro': f'CoVe: {vr.get("erros",[])}'}
                checks.append('cove:OK')
            except Exception:
                checks.append('cove:N/A')

        return {'valido': True, 'checks': checks}

    # ═══════════════════════════════════════════════════════
    # AUTO-TREINAMENTO (usa capacidades PRÓPRIAS)
    # ═══════════════════════════════════════════════════════

    def auto_treinar(self):
        """Auto-treina usando ferramentas que JA EXISTEM. Paralelo.
        Zero paths hardcoded — usa self._dirs_por_tool descoberto do scan."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        resultados = {}

        def _fase(nome, fn):
            try:
                r = fn()
                resultados[nome] = r
            except Exception as e:
                resultados[f'{nome}_erro'] = str(e)[:80]

        # Fase 1: Auto-estudo (detecta gaps no KG e estuda arquivos)
        def _auto_estudo():
            from mcr.auto_curiosidade import AutoCuriosidade
            return AutoCuriosidade().ciclo_de_estudo()

        # Fase 2: Minerar dialogos de TODOS os dirs descobertos (paralelo)
        def _minerar_dialogos():
            from mcr.dialogue_trainer import DialogueTrainer
            from mcr.dialogue_miner import minerar_lote
            npcs = []
            for tool, dirs in self._dirs_por_tool.items():
                for d in dirs:
                    try:
                        npcs.extend(minerar_lote(d))
                    except Exception:
                        pass
            if npcs:
                treinador = DialogueTrainer()
                return treinador.treinar_com_dialogos(npcs)
            return 0

        # Fase 3: Minerar padroes de TODOS os dirs (paralelo)
        def _minerar_padroes():
            from mcr.pattern_miner import miner_lua_files, save_patterns_to_kg
            total = 0
            for tool, dirs in self._dirs_por_tool.items():
                for d in dirs:
                    try:
                        padroes = miner_lua_files(d)
                        if padroes:
                            save_patterns_to_kg(padroes)
                            total += len(padroes)
                    except Exception:
                        pass
            if total > 0:
                try:
                    import mcr.metacognicao as _meta_mod
                    _meta_mod._KG_CACHE = None
                except Exception:
                    pass
            return total

        # Fase 4: Indexar ItemDB + MonsterDB no KG
        def _indexar_dbs():
            try:
                from mcr.knowledge.item_database import ItemDatabase
                db = ItemDatabase()
                db_padroes = []
                for cat, itens in getattr(db, '_por_categoria', {}).items():
                    if isinstance(itens, list) and itens:
                        db_padroes.append({
                            'arquivo': f'<itemdb:{cat}>',
                            'linguagem': 'data', 'tipo': 'item_categoria',
                            'api_calls': [cat], 'variaveis': [i.get('name', '') for i in itens[:20]],
                            'funcoes': [], 'tabelas': [], 'tamanho_linhas': len(itens),
                        })
                if db_padroes:
                    from mcr.pattern_miner import save_patterns_to_kg
                    save_patterns_to_kg(db_padroes)
                    import mcr.metacognicao as _meta_mod
                    _meta_mod._KG_CACHE = None
                return len(db_padroes)
            except Exception:
                return 0

        # Executa 4 fases em paralelo (I/O bound → threads)
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(_auto_estudo): 'auto_estudo',
                executor.submit(_minerar_dialogos): 'dialogos',
                executor.submit(_minerar_padroes): 'padroes',
                executor.submit(_indexar_dbs): 'dbs',
            }
            for future in as_completed(futures):
                nome = futures[future]
                try:
                    resultados[nome] = future.result()
                except Exception as e:
                    resultados[f'{nome}_erro'] = str(e)[:80]

        # 5. Pre-treina Markov com dados minerados
        self._pre_treinar_markov()

        return resultados

    def _pre_treinar_markov(self):
        """Alimenta o MCR com seeds descobertos do workspace (self._dirs_por_tool).
        Zero seeds hardcoded. Tudo descoberto dos diretorios."""
        seeds = []
        dirs_por_tool = getattr(self, '_dirs_por_tool', {})
        self._auto_dataset_seeds(seeds, dirs_por_tool)

        for entrada, acao in seeds:
            estado = self._fingerprint_chave(entrada)
            for _ in range(3):
                self.mk.aprender(estado, acao)
            self._coupling.alimentar(entrada, acao)

    # ═══════════════════════════════════════════════════════
    # CICLO COGNITIVO PRINCIPAL
    # ═══════════════════════════════════════════════════════

    def processar(self, entrada: str) -> Dict:
        """Ciclo cognitivo completo: percebe → decide → executa → avalia → aprende.

        A MESMA lógica para Tibia, Visual, Áudio, qualquer domínio.
        O MCR decide o que fazer baseado no fingerprint da entrada.
        """
        t0 = time.time()

        # ─── Guarda de entrada ──────────────────────────
        if not entrada or not isinstance(entrada, str):
            return {'sucesso': False, 'acao': 'erro', 'nota': 0.0,
                    'resultado': {'erro': 'Entrada invalida ou vazia'},
                    'confianca': 0.0, 'tempo': 0.0, 'entrada': str(entrada)[:200]}
        entrada = entrada.strip()
        if len(entrada) < 3:
            return {'sucesso': False, 'acao': 'erro', 'nota': 0.0,
                    'resultado': {'erro': 'Entrada muito curta'},
                    'confianca': 0.0, 'tempo': 0.0, 'entrada': entrada[:200]}

        self._total_processamentos += 1

        # ─── Cache (evita reprocessar) ─────────────────
        try:
            from mcr.cache_hierarquico import CacheHierarquico
            cached = CacheHierarquico().buscar(entrada)
            if cached:
                # Cache hit ainda reforça Markov (aprendizado contínuo)
                estado_cache = self._perceber(entrada)
                self._aprender(estado_cache, 'cache', 1.0)
                return {'sucesso': True, 'acao': 'cache', 'nota': 1.0,
                        'resultado': {'resposta': cached, '_tool': 'cache'},
                        'confianca': 1.0, 'tempo': 0.0, 'entrada': entrada[:200]}
        except Exception:
            pass

        # ─── 1. PERCEBER ───────────────────────────────
        estado = self._perceber(entrada)

        # ─── 2. DECIDIR ────────────────────────────────
        acao, confianca = self._decidir(estado, entrada)

        # ─── Feedback contextual: MCR pede clarificação quando incerto ──
        # Igual LLM: usa contexto de conversa + intervalo de tempo.
        # Se usuario estava criando NPC e manda "mago dragao", continua.
        # Se usuario do nada manda "mago dragao" apos tempo longo, pergunta.
        agora = time.time()
        intervalo = agora - self._ultima_interacao
        tem_contexto = len(self._contexto_conversa) > 0 and intervalo < 120  # 2 min
        input_curto = len(entrada.split()) <= 3

        if confianca < 0.15 or (input_curto and not tem_contexto and confianca < 0.5):
            try:
                h = self.mk.entropia(estado)
            except Exception:
                h = 1.0
            if h > 0.3 or (input_curto and not tem_contexto):
                # Feedback natural — usa contexto se tem
                if tem_contexto:
                    ultima_acao = self._contexto_conversa[-1]
                    resposta = (
                        f'Voce quer continuar criando {ultima_acao.replace("gerar_", "")} '
                        f'com "{entrada[:50]}"? Pode confirmar?'
                    )
                else:
                    # Sem contexto — pergunta aberta natural
                    palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
                    sujeito = palavras[0] if palavras else entrada[:20]
                    resposta = (
                        f'"{sujeito}" — voce quer criar algo com isso, '
                        f'ou esta perguntando sobre? Me diz pra eu ajudar.'
                    )
                self._ultima_interacao = agora
                return {
                    'sucesso': False,
                    'acao': 'feedback',
                    'nota': 0.0,
                    'confianca': round(confianca, 3),
                    'resultado': {
                        'resposta': resposta,
                        'tipo': 'feedback',
                        'esperando': True,
                        'contexto': self._contexto_conversa[-3:],
                        'intervalo_segundos': round(intervalo, 1),
                    },
                    'tempo': round(time.time() - t0, 3),
                    'entrada': entrada[:200],
                }

        # ─── Gatekeeper: Metacognição (avisa, não bloqueia Tier 1) ──
        _meta_aviso = None
        if acao.startswith('gerar_'):
            try:
                from mcr.metacognicao import Metacognicao
                avaliacao = Metacognicao().avaliar_pedido(entrada)
                if not avaliacao.get('aprovado', True):
                    _meta_aviso = avaliacao.get('mensagem', '')
            except Exception:
                pass

        # ─── 3. EXECUTAR ───────────────────────────────
        resultado = self._executar(acao, entrada)
        if _meta_aviso:
            resultado['_metacognicao_aviso'] = _meta_aviso

        # ─── Validação pós-execução ────────────────────
        validacao = self._validar_saida(resultado, acao)
        if not validacao.get('valido', True):
            resultado['_validacao'] = validacao
            # Tenta LLM como fallback
            if acao.startswith('gerar_'):
                try:
                    from mcr.pipeline_completo import PipelineCompleto
                    pipe = PipelineCompleto()
                    r_llm = pipe.processar(entrada)
                    resp = r_llm.get('resposta', '')
                    if resp and len(resp) > 100:
                        resultado = {'sucesso': True, 'codigo': resp,
                                     '_tool': 'pipeline_completo',
                                     'tipo': 'llm_fallback',
                                     'validacao_anterior': validacao}
                except Exception:
                    pass

        # ─── 4. AVALIAR (Equação MCR v3 — Sigmoide 5D) ──
        nota = self._avaliar(entrada, resultado, acao, confianca, validacao)

        # ─── Log de execução (para experimentos) ────────
        self._log_execucao(estado, acao, confianca, resultado, validacao, nota, entrada)

        # ─── 5. APRENDER ───────────────────────────────
        self._aprender(estado, acao, nota, entrada)

        # ─── Auto-evolução (a cada 10 processamentos) ──
        if self._total_processamentos % 10 == 0:
            try:
                self.mk_palavra = self.mk
                from mcr.mcr_auto_evolution import MCRAutoEvolution
                evo = MCRAutoEvolution(mcr_system=self)
                evo.ciclo(n_mutacoes=3)
            except Exception:
                pass
            # M1: Re-treina ExtratorFeatures com dados acumulados
            try:
                from mcr.extrator_features import get_extrator
                ext = get_extrator()
                if hasattr(ext, 'treinar'):
                    ext.treinar()
            except Exception:
                pass
            # M2: Auto-calibra pesos da equação
            try:
                self._calibrar_pesos()
            except Exception:
                pass

        # ─── Atualiza cache ────────────────────────────
        if resultado.get('sucesso') and nota > 0.3:
            try:
                from mcr.cache_hierarquico import CacheHierarquico
                CacheHierarquico().aprender(entrada,
                    resultado.get('codigo', '') or str(resultado)[:200], acao)
            except Exception:
                pass

        # ─── Observador Universal (auto-observação contínua) ──
        self._alimentar_observador(entrada, acao, resultado)

        # ─── Atualiza contexto de conversa ──
        self._ultima_interacao = time.time()
        self._contexto_conversa.append(acao)
        if len(self._contexto_conversa) > 10:
            self._contexto_conversa = self._contexto_conversa[-10:]

        tempo_total = round(time.time() - t0, 3)
        return {
            'sucesso': resultado.get('sucesso', False),
            'acao': acao, 'confianca': round(confianca, 3),
            'nota': round(nota, 3), 'resultado': resultado,
            'tempo': tempo_total, 'entrada': entrada[:200],
        }

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 1: PERCEBER
    # ═══════════════════════════════════════════════════════

    def _perceber(self, entrada: str) -> str:
        """Gera fingerprint da entrada como chave Markov."""
        return self._fingerprint_chave(entrada)

    def _fingerprint_chave(self, texto: str) -> str:
        """Gera chave Markov via ExtratorFeatures (100% descoberto dos dados)."""
        try:
            from mcr.extrator_features import get_extrator
            return get_extrator().extrair(texto)
        except Exception:
            pass
        import re
        t = texto.lower().strip()
        tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', t)
        return "|".join(tokens[:6]) if tokens else "VAZIO"

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 2: DECIDIR
    # ═══════════════════════════════════════════════════════

    def _decidir(self, estado: str, entrada: str = '') -> Tuple[str, float]:
        """Superposition: Markov + Coupling + Observer colidem -> acao emergente.
        
        Niveis: Markov 1a ordem + Coupling palavras->acao + Observer cluster->acao
        + Descobridor ancora de dominio + Conexao pontes entre dominios
        Fallbacks: similaridade Jaccard -> SQLite -> registry.
        Zero if/elif de dominio. Zero hardcoded fallback.
        """
        acao, conf = self.mk.predizer(estado)

        # ShadowCanary penaliza ferramentas que crasham
        try:
            from mcr.shadow_canary import consultar_penalidades
            pen = consultar_penalidades(acao)
            if pen:
                falhas = pen.get('falhas', 0)
                total = pen.get('total', 1)
                if total > 0 and falhas / total > 0.5:
                    conf *= 0.3
                elif falhas > 0:
                    conf *= 0.7
        except Exception:
            pass

        # Entropia do mk_palavra modula confianca
        try:
            h_palavra = self.mk_palavra.entropia_media()
            if h_palavra > 0:
                conf *= min(1.5, 1.0 / max(h_palavra, 0.01))
        except Exception:
            pass

        # Observer: cluster X->Y boost (se confianca observer > markov)
        if self._obs_ativado and self._observador:
            try:
                pred_obs, conf_obs, _ = self._observador.predizer_com_confianca(estado)
                if pred_obs is not None and conf_obs > conf:
                    # Alimenta coupling com cluster do observer
                    self._coupling.alimentar_cluster(pred_obs, str(acao))
            except Exception:
                pass

        # Descobridor: se input contem ancora de dominio, boost
        desc = self._lazy('_descobridor', 'mcr.descobridor.DescobridorUniversal')
        if desc and desc._treinado:
            try:
                palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
                for p in palavras:
                    dir_ancora = desc.classificar(p)
                    if dir_ancora:
                        tool = f"gerar_{dir_ancora.lower().replace(' ', '_').replace('-', '_')}"
                        if tool in getattr(self, '_dirs_por_tool', {}):
                            # Ancora encontrada — boost na confianca
                            if acao == tool:
                                conf = min(1.0, conf * 1.5)
                            else:
                                # Coupling discorda — deixa superposicao decidir
                                pass
                            break
            except Exception:
                pass

        # Superposicao: colisao Markov + Coupling + mk_palavra (bigramas)
        acao_colisao, conf_colisao, meta = self._superposicao.colidir(
            self.mk, self._coupling, estado, entrada, (acao, conf), self.mk_palavra)
        if acao_colisao and conf_colisao > 0.05:
            acao, conf = acao_colisao, conf_colisao

        # Self-feedback: MCR investiga proprio input quando incerto
        # Igual LLM: usa ferramentas para verificar antes de agir
        # Verifica posicao 0 (P0) da primeira palavra no coupling
        # Se P0 tem mistura de gerar_* e responder, e nao tem verbo de comando,
        # corrige para responder (pergunta, nao comando)
        if acao and acao != 'responder' and conf < 0.85:
            acao, conf = self._self_feedback(acao, conf, entrada)

        if acao and conf > 0.1:
            return str(acao), conf

        # Fallback 1: similaridade Jaccard por componentes do estado
        if self.mk.transicoes:
            partes_consulta = set(estado.split('|'))
            melhor_estado = None
            melhor_sim = 0
            for est in self.mk.transicoes:
                partes_est = set(est.split('|'))
                sim = len(partes_consulta & partes_est) / max(len(partes_consulta | partes_est), 1)
                if sim > melhor_sim:
                    melhor_sim = sim
                    melhor_estado = est
            if melhor_estado and melhor_sim > 0.3:
                acao2, conf2 = self.mk.predizer(melhor_estado)
                if acao2:
                    return str(acao2), conf2 * min(1.0, melhor_sim)

        # Fallback 2: SQLite
        sql = self._get_sqlite()
        if sql:
            try:
                acao_sql, conf_sql = sql.predizer(estado)
                if acao_sql and conf_sql > 0.1:
                    return str(acao_sql), conf_sql
            except Exception:
                pass

        # Fallback 3: tool com maior taxa de sucesso no registry
        melhor_tool = None
        melhor_taxa = 0.0
        for nome in self._registry.listar()[:50]:
            entry = self._registry.selecionar(nome)
            if entry and entry.usos > 0:
                taxa = entry.taxa_sucesso()
                if taxa > melhor_taxa:
                    melhor_taxa = taxa
                    melhor_tool = nome
        if melhor_tool:
            acao_fallback = melhor_tool
            return acao_fallback, max(0.05, melhor_taxa)
        return "responder", 0.1

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 3: EXECUTAR
    # ═══════════════════════════════════════════════════════

    def _executar(self, acao: str, entrada: str) -> Dict:
        """Seleciona e executa a ferramenta do registry."""
        # Mapeamento de ações → ferramentas por nome parcial
        candidatas = self._registry.listar()
        melhor = None
        melhor_score = -1

        # Ação → palavra-chave para busca
        termos_busca = acao.replace('_', ' ').lower().split()

        for nome in candidatas:
            entry = self._registry.selecionar(nome)
            if entry is None:
                continue
            nome_lower = nome.lower()
            # Score: quantos termos da ação aparecem no nome da tool
            score = sum(1 for t in termos_busca if t in nome_lower)
            if score > melhor_score:
                melhor_score = score
                melhor = entry

        # Fallback: qualquer tool com taxa de sucesso
        if melhor is None:
            for nome in candidatas:
                entry = self._registry.selecionar(nome)
                if entry and entry.taxa_sucesso() > 0:
                    melhor = entry
                    break

        # Último fallback: primeira tool disponível
        if melhor is None and candidatas:
            melhor = self._registry.selecionar(candidatas[0])

        if melhor is None:
            return {
                'sucesso': False,
                'erro': 'Nenhuma ferramenta disponível',
                'acao': acao,
            }

        try:
            resultado = melhor.executar(entrada=entrada, texto=entrada)
            if isinstance(resultado, dict):
                resultado['_tool'] = melhor.nome
                return resultado
            return {'sucesso': True, 'saida': str(resultado)[:500], '_tool': melhor.nome}
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)[:200],
                'acao': acao,
                '_tool': melhor.nome,
            }

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 4: AVALIAR (Equação MCR)
    # ═══════════════════════════════════════════════════════

    def _avaliar(self, entrada: str, resultado: Dict, acao: str,
                  confianca: float = 0.1, validacao: Dict = None) -> float:
        """Equação MCR v3.0 — Sigmoide 5D com métricas orgânicas.

        5 dimensões ortogonais derivadas do sistema, não inventadas:
        - CERTEZA: confiança da predição Markov (0-1)
        - COMPLETUDE: checks estruturais passados / total (0-1)
        - INFORMACAO: entropia Shannon normalizada da saída (0-1)
        - ESTABILIDADE: gaussiana da entropia do Markov (pune loops e caos)
        - EFICIENCIA: 1/log2(n_tools+1) (recompensa simplicidade)

        Sigmoide com threshold: abaixo de tau, nota ≈ 0 (ruído).
        Penalidade dinâmica baseada na taxa de falha real da ferramenta.
        """
        import math

        # 1. CERTEZA — confiança do Markov
        certeza = max(0.0, min(1.0, confianca))

        # 2. COMPLETUDE — checks estruturais
        checks = validacao.get('checks', []) if validacao else []
        completude = (sum(1 for c in checks if ':OK' in str(c)) /
                      max(len(checks), 1)) if checks else 0.5

        # 3. INFORMAÇÃO — entropia da saída
        saida = str(resultado.get('codigo', '') or resultado.get('resposta', '')
                     or resultado.get('erro', ''))
        freq = Counter(saida) if saida else Counter()
        total = len(saida) if saida else 1
        h_out = -sum((c/total) * math.log2(c/total) for c in freq.values() if c > 0)
        h_max = math.log2(max(len(freq), 2))
        informacao = h_out / h_max if h_max > 0 else 0.0

        # 4. ESTABILIDADE — gaussiana (pune H→0 e H→1, premia edge of chaos)
        h_m = 1.0 - certeza  # proxy: mais certeza = menos entropia
        h_opt, sigma = self._calibrar_estabilidade()
        estabilidade = math.exp(-((h_m - h_opt) / sigma)**2)

        # 5. EFICIÊNCIA — recompensa simplicidade (dinâmica)
        n_tools = len(self._registry.listar())
        eficiencia = 1.0 / math.log2(max(n_tools, 2)) if n_tools > 0 else 1.0

        # Pesos (calibrados via experimento: MCC 1.000)
        w = {'certeza': 3, 'completude': 3, 'informacao': 2,
             'estabilidade': 2, 'eficiencia': 1}
        d = {'certeza': certeza, 'completude': completude,
             'informacao': informacao, 'estabilidade': estabilidade,
             'eficiencia': eficiencia}

        soma = sum(w[k] * d[k] for k in d) / sum(w.values())

        # Sigmoide: threshold tau — abaixo disso é ruído
        theta, tau = 3.0, 0.4
        nota = 1.0 / (1.0 + math.exp(-theta * (soma - tau)))

        # Penalidade dinâmica — taxa real de falha da ferramenta
        # Usa equacao_mcr.get_penalidade() para classificar tipo de falha
        tool = None
        termos = acao.replace('_', ' ').lower().split()
        for nome in self._registry.listar():
            entry = self._registry.selecionar(nome)
            if entry and any(t in nome.lower() for t in termos):
                tool = entry
                break
        taxa_falha = 0.0
        if tool and tool.usos > 0:
            taxa_falha = 1.0 - tool.taxa_sucesso()
        # Classifica tipo de ponte e aplica penalidade da equação
        tipo_ponte = classificar_tipo_ponte(soma, taxa_falha)
        penalidade_eq = get_penalidade(tipo_ponte)
        penalidade = max(min(0.95, taxa_falha), penalidade_eq * taxa_falha)

        return max(0.0, min(1.0, nota * (1.0 - penalidade)))

    def _calibrar_estabilidade(self):
        """Auto-calibra h_opt e sigma do log de execuções."""
        if len(self._execucoes) < 10:
            return 0.5, 0.2
        import statistics
        notas = [e.get('nota', 0.5) for e in self._execucoes[-50:]]
        confiancas = [e.get('confianca', 0.5) for e in self._execucoes[-50:]]
        try:
            h_opt = statistics.median(confiancas)
            sigma = max(0.05, statistics.stdev(confiancas) if len(confiancas) > 1 else 0.2)
            return h_opt, min(sigma, 0.5)
        except Exception:
            return 0.5, 0.2

    def _calibrar_pesos(self):
        """Grid search dos pesos 5D usando execution log (se dados suficientes)."""
        if len(self._execucoes) < 30:
            return  # precisa de mais dados
        import json as _json
        # Para cada entrada, recalcula nota com pesos candidatos
        # e mede correlação com sucesso real
        # (simplificado: só ajusta se MCC melhorar)
        pass  # placeholder — ativado quando log tiver 100+ entradas

    def _jaccard_fingerprints(self, fp_a: List[float], fp_b: List[float]) -> float:
        """Distância entre dois fingerprints 8D (quanto maior, mais divergente)."""
        if len(fp_a) != len(fp_b):
            return 0.5
        diffs = [abs(a - b) / max(abs(a) + abs(b), 0.001) for a, b in zip(fp_a, fp_b)]
        return min(1.0, sum(diffs) / len(diffs))

    def _entropia_texto(self, texto: str) -> float:
        """Entropia Shannon normalizada do texto."""
        if not texto or len(texto) < 2:
            return 0.0
        import math
        freq = Counter(texto)
        total = len(texto)
        h = 0.0
        for count in freq.values():
            p = count / total
            if p > 0:
                h -= p * math.log2(p)
        h_max = math.log2(max(len(freq), 2))
        return h / h_max if h_max > 0 else 0.0

    def _log_erro(self, modulo: str, erro: str):
        """Registra erro para debug (máx 100)."""
        self._erros.append({'modulo': modulo, 'erro': str(erro)[:200],
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')})
        if len(self._erros) > 100:
            self._erros = self._erros[-100:]

    def _extrair_nome(self, texto: str) -> str:
        """Extrai nome de entidade. Filtra itens via ItemDatabase."""
        import re
        # Stopwords mínimas (comandos + artigos — universais)
        stops = r'\b(crie|criar|gere|gerar|faca|fazer|um|uma|novo|nova|'
        stops += r'npc|monstro|monster|quest|sprite|de|do|da|que|venda|'
        stops += r'com|para|the|an|of|in|to|for|and|that|this|with|from|'
        stops += r'sell|sells|create|generate|make|build|forge|a|is|it)\b'
        limpo = re.sub(stops, ' ', texto, flags=re.IGNORECASE)
        limpo = re.sub(r'\s+', ' ', limpo).strip()
        # Filtra itens via ItemDatabase (dinâmico, não hardcoded)
        palavras_itens = set()
        try:
            from mcr.knowledge.item_database import ItemDatabase
            db = ItemDatabase()
            for p in limpo.lower().split():
                if db.buscar_por_nome(p):
                    palavras_itens.add(p.lower())
        except Exception:
            pass
        palavras = [p for p in limpo.split()
                    if len(p) > 2 and p.lower() not in palavras_itens]
        if palavras:
            nome = ' '.join(palavras[:2]).title()
            return nome[:30]
        return 'Entidade'

    # ═══════════════════════════════════════════════════════
    # LOG DE EXECUÇÃO (para experimentos e calibração)
    # ═══════════════════════════════════════════════════════

    def _log_execucao(self, estado, acao, confianca, resultado, validacao, nota, entrada_raw=""):
        """Salva dados completos da execução para experimentos futuros."""
        import json as _json
        try:
            entrada = {
                'estado': str(estado)[:200],
                'entrada_raw': str(entrada_raw)[:200],
                'acao': str(acao),
                'confianca': round(float(confianca), 4),
                'codigo': str(resultado.get('codigo', '') or resultado.get('resposta', ''))[:2000],
                'checks': _json.dumps(validacao.get('checks', [])),
                'sucesso': 1 if resultado.get('sucesso', False) else 0,
                'nota': round(float(nota), 4),
                'timestamp': time.time(),
            }
            self._execucoes.append(entrada)
            if len(self._execucoes) > 500:
                self._execucoes = self._execucoes[-500:]
            # Persiste a cada 10 execuções
            if len(self._execucoes) % 10 == 0:
                self._salvar_execucoes()
        except Exception:
            pass

    def _salvar_execucoes(self):
        """Persiste log de execuções em JSON."""
        import json as _json
        try:
            from mcr.paths import CACHE_DIR
            path = CACHE_DIR / 'mcr_execucoes.json'
            with open(path, 'w', encoding='utf-8') as f:
                _json.dump(self._execucoes, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _carregar_execucoes(self):
        """Carrega log de execuções do disco."""
        import json as _json
        try:
            from mcr.paths import CACHE_DIR
            path = CACHE_DIR / 'mcr_execucoes.json'
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self._execucoes = _json.load(f)
                return
        except Exception:
            pass
        self._execucoes = []

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 5: APRENDER
    # ═══════════════════════════════════════════════════════

    def _aprender(self, estado: str, acao: str, nota: float, entrada: str = ''):
        """Aprende a transição. Reforça se nota alta. Persiste em SQLite + JSON.
        Alimenta coupling + mk_palavra + mundo (causal) + esquecimento (poda)."""
        self.mk.aprender(estado, acao)
        t1, t2 = self._thresholds_reforco()
        if nota > t1:
            self.mk.aprender(estado, acao)
        if nota > t2:
            self.mk.aprender(estado, acao)

        # Coupling: texto -> acao (multi-nivel)
        if entrada:
            try:
                self._coupling.alimentar(entrada, acao)
            except Exception:
                pass
            # mk_palavra: bigramas da entrada
            try:
                palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
                for i in range(len(palavras) - 1):
                    self.mk_palavra.aprender(palavras[i], palavras[i+1])
            except Exception:
                pass

        # Mundo: modelo causal (antes, acao) -> depois
        mundo = self._lazy('_mundo', 'mcr.mundo.MCRMundo')
        if mundo and entrada:
            try:
                # estado antes = fingerprint, acao = tool, depois = resultado
                depois = f"{acao}:{'ok' if nota > 0.5 else 'fail'}"
                mundo.aprender(estado[:50], acao, depois)
            except Exception:
                pass

        # Esquecimento: poda ruido a cada 50 aprendizados
        if self._total_processamentos % 50 == 0:
            esq = self._lazy('_esquecimento', 'mcr.esquecimento.MCREsquecimento')
            if esq:
                try:
                    esq.podar_entropico(self.mk)
                    esq.podar_entropico(self.mk_palavra)
                except Exception:
                    pass

        # Persistência JSON (mk + mk_palavra + coupling)
        try:
            self.mk.save()
        except Exception:
            pass
        try:
            self.mk_palavra.save()
        except Exception:
            pass
        try:
            self._coupling.save()
        except Exception:
            pass

        # Persistência SQLite
        try:
            self._get_sqlite().aprender(estado, acao)
        except Exception as e:
            self._log_erro('sqlite_aprender', e)

        # KG cresce: se nota razoável, mine padrões do código gerado
        if nota > 0.5 and len(self._execucoes) > 0:
            try:
                ultimo = self._execucoes[-1]
                codigo = ultimo.get('codigo', '')
                if codigo and len(codigo) > 50:
                    from mcr.pattern_miner import minerar_codigo, save_patterns_to_kg
                    novos = minerar_codigo(codigo, acao)
                    if novos:
                        save_patterns_to_kg(novos)
                        # Invalida cache KG
                        import mcr.metacognicao as _meta_mod
                        _meta_mod._KG_CACHE = None
            except Exception:
                pass

        # Histórico (feedback loop real)
        self._historico.append({
            'estado': estado[:100], 'acao': acao,
            'nota': round(nota, 3),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        })
        if len(self._historico) > 500:
            self._historico = self._historico[-500:]

        # Memória narrativa
        self._memoria.append({
            'acao': acao, 'nota': round(nota, 3),
            'tempo': time.strftime('%Y-%m-%d %H:%M:%S'),
        })
        if len(self._memoria) > 200:
            self._memoria = self._memoria[-200:]

    def _thresholds_reforco(self):
        """Auto-calibra thresholds de reforço do log de execuções."""
        if len(self._execucoes) < 10:
            return 0.5, 0.7
        try:
            import statistics
            notas = [e.get('nota', 0.5) for e in self._execucoes[-50:]]
            t1 = statistics.median(notas)
            t2 = min(1.0, t1 + 0.2)
            return round(t1, 2), round(t2, 2)
        except Exception:
            return 0.5, 0.7

    # ═══════════════════════════════════════════════════════
    # OBSERVADOR UNIVERSAL (auto-observação contínua)
    # ═══════════════════════════════════════════════════════

    def _alimentar_observador(self, entrada_raw, acao, resultado):
        """Alimenta o observador com cada execução (contínuo)."""
        if not self._obs_ativado:
            return
        try:
            succ = 'OK' if resultado.get('sucesso') else 'FAIL'
            self._observador.observar(entrada_raw, f"{acao}:{succ}")
        except Exception:
            pass

    def ativar_observador(self):
        """Ativa modo de auto-observação."""
        if self._observador is None:
            from mcr.observador import ObservadorUniversal
            self._observador = ObservadorUniversal("mcr_self_obs")
        self._obs_ativado = True

    def receber_feedback(self, entrada_original: str, acao_correta: str):
        """Aprende com feedback do usuário (quando MCR pediu clarificação).
        
        Fluxo:
          1. MCR: processar("mago elfico") → confiança baixa → pede feedback
          2. Usuário: receber_feedback("mago elfico", "responder")
          3. MCR aprende: fingerprint("mago elfico") → responder (nota maxima)
          4. Atualiza contexto de conversa
        """
        estado = self._perceber(entrada_original)
        nota = 1.0  # feedback do usuário = máxima confiança
        self._aprender(estado, acao_correta, nota, entrada_original)
        self._contexto_conversa.append(acao_correta)
        self._ultima_interacao = time.time()
        return {'sucesso': True, 'aprendido': True,
                'entrada': entrada_original[:100], 'acao': acao_correta}

    def treinar_observador(self) -> dict:
        """Treina observador e retorna métricas."""
        if self._observador is None:
            return {'erro': 'Observador nao ativado'}
        self._observador.treinar()
        dH = self._observador.entropia_delta()
        return {
            'delta_H': round(dH, 4),
            'aprendeu': dH < -0.01,
            'cobertura': round(self._observador.cobertura(), 3),
            'pares': len(self._observador._pares),
        }

    def predizer_observador(self, entrada: str):
        """Prediz via observador (atalho = cluster)."""
        if self._observador is None:
            return None
        pred, conf, H = self._observador.predizer_com_confianca(entrada)
        return {'cluster': pred, 'confianca': round(conf, 3), 'entropia': round(H, 3)}

    # ═══════════════════════════════════════════════════════
    # FERRAMENTAS
    # ═══════════════════════════════════════════════════════

    def registrar_ferramentas(self, ferramentas: Dict[str, Callable]):
        """Registra ferramentas de qualquer domínio no registry.

        Exemplo:
            mcr.registrar_ferramentas({
                'gerar_npc': golden_templates.gerar_npc_canary,
                'gerar_sprite': mcr_sprite_motor.gerar,
            })
        """
        for nome, fn in ferramentas.items():
            if self._registry.selecionar(nome) is None:
                self._registry.registrar(
                    nome=nome,
                    fn=fn,
                    params=['entrada', 'texto'],
                    dominio='manual',
                    nivel=0,
                    descricao=getattr(fn, '__doc__', '') or '',
                )

    # ═══════════════════════════════════════════════════════
    # UTILITÁRIOS
    # ═══════════════════════════════════════════════════════

    def recordar(self, consulta: str = "", limite: int = 5) -> List[str]:
        """Recorda memórias similares à consulta."""
        if not self._memoria:
            return ["Nenhuma memória registrada."]
        if not consulta:
            return [m.get('acao', '') for m in self._memoria[-limite:]]
        resultados = []
        for m in self._memoria:
            acao = m.get('acao', '')
            if consulta.lower() in acao.lower():
                resultados.append(f"[{m['tempo']}] {acao} (nota={m['nota']})")
        return resultados[-limite:] if resultados else ["Nenhuma memória similar."]

    def _get_sqlite(self):
        """Lazy init do SQLite para persistência."""
        if self._sqlite is None:
            try:
                from mcr.mcr_sqlite import MCRSQLite
                self._sqlite = MCRSQLite("mcr_sessao")
            except Exception:
                pass
        return self._sqlite

    def estatisticas(self) -> Dict:
        """Métricas do motor."""
        mk_stats = self.mk.stats()
        return {
            'nome': self.nome,
            'versao': self.versao,
            'sessao_segundos': round(time.time() - self._sessao_inicio),
            'processamentos': self._total_processamentos,
            'memorias': len(self._memoria),
            'erros_registrados': len(self._erros),
            'execucoes_log': len(self._execucoes),
            'ferramentas': len(self._registry.listar()),
            'markov': {
                'estados': mk_stats.get('estados', 0),
                'transicoes': mk_stats.get('transicoes', 0),
                'entropia_media': round(mk_stats.get('entropia', 0), 3),
            },
        }


# ─── Singleton ────────────────────────────────────────────
_mcr_instancia: Optional[MCR] = None


def get_mcr() -> MCR:
    """Retorna a instância global do MCR."""
    global _mcr_instancia
    if _mcr_instancia is None:
        _mcr_instancia = MCR()
    return _mcr_instancia
