#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 7: MCRMind — Consciencia Operacional 24/7
================================================
Integra TODOS os modulos em um unico sistema autonomo.
Roda 24/7, aprende sozinho, se modifica, interage via chat.

Modos:
  --daemon:  executa em background, ciclo dormir/acordar
  --chat:    interface REPL de conversacao
  --batch:   executa N ciclos de auto-melhoria e sai
"""
import sys, os, json, time, threading, traceback
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import (
    MCR, MCRByteUtils, MCRSignatureExpansiva, MCRThreshold,
    MCREntropia, CerebroAGI, EstadoMundo, MotorFisica,
    Entidade
)
from prototipo_mcr_hq import MCRMemory, MCRIndex
from prototipo_mcr_rl import MCRRL, MCRReward, MCRQLearn
from prototipo_mcr_codex import MCRCodex, MCRSelfTest
from prototipo_mcr_bridge import MCRBridge, MCRCrossDomain
from prototipo_mcr_genesis import MCRGenesis
from prototipo_mcr_config import C


class MCRMind:
    """Consciencia operacional: todos os modulos integrados em um loop vital.
    
    Ciclo vital (a cada tick):
      1. PERCEPCAO: processa entrada (texto ou acao)
      2. RACIOCINIO: gera plano ou resposta
      3. ACAO: executa e aprende
      4. REFLEXAO: auto-diagnostico e melhoria
      C("limite_busca") // 2. PERSISTENCIA: salva estado
    
    Ciclo noturno (a cada 1000 ticks ou dormir() explicito):
      1. Replay de experiencias
      2. Genesis: detecta gaps e cria modulos
      3. Codex: substitui hardcodes
      4. Evolution: testa variacoes de parametros
    """
    def __init__(self, db_path: str = "mind_hq.db"):
        # Nucleo
        self.cerebro = CerebroAGI()
        
        # Fase 1: Memoria (usa :memory: se db_path vazio)
        self._db_path = db_path
        self.memoria = MCRMemory(db_path if db_path else ":memory:")
        self.index = MCRIndex(self.memoria)
        
        # Fase 2: Auto-modificacao
        self.codex = MCRCodex(self.cerebro)
        self.selftest = MCRSelfTest()
        
        # Fase 3: Reforco
        self.rl = MCRRL()
        
        # Fase C("limite_busca") // 2: Bridge
        self.bridge = MCRBridge()
        self.crossdomain = MCRCrossDomain(self.bridge)
        
        # Fase 6: Genesis
        self.genesis = MCRGenesis(self.cerebro)
        
        # Estado interno
        self.tick = 0
        self.estado_mundo = EstadoMundo.criar_simples()
        self.objetivo_atual = ""
        self.planos_cache: Dict[str, List[str]] = {}
        self.threshold = MCRThreshold("mind")
        self.entropia = MCREntropia("mind")
        self.log: List[Dict] = []
        self.rodando = True
        self.pausado = False

    def percepcao(self, entrada: str) -> Dict:
        """Processa uma entrada (texto, acao, comando)."""
        entrada = entrada.strip()
        if not entrada:
            return {"tipo": "vazio"}
        
        # Comandos especiais
        if entrada.startswith("/"):
            return self._comando(entrada[1:])
        
        self.tick += 1
        self.cerebro.alimentar(entrada, f"percepcao:{self.tick}")
        
        # Tenta entender como instrucao
        acoes = self.crossdomain.entender_instrucao(entrada)
        if acoes:
            for acao in acoes[:C("top_k")]:
                novo_estado = MotorFisica.executar(self.estado_mundo, acao)
                self.cerebro.aprender_causal(self.estado_mundo, acao, novo_estado)
                self.memoria.salvar_causal(self.estado_mundo, acao, novo_estado)
                
                # RL
                prox, recompensa = self.rl.agir(self.estado_mundo, acao)
                self.estado_mundo = prox
            
            return {
                "tipo": "acao",
                "acoes": acoes,
                "tick": self.tick,
            }
        
        # Processa como conhecimento
        self.memoria.salvar_estado(self.estado_mundo)
        self.index.indexar(entrada, f"entrada:{self.tick}")
        
        return {
            "tipo": "conhecimento",
            "chars": len(entrada),
            "tick": self.tick,
        }

    def razao(self, pergunta: str) -> str:
        """Gera uma resposta usando todos os modulos disponiveis."""
        self.tick += 1
        self.cerebro.alimentar(pergunta, f"pergunta:{self.tick}")
        
        # 1. Tenta buscar na memoria
        fp = MCRByteUtils.fingerprint(pergunta, C("dim_fingerprint"))
        similares = self.memoria.buscar_estado_similar(str(fp), limite = C("top_k") + 2)
        if similares:
            _, serial, sim = similares[0]
            if sim > C("bridge_sim_transferencia"):
                return f"[Memoria] {serial[:80]}"
        
        # 2. Tenta gerar com coupling
        gerado = self.cerebro.gerar(pergunta, passos = C("passos_gerar"))
        j = MCRByteUtils.jaccard_bytes(pergunta, gerado)
        if j < 0.8 and len(gerado) > len(pergunta):
            return f"[Geracao] {gerado}"
        
        # 3. Tenta planejar
        try:
            plan = self.cerebro.planejar(pergunta, self.estado_mundo)
            if plan["plano"]:
                return f"[Plano] {' -> '.join(plan['plano'])} (nota={plan['nota']})"
        except Exception:
            pass
        
        # 4. Fallback: geracao simples
        return f"[MCR] {gerado[:C("historico_max")]}"

    def dormir(self):
        """Ciclo noturno de auto-melhoria."""
        print(f"\n[MCRMind] Dormindo (tick {self.tick})...")
        
        # 1. Genesis: detecta gaps e cria modulos
        diag = self.genesis.diagnosticar_gap()
        if diag["total"] > 0:
            print(f"  Gaps detectados: {diag['total']} (severidade={diag['severidade_media']})")
            resultado = self.genesis.genesis_loop(max_ciclos=3)
            print(f"  Genesis: {resultado['modulos_criados']} modulos criados")
        
        # 2. Codex: substitui hardcodes
        arquivo_alvo = os.path.join(os.path.dirname(__file__), "prototipo_agi_completo.py")
        resultado_codex = self.codex.evoluir(arquivo_alvo, max_iter = C("max_iter") // 3)
        if resultado_codex["modificacoes"]:
            print(f"  Codex: {len(resultado_codex['modificacoes'])} modificacoes")
        
        # 3. Persiste estado
        self.memoria.salvar_estado(self.estado_mundo)
        
        # 4. Registro
        entry = {
            "tick": self.tick,
            "tipo": "dormir",
            "gaps": diag["total"],
            "modulos_criados": resultado["modulos_criados"] if diag["total"] > 0 else 0,
            "modificacoes_codex": len(resultado_codex["modificacoes"]),
        }
        self.log.append(entry)
        print(f"[MCRMind] Acordou (tick {self.tick})\n")

    def _comando(self, cmd: str) -> Dict:
        """Processa comandos especiais."""
        partes = cmd.split()
        if not partes:
            return {"tipo": "comando_invalido"}
        
        comando = partes[0].lower()
        
        if comando == "status":
            return {"tipo": "status", "dados": self.stats()}
        elif comando == "dormir":
            self.dormir()
            return {"tipo": "dormir"}
        elif comando == "diagnostico":
            diag = self.genesis.diagnosticar_gap()
            return {"tipo": "diagnostico", "dados": diag}
        elif comando == "plano":
            objetivo = " ".join(partes[1:])
            plan = self.cerebro.planejar(objetivo, self.estado_mundo)
            return {"tipo": "plano", "dados": plan}
        elif comando == "genesis":
            resultado = self.genesis.genesis_loop(max_ciclos=5)
            return {"tipo": "genesis", "dados": resultado}
        elif comando == "codex":
            arquivo = os.path.join(os.path.dirname(__file__), "prototipo_agi_completo.py")
            resultado = self.codex.evoluir(arquivo, max_iter = C("max_iter") // 3)
            return {"tipo": "codex", "dados": resultado}
        elif comando == "mundo":
            return {"tipo": "mundo", "dados": self.estado_mundo.serializar()[:200]}
        elif comando == "help":
            return {"tipo": "help", "comandos": [
                "/status", "/dormir", "/diagnostico", "/plano <obj>",
                "/genesis", "/codex", "/mundo", "/help"
            ]}
        else:
            return {"tipo": "comando_invalido", "comando": comando}

    def chat(self):
        """Loop REPL de conversacao."""
        print()
        print("#" * 55)
        print("  MCRMind — Modo Chat")
        print("  Digite /help para comandos, 'sair' para encerrar")
        print("#" * 55)
        print()
        
        while True:
            try:
                entrada = input("voce: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[MCRMind] Encerrando chat...")
                break
            
            if not entrada:
                continue
            if entrada.lower() in ("sair", "exit", "quit"):
                print("[MCRMind] Ate logo!")
                break
            
            resultado = self.percepcao(entrada)
            
            if resultado["tipo"] == "comando":
                cmd_result = self._comando(entrada[1:])
                if cmd_result["tipo"] == "help":
                    for c in cmd_result["comandos"]:
                        print(f"  {c}")
                elif cmd_result["tipo"] == "status":
                    s = cmd_result["dados"]
                    for k, v in s.items():
                        print(f"  {k}: {v}")
                elif cmd_result["tipo"] == "diagnostico":
                    for g in cmd_result["dados"]["gaps"]:
                        print(f"  Gap: {g['nome']} ({g['severidade']}) — {g['sugestao']}")
                elif cmd_result["tipo"] == "plano":
                    print(f"  Plano: {cmd_result['dados']['plano']}")
                elif cmd_result["tipo"] == "genesis":
                    print(f"  Genesis: {cmd_result['dados']['modulos_criados']} modulos")
                elif cmd_result["tipo"] == "codex":
                    print(f"  Codex: {len(cmd_result['dados']['modificacoes'])} modificacoes")
                elif cmd_result["tipo"] == "mundo":
                    print(f"  Mundo: {cmd_result['dados']}")
            else:
                resposta = self.razao(entrada)
                print(f"  MCR: {resposta}")

    def daemon(self, intervalo: float = 5.0):
        """Loop autonomo em background."""
        print(f"\n[MCRMind] Daemon iniciado (intervalo={intervalo}s)")
        while self.rodando:
            if not self.pausado:
                # Ciclo vital
                self.tick += 1
                self._ciclo_autonomo()
                
                # A cada 100 ticks, dorme
                if self.tick % C("ambiente_ticks_por_dia") == 0:
                    self.dormir()
            
            time.sleep(intervalo)
        
        print("[MCRMind] Daemon encerrado")

    def _ciclo_autonomo(self):
        """Um ciclo de vida autonomo sem entrada externa."""
        # Explora o mundo
        acao = self.rl.escolher_acao(self.estado_mundo)
        novo_estado = MotorFisica.executar(self.estado_mundo, acao)
        self.cerebro.aprender_causal(self.estado_mundo, acao, novo_estado)
        self.memoria.salvar_causal(self.estado_mundo, acao, novo_estado)
        self.rl.agir(self.estado_mundo, acao)
        self.estado_mundo = novo_estado

    def stats(self) -> Dict:
        return {
            "tick": self.tick,
            "estado_mundo": self.estado_mundo.serializar()[:40],
            "memoria": self.memoria.estatisticas(),
            "rl": self.rl.stats(),
            "genesis": self.genesis.stats(),
            "codex": self.codex.stats(),
            "bridge": self.bridge.stats(),
            "causal_exemplos": len(self.cerebro.world.historico),
            "topicos": len(self.cerebro.topicos),
            "log_size": len(self.log),
        }

    def relatorio(self) -> str:
        s = self.stats()
        linhas = []
        linhas.append("#" * 55)
        linhas.append("  MCRMind — Relatorio Operacional")
        linhas.append("#" * 55)
        linhas.append(f"  Tick: {s['tick']}")
        linhas.append(f"  Topicos: {s['topicos']}")
        linhas.append(f"  Causais: {s['causal_exemplos']}")
        linhas.append(f"  Memoria: estados={s['memoria']['estados']}, "
                      f"causais={s['memoria']['causais']}, planos={s['memoria']['planos']}")
        linhas.append(f"  RL: episodios={s['rl']['episodios']}, "
                      f"politicas={s['rl']['politicas_aprendidas']}")
        linhas.append(f"  Genesis: {s['genesis']}")
        linhas.append(f"  Codex: {s['codex']}")
        linhas.append(f"  Bridge: {s['bridge']}")
        linhas.append(f"  Log: {s['log_size']} entradas")
        linhas.append("#" * 55)
        return '\n'.join(linhas)


def main():
    args = sys.argv[1:]
    
    mind = MCRMind()
    
    if "--chat" in args:
        mind.chat()
    elif "--daemon" in args:
        try:
            mind.daemon(intervalo=2.0)
        except KeyboardInterrupt:
            print("\n[MCRMind] Daemon interrompido")
    elif "--batch" in args:
        n = 10
        for i in range(args.index("--batch") + 1, len(args)):
            try:
                n = int(args[i])
                break
            except ValueError:
                continue
        
        for ciclo in range(n):
            mind._ciclo_autonomo()
            if ciclo % 10 == 0:
                mind.dormir()
        
        print(mind.relatorio())
    else:
        # Modo interativo padrao
        mind.chat()


if __name__ == "__main__":
    main()
