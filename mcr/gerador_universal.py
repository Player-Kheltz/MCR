"""gerador_universal.py — Geração por componentes + Auto-dataset.

Princípios MCR:
  Template + gaps — extrair_template_entropico descobre estrutura vs variável
  Mesmo motor, N domínios — funciona pra Lua, JSON, PNG, qualquer formato
  Fecha o loop — gera → treina → gera melhor

Zero hardcode. Zero if específico de domínio. Entropia decide tudo.
"""
import re, math, os
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple, Optional
from mcr.template_entropico import extrair_template_entropico, gerar_do_template


def tokenizar_arquivo(caminho: str) -> List[str]:
    """Tokeniza qualquer arquivo em tokens universais (nível linha)."""
    try:
        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
            linhas = f.readlines()
    except Exception:
        return []
    tokens = []
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            tokens.append('VAZIO')
            continue
        # Tokeniza: palavras 3+, números, símbolos estruturais
        parts = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}|\d+|[=(){}\[\];,"\'.]', linha)
        if parts:
            tokens.extend(parts)
        else:
            tokens.append(linha[:20])
    return tokens


def extrair_template_dominio(arquivos: List[str], max_arquivos: int = 30) -> List[Tuple]:
    """Extrai template entrópico universal de um domínio (NPC, monstro, etc.)."""
    sequencias = []
    for arq in arquivos[:max_arquivos]:
        tokens = tokenizar_arquivo(arq)
        if tokens and len(tokens) > 5:
            sequencias.append(tokens)
    return extrair_template_entropico(sequencias)


def gerar_do_dominio(template: List[Tuple], coupling=None, temperatura: float = 0.9) -> str:
    """Gera novo conteúdo a partir do template entrópico.

    Componentes fixos: mantidos como estão.
    Componentes gap: preenchidos pelo coupling ou amostragem probabilística.
    """
    tokens = gerar_do_template(template, temperatura)
    if not tokens:
        return ''

    saida = []
    buffer = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == 'VAZIO':
            saida.append('')
            i += 1
            continue
        # Reconstrói linhas: símbolos de fim de statement fecham
        linha_parts = [t]
        i += 1
        while i < len(tokens):
            nt = tokens[i]
            linha_parts.append(nt)
            i += 1
        saida.append(' '.join(linha_parts))

    return '\n'.join(saida)


def explorar_workspace(raiz: str, profundidade: int = 3) -> Dict[str, List[str]]:
    """Explora workspace, agrupa arquivos por diretório. Zero hardcode."""
    dominios = {}
    for r, _, arquivos in os.walk(raiz):
        profundidade_atual = len(Path(r).relative_to(raiz).parts) if r != raiz else 0
        if profundidade_atual > profundidade:
            continue
        if len(arquivos) > 5:
            nome = os.path.basename(r)
            if nome not in dominios:
                dominios[nome] = []
            for a in arquivos:
                dominios[nome].append(os.path.join(r, a))
    return dominios


def auto_dataset(mcr_instance, workspace_raiz: str = None) -> Dict:
    """Loop fechado: explora → extrai templates → gera → treina.

    Sem dataset externo. MCR descobre seus próprios dados.
    """
    if workspace_raiz is None:
        workspace_raiz = str(Path(__file__).parent.parent)

    resultados = {}
    dominios = explorar_workspace(workspace_raiz)

    for nome_dir, arquivos in dominios.items():
        if len(arquivos) < 10:
            continue

        # Extrai template entrópico do domínio
        template = extrair_template_dominio(arquivos)
        if not template:
            continue

        # Gera exemplos sintéticos
        n_gerados = 0
        seeds_gerados = []
        for _ in range(min(5, len(arquivos) // 5)):
            novo = gerar_do_dominio(template)
            if novo and len(novo) > 20:
                seeds_gerados.append(novo)
                n_gerados += 1

        # Alimenta Markov com fingerprints dos exemplos gerados
        if seeds_gerados and mcr_instance:
            wrappers = getattr(mcr_instance, '_wrappers', {})
            for tool_name in wrappers:
                nome = tool_name.replace('_lua', '')
                tool_tokens = set(nome.replace('_', ' ').split())
                dir_tokens = set(nome_dir.replace('_', ' ').split())
                if tool_tokens & dir_tokens or nome_dir in tool_name:
                    for seed in seeds_gerados[:3]:
                        estado = mcr_instance._fingerprint_chave(seed)
                        mcr_instance.mk.aprender(estado, nome)
                        mcr_instance._coupling.alimentar(seed, nome)
                    break

        resultados[nome_dir] = {
            'arquivos': len(arquivos),
            'template_tamanho': len(template),
            'gerados': n_gerados,
        }

    return resultados


def extrair_componentes_template(template: List[Tuple]) -> Dict:
    """Extrai componentes estruturados do template entrópico.

    Retorna {'fixos': [...], 'gaps': [...]} com metadados de cada posição.
    """
    fixos = []
    gaps = []
    for i, (tipo, valor, h) in enumerate(template):
        if tipo == 'fixo':
            fixos.append({'pos': i, 'valor': valor, 'entropia': h})
        else:
            n_opcoes = len(valor) if isinstance(valor, Counter) else 1
            gaps.append({'pos': i, 'opcoes': n_opcoes, 'entropia': h,
                        'distribuicao': dict(valor.most_common(10)) if isinstance(valor, Counter) else {}})
    return {'fixos': fixos, 'gaps': gaps, 'total': len(template)}
