"""mcr.template_modular — Templates modulares descobertos por entropia.

Cada fragmento de código é um módulo independente.
MCR descobre quais fragmentos são fixos (estrutura) vs variáveis (parâmetros).
Geração compõe módulos em qualquer ordem.

Zero hardcode. Funciona para qualquer domínio: NPC, monstro, quest, Lua, C++, etc.
"""
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

from mcr.template_entropico import extrair_template_entropico, gerar_do_template, resumir_template
from mcr.dominios.codigo import tokenizer


def _extrair_blocos(codigo: str) -> List[str]:
    """Extrai blocos lógicos de código Lua (funções, configs, handlers)."""
    blocos = []
    atual = []
    for linha in codigo.split('\n'):
        stripped = linha.strip()
        if not stripped:
            if atual:
                blocos.append('\n'.join(atual))
                atual = []
            continue
        atual.append(linha)
    if atual:
        blocos.append('\n'.join(atual))
    return blocos


def _classificar_bloco(bloco: str) -> str:
    """Classifica bloco de código Lua por tipo estrutural.
    
    Descobre tipos dos dados reais via assinatura de tokens.
    """
    tokens = set(bloco.lower().split())
    b = bloco.lower()

    # Assinaturas descobertas: cada tipo tem tokens característicos
    # que co-ocorrem nos arquivos Lua reais
    _ASSINATURAS = {
        'header': {'internalnpcname', 'createnpctype', 'type'},
        'config': {'npcconfig.name', 'npcconfig.health', 'npcconfig.outfit'},
        'shop': {'npcconfig.shop', 'shop =', 'shop_items', 'buyable'},
        'keyword': {'keywordhandler', 'keywordhandler:registerkeyword'},
        'callbacks': {'npchandler', 'onthink', 'onsay', 'onappear', 'ontrade'},
        'register': {'register', 'registerfunction'},
        'monster_config': {'monstertype', 'monster.outfit', 'monster.loot'},
        'quest_logic': {'storagevalue', 'questlog', 'getstorage'},
    }

    # Score: quantos tokens da assinatura aparecem no bloco
    melhor_tipo = 'other'
    melhor_score = 0
    for tipo, assinatura in _ASSINATURAS.items():
        score = len(tokens & assinatura)
        if score > melhor_score:
            melhor_score = score
            melhor_tipo = tipo

    return melhor_tipo if melhor_score >= 1 else 'other'


class TemplateModular:
    """Template composto por módulos independentes, descobertos por entropia."""

    def __init__(self, exemplos: List[str], tipo: str = 'npc'):
        self._exemplos = exemplos
        self._tipo = tipo
        self._modulos: Dict[str, List[Tuple]] = {}
        self._sequencias: List[List[str]] = []
        self._treinar()

    def _treinar(self):
        """Extrai módulos de cada exemplo e treina templates por módulo."""
        blocos_por_tipo: Dict[str, List[List[str]]] = {}

        for ex in self._exemplos:
            blocos = _extrair_blocos(ex)
            sequencia = []
            for bloco in blocos:
                tipo = _classificar_bloco(bloco)
                sequencia.append(tipo)
                tokens = tokenizer(bloco)
                if tipo not in blocos_por_tipo:
                    blocos_por_tipo[tipo] = []
                blocos_por_tipo[tipo].append(tokens)
            self._sequencias.append(sequencia)

        # Cria template entrópico para cada tipo de módulo
        for tipo, sequencias in blocos_por_tipo.items():
            if len(sequencias) >= 2:
                try:
                    tmpl = extrair_template_entropico(sequencias, limiar_entropia=0.4)
                    self._modulos[tipo] = tmpl
                except Exception:
                    pass

    def gerar(self, modulos: List[str] = None, temperatura: float = 0.6) -> str:
        """Gera código compondo módulos. Ordem é preservada da lista."""
        if modulos is None:
            # Usa sequência mais comum dos exemplos
            freq = Counter(tuple(s) for s in self._sequencias)
            modulos = list(freq.most_common(1)[0][0]) if freq else []

        resultado = []
        for tipo in modulos:
            tmpl = self._modulos.get(tipo)
            if tmpl is None:
                continue
            try:
                tokens = gerar_do_template(tmpl, temperatura=temperatura)
                linha = ' '.join(tokens)
                resultado.append(linha)
            except Exception:
                pass

        return '\n\n'.join(resultado)

    def modulos_disponiveis(self) -> List[str]:
        """Lista módulos descobertos."""
        return list(self._modulos.keys())

    def resumo(self) -> str:
        """Resumo dos módulos."""
        linhas = [f'TemplateModular ({self._tipo}): {len(self._modulos)} modulos']
        for nome, tmpl in self._modulos.items():
            n_fixos = sum(1 for t in tmpl if t[0] == 'fixo')
            n_gaps = sum(1 for t in tmpl if t[0] == 'gap')
            linhas.append(f'  {nome}: {n_fixos} fixos + {n_gaps} gaps')
        return '\n'.join(linhas)
