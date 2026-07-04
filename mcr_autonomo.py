#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCR AUTONOMO — Ciclo perpetuo de aprendizado autonomo.
=======================================================
Lanca o MCR em modo autonomo: explora, aprende, pensa, evolui,
busca na web, e recomeca. So para quando fechar a janela.

Uso:
    python mcr_autonomo.py              # modo terminal
    python mcr_autonomo.py --verbose    # logs detalhados
    pythonw mcr_autonomo.py             # sem terminal (atalho)

Atalho:
    Clique duas vezes em "Iniciar MCR Autonomo.bat"
"""

import sys, os, json, time, math, random as _rand, threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

__file__ = os.path.join(BASE_DIR, "MCR_AGI.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR_AGI.py", "exec"))

VERBOSE = "--verbose" in sys.argv
LOG_PATH = os.path.join(CACHE_DIR, "mcr_autonomo.log")
ESTADO_PATH = os.path.join(CACHE_DIR, "mcr_autonomo_estado.json")

def log(msg):
    msg = f"[{time.strftime('%H:%M:%S')}] {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    if VERBOSE:
        print(msg)

class MCRAutonomo:
    """Ciclo perpetuo de aprendizado autonomo do MCR.
    
    Decisoes sao tomadas por:
    - MCRDecisorUniversal para parametros iterativos
    - mk_ciclo (Markov) para escolha do modo (explorar/pensar/web/evoluir)
    - MCRThreshold para pausas adaptativas
    
    Zero if/elif na orquestracao — tudo por predizer()."""

    MODO_PASSIVO = "passivo"
    MODO_DIAG = "diagnostico"
    MODO_EXPLORAR = "explorar"
    MODO_PENSAR = "pensar"
    MODO_WEB = "web"
    MODO_EVOLUIR = "evoluir"
    MODO_DESCANSO = "descanso"

    def __init__(self):
        self.cerebro = CerebroAGI()
        self.curiosidade = MCRCuriosidade(self.cerebro)
        self.conversa = MCRConversa(self.cerebro)
        self.mk_ciclo = MCR("ciclo_autonomo")

        self.total_ciclos = 0
        self.total_descobertas = 0
        self.total_webs = 0
        self._rodando = True
        self._modo_atual = None
        self._ultimo_modo = None
        self._n_vezes_mesmo_modo = 0

        # Carrega estado anterior
        self._carregar_estado()
        
        log("MCR Autonomo iniciado.")
        log(f"Topicos: {len(self.cerebro.topicos)} | Bytes: {self.cerebro.mk_byte.total} | Palavras: {self.cerebro.mk_palavra.total}")

    def _carregar_estado(self):
        try:
            cerebro_path = os.path.join(CACHE_DIR, "cerebro.json")
            self.cerebro.carregar(cerebro_path)
        except:
            pass
        try:
            if os.path.exists(ESTADO_PATH):
                with open(ESTADO_PATH) as f:
                    d = json.load(f)
                self.total_ciclos = d.get("ciclos", 0)
                self.total_descobertas = d.get("descobertas", 0)
        except:
            pass

    def _salvar_estado(self):
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(ESTADO_PATH, "w") as f:
                json.dump({
                    "ciclos": self.total_ciclos,
                    "descobertas": self.total_descobertas,
                    "topicos": len(self.cerebro.topicos),
                    "bytes": self.cerebro.mk_byte.total,
                    "palavras": self.cerebro.mk_palavra.total,
                    "modo": self._modo_atual,
                    "timestamp": time.time(),
                }, f)
        except:
            pass

    # ─── FASE 1: PROCESSAMENTO PASSIVO ──────────────────────
    def _fase_passiva(self):
        """Drena fila de eventos do sistema (hooks + arquivos)."""
        self.cerebro._ciclo_passivo(max_eventos=20)

        # Detecta eventos multi-nivel
        try:
            evento, info = self.cerebro.ent_temporal.detectar()
            if evento:
                log(f"EVENTO: {info['n_afetados']} niveis oscilaram: {info['niveis']}")
        except:
            pass

    # ─── FASE 2: DIAGNOSTICO ───────────────────────────────
    def _fase_diagnostico(self):
        """Mede o estado atual do sistema."""
        ent_byte = self.cerebro.mk_byte.entropia_media() if self.cerebro.mk_byte.total > 0 else 1.0
        ent_palavra = self.cerebro.mk_palavra.entropia_media() if self.cerebro.mk_palavra.total > 0 else 1.0
        ent_media = (ent_byte + ent_palavra) / 2

        fome = self.curiosidade.diagnosticar_fome()
        tem_fome = fome.get('fome', False)

        n_topicos = len(self.cerebro.topicos)
        n_bytes = self.cerebro.mk_byte.total
        n_palavras = self.cerebro.mk_palavra.total

        gaps = []
        try:
            g = self.cerebro.genesis.diagnosticar()
            gaps = g.get('gaps', [])
        except:
            pass

        estado = f"ent:{'alta' if ent_media > 0.7 else 'baixa' if ent_media < 0.3 else 'media'}"
        estado += f"_fome:{'sim' if tem_fome else 'nao'}"
        estado += f"_topicos:{min(n_topicos, 9)}"
        estado += f"_gap:{len(gaps)}"
        estado += f"_ultimo:{self._ultimo_modo or 'nada'}"
        estado += f"_rep:{min(self._n_vezes_mesmo_modo, 5)}"

        return estado, ent_media, tem_fome, gaps, n_topicos, n_bytes, n_palavras

    # ─── FASE 3: EXPLORAR ──────────────────────────────────
    def _fase_explorar(self):
        """Explora o sistema de arquivos por novos dados."""
        log("Explorando...")
        try:
            r = self.curiosidade.ciclo()
            d = r.get('descobertas', 0)
            if d > 0:
                self.total_descobertas += d
                log(f"  Descobriu {d} novos arquivos!")
            return d
        except Exception as e:
            log(f"  Erro na exploracao: {e}")
            return 0

    # ─── FASE 4: PENSAR ────────────────────────────────────
    def _fase_pensar(self):
        """Executa ciclo autonomo de acoes internas."""
        log("Pensando...")
        try:
            passos = MCRDecisorUniversal.decidir_passos("autonomo_pensar",
                {"n_topicos": len(self.cerebro.topicos)})
            self.cerebro.ciclo_autonomo(max_passos=passos)
        except Exception as e:
            log(f"  Erro ao pensar: {e}")

    # ─── FASE 5: WEB SEARCH ────────────────────────────────
    def _fase_web(self):
        """Busca na web topicos que o sistema nao conhece."""
        if not self.cerebro.mk_palavra.freq:
            return
        if self.total_webs >= 3 and self.total_ciclos % 15 != 0:
            return  # max 3 webs a cada 15 ciclos

        # Palavras comuns demais para buscar
        PALAVRAS_IGNORAR = frozenset([
            'mais', 'que', 'para', 'com', 'por', 'como', 'dos', 'das',
            'mas', 'era', 'seu', 'sua', 'tem', 'sao', 'muito', 'pode',
            'quem', 'ate', 'sobre', 'apos', 'antes', 'entre', 'todo',
            'tudo', 'cada', 'vai', 'foi', 'era', 'ser', 'esta',
        ])

        # Encontra palavra com maior entropia e > 4 chars
        maior_ent = 0.0
        palavra_alvo = None
        for palavra in list(self.cerebro.mk_palavra.freq.keys())[:100]:
            if palavra.lower() in PALAVRAS_IGNORAR:
                continue
            if len(palavra) < 5:
                continue
            ent = self.cerebro.mk_palavra.entropia(palavra)
            if ent > maior_ent:
                maior_ent = ent
                palavra_alvo = palavra

        if not palavra_alvo or maior_ent < 0.7:
            return  # entropia nao alta o suficiente

        # Evita buscar a mesma palavra repetidamente
        if hasattr(self, '_ultima_busca') and self._ultima_busca == palavra_alvo:
            return
        self._ultima_busca = palavra_alvo

        log(f"Entropia alta para '{palavra_alvo}' ({maior_ent:.2f}). Buscando na web...")
        try:
            from urllib.request import Request, urlopen
            from urllib.parse import quote
            import re

            url = "https://html.duckduckgo.com/html/?q=" + quote(palavra_alvo)
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=5) as r:
                html = r.read().decode('utf-8', errors='replace')
            snippets = re.findall(
                r'<a rel="nofollow" class="result__a" href="[^"]*">(.*?)</a>',
                html)[:3]

            for s in snippets:
                texto = s.strip()
                if texto:
                    self.cerebro.alimentar(texto, f"web_auto_{palavra_alvo}")
                    self.total_webs += 1
                    log(f"  Aprendido: {texto[:80]}...")
        except Exception as e:
            log(f"  Erro na busca web: {e}")

    # ─── FASE 6: EVOLUIR ───────────────────────────────────
    def _fase_evoluir(self):
        """Auto-evolucao: muta thresholds e valida por entropia."""
        log("Evoluindo...")
        try:
            r = self.cerebro.auto_evolution.ciclo()
            if r.get('mutado'):
                log(f"  Threshold mutado: {r['resultado']}")
        except Exception as e:
            log(f"  Erro na evolucao: {e}")

    # ─── ORQUESTRADOR DO CICLO ─────────────────────────────
    MODOS_CICLICOS = ["explorar", "pensar", "web", "evoluir", "explorar", "pensar"]

    def _decidir_modo(self, estado_str):
        """Decide o modo via Markov (se aprendeu) + epsilon-greedy."""
        # Epsilon-greedy: 15% de chance de explorar modo aleatorio
        if _rand.random() < 0.15:
            return _rand.choice(self.MODOS_CICLICOS)

        modo_pred, conf = self.mk_ciclo.predizer(estado_str)
        if modo_pred and conf > 0.3:
            return modo_pred

        # Estado nunca visto: fallback deterministico pelo hash
        idx = abs(hash(estado_str)) % len(self.MODOS_CICLICOS)
        return self.MODOS_CICLICOS[idx]

    def ciclo(self):
        """Um ciclo completo: passivo → diagnostico → acao → descanso."""
        self.total_ciclos += 1

        # 1. Passivo
        self._fase_passiva()

        # 2. Diagnostico
        estado_str, ent_media, tem_fome, gaps, n_top, n_byte, n_pal = self._fase_diagnostico()

        # 3. Decidir modo
        modo = self._decidir_modo(estado_str)
        self._modo_atual = modo

        # Conta repeticoes do mesmo modo
        if modo == self._ultimo_modo:
            self._n_vezes_mesmo_modo += 1
        else:
            self._n_vezes_mesmo_modo = 0
        self._ultimo_modo = modo

        if self.total_ciclos % 5 == 0 or VERBOSE:
            log(f"Ciclo #{self.total_ciclos} | ent={ent_media:.2f} | modo={modo} | topicos={n_top} | bytes={n_byte}")

        # 4. Executar modo
        if modo == self.MODO_EXPLORAR:
            self._fase_explorar()
        elif modo == self.MODO_PENSAR:
            self._fase_pensar()
        elif modo == self.MODO_WEB:
            self._fase_web()
        elif modo == self.MODO_EVOLUIR:
            self._fase_evoluir()

        # 5. Aprender transicao (modo puro, sem recompensa)
        self.mk_ciclo.aprender(estado_str, modo)

        # 6. Salva estado a cada 10 ciclos
        if self.total_ciclos % 10 == 0:
            self._salvar_estado()

    def _pausa_adaptativa(self):
        """Pausa entre ciclos, ajustada por MCRThreshold."""
        thr = MCRThreshold("autonomo_pausa")
        # Mais pausa se sistema esta estavel (entropia media)
        ent_byte = self.cerebro.mk_byte.entropia_media() if self.cerebro.mk_byte.total > 0 else 1.0
        ent_palavra = self.cerebro.mk_palavra.entropia_media() if self.cerebro.mk_palavra.total > 0 else 1.0
        base = (ent_byte + ent_palavra) / 2  # 0~1
        pausa = max(0.3, min(3.0, base * 2))
        time.sleep(pausa)

    def parar(self):
        self._rodando = False
        self._salvar_estado()
        try: self.cerebro.file_observer.parar()
        except: pass
        log("MCR Autonomo parado.")

    def executar(self):
        """Loop perpetuo — so para com Ctrl+C ou ao fechar."""
        # Inicia observadores
        try:
            self.cerebro.hook_observer.iniciar()
            log("HookObserver iniciado.")
        except Exception as e:
            log(f"HookObserver nao disponivel: {e}")
        try:
            self.cerebro.file_observer.iniciar()
            drives = self.cerebro.file_observer._get_drives()
            log(f"FileObserver monitorando: {' '.join(drives)}")
        except Exception as e:
            log(f"FileObserver nao disponivel: {e}")

        log("=" * 50)
        log("Ciclo perpetuo iniciado. Pressione Ctrl+C para parar.")
        log("=" * 50)

        while self._rodando:
            try:
                self.ciclo()
                self._pausa_adaptativa()
            except KeyboardInterrupt:
                log("Ctrl+C recebido. Parando...")
                break
            except Exception as e:
                log(f"ERRO no ciclo: {e}")
                import traceback
                log(traceback.format_exc())
                time.sleep(1)

        self.parar()


# ═══════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 55)
    print("  MCR AUTONOMO — Aprendizado perpetuo")
    print("  Zero GPU. Zero LLM. Zero dependencias.")
    print("=" * 55)
    print(f"  Log: {LOG_PATH}")
    if not VERBOSE:
        print("  Use --verbose para logs detalhados no terminal.")
    print("=" * 55)
    print("  Pressione Ctrl+C para parar.")
    print("=" * 55)

    aut = MCRAutonomo()
    try:
        aut.executar()
    except KeyboardInterrupt:
        pass
