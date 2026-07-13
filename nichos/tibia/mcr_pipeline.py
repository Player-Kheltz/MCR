#!/usr/bin/env python3
"""
MCR Pipeline — geracao de texto coerente ILIMITADA, sem LLM.

Conecta TODAS as ferramentas do MCR em pipeline sequencial:
  Entrada → Parse → Contexto → Fragmentos → Geracao → Aprendizado

Cada estagio enriquece o contexto do seguinte. O resultado
alimenta de volta o cerebro. O sistema aprende enquanto gera.

Nao ha limite de tokens. O SessionCache mantem historico infinito.
Nao ha LLM. Nao ha PyTorch. Nao ha dependencias externas.
"""

import sys, os, time, json, re
from collections import deque
from typing import Dict, List, Tuple, Optional, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class MCRPipeline:
    """Pipeline de geracao contextualizada sem LLM.
    
    Conecta parse → cache → ponte → fragmento → geracao → aprendizado.
    """

    def __init__(self, cerebro):
        self.cerebro = cerebro
        self.fragmentador = MCRFragmentador("pipeline")
        self.total_gerado = 0
        self.tempo_total = 0.0
        
        # Inicializa niveis do coupling se necessario
        self._init_niveis()

    def _init_niveis(self):
        """Garante que niveis semanticos estao registrados."""
        if not hasattr(self.cerebro, '_pipeline_init'):
            for nivel in ['sujeito', 'relacao', 'objeto']:
                if nivel not in self.cerebro.coupling.niveis:
                    self.cerebro.topologia.registrar(nivel, MCR(nivel))
            self.cerebro._pipeline_init = True

    def executar(self, entrada, max_passos=6, contexto_extra="", verbose=False):
        """Executa pipeline completa: entrada → texto coerente.
        
        Args:
            entrada: str, texto de entrada (pergunta/contexto)
            max_passos: int, passos de geracao por fragmento
            contexto_extra: str, contexto adicional opcional
            verbose: bool, log detalhado
        
        Returns:
            str, texto gerado
        """
        t0 = time.perf_counter()
        self.fragmentador.limpar()
        resultado = ""
        
        # ─── 1. PARSE ───────────────────────────────────────────
        triplas = self._estagio_parse(entrada)
        
        # ─── 2. CONTEXTO ─────────────────────────────────────────
        contexto = self._estagio_contexto(entrada, triplas, contexto_extra)
        
        # ─── 3. PONTES ───────────────────────────────────────────
        pontes = self._estagio_pontes(entrada, triplas)
        
        # ─── 4. FRAGMENTACAO ─────────────────────────────────────
        fragmentos = self._estagio_fragmentar(entrada, contexto, pontes)
        
        # ─── 5. GERACAO ──────────────────────────────────────────
        for i, fragmento in enumerate(fragmentos):
            self.fragmentador.adicionar(
                f"gerar_{i}", self._gerar_fragmento,
                {'fragmento': fragmento, 'passos': max_passos})
        
        resultados = self.fragmentador.executar_todos()
        
        # Pega APENAS o melhor resultado (maior numero de tokens novos)
        melhor_resultado = ""
        melhor_n_tokens = 0
        for r in resultados:
            if r.sucesso and r.resultado:
                tokens_resp = r.resultado.split()
                # So considera se gerou algo alem do fragmento original
                if len(tokens_resp) > 2 and not any(t.startswith('B:') for t in tokens_resp):
                    if len(tokens_resp) > melhor_n_tokens:
                        melhor_resultado = r.resultado
                        melhor_n_tokens = len(tokens_resp)
        
        resultado = melhor_resultado
        
        # ─── 6. APRENDIZADO ──────────────────────────────────────
        if resultado:
            self._estagio_aprendizado(entrada, resultado)
        
        self.total_gerado += len(resultado.split())
        self.tempo_total += time.perf_counter() - t0
        
        if verbose:
            print(f"[Pipeline] {len(resultado.split())} tokens em {time.perf_counter()-t0:.2f}s")
            print(f"[Pipeline] Fragmentos: {len(fragmentos)}, Pontes: {len(pontes)}")
        
        return resultado if resultado else entrada

    def _estagio_parse(self, entrada):
        """Extrai triplas semanticas da entrada."""
        triplas = []
        try:
            triplas = self.cerebro.parser.extrair(entrada)
        except Exception:
            pass
        return triplas

    def _estagio_contexto(self, entrada, triplas, extra=""):
        """Absorve entrada no cache e pesca contexto relevante."""
        self.cerebro.session_cache.absorver(
            f"pipe_{self.total_gerado}",
            entrada, "request", tags=["pipeline"])
        
        pergunta = entrada
        if triplas:
            s, r, o = triplas[0]
            if o: pergunta = f"{s} {r} {o}"
        
        contexto = self.cerebro.session_cache.pescar(
            pergunta=pergunta, n=5, max_tokens=800)
        
        ctx_textos = []
        for frag in contexto:
            if frag and frag.conteudo and len(frag.conteudo) > 10:
                ctx_textos.append(frag.conteudo[:500])
        
        if extra:
            ctx_textos.append(extra)
        
        contexto_texto = " ".join(ctx_textos[-5:])
        
        # Se nao ha contexto suficiente, alimenta a entrada como aprendizado
        if len(contexto_texto.split()) < 5:
            self.cerebro.alimentar(entrada, f"ctx_{self.total_gerado}")
            contexto_texto = entrada
        
        return contexto_texto

    def _estagio_pontes(self, entrada, triplas):
        """Encontra pontes entre a entrada e topicos conhecidos."""
        pontes = []
        if not self.cerebro.topicos or len(self.cerebro.topicos) < 2:
            return pontes
        
        palavra_chave = ""
        if triplas:
            s, r, o = triplas[0]
            palavra_chave = o if o else s
        if not palavra_chave and entrada.split():
            palavra_chave = entrada.split()[-1]
        
        palavra_chave = palavra_chave.strip('.,!?;:()[]{}"\'')
        
        topicos = list(self.cerebro.topicos.keys())[:10]
        for topico in topicos:
            texto_topico = self.cerebro.topicos[topico].get('texto', '')
            if palavra_chave.lower() in texto_topico.lower():
                try:
                    chave_entrada = f"pipe_{max(0, self.total_gerado)}"
                    if chave_entrada in self.cerebro.topicos:
                        r = self.cerebro.conexao.analisar(chave_entrada, topico)
                        melhor = r.get('melhor')
                        if melhor and melhor.get('palavra'):
                            pontes.append(melhor['palavra'])
                except Exception:
                    pass
        
        return pontes[:5]

    def _estagio_fragmentar(self, entrada, contexto, pontes):
        """Fragmenta o contexto enriquecido em partes para geracao."""
        fragmentos = []
        
        # Fragmento 1: palavras-chave + ponte (pequeno, para geracao)
        palavras_chave = entrada.split()[-3:] if len(entrada.split()) >= 3 else entrada.split()
        if pontes:
            fragmentos.append(" ".join(palavras_chave + pontes))
        else:
            fragmentos.append(" ".join(palavras_chave))
        
        # Fragmento 2: contexto resumido (primeira frase apenas)
        if contexto and contexto != entrada:
            primeira_frase = contexto.split('.')[0] if '.' in contexto else contexto[:100]
            if primeira_frase not in fragmentos:
                fragmentos.append(primeira_frase)
        
        # Fragmento 3: sempre a entrada como fallback
        fragmentos.append(entrada[:100])
        
        return fragmentos[:3]

    def _gerar_fragmento(self, fragmento="", passos=6):
        """Gera texto para um fragmento. Usa entropia como temperatura e radar."""
        if not fragmento or not fragmento.strip():
            return ""
        
        fragmento_original = fragmento
        
        # Enriquece com contexto do SessionCache
        ctx_frags = self.cerebro.session_cache.pescar(
            pergunta=fragmento[:100], n=3, max_tokens=300)
        ctx_texto = ""
        for frag in ctx_frags:
            if frag and frag.conteudo and len(frag.conteudo) > 20:
                frase = frag.conteudo.split('.')[0] if '.' in frag.conteudo else frag.conteudo[:100]
                ctx_texto += " " + frase
        
        fragmento_enriquecido = fragmento
        if ctx_texto and len(ctx_texto.split()) > 2:
            fragmento_enriquecido = ctx_texto.strip()[:150] + " " + fragmento
        
        # Gera multiplos candidatos com temperatura entropica
        candidatos = []
        ultima_palavra = fragmento_enriquecido.split()[-1] if fragmento_enriquecido.split() else ""
        
        if ultima_palavra in self.cerebro.mk_palavra.freq:
            n_candidatos = max(2, min(8, int(self.cerebro.mk_palavra.entropia(ultima_palavra) * 3)))
            for _ in range(n_candidatos):
                resultado = self.cerebro._cadeia_pensamento(
                    fragmento_enriquecido, intencao="responder", passos=passos)
                if resultado and resultado != fragmento_original:
                    tokens_resp = resultado.split()
                    if len(tokens_resp) > 2 and not any(t.startswith('B:') for t in tokens_resp):
                        candidatos.append(" ".join(tokens_resp[:15]))
        
        # Seleciona o melhor candidato (maior diversidade de tokens)
        if candidatos:
            unicos = list(dict.fromkeys(candidatos))
            if unicos:
                return _rand.choice(unicos[:3]) if len(unicos) > 1 else unicos[0]
        
        # Fallback unico
        resultado = self.cerebro._cadeia_pensamento(
            fragmento_enriquecido, intencao="responder", passos=passos)
        if resultado and resultado != fragmento_original:
            tokens_resp = resultado.split()
            if len(tokens_resp) > 2 and not any(t.startswith('B:') for t in tokens_resp):
                return " ".join(tokens_resp[:15])
        
        return fragmento_original if len(fragmento_original.split()) <= 4 else ""

    def _estagio_aprendizado(self, entrada, saida):
        """Alimenta o resultado de volta no cerebro."""
        if not saida or saida == entrada:
            return
        
        # Aprende a transicao na cadeia palavra
        palavras_entrada = entrada.split()
        palavras_saida = saida.split()
        
        if palavras_entrada and palavras_saida:
            self.cerebro.mk_palavra.aprender(
                palavras_entrada[-1], palavras_saida[0])
        
        # Aprende transicoes internas da saida
        for i in range(len(palavras_saida) - 1):
            self.cerebro.mk_palavra.aprender(
                palavras_saida[i], palavras_saida[i+1])
        
        # Absorve no cache
        self.cerebro.session_cache.absorver(
            f"pipe_out_{self.total_gerado}",
            saida[:500], "resposta", tags=["pipeline", "gerado"])

    def stats(self):
        return {
            'total_gerado': self.total_gerado,
            'tempo_total': round(self.tempo_total, 2),
            'token_por_segundo': round(self.total_gerado / max(self.tempo_total, 0.001), 1),
            'fragmentos_total': self.fragmentador.total_sucesso + self.fragmentador.total_falha,
            'taxa_sucesso': self.fragmentador.stats()['taxa'],
        }


# ═══════════════════════════════════════════════════════════════════
# Teste / Demo
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    __file__ = os.path.join(os.path.dirname(__file__), '..', '..', 'MCR.py')
    with open(__file__, encoding='utf-8') as f:
        _code = f.read().split('def main():')[0]
    exec(compile(_code, 'MCR.py', 'exec'))
    
    print("=" * 55)
    print("  MCR PIPELINE — geracao sem LLM")
    print("=" * 55)
    
    c = CerebroAGI()
    pipe = MCRPipeline(c)
    
    # Alimenta conhecimento basico (20+ frases para Markov aprender)
    seeds = [
        "Sou um ferreiro experiente e trabalho com metal ha decadas",
        "Minha forja produz as melhores armas e armaduras da regiao",
        "Umo minerio de alta qualidade vindo das montanhas do norte",
        "Cada peca que sai da minha forja e testada pessoalmente",
        "O aco precisa ser aquecido ate ficar rubro antes de martelar",
        "Uma boa lamina leva horas de martelada e paciencia",
        "O fogo da forja nunca se apaga, nem durante a noite",
        "A tempera e a parte mais importante do processo",
        "Preciso de minerio fresco para continuar trabalhando",
        "Os melhores clientes voltam sempre pela qualidade",
        "Uma armadura bem feita pode salvar a vida do guerreiro",
        "A agua de tempera vem do rio cristalino da floresta",
        "O martelo e a bigorna sao as ferramentas mais importantes",
        "Cada golpe na bigorna e calculado com precisao",
        "O fole precisa ser acionado sem parar para manter a brasa",
        "A temperatura do ferro determina a qualidade do aco",
        "Um ferreiro nunca revela todos os seus segredos",
        "A forja e o coracao da minha oficina de ferreiro",
        "Trabalho com ferro aco prata e mitril quando encontro",
        "As melhores armas sao forjadas com paciencia e carinho",
    ]
    for i, texto in enumerate(seeds):
        c.alimentar(texto, f"seed_{i}")
    
    # Seeds de itens em ordem natural (tipo + qualidade)
    itens_data = [
        "espada rara de aco", "espada comum de ferro", "espada epica de prata",
        "armadura rara de aco", "armadura comum de ferro", "armadura epica de prata",
        "escudo raro de aco", "escudo comum de ferro", "escudo epico de prata",
        "elmo raro de aco", "elmo comum de ferro", "elmo epico de prata",
        "bota rara de aco", "bota comum de ferro", "bota epica de prata",
        "luvas raras de aco", "luvas comuns de ferro", "luvas epicas de prata",
        "espada lendaria de mitril", "armadura lendaria de mitril",
        "escudo lendario de mitril", "elmo lendario de mitril",
    ]
    for texto in itens_data:
        c.alimentar(texto, f"item_{abs(hash(texto))%10000}")
    
    # Alimenta conversas simuladas no SessionCache
    pipe.cerebro.session_cache.absorver("ctx_ferreiro",
        "Sou um ferreiro experiente. Trabalho com aco e ferro ha decadas. "
        "Minha forja produz as melhores armas e armaduras da regiao. "
        "Uso minerio de alta qualidade e tecnica de tempera especial.", "contexto")
    pipe.cerebro.session_cache.absorver("ctx_precos",
        "Os precos variam conforme o material e o tempo de trabalho. "
        "Uma espada de aco custa cerca de 200 a 500 moedas. "
        "Armaduras sao mais caras porque exigem mais material e tempo.", "contexto")
    pipe.cerebro.session_cache.absorver("ctx_materiais",
        "Mitril e um metal raro e leve, muito procurado por guerreiros. "
        "Trabalhar com mitril exige forja especial e tecnicas antigas. "
        "Pec,as de mitril sao valiosas e duradouras.", "contexto")
    
    # Pre-alimenta com uma conversa para acumular contexto
    pipe.executar("Ola, ferreiro! Preciso de uma arma.", max_passos=4)
    pipe.executar("Quanto custa uma espada de aco?", max_passos=4)
    
    # Testes
    entradas = [
        "Ola, ferreiro!",
        "Quanto custa uma espada de aco?",
        "Preciso de uma armadura para a batalha",
        "O que voce sabe sobre mitril?",
    ]
    
    for entrada in entradas:
        print(f"\n[Entrada] {entrada}")
        resultado = pipe.executar(entrada, max_passos=6, verbose=True)
        print(f"[Saida]   {resultado}")
    
    print(f"\n[Stats] {pipe.stats()}")
