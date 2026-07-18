"""mcr.chat — Loop de conversa bidirecional 100% MCR.

Ciclo completo:
  1. Coldstart (consentimento LGPD + perguntas fundamentais)
     → respostas ingeridas no BaseConhecimento (Fix 1)
  2. Chat normal (humano ↔ MCR, bidirecional)
     → ContextBuffer ativo para contexto imediato (Fix 3)
     → GeradorCoerente para geração com working memory (Fix 2)
     → Admite ignorância quando não sabe (Pilar 9, Fix 4)
     → Registra episódio após cada interação (Fix 6)

Sem LLM. Sem API. Sem GPU.
"""
from typing import List, Tuple, Optional

from mcr.coupling import MCRCoupling
from mcr.coldstart import Coldstart
from mcr.perfil_humano import PerfilHumano


class MCRChat:

    def __init__(self, coupling: MCRCoupling = None,
                 perfil: PerfilHumano = None,
                 coldstart: Coldstart = None):
        self._coupling = coupling or MCRCoupling()
        if not self._coupling._total:
            self._coupling.load()
        self._perfil = perfil or PerfilHumano()
        self._coldstart = coldstart or Coldstart()
        self._coldstart.vincular_perfil(self._perfil)
        self._historico: List[dict] = []
        self._ultima_pergunta_cs: Optional[str] = None
        self._gerador = None  # lazy init
        self._auto_conhecimento = None  # lazy init
        self._ultima_ignorancia: Optional[str] = None  # pergunta que MCR nao soube

    @property
    def coupling(self) -> MCRCoupling:
        return self._coupling

    @property
    def perfil(self) -> PerfilHumano:
        return self._perfil

    @property
    def em_coldstart(self) -> bool:
        return self._coldstart.estado != Coldstart.CHAT

    def _get_gerador(self):
        """Lazy init do GeradorCoerente (Fix 2)."""
        if self._gerador is None:
            from mcr.gerador_coerente import GeradorCoerente
            self._gerador = GeradorCoerente(self._coupling)
        return self._gerador

    def _get_auto_conhecimento(self):
        """Lazy init do AutoConhecimento."""
        if self._auto_conhecimento is None:
            from mcr.auto_conhecimento import AutoConhecimento
            self._auto_conhecimento = AutoConhecimento(self._coupling)
        return self._auto_conhecimento

    def inicializar_conhecimento(self) -> int:
        """Alimenta o MCR com conhecimento base (data, identidade, vocabulario).

        Chamar apos coldstart para o MCR ter conhecimento basico.
        Returns: numero de fatos ingeridos.
        """
        ac = self._get_auto_conhecimento()
        return ac.ingerir_base()

    def _get_base_conhecimento(self):
        """Acessa BaseConhecimento registrado no triunvirato (Fix 1+4)."""
        delib = self._coupling._deliberacao
        if delib is None:
            delib = self._coupling._inic_deliberacao()
        return delib._fontes.get('BaseConhecimento') if delib else None

    # ─── Coldstart ──────────────────────────────────────────────

    def iniciar(self) -> str:
        """Inicia a sessao. Retorna primeira mensagem ao humano."""
        if self._coldstart.estado == Coldstart.CONSENTIMENTO:
            return self._coldstart.pergunta_consentimento()
        p = self._coldstart.pergunta_atual()
        if p:
            self._ultima_pergunta_cs = p
            return p
        # Ja passou do coldstart — ativa contexto conversacional
        self._coupling.ativar_contexto()
        return "pronto! o que voce gostaria de fazer?"

    def _processar_coldstart(self, entrada: str) -> Optional[str]:
        """Processa entrada durante coldstart. Retorna proxima pergunta ou None."""
        cs = self._coldstart

        if cs.estado == Coldstart.CONSENTIMENTO:
            consentiu = cs.processar_consentimento(entrada)
            if not consentiu:
                cs._estado = Coldstart.CHAT
                self._coupling.ativar_contexto()
                return "entendido. sem coleta de sinais. o que voce gostaria de fazer?"
            p = cs.pergunta_atual()
            if p:
                self._ultima_pergunta_cs = p
                return p
            self._coupling.ativar_contexto()
            return "obrigado! o que voce gostaria de fazer?"

        if cs.estado == Coldstart.PERGUNTAS:
            pergunta = self._ultima_pergunta_cs
            if pergunta:
                cs.processar_resposta(pergunta, entrada)
                # Fix 1: ingerir resposta no BaseConhecimento
                self._ingerir_coldstart_bc(pergunta, entrada)

            # Aprender resposta como observacao (Pilar 11)
            self._coupling.alimentar(entrada, "aprender")

            p = cs.pergunta_atual()
            if p:
                self._ultima_pergunta_cs = p
                return p

            # Transicionou para CHAT — ativa contexto (Fix 3)
            self._coupling.ativar_contexto()
            return "aprendi sobre voce. podemos comecar! o que quer fazer?"

        return None

    def _ingerir_coldstart_bc(self, pergunta: str, resposta: str) -> None:
        """Fix 1: ingerir resposta do coldstart no BaseConhecimento.

        Pilar 5: ingerir → recuperar → aprender.
        O BC extrai frases e indexa por conceito. Quando o humano
        perguntar algo relacionado, a busca ativa do triunvirato
        encontra os fatos ingeridos.
        """
        bc = self._get_base_conhecimento()
        if bc:
            bc.ingerir(f"pergunta: {pergunta} resposta: {resposta}", "coldstart")

    def _ingerir_explicacao(self, pergunta: str, explicacao: str) -> None:
        """Loop de auto-treinamento: humano explica → MCR ingere como fato.

        Pilar 5: ingerir → recuperar → aprender.
        Pilar 11: tudo que o humano diz entra como observacao.
        Proxima vez que alguem perguntar, o MCR sabe.
        """
        ac = self._get_auto_conhecimento()
        ac.ingerir_fato(
            f"pergunta: {pergunta} resposta: {explicacao}",
            "humano"
        )

    # ─── Chat principal ─────────────────────────────────────────

    def interagir(self, entrada: str) -> str:
        """Processa entrada do humano no loop de conversa.

        Fluxo:
          0. Se humano esta explicando algo (apos ignorancia) → ingerir como fato
          1. Se em coldstart → processar coldstart
          2. Classificar intencao via coupling (triunvirato decide)
          3. Se acao=responder → buscar no BC (Fix 4)
             → se BC encontra: usa fato
             → se BC nao encontra: admite ignorancia (Pilar 9)
          4. Se MCR seguro → gerar resposta via GeradorCoerente (Fix 2)
          5. Aprender (Pilar 11) + registrar episodio (Fix 6)

        Returns: resposta do MCR ao humano.
        """
        # Registrar no perfil (se consentido)
        self._perfil.registrar_resposta(entrada, self._complexidade_contexto())

        # Loop de auto-treinamento: se MCR admitiu ignorancia e humano respondeu
        # Pilar 1: IDF (P(palavra) invertido) define palavra-chave da pergunta
        # Pilar 5: ingerir → recuperar → aprender
        # Pilar 7: NMI morfologico NAO discrimina explicacao de pergunta quando
        #          ambas compartilham a palavra-chave. Usar IDF + informacao nova.
        # Pilar 9: admite ignorancia, e aprende quando humano explica
        if self._ultima_ignorancia and not self.em_coldstart:
            pergunta = self._ultima_ignorancia
            self._ultima_ignorancia = None

            import re as _re
            import math as _math

            pal_perg = set(_re.findall(r'[a-zà-ÿ]{3,}', pergunta.lower()))
            pal_entr = set(_re.findall(r'[a-zà-ÿ]{3,}', entrada.lower()))

            if pal_perg and pal_entr:
                # IDF de cada palavra da pergunta (do coupling)
                # Pilar 1: palavras raras (freq baixa) tem IDF alto = mais informativas
                total_global = self._coupling._total or 1
                idf_perg = {}
                for p in pal_perg:
                    freq = sum(self._coupling._palavra_acao.get(p, {}).values())
                    idf_perg[p] = _math.log(total_global / max(freq, 1))

                # Palavra-chave = palavra de maior IDF (mais rara/informadora)
                palavra_chave = max(idf_perg, key=idf_perg.get)

                # Criterio 1: entrada contem a palavra-chave (e relacionada à pergunta)
                # Criterio 2: entrada tem mais palavras novas que compartilhadas
                #             (traz mais informacao nova do que repete a pergunta)
                pal_novas = pal_entr - pal_perg
                pal_compart = pal_entr & pal_perg

                if palavra_chave in pal_entr and len(pal_novas) > len(pal_compart):
                    self._ingerir_explicacao(pergunta, entrada)
                    ack = "obrigado! aprendi algo novo."
                    self._historico.append({
                        'entrada': entrada, 'tipo': 'aprendizado',
                        'resposta': ack,
                    })
                    return ack
                # palavra-chave ausente ou pouca informacao nova → nova pergunta

        # Coldstart
        if self.em_coldstart:
            resp = self._processar_coldstart(entrada)
            if resp:
                self._historico.append({
                    'entrada': entrada, 'tipo': 'coldstart',
                    'resposta': resp,
                })
                return resp

        # Classificar intencao (triunvirato: 13 fontes + HRC + busca ativa)
        acao, conf = self._coupling.decidir(entrada, (None, 0.0))
        acao = acao or 'responder'

        # Pilar 5: recuperar → decidir. BC sempre primeiro, independente da acao.
        # Se BC encontra fato relevante, usa. Se nao, segue fluxo normal.
        resposta_bc = self._tentar_base_conhecimento(entrada)
        if resposta_bc:
            self._coupling.alimentar(entrada, acao)
            self._coupling.registrar_episodio(entrada, resposta_bc, "")
            self._historico.append({
                'entrada': entrada, 'acao': acao, 'conf': conf,
                'tipo': 'resposta_bc', 'resposta': resposta_bc,
            })
            return resposta_bc

        # BC nao encontrou — decidir entre ignorancia (Pilar 9) e acao executavel.
        # Acoes de chat (responder, descrever, etc.): quando BC nao encontra,
        # admite ignorancia e ativa auto-treinamento (humano pode explicar).
        # Acoes de jogo (gerar_*, etc.): sao executaveis, seguir fluxo normal.
        is_chat = (acao in ('responder', 'descrever', 'explicar',
                            'confirmar', 'ajudar', 'saudar'))
        if is_chat or conf < 0.5:
            ignorancia = "nao sei responder isso. posso aprender se voce me explicar."
            self._coupling.alimentar(entrada, acao)
            self._ultima_ignorancia = entrada
            self._historico.append({
                'entrada': entrada, 'acao': acao, 'conf': conf,
                'tipo': 'ignorancia', 'resposta': ignorancia,
            })
            return ignorancia

        # Avaliar lacuna — MCR questiona se incerto
        if self._deve_questionar(conf):
            pergunta = self._gerar_pergunta(entrada, acao, conf)
            self._coupling.alimentar(entrada, acao)
            self._historico.append({
                'entrada': entrada, 'acao': acao, 'conf': conf,
                'tipo': 'pergunta', 'resposta': pergunta,
            })
            return pergunta

        # Fix 2: gerar resposta via GeradorCoerente (working memory)
        resposta = self._gerar_resposta(acao)

        # Aprender (Pilar 11: tudo que humano diz vira observacao)
        self._coupling.alimentar(entrada, acao)
        if resposta and len(resposta.split()) >= 2:
            self._coupling.alimentar(resposta, acao)

        # Fix 6: registrar episodio (EpisodicGateway)
        self._coupling.registrar_episodio(entrada, resposta, "")

        self._historico.append({
            'entrada': entrada, 'acao': acao, 'conf': conf,
            'tipo': 'resposta', 'resposta': resposta,
        })

        return resposta or "hmm, nao sei o que dizer sobre isso."

    def _tentar_base_conhecimento(self, entrada: str) -> Optional[str]:
        """Consulta BaseConhecimento via IDF sobre todos os fatos.

        Pilar 1: P(palavra|fato) — IDF pondera palavras raras no BC.
        Pilar 2: threshold emerge do gap relativo entre scores.
        Pilar 5: recuperar → decidir.
        Pilar 7: NMI de assinatura nao discrimina fatos — IDF de palavras sim.
        Pilar 9: se nao sabe, admite — nao inventa.

        Criterio de relevancia (sem threshold hardcoded):
          - IDF(palavra) = log(N_fatos / df(palavra))
          - Score(fato) = soma de IDF para palavras em overlap
          - Gap relativo: maior despenca entre scores consecutivos define corte
          - Fatos acima do gap sao discriminativos
        """
        bc = self._get_base_conhecimento()
        if not bc:
            return None
        if not bc._fatos:
            return None

        import re as _re
        import math as _math

        # IDF: palavras que aparecem em poucos fatos sao mais discriminativas
        n_fatos = len(bc._fatos)
        df = {}
        for fato, fonte, conceito in bc._fatos:
            palavras_f = set(_re.findall(r'[a-zà-ÿ]{3,}', fato.lower()))
            for p in palavras_f:
                df[p] = df.get(p, 0) + 1

        palavras_entrada = set(_re.findall(r'[a-zà-ÿ]{3,}', entrada.lower()))
        if not palavras_entrada:
            return None

        # Score: max(IDF_ponderado) — palavra mais discriminativa dita o score
        # Pilar 1: P(palavra|BC) * P(palavra|coupling) — probabilidade composta
        # Stopwords (freq_coupling alta) tem peso reduzido e nao distorcem
        scores = []
        for fato, fonte, conceito in bc._fatos:
            palavras_fato = set(_re.findall(r'[a-zà-ÿ]{3,}', fato.lower()))
            overlap = palavras_entrada & palavras_fato
            if not overlap:
                continue
            pesos = []
            for p in overlap:
                df_p = df.get(p, 1)
                idf_bc = _math.log(n_fatos / df_p) if df_p > 0 else 0.0
                freq_c = sum(self._coupling._palavra_acao.get(p, {}).values())
                peso = idf_bc / (1 + _math.log(max(freq_c, 1)))
                pesos.append(peso)
            if pesos:
                # max puro: palavra mais discriminativa dita o score
                # se dois fatos tem a mesma palavra mais discriminativa, gap=0
                # → MCR admite ignorancia (Pilar 9: honesto, nao inventa)
                scores.append((max(pesos), fato, fonte))

        if not scores:
            return None

        scores.sort(key=lambda x: -x[0])

        # Gap relativo: encontrar maior despenca entre scores consecutivos
        # Pilar 2: threshold emerge dos dados — sem valor magico
        if len(scores) == 1:
            pass  # unico fato com overlap — usar
        else:
            maior_gap = 0.0
            for i in range(len(scores) - 1):
                if scores[i][0] <= 0:
                    continue
                gap = (scores[i][0] - scores[i + 1][0]) / scores[i][0]
                if gap > maior_gap:
                    maior_gap = gap
            # Se todos os scores sao iguais (gap=0), sem discriminancia
            if maior_gap <= 0:
                return None

        # Fato de maior score (sempre scores[0] — gap define corte, nao escolha)
        _, texto, fonte = scores[0]
        if 'resposta:' in texto:
            partes = texto.split('resposta:', 1)
            if len(partes) > 1:
                return partes[1].strip()
        return texto

    # ─── MCR que questiona ──────────────────────────────────────

    def _deve_questionar(self, conf: float) -> bool:
        """MCR decide se deve questionar o humano.

        Pilar 2: threshold emerge dos dados — confianca historica.
        """
        if conf >= 0.6:
            return False
        confs = [h.get('conf', 0.5) for h in self._historico
                 if h.get('tipo') == 'resposta']
        if len(confs) >= 3:
            ord_ = sorted(confs)
            mediana = ord_[len(ord_) // 3]
            if conf >= mediana:
                return False
        return conf < 0.4

    def _gerar_pergunta(self, entrada: str, acao: str, conf: float) -> str:
        """Gera pergunta ao humano quando MCR esta incerto.

        Pilar 11: pergunta e um convite ao humano (4D) para alinhar.
        """
        if conf < 0.2:
            return f"nao entendi bem '{entrada}'. pode explicar de outra forma?"
        if conf < 0.4:
            return f"sobre '{entrada}' — voce quer que eu faca algo especifico? me de mais detalhes."
        return f"antes de responder sobre {entrada[:30]}, voce prefere algo mais especifico?"

    # ─── Complexidade do contexto ───────────────────────────────

    def _complexidade_contexto(self) -> float:
        """Estima complexidade do contexto atual para o perfil humano.

        Pilar 2: complexidade = entropia do historico recente.
        """
        if not self._historico:
            return 0.0
        recentes = self._historico[-5:]
        palavras = set()
        for h in recentes:
            palavras.update(h.get('entrada', '').split())
        n = len(palavras)
        return min(1.0, n / 20)

    # ─── Geracao de resposta (Fix 2: GeradorCoerente) ───────────

    def _gerar_resposta(self, semente: str, max_tokens: int = 50) -> Optional[str]:
        """Fix 2: gera texto via GeradorCoerente com working memory.

        Ressalva honesta (Pilar 9): working memory de 3 buffers contorna
        o limite de Markov 1ª ordem, nao o resolve. Gera mais coerente
        que Markov puro, mas ainda colapsa em ~N tokens (N >> 20).
        """
        gen = self._get_gerador()
        return gen.gerar(semente, max_tokens=max_tokens)

    # ─── Teto de paciencia ──────────────────────────────────────

    def teto_paciencia(self) -> float:
        """Teto de paciencia aprendido do humano.

        Pilar 2: emerge dos dados do perfil humano.
        """
        if self._perfil.consentido():
            return self._perfil.teto_paciencia()
        return 60.0

    def deve_lembrar_humano(self, tempo_espera: float) -> bool:
        """MCR decide se deve lembrar o humano que esta esperando."""
        teto = self.teto_paciencia()
        return tempo_espera > teto * 0.5

    def mensagem_lembrete(self, tempo_espera: float) -> Optional[str]:
        """Mensagem de lembrete quando humano demora."""
        if not self.deve_lembrar_humano(tempo_espera):
            return None
        segs = int(tempo_espera)
        return f"ainda estou aqui... ({segs}s)"

    # ─── Persistencia (Fix 5) ───────────────────────────────────

    def salvar(self, caminho: str = None) -> None:
        """Fix 5: salva perfil humano e coldstart para persistir entre sessoes."""
        import os, json
        if caminho is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            caminho = os.path.join(base, 'cache', 'mcr_sessao.json')
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        dados = {
            'perfil': self._perfil.to_dict() if hasattr(self._perfil, 'to_dict') else {},
            'coldstart': self._coldstart.to_dict() if hasattr(self._coldstart, 'to_dict') else {},
            'historico': self._historico[-100:],
        }
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def carregar(self, caminho: str = None) -> bool:
        """Fix 5: carrega perfil humano e coldstart de sessao anterior."""
        import os, json
        if caminho is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            caminho = os.path.join(base, 'cache', 'mcr_sessao.json')
        if not os.path.exists(caminho):
            return False
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            # Restaurar coldstart
            cs_dados = dados.get('coldstart', {})
            if cs_dados.get('estado') == Coldstart.CHAT:
                self._coldstart._estado = Coldstart.CHAT
                self._coldstart._perguntas_feitas = list(cs_dados.get('perguntas_feitas', []))
                self._coldstart._respostas = dict(cs_dados.get('respostas', {}))
                self._coldstart._confiancas = list(cs_dados.get('confiancas', []))
            # Restaurar historico
            self._historico = dados.get('historico', [])
            # Perfil: restaurar consentimento
            if dados.get('perfil', {}).get('consentido'):
                self._perfil.consentir()
            return True
        except Exception:
            return False

    # ─── Estado ─────────────────────────────────────────────────

    def historico(self, n: int = 5) -> List[dict]:
        return self._historico[-n:]

    def estado(self) -> dict:
        est = self._coupling.estatisticas()
        return {
            'fase': self._coldstart.estado,
            'consentido': self._perfil.consentido(),
            'perfil': self._perfil.to_dict() if hasattr(self._perfil, 'to_dict') else {},
            'observacoes': est['total'],
            'palavras': est['palavras'],
            'interacoes': len(self._historico),
            'teto_paciencia': round(self.teto_paciencia(), 1),
            'contexto_ativo': self._coupling._contexto_ativo,
        }
