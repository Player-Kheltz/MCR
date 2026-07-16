"""
mcr.template_entropico — Template Estrutural Universal por Entropia Diferencial.

Principio: Dadas N sequencias do mesmo tipo (sprites, scripts, nomes, audio),
a entropia de Shannon em cada posicao revela:
  - Baixa entropia (< limiar) → ESTRUTURA INVARIANTE
  - Alta entropia (>= limiar) → GAP CRIATIVO

Zero hardcode. A entropia decide o que e estrutura e o que e gap.
Funciona para qualquer dominio: texto, codigo, sprites, audio, mapas.
"""
import math, random
from collections import Counter
from typing import List, Tuple, Dict, Optional


def entropia_shannon(sequencia) -> float:
    if not sequencia:
        return 0.0
    c = Counter(sequencia)
    n = len(sequencia)
    h = 0.0
    for v in c.values():
        p = v / n
        if p > 0:
            h -= p * math.log2(p)
    max_h = math.log2(min(len(c), n))
    return h / max_h if max_h > 0 else 0.0


def extrair_template_entropico(
    sequencias: List[List],
    limiar_entropia: float = 0.5,
) -> List[Tuple[str, any]]:
    """
    Extrai template estrutural universal de N sequencias.
    
    Args:
        sequencias: lista de listas de tokens (todas do mesmo tipo)
        limiar_entropia: abaixo disso e estrutura, acima e gap
    
    Returns:
        template: lista de tuplas (tipo, valor)
                 tipo='fixo' → valor e o token mais comum
                 tipo='gap'  → valor e a distribuicao (Counter)
    """
    if not sequencias:
        return []
    
    max_len = max(len(seq) for seq in sequencias)
    template = []
    
    for pos in range(max_len):
        tokens_na_posicao = []
        for seq in sequencias:
            if pos < len(seq):
                tokens_na_posicao.append(seq[pos])
        
        if not tokens_na_posicao:
            continue
        
        h = entropia_shannon(tokens_na_posicao)
        
        if h < limiar_entropia:
            mais_comum = Counter(tokens_na_posicao).most_common(1)[0][0]
            template.append(('fixo', mais_comum, h))
        else:
            distribuicao = Counter(tokens_na_posicao)
            template.append(('gap', distribuicao, h))
    
    return template


def gerar_do_template(
    template: List[Tuple[str, any]],
    temperatura: float = 0.8,
) -> List:
    """
    Gera nova sequencia a partir do template entropico.
    
    Para posicoes 'fixo': usa o valor do template.
    Para posicoes 'gap': amostra probabilisticamente da distribuicao.
    """
    resultado = []
    
    for tipo, valor, h in template:
        if tipo == 'fixo':
            resultado.append(valor)
        else:
            distribuicao = valor
            tokens = list(distribuicao.keys())
            if not tokens:
                continue
            total = sum(distribuicao.values())
            if total == 0:
                continue
            # Aplicar temperatura na distribuicao
            pesos = [
                (distribuicao[t] / total) ** (1.0 / max(temperatura, 0.01))
                for t in tokens
            ]
            total_peso = sum(pesos)
            if total_peso <= 0:
                resultado.append(tokens[0])
                continue
            r = random.random() * total_peso
            acum = 0.0
            escolhido = tokens[0]
            for token, peso in zip(tokens, pesos):
                acum += peso
                if r <= acum:
                    escolhido = token
                    break
            resultado.append(escolhido)
    
    return resultado


def resumir_template(template: List[Tuple]) -> str:
    """Retorna resumo textual do template."""
    partes = []
    fixos = 0
    gaps = 0
    h_media = 0.0
    for tipo, valor, h in template:
        if tipo == 'fixo':
            fixos += 1
            partes.append(f"[{valor}]")
        else:
            gaps += 1
            n_uniq = len(valor)
            partes.append(f"[{n_uniq}opts]")
        h_media += h
    h_media /= max(len(template), 1)
    return (f'{len(template)} posicoes: {fixos} fixas + {gaps} gaps, '
            f'H_media={h_media:.3f}')
