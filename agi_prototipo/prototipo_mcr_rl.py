#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 3: MCRRL — Aprendizado por Reforco
=========================================
Q-learning simplificado usando Markov chains.
O MCR aprende nao apenas por acumulacao, mas por REcompensa.
"""
import sys, os, math, random as _rand
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_agi_completo import (
    MCR, MCRByteUtils, MCRSignatureExpansiva, MCRThreshold,
    MCREntropia, EstadoMundo, MotorFisica
)
from prototipo_mcr_config import C


class MCRReward:
    """Sistema de recompensa: avalia automaticamente o resultado de uma acao.
    
    Fontes de recompensa:
      - Aproximacao: quanto mais perto do objetivo, maior a recompensa
      - Sucesso: acao foi bem-sucedida na fisica
      - Novidade: entropia alta = nova descoberta
      - Eficiencia: poucos passos = bonus
    """
    def __init__(self):
        self.mk = MCR("reward")
        self.threshold = MCRThreshold("reward")
        self.historico_recompensas: List[float] = []
        self.total_recompensas = 0

    def avaliar(self, estado_atual: EstadoMundo, estado_anterior: EstadoMundo,
                estado_objetivo: EstadoMundo = None, acao_bem_sucedida: bool = True) -> float:
        """Calcula recompensa automatica para (estado_anterior + acao -> estado_atual)."""
        r = 0.0

        # 1. Aproximacao do objetivo (se fornecido)
        if estado_objetivo:
            dist_antes = MCRByteUtils.similaridade_cosseno(
                estado_anterior.fingerprint(C("dim_fingerprint")), estado_objetivo.fingerprint(C("dim_fingerprint")))
            dist_depois = MCRByteUtils.similaridade_cosseno(
                estado_atual.fingerprint(C("dim_fingerprint")), estado_objetivo.fingerprint(C("dim_fingerprint")))
            r += (dist_depois - dist_antes) * 10  # [-10, +10]

        # 2. Sucesso da acao
        if acao_bem_sucedida:
            r += C("rl_recompensa_sucesso")

        # 3. Novidade (entropia alta = exploracao valiosa)
        h = MCRByteUtils.entropia_bytes(estado_atual.serializar())
        if h > C("gap_entropia_alta"):
            r += C("rl_recompensa_novidade")

        # 4. Mudanca de estado significativa
        sim = MCRByteUtils.similaridade_cosseno(
            estado_atual.fingerprint(C("dim_fingerprint")), estado_anterior.fingerprint(C("dim_fingerprint")))
        if sim < 0.95:
            r += C("rl_recompensa_mudanca")  # mudou algo

        r = max(-10.0, min(10.0, r))
        self.historico_recompensas.append(r)
        self.total_recompensas += 1
        self.mk.aprender(f"REWARD:{r:.1f}", f"total:{self.total_recompensas}")
        return r


class MCRQLearn:
    """Q-learning simplificado usando Markov.
    
    Q(s,a) = recompensa + gamma * max_a' Q(s',a')
    
    Armazenado como transicoes no MCR:
      mk_Q: "Q:{fp_estado}:{acao}" -> valor_Q
    """
    def __init__(self, gamma: float = C("rl_gamma"), alpha: float = C("rl_alpha")):
        self.mk_Q = MCR("qlearn")
        self.mk_politica = MCR("politica")
        self.gamma = gamma
        self.alpha = alpha
        self.threshold = MCRThreshold("qlearn")
        self.entropia = MCREntropia("qlearn")
        self.episodio = 0
        self.total_passos = 0
        self.historico_episodios: List[Dict] = []

    def q_valor(self, estado: EstadoMundo, acao: str) -> float:
        """Retorna Q(s,a)."""
        chave = f"Q:{str(estado.fingerprint(C("dim_fingerprint"))[:2])}:{acao}"
        pred, conf = self.mk_Q.predizer(chave)
        if pred and conf > 0:
            try:
                return float(pred)
            except ValueError:
                return 0.0
        return 0.0

    def atualizar(self, estado: EstadoMundo, acao: str,
                  recompensa: float, proximo_estado: EstadoMundo):
        """Q-learning update: Q(s,a) += alpha * (r + gamma * max Q(s',a') - Q(s,a))."""
        chave = f"Q:{str(estado.fingerprint(C("dim_fingerprint"))[:2])}:{acao}"
        q_atual = self.q_valor(estado, acao)

        # max_a' Q(s',a')
        acoes_possiveis = MotorFisica.ACOES if hasattr(MotorFisica, "ACOES") else \
            ["andar_cima", "andar_baixo", "andar_esq", "andar_dir",
             "empurrar", "abrir", "atacar"]
        max_q_futuro = max(
            self.q_valor(proximo_estado, a) for a in acoes_possiveis
        ) if acoes_possiveis else 0.0

        # Q-learning formula
        td_target = recompensa + self.gamma * max_q_futuro
        td_error = td_target - q_atual
        novo_q = q_atual + self.alpha * td_error

        self.mk_Q.aprender(chave, f"{novo_q:.4f}")

        # Atualiza politica: melhor acao para este estado
        melhor_acao = self.melhor_acao(estado)
        if melhor_acao:
            fp_estado = str(estado.fingerprint(C("dim_fingerprint")))
            self.mk_politica.aprender(fp_estado, melhor_acao)

        self.total_passos += 1
        self.threshold.observar(abs(td_error))

    def melhor_acao(self, estado: EstadoMundo,
                    acoes_disponiveis: List[str] = None) -> Optional[str]:
        """Retorna a acao com maior Q(s,*) para este estado."""
        if acoes_disponiveis is None:
            acoes_disponiveis = ["andar_cima", "andar_baixo", "andar_esq", "andar_dir",
                                 "empurrar", "abrir", "atacar"]
        if not acoes_disponiveis:
            return None
        return max(acoes_disponiveis, key=lambda a: self.q_valor(estado, a))

    def escolher_acao(self, estado: EstadoMundo, epsilon: float = C("rl_epsilon_inicial"),
                      acoes_disponiveis: List[str] = None) -> str:
        """epsilon-greedy: explora ou explota."""
        if acoes_disponiveis is None:
            acoes_disponiveis = ["andar_cima", "andar_baixo", "andar_esq", "andar_dir",
                                 "empurrar", "abrir", "atacar"]
        if not acoes_disponiveis:
            return "andar_cima"

        if _rand.random() < epsilon:
            return _rand.choice(acoes_disponiveis)
        return self.melhor_acao(estado, acoes_disponiveis) or acoes_disponiveis[0]

    def episodio_treino(self, estado_inicial: EstadoMundo,
                        estado_objetivo: EstadoMundo,
                        max_passos: int = 20) -> Dict:
        """Executa um episodio completo de treino."""
        estado = estado_inicial.clone()
        recompensa_total = 0.0
        acoes_executadas = []
        passo = 0

        for passo in range(max_passos):
            acao = self.escolher_acao(estado, epsilon=max(C("rl_epsilon_min"), C("rl_epsilon_inicial") - self.episodio * C("rl_epsilon_decay")))
            proximo_estado = MotorFisica.executar(estado, acao)

            acao_mudou_estado = proximo_estado.serializar() != estado.serializar()
            reward = MCRReward().avaliar(proximo_estado, estado, estado_objetivo, acao_mudou_estado)

            self.atualizar(estado, acao, reward, proximo_estado)
            recompensa_total += reward
            acoes_executadas.append(acao)
            estado = proximo_estado

            # Criterio de objetivo: heroi chegou na posicao alvo
            heroi = estado.get("heroi")
            heroi_obj = estado_objetivo.get("heroi")
            chegou = False
            if heroi and heroi_obj:
                dx = abs(heroi.props.get("x", 0) - heroi_obj.props.get("x", 0))
                dy = abs(heroi.props.get("y", 0) - heroi_obj.props.get("y", 0))
                if dx + dy <= 1:
                    chegou = True

            if not chegou:
                sim_obj = MCRByteUtils.similaridade_cosseno(
                    estado.fingerprint(C("dim_fingerprint")), estado_objetivo.fingerprint(C("dim_fingerprint")))
                if sim_obj > C("conf_maxima"):
                    chegou = True

            if chegou:
                break

        self.episodio += 1
        resultado = {
            "episodio": self.episodio,
            "passos": passo + 1,
            "recompensa_total": round(recompensa_total, 2),
            "acoes": acoes_executadas[:C("limite_busca")],
        }
        self.historico_episodios.append(resultado)
        self.mk_Q.aprender(f"EP:{self.episodio}", f"R:{recompensa_total:.1f}_P:{passo+1}")
        return resultado

    def stats(self) -> Dict:
        return {
            "episodios": self.episodio,
            "passos_totais": self.total_passos,
            "estados_q": self.mk_Q.total,
            "gamma": self.gamma,
            "alpha": self.alpha,
            "ultima_recompensa_media": round(
                sum(e["recompensa_total"] for e in self.historico_episodios[-C("janela_entropia"):]) / 10
                if len(self.historico_episodios) >= 10 else 0, 2),
            "politicas_aprendidas": self.mk_politica.total,
        }


class MCRRL:
    """Integrador de aprendizado por reforco.
    
    Combina MCRReward + MCRQLearn em uma interface unificada.
    """
    def __init__(self, gamma: float = C("rl_gamma"), alpha: float = C("rl_alpha")):
        self.reward = MCRReward()
        self.qlearn = MCRQLearn(gamma, alpha)
        self.mk = MCR("rl_integrador")
        self.total_acoes = 0

    def agir(self, estado: EstadoMundo, acao: str,
             estado_objetivo: EstadoMundo = None) -> Tuple[EstadoMundo, float, float]:
        """Executa acao, recebe recompensa, aprende."""
        proximo_estado = MotorFisica.executar(estado, acao)
        acao_mudou = proximo_estado.serializar() != estado.serializar()
        recompensa = self.reward.avaliar(proximo_estado, estado, estado_objetivo, acao_mudou)
        self.qlearn.atualizar(estado, acao, recompensa, proximo_estado)
        self.total_acoes += 1
        self.mk.aprender(f"AGIR:{acao}", f"R:{recompensa:.1f}")
        return proximo_estado, recompensa

    def escolher_acao(self, estado: EstadoMundo, epsilon: float = C("rl_epsilon_inicial")) -> str:
        return self.qlearn.escolher_acao(estado, epsilon)

    def convergiu(self, janela: int = 20) -> bool:
        """True se a politica estabilizou (recompensa media estagnou)."""
        if len(self.qlearn.historico_episodios) < janela:
            return False
        recentes = [e["recompensa_total"] for e in self.qlearn.historico_episodios[-janela:]]
        return max(recentes) - min(recentes) < 1.0

    def stats(self) -> Dict:
        return self.qlearn.stats()
