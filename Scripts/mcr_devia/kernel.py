#!/usr/bin/env python
"""
MCR-DevIA Kernel v1
====================
Nucleo minimo: carregador de comandos, bus de eventos, contexto compartilhado.
Fase 3 da arquitetura modular.

Uso:
    from kernel import MCRKernel
    k = MCRKernel()
    k.executar('status', [])
"""
import os, sys, json, importlib, time, re

# ============================================================
# DETECCAO DE BASE (dinamica, universal)
# ============================================================
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')
DEVIA_DIR = os.path.dirname(os.path.abspath(__file__))
COMANDOS_DIR = os.path.join(DEVIA_DIR, 'comandos')
MODULOS_DIR = os.path.join(DEVIA_DIR, 'modulos')
HOOKS_DIR = os.path.join(DEVIA_DIR, 'hooks')

# ============================================================
# EVENT BUS (hooks pre/post/error)
# ============================================================
class EventBus:
    """Sistema simples de hooks. Qualquer modulo pode registrar handlers."""
    
    def __init__(self):
        self._handlers = {'pre_exec': [], 'pos_exec': [], 'on_error': []}
    
    def on(self, evento, handler):
        """Registra handler para um evento."""
        if evento in self._handlers:
            self._handlers[evento].append(handler)
    
    def emit(self, evento, **kwargs):
        """Dispara evento, chamando todos os handlers."""
        results = []
        for handler in self._handlers.get(evento, []):
            try:
                r = handler(**kwargs)
                results.append(r)
            except Exception as e:
                print(f'[Kernel] ERRO no hook {evento}: {e}')
        return results


# ============================================================
# COMMAND LOADER (carregamento dinamico de comandos)
# ============================================================
class CommandLoader:
    """Carrega comandos de comandos/ diretorio. Lazy loading + cache."""
    
    def __init__(self, cmd_dir=None):
        self.cmd_dir = cmd_dir or COMANDOS_DIR
        self._cache = {}   # nome -> {meta, handler, module}
        self._loaded = False
    
    def _carregar_modulo(self, fpath):
        """Carrega um modulo .py de arquivo seguramente."""
        import importlib.util as _util
        nome_mod = os.path.splitext(os.path.basename(fpath))[0]
        spec = _util.spec_from_file_location(nome_mod, fpath)
        if not spec or not spec.loader:
            return None
        mod = _util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    
    def scan(self):
        """Escaneia diretorio e carrega todos os comandos."""
        self._cache = {}
        if not os.path.isdir(self.cmd_dir):
            return 0
        
        count = 0
        for f in sorted(os.listdir(self.cmd_dir)):
            if not f.startswith('cmd_') or not f.endswith('.py'):
                continue
            fpath = os.path.join(self.cmd_dir, f)
            try:
                mod = self._carregar_modulo(fpath)
                if mod and hasattr(mod, 'register'):
                    meta = mod.register()
                    nome = meta.get('name', f[4:-3])
                    self._cache[nome] = {
                        'meta': meta,
                        'handler': meta.get('handler'),
                        'module': mod,
                        'arquivo': fpath,
                    }
                    count += 1
            except Exception as e:
                print(f'[Loader] ERRO {f}: {e}')
        self._loaded = True
        return count
    
    def get(self, nome):
        """Retorna comando pelo nome (lazy load se necessario)."""
        if not self._loaded:
            self.scan()
        return self._cache.get(nome)
    
    def listar(self):
        """Lista todos os comandos disponiveis."""
        if not self._loaded:
            self.scan()
        return [(n, i['meta'].get('desc','')) for n, i in sorted(self._cache.items())]
    
    def refresh(self):
        """Hot-reload: recarrega tudo."""
        self._loaded = False
        return self.scan()


# ============================================================
# KERNEL PRINCIPAL
# ============================================================
class MCRKernel:
    """Orquestrador principal. Gerencia comandos, modulos, eventos."""
    
    def __init__(self):
        self.events = EventBus()
        self.loader = CommandLoader()
        self.modulos = {}
        self.orquestrador_ctx = None
        self.ctx_crew = None
        self.contexto = {
            'kg': None,
            'ia': None,
            'ctx_crew': None,
            'orquestrador_ctx': None,
            'kernel': self,
        }
        self._inicializado = False
    
    def inicializar(self):
        """Inicializa kernel: carrega modulos essenciais + comandos."""
        if self._inicializado:
            return
        
        # 0. Auto-cleanup: temp/ > 24h e output/ relatorios temporarios
        self._auto_cleanup()
        
        # 0.5. KGCleaner: marca lessons poluentes como inactive
        try:
            from modulos.kg_cleaner import limpar as _clean_kg
            _clean_kg()
        except Exception as _kg_err:
            print(f'[Kernel] KGCleaner: {_kg_err}')
        
        # 0.6. Truncation Fixer: remove [:N] do codigo ativo
        try:
            from modulos.truncation_fixer import executar as _fix_truncation
            _fix_truncation()
        except Exception as _trunc_err:
            print(f'[Kernel] TruncationFixer: {_trunc_err}')
        
        # 1. Carrega modulos
        self._carregar_modulos()
        
        # 2. Orquestrador de Contexto Global (Context Infinity)
        self._inicializar_orquestrador_ctx()
        
        # 3. ContextCrew (leitor universal de contexto)
        self._inicializar_ctx_crew()
        
        # 4. Escaneia comandos
        n = self.loader.scan()
        
        # 5. Hooks padrao
        self.events.on('pre_exec', self._hook_contexto_pre)
        self.events.on('pos_exec', self._hook_registrar_kg)
        self.events.on('pos_exec', self._hook_contexto_pos)
        
        # 6. Watchdog (monitora sandbox/)
        try:
            from modulos.watchdog import iniciar_watchdog
            iniciar_watchdog()
            print('[Kernel] Watchdog iniciado')
        except Exception as e:
            print(f'[Kernel] Watchdog nao iniciado: {e}')
        
        self._inicializado = True
        return n
    
    def _inicializar_orquestrador_ctx(self):
        """Cria OrquestradorContexto global com contexto persistente entre comandos."""
        try:
            from context_infinity import OrquestradorContexto
            from modulos.util import _get_modelo
            kg_path = os.path.join(SANDBOX, '.mcr_devia', 'knowledge.json')  # master
            kg_dir = os.path.join(SANDBOX, '.mcr_devia', 'kg')  # ctx files
            cfg_modelo = _get_modelo("leve")
            if os.path.exists(kg_dir):
                self.orquestrador_ctx = OrquestradorContexto(
                    modelo=cfg_modelo["modelo"], kg_path=kg_path)
            else:
                self.orquestrador_ctx = OrquestradorContexto(modelo=cfg_modelo["modelo"])
            self.contexto['orquestrador_ctx'] = self.orquestrador_ctx
        except Exception as e:
            print(f'[Kernel] AVISO: Context Infinity nao disponivel: {e}')
    
    def _inicializar_ctx_crew(self):
        """Carrega ContextCrew V3 como modulo de contexto."""
        try:
            sys.path.insert(0, DEVIA_DIR)
            from context_crew import ContextCrew
            self.ctx_crew = ContextCrew()
            self.contexto['ctx_crew'] = self.ctx_crew
        except Exception as e:
            print(f'[Kernel] AVISO: ContextCrew nao disponivel: {e}')
    
    def _carregar_modulos(self):
        """Tenta carregar modulos de modulos/ ou fallback para imports diretos."""
        # Tenta carregar modulos do diretorio modulos/
        if os.path.isdir(MODULOS_DIR):
            for f in os.listdir(MODULOS_DIR):
                if f.endswith('.py') and not f.startswith('_'):
                    try:
                        mod_path = os.path.join(MODULOS_DIR, f)
                        mod = self._carregar_modulo_file(mod_path)
                        if mod and hasattr(mod, 'init_module'):
                            nome, instancia = mod.init_module(self.contexto)
                            self.modulos[nome] = instancia
                            self.contexto[nome] = instancia
                    except ImportError:
                        pass
        # Fallback: importa direto do mcr_devia.py (compatibilidade)
        if 'kg' not in self.modulos:
            try:
                sys.path.insert(0, DEVIA_DIR)
                from mcr_devia import KnowledgeGraph, IA
                kg = KnowledgeGraph()
                ia = IA()
                self.modulos['kg'] = kg
                self.modulos['ia'] = ia
                self.contexto['kg'] = kg
                self.contexto['ia'] = ia
            except ImportError:
                print('[Kernel] AVISO: mcr_devia.py nao encontrado, modo limitado')
        
        # SelfStudy: thread background a cada 10 minutos (fora do try)
        try:
            import threading as _th
            def _ss_loop():
                import time as _t
                while True:
                    _t.sleep(3600)
                    try:
                        from modulos.self_study import executar as _ss_exec
                        _ss_exec()
                    except Exception:
                        pass
            _th.Thread(target=_ss_loop, daemon=True).start()
            print('[Kernel] SelfStudy: thread background iniciada')
        except Exception:
            pass
    
    def _auto_cleanup(self):
        """Limpa temp/ > 24h e relatorios temporarios em output/."""
        import shutil
        agora = time.time()
        dias_seg = 86400
        removidos = 0
        
        # temp/
        temp_dir = os.path.join(SANDBOX, 'temp')
        if os.path.isdir(temp_dir):
            for nome in os.listdir(temp_dir):
                fpath = os.path.join(temp_dir, nome)
                try:
                    if os.path.isfile(fpath) and (agora - os.path.getmtime(fpath)) > dias_seg:
                        os.remove(fpath)
                        removidos += 1
                    elif os.path.isdir(fpath) and (agora - os.path.getmtime(os.path.dirname(fpath))) > dias_seg:
                        shutil.rmtree(fpath, ignore_errors=True)
                        removidos += 1
                except:
                    pass
        
        # output/relatorios temporarios (> 7 dias)
        rel_dir = os.path.join(SANDBOX, 'output', 'relatorios')
        if os.path.isdir(rel_dir):
            for nome in os.listdir(rel_dir):
                fpath = os.path.join(rel_dir, nome)
                try:
                    if os.path.isfile(fpath) and (agora - os.path.getmtime(fpath)) > dias_seg * 7:
                        os.remove(fpath)
                        removidos += 1
                except:
                    pass
        
        if removidos:
            print(f'[Kernel] Auto-cleanup: {removidos} arquivos removidos')
    
    def _carregar_modulo_file(self, fpath):
        """Carrega um arquivo .py como modulo."""
        import importlib.util as _util
        nome = os.path.splitext(os.path.basename(fpath))[0]
        spec = _util.spec_from_file_location(nome, fpath)
        if spec and spec.loader:
            mod = _util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        return None
    
    def _hook_contexto_pre(self, **kw):
        """Hook pre-exec: carrega lessons relevantes do KG no orquestrador."""
        orq = self.orquestrador_ctx
        kg = self.contexto.get('kg')
        if not orq or not kg:
            return
        cmd = kw.get('cmd', '')
        args = kw.get('args', [])
        consulta = f"{cmd} {' '.join(args)}"
        # Busca lessons relevantes no KG e adiciona como fragmentos
        lessons = kg.buscar(consulta, max_r=3)
        for i, l in enumerate(lessons):
            from context_infinity import FragmentoContexto
            err = l.get('erro', '')
            sol = l.get('solucao', '')
            ctx_tag = l.get('ctx', 'geral')
            score = 50  # peso medio
            frag = FragmentoContexto(
                id=f"kg_{cmd}_{i}",
                conteudo=f"[KG] {err}: {sol}",
                origem=f"KG/{ctx_tag}",
                prioridade=min(100, score),
                tipo="kg_lesson"
            )
            orq.adicionar(frag)
    
    def _hook_contexto_pos(self, **kw):
        """Hook pos-exec: salva resultado no orquestrador como fragmento."""
        orq = self.orquestrador_ctx
        if not orq:
            return
        cmd = kw.get('cmd', '')
        resultado = kw.get('resultado', False)
        from context_infinity import FragmentoContexto
        frag = FragmentoContexto(
            id=f"exec_{cmd}_{int(time.time())}",
            conteudo=f"Comando {cmd} executado: {'OK' if resultado else 'FALHA'}",
            origem="kernel/exec",
            prioridade=30,
            tipo="resultado"
        )
        orq.adicionar(frag)
    
    def _hook_registrar_kg(self, **kw):
        """Hook padrao: registra execucao no KG."""
        ctx = self.contexto
        kg = ctx.get('kg')
        if kg and 'cmd' in kw:
            kg.aprender(f"Comando executado: {kw['cmd']}", 
                       f"args: {str(kw.get('args',[]))}",
                       f"resultado: {kw.get('resultado', 'ok')}", 'runtime')
    
    def executar(self, cmd, args):
        """Executa um comando pelo nome."""
        # Pre-exec hook
        self.events.emit('pre_exec', cmd=cmd, args=args)
        
        t0 = time.perf_counter()
        resultado = False
        try:
            import json as _j
            _rp = os.path.join(os.path.dirname(__file__), '..', '..', 'sandbox', '.mcr_result.json')
            with open(_rp, 'w', encoding='utf-8') as _f:
                _j.dump({'cmd':cmd,'status':'processando','ts':time.time()}, _f, ensure_ascii=False)
        except Exception:
            pass
        # Progress tracker
            try:
                from modulos.progress_tracker import reportar as _trk_report2
                _trk_report2('Kernel', f'executando {cmd}', 0.1)
            except Exception:
                pass
        
        try:
            # 1. Tenta comando carregado
            comando = self.loader.get(cmd)
            if comando:
                handler = comando['handler']
                if handler:
                    # Inspeciona os parametros que o handler aceita
                    import inspect
                    sig = inspect.signature(handler)
                    params = list(sig.parameters.keys())
                    kwargs = {}
                    if 'ctx_crew' in params:
                        kwargs['ctx_crew'] = self.contexto.get('ctx_crew')
                    if 'orquestrador_ctx' in params:
                        kwargs['orquestrador_ctx'] = self.contexto.get('orquestrador_ctx')
                    resultado = handler(
                        self.contexto.get('kg'),
                        self.contexto.get('ia'),
                        args,
                        **kwargs
                    )
                    if resultado:
                        elapsed = time.perf_counter() - t0
                        print(f'[Kernel] {cmd} executado em {elapsed*1000:.1f}ms')
                        return True
            
            # 2. Fallback: comando nao encontrado
            print(f'[Kernel] Comando nao encontrado: {cmd}')
            return False
            
        except Exception as e:
            print(f'[Kernel] ERRO em {cmd}: {e}')
            import traceback; traceback.print_exc()
            self.events.emit('on_error', cmd=cmd, args=args, error=e)
            return False
        finally:
            self.events.emit('pos_exec', cmd=cmd, args=args, resultado=resultado)
            # Escreve .mcr_result.json para Cloud saber que terminou
            try:
                import json as _json_result
                _r_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sandbox', '.mcr_result.json')
                with open(_r_path, 'w', encoding='utf-8') as _f:
                    _json_result.dump({'cmd':cmd,'resultado':bool(resultado),'ts':time.time()}, _f, ensure_ascii=False)
            except: pass
    
    def listar_comandos(self):
        """Lista comandos disponiveis."""
        return self.loader.listar()


# ============================================================
# MODO --json (IPC sem shell)
# ============================================================
def main_json():
    """Entry point para --json mode."""
    if '--json' in sys.argv:
        idx = sys.argv.index('--json')
        if idx + 1 < len(sys.argv):
            json_path = sys.argv[idx + 1]
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    import json as _json
                    cmd_data = _json.load(f)
                sys.argv = [sys.argv[0], cmd_data.get('cmd', '')] + cmd_data.get('args', [])
            except Exception as e:
                print(f'[Kernel] Erro lendo {json_path}: {e}')
                return True
        else:
            print('[Kernel] Use: --json <arquivo_cmd>')
            return True
    return False


def try_executar(cmd, args, kg=None, ia=None):
    """Tenta executar comando via kernel. Retorna True se executou."""
    try:
        k = MCRKernel()
        if kg: k.contexto['kg'] = kg
        if ia: k.contexto['ia'] = ia
        k.loader.scan()
        if k.loader.get(cmd):
            k.executar(cmd, args)
            return True
    except Exception:
        pass
    return False


# ============================================================
# ENTRY POINT
# ============================================================
def main_kernel():
    """Entry point principal do kernel."""
    
    # ============================================================
    # Limpa progress tracker anterior (se houver)
    try:
        from modulos.progress_tracker import limpar as _trk_limpar
        _trk_limpar()
    except ImportError:
        pass
    
    # Inicia tracker para esta execucao
    if '--json' in sys.argv:
        try:
            from modulos.progress_tracker import iniciar as _trk_iniciar, reportar as _trk_report
            _trk_iniciar(pipeline='kernel_json')
            _trk_report('Kernel', 'inicializando', 0.05)
        except Exception as e:
            pass
    
    # ============================================================
    # Processa --json    # Contexto rapido para Cloud (suprimido se --chat)
    # Processa --json antes de tudo
    if main_json():
        sys.exit(0)
    
    if len(sys.argv) < 2:
        print('MCR-DevIA Kernel v1')
        print('Uso: python kernel.py <comando> [args...]')
        print('     python kernel.py --json <arquivo.json>')
        print(f'Comandos em: {COMANDOS_DIR}')
        sys.exit(0)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    
    k = MCRKernel()
    n = k.inicializar()
    
    if cmd == '--chat':
        print('[Chat] Modo chat ativado')
        return
    if cmd == 'listar':
        print(f'Comandos carregados: {n}')
        for nome, desc in k.listar_comandos():
            print(f'  {nome:20s} | {desc}')
    elif cmd == 'refresh':
        n = k.loader.refresh()
        print(f'[Kernel] {n} comandos recarregados (hot-reload)')
    elif cmd == "--serve":
        from modulos.serve import Serve
        Serve(k).loop()
    elif cmd == "--self-study":
        print('[Kernel] Iniciando Self-Study...')
        sys.stdout.flush()
        from modulos.master_agent import MasterAgent
        ma = MasterAgent()
        ma._execution_count = 10  # força o gatilho
        ma._self_study()
        print('[Kernel] Self-Study concluido.')
    elif cmd == "--auto-melhorar":
        print('[Kernel] Iniciando Auto-Melhoria...')
        sys.stdout.flush()
        from modulos.master_agent import MasterAgent
        ma = MasterAgent()
        ma._execution_count = 20
        ma._auto_melhorar()
        print('[Kernel] Auto-Melhoria concluida.')
    elif cmd == "--diagnosticar":
        print('[Kernel] Iniciando Diagnostico...')
        sys.stdout.flush()
        from modulos.diagnostic_engine import DiagnosticEngine
        from modulos.ia import IA
        de = DiagnosticEngine(IA(), None, None)
        problemas = de.diagnosticar()
        print(de.gerar_relatorio(problemas))
    elif cmd == "--pattern":
        args_texto = ' '.join(args) if args else ''
        if not args_texto:
            print('[Kernel] Uso: --pattern <texto>')
            sys.stdout.flush()
        else:
            print('[Kernel] Analisando padroes...')
            sys.stdout.flush()
            from modulos.pattern_engine import PatternEngine
            from modulos.ia import IA
            pe = PatternEngine(IA())
            resultado = pe.analisar(args_texto, 'texto')
            print(f'Dominio: {resultado["dominio"]}')
            print(f'Eixo Nirvana-Caos: {resultado["eixo_nirvana_caos"]}')
            print(f'Tokens: {resultado["tokens"]}')
            print(f'Sugestao: {resultado["sugestao"]}')
    elif cmd in ("--dashboard", "--sse"):
        print('[Kernel] Iniciando SSE Server em http://localhost:8765')
        print('[Kernel] Dashboard: http://localhost:8765/thought_dashboard.html')
        sys.stdout.flush()
        from modulos.sse_server import iniciar_sse
        iniciar_sse(8765)
        # Mantem o processo vivo
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print('\n[Kernel] SSE Server encerrado.')
    else:
        resultado = k.executar(cmd, args)
        if not resultado:
            print(f'[Kernel] Comando nao encontrado: {cmd}')

if __name__ == '__main__':
    main_kernel()
