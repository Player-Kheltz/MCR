"""mcr.daemon — MCR Daemon Unificado.

Loop cognitivo contínuo. O MCR como sistema operacional.
Observa eventos, processa via pipeline, gerencia o mundo,
conversa com NPCs, gera conteúdo, aprende e evolui.

Tudo é byte. Tudo é Markov. Tudo é Equação + Entropia.

Uso:
    daemon = MCRDaemon()
    daemon.iniciar()
"""
import time
import threading
from typing import Dict, List, Optional

from mcr.mcr import MCR
from mcr.paths import ensure_dirs


class MCRDaemon:
    """Sistema operacional cognitivo contínuo.

    Unifica:
    - Pipeline cognitiva (percebe → decide → executa → avalia → aprende)
    - World Observer (eventos do servidor)
    - World System (expansão, conexão, equilíbrio do mundo)
    - Dialogue Trainer (conversa com NPCs)
    - Auto-Curiosidade (auto-estudo)
    - Auto-Evolução (mutação de thresholds)
    """

    def __init__(self, tema: str = "Mundo MCR"):
        ensure_dirs()
        self.tema = tema
        self._ativo = False
        self._threads: List[threading.Thread] = []

        # ─── Núcleo cognitivo ──────────────────────────
        self.pipeline = MCR()

        # ─── Subsistemas (lazy init) ───────────────────
        self._world_system = None
        self._observer = None
        self._dialogue = None
        self._conector = None
        self._curiosidade = None

        # ─── Estado ────────────────────────────────────
        self._ciclos = 0
        self._eventos_processados = 0
        self._entidades_criadas = 0
        self._t_inicio = time.time()

    # ═══════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════

    def iniciar(self):
        """Inicia o daemon. Bloqueia até Ctrl+C."""
        self._ativo = True
        self._iniciar_subsistemas()

        print(f'\n{"="*60}')
        print(f'  MCR DAEMON — {self.tema}')
        print(f'  Pipeline: {self.pipeline.nome} v{self.pipeline.versao}')
        print(f'  Ferramentas: {len(self.pipeline._registry.listar())}')
        print(f'{"="*60}\n')

        try:
            self._loop_principal()
        except KeyboardInterrupt:
            print('\n[MCR Daemon] Encerrando...')
        finally:
            self.parar()

    def parar(self):
        """Para todos os subsistemas."""
        self._ativo = False
        if self._observer:
            try: self._observer.parar()
            except Exception: pass

        for t in self._threads:
            if t.is_alive():
                t.join(timeout=3)

        self._salvar_estado()
        print(f'[MCR Daemon] Encerrado. {self._eventos_processados} eventos, '
              f'{self._entidades_criadas} entidades, {self._ciclos} ciclos.')

    # ═══════════════════════════════════════════════════════
    # LOOP PRINCIPAL
    # ═══════════════════════════════════════════════════════

    def _loop_principal(self):
        """Loop principal: observa → processa → gerencia → evolui."""
        intervalo_auto = 60  # segundos entre ciclos autônomos
        ultimo_ciclo = 0

        while self._ativo:
            try:
                # 1. Processa eventos externos (diálogo, perturbações)
                eventos = self._coletar_eventos()
                for evento in eventos:
                    self._processar_evento(evento)

                # 2. Ciclo autônomo (expansão do mundo, auto-estudo)
                agora = time.time()
                if agora - ultimo_ciclo > intervalo_auto:
                    self._ciclo_autonomo()
                    ultimo_ciclo = agora

                # 3. Auto-evolução (a cada 50 processamentos)
                if self.pipeline._total_processamentos > 0 and \
                   self.pipeline._total_processamentos % 50 == 0:
                    self._ciclo_evolutivo()

                time.sleep(1)

            except Exception as e:
                self.pipeline._log_erro('daemon_loop', e)
                time.sleep(5)

    # ═══════════════════════════════════════════════════════
    # SUBSISTEMAS
    # ═══════════════════════════════════════════════════════

    def _iniciar_subsistemas(self):
        """Inicializa subsistemas em threads separadas."""
        # World Observer (eventos do servidor)
        try:
            from mcr.world_observer import WorldObserver
            self._observer = WorldObserver()
            self._observer.iniciar()
            print('[Daemon] WorldObserver ativo')
        except Exception as e:
            print(f'[Daemon] WorldObserver indisponivel: {e}')

        # Auto-Curiosidade (auto-estudo em background)
        try:
            from mcr.auto_curiosidade import AutoCuriosidade
            self._curiosidade = AutoCuriosidade()
            self._curiosidade.iniciar_thread_background(intervalo=300)
            print('[Daemon] AutoCuriosidade ativa (5min)')
        except Exception as e:
            print(f'[Daemon] AutoCuriosidade indisponivel: {e}')

        # MCRConector (pontes semânticas)
        try:
            from mcr.memory import MCRConector
            self._conector = MCRConector()
            print('[Daemon] MCRConector ativo')
        except Exception as e:
            print(f'[Daemon] MCRConector indisponivel: {e}')

    # ═══════════════════════════════════════════════════════
    # EVENTOS
    # ═══════════════════════════════════════════════════════

    def _coletar_eventos(self) -> List[Dict]:
        """Coleta eventos pendentes do observer."""
        eventos = []
        if self._observer:
            try:
                eventos = self._observer.get_ultimos_eventos(n=10)
            except Exception:
                pass
        return eventos

    def _processar_evento(self, evento: Dict):
        """Roteia evento para o pipeline correto."""
        tipo = evento.get('type', evento.get('tipo', ''))
        entrada = str(evento)

        # ─── Diálogo (jogador falando com NPC) ──────────
        if tipo in ('chat', 'dialogo', 'message', 'say'):
            resultado = self.pipeline.processar(entrada)
            self._eventos_processados += 1
            return resultado

        # ─── Perturbação (NPC morreu, spawn) ────────────
        if tipo in ('death', 'kill', 'spawn', 'login', 'world_perturbation'):
            try:
                if self._world_system is None:
                    from mcr.mcr_world_system import MCRWorldSystem
                    self._world_system = MCRWorldSystem()
                resultado = self._world_system.perceber_perturbacao(evento)
                if resultado.get('sub_acao') == 'reposicao':
                    self._entidades_criadas += 1
                self._eventos_processados += 1
            except Exception as e:
                self.pipeline._log_erro('perturbacao', e)

        # ─── Genérico: pipeline cognitiva ───────────────
        else:
            self.pipeline.processar(entrada)
            self._eventos_processados += 1

    # ═══════════════════════════════════════════════════════
    # CICLOS AUTÔNOMOS
    # ═══════════════════════════════════════════════════════

    def _ciclo_autonomo(self):
        """Expande o mundo, estuda gaps, equilibra."""
        self._ciclos += 1

        # 1. Expansão: cria entidades se mundo está vazio
        try:
            if self._world_system is None:
                from mcr.mcr_world_system import MCRWorldSystem
                self._world_system = MCRWorldSystem()
            report = self._world_system.ciclo(
                tema=self.tema, max_entidades=2)
            criadas = report.get('entidades_criadas', 0)
            self._entidades_criadas += criadas
            if criadas > 0:
                print(f'  [Ciclo {self._ciclos}] +{criadas} entidades')
        except Exception as e:
            self.pipeline._log_erro('ciclo_mundo', e)

        # 2. Auto-treino (alimenta o MCR com dados novos)
        if self._ciclos % 5 == 0:
            try:
                self.pipeline.auto_treinar()
            except Exception as e:
                self.pipeline._log_erro('auto_treino', e)

    def _ciclo_evolutivo(self):
        """Mutação de thresholds (auto-evolução)."""
        try:
            self.pipeline.mk_palavra = self.pipeline.mk
            from mcr.mcr_auto_evolution import MCRAutoEvolution
            evo = MCRAutoEvolution(mcr_system=self.pipeline)
            resultado = evo.ciclo(n_mutacoes=2)
            aceitas = sum(1 for r in resultado if r.get('aceita', False))
            if aceitas > 0:
                print(f'  [Evo] {aceitas} mutações aceitas')
        except Exception as e:
            self.pipeline._log_erro('evolucao', e)

    # ═══════════════════════════════════════════════════════
    # PERSISTÊNCIA
    # ═══════════════════════════════════════════════════════

    def _salvar_estado(self):
        """Persiste estado ao encerrar."""
        try:
            self.pipeline._salvar_execucoes()
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════
    # API PÚBLICA
    # ═══════════════════════════════════════════════════════

    def processar(self, entrada: str) -> Dict:
        """Processa entrada diretamente via pipeline (modo síncrono)."""
        self._eventos_processados += 1
        return self.pipeline.processar(entrada)

    def responder_dialogo(self, npc_id: str, jogador_id: str,
                          mensagem: str) -> str:
        """Responde diálogo de NPC (modo síncrono)."""
        try:
            from mcr.dialogue_trainer import DialogueTrainer
            if self._dialogue is None:
                self._dialogue = DialogueTrainer(mcr_system=self.pipeline)
            return self._dialogue.gerar_resposta(npc_id, mensagem)
        except Exception:
            return "..."

    def estatisticas(self) -> Dict:
        """Métricas do daemon."""
        stats = self.pipeline.estatisticas()
        stats.update({
            'daemon_ativo': self._ativo,
            'tema': self.tema,
            'ciclos': self._ciclos,
            'eventos_processados': self._eventos_processados,
            'entidades_criadas': self._entidades_criadas,
            'tempo_ativo': round(time.time() - self._t_inicio),
            'observer_ativo': self._observer is not None,
            'curiosidade_ativa': self._curiosidade is not None,
        })
        return stats


# ─── Singleton ────────────────────────────────────────────
_daemon: Optional[MCRDaemon] = None


def get_daemon() -> MCRDaemon:
    """Retorna instância global do daemon."""
    global _daemon
    if _daemon is None:
        _daemon = MCRDaemon()
    return _daemon


# ─── CLI ──────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    tema = sys.argv[1] if len(sys.argv) > 1 else "Mundo MCR"
    daemon = MCRDaemon(tema=tema)
    daemon.iniciar()
