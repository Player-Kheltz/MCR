"""TemplateExtractor — extrai esqueleto estrutural de arquivos de código similares.

Funcionamento:
1. Recebe um ou mais arquivos de referência (código similar existente)
2. Compara linhas para identificar o que é ESTRUTURA FIXA vs VALOR VARIÁVEL
3. Retorna um template com placeholders para os valores variáveis

Útil para: habilidades SPA, NPCs, quests, comandos — qualquer código com estrutura repetitiva.
"""
import re
from typing import List, Dict, Optional, Tuple


def extrair_template(conteudo: str, nome_arquivo: str = "") -> Tuple[str, List[str]]:
    """Extrai template de um conteúdo de arquivo.
    
    Retorna (template_com_placeholders, lista_de_gaps).
    Gaps são identificados como padrões que variam entre arquivos similares.
    """
    gaps = []
    linhas = conteudo.split('\n')
    template_linhas = []
    
    for i, linha in enumerate(linhas):
        # Identifica linhas que são valores provavelmente variáveis
        # Padrões comuns em habilidades SPA, NPCs, quests
        
        # Strings entre aspas (nomes, descrições, textos)
        if _linha_eh_valor_textual(linha):
            gap_nome = _inferir_gap(linha, i, linhas)
            template_linhas.append(_substituir_valor_por_placeholder(linha, gap_nome))
            gaps.append(gap_nome)
        # Números que parecem configuráveis (cooldown, dano, IDs)
        elif _linha_eh_valor_numerico(linha, i, linhas):
            gap_nome = _inferir_gap(linha, i, linhas)
            template_linhas.append(_substituir_numero_por_placeholder(linha, gap_nome))
            gaps.append(gap_nome)
        # Linhas de estrutura (chaves, colchetes, return, etc.) — mantém intactas
        else:
            template_linhas.append(linha)
    
    return '\n'.join(template_linhas), gaps


def extrair_template_multi(arquivos: Dict[str, str]) -> Tuple[str, List[str]]:
    """Extrai template comparando múltiplos arquivos similares.
    
    O que é IGUAL entre todos = estrutura fixa.
    O que DIFERE = gap.
    """
    if not arquivos:
        return "", []
    
    conteudos = list(arquivos.values())
    linhas_por_arquivo = [c.split('\n') for c in conteudos]
    
    if not linhas_por_arquivo:
        return "", []
    
    template_linhas = []
    gaps = []
    
    max_linhas = max(len(l) for l in linhas_por_arquivo)
    
    for i in range(max_linhas):
        linhas_na_posicao = []
        for l in linhas_por_arquivo:
            if i < len(l):
                linhas_na_posicao.append(l[i])
        
        if not linhas_na_posicao:
            continue
        
        if len(set(linhas_na_posicao)) == 1:
            # Todas iguais — estrutura fixa
            template_linhas.append(linhas_na_posicao[0])
        else:
            # Diferem — gap
            primeira = linhas_na_posicao[0]
            gap_nome = _inferir_gap(primeira, i, linhas_na_posicao)
            template_linhas.append(f"<<<{gap_nome}>>>")
            gaps.append(gap_nome)
    
    return '\n'.join(template_linhas), gaps


def _linha_eh_valor_textual(linha: str) -> bool:
    """Identifica linhas que contêm valores textuais (strings, nomes, descrições)."""
    linha_strip = linha.strip()
    # Padrões como: nome = "Algo", descricao = "texto"
    if re.match(r'^[\w_]+\s*=\s*"[^"]*"', linha_strip):
        return True
    # Padrões como: "texto", (string solta em array/tabela)
    if re.match(r'^\s*"[^"]*"\s*,?\s*$', linha_strip):
        return True
    return False


def _linha_eh_valor_numerico(linha: str, idx: int, linhas: List[str]) -> bool:
    """Identifica linhas com valores numéricos configuráveis."""
    linha_strip = linha.strip()
    # Padrões como: cooldown = 5, dano = 1.5, nivelMin = 5
    if re.match(r'^[\w_]+\s*=\s*\d+\.?\d*\s*,?\s*$', linha_strip):
        # Exclui contadores de índice simples como "id = 1"
        nome_var = linha_strip.split('=')[0].strip()
        if nome_var.lower() in ('id', 'index', 'i', 'j', 'k', 'x', 'y', 'z'):
            return False
        return True
    return False


def _inferir_gap(linha: str, idx: int, contexto: List[str]) -> str:
    """Tenta inferir um nome descritivo para o gap baseado no contexto."""
    linha_strip = linha.strip()
    
    # Extrai nome da variável se for assignment
    match = re.match(r'^([\w_]+)\s*=', linha_strip)
    if match:
        nome_var = match.group(1)
        # Mapeia nomes de variáveis para gaps semânticos
        mapeamento = {
            'nome': 'nome_habilidade',
            'name': 'nome_npc',
            'descricao': 'descricao',
            'descricaoEfeito': 'descricao_efeito',
            'cooldown': 'cooldown_segundos',
            'nivelMin': 'nivel_minimo',
            'condicaoFocoMin': 'foco_minimo',
            'cor': 'cor_dominio',
            'plural': 'plural_item',
            'article': 'artigo_item',
            'outfit': 'outfit_npc',
            'lookType': 'looktype',
            'health': 'vida_npc',
            'maxHealth': 'vida_max_npc',
            'walkInterval': 'intervalo_andar',
            'walkSpeed': 'velocidade_andar',
        }
        return mapeamento.get(nome_var, f"{nome_var}")
    
    # Se é uma string literal, tenta inferir pelo contexto anterior
    if re.match(r'^\s*"[^"]*"', linha_strip):
        if idx > 0:
            linha_anterior = contexto[idx - 1].strip()
            match_ant = re.match(r'^([\w_]+)\s*=', linha_anterior)
            if match_ant:
                return f"valor_{match_ant.group(1)}"
        return "texto"
    
    return f"gap_{idx}"


def _substituir_valor_por_placeholder(linha: str, gap_nome: str) -> str:
    """Substitui o valor textual por placeholder."""
    # Substitui "texto" por <<<gap_nome>>>
    return re.sub(r'"([^"]*)"', f'<<<{gap_nome}>>>', linha, count=1)


def _substituir_numero_por_placeholder(linha: str, gap_nome: str) -> str:
    """Substitui o valor numérico por placeholder."""
    return re.sub(r'=\s*\d+\.?\d*', f'= <<<{gap_nome}>>>', linha, count=1)
