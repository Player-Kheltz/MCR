"""mcr.mcr_conversa — Dialogo com injecao rigida de contexto + roteamento de intencao.
Se for acao -> pipeline. Se for dialogo -> LLM com system message blindada."""
import os
import sys
import json
import time
import re
import urllib.request
from typing import Optional, Dict

from mcr.mcr_self import MCRSelf
from mcr.mcr_autobiography import Autobiography

from mcr.config_llm import MODELO_CHAT, MODELO_CODIGO, OLLAMA_URL

_OLLAMA = OLLAMA_URL + "/generate"
MODELO = MODELO_CHAT

# Palavras que indicam acao
_VERBOS_ACAO = {'cria', 'crie', 'criar', 'faz', 'faca', 'fazer', 'gere', 'gerar',
                'escreve', 'escrever', 'salva', 'salvar', 'modifica', 'modificar',
                'adiciona', 'adicionar', 'implementa', 'implementar', 'corrige',
                'corrigir', 'arruma', 'arrumar', 'analisa', 'analisar'}
_SUBSTANTIVOS_ACAO = {'npc', 'monstro', 'monster', 'item', 'spell', 'magia',
                      'habilidade', 'quest', 'missao', 'sistema', 'arquivo',
                      'script', 'lua', 'codigo', 'lore', 'classe', 'funcao'}


class Conversa:
    """Orquestrador de dialogo com roteamento de intencao."""

    def __init__(self, mcr_system=None, llm_func=None):
        self.self = MCRSelf()
        self.auto = Autobiography()
        self._mcr = mcr_system
        self._llm_func = llm_func

    def vincular_inner_voice(self, voice):
        self.inner_voice = voice

    def _classificar_intencao(self, mensagem: str) -> str:
        """Classifica em 'action' ou 'dialogue' usando heuristica."""
        msg_lower = mensagem.lower().strip()
        palavras = set(re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', msg_lower))
        tem_acao = bool(palavras & _VERBOS_ACAO)
        tem_substantivo = bool(palavras & _SUBSTANTIVOS_ACAO)
        if tem_acao and tem_substantivo:
            return 'action'
        return 'dialogue'

    def _executar_acao(self, message: str) -> str:
        """Chama o pipeline do DevIA para executar a acao."""
        try:
            from mcr_devia import processar
            resultado = processar(message)
            if resultado and resultado.get('resposta'):
                return '[Acao] ' + resultado['resposta'][:300]
        except Exception as e:
            pass
        return '[Acao] Comando recebido. Processando...'

    def conversar(self, user_id: str, message: str) -> str:
        if not message or not message.strip():
            return "..."

        t0 = time.time()
        intencao = self._classificar_intencao(message)

        # Se for acao, executa pipeline sem chamar LLM
        if intencao == 'action':
            resposta = self._executar_acao(message)
            self.auto.record_memory('acao', '%s pediu: %s' % (user_id, message[:80]),
                                    [self.self.nome, user_id])
            return '%s (%.0fms)' % (resposta, (time.time() - t0) * 1000)

        # --- DIALOGO: Monta o prompt com injecao de contexto ---
        lembrancas = self.auto.recall(user_id, limit=3)
        memorias = '\n'.join('- ' + l for l in lembrancas) if lembrancas else 'Nenhuma conversa anterior.'

        opinioes = []
        for tema, opiniao in self.self.opinioes.items():
            if tema.lower() in message.lower():
                opinioes.append('%s: %s' % (tema, opiniao[:200]))
        opinioes_str = '\n'.join(opinioes) if opinioes else 'Nenhuma opiniao formada sobre este tema.'

        # Prompt do usuario (so memorias + mensagem, sem regras)
        user_prompt = (
            "MEMORIAS CONFIRMADAS:\n%s\n\n" % memorias +
            "OPINIOES DO MCR SOBRE O TEMA:\n%s\n\n" % opinioes_str +
            "REGRAS: Nao seja um assistente. Nao ofereca ajuda. Nao use frases de cortesia.\n"
            "MENSAGEM DO USUARIO:\n%s" % message
        )

        resposta = self._chamar_llm(user_prompt)
        if not resposta:
            resposta = 'Nao consegui processar sua mensagem agora.'

        self.auto.record_memory('dialogue', '%s disse: %s | %s respondeu: %s' % (
            user_id, message[:80], self.self.nome, resposta[:80]),
            [self.self.nome, user_id])

        return '%s (%.0fms)' % (resposta, (time.time() - t0) * 1000)

    def _chamar_llm(self, user_prompt: str) -> Optional[str]:
        """Chama o LLM (mistral:7b) com system message."""
        if self._llm_func:
            try:
                return self._llm_func(user_prompt, modelo=MODELO_CHAT)[:600]
            except Exception:
                pass

        try:
            system_msg = (
                "IDENTIDADE: Voce e o MCR-DevIA, versao 4.0, criado por Kheltz.\n"
                "PROIBICOES: nunca diga 'como posso ajudar', 'sinta-se a vontade', "
                "'estou aqui para ajudar'. Nao seja um assistente. Seja direto e opinativo."
            )
            payload = json.dumps({
                "model": MODELO_CHAT,
                "system": system_msg,
                "prompt": user_prompt,
                "stream": False,
                "options": {"temperature": 0.7, "max_tokens": 250}
            }).encode()
            req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                resp = json.loads(r.read())
            texto = resp.get('response', '').strip()
            return texto[:600] if texto else None
        except Exception:
            pass
        return None
