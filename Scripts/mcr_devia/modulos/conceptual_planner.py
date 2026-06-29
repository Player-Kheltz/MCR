"""Conceptual Planner — Transforma conceitos gerais em planos de aplicacao.
Usa BlankFiller + EMERGIR + Conselho + PatternEngine para criar planos
conceituais profundos sem escrever codigo. Cada etapa do plano descreve
O QUE o codigo faria e COMO faria, usando metaforas e exemplos.

Diferenca do pipeline normal:
  - Nao gera codigo — gera SIGNIFICADO
  - Nao responde o que e — responde COMO aplicar
  - Usa metaforas que sao facilmente traduziveis para logica
"""
import os, re, json, time

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Template de esqueleto para planos conceituais
_ESQUELETO_PLANO = """---
PLANO CONCEITUAL: {conceito}
---

## 1. ESSENCIA
O que realmente importa neste conceito? Qual o padrao universal?

## 2. EM QUE MUNDO ISSO EXISTE
Onde este conceito ja aparece no projeto MCR? (KG, codigo, docs)
Cite lessons, arquivos, modulos — tudo que ja temos.

## 3. METAFORA CENTRAL
Uma unica frase que traduz mil linhas de codigo em uma imagem mental.

## 4. COMO APLICAR (passo a passo conceitual)
Para cada passo: explique O QUE o codigo faria, nao escreva o codigo.
Use analogias do mundo real.
- Passo 1: [descricao] — analogia: [como se fosse...]
- Passo 2: [descricao] — analogia: [como se fosse...]
- Passo N: ...

## 5. O QUE EMERGE
O que surge dessa aplicacao que nao existia antes?

## 6. EIXO NIRVANA-CAOS
Onde este plano se posiciona? O que o aproxima do Nirvana?
O que o afasta do Caos?
"""


class ConceptualPlanner:
    """Gera planos conceituais profundos usando ferramentas existentes."""
    
    def __init__(self, kg=None, ia=None, pe=None, conselho=None):
        self.kg = kg
        self.ia = ia
        self.pe = pe
        self.conselho = conselho
    
    def criar_plano(self, conceito):
        """Gera um plano conceitual completo a partir de um conceito.
        
        Args:
            conceito: str, o conceito a ser explorado (ex: "PatternEngine")
        
        Returns:
            dict: {plano, metafora, passos, eixo, lessons_usadas}
        """
        t0 = time.time()
        
        # 1. Busca no KG
        lessons = []
        if self.kg:
            lessons = self.kg.buscar_expandido(conceito, max_r=10)
        
        # 2. Cria esqueleto via BlankFiller
        plano_esqueleto = _ESQUELETO_PLANO.format(conceito=conceito)
        
        # 3. Preenche blanks em cadeia (cada blank alimenta o proximo)
        blanks = {
            'essencia': self._gerar_essencia(conceito, lessons),
            'metafora': self._gerar_metafora(conceito, lessons),
            'passos': self._gerar_passos(conceito, lessons),
            'emergencia': self._gerar_emergencia(conceito, lessons),
            'eixo': self._gerar_eixo(conceito, lessons),
        }
        
        # 4. Monta plano final
        plano = plano_esqueleto
        for chave, valor in blanks.items():
            placeholder = "{" + chave + "}"
            if placeholder in plano:
                plano = plano.replace(placeholder, str(valor))
        
        # 5. Extrai metafora central
        metafora = blanks.get('metafora', '')
        if isinstance(metafora, str) and len(metafora) > 100:
            metafora = metafora + '...'
        
        tempo = round(time.time() - t0, 1)
        
        return {
            'plano': plano,
            'metafora': metafora,
            'passos': len(blanks.get('passos', [])),
            'eixo': blanks.get('eixo', 0.5),
            'lessons_usadas': [l.get('id', '?') for l in lessons],
            'tempo': tempo,
        }
    
    def _gerar_essencia(self, conceito, lessons):
        """Gera a essencia do conceito: o que realmente importa."""
        contexto_kg = '\n'.join([f"- {l.get('erro','')}: {l.get('solucao','')}" 
                                for l in lessons]) if lessons else "(sem contexto)"
        
        if not self.ia:
            return f"Essencia de {conceito}: padrão identificado em {len(lessons)} lessons do KG."
        
        prompt = (
            f"[SISTEMA]\nSeja PROFUNDO. Qual a essencia de {conceito}?\n"
            f"Nao descreva o que ele faz — descreva o que ele REALMENTE E.\n"
            f"Use uma analogia. Seja original. Evite cliches.\n\n"
            f"[CONTEXTO DO KG]\n{contexto_kg}\n\n"
            f"[PERGUNTA]\nQual a essencia de {conceito}? Responda em 3-5 frases."
        )
        return self.ia.gerar(prompt, 0.4, 'texto') or f"Essencia de {conceito}"
    
    def _gerar_metafora(self, conceito, lessons):
        """Gera a metafora central: uma frase que traduz tudo."""
        contexto_kg = '\n'.join([f"- {l.get('erro','')}" for l in lessons]) if lessons else ""
        
        if not self.ia:
            return f"{conceito} e como um organismo vivo que se adapta ao ambiente."
        
        prompt = (
            f"[SISTEMA]\nCrie UMA metafora poderosa para {conceito}.\n"
            f"A metafora deve ser do MUNDO REAL (natureza, engenharia, musica, etc).\n"
            f"Deve ser facilmente traduzivel para logica de programacao.\n"
            f"Ex: 'Fingerprint e a digital de um conceito — duas coisas com a mesma digital sao a mesma coisa.'\n\n"
            f"[CONTEXTO]\n{contexto_kg}\n\n"
            f"[MEFORA] (uma frase, sem explicacao):"
        )
        return self.ia.gerar(prompt, 0.5, 'texto') or f"{conceito} e um padrao que emerge da complexidade."
    
    def _gerar_passos(self, conceito, lessons):
        """Gera os passos conceituais: O QUE fazer, nao COMO fazer codigo."""
        contextos = set(l.get('ctx', '') for l in lessons)
        ctx_str = ', '.join(contextos) if contextos else 'geral'
        
        if not self.ia:
            return ["Analise o padrao", "Identifique as variaveis", "Aplique a transformacao"]
        
        prompt = (
            f"[SISTEMA]\nCrie um plano conceitual para APLICAR {conceito}.\n"
            f"NAO escreva codigo. Descreva O QUE o codigo faria.\n"
            f"Cada passo deve ter: acao + analogia do mundo real.\n"
            f"Contextos envolvidos: {ctx_str}\n\n"
            f"Formato EXATO (3-5 passos):\n"
            f"PASSO 1: [acao] — analogia: [como se fosse...]\n"
            f"PASSO 2: [acao] — analogia: [como se fosse...]"
        )
        resp = self.ia.gerar(prompt, 0.4, 'texto') if self.ia else ""
        if resp and 'PASSO' in resp:
            return [linha.strip() for linha in resp.split('\n') if linha.strip().startswith('PASSO')]
        return [f"Passo 1: Integrar {conceito} com as ferramentas existentes"]
    
    def _gerar_emergencia(self, conceito, lessons):
        """O que emerge da aplicacao que nao existia antes."""
        if not self.ia:
            return f"Ao aplicar {conceito}, emerge um novo padrao de compreensao."
        
        prompt = (
            f"[SISTEMA]\nO que EMERGE de UNICO ao aplicar {conceito} no MCR?\n"
            f"Nao liste beneficios obvios. Pense no que SURGE de NOVO.\n"
            f"Qual capacidade que nao existia antes? Qual padrao que so aparece agora?\n\n"
            f"[PERGUNTA]\nO que emerge de {conceito}?"
        )
        return self.ia.gerar(prompt, 0.4, 'texto') or f"Emergencia de {conceito}: novos padroes de interacao."
    
    def _gerar_eixo(self, conceito, lessons):
        """Onde o plano se posiciona no eixo Nirvana-Caos."""
        if self.pe and lessons:
            try:
                textos = ' '.join([l.get('solucao', '') + l.get('erro', '') for l in lessons])
                tokens = self.pe.tokenizar(textos, 'texto')
                eixo = self.pe.eixo_nirvana_caos(tokens)
                return round(eixo, 3)
            except Exception:
                pass
        return 0.5
