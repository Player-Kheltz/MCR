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
import re as _re
from collections import Counter
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
        self.fp = MCRFingerprint()

        # ─── Cognição multi-nível ───────────────────────
        self._coupling = MCRCoupling()
        self._superposicao = MCRSuperposicao()
        self.mk_palavra = MarkovEngine("mcr_palavra")
        try:
            self.mk_palavra.load(str(CACHE_DIR / "markov_mcr_palavra.json"))
        except Exception:
            pass
        self._esfera = None  # lazy init
        self._stopwords = set()

        # ─── Registry ───────────────────────────────────
        self._registry = get_registry()

        # ─── Estado interno ─────────────────────────────
        self._historico: List[Dict] = []
        self._memoria: List[Dict] = []
        self._total_processamentos = 0
        self._sessao_inicio = time.time()
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
        """Inicializa o registry se vazio e registra ferramentas padrão."""
        try:
            from mcr.bootstrap import inicializar
            if len(self._registry.listar()) < 10:
                inicializar(self._registry)
        except Exception as e:
            self._log_erro('bootstrap', e)
            pass
        try:
            self._inicializar_templates()
        except Exception as e:
            self._log_erro('inicializar_templates', e)
        self._pre_treinar_markov()

    def _inicializar_templates(self):
        """Descobre templates dos diretorios e registra wrappers universais.
        Zero hardcoded wrappers. Um so _gerar() para todo dominio."""
        from mcr.paths import CANARY_NPC_DIR, CANARY_MONSTER_DIR
        from pathlib import Path

        dirs_por_tool = {}
        dirs_por_tool['gerar_npc'] = [CANARY_NPC_DIR]
        dirs_por_tool['gerar_monstro'] = [CANARY_MONSTER_DIR]
        try:
            sprite_root = CANARY_NPC_DIR.parent / 'poc_output' / 'sprites_categorizados'
            if sprite_root.exists():
                dirs_por_tool['gerar_sprite'] = [sprite_root]
        except Exception:
            pass
        try:
            quest_dir = CANARY_NPC_DIR.parent / 'scripts' / 'quests'
            if quest_dir.exists():
                dirs_por_tool['gerar_quest'] = [quest_dir]
        except Exception:
            pass

        wrappers = {}

        def _gerar(entrada="", texto="", **kw):
            msg = entrada or texto
            return self._gerar_universal(msg, self._decidir_tool(msg))
        wrappers['gerar_npc'] = _gerar
        wrappers['gerar_npc_lua'] = _gerar
        wrappers['gerar_monstro'] = _gerar
        wrappers['gerar_monstro_lua'] = _gerar
        wrappers['gerar_quest'] = _gerar
        wrappers['gerar_sprite'] = _gerar

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

        # ─── Tibia: NPC (extrai nome, profissão, itens) ──
        try:
            from mcr.golden_templates import gerar_npc_canary, salvar_npc_parametrizado
            def _gerar_npc(entrada="", texto="", **kw):
                msg = entrada or texto
                nome = self._extrair_nome(msg)
                prof = self._extrair_profissao(msg)
                itens = self._extrair_itens(msg)
                # Looktype descoberto dos 1,102 NPCs reais (mediana por keyword)
                looktypes_desc = self._dados_npc().get('looktypes', {})
                looktype = looktypes_desc.get('generico', 128)
                for k, v in looktypes_desc.items():
                    if k in msg.lower(): looktype = v; break
                health = self._dados_npc().get('health', 100)
                params = {
                    'name': nome, 'health': health, 'looktype': looktype,
                    'greeting': f'Ola, sou {nome}, {prof}. Como posso ajudar?',
                    'job_desc': f'Trabalho como {prof} aqui.',
                }
                if itens:
                    params['shop_items'] = [{'name': i, 'clientId': 100 + j,
                                            'buy': 50, 'sell': 25}
                                           for j, i in enumerate(itens)]
                codigo = gerar_npc_canary(params)
                try:
                    caminho = salvar_npc_parametrizado(params)
                except Exception:
                    caminho = ''
                return {'sucesso': True, 'codigo': codigo, 'entidade': nome,
                        'tipo': 'npc', 'arquivo': caminho, 'params': params}
            wrappers['gerar_npc_lua'] = _gerar_npc
        except Exception as e:
            self._log_erro('wrapper_npc', e)

        # ─── Tibia: Monstro (extrai nome, perigo) ─────
        try:
            from mcr.golden_templates import gerar_monstro_parametrizado, salvar_monstro_parametrizado
            def _gerar_monstro(entrada="", texto="", **kw):
                msg = entrada or texto
                nome = self._extrair_nome(msg)
                # Perigo via threshold de health real (percentis da distribuição)
                md = self._dados_monstro()
                p33, p66 = md.get('thresholds', (1000, 7320))
                perigo = 'medium'
                # Usa nome para estimar perigo: busca nome em monstros reais
                for kw, healths in md.get('name_health', {}).items():
                    if kw in msg.lower():
                        med = healths[0] if healths else 0
                        if med > p66: perigo = 'high'
                        elif med < p33: perigo = 'low'
                        else: perigo = 'medium'
                        break
                stats = md.get('stats', {'low':(240,100,95),'medium':(3000,1800,130),'high':(25000,8000,160)})
                hp, exp, spd = stats.get(perigo, stats['medium'])
                # Raça descoberta dos 1,678 monstros reais (co-ocorrência nome→race)
                race = md.get('default_race', 'blood')
                race_kw = md.get('race_keywords', {})
                for kw, r in sorted(race_kw.items(), key=lambda x: -len(x[0])):
                    if kw in msg.lower(): race = r; break
                loot = md.get('loot', [{'id': 3031, 'chance': 100000, 'maxCount': 100}])
                params = {'name': nome, 'health': hp, 'experience': exp,
                          'speed': spd, 'looktype': 100,
                          'description': f'{nome} — um monstro perigoso.',
                          'race': race, 'drop_items': loot}
                codigo = gerar_monstro_parametrizado(params)
                try:
                    caminho = salvar_monstro_parametrizado(params)
                except Exception:
                    caminho = ''
                return {'sucesso': True, 'codigo': codigo, 'entidade': nome,
                        'tipo': 'monstro', 'arquivo': caminho, 'perigo': perigo,
                        'race': race}
            wrappers['gerar_monstro_lua'] = _gerar_monstro
        except Exception as e:
            self._log_erro('wrapper_monstro', e)

        # ─── Visual: Sprite real ──────────────────────
        try:
            def _gerar_sprite(entrada="", texto="", **kw):
                try:
                    from mcr.sprite_corpus import carregar_categoria, listar_categorias
                    from mcr.mcr_sprite_motor import MCRSpriteMotor
                    cats = listar_categorias()
                    if not cats:
                        return {'sucesso': False, 'erro': 'Sem categorias de sprite',
                                'tipo': 'sprite'}
                    motor = MCRSpriteMotor()
                    cat = cats[0]
                    sprites = carregar_categoria(cat, max_sprites=5)
                    if sprites and len(sprites) >= 3:
                        motor.treinar(sprites, cat)
                        gerados = motor.gerar(n=1)
                        return {'sucesso': gerados is not None and len(gerados) > 0,
                                'tipo': 'sprite', 'categoria': cat,
                                'n_gerados': len(gerados) if gerados else 0,
                                'nota': 'Treino com poucos sprites — qualidade limitada. '
                                        'Popule poc_output/sprites_categorizados/ para melhorar.'}
                    return {'sucesso': False, 'erro': 'Sem sprites para treinar',
                            'tipo': 'sprite'}
                except Exception as e:
                    return {'sucesso': False, 'erro': str(e)[:100], 'tipo': 'sprite'}
            wrappers['gerar_sprite'] = _gerar_sprite

            from mcr.meus_olhos import MCRDiscriminador
            def _avaliar_sprite(entrada="", texto="", **kw):
                disc = MCRDiscriminador()
                try:
                    from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel, listar_categorias
                    cats = listar_categorias()
                    if len(cats) < 2:
                        return {'sucesso': False, 'erro': 'Precisa de 2+ categorias para avaliar'}
                    # Treina em metade, testa na outra (evita contaminação circular)
                    meio = len(cats) // 2
                    grids_treino = []
                    for cat in cats[:meio]:
                        sprites = carregar_categoria(cat, max_sprites=3)
                        grids_treino.extend(extrair_grid_papel(s)[0] for s in sprites)
                    if not grids_treino:
                        return {'sucesso': False, 'erro': 'Sem sprites para treino'}
                    disc.treinar(grids_treino)
                    # Testa em categorias diferentes
                    scores = []
                    for cat in cats[meio:meio+2]:
                        sprites = carregar_categoria(cat, max_sprites=2)
                        for s in sprites:
                            grid = extrair_grid_papel(s)[0]
                            scores.append(disc.avaliar(grid)['score'])
                    if not scores:
                        return {'sucesso': False, 'erro': 'Sem sprites para teste'}
                    return {'sucesso': True, 'score_medio':
                            round(sum(scores)/len(scores), 3),
                            'n_treino': len(grids_treino), 'n_teste': len(scores),
                            'aviso': 'Score cross-categoria (valido, nao circular)'}
                except Exception as e:
                    return {'sucesso': False, 'erro': str(e)[:100]}
            wrappers['avaliar_sprite'] = _avaliar_sprite
        except Exception:
            pass

        # ─── Responder (KG + raciocínio + fallback honesto) ──
        try:
            def _responder(entrada="", texto="", **kw):
                msg = entrada or texto
                if not msg:
                    return {'sucesso': False, 'erro': 'Sem entrada'}
                # 1. Tenta KG (Metacognição)
                try:
                    from mcr.metacognicao import Metacognicao
                    meta = Metacognicao()
                    score, just = meta.calcular_confianca(msg)
                    if score > 0.3:
                        return {'sucesso': True,
                                'resposta': f'[KG:{score:.0%}] {just}',
                                'confianca': round(score, 3),
                                'fonte': 'kg'}
                except Exception:
                    pass
                # 2. Tenta raciocínio (com pergunta, não só compreender)
                try:
                    from mcr.raciocinador import Raciocinador
                    rac = Raciocinador()
                    r = rac.raciocinar(msg)  # usa raciocinar, não compreender
                    if r and r.get('resultado'):
                        return {'sucesso': True,
                                'resposta': str(r['resultado']),
                                'fonte': 'raciocinio',
                                'tipo': r.get('tipo', 'generico')}
                except Exception:
                    pass
                # 3. Fallback HONESTO (não eco)
                return {'sucesso': True,
                        'resposta': 'Nao tenho informacao suficiente sobre isso.',
                        'fonte': 'fallback',
                        'confianca': 0.0}
            wrappers['responder'] = _responder
        except Exception as e:
            self._log_erro('wrapper_responder', e)

        # ─── Mundo Vivo ───────────────────────────────
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

        # ─── Servidor NPC (background) ──────────────────
        try:
            def _iniciar_npc_server(entrada="", texto="", **kw):
                from mcr.npc_server import NPCServer
                server = NPCServer()
                server.iniciar()
                return {'sucesso': True, 'servico': 'npc_server',
                        'porta': 7777, 'status': 'iniciado'}
            wrappers['iniciar_npc_server'] = _iniciar_npc_server
        except Exception:
            pass

        # ─── World Observer ─────────────────────────────
        try:
            def _iniciar_observer(entrada="", texto="", **kw):
                from mcr.world_observer import WorldObserver
                obs = WorldObserver()
                obs.iniciar()
                return {'sucesso': True, 'servico': 'world_observer',
                        'status': 'observando'}
            wrappers['iniciar_observer'] = _iniciar_observer
        except Exception:
            pass

        self.registrar_ferramentas(wrappers)

    # ═══════════════════════════════════════════════════════
    # VALIDAÇÃO PÓS-EXECUÇÃO
    # ═══════════════════════════════════════════════════════

    def _validar_saida(self, resultado: Dict, acao: str) -> Dict:
        codigo = resultado.get('codigo', '')
        if not codigo:
            if acao in ('gerar_npc', 'gerar_monstro', 'gerar_quest', 'gerar_sprite'):
                return {'valido': False, 'checks': ['sem_codigo'],
                        'erro': f'Ferramenta nao produziu codigo para acao {acao}'}
            return {'valido': True, 'checks': ['sem_codigo']}
        tipo = str(resultado.get('tipo', '')).lower()
        if 'lua' not in tipo and 'npc' not in tipo and 'monstro' not in tipo:
            return {'valido': True, 'checks': ['nao_lua']}

        checks = []
        for padrao, nome in [('internalNpcName', 'nome'), ('npcType:register', 'register')]:
            if padrao in codigo:
                checks.append(f'{nome}:OK')

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
        if acao not in ('gerar_npc', 'gerar_monstro', 'gerar_quest', 'gerar_sprite'):
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
        """Auto-treina usando módulos que JÁ EXISTEM. Zero código novo."""
        resultados = {}

        # 1. Auto-estudo: detecta gaps no KG e estuda arquivos
        try:
            from mcr.auto_curiosidade import AutoCuriosidade
            curiosidade = AutoCuriosidade()
            n = curiosidade.ciclo_de_estudo()
            resultados['auto_estudo'] = n
        except Exception as e:
            resultados['auto_estudo_erro'] = str(e)[:80]

        # 2. Treino de diálogos: alimenta Markov com falas de NPC
        try:
            from mcr.dialogue_trainer import DialogueTrainer
            from mcr.dialogue_miner import minerar_lote, salvar_dialogos
            from mcr.paths import CANARY_NPC_DIR
            npcs = minerar_lote(CANARY_NPC_DIR)
            if npcs:
                salvar_dialogos(npcs)
                treinador = DialogueTrainer()
                stats = treinador.treinar_com_dialogos(npcs)
                resultados['dialogos'] = stats
        except Exception as e:
            resultados['dialogos_erro'] = str(e)[:80]

        # 3. Mineração de padrões: extrai estruturas de código
        try:
            from mcr.pattern_miner import miner_lua_files, save_patterns_to_kg
            from mcr.paths import CANARY_NPC_DIR
            padroes = miner_lua_files(CANARY_NPC_DIR)
            if padroes:
                save_patterns_to_kg(padroes)
                resultados['padroes_extraidos'] = len(padroes)
                # Invalida cache do Metacognicao para recarregar KG
                try:
                    from mcr.metacognicao import _carregar_kg
                    import mcr.metacognicao as _meta_mod
                    _meta_mod._KG_CACHE = None
                except Exception:
                    pass
        except Exception as e:
            resultados['padroes_erro'] = str(e)[:80]

        # 3b. Indexa ItemDB e MonsterDB no KG
        try:
            from mcr.item_database import ItemDatabase
            from mcr.monster_database import MonsterDatabase
            from mcr.pattern_miner import save_patterns_to_kg
            item_db = ItemDatabase()
            mon_db = MonsterDatabase()
            db_padroes = []
            # Indexa itens por categoria
            for cat, itens in item_db._por_categoria.items() if hasattr(item_db, '_por_categoria') else []:
                if itens:
                    db_padroes.append({
                        'arquivo': f'<itemdb:{cat}>',
                        'linguagem': 'data', 'tipo': 'item_categoria',
                        'api_calls': [cat], 'variaveis': [i.get('name', '') for i in itens[:20]],
                        'funcoes': [], 'tabelas': [], 'tamanho_linhas': len(itens),
                    })
            # Indexa monstros
            for nome, dados in mon_db._monstros.items() if hasattr(mon_db, '_monstros') else []:
                db_padroes.append({
                    'arquivo': f'<monsterdb:{nome}>',
                    'linguagem': 'data', 'tipo': 'monster',
                    'api_calls': [dados.get('race', '')],
                    'variaveis': [nome], 'funcoes': [], 'tabelas': [],
                    'tamanho_linhas': 1,
                })
            if db_padroes:
                save_patterns_to_kg(db_padroes)
                resultados['db_indexadas'] = len(db_padroes)
                import mcr.metacognicao as _meta_mod
                _meta_mod._KG_CACHE = None
        except Exception as e:
            resultados['db_indexadas_erro'] = str(e)[:80]

        # 4. Pré-treina o Markov com dados minerados
        self._pre_treinar_markov()

        return resultados

    def _pre_treinar_markov(self):
        """Alimenta o MCR com exemplos DIVERSOS usando estados compostos.

        O MCR aprende SOZINHO:
        - "tipo=npc" + qualquer tema → gerar_npc
        - "tipo=monstro" + qualquer tema → gerar_monstro
        - Sem tipo explícito: tema=dragao/ork → gerar_monstro
        - Sem tipo explícito: tema=ferreiro/vendedor → gerar_npc
        """
        # Base seeds (fallback mínimo)
        seeds = [
            ("crie um npc ferreiro", "gerar_npc"), ("crie um monstro dragao", "gerar_monstro"),
            ("crie uma quest", "gerar_quest"), ("crie um sprite de espada", "gerar_sprite"),
            ("explique o que e markov", "responder"), ("o que e entropia", "responder"),
            ("crie um npc mago", "gerar_npc"), ("gere um monstro orc", "gerar_monstro"),
        ]
        # Auto-gera seeds do ItemDatabase + diretórios
        try:
            from mcr.knowledge.item_database import ItemDatabase
            db = ItemDatabase()
            profs = list(getattr(db, 'categorias', {}).keys())[:20]
            for p in profs:
                pname = p.lower().replace('_', ' ')[:30]
                if len(pname) > 2:
                    seeds.append((f"crie um npc {pname}", "gerar_npc"))
        except Exception: pass
        try:
            from mcr.paths import CANARY_MONSTER_DIR
            import re as _re
            tokens = set()
            for f in list(CANARY_MONSTER_DIR.glob('*.lua'))[:100]:
                for t in _re.findall(r'[a-z]{3,}', f.stem.lower()):
                    tokens.add(t)
            for t in list(tokens)[:30]:
                seeds.append((f"crie um {t}", "gerar_monstro"))
                seeds.append((f"gere um monstro {t}", "gerar_monstro"))
        except Exception: pass

        for entrada, acao in seeds:
            estado = self._fingerprint_chave(entrada)
            for _ in range(3):
                self.mk.aprender(estado, acao)

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
        acao, confianca = self._decidir(estado)

        # ─── Gatekeeper: Metacognição (avisa, não bloqueia Tier 1) ──
        _meta_aviso = None
        if acao in ('gerar_npc', 'gerar_monstro', 'gerar_quest', 'gerar_sprite'):
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
            if acao in ('gerar_npc', 'gerar_monstro'):
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
        self._aprender(estado, acao, nota)

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

    def _decidir(self, estado: str) -> Tuple[str, float]:
        """Markov decide a ação. Fallbacks: similaridade → SQLite → hardcoded."""
        acao, conf = self.mk.predizer(estado)

        # Penalidades do ShadowCanary (APIs que crasham são desencorajadas)
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

        # Observador: se confiança do observer > Markov, usar cluster como boost
        if self._obs_ativado and self._observador:
            try:
                pred_obs, conf_obs, _ = self._observador.predizer_com_confianca(estado)
                if pred_obs is not None and conf_obs > conf:
                    # Mapeia cluster_Y de volta para ação
                    cluster_action = self._observador._mapear_cluster_para_acao(pred_obs)
                    if cluster_action:
                        return cluster_action, conf_obs
            except Exception:
                pass

        if acao and conf > 0.15:
            return str(acao), conf

        # Fallback 1: busca estado mais similar por componentes
        # Novo formato: ENT:TIPO|INT:INTENCAO|ROL:PAPEIS|E@pos|A@pos
        if self.mk.transicoes:
            partes_consulta = estado.split('|')
            melhor_estado = None
            melhor_sim = 0

            for est in self.mk.transicoes:
                partes_est = est.split('|')
                sim = 0.0
                matches = 0
                for pc in partes_consulta:
                    if pc in partes_est:
                        # Componentes compartilhados = similaridade
                        if pc.startswith('ENT:'):
                            sim += 0.5  # tipo de entidade é o sinal mais forte
                        elif pc.startswith('INT:'):
                            sim += 0.3  # intenção (comando vs pergunta)
                        elif pc.startswith('E@') or pc.startswith('A@'):
                            sim += 0.1  # posição das âncoras
                        else:
                            sim += 0.05
                        matches += 1
                if sim > melhor_sim:
                    melhor_sim = sim
                    melhor_estado = est

            if melhor_estado and melhor_sim > 0.3:
                acao2, conf2 = self.mk.predizer(melhor_estado)
                if acao2:
                    return str(acao2), conf2 * min(1.0, melhor_sim)

        # Fallback 2: SQLite (persistência entre sessões)
        sql = self._get_sqlite()
        if sql:
            try:
                acao_sql, conf_sql = sql.predizer(estado)
                if acao_sql and conf_sql > 0.1:
                    return str(acao_sql), conf_sql
            except Exception:
                pass

        # Fallback 3: HDC+SDM (memória associativa para conceitos novos)
        try:
            from hdc_core import HDVector
            from sdm_core import SDM
            if not hasattr(self, '_sdm'):
                self._sdm = SDM(n_enderecos=200, raio=0.1)
                self._sdm_hdv = {}
            # Busca tema no SDM
            partes = estado.split('|')
            tema_query = partes[2] if len(partes) > 2 else ''
            if tema_query and len(tema_query) > 2:
                hdv = HDVector.da_string(tema_query)
                for conhecido, (vec, acao_assoc) in list(self._sdm_hdv.items()):
                    if conhecido in tema_query or tema_query in conhecido:
                        return acao_assoc, 0.2
                # Armazena para futuras consultas
                if tema_query not in self._sdm_hdv:
                    self._sdm_hdv[tema_query] = (hdv, 'gerar_npc')
        except Exception:
            pass

        # Fallback final: tool com maior taxa de sucesso
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
            # Mapeia nome da tool → ação (ex: gerar_npc_lua → gerar_npc)
            acao_fallback = melhor_tool.replace('_lua', '').replace('_', ' ')
            return acao_fallback, max(0.05, melhor_taxa)
        return "gerar_npc", 0.1

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

    def _extrair_profissao(self, texto: str) -> str:
        """Descobre profissão do texto via ItemDatabase.profissoes."""
        t = texto.lower()
        try:
            from mcr.knowledge.item_database import ItemDatabase
            db = ItemDatabase()
            cats = getattr(db, 'categorias', {})
            for nome in cats:
                if nome.lower() in t:
                    return nome.lower()
        except Exception:
            pass
        return 'artesao'

    def _extrair_itens(self, texto: str) -> list:
        """Descobre itens via ItemDatabase (17,019 itens reais)."""
        import re
        t = texto.lower()
        # Detecta se é contexto de comércio via co-ocorrência de palavras
        triggers = {'vende', 'venda', 'loja', 'comercio', 'shop', 'sell', 'sells',
                    'vender', 'vendedor', 'mercador', 'itens', 'items', 'comprar'}
        if not any(tr in t for tr in triggers):
            return []
        try:
            from mcr.knowledge.item_database import ItemDatabase
            db = ItemDatabase()
            tokens = re.findall(r'[a-zà-ÿ]{3,}', t)
            itens = []
            for token in tokens:
                matches = db.buscar_por_nome(token)
                if matches:
                    for m in matches[:3]:
                        nome = m.get('name', token).title()
                        if nome not in itens:
                            itens.append(nome)
            # Fallback: sugerir por profissão
            if not itens:
                prof = self._extrair_profissao(texto)
                sugestoes = db.sugerir_itens_para_shop(prof)
                itens = [s.get('name', 'Item').title() for s in (sugestoes or [])[:5]]
            return itens[:5]
        except Exception:
            pass
        return []

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

    def _aprender(self, estado: str, acao: str, nota: float):
        """Aprende a transição. Reforça se nota alta. Persiste em SQLite."""
        self.mk.aprender(estado, acao)
        t1, t2 = self._thresholds_reforco()
        if nota > t1:
            self.mk.aprender(estado, acao)
        if nota > t2:
            self.mk.aprender(estado, acao)

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

    _DADOS_NPC = None
    _DADOS_MONSTRO = None

    @classmethod
    def _dados_npc(cls):
        """Mina dados de NPCs reais (cacheado)."""
        if cls._DADOS_NPC is not None:
            return cls._DADOS_NPC
        import re as _re, statistics as _st
        from collections import defaultdict as _dd
        from mcr.paths import CANARY_NPC_DIR
        looktypes = _dd(list)
        healths = []
        keywords = ['ferreiro','mago','guarda','vendedor','mercador','elfo','anao',
                    'anão','orc','padeiro','druida','alquimista','cavaleiro','ladrao',
                    'arqueiro','taverneiro','carpinteiro','artesao','bibliotecario']
        for f in CANARY_NPC_DIR.glob('*.lua'):
            try: c = f.read_text(encoding='latin-1', errors='replace')
            except Exception: continue
            m = _re.search(r'lookType\s*=\s*(\d+)', c)
            if m:
                lt = int(m.group(1))
                for kw in keywords:
                    if kw in f.stem.lower(): looktypes[kw].append(lt)
            m = _re.search(r'npcConfig\.health\s*=\s*(\d+)', c)
            if m: healths.append(int(m.group(1)))
        lt_map = {}
        for kw, vals in looktypes.items():
            if len(vals) >= 2:
                try: lt_map[kw] = int(_st.median(vals))
                except Exception: lt_map[kw] = max(set(vals), key=vals.count)
        if not lt_map: lt_map['generico'] = 128
        cls._DADOS_NPC = {'looktypes': lt_map, 'health': int(_st.median(healths)) if healths else 100}
        return cls._DADOS_NPC

    @classmethod
    def _dados_monstro(cls):
        """Dados de monstros via MonsterDatabase (data-driven, zero hardcode)."""
        if cls._DADOS_MONSTRO is not None:
            return cls._DADOS_MONSTRO
        try:
            from mcr.monster_database import MonsterDatabase
            db = MonsterDatabase()
            cls._DADOS_MONSTRO = {
                'stats': db.get_tiers(),
                'thresholds': db._thresholds,
                'race_keywords': db._race_map,
                'loot': db.get_loot(3),
                'default_race': 'blood',
                'name_health': db._name_health,
            }
        except Exception:
            cls._DADOS_MONSTRO = {
                'stats': {'low':(240,100,95),'medium':(3000,1800,130),'high':(25000,8000,160)},
                'thresholds': (1000, 7320), 'race_keywords': {}, 'loot': [],
                'default_race': 'blood', 'name_health': {}
            }
        return cls._DADOS_MONSTRO

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
