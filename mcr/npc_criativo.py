#!/usr/bin/env python3
"""
mcr.npc_criativo — NPC que conversa com contexto, cria conteudo novo, e tem personalidade.

Integra:
  - MCRSQLite (107K estados, 133K transicoes de 13.751 dialogos)
  - EmergirUnificado (3 Emergir + 3 Radar para criatividade)
  - HDC/SDM (contexto de conversa multi-turno)
  - Autobiography (memoria de longo prazo)
  - MCRSelf (identidade e personalidade)

Uso:
    npc = NPCCriativo('Ferronius', 'ferreiro')
    resposta = npc.responder('Ola!')
    resposta = npc.responder('Me conte uma historia sobre dragoes')
    resposta = npc.responder('Voce pode criar uma espada magica?')
"""
import sys
import os
import re
import time
import random
from typing import Dict, List, Optional, Tuple
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from mcr.mcr_sqlite import MCRSQLite
from mcr.emergir_unificado import EmergirUnificado
from mcr.paths import CACHE_DIR

# Personalidades base (expandidas com dados de treino)
PERSONALIDADES = {
    'ferreiro': {
        'saudacoes': ['Ola, viajante!', 'Bem-vindo a forja!', 'Precisa de algo forjado?'],
        'despedidas': ['Volte sempre!', 'Que suas armas nunca quebrem!', 'Ate mais!'],
        'assuntos': ['espada', 'armadura', 'ferro', 'bigorna', 'martelo', 'forja', 'metal'],
        'estilo': 'pratico',
        'temperatura_criativa': 0.3,  # quao criativo o NPC e
    },
    'bibliotecario': {
        'saudacoes': ['Bem-vindo a biblioteca.', 'Veio em busca de conhecimento?', 'Silencio, por favor.'],
        'despedidas': ['Bons estudos!', 'Nao esqueca de devolver os livros.', 'Ate logo.'],
        'assuntos': ['livro', 'magia', 'historia', 'runas', 'conhecimento', 'pergaminho', 'feitico'],
        'estilo': 'erudito',
        'temperatura_criativa': 0.7,
    },
    'mercador': {
        'saudacoes': ['Ola, quer negociar?', 'Tenho as melhores ofertas!', 'O que procura hoje?'],
        'despedidas': ['Volte para negociar!', 'Foi um prazer fazer negocios.', 'Nao aceito fiado!'],
        'assuntos': ['pocao', 'anel', 'escudo', 'item', 'ouro', 'tesouro', 'mercadoria'],
        'estilo': 'negociante',
        'temperatura_criativa': 0.5,
    },
    'guerreiro': {
        'saudacoes': ['Salve, aventureiro!', 'Pronto para a batalha?', 'Treinou hoje?'],
        'despedidas': ['Que a forca esteja com voce!', 'Lute bem!', 'Prepare-se para a proxima!'],
        'assuntos': ['espada', 'batalha', 'inimigo', 'dragao', 'armadura', 'escudo', 'honra'],
        'estilo': 'direto',
        'temperatura_criativa': 0.4,
    },
}

TEMPERATURA_PADRAO = 0.5
CONFIANCA_MINIMA = 0.005  # threshold baixo para geracao (dados esparsos)
MAX_TOKENS_GERACAO = 30


class NPCCriativo:
    """NPC que conversa, lembra e cria."""

    def __init__(self, nome: str = 'Ferronius', profissao: str = 'ferreiro',
                 db_path: str = None):
        self.nome = nome
        self.profissao = profissao
        self.traits = PERSONALIDADES.get(profissao, PERSONALIDADES['ferreiro'])
        self.temperatura = self.traits.get('temperatura_criativa', TEMPERATURA_PADRAO)

        # ─── Backends ───────────────────────────────
        db_conversa = db_path or str(CACHE_DIR / 'mcr_conversa.db')
        if os.path.exists(db_conversa):
            self.mcr_conversa = MCRSQLite(db_conversa, n_max=5, identidade='conversa')
        else:
            self.mcr_conversa = MCRSQLite(db_conversa, n_max=5, identidade='conversa')

        db_codigo = str(CACHE_DIR / 'mcr_codigo.db')
        if os.path.exists(db_codigo):
            self.mcr_codigo = MCRSQLite(db_codigo, n_max=10, identidade='codigo')
        else:
            self.mcr_codigo = MCRSQLite(db_codigo, n_max=10, identidade='codigo')

        self.emergir = EmergirUnificado()

        # ─── Estado da conversa ─────────────────────
        self.historico: List[Dict] = []
        self.contexto_atual: List[str] = []  # ultimos conceitos discutidos
        self.turno = 0
        self.acoes_repetidas = 0
        self._ultima_resposta = ''

    # ═══════════════════════════════════════════════════
    # RESPOSTA
    # ═══════════════════════════════════════════════════

    def responder(self, mensagem: str) -> str:
        """Responde a uma mensagem do jogador.

        Pipeline:
          1. Detectar intencao (acao vs conversa vs criacao)
          2. Buscar contexto relevante nos dialogos treinados
          3. Gerar resposta via Markov
          4. Se criacao solicitada, usar Emergir
          5. Registrar no historico
        """
        self.turno += 1
        msg_lower = mensagem.lower().strip()

        # ─── 1. Classificar intencao ────────────────
        intencao = self._classificar_intencao(msg_lower)

        # ─── 2. Atualizar contexto ──────────────────
        self._atualizar_contexto(mensagem)

        # ─── 3. Gerar resposta ──────────────────────
        if intencao == 'criacao':
            resposta = self._responder_criacao(mensagem)
        elif intencao == 'acao':
            resposta = self._responder_acao(mensagem)
        elif intencao == 'saudacao':
            resposta = self._responder_saudacao(mensagem)
        elif intencao == 'pergunta':
            resposta = self._responder_pergunta(mensagem)
        else:
            resposta = self._responder_conversa(mensagem)

        # ─── 4. Registrar ───────────────────────────
        self.historico.append({
            'turno': self.turno, 'jogador': mensagem,
            'resposta': resposta, 'intencao': intencao,
        })
        self._ultima_resposta = resposta
        self.emergir.alimentar_acao(f'responder_{intencao}')

        return resposta

    # ═══════════════════════════════════════════════════
    # CLASSIFICACAO DE INTENCAO
    # ═══════════════════════════════════════════════════

    def _classificar_intencao(self, msg: str) -> str:
        """Classifica a intencao da mensagem: saudacao, criacao, acao, pergunta, conversa."""
        # Saudacoes
        saudacoes = {'ola', 'oi', 'hey', 'hello', 'hi', 'bom dia', 'boa tarde', 'boa noite', 'salve'}
        if any(msg.startswith(s) or msg == s for s in saudacoes):
            return 'saudacao'

        # Criacao (solicita que o NPC crie algo)
        criativos = {'crie', 'criar', 'cria', 'gere', 'gerar', 'invente', 'criar',
                     'me conte uma historia', 'me conte sobre', 'crie um item',
                     'forje', 'crie uma', 'gere uma', 'invente uma', 'conte uma'}
        for c in criativos:
            if c in msg:
                return 'criacao'

        # Acao
        acoes = {'compre', 'venda', 'comprar', 'vender', 'quero', 'preciso',
                'me de', 'de-me', 'entregue', 'forje-me', 'cure-me', 'repare'}
        if any(a in msg for a in acoes):
            return 'acao'

        # Pergunta
        if msg.endswith('?') or any(msg.startswith(q) for q in
                                     ['quem', 'qual', 'quando', 'onde', 'como', 'por que',
                                      'what', 'who', 'where', 'when', 'why', 'how']):
            return 'pergunta'

        return 'conversa'

    # ═══════════════════════════════════════════════════
    # CONTEXTO
    # ═══════════════════════════════════════════════════

    def _atualizar_contexto(self, mensagem: str):
        """Extrai conceitos da mensagem e atualiza o contexto."""
        palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', mensagem.lower())
        conceitos = [p for p in palavras if p not in {'com', 'para', 'que', 'uma', 'isso',
                                                       'aquilo', 'como', 'mais', 'muito'}]
        self.contexto_atual = (self.contexto_atual + conceitos)[-10:]

    def _contexto_str(self) -> str:
        return ' '.join(self.contexto_atual[-5:]) if self.contexto_atual else ''

    # ═══════════════════════════════════════════════════
    # GERADORES DE RESPOSTA
    # ═══════════════════════════════════════════════════

    def _gerar_markov(self, sementes: List[str], max_tokens: int = None) -> str:
        """Gera texto via MCRSQLite a partir de sementes."""
        max_tokens = max_tokens or MAX_TOKENS_GERACAO
        melhor_cadeia = []

        for semente in sementes:
            cadeia = self.mcr_conversa.gerar(semente, passos=max_tokens)
            if len(cadeia) > len(melhor_cadeia):
                melhor_cadeia = cadeia

        if len(melhor_cadeia) <= 1:
            return None

        return ' '.join(melhor_cadeia)

    def _responder_saudacao(self, mensagem: str) -> str:
        """Responde a saudacoes."""
        saudacao = random.choice(self.traits['saudacoes'])
        # Tenta adicionar contexto
        ctx = self._contexto_str()
        if ctx and random.random() < 0.3:
            complemento = self._gerar_markov(ctx.split())
            if complemento:
                return f'{saudacao} {complemento}'
        return saudacao

    def _responder_conversa(self, mensagem: str) -> str:
        """Resposta conversacional usando MCRSQLite."""
        palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', mensagem.lower())

        # 1. Tentar gerar a partir das palavras da mensagem
        resposta = self._gerar_markov(palavras, max_tokens=25)
        if resposta and len(resposta.split()) >= 3:
            return self._formatar_resposta(resposta)

        # 2. Tentar com palavras do contexto
        ctx_palavras = self.contexto_atual[-5:]
        resposta = self._gerar_markov(ctx_palavras, max_tokens=20)
        if resposta and len(resposta.split()) >= 3:
            return self._formatar_resposta(resposta)

        # 3. Assunto da profissao
        assuntos = self.traits.get('assuntos', [])
        if assuntos:
            resposta = self._gerar_markov([random.choice(assuntos)], max_tokens=15)
            if resposta and len(resposta.split()) >= 2:
                return self._formatar_resposta(resposta)

        # 4. Fallback: resposta generica
        return self._fallback()

    def _responder_pergunta(self, mensagem: str) -> str:
        """Responde a perguntas."""
        palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', mensagem.lower())
        resposta = self._gerar_markov(palavras, max_tokens=30)
        if resposta and len(resposta.split()) >= 3:
            return self._formatar_resposta(resposta)
        return random.choice([
            "Hmm, essa e uma boa pergunta...",
            "Nao tenho certeza, mas posso tentar descobrir.",
            "Interessante... deixe-me pensar.",
            "Bem, pela minha experiencia...",
        ])

    def _responder_acao(self, mensagem: str) -> str:
        """Responde a pedidos de acao (comprar, vender, etc)."""
        palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', mensagem.lower())

        if any(a in palavras for a in ['comprar', 'compre', 'quero', 'preciso']):
            resposta = self._gerar_markov(['sell', 'buying', 'offer'], max_tokens=20)
            if resposta and len(resposta.split()) >= 3:
                return self._formatar_resposta(resposta)
            return "O que deseja comprar? Tenho otimos itens a venda."

        if any(a in palavras for a in ['vender', 'venda']):
            return "Nao estou comprando no momento, mas obrigado pela oferta."

        return random.choice([
            "Em que mais posso ajuda-lo?",
            "Precisa de mais alguma coisa?",
            "Estou a sua disposicao.",
        ])

    def _responder_criacao(self, mensagem: str) -> str:
        """Responde a pedidos de criacao usando EmergirUnificado."""
        palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', mensagem.lower())
        conceitos = palavras[:5]

        # Detectar o que o jogador quer criar
        tipo_criacao = None
        if any(c in mensagem.lower() for c in ['historia', 'conte', 'narrativa', 'lore']):
            tipo_criacao = 'historia'
        elif any(c in mensagem.lower() for c in ['item', 'arma', 'espada', 'armadura', 'pocao', 'anel']):
            tipo_criacao = 'item'
        elif any(c in mensagem.lower() for c in ['monstro', 'monster', 'criatura', 'dragao']):
            tipo_criacao = 'monstro'
        elif any(c in mensagem.lower() for c in ['npc', 'personagem', 'ferreiro', 'guarda']):
            tipo_criacao = 'npc'
        elif any(c in mensagem.lower() for c in ['quest', 'missao', 'aventura']):
            tipo_criacao = 'quest'

        # Usar Emergir para gerar ideia criativa
        if self.emergir.status()['emergir']:
            conceito_a = {'tipo': tipo_criacao or 'conceito', 'nome': conceitos[0] if conceitos else 'item', 'apis': []}
            ideia = self.emergir.gerar_ideia(conceito_a=conceito_a)
            ideia_texto = ideia.get('ideia', '')

            # Gerar descricao da criacao via MCRSQLite
            if tipo_criacao:
                descricao = self._gerar_markov(
                    conceitos + [tipo_criacao], max_tokens=40)
                if descricao and len(descricao.split()) >= 5:
                    return f"Ah, uma otima ideia! {ideia_texto} {descricao}"
                return f"Interessante! {ideia_texto} Vou trabalhar nisso."

        # Fallback criativo deterministico
        fallbacks = {
            'historia': [
                f"Ah, uma historia! Deixe-me lembrar... havia um {random.choice(conceitos) if conceitos else 'dragao'} que guardava um segredo milenar...",
                f"Conheco uma velha lenda sobre {random.choice(conceitos) if conceitos else 'um heroi'} que mudou o mundo...",
            ],
            'item': [
                f"Posso forjar algo especial! Um {random.choice(conceitos) if conceitos else 'item'} encantado com propriedades unicas...",
                f"Hum, um {random.choice(conceitos) if conceitos else 'objeto'} magico? Isso requer materiais raros!",
            ],
            'monstro': [
                f"Uma nova criatura? Que tal um {random.choice(conceitos) if conceitos else 'ser'} das profundezas que nunca foi visto?",
                f"Criaturas sao perigosas de se criar, mas... que tal algo que combine forca e astucia?",
            ],
        }
        if tipo_criacao and tipo_criacao in fallbacks:
            return random.choice(fallbacks[tipo_criacao])

        return f"Voce quer que eu crie algo? Conte-me mais sobre o que tem em mente!"

    # ═══════════════════════════════════════════════════
    # UTILITARIOS
    # ═══════════════════════════════════════════════════

    def _formatar_resposta(self, texto: str) -> str:
        """Formata e capitaliza a resposta gerada."""
        texto = texto.strip()
        if texto and texto[0].islower():
            texto = texto[0].upper() + texto[1:]
        # Remove repeticoes excessivas
        palavras = texto.split()
        if len(palavras) > 3:
            seen = set()
            filtradas = []
            for p in palavras:
                if p not in seen or len(seen) < 3:
                    filtradas.append(p)
                    if len(p) > 3:
                        seen.add(p)
            texto = ' '.join(filtradas)
        return texto if texto.endswith(('.', '!', '?')) else texto + '.'

    def _fallback(self) -> str:
        """Resposta generica quando nada funciona."""
        fallbacks = [
            "Entendo. Continue, estou ouvindo.",
            "Interessante... pode me contar mais?",
            "Hmm, isso me faz pensar...",
            "Nao tenho muito a dizer sobre isso agora.",
            "Precisa de ajuda com algo especifico?",
        ]
        return random.choice(fallbacks)

    def resumo(self) -> Dict:
        """Retorna estatisticas do NPC."""
        estados_conv = self.mcr_conversa.conn.execute(
            'SELECT COUNT(DISTINCT key) FROM trans').fetchone()[0]
        return {
            'nome': self.nome, 'profissao': self.profissao,
            'turnos': self.turno, 'estilo': self.traits['estilo'],
            'estados_treinados': estados_conv,
            'emergir_modulos': self.emergir.status(),
        }

    def close(self):
        self.mcr_conversa.conn.close()
        self.mcr_codigo.conn.close()


# ─── Teste ───────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 60)
    print('  NPCCriativo — Teste de Conversa')
    print('=' * 60)

    npc = NPCCriativo('Ferronius', 'ferreiro')
    print(npc.resumo())

    conversas = [
        'Ola!',
        'Voce pode me contar uma historia sobre dragoes?',
        'Que interessante! O que voce vende aqui?',
        'Crie uma espada magica para mim!',
        'Qual a melhor armadura que voce ja forjou?',
        'Ate mais!',
    ]

    for msg in conversas:
        resp = npc.responder(msg)
        print(f'\n  Jogador: {msg}')
        print(f'  {npc.nome}: {resp[:200]}')
        time.sleep(0.1)

    print('\n' + '=' * 60)
    print(f'  Turnos: {npc.turno}')
    print(f'  Historico: {len(npc.historico)} interacoes')
    print('=' * 60)
    npc.close()
