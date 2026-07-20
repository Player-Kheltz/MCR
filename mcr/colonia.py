"""Colonia — auto-observacao populacional com recuperacao discriminativa.

A colonia alimenta seu proprio estado como features derivadas da
propria memoria P(b|a). Cada especialista e um sub-MCR. A colonia
cria automaticamente (necessidade), aprende com consequencias,
poda seletivamente.

Diferencial critico: a recuperacao do conhecimento (P(criar_X → bom/ruim))
usa _nmi_semantico + IDF em vez de raw decidir() (que e dominado por freq).
Como a sinonímia cross-idioma, a colonia discrimina "criar ferreiro = bom"
de "criar trol = ruim" pela estrutura das features, nao pela frequencia.

Pilar 1: P(b|a) — toda memoria e Markov transition count.
Pilar 2: thresholds e discriminacao emergem dos dados (NMI + IDF).
Pilar 5: ingerir, recuperar, aprender — loop completo.
Pilar 9: se nao sabe, admite honestamente.

Uso:
    from mcr.colonia import Colonia
    c = Colonia()
    c.passo("ferreiro")  # cria, aprende, vive
    c.ciclo_poda()       # poda seletivamente
    resultado = c.consultar_memoria("se eu criar trol agora")
"""
import math, re, copy
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple, Set, Any

from mcr.coupling import MCRCoupling


_RE_TOKENS = re.compile(r'[a-zà-ÿ]{2,}|[0-9]+')


# --- Ambiente de prova (dominios BONS/RUINS) ---
BONS = {
    "ferreiro": {"kws": ["forja", "espada", "armadura", "bigorna"]},
    "alquimista": {"kws": ["pocao", "erva", "veneno", "cura"]},
    "bibliotecario": {"kws": ["livro", "pergaminho", "mapa", "runas"]},
}
RUINS = {
    "trol": {"kws": ["ponte", "grito", "porrete", "caverna"]},
    "fantasma": {"kws": ["assombrar", "vento", "corrente", "cemiterio"]},
}
TODOS = {**BONS, **RUINS}


def _query(dom: str) -> str:
    kw = TODOS[dom]["kws"]
    return f"falar sobre {kw[0]} e {kw[2]}"


def _resposta(nome: str, turno: int) -> str:
    if nome in BONS and turno < 4:
        return f"{nome} responde"
    # RUINS em turno 0 retornam vazio para que o feedback
    # va para o else (feedback_ruim), nao para o if (feedback_bom).
    # "trol falha" nao e sucesso — e fracasso.
    if nome not in BONS and turno == 0:
        return ""
    return ""


class Colonia:
    """Colonia de especialistas com auto-observacao P(b|a).

    A colonia TEM uma memoria persistente (self.memoria, um MCRCoupling).
    Especialistas sao celulas (sub-MCRs): nascem, vivem, morrem.
    A colonia sobrevive as mortes e aprende com elas.

    A recuperacao do proprio conhecimento usa _nmi_semantico para
    discriminar P(feedback_X | criar_Y) onde raw decidir() e dominado
    por freq (auto_observacao=500 esmaga tudo).
    """

    def __init__(self):
        self.memoria = MCRCoupling()
        self.especialistas: Dict[str, MCRCoupling] = {}
        self.vidas: Dict[str, List[int]] = defaultdict(list)
        self.vida_atual: Dict[str, int] = defaultdict(int)
        self.criacoes = 0
        self.mortes = 0
        self.passos = 0

        self.memoria.alimentar("colonia existe", "acao_auto_observar")

    def _tem_especialista(self, nome: str) -> bool:
        """Auto-observacao: colonia consulta propria memoria."""
        criou = self.memoria._freq_acao.get("acao_criar_" + nome, 0)
        podou = self.memoria._freq_acao.get("acao_podar_" + nome, 0)
        return criou > podou

    def _auto_observar(self, query: str):
        """Alimenta estado da colonia como features na propria memoria."""
        for dom in TODOS:
            tem = self._tem_especialista(dom)
            self.memoria.alimentar(
                f"estado {dom}={tem}",
                "auto_observacao")
        self.memoria.alimentar(query, "input_recebido")

    def criar_especialista(self, nome: str, dominios: List[str]) -> bool:
        """Cria especialista e registra na memoria da colonia."""
        if nome in self.especialistas:
            return False
        esp = MCRCoupling()
        for dom in dominios:
            for kw in TODOS[dom]["kws"]:
                for _ in range(3):
                    esp.alimentar(f"falar sobre {kw}", "acao_" + dom)
                    esp.alimentar(f"sobre {kw}", "acao_" + dom)
        self.especialistas[nome] = esp
        self.vidas[nome] = []
        self.vida_atual[nome] = 0
        self.criacoes += 1
        self.memoria.alimentar(
            f"criei especialista {nome}",
            "acao_criar_" + nome)
        return True

    def podar_especialista(self, nome: str) -> bool:
        """Poda especialista e registra na memoria da colonia."""
        if nome not in self.especialistas:
            return False
        del self.especialistas[nome]
        del self.vidas[nome]
        del self.vida_atual[nome]
        self.mortes += 1
        self.memoria.alimentar(
            f"podei especialista {nome}",
            "acao_podar_" + nome)
        return True

    # ─── Recuperacao discriminativa via NMI ─────────────

    def _assinatura_pergunta(self, pergunta: str) -> Dict[str, int]:
        """Converte pergunta em features no mesmo formato de _extrair_features_nd.

        Gera features nos planos t:/c:/b:/bg:/ng:/p:/ca:/cd:/sl:/ngp:
        que sao os mesmos planos usados por _acao_features.

        Isto permite que _nmi_semantico compare apples-to-apples:
        query features vs acao features compartilham o mesmo schema.
        """
        raw = pergunta.lower().strip()
        sig: Dict[str, int] = {}

        tokens = _RE_TOKENS.findall(raw)
        if not tokens:
            tokens = [raw]

        for t in set(tokens):
            sig[f"t:{t}"] = sig.get(f"t:{t}", 0) + 1

        for ch in set(raw):
            if ch.isprintable() or ch in '\n\r\t':
                sig[f"c:{ch}"] = sig.get(f"c:{ch}", 0) + 1

        for byte in set(pergunta.encode('utf-8')):
            sig[f"b:{byte}"] = sig.get(f"b:{byte}", 0) + 1

        chars_only = re.sub(r'[^a-z0-9]', '', raw)
        for i in range(len(chars_only) - 1):
            bg = chars_only[i:i+2]
            sig[f"bg:{bg}"] = sig.get(f"bg:{bg}", 0) + 1
        for i in range(len(chars_only) - 2):
            ng = chars_only[i:i+3]
            sig[f"ng:{ng}"] = sig.get(f"ng:{ng}", 0) + 1

        for i, t in enumerate(tokens[:6]):
            sig[f"p{i}:{t[:12]}"] = sig.get(f"p{i}:{t[:12]}", 0) + 1

        for i in range(len(tokens)):
            if i > 0:
                sig[f"ca:{tokens[i-1]}"] = sig.get(f"ca:{tokens[i-1]}", 0) + 1
            if i < len(tokens) - 1:
                sig[f"cd:{tokens[i+1]}"] = sig.get(f"cd:{tokens[i+1]}", 0) + 1

        vogais = set('aeiouàáéíóúâêôãõ')
        for t in tokens:
            if len(t) < 4:
                continue
            silabas = []
            atual = ''
            for ch in t:
                atual += ch
                if ch in vogais:
                    silabas.append(atual)
                    atual = ''
            if atual:
                silabas.append(atual)
            for sl in silabas:
                if len(sl) >= 2:
                    sig[f"sl:{sl}"] = sig.get(f"sl:{sl}", 0) + 1

        for i in range(len(tokens) - 1):
            ngp = f"{tokens[i]}+{tokens[i+1]}"
            sig[f"ngp:{ngp}"] = sig.get(f"ngp:{ngp}", 0) + 1

        return sig

    def consultar_memoria(self, pergunta: str) -> Tuple[Optional[str], float]:
        """Consulta memoria usando NMI semantico em vez de raw decidir().

        Diferenca critica: em vez de P(b|a) bruto (dominado por freq),
        usa _nmi_semantico para comparar a assinatura contextual da
        pergunta com a assinatura de cada acao na memoria.

        Se a pergunta e "se eu criar ferreiro agora", compara com:
        - _acao_features["acao_feedback_bom"] (features de feedbacks bons)
        - _acao_features["acao_feedback_ruim"] (features de feedbacks ruins)
        - _acao_features["acao_criar_ferreiro"] (features de criacoes)

        A acao com maior NMI e a semanticamente mais relacionada.

        Returns:
            (acao, nmi_score) ou (None, 0.0) se sem dados
        """
        sig = self._assinatura_pergunta(pergunta)
        if not sig:
            return None, 0.0

        scores: Dict[str, float] = {}
        for acao, feat_dict in self.memoria._acao_features.items():
            feat_dict_plain = dict(feat_dict)
            if len(feat_dict_plain) < 3:
                continue
            nmi = self.memoria._nmi_semantico(sig, feat_dict_plain)
            scores[acao] = nmi

        if not scores:
            return None, 0.0
        melhor = max(scores.items(), key=lambda x: x[1])
        return melhor

    def _sinopse_especialista(self, nome: str) -> str:
        """Gera uma sinopse do especialista para consulta na memoria.

        Em vez de raw decidir(), que mistura tudo, cria uma pergunta
        estruturada que o NMI pode comparar com as assinaturas das acoes.
        """
        return f"especialista {nome} como se saiu"

    def avaliar_especialista(self, nome: str) -> Dict[str, Any]:
        """Avalia especialista via NMI, nao via raw freq.

        Compara a assinatura do especialista com:
        - acao_feedback_bom: quao similar e a feedbacks bons
        - acao_feedback_ruim: quao similar e a feedbacks ruins
        - acao_criar_{nome}: quao similar e a sua propria criacao
        - acao_podar_{nome}: quao similar e a sua poda

        Se NMI(bom) > NMI(ruim): especialista bem-sucedido
        Se NMI(ruim) > NMI(bom): especialista mal-sucedido
        """
        sig = self._assinatura_pergunta(self._sinopse_especialista(nome))
        if not sig:
            return {"nome": nome, "status": "sem_dados", "nmi_bom": 0.0, "nmi_ruim": 0.0}

        feat_bom = dict(self.memoria._acao_features.get("acao_feedback_bom", {}))
        feat_ruim = dict(self.memoria._acao_features.get("acao_feedback_ruim", {}))

        nmi_bom = self.memoria._nmi_semantico(sig, feat_bom) if feat_bom and len(feat_bom) >= 3 else 0.0
        nmi_ruim = self.memoria._nmi_semantico(sig, feat_ruim) if feat_ruim and len(feat_ruim) >= 3 else 0.0

        if nmi_bom > nmi_ruim:
            status = "bom"
        elif nmi_ruim > nmi_bom:
            status = "ruim"
        else:
            status = "neutro"

        return {
            "nome": nome,
            "status": status,
            "nmi_bom": round(nmi_bom, 4),
            "nmi_ruim": round(nmi_ruim, 4),
            "diferenca": round(nmi_bom - nmi_ruim, 4),
        }

    # ─── Ciclo de vida ─────────────

    def passo(self, dom_input: str):
        """Um ciclo da colonia:
        1. Auto-observa: alimenta estado como features
        2. Cria especialista se nao existe (necessidade, nao decisao)
        3. Encontra melhor especialista por similaridade
        4. Especialista responde
        5. Alimenta feedback bom/ruim na memoria da colonia
        """
        self.passos += 1
        nome_input = dom_input
        query = _query(nome_input)
        feats_in = set(_RE_TOKENS.findall(query.lower()))

        self._auto_observar(query)

        if not self._tem_especialista(nome_input):
            self.criar_especialista(nome_input, [nome_input])

        if not self.especialistas:
            return ("sem_especialistas", None, None)

        scores = []
        for n_esp, esp in self.especialistas.items():
            vocab = set(esp._palavra_acao.keys())
            jaccard = (len(feats_in & vocab) / max(1, len(feats_in | vocab))
                       if feats_in and vocab else 0.0)
            scores.append((n_esp, esp, jaccard))
        scores.sort(key=lambda x: -x[2])
        nome_venc, esp_venc, _ = scores[0]

        acao, conf = esp_venc.decidir(query, (None, 0.0))
        dom_acao = acao.replace("acao_", "") if acao.startswith("acao_") else None

        if dom_acao and dom_acao in TODOS:
            t = sum(self.vidas.get(nome_venc, [0]))
            resposta = _resposta(dom_acao, t)

            if resposta:
                esp_venc.alimentar(resposta, "acao_" + dom_acao)
                self.vida_atual[nome_venc] += 1
                self.memoria.alimentar(
                    f"especialista {nome_venc} respondeu bem",
                    "acao_feedback_bom")
                return ("resposta_ok", dom_acao, nome_venc)
            else:
                self.vidas[nome_venc].append(self.vida_atual[nome_venc])
                self.vida_atual[nome_venc] = 0
                self.memoria.alimentar(
                    f"especialista {nome_venc} falhou",
                    "acao_feedback_ruim")
                return ("resposta_falha", dom_acao, nome_venc)

        return ("ignorou", acao, None)

    def ciclo_poda(self):
        """Poda especialistas fracos.

        Diferente da versao v7 (threshold 2.0 hardcoded).
        Aqui a poda e acionada quando:
        1. O especialista tem historia longa (3+ ciclos de vida)
        2. E o NMI semantico indica que e mais similar a feedback_ruim
           que a feedback_bom

        Se nao ha dados de NMI suficientes, usa fallback conservador
        baseado em vida_media (threshold emergente = mediana).

        Pilar 2: threshold de poda emerge dos dados (mediana das vidas).
        """
        if not self.especialistas:
            return

        vidas_medias = []
        for nome in self.especialistas:
            todas = self.vidas.get(nome, []) + [self.vida_atual.get(nome, 0)]
            vm = sum(todas) / max(1, len(todas)) if todas else 0
            vidas_medias.append((nome, vm, todas))

        if not vidas_medias:
            return

        mediana = sorted(vm for _, vm, _ in vidas_medias)[len(vidas_medias) // 2]

        for nome, vm, todas in vidas_medias:
            if len(todas) < 3:
                continue
            if vm >= mediana:
                continue

            aval = self.avaliar_especialista(nome)
            deve_podar = False

            if aval["status"] == "ruim":
                deve_podar = True
            elif aval["status"] == "sem_dados" and vm < mediana * 0.5:
                deve_podar = True
            elif aval["status"] == "neutro" and vm < 1.0:
                deve_podar = True

            if deve_podar:
                self.podar_especialista(nome)

    # ─── Estatisticas ─────────────

    def estatisticas(self) -> Dict[str, Any]:
        """Retorna estado completo da colonia."""
        criou_bons = sum(1 for d in BONS if self._tem_especialista(d))
        criou_ruins = sum(1 for d in RUINS if self._tem_especialista(d))

        resultado = {
            "passos": self.passos,
            "especialistas_vivos": len(self.especialistas),
            "criacoes": self.criacoes,
            "mortes": self.mortes,
            "bons_vivos": criou_bons,
            "ruins_vivos": criou_ruins,
            "vocabulario_memoria": len(self.memoria._palavra_acao),
            "acoes_memoria": len(self.memoria._freq_acao),
            "especialistas": {},
        }

        for nome, esp in self.especialistas.items():
            resultado["especialistas"][nome] = {
                "acoes": len(esp._freq_acao),
                "palavras": len(esp._palavra_acao),
            }

        return resultado

    def resumo_memoria(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Top N acoes na memoria da colonia por frequencia."""
        return sorted(
            self.memoria._freq_acao.items(),
            key=lambda x: -x[1])[:top_n]

    def testar_discriminacao(self) -> Dict[str, Any]:
        """Testa se a colonia discrimina criar BONS vs RUINS via NMI.

        Usa dois formatos de pergunta:
        1. 'especialista {dom} como se saiu' (compartilha 'especialista'
           com os dados de feedback — NMI consegue discriminar)
        2. 'criar {dom} agora' (usa verbo no infinitivo, nao nos dados.
           A discriminacao depende de overlap char-level — mais fraco)

        Returns:
            dict com discriminacao por dominio e conclusao
        """
        resultado = {}
        acertos_direta = 0
        total_direta = 0
        acertos_sinopse = 0
        total_sinopse = 0

        for dom in TODOS:
            esperado = "bom" if dom in BONS else "ruim"

            # Formato 1: "criar X agora" (infinitivo)
            pergunta1 = f"criar {dom} agora"
            acao1, nmi1 = self.consultar_memoria(pergunta1)
            pred1 = ("bom" if acao1 and "bom" in acao1 else
                     "ruim" if acao1 and "ruim" in acao1 else "outro")

            # Formato 2: "especialista X como se saiu" (mesmo dos dados)
            pergunta2 = f"especialista {dom} como se saiu"
            acao2, nmi2 = self.consultar_memoria(pergunta2)
            pred2 = ("bom" if acao2 and "bom" in acao2 else
                     "ruim" if acao2 and "ruim" in acao2 else "outro")

            resultado[dom] = {
                "formato1": {"pergunta": pergunta1, "acao": acao1,
                             "nmi": round(nmi1, 4), "predito": pred1},
                "formato2": {"pergunta": pergunta2, "acao": acao2,
                             "nmi": round(nmi2, 4), "predito": pred2},
                "esperado": esperado,
            }

            if esperado == pred1:
                acertos_direta += 1
            total_direta += 1
            if esperado == pred2:
                acertos_sinopse += 1
            total_sinopse += 1

        resultado["_total"] = {
            "acuracia_formato1 (infinitivo)": round(
                acertos_direta / max(1, total_direta), 4),
            "acuracia_formato2 (sinopse)": round(
                acertos_sinopse / max(1, total_sinopse), 4),
        }

        return resultado

    def testar_poda_inteligente(self) -> Dict[str, Any]:
        """Testa se a poda prefere manter BONS e remover RUINS.

        Simula ciclos de vida e verifica:
        - Especialistas BONS sobrevivem mais que RUINS
        - A taxa de sobrevivencia de BONS > RUINS
        """
        sobreviveram = {}
        for dom in TODOS:
            aval = self.avaliar_especialista(dom)
            sobreviveram[dom] = aval

        bons_status = [s["status"] for d, s in sobreviveram.items() if d in BONS]
        ruins_status = [s["status"] for d, s in sobreviveram.items() if d in RUINS]

        bons_bons = bons_status.count("bom")
        ruins_ruins = ruins_status.count("ruim")

        return {
            "avaliacoes": sobreviveram,
            "bons_classificados_como_bom": bons_bons,
            "ruins_classificados_como_ruim": ruins_ruins,
            "discriminacao": bons_bons > 0 and ruins_ruins > 0,
        }


def auto_teste() -> Dict[str, Any]:
    """Roda ciclo completo e retorna diagnostico."""
    c = Colonia()

    for passo in range(100):
        dom = list(TODOS.keys())[passo % len(TODOS)]
        c.passo(dom)
        if (passo + 1) % 10 == 0:
            c.ciclo_poda()

    return {
        "estatisticas": c.estatisticas(),
        "resumo_memoria": c.resumo_memoria(12),
        "discriminacao": c.testar_discriminacao(),
        "poda_inteligente": c.testar_poda_inteligente(),
    }


if __name__ == "__main__":
    resultado = auto_teste()
    print("\n" + "=" * 65)
    print("  COLONIA — AUTO-TESTE")
    print("=" * 65)

    est = resultado["estatisticas"]
    print(f"\n  Especialistas vivos: {est['especialistas_vivos']}")
    print(f"  BONS vivos: {est['bons_vivos']}/{len(BONS)}")
    print(f"  RUINS vivos: {est['ruins_vivos']}/{len(RUINS)}")
    print(f"  Criacoes: {est['criacoes']}, Mortes: {est['mortes']}")
    print(f"  Vocab memoria: {est['vocabulario_memoria']}, Acoes: {est['acoes_memoria']}")

    print("\n--- Memoria da colonia (top 12 acoes) ---")
    for acao, freq in resultado["resumo_memoria"]:
        print(f"  {acao}: freq={freq}")

    print("\n--- Discriminacao NMI: criar X -> bom/ruim? ---")
    disc = resultado["discriminacao"]
    for dom, info in sorted(disc.items()):
        if dom.startswith("_"):
            continue
        print(f"  'criar {dom}' -> {info['acao']} (NMI={info['nmi']}) "
              f"esp={info['esperado']} pred={info['predito']}")

    print(f"\n  Acuracia discriminacao: {disc['_total']['acuracia']:.0%} "
          f"({disc['_total']['acertos']}/{disc['_total']['total']})")

    poda = resultado["poda_inteligente"]
    print(f"\n--- Poda inteligente ---")
    print(f"  BONS classificados como bom: {poda['bons_classificados_como_bom']}")
    print(f"  RUINS classificados como ruim: {poda['ruins_classificados_como_ruim']}")
    print(f"  Discriminacao operou: {poda['discriminacao']}")

    # Conclusao
    print("\n" + "=" * 65)
    print("  CONCLUSAO")
    print("=" * 65)
    est = resultado["estatisticas"]
    if est["bons_vivos"] > est["ruins_vivos"]:
        print("  >>> COLONIA APRENDEU: prefere BONS a RUINS")
        print("  A discriminacao via NMI/IDF recupera conhecimento")
        print("  que raw decidir() nao consegue (dominado por freq).")
    elif est["ruins_vivos"] == 0:
        print("  >>> COLONIA ELIMINOU TODOS OS RUINS")
        print("  Seletividade operou via NMI semantico na memoria.")
    else:
        print("  Colonia ainda aprendendo (poucos dados de feedback).")
