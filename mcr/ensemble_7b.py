#!/usr/bin/env python3
"""ensemble_7b.py — Ensemble de modelos 7B com juiz simbólico.

Para perguntas complexas, 3 modelos 7B geram respostas em paralelo.
O juiz simbólico (Jaccard + entropia) seleciona a melhor.

Uso:
    ens = Ensemble7B()
    resultado = ens.gerar("Explique o SPA")
    # → {"resposta": "...", "consenso": True, "entropia": 0.3}
"""
import json, time, urllib.request, concurrent.futures
from typing import Dict, List, Optional
from collections import Counter

OLLAMA_URL = "http://localhost:11434/api/generate"

from mcr.config_llm import MODELOS, MODELO


def _chamar_llm(modelo: str, prompt: str, timeout: int = 120) -> str:
    """Chama LLM via Ollama API."""
    try:
        payload = json.dumps({
            "model": modelo,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_ctx": 32768}
        }).encode()
        req = urllib.request.Request(OLLAMA_URL, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")
    except Exception as e:
        return f"[Erro no modelo {modelo}: {e}]"


def _tokenizar(texto: str) -> set:
    """Tokeniza texto para similaridade Jaccard."""
    import re
    return set(re.findall(r'\b[a-zA-ZÀ-ÿ_0-9]{2,}\b', texto.lower()))


def _jaccard(a: set, b: set) -> float:
    inter = a & b
    uniao = a | b
    return len(inter) / len(uniao) if uniao else 0.0


def _entropia(texto: str) -> float:
    """Entropia de Shannon do texto (baixa = mais coerente/previsivel)."""
    import math
    from collections import Counter
    tokens = _tokenizar(texto)
    if not tokens:
        return 1.0
    total = len(tokens)
    h = 0.0
    freq = Counter(t.lower() for t in texto.split())
    for count in freq.values():
        p = count / max(total, 1)
        if p > 0:
            h -= p * math.log2(p)
    return h / math.log2(max(len(freq), 2)) if len(freq) > 1 else 0.0


class Ensemble7B:
    """Ensemble de 3 modelos 7B com juiz simbólico."""

    def __init__(self):
        self._stats = {
            'total': 0, 'consenso': 0, 'sem_consenso': 0,
            'tempo_total': 0.0,
        }

    def gerar(self, prompt: str, timeout: int = 120) -> Dict:
        """Gera resposta usando ensemble de 3 modelos.

        Args:
            prompt: prompt completo (com system + contexto + pergunta)
            timeout: timeout por modelo

        Returns:
            dict com resposta, consenso, entropia, detalhes
        """
        self._stats['total'] += 1
        t0 = time.time()

        # 1. Chama modelos em paralelo
        respostas = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futuros = {
                executor.submit(_chamar_llm, modelo, prompt, timeout): nome
                for modelo, nome in MODELOS
            }
            for futuro in concurrent.futures.as_completed(futuros):
                nome = futuros[futuro]
                try:
                    respostas[nome] = futuro.result()
                except Exception as e:
                    respostas[nome] = f"[Erro: {e}]"

        # 2. Calcula similaridades e entropia
        detalhes = []
        tokens_por_modelo = {}
        for nome, resp in respostas.items():
            tokens_por_modelo[nome] = _tokenizar(resp)
            detalhes.append({
                'modelo': nome,
                'tamanho': len(resp),
                'entropia': round(_entropia(resp), 4),
                'erro': resp.startswith('[Erro'),
            })

        # 3. Juiz simbólico: encontra consenso por Jaccard
        melhor_consenso = ('', 0.0)
        pares_modelos = list(respostas.keys())

        for i in range(len(pares_modelos)):
            for j in range(i + 1, len(pares_modelos)):
                a, b = pares_modelos[i], pares_modelos[j]
                sim = _jaccard(tokens_por_modelo[a], tokens_por_modelo[b])
                if sim > melhor_consenso[1]:
                    melhor_consenso = (f"{a} x {b}", sim)

        # 4. Decide resposta final
        consenso = melhor_consenso[1] >= 0.3
        if consenso:
            self._stats['consenso'] += 1
            # Escolhe a resposta com menor entropia entre as que têm consenso
            candidatas = [
                (nome, respostas[nome], _entropia(respostas[nome]))
                for nome in respostas
                if not respostas[nome].startswith('[Erro')
            ]
            candidatas.sort(key=lambda x: x[2])  # menor entropia primeiro
            resposta_final = candidatas[0][1]
            entropia_final = candidatas[0][2]
        else:
            self._stats['sem_consenso'] += 1
            # Sem consenso: escolhe a de menor entropia
            candidatas = [
                (nome, respostas[nome], _entropia(respostas[nome]))
                for nome in respostas
                if not respostas[nome].startswith('[Erro')
            ]
            if candidatas:
                candidatas.sort(key=lambda x: x[2])
                resposta_final = candidatas[0][1]
                entropia_final = candidatas[0][2]
            else:
                resposta_final = "[Todos os modelos falharam]"
                entropia_final = 1.0

        tempo = round(time.time() - t0, 2)
        self._stats['tempo_total'] += tempo

        return {
            'resposta': resposta_final,
            'consenso': consenso,
            'similaridade_max': round(melhor_consenso[1], 4),
            'entropia': round(entropia_final, 4),
            'tempo': tempo,
            'detalhes': detalhes,
        }

    def estatisticas(self) -> Dict:
        total = max(self._stats['total'], 1)
        return {
            'total': self._stats['total'],
            'consenso': self._stats['consenso'],
            'sem_consenso': self._stats['sem_consenso'],
            'taxa_consenso': round(self._stats['consenso'] / total * 100, 1),
            'tempo_medio': round(self._stats['tempo_total'] / total, 1),
        }
