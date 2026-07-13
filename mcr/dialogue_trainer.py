"""mcr.dialogue_trainer — Alimenta o MCR com dialogos reais de NPCs do Canary.
Transforma falas de NPCs em conhecimento Markoviano para o NPC Server."""
import json
import re
import random
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

from mcr.encoding import read_file, write_file
from mcr.paths import KG_DIR, CANARY_NPC_DIR
from mcr.dialogue_miner import minerar_lote


class DialogueTrainer:
    """Treina o MCR com dialogos de NPCs para geracao de falas naturais."""

    FALLBACKS = [
        "Nao tenho nada a dizer sobre isso agora.",
        "Hmm, interessante.",
        "Nao sei o que dizer sobre isso.",
        "Precisa de mais alguma coisa?",
        "Continue, estou ouvindo.",
        "Entendo.",
        "Sim, claro.",
        "Ora, ora...",
        "Nao faz ideia do que isso significa.",
        "Deixe-me pensar... nao, nao sei.",
    ]

    def __init__(self, mcr_system=None):
        self.mcr = mcr_system  # MCRSystem ou None
        self.vocabulario_por_npc = defaultdict(dict)  # npc_name -> {keyword: [responses]}
        self.npc_personas = {}  # npc_name -> vocabulario Markov
        self.total_dialogos = 0
        self.total_npcs = 0

    # ─── Carregar dialogos do JSON ────────────────────────────

    def carregar_dialogos_json(self, caminho: Path = None) -> List[Dict]:
        """Carrega dialogos do JSON gerado pelo dialogue_miner."""
        if caminho is None:
            caminho = KG_DIR / 'dialogos_npc.json'
        if not caminho.exists():
            return []
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        return dados.get('npcs', [])

    def treinar_com_dialogos(self, npcs: List[Dict]) -> Dict:
        """Treina o MCR com os dialogos extraidos.
        
        Para cada NPC:
        1. Cria uma persona Markov com transicoes keyword -> response
        2. Alimenta o MCR principal com bigramas das falas
        3. Indexa keywords para busca rapida
        
        Returns:
            dict com estatisticas do treinamento
        """
        if not npcs:
            return {'erro': 'Nenhum dialogo para treinar'}

        palavras_unicas = set()
        self.total_npcs = 0
        self.total_dialogos = 0

        for npc in npcs:
            npc_name = npc.get('npc_name', 'Desconhecido')
            dialogos = npc.get('dialogos', [])
            if not dialogos:
                continue

            # Cria persona
            persona = {'keywords': {}, 'falas': []}
            self.total_npcs += 1

            for dial in dialogos:
                keyword = dial.get('keyword', '').lower()
                response = dial.get('response', '')
                if not response:
                    continue

                # Indexa por keyword
                if keyword:
                    if keyword not in persona['keywords']:
                        persona['keywords'][keyword] = []
                    persona['keywords'][keyword].append(response)

                persona['falas'].append(response)
                self.total_dialogos += 1

                # Alimenta vocabulário (sempre, mesmo sem MCR)
                palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', response.lower())
                palavras_unicas.update(palavras)

                # Alimenta o MCR com bigramas das palavras da fala
                if self.mcr and hasattr(self.mcr, 'mk_palavra'):
                    for i in range(len(palavras) - 1):
                        try:
                            # Alimenta 3x para reforco
                            for _ in range(3):
                                self.mcr.mk_palavra.aprender(palavras[i], palavras[i + 1])
                        except Exception:
                            pass

                    # Alimenta keyword -> primeira palavra da resposta
                    if keyword and palavras:
                        try:
                            for _ in range(5):  # reforco extra para keywords
                                self.mcr.mk_palavra.aprender(keyword, palavras[0])
                        except Exception:
                            pass

            self.npc_personas[npc_name] = persona
            self.vocabulario_por_npc[npc_name.lower()] = persona['keywords']

        stats = {
            'npcs_treinados': self.total_npcs,
            'dialogos_aprendidos': self.total_dialogos,
            'vocabulario_unico': len(palavras_unicas),
            'personas_criadas': len(self.npc_personas),
        }

        print('[DialogueTrainer] Treinamento concluido:')
        for k, v in stats.items():
            print('  %s: %s' % (k, v))
        return stats

    # ─── Geracao de resposta ──────────────────────────────────

    def gerar_resposta(self, npc_id: str, mensagem: str) -> str:
        """Gera uma resposta para um NPC especifico com base no treinamento.
        NUNCA retorna None — sempre retorna uma string, mesmo que generica."""
        npc_lower = npc_id.lower()

        # Busca keyword na mensagem
        palavras_msg = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', mensagem.lower())

        # Procura no vocabulario do NPC
        keywords_pool = self.vocabulario_por_npc.get(npc_lower, {})
        if not keywords_pool:
            # Tenta fuzzy matching pelo nome
            for nome, kw in self.vocabulario_por_npc.items():
                if npc_lower in nome or nome in npc_lower:
                    keywords_pool = kw
                    break

        if keywords_pool:
            # Match da mensagem contra keywords
            for palavra in palavras_msg:
                for keyword, responses in keywords_pool.items():
                    if not keyword:
                        continue
                    if palavra == keyword or keyword in ' '.join(palavras_msg):
                        if responses:
                            return random.choice(responses)

        # Fallback: tenta gerar via Markov
        if self.mcr and hasattr(self.mcr, 'mk_palavra'):
            cadeia = []
            for p in palavras_msg[:3]:
                pred, conf = self.mcr.mk_palavra.predizer(p)
                if pred and conf > 0.03:
                    atual = p
                    for _ in range(15):
                        prox, c = self.mcr.mk_palavra.predizer(atual)
                        if not prox or c < 0.02:
                            break
                        cadeia.append(prox)
                        atual = prox
                    break
            if cadeia:
                return ' '.join(cadeia[:10])

        # Fallback final: NUNCA retorna None
        return random.choice(self.FALLBACKS)

    def estatisticas(self) -> Dict:
        return {
            'npcs_treinados': self.total_npcs,
            'dialogos_aprendidos': self.total_dialogos,
            'personas': len(self.npc_personas),
        }
