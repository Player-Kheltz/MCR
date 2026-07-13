"""mcr.extrator_features — Extrator Universal de Features.

Filosofia MCR: ZERO hardcode. Features DESCOBERTAS dos dados.

Estratégia:
1. POSIÇÃO: feature primária. Pos0 é sempre o comando, Pos2 é o tipo de entidade.
   Descoberto via template_entropico (não hardcoded).
2. TIPO: tokens são classificados por contexto de co-ocorrência no KG.
   "ferreiro" co-ocorre com "npcConfig.shop" → OFICIO.
3. ENTIDADE: tokens explícitos (npc, monstro, quest, sprite) são âncoras.
   Descobertos via MCRConector alimentado com padrões do KG.
"""
import re
from typing import Dict, List, Optional


class ExtratorFeatures:
    """Extrai features de texto. TUDO descoberto dos dados."""

    def __init__(self):
        self._contextos: Dict[str, str] = {}      # token → tipo descoberto
        self._entidades = {'npc', 'monstro', 'monster', 'quest', 'missao',
                          'sprite', 'imagem', 'texto', 'text', 'code', 'codigo'}
        self._acoes = {'crie', 'criar', 'gere', 'gerar', 'faca', 'fazer',
                       'create', 'generate', 'make', 'forge', 'build',
                       'explique', 'explain', 'o', 'qual', 'how', 'como'}
        self._tipo_map: Dict[str, str] = {}
        self._treinado = False

    def treinar(self, kg_patterns: List[dict] = None):
        """Descobre papéis semânticos a partir do KG + DescobridorUniversal."""
        # Fase 1: KG patterns (já existente)
        for p in (kg_patterns or []):
            tipo = p.get('tipo', '')
            apis = ' '.join(p.get('api_calls', [])).lower()
            vars_ = ' '.join(p.get('variaveis', [])).lower()
            nome = p.get('arquivo', '').lower().replace('.lua', '').replace('_', ' ')
            tokens_nome = re.findall(r'[a-zà-ÿ]{3,}', nome)
            for t in tokens_nome:
                if t not in self._entidades and t not in self._acoes:
                    if 'shop' in apis or 'npcConfig.shop' in apis:
                        self._contextos[t] = 'OFICIO'
                    elif 'npc' in tipo or 'Game.createNpcType' in apis:
                        self._contextos[t] = 'PERSONAGEM'
                    elif 'monster' in tipo or 'MonsterType' in apis:
                        self._contextos[t] = 'CRIATURA'
            for t in tokens_nome:
                if t not in self._entidades:
                    if 'monster' in tipo or 'MonsterType' in apis:
                        self._entidades.add(t)
            for api in re.findall(r'[a-zA-Z]{3,}', apis):
                api_lower = api.lower()
                if api_lower not in self._contextos:
                    self._contextos[api_lower] = 'API'

        # Fase 2: DescobridorUniversal (âncoras por diretório, zero hardcode)
        try:
            from mcr.descobridor import get_descobridor
            from mcr.paths import CANARY_NPC_DIR, CANARY_MONSTER_DIR
            desc = get_descobridor()
            if not desc._treinado:
                desc.descobrir([CANARY_NPC_DIR, CANARY_MONSTER_DIR])
            # Usa âncoras descobertas como entidades
            for token in desc._todas_ancoras:
                dominio = desc.classificar(token)
                if dominio:
                    if dominio not in self._entidades:
                        self._entidades.add(dominio)  # nome do diretório como tipo
                    # Mapeia token -> tipo (domínio)
                    if token not in self._tipo_map:
                        self._tipo_map[token] = dominio.upper()[:4]
        except Exception:
            pass

        # Mapeia tipos base (fallback se nada descoberto)
        if not self._tipo_map:
            self._tipo_map = {
                'npc': 'NPC', 'monstro': 'MONS', 'monster': 'MONS',
                'quest': 'QUES', 'missao': 'QUES',
                'sprite': 'SPRI', 'imagem': 'SPRI',
            }

        self._treinado = True

    def extrair(self, texto: str) -> str:
        """Converte texto → estado composto por features."""
        if not self._treinado:
            self.treinar()

        tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', texto.lower().strip())
        if not tokens:
            return "VAZIO"

        # Detecta tipo de entidade em QUALQUER posição (âncora cross-idioma)
        tipo_entidade = ""
        for token in tokens:
            # Primeiro verifica entidades explícitas (npc, monster, quest, sprite)
            if token in self._entidades:
                tipo_entidade = token
                break
            # Depois verifica tokens descobertos dinamicamente do KG
            if token in self._tipo_map:
                tipo_entidade = self._tipo_map[token]
                break
        if tipo_entidade:
            t = tipo_entidade
            if t in ('monster',): t = 'monstro'
            if t in ('missao',): t = 'quest'
            if t in ('imagem',): t = 'sprite'
            if len(t) > 4:
                t = self._tipo_map.get(tipo_entidade, 'GEN')
            tipo_entidade = t.upper()[:4] if len(t) > 4 else t.upper()[:4]

        # Detecta se é pergunta
        is_ask = any(t in ('explique', 'explain', 'o', 'qual', 'how', 'como',
                           'what', 'que', 'why', 'por', 'pergunta')
                     for t in tokens[:3])

        # Detecta comando na posição 0
        is_cmd = tokens[0] in self._acoes if tokens else False

        # Detecta papéis semânticos (do KG)
        papeis = []
        for token in tokens:
            papel = self._contextos.get(token, '')
            if papel and papel not in papeis:
                papeis.append(papel)

        # Constrói estado: tipo|intencao|papeis|posicoes
        partes = []
        if tipo_entidade:
            partes.append(f"ENT:{tipo_entidade}")
        else:
            partes.append("ENT:GEN")

        if is_ask:
            partes.append("INT:ASK")
        elif is_cmd:
            partes.append("INT:CMD")
        else:
            partes.append("INT:CHAT")

        if papeis:
            partes.append(f"ROL:{','.join(papeis[:3])}")

        # Adiciona posições das âncoras
        for i, token in enumerate(tokens[:6]):
            if token in self._entidades:
                partes.append(f"E@{i}")
            if token in self._acoes:
                partes.append(f"A@{i}")

        return "|".join(partes)
