"""gerador_mcr.py — Geração universal por template entrópico + coupling.

Princípios MCR:
  TUDO é P(b|a) — cada linha é uma transição no template
  Entropia descobre estrutura — linhas com baixa entropia = fixas, alta = gaps
  Mesmo motor, N domínios — mesmo código gera Lua, JSON, qualquer formato
  Zero hardcode — template extraído dos dados, valores do coupling

Arquitetura:
  1. Extrai template entrópico das linhas dos arquivos-fonte
  2. Linhas com entropia < limiar: estrutura fixa (sintaxe Lua)
  3. Linhas com entropia >= limiar: gap criativo (valor, nome, loot)
  4. Gaps preenchidos pelo coupling cross-domain
  5. Montagem segue ordem do fingerprint
"""
import re, math, random
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional


def extrair_linhas_arquivo(caminho: str) -> List[str]:
    """Lê arquivo e retorna linhas não-vazias."""
    try:
        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
            return [l.rstrip() for l in f.readlines() if l.strip()]
    except Exception:
        return []


def fingerprint_linha(linha: str) -> str:
    """Fingerprint MCR de uma linha: substitui valores por tipos.

    Números → N, strings → S, resto = token estrutural.
    Zero hardcode: a classificação emerge dos caracteres.
    """
    partes = []
    i = 0
    while i < len(linha):
        c = linha[i]
        if c.isdigit():
            partes.append('N')
            while i < len(linha) and linha[i].isdigit():
                i += 1
        elif c in '"\'':
            partes.append('S')
            i += 1
            while i < len(linha) and linha[i] not in '"\'':
                i += 1
            if i < len(linha):
                i += 1
        elif c.isalpha() or c == '_':
            token = []
            while i < len(linha) and (linha[i].isalnum() or linha[i] == '_'):
                token.append(linha[i])
                i += 1
            partes.append(''.join(token))
        else:
            partes.append(c)
            i += 1
    return '|'.join(partes)


def extrair_template_linhas(arquivos: List[str], max_arq: int = 40) -> List[Tuple]:
    """Extrai template entrópico de LINHAS de arquivos.

    Retorna lista de (tipo, valor_exemplo, entropia, distribuicao)
    onde tipo='fixo' (estrutura) ou tipo='gap' (criativo).
    """
    if not arquivos:
        return []

    # Lê todos os arquivos, alinha por posição de linha
    todas_linhas = []
    for arq in arquivos[:max_arq]:
        linhas = extrair_linhas_arquivo(arq)
        if linhas:
            todas_linhas.append(linhas)

    if not todas_linhas:
        return []

    # Alinha por fingerprint da linha (não por posição absoluta)
    # Linhas com mesmo fingerprint em todos os arquivos = provável estrutura
    max_pos = max(len(ls) for ls in todas_linhas)

    # Conta fingerprints por posição
    fps_por_pos = defaultdict(list)
    vals_por_pos = defaultdict(list)

    for linhas in todas_linhas:
        for i, linha in enumerate(linhas[:max_pos]):
            fp = fingerprint_linha(linha)
            fps_por_pos[i].append(fp)
            # Extrai apenas o VALOR (número, string) da linha para distribuição
            match = re.search(r'=\s*(.+)$', linha)
            val = match.group(1).strip() if match else linha
            vals_por_pos[i].append(val)

    # Monta template
    template = []
    for pos in sorted(fps_por_pos.keys()):
        fps = fps_por_pos[pos]
        vals = vals_por_pos[pos]
        fp_comum = Counter(fps).most_common(1)[0][0]

        # Entropia dos fingerprints: baixa = mesmo fp em todos = estrutura
        fp_counter = Counter(fps)
        n = len(fps)
        h = 0.0
        for c in fp_counter.values():
            p = c / n
            if p > 0:
                h -= p * math.log2(p)
        max_h = math.log2(max(len(fp_counter), 2))
        h_norm = h / max_h if max_h > 0 else 0.0

        if h_norm < 0.3:
            # Baixa entropia = estrutura fixa
            idx = fps.index(fp_comum) if fp_comum in fps else 0
            linha_ex = todas_linhas[idx][pos] if idx < len(todas_linhas) and pos < len(todas_linhas[idx]) else ''
            template.append(('fixo', linha_ex, h_norm, {}))
        else:
            # Alta entropia = gap criativo
            # Guarda uma linha exemplo (de qualquer arquivo) para reconstrução
            linha_ex = todas_linhas[0][pos] if pos < len(todas_linhas[0]) else fp_comum
            template.append(('gap', linha_ex, h_norm, Counter(vals)))

    return template


def gerar_do_template_linhas(template: List[Tuple], coupling=None, esfera=None,
                             nome: str = '', contexto: str = '') -> str:
    """Gera conteúdo a partir do template de linhas.

    Linhas fixas: mantidas como estão.
    Linhas gap: valor preenchido por:
      1. Esfera cross-domain (correlação fingerprint↔valor)
      2. Distribuição de valores observados
    """
    saida = []
    for tipo, valor_ex, h, dist in template:
        if tipo == 'fixo':
            saida.append(valor_ex)
        else:
            preenchido = None

            # 1. Tenta esfera cross-domain: dado o fingerprint do gap,
            #    busca valores correlacionados neste domínio
            if esfera and dist and contexto:
                fp = fingerprint_linha(valor_ex)
                preenchido = esfera.predizer_cross(contexto, dominio=fp)

            # 2. Amostra da distribuição
            if preenchido is None and dist:
                items = list(dist.keys())
                pesos = [dist[k] for k in items]
                total = sum(pesos) or 1
                r = random.random() * total
                acc = 0
                for item, peso in zip(items, pesos):
                    acc += peso
                    if r <= acc:
                        preenchido = item
                        break
                if preenchido is None:
                    preenchido = items[0] if items else valor_ex

            if preenchido is None:
                preenchido = str(valor_ex)

            if '=' in str(valor_ex):
                prefixo = str(valor_ex).split('=')[0].strip()
                saida.append(f"{prefixo} = {preenchido}")
            else:
                saida.append(str(preenchido))
    return '\n'.join(saida)


def descobrir_template_do_dominio(diretorio: str, max_arq: int = 40) -> Optional[List[Tuple]]:
    """Descobre template entrópico de um diretório de arquivos."""
    arquivos = [str(f) for f in Path(diretorio).iterdir()
                if f.is_file() and f.suffix in ('', '.lua', '.txt')][:max_arq]
    if len(arquivos) < 3:
        return None
    return extrair_template_linhas(arquivos, max_arq)
