#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCRAttention — Foco Seletivo para Base Massiva
================================================
Quando o MCR tem milhares de topicos, Markov ordem 1 perde o alvo.
MCRAttention pontua cada candidato por 4 sinais independentes,
combinados pela Equacao MCR.

Sinais:
  prob_markov  → fluencia local (cadeia de Markov)
  fingerprint  → relevancia semantica ao contexto
  jaccard_fonte → pertinencia a pergunta original
  bonus_entropia → novidade util

Uso:
    MCRAttention.gerar(cerebro, "SPA", pergunta="explique SPA")
    MCRAttention.pontuar(cerebro, "SPA e", pergunta="SPA", k=5)
"""
import sys, os, math
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prototipo_mcr_config import C


class MCRAttention:
    """Atencao seletiva pela Equacao MCR.
    
    Pesos descobertos por evolucao (evoluir_autonomo.py).
    Valores iniciais: prob=3, fp=5, jac=4, ent=1.
    
    A cada chamada, pesos podem ser ajustados por MCRThreshold
    baseado no fitness da ultima geracao.
    """
    
    _pesos = {"prob": 3.0, "fp": 5.0, "jac": 4.0, "ent": 1.0}
    _historico_fitness: List[float] = []
    
    @classmethod
    def _topico_relevante(cls, cerebro, pergunta: str) -> Optional[tuple]:
        """Encontra o topico mais relevante para a pergunta.
        
        Usa jaccard entre pergunta e texto do topico.
        Retorna (nome, texto, score) ou None.
        """
        if not pergunta or not cerebro.topicos:
            return None
        from prototipo_agi_completo import MCRByteUtils
        melhor_nome, melhor_texto, melhor_j = None, None, 0.0
        for nome, dados in cerebro.topicos.items():
            texto = dados.get("texto", "")
            if len(texto) < 20:
                continue
            j = MCRByteUtils.jaccard_bytes(pergunta, texto[:500])
            if j > melhor_j:
                melhor_j = j
                melhor_nome = nome
                melhor_texto = texto
        if melhor_j > 0.01:
            return (melhor_nome, melhor_texto, melhor_j)
        return None

    @classmethod
    def _candidatos_do_topico(cls, topico_texto: str, semente: str,
                               k: int) -> List[Tuple[str, float]]:
        """Extrai candidatos de um texto de topico especifico.
        
        Encontra a semente no texto e retorna os tokens seguintes.
        """
        if not topico_texto or not semente:
            return []
        palavras = topico_texto.split()
        ocorrencias = [i for i, p in enumerate(palavras) if p == semente]
        candidatos = {}
        for idx in ocorrencias:
            if idx + 1 < len(palavras):
                prox = palavras[idx + 1]
                candidatos[prox] = candidatos.get(prox, 0) + 1
        total = sum(candidatos.values()) or 1
        return [(tok, cnt / total) for tok, cnt in 
                sorted(candidatos.items(), key=lambda x: -x[1])[:k]]

    @classmethod
    def pontuar(cls, cerebro, contexto: str, pergunta: str = "",
                k: int = 10) -> List[Tuple[str, float]]:
        """Pontua candidatos para continuar o contexto.
        
        Fluxo:
          1. Encontra topico mais relevante para a pergunta
          2. Extrai candidatos desse topico (nao do Markov global)
          3. Pontua cada candidato por 4 sinais da Equacao MCR
        """
        if not contexto:
            return []
        
        from prototipo_agi_completo import MCRByteUtils
        palavras = contexto.split()
        semente = palavras[-1] if palavras else ""
        
        # Stage 1: Encontra o topico mais relevante
        topico = cls._topico_relevante(cerebro, pergunta)
        
        # Stage 2: Extrai candidatos
        if topico:
            _, texto_fonte, _ = topico
            candidatos = cls._candidatos_do_topico(texto_fonte, semente, k * 3)
        else:
            # Fallback: Markov global
            candidatos = cerebro.mk_palavra.predizer_n(semente, k * 3)
        
        if not candidatos:
            return []
        
        # Fingerprint do contexto
        fp_contexto = MCRByteUtils.fingerprint(contexto, C("dim_fingerprint"))
        
        pontuados = []
        for token, prob in candidatos:
            # 1. prob_markov — fluencia local
            s_prob = prob
            
            # 2. fingerprint — relevancia semantica ao contexto
            fp_token = MCRByteUtils.fingerprint(
                f"{contexto} {token}", C("dim_fingerprint"))
            s_fp = MCRByteUtils.similaridade_cosseno(fp_contexto, fp_token)
            
            # 3. jaccard_fonte — pertinencia a pergunta
            s_jac = 0.0
            if pergunta:
                for dados in cerebro.topicos.values():
                    texto = dados.get("texto", "")
                    if token in texto and len(texto) > 20:
                        j = MCRByteUtils.jaccard_bytes(pergunta, texto[:500])
                        if j > s_jac:
                            s_jac = j
            
            # 4. bonus_entropia — entropia media = ideal
            h = cerebro.mk_palavra.entropia(token) if token in cerebro.mk_palavra.freq else 0.5
            s_ent = 1.0 - abs(h - 0.5) * 2
            
            # Equacao MCR
            w = cls._pesos
            nota = (s_prob * w["prob"] + s_fp * w["fp"] + 
                    s_jac * w["jac"] + s_ent * w["ent"])
            nota /= sum(w.values())
            
            pontuados.append((token, round(nota, 4)))
        
        pontuados.sort(key=lambda x: -x[1])
        return pontuados[:k]
    
    @classmethod
    def gerar(cls, cerebro, texto: str, passos: int = None,
              pergunta: str = "") -> str:
        """Gera texto com atencao.
        
        A cada passo, usa MCRAttention.pontuar() em vez de predizer_n().
        O contexto completo e a pergunta original guiam a escolha.
        """
        from prototipo_mcr_config import C as config
        passos = passos or int(config("passos_gerar"))
        palavras = texto.split()
        if not palavras:
            return texto
        
        pergunta = pergunta or texto
        
        for _ in range(passos):
            contexto = " ".join(palavras)
            candidatos = cls.pontuar(cerebro, contexto, pergunta, k=int(config("top_k")) + 2)
            
            if not candidatos:
                break
            
            melhor_token = candidatos[0][0]
            palavras.append(melhor_token)
            
            # Loop detection: 4 tokens iguais consecutivos
            if len(palavras) >= 4 and len(set(palavras[-4:])) == 1:
                break
        
        return " ".join(palavras)
    
    @classmethod
    def comparar(cls, cerebro, semente: str, pergunta: str = "",
                 passos: int = 6) -> Dict:
        """Compara geracao com e sem atencao."""
        from prototipo_agi_completo import MCRByteUtils
        
        # Sem atencao (Markov puro)
        antes = cerebro._gerar_original(semente, passos)
        
        # Com atencao
        depois = cls.gerar(cerebro, semente, passos, pergunta)
        
        j_antes = MCRByteUtils.jaccard_bytes(pergunta or semente, antes)
        j_depois = MCRByteUtils.jaccard_bytes(pergunta or semente, depois)
        
        return {
            "semente": semente,
            "pergunta": pergunta,
            "sem_atencao": antes,
            "com_atencao": depois,
            "jaccard_sem": round(j_antes, 3),
            "jaccard_com": round(j_depois, 3),
            "melhorou": j_depois > j_antes,
        }
    
    @classmethod
    def evoluir_pesos(cls, cerebro, geracoes: int = 30) -> Dict:
        """Evolui pesos para maximizar fitness.
        
        Fitness = jaccard medio entre texto gerado e texto fonte.
        Cada geracao: muta um peso, testa, mantem se melhor.
        """
        from prototipo_agi_completo import MCRByteUtils
        import random as _rand
        
        historico = []
        melhor_fitness = -1
        melhores_pesos = dict(cls._pesos)
        
        sementes = list(cerebro.topicos.keys())[:5] if cerebro.topicos else ["SPA", "MCR"]
        
        for ger in range(geracoes):
            fitness_total = 0.0
            n_testes = 0
            
            for semente in sementes:
                texto_fonte = cerebro.topicos.get(semente, {}).get("texto", semente)[:200]
                if len(texto_fonte) < 10:
                    continue
                gerado = cls.gerar(cerebro, texto_fonte[:20], 4, texto_fonte)
                j = MCRByteUtils.jaccard_bytes(texto_fonte, gerado)
                fitness_total += j
                n_testes += 1
            
            fitness = fitness_total / max(n_testes, 1) if n_testes > 0 else 0
            
            if fitness > melhor_fitness:
                melhor_fitness = fitness
                melhores_pesos = dict(cls._pesos)
                historico.append({"geracao": ger, "fitness": round(fitness, 4), "pesos": dict(cls._pesos)})
            
            # Muta um peso aleatorio
            chave = _rand.choice(list(cls._pesos.keys()))
            delta = _rand.choice([-0.5, -0.3, 0.3, 0.5])
            cls._pesos[chave] = max(0.1, cls._pesos[chave] + delta)
        
        # Restaura melhores pesos
        cls._pesos = melhores_pesos
        cls._historico_fitness.append(melhor_fitness)
        
        return {
            "fitness_final": round(melhor_fitness, 4),
            "pesos_finais": melhores_pesos,
            "historico": historico[-5:] if historico else [],
        }
    
    @classmethod
    def stats(cls) -> Dict:
        return {
            "pesos": dict(cls._pesos),
            "fitness_medio": round(
                sum(cls._historico_fitness) / max(len(cls._historico_fitness), 1), 4
            ) if cls._historico_fitness else 0,
        }
