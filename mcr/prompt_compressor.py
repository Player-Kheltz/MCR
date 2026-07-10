#!/usr/bin/env python3
"""prompt_compressor.py — Compressao de prompt via Selective Context.

Reduce o tamanho do prompt em 50-80% mantendo informacao relevante.

Estrategia:
1. Divide o prompt em paragrafos (por \n\n duplo)
2. Preserva primeiro e ultimo paragrafo (system + pergunta)
3. Para paragrafos intermediarios: remove duplicatas, 
   depois filtra por similaridade Jaccard com a pergunta
   usando threshold adaptativo
"""
import re
from typing import Set


def _tokenizar(texto: str) -> Set[str]:
    """Tokeniza texto em palavras para similaridade Jaccard."""
    return set(re.findall(r'\b[a-zA-ZÀ-ÿ_0-9]{2,}\b', texto.lower()))


def _jaccard(a: Set[str], b: Set[str]) -> float:
    inter = a & b
    uniao = a | b
    return len(inter) / len(uniao) if uniao else 0.0


def _estimar_tokens(texto: str) -> int:
    return max(1, len(texto) // 4)


def comprimir_prompt(prompt: str, pergunta: str, max_tokens: int = 24000) -> str:
    """Comprime prompt mantendo apenas paragrafos relevantes."""
    if _estimar_tokens(prompt) <= max_tokens:
        return prompt

    tokens_pergunta = _tokenizar(pergunta)
    if not tokens_pergunta:
        return prompt

    # Divide em paragrafos
    paragrafos = prompt.split('\n\n')
    
    # Se ha poucos paragrafos mas algum e muito longo, divide por .
    if len(paragrafos) <= 3:
        novos = []
        for p in paragrafos:
            if _estimar_tokens(p) > 500:
                frases = [f.strip() for f in p.split('.') if f.strip() and len(f.strip()) > 10]
                novos.extend(frases)
            else:
                novos.append(p)
        if len(novos) > len(paragrafos):
            paragrafos = novos
        else:
            return prompt  # realmente pouco o que comprimir

    # Preserva primeiro (system) e ultimo (pergunta)
    system = paragrafos[0]
    pergunta_par = paragrafos[-1]
    meio = paragrafos[1:-1]

    # Remove duplicatas do meio
    vistos = set()
    meio_unicos = []
    for p in meio:
        norm = p.strip().lower()
        if norm and norm not in vistos:
            vistos.add(norm)
            meio_unicos.append(p)
        elif not norm:
            meio_unicos.append(p)

    # Se nao ha nada no meio, retorna prompt original
    if not meio_unicos:
        return prompt

    # Filtra por relevancia (threshold adaptativo)
    threshold = 0.05
    while _estimar_tokens('\n\n'.join([system] + meio_unicos + [pergunta_par])) > max_tokens and threshold < 0.95:
        meio_filtrado = []
        for p in meio_unicos:
            p = p.strip()
            if not p or len(p) < 15:
                meio_filtrado.append(p)
                continue
            tokens_p = _tokenizar(p)
            sim = _jaccard(tokens_p, tokens_pergunta)
            if sim >= threshold:
                meio_filtrado.append(p)
        meio_unicos = meio_filtrado
        threshold += 0.05

    resultado = '\n\n'.join([system] + meio_unicos + [pergunta_par])
    return resultado


def comprimir_e_logar(prompt: str, pergunta: str, max_tokens: int = 24000) -> str:
    original = _estimar_tokens(prompt)
    comprimido = comprimir_prompt(prompt, pergunta, max_tokens)
    final = _estimar_tokens(comprimido)
    if final < original:
        print(f'[PromptCompressor] {original} -> {final} tokens ({(1-final/original)*100:.0f}% comprimido)')
    return comprimido
