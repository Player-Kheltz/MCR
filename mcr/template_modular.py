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
    """Classifica bloco de código Lua por tipo estrutural."""
    b = bloco.lower()
    if 'internalnpcname' in b or 'createnpctype' in b:
        return 'header'
    if 'npcConfig.name' in b or 'npcConfig.health' in b or 'npcConfig.outfit' in b:
        return 'config'
    if 'npcConfig.shop' in b or 'shop =' in b or 'shop_items' in b:
        return 'shop'
    if 'keywordhandler' in b:
        return 'keyword'
    if 'npcHandler' in b or 'onThink' in b or 'onSay' in b or 'onAppear' in b:
        return 'callbacks'
    if 'register' in b:
        return 'register'
    if 'MonsterType' in b or 'monster.outfit' in b or 'monster.loot' in b:
        return 'monster_config'
    if 'storageValue' in b or 'QuestLog' in b or 'getStorage' in b:
        return 'quest_logic'
    return 'other'


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
