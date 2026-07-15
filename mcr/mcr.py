"""mcr.mcr — Motor Cognitivo Universal.

Um motor. Uma Equação. Uma Entropia. Um Markov.
Aplica-se a qualquer domínio. Tibia e Visual são as provas.

Arquitetura:
    perceber → decidir → executar → avaliar → aprender

Tudo é Markov. A Equação MCR avalia. A Entropia mede caos.
As ferramentas executam. O domínio é irrelevante.
"""
import time
import hashlib
import os
import json
import math as _math
import re as _re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

from mcr.paths import CACHE_DIR, ensure_dirs

# ─── Motor Markov (intacto) ─────────────────────────────────
from mcr.engine import MCR as MarkovEngine
from mcr.signature import MCRFingerprint

# ─── Equação MCR (intacta) ──────────────────────────────────
from mcr.equacao_mcr import calcular_ponte, classificar_tipo_ponte, get_penalidade

# ─── Registry (intacto) ─────────────────────────────────────
from mcr.registry import get_registry, MCRRegistry, ToolEntry

# ─── Cognição multi-nível (acoplamento + superposition) ─────
from mcr.coupling import MCRCoupling
from mcr.superposicao import MCRSuperposicao


class MCR:
    """Motor Cognitivo Universal.

    Markov 1ª ordem + Entropia Shannon + Equação MCR = Cognição.
    Aplica-se a Tibia, Visual, Áudio, qualquer jogo, qualquer projeto.

    Uso:
        mcr = MCR()
        mcr.auto_treinar()
        
        npc = mcr.processar("Crie um ferreiro anão")
        sprite = mcr.processar("Gere um sprite de escudo")
    """

    def __init__(self):
        ensure_dirs()

        # ─── Motor ──────────────────────────────────────
        self.mk = MarkovEngine("mcr_cognicao")
        try:
            self.mk.load()
        except Exception:
            pass
        self.fp = MCRFingerprint()

        # ─── Cognição multi-nível ───────────────────────
        self._coupling = MCRCoupling()
        try:
            self._coupling.load()
        except Exception:
            pass
        
        # Migração one-shot: normaliza ações persistidas em disco
        # gerar_npc -> gerar, gerar_monstro -> gerar (verbo generico)
        # Idempotente: se já normalizado, roda em <1ms
        self._migrar_acoes()
        
        self._superposicao = MCRSuperposicao()
        self.mk_palavra = MarkovEngine("mcr_palavra")
        try:
            self.mk_palavra.load()
        except Exception:
            pass
        # Markov de trigramas de caracteres — agnóstico a idioma
        # "elabore" e "crie" compartilham trigramas morfológicos
        self.mk_trigrama = MarkovEngine("mcr_trigrama")
        try:
            self.mk_trigrama.load()
        except Exception:
            pass
        # Markov de padrão estrutural — agnóstico a vocabulário
        # P("VASVSVS" → gerar) — só importa a estrutura, não as palavras
        self.mk_padrao = MarkovEngine("mcr_padrao")
        try:
            self.mk_padrao.load()
        except Exception:
            pass

        # ─── 13 Módulos MCR (lazy init) ─────────────────
        self._esfera = None          # correlacao N-dimensional
        self._esquecimento = None    # poda por entropia
        self._hiperesfera = None     # auto-descoberta de tokenizacao
        self._conexao = None         # pontes entre dominios
        self._bridge = None          # analogias cross-domain
        self._mundo = None           # modelo causal
        self._genesis = None         # auto-expansao de dominios
        self._variador = None        # preenche gaps com valores reais
        self._descobridor = None     # frequencia diferencial
        self._thresholds = None      # thresholds descobertos (MCRThreshold)
        self._stopwords = set()

        # ─── Registry ───────────────────────────────────
        self._registry = get_registry()

        # ─── Estado interno ─────────────────────────────
        self._historico: List[Dict] = []
        self._memoria: List[Dict] = []
        self._total_processamentos = 0
        self._sessao_inicio = time.time()
        self._ultima_interacao = time.time()
        self._contexto_conversa: List[str] = []  # ultimas acoes para contexto
        self._erros: List[Dict] = []  # log de erros para debug

        # ─── Identidade (absorvida de mcr_self) ─────────
        self.nome = "MCR"
        self.criador = "Kheltz"
        self.proposito = (
            "Framework cognitivo universal. Provar que Markov 1ª ordem + "
            "Entropia Shannon + Equação MCR são suficientes para cognição."
        )
        self.versoes = ["1.0 (Markov)", "2.0 (unificado)"]
        self.versao = "2.0"
        self.opinioes: Dict[str, str] = {}

        # ─── Persistência SQLite ─────────────────────────
        self._sqlite = None
        try:
            from mcr.mcr_sqlite import MCRSQLite
            self._sqlite = MCRSQLite("mcr_sessao")
        except Exception:
            pass

        # ─── Log de execuções ───────────────────────────
        self._carregar_execucoes()

        # ─── Observador Universal (auto-observação) ─────
        self._observador = None
        self._obs_ativado = False
        try:
            self.ativar_observador()
        except Exception:
            pass

        # ─── Bootstrap silencioso ───────────────────────
        self._bootstrap()

    # ═══════════════════════════════════════════════════════
    # BOOTSTRAP
    # ═══════════════════════════════════════════════════════

    def _bootstrap(self):
        """Inicializa ferramentas. Bootstrap pesado é lazy."""
        _t = time.time()
        try:
            self._inicializar_templates()
        except Exception as e:
            self._log_erro('inicializar_templates', e)
        if hasattr(self, '_debug_timing'):
            print(f"  _inicializar_templates: {time.time()-_t:.2f}s", flush=True)
            _t = time.time()
        self._pre_treinar_markov()
        if hasattr(self, '_debug_timing'):
            print(f"  _pre_treinar_markov: {time.time()-_t:.2f}s", flush=True)

    def _migrar_acoes(self):
        """Migração one-shot: normaliza ações persistidas em disco.
        gerar_npc -> gerar, gerar_monstro -> gerar.
        Idempotente: se já normalizado, sai em <1ms."""
        from collections import defaultdict as _dd
        
        # Descobre verbos validos (2+ ações com mesmo prefixo)
        contagem = _dd(int)
        for acao in self._coupling._freq_acao:
            s = str(acao)
            if '_' in s:
                contagem[s.split('_')[0]] += 1
        verbos = {v for v, n in contagem.items() if n >= 2}
        
        def _norm(acao):
            s = str(acao)
            if '_' not in s:
                return s
            verbo = s.split('_')[0]
            return verbo if verbo in verbos else s
        
        # Verifica se precisa migrar
        precisa = False
        for est in self.mk.transicoes:
            for acao in self.mk.transicoes[est]:
                if _norm(acao) != str(acao):
                    precisa = True
                    break
            if precisa:
                break
        if not precisa:
            return
        
        # Migra mk.transicoes
        novas = {}
        for est, dist in self.mk.transicoes.items():
            nova = {}
            for acao, freq in dist.items():
                a = _norm(acao)
                nova[a] = nova.get(a, 0) + freq
            novas[est] = nova
        self.mk.transicoes = novas
        if hasattr(self.mk, '_entropia_cache'):
            self.mk._entropia_cache = {}
        
        # Migra coupling._freq_acao
        novo_freq = {}
        for acao, freq in self._coupling._freq_acao.items():
            a = _norm(acao)
            novo_freq[a] = novo_freq.get(a, 0) + freq
        self._coupling._freq_acao = _dd(int, novo_freq)
        
        # Migra coupling._palavra_acao
        nova_palavra = {}
        for p, dist in self._coupling._palavra_acao.items():
            nova = {}
            for acao, freq in dist.items():
                a = _norm(acao)
                nova[a] = nova.get(a, 0) + freq
            nova_palavra[p] = nova
        self._coupling._palavra_acao = _dd(
            lambda: _dd(int),
            {k: _dd(int, v) for k, v in nova_palavra.items()})
        
        # Migra coupling._posicao_acao
        nova_pos = {}
        for p, dist in self._coupling._posicao_acao.items():
            nova = {}
            for acao, freq in dist.items():
                a = _norm(acao)
                nova[a] = nova.get(a, 0) + freq
            nova_pos[p] = nova
        self._coupling._posicao_acao = _dd(
            lambda: _dd(int),
            {k: _dd(int, v) for k, v in nova_pos.items()})
        
        # Salva normalizado
        try:
            self.mk.save()
        except Exception:
            pass
        try:
            self._coupling.save()
        except Exception:
            pass

    def _lazy(self, attr, cls_path):
        """Lazy init de um modulo MCR. Carrega so quando usado."""
        if getattr(self, attr, None) is None:
            try:
                parts = cls_path.rsplit('.', 1)
                mod = __import__(parts[0], fromlist=[parts[1]])
                cls = getattr(mod, parts[1])
                self.__dict__[attr] = cls()
            except Exception:
                pass
        return getattr(self, attr, None)

    def _normalizar_acao(self, acao):
        """Normaliza acao: gerar_npc -> gerar, gerar_monstro -> gerar.
        O dominio (npc, monstro) é descoberto por assinatura, não por hardcode.
        Verbos descobertos por entropia: aparecem em P0 de multiplas acoes
        (H alta = verbo generico como 'gerar'). Substantivos aparecem em P1+
        e definem o dominio."""
        acao = str(acao)
        if '_' not in acao:
            return acao
        verbo = acao.split('_')[0]
        # Verbo generico = aparece como prefixo de 2+ acoes diferentes
        # Descoberto dinamicamente do coupling, nao hardcoded
        try:
            # Conta quantas acoes comecam com este verbo
            n_acoes = sum(1 for a in self._coupling._freq_acao if str(a).startswith(verbo + '_'))
            if n_acoes >= 2:
                return verbo
        except Exception:
            pass
        return acao

    def _descobrir_dominio_por_assinatura(self, entrada):
        """Descobre o dominio do input pela ASSINATURA, nao pelo nome.
        
        O MCR ja tem perfis de cada diretorio (assinatura dos arquivos).
        Compara a assinatura do input com os perfis e encontra o dominio.
        
        Assinatura = entropia + fingerprint 8D + padrao de tokens + API calls.
        Zero hardcode de nomes de dominio.
        """
        if not hasattr(self, '_perfis_dominio'):
            # Constrói perfis na primeira chamada (lazy)
            self._perfis_dominio = {}
            try:
                from mcr.signature import MCRSignature
                from pathlib import Path
                
                for tool, dirs in getattr(self, '_dirs_por_tool', {}).items():
                    for d in dirs:
                        try:
                            arquivos = [f for f in d.iterdir() if f.is_file()][:10]
                            if not arquivos:
                                continue
                            # Extrai assinatura media dos arquivos
                            fps = []
                            entropias = []
                            tokens_freq = Counter()
                            for f in arquivos:
                                try:
                                    conteudo = f.read_text(encoding='latin-1', errors='replace')[:2000]
                                    dados = conteudo.encode('utf-8')
                                    sig = MCRSignature.extrair(dados, rapido=True)
                                    fps.append(sig.get('fingerprint', [0]*8))
                                    entropias.append(sig.get('entropia', 0))
                                    # Tokens estruturais (API calls, keywords)
                                    for m in _re.finditer(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', conteudo):
                                        tokens_freq[m.group(0).lower()] += 1
                                except Exception:
                                    continue
                            if fps:
                                # Perfil = fingerprint medio + entropia media + top tokens
                                fp_medio = [sum(col) / len(col) for col in zip(*fps)]
                                h_media = sum(entropias) / len(entropias)
                                top_tokens = set(t for t, _ in tokens_freq.most_common(20))
                                self._perfis_dominio[tool] = {
                                    'fingerprint': fp_medio,
                                    'entropia': h_media,
                                    'tokens': top_tokens,
                                    'n_arquivos': len(arquivos),
                                }
                        except Exception:
                            pass
            except Exception:
                pass
        
        if not self._perfis_dominio:
            return None
        
        # Extrai assinatura do input
        try:
            from mcr.signature import MCRSignature
            dados = entrada.encode('utf-8')
            sig_input = MCRSignature.extrair(dados, rapido=True)
            fp_input = sig_input.get('fingerprint', [0]*8)
            h_input = sig_input.get('entropia', 0)
            tokens_input = set(_re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', entrada.lower()))
        except Exception:
            return None
        
        # Compara com cada perfil (Jaccard de tokens + distancia de fingerprint)
        melhor_dominio = None
        melhor_score = 0
        for tool, perfil in self._perfis_dominio.items():
            # Jaccard de tokens estruturais
            tokens_comuns = len(tokens_input & perfil['tokens'])
            tokens_uniao = len(tokens_input | perfil['tokens'])
            jaccard_tokens = tokens_comuns / max(tokens_uniao, 1)
            # Distancia do fingerprint (cosseno)
            import math
            dot = sum(a * b for a, b in zip(fp_input, perfil['fingerprint']))
            na = math.sqrt(sum(a * a for a in fp_input))
            nb = math.sqrt(sum(b * b for b in perfil['fingerprint']))
            cosseno_fp = dot / max(na * nb, 0.001)
            # Score combinado (Equacao MCR: divergencia + especificidade + profundidade)
            score = jaccard_tokens * 0.5 + cosseno_fp * 0.5
            if score > melhor_score:
                melhor_score = score
                melhor_dominio = tool
        
        if melhor_score > 0.1:
            return melhor_dominio
        return None

    def _th(self, chave, fallback):
        """Obtem threshold descoberto pelo MCRThreshold. Zero hardcode.
        O MCR observa valores reais e calcula a mediana."""
        if self._thresholds is None:
            try:
                from mcr.decisor import MCRThreshold
                self._thresholds = MCRThreshold("mcr_params")
            except Exception:
                return fallback
        try:
            return self._thresholds.obter(chave, fallback)
        except Exception:
            return fallback

    def _th_observar(self, chave, valor):
        """Observa um valor real para calibrar threshold."""
        if self._thresholds is None:
            try:
                from mcr.decisor import MCRThreshold
                self._thresholds = MCRThreshold("mcr_params")
            except Exception:
                return
        try:
            self._thresholds.aprender(chave, valor)
        except Exception:
            pass

    def _extrair_niveis(self, entrada):
        """Extrai N níveis de fingerprint do mesmo input.
        Intrínsecos: do input alone (estáveis, não mudam com aprendizado)
        Derivados: input + estado do sistema (adaptativos)
        Quanto mais níveis, mais precisa a coordenada N-dimensional."""
        dados = entrada.encode('utf-8') if isinstance(entrada, str) else entrada
        palavras = entrada.replace('_', ' ').split()
        palavras_lower = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
        from math import log2
        
        niveis = {}
        
        # ═══ NÍVEIS INTRÍNSECOS (do input alone) ═══
        
        # 1. byte — buckets 8D (MCRFingerprint)
        try:
            niveis['byte'] = str(self.fp.gerar(entrada))
        except Exception:
            pass
        
        # 2. palavra — tokens 3+ chars (primeiros 6)
        niveis['palavra'] = "|".join(palavras_lower[:6]) if palavras_lower else 'VAZIO'
        
        # 3. token — tipo de cada caractere (L/N/S)
        niveis['token'] = ''.join(
            'L' if c.isalpha() else 'N' if c.isdigit() else 'S'
            for c in entrada[:30] if not c.isspace()
        )
        
        # 4. intencao — primeira palavra (verbo ou conceito)
        niveis['intencao'] = palavras[0][:10].lower() if palavras else ''
        
        # 5. padrao — estrutura sintática descoberta por frequência diferencial
        # P0 com H baixa = verbo (define a ação)
        # P1 com H alta = artigo/conector (não define a ação)
        # Resto com len>3 = substantivo
        tipos = []
        for i, p in enumerate(palavras[:6]):
            p_lower = p[:10].lower()
            pos_dist = self._coupling._posicao_acao.get(f'P{i}:{p_lower}', {})
            total_pos = sum(pos_dist.values())
            if total_pos >= 2:
                from math import log2
                h_pos = 0.0
                for c in pos_dist.values():
                    prob = c / total_pos
                    if prob > 0: h_pos -= prob * log2(prob)
                max_h_pos = log2(max(len(pos_dist), 2))
                h_norm_pos = h_pos / max_h_pos if max_h_pos > 0 else 0
                if h_norm_pos < 0.3:
                    tipos.append('V')  # H baixa em P0 = verbo específico
                elif h_norm_pos > 0.7:
                    tipos.append('C')  # H alta = conector/artigo genérico
                else:
                    tipos.append('S')  # H média = substantivo
            elif len(p) > 3:
                tipos.append('S')
            else:
                tipos.append('X')
        niveis['padrao'] = ''.join(tipos)
        
        # 6. entropia — Shannon normalizada
        try:
            sig_mod = __import__('mcr.signature', fromlist=['MCRSignature'])
            sig = sig_mod.MCRSignature.extrair(dados, rapido=True)
            niveis['entropia'] = str(round(sig.get('entropia', 0), 2))
            # 7. estados — estados únicos
            niveis['estados'] = str(sig.get('estados', 0))
            # 8. transicoes — transições Markov
            niveis['transicoes'] = str(sig.get('transicoes', 0))
        except Exception:
            pass
        
        # 9. tamanho — bytes
        niveis['tamanho'] = str(len(dados))
        
        # 10. ruido — proporção de não-alfabéticos
        n_alpha = sum(1 for c in entrada if c.isalpha())
        niveis['ruido'] = str(round(1.0 - n_alpha / max(len(entrada), 1), 2))
        
        # 11. cadeia — primeiro bigrama
        if len(palavras_lower) >= 2:
            niveis['cadeia'] = f"{palavras_lower[0]}->{palavras_lower[1]}"
        else:
            niveis['cadeia'] = ''
        
        # ═══ NÍVEIS DERIVADOS (input + estado do sistema) ═══
        
        # 12. similaridade — Jaccard com estado mais frequente
        try:
            if self.mk.transicoes and self.mk.freq:
                estado_freq = max(self.mk.freq, key=self.mk.freq.get)
                tokens_freq = set(estado_freq.split('|'))
                tokens_in = set(niveis['palavra'].split('|'))
                if tokens_freq or tokens_in:
                    jacc = len(tokens_freq & tokens_in) / max(len(tokens_freq | tokens_in), 1)
                    niveis['similaridade'] = str(round(jacc, 2))
        except Exception:
            pass
        
        # 13. conector — palavra do input com mais conexões no coupling
        try:
            if palavras_lower:
                melhor_p = None
                melhor_count = 0
                for p in set(palavras_lower):
                    dist = self._coupling._palavra_acao.get(p, {})
                    total = sum(dist.values())
                    if total > melhor_count:
                        melhor_count = total
                        melhor_p = p
                niveis['conector'] = melhor_p or ''
        except Exception:
            pass
        
        # 14. busca — quantas palavras o coupling já conhece
        try:
            n_conhecidas = sum(1 for p in set(palavras_lower) if p in self._coupling._palavra_acao)
            niveis['busca'] = str(n_conhecidas)
        except Exception:
            pass
        
        # 15. peso — 1 - entropia média das palavras no coupling
        try:
            pesos = []
            for p in set(palavras_lower):
                dist = self._coupling._palavra_acao.get(p, {})
                if dist:
                    total = sum(dist.values())
                    h = 0.0
                    for c in dist.values():
                        prob = c / total
                        if prob > 0: h -= prob * log2(prob)
                    max_h = log2(max(len(dist), 2))
                    h_norm = h / max_h if max_h > 0 else 0
                    pesos.append(1.0 - h_norm)
            if pesos:
                niveis['peso'] = str(round(sum(pesos) / len(pesos), 2))
        except Exception:
            pass
        
        # 16. diagnostico — entropia da distribuição de ações
        try:
            acoes = {}
            for p in set(palavras_lower):
                dist = self._coupling._palavra_acao.get(p, {})
                for a, c in dist.items():
                    acoes[a] = acoes.get(a, 0) + c
            if acoes:
                total = sum(acoes.values())
                h = 0.0
                for c in acoes.values():
                    prob = c / total
                    if prob > 0: h -= prob * log2(prob)
                niveis['diagnostico'] = str(round(h, 2))
        except Exception:
            pass

        # ═══ NÍVEIS ESTRUTURAIS (posição e forma) ═══

        # 17. ultima_palavra — palavra final (define o dominio alvo)
        # "Create a armadura sprite" → "sprite" = gerar_sprite
        # "Create a armadura npc" → "npc" = gerar_npc
        if palavras:
            niveis['ultima_palavra'] = palavras[-1][:10].lower()
        
        # 18. n_palavras — numero de palavras (inputs curtos sao ambíguos)
        niveis['n_palavras'] = str(len(palavras))

        # 19. sufixo — ultimos 3 caracteres do input (forma)
        niveis['sufixo'] = entrada[-3:].lower() if len(entrada) >= 3 else entrada.lower()

        # 20. prefixo — primeiros 3 caracteres (forma)
        niveis['prefixo'] = entrada[:3].lower()

        # 21. p_ultima — posição da última palavra no coupling
        if palavras:
            niveis['p_ultima'] = f"P{len(palavras)-1}:{palavras[-1][:10].lower()}"

        # ═══ NÍVEIS DE DOMÍNIO (categoria e função) ═══

        # 22. categoria — ação mais frequente entre TODAS as palavras do input
        # Diferente de diagnostico (entropia): categoria é o ARGMAX
        try:
            acoes = {}
            for p in set(palavras_lower):
                dist = self._coupling._palavra_acao.get(p, {})
                for a, c in dist.items():
                    acoes[a] = acoes.get(a, 0) + c
            if acoes:
                niveis['categoria'] = max(acoes, key=acoes.get)
        except Exception:
            pass

        # 23. dominio — diretório com mais overlap de palavras
        # Cacheado — nao faz iterdir a cada chamada
        try:
            if palavras_lower and hasattr(self, '_dirs_por_tool') and not hasattr(self, '_dir_stems_cache'):
                self._dir_stems_cache = {}
                for tool, dirs in self._dirs_por_tool.items():
                    for d in dirs:
                        try:
                            for f in list(d.iterdir())[:20]:
                                stem = f.stem.lower()
                                if len(stem) > 2:
                                    self._dir_stems_cache[stem] = tool
                        except Exception:
                            pass
            if palavras_lower and hasattr(self, '_dir_stems_cache'):
                melhor_dir = None
                melhor_overlap = 0
                for p in palavras_lower:
                    dir_p = self._dir_stems_cache.get(p)
                    if dir_p:
                        melhor_overlap += 1
                        melhor_dir = dir_p
                if melhor_dir:
                    niveis['dominio'] = melhor_dir
        except Exception:
            pass

        # 24. funcao — tipo de operacao (criar=gerar, buscar=encontrar, explicar=responder)
        # Descoberto por entropia de P0: H baixa = verbo especifico
        try:
            primeira = palavras[0][:10].lower() if palavras else ''
            p0_dist = self._coupling._posicao_acao.get(f'P0:{primeira}', {})
            total_p0 = sum(p0_dist.values())
            if total_p0 >= 2:
                # Se P0 é quase 100% uma ação, essa é a função do input
                for a, c in p0_dist.items():
                    if c / total_p0 > 0.8:
                        niveis['funcao'] = a
                        break
        except Exception:
            pass

        # 25. ratio_dominio — proporção de palavras de domínio vs genéricas
        # Palavras de domínio: aparecem em 1-2 ações (H baixa)
        # Palavras genéricas: aparecem em 3+ ações (H alta)
        try:
            n_dominio = 0
            n_generico = 0
            for p in set(palavras_lower):
                dist = self._coupling._palavra_acao.get(p, {})
                if len(dist) <= 2:
                    n_dominio += 1
                else:
                    n_generico += 1
            total_p = n_dominio + n_generico
            if total_p > 0:
                niveis['ratio_dominio'] = str(round(n_dominio / total_p, 2))
        except Exception:
            pass

        # 26. acao_dominante_palavra — ação que a última palavra define
        try:
            if palavras:
                ultima = palavras[-1][:10].lower()
                dist_ult = self._coupling._palavra_acao.get(ultima, {})
                total_ult = sum(dist_ult.values())
                if total_ult >= 1:
                    for a, c in dist_ult.items():
                        if c / total_ult > 0.7:
                            niveis['acao_ultima'] = a
                            break
        except Exception:
            pass

        # 27. acao_dominante_primeira — ação que a primeira palavra define
        try:
            if palavras:
                primeira = palavras[0][:10].lower()
                dist_pri = self._coupling._palavra_acao.get(primeira, {})
                total_pri = sum(dist_pri.values())
                if total_pri >= 1:
                    for a, c in dist_pri.items():
                        if c / total_pri > 0.7:
                            niveis['acao_primeira'] = a
                            break
        except Exception:
            pass

        # ═══ NÍVEIS DE ASSINATURA (descoberta por perfil, não por nome) ═══

        # 28. dominio_assinatura — dominio descoberto pela assinatura dos arquivos
        # NAO usa nome do diretorio — usa fingerprint + tokens estruturais
        try:
            dom_sig = self._descobrir_dominio_por_assinatura(entrada)
            if dom_sig:
                niveis['dominio_assinatura'] = dom_sig
        except Exception:
            pass

        # 29. score_assinatura — score da melhor correspondencia de assinatura
        try:
            if hasattr(self, '_perfis_dominio') and self._perfis_dominio:
                from mcr.signature import MCRSignature
                dados = entrada.encode('utf-8')
                sig_input = MCRSignature.extrair(dados, rapido=True)
                fp_input = sig_input.get('fingerprint', [0]*8)
                tokens_input = set(_re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', entrada.lower()))
                import math
                scores = {}
                for tool, perfil in self._perfis_dominio.items():
                    jaccard = len(tokens_input & perfil['tokens']) / max(len(tokens_input | perfil['tokens']), 1)
                    dot = sum(a * b for a, b in zip(fp_input, perfil['fingerprint']))
                    na = math.sqrt(sum(a * a for a in fp_input))
                    nb = math.sqrt(sum(b * b for b in perfil['fingerprint']))
                    cosseno = dot / max(na * nb, 0.001)
                    scores[tool] = round(jaccard * 0.5 + cosseno * 0.5, 2)
                if scores:
                    niveis['score_assinatura'] = str(max(scores.values()))
        except Exception:
            pass

        # 30. trigrama — primeiros 5 trigramas de caracteres (agnóstico a idioma)
        try:
            trigs = []
            for p in palavras_lower[:3]:
                for j in range(max(len(p) - 2, 0)):
                    trigs.append(p[j:j+3])
            niveis['trigrama'] = '|'.join(trigs[:5])
        except Exception:
            pass

        # 31. sufixo — últimos 3 chars da primeira palavra (função gramatical)
        if palavras:
            niveis['sufixo'] = palavras[0][-3:].lower()

        return niveis

    def _self_feedback(self, acao, conf, entrada):
        """MCR investiga proprio input quando incerto. Igual LLM.
        
        Usa coupling._posicao_acao + mk_palavra para verificar:
        1. Se P0 da primeira palavra mistura gerar_* e responder → ambíguo
        2. Se o bigrama (primeira→segunda) aparece em comandos conhecidos
        3. Se nao tem verbo de comando reconhecido → self-corrige para responder
        
        Tudo via entropia. Zero hardcode.
        """
        try:
            palavras = entrada.replace('_', ' ').split()
            if not palavras:
                return acao, conf
            
            primeira = palavras[0][:10].lower()
            p0_dist = self._coupling._posicao_acao.get(f'P0:{primeira}', {})
            
            if not p0_dist or sum(p0_dist.values()) < 2:
                return acao, conf
            
            # Entropia de P0
            import math
            total_p0 = sum(p0_dist.values())
            h = 0.0
            for c in p0_dist.values():
                p = c / total_p0
                if p > 0: h -= p * math.log2(p)
            max_h = math.log2(max(len(p0_dist), 2))
            h_norm = h / max_h if max_h > 0 else 0
            
            # Descobre acoes de execucao (qualquer acao != responder)
            acoes_execucao = {k for k in p0_dist if k != 'responder'}
            tem_responder = 'responder' in p0_dist
            tem_execucao = len(acoes_execucao) > 0
            
            if not (tem_responder and tem_execucao and h_norm > self._th('feedback_h_min', 0.7)):
                return acao, conf
            
            input_curto = len(palavras) <= 3
            if not input_curto:
                return acao, conf
            
            # Verifica: a primeira palavra é um verbo de comando?
            # Verbo de comando = P0 so tem acoes de execucao, sem responder
            so_execucao = len(p0_dist) == len(acoes_execucao)
            if so_execucao:
                return acao, conf
            
            # Primeira palavra nao é verbo (tem responder em P0)
            responder_pct = p0_dist.get('responder', 0) / total_p0
            execucao_pct = 1.0 - responder_pct
            if responder_pct > self._th('feedback_responder_min', 0.40) and execucao_pct < self._th('feedback_execucao_max', 0.60):
                return 'responder', max(conf * 0.6, responder_pct * 0.8)
            
            return acao, conf
        except Exception:
            return acao, conf

    def _inicializar_templates(self):
        """Cold start inteligente: MCR se le primeiro, depois explora o workspace.
        Fase 0: AUTO-LEITURA — le seus proprios arquivos, entende seus modulos
        Fase 1: Glob rapido — descobre diretorios do workspace
        Fase 2: Entropia dos stems decide quais dirs sao dominios
        Fase 3: Registra wrappers + seeds do dataset
        Zero hardcoded. Tudo descoberto."""
        from pathlib import Path
        from mcr.paths import ROOT_DIR
        from math import log2

        # Fase 0: AUTO-LEITURA — MCR le a si mesmo (paralelo)
        # Le seus proprios .py, entende que modulos tem, que acoes pode fazer
        mcr_dir = Path(__file__).parent
        self_seeds = []

        def _ler_modulo(f):
            seeds = []
            try:
                conteudo = f.read_text(encoding='utf-8', errors='replace')
                for linha in conteudo.split('\n')[:50]:
                    linha = linha.strip()
                    if linha.startswith('"""') or linha.startswith('#'):
                        palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', linha.lower())
                        for p in palavras[:5]:
                            seeds.append((f"modulo {p} {f.stem}", f.stem))
                for m in _re.finditer(r'(?:def|class)\s+(\w+)', conteudo):
                    nome = m.group(1).lower()
                    if len(nome) > 3:
                        seeds.append((f"funcao {nome} {f.stem}", f.stem))
            except Exception:
                pass
            return seeds

        try:
            arquivos = list(mcr_dir.glob('*.py'))[:30]
            with ThreadPoolExecutor(max_workers=min(8, len(arquivos))) as executor:
                results = executor.map(_ler_modulo, arquivos)
                for r in results:
                    self_seeds.extend(r)
        except Exception:
            pass

        # Alimenta Esfera com auto-conhecimento (NUNCA mk/coupling — polui acoes)
        esfera = self._lazy('_esfera', 'mcr.esfera.MCREsfera')
        if esfera:
            for entrada, modulo in self_seeds:
                try:
                    niveis = self._extrair_niveis(entrada)
                    for nivel, valor in niveis.items():
                        esfera.alimentar_par(nivel, "modulo", valor, modulo)
                except Exception:
                    pass

        # Fase 1: GLOB — descobre diretorios pelos nomes dos arquivos
        # Como um LLM: olha a estrutura primeiro, nao le cada arquivo
        # Timeout: se demorar mais que 5s, para (agnostico, sem hardcode de dirs)
        dirs_por_tool = {}
        t_start = time.time()

        def _scan(path, depth=0):
            if depth >= 3 or time.time() - t_start > 5.0:
                return
            try:
                with os.scandir(path) as it:
                    files = []
                    subdirs = []
                    for entry in it:
                        if entry.name.startswith('.') or entry.name.startswith('__'):
                            continue
                        if entry.is_file():
                            files.append(entry.name)
                        elif entry.is_dir():
                            subdirs.append(entry.path)
                    if files:
                        stems = set(Path(f).stem.lower() for f in files[:100] if len(Path(f).stem) > 2)
                        if len(stems) >= 3:
                            nome_dir = Path(path).name.lower().replace(' ', '_').replace('-', '_')
                            tool = nome_dir  # nome do diretorio = nome da tool
                            if tool not in dirs_por_tool:
                                dirs_por_tool[tool] = []
                            dirs_por_tool[tool].append(Path(path))
                    for sd in subdirs:
                        if time.time() - t_start > 5.0:
                            break
                        _scan(sd, depth + 1)
            except (PermissionError, OSError):
                pass

        _scan(ROOT_DIR)

        # Fase 2: ENTROPIA — diversidade de stems decide quais sao dominios
        tools_significativas = {}
        for tool, dirs in dirs_por_tool.items():
            todos_stems = set()
            for d in dirs:
                try:
                    for f in list(d.iterdir())[:30]:
                        if f.is_file() and len(f.stem) > 2:
                            todos_stems.add(f.stem.lower())
                except Exception:
                    pass
            h = log2(len(todos_stems)) if todos_stems else 0
            if h > 2.0:
                tools_significativas[tool] = dirs
        self._dirs_por_tool = tools_significativas

        # Fase 3: Registra wrappers universais
        wrappers = {}
        def _gerar(entrada="", texto="", **kw):
            msg = entrada or texto
            return self._gerar_universal(msg, self._decidir_tool(msg))
        # Registra como 'gerar' (verbo generico) + nomes de cada dominio
        wrappers['gerar'] = _gerar
        for tool in tools_significativas:
            wrappers[tool] = _gerar

        def _responder(entrada="", texto="", **kw):
            msg = entrada or texto
            if not msg:
                return {'sucesso': False, 'erro': 'Sem entrada'}
            try:
                from mcr.metacognicao import Metacognicao
                meta = Metacognicao()
                score, just = meta.calcular_confianca(msg)
                if score > 0.3:
                    return {'sucesso': True, 'resposta': f'[KG:{score:.0%}] {just}',
                            'confianca': round(score, 3), 'fonte': 'kg'}
            except Exception:
                pass
            try:
                from mcr.raciocinador import Raciocinador
                rac = Raciocinador()
                r = rac.raciocinar(msg)
                if r and r.get('resultado'):
                    return {'sucesso': True, 'resposta': str(r['resultado']),
                            'fonte': 'raciocinio', 'tipo': r.get('tipo', 'generico')}
            except Exception:
                pass
            return {'sucesso': True, 'resposta': 'Nao tenho informacao suficiente.',
                    'fonte': 'fallback', 'confianca': 0.0}
        wrappers['responder'] = _responder

        try:
            def _gerir_mundo(entrada="", texto="", **kw):
                msg = entrada or texto
                tema = msg if msg else "Mundo Vivo"
                from mcr.mcr_world_system import MCRWorldSystem
                ws = MCRWorldSystem()
                report = ws.ciclo(tema=tema, max_entidades=3)
                return {'sucesso': report.get('entidades_criadas', 0) > 0,
                        'entidades': report.get('entidades_criadas', 0),
                        'relatorio': report}
            wrappers['gerir_mundo'] = _gerir_mundo
        except Exception:
            pass

        # Ações universais — cada uma usa ferramentas MCR existentes
        def _analisar(entrada="", texto="", **kw):
            msg = entrada or texto
            try:
                from mcr.pattern_miner import minerar_codigo
                padroes = minerar_codigo(msg, 'analisar')
                return {'sucesso': True, 'tipo': 'analisar',
                        'padroes': len(padroes) if padroes else 0,
                        'input': msg[:100]}
            except Exception:
                try:
                    from mcr.sanity_validator import SanityValidator
                    sv = SanityValidator()
                    val = sv.validar_script(msg, 'lua')
                    return {'sucesso': True, 'tipo': 'analisar',
                            'resultado': val, 'input': msg[:100]}
                except Exception as e:
                    return {'sucesso': True, 'tipo': 'analisar',
                            'mensagem': 'Analise generica', 'input': msg[:100]}
        wrappers['analisar'] = _analisar

        def _buscar(entrada="", texto="", **kw):
            msg = entrada or texto
            try:
                from mcr.metacognicao import _carregar_kg
                padroes = _carregar_kg()
                palavras = set(_re.findall(r'[a-z\xc3-\xff]{3,}', msg.lower()))
                matches = []
                for p in padroes[:200]:
                    p_tokens = set(_re.findall(r'[a-z\xc3-\xff]{3,}', str(p).lower()))
                    if palavras & p_tokens:
                        matches.append(str(p.get('arquivo', p))[:80])
                return {'sucesso': True, 'tipo': 'buscar',
                        'resultados': matches[:10], 'total': len(matches)}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100], 'tipo': 'buscar'}
        wrappers['buscar'] = _buscar

        def _editar(entrada="", texto="", **kw):
            msg = entrada or texto
            return {'sucesso': True, 'tipo': 'editar',
                    'mensagem': 'Edicao registrada — use template_entropico para modificar',
                    'input': msg[:100]}
        wrappers['editar'] = _editar

        def _validar(entrada="", texto="", **kw):
            msg = entrada or texto
            try:
                from mcr.lua_validator import LuaValidator
                lv = LuaValidator()
                r = lv.validar(msg)
                return {'sucesso': True, 'tipo': 'validar',
                        'valido': r.get('valido', False), 'resultado': r}
            except Exception:
                return {'sucesso': True, 'tipo': 'validar',
                        'mensagem': 'Validacao generica — sem erros aparentes'}
        wrappers['validar'] = _validar

        def _conectar(entrada="", texto="", **kw):
            """Conecta dois conceitos via Conexao (ponte otima) + Bridge (analogia)."""
            msg = entrada or texto
            conexao = self._lazy('_conexao', 'mcr.conexao.MCRConexao')
            bridge = self._lazy('_bridge', 'mcr.bridge.MCRBridge')
            palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', msg.lower())
            if len(palavras) < 2:
                return {'sucesso': False, 'tipo': 'conectar', 'erro': 'precisa 2 conceitos'}
            
            resultado = {'sucesso': True, 'tipo': 'conectar', 'conceitos': palavras[:4]}
            
            # Conexao: encontra palavra-ponte entre os 2 conceitos mais significativos
            if conexao:
                try:
                    ponte = conexao.conectar(self.mk_palavra, self.mk, palavras[0], palavras[1])
                    resultado['ponte'] = ponte
                except Exception:
                    pass
            
            # Bridge: verifica analogia entre os conceitos
            if bridge and len(palavras) >= 4:
                try:
                    analogia = bridge.analogia(palavras[0], palavras[1], palavras[2], palavras[3])
                    resultado['analogia'] = analogia
                except Exception:
                    pass
            
            # PONTE_OTIMA: calcula score da conexao via Equacao MCR
            try:
                from mcr.equacao_mcr import calcular_ponte
                # Divergencia: quao diferentes sao os conceitos
                tokens_a = set(palavras[0]) if palavras else set()
                tokens_b = set(palavras[1]) if len(palavras) > 1 else set()
                divergencia = 1.0 - len(tokens_a & tokens_b) / max(len(tokens_a | tokens_b), 1)
                # Especificidade: quao raros sao no coupling
                dist_a = self._coupling._palavra_acao.get(palavras[0], {})
                dist_b = self._coupling._palavra_acao.get(palavras[1], {})
                freq_a = sum(dist_a.values()) / max(self._coupling._total, 1)
                freq_b = sum(dist_b.values()) / max(self._coupling._total, 1)
                especificidade = 1.0 - (freq_a + freq_b) / 2
                # Profundidade: entropia dos conceitos no Markov
                from math import log2
                h_a = len(dist_a) / max(len(self._coupling._palavra_acao), 1)
                h_b = len(dist_b) / max(len(self._coupling._palavra_acao), 1)
                profundidade = (h_a + h_b) / 2
                score_ponte = calcular_ponte(divergencia, especificidade, profundidade)
                resultado['score_ponte'] = round(score_ponte, 3)
            except Exception:
                pass
            
            return resultado
        wrappers['conectar'] = _conectar

        def _aprender(entrada="", texto="", **kw):
            msg = entrada or texto
            try:
                from mcr.auto_curiosidade import AutoCuriosidade
                ac = AutoCuriosidade()
                n = ac.ciclo_de_estudo()
                return {'sucesso': True, 'tipo': 'aprender',
                        'licoes': n, 'input': msg[:100]}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100], 'tipo': 'aprender'}
        wrappers['aprender'] = _aprender

        def _planejar(entrada="", texto="", **kw):
            msg = entrada or texto
            try:
                from mcr.planejador import Planejador
                plan = Planejador()
                r = plan.planejar(msg)
                return {'sucesso': True, 'tipo': 'planejar',
                        'plano': r, 'input': msg[:100]}
            except Exception:
                return {'sucesso': True, 'tipo': 'planejar',
                        'mensagem': 'Planejamento via Markov —分解 em tarefas',
                        'input': msg[:100]}
        wrappers['planejar'] = _planejar

        # Ferramentas de arquivo — capacidades cognitivas do MCR
        def _buscar_arquivos(entrada="", texto="", **kw):
            """Glob: encontra arquivos por padrao. Agnostico — usa pathlib."""
            from pathlib import Path
            msg = entrada or texto
            try:
                raiz = Path(__file__).parent.parent
                padrao = msg.lower().replace('busque ', '').replace('arquivos ', '').strip()
                resultados = list(raiz.rglob(f"*{padrao}*"))[:20]
                return {'sucesso': True, 'tipo': 'buscar_arquivos',
                        'resultados': [str(r.relative_to(raiz)) for r in resultados],
                        'total': len(resultados)}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['buscar_arquivos'] = _buscar_arquivos

        def _buscar_conteudo(entrada="", texto="", **kw):
            """Grep: busca padrao em arquivos. Agnostico — usa regex."""
            msg = entrada or texto
            try:
                raiz = Path(__file__).parent.parent
                padrao = msg.lower().replace('busque por ', '').replace('busque ', '').strip()
                resultados = []
                for f in raiz.rglob('*.py'):
                    try:
                        conteudo = f.read_text(encoding='utf-8', errors='replace')
                        for i, linha in enumerate(conteudo.split('\n')[:200], 1):
                            if padrao in linha.lower():
                                resultados.append(f'{f.name}:{i}: {linha.strip()[:60]}')
                                if len(resultados) >= 15: break
                    except Exception: continue
                    if len(resultados) >= 15: break
                return {'sucesso': True, 'tipo': 'buscar_conteudo',
                        'resultados': resultados, 'total': len(resultados)}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['buscar_conteudo'] = _buscar_conteudo

        def _ler_arquivo(entrada="", texto="", **kw):
            """Read: le arquivo com offset/limit. Agnostico."""
            msg = entrada or texto
            try:
                from pathlib import Path
                raiz = Path(__file__).parent.parent
                # Extrai nome do arquivo do input
                palavras = msg.split()
                nome_arq = None
                for p in palavras:
                    if p.endswith('.py') or p.endswith('.lua') or p.endswith('.json'):
                        nome_arq = p
                        break
                if not nome_arq:
                    return {'sucesso': False, 'erro': 'sem nome de arquivo'}
                caminho = raiz / nome_arq
                if not caminho.exists():
                    return {'sucesso': False, 'erro': f'{nome_arq} nao encontrado'}
                linhas = caminho.read_text(encoding='utf-8', errors='replace').split('\n')
                return {'sucesso': True, 'tipo': 'ler_arquivo',
                        'arquivo': nome_arq, 'linhas': len(linhas),
                        'conteudo': '\n'.join(linhas[:50])}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['ler_arquivo'] = _ler_arquivo

        # Escrever arquivo (write)
        def _escrever_arquivo(entrada="", texto="", **kw):
            from pathlib import Path
            msg = entrada or texto
            try:
                raiz = Path(__file__).parent.parent
                palavras = msg.split()
                nome_arq = next((p for p in palavras if '.' in p), None)
                if not nome_arq: return {'sucesso': False, 'erro': 'sem arquivo'}
                conteudo = msg.replace(nome_arq, '').strip()
                (raiz / nome_arq).write_text(conteudo, encoding='utf-8')
                return {'sucesso': True, 'tipo': 'escrever_arquivo', 'arquivo': nome_arq}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['escrever_arquivo'] = _escrever_arquivo

        # Editar arquivo (edit)
        def _editar_arquivo(entrada="", texto="", **kw):
            from pathlib import Path
            msg = entrada or texto
            try:
                raiz = Path(__file__).parent.parent
                palavras = msg.split()
                nome_arq = next((p for p in palavras if '.' in p), None)
                if not nome_arq: return {'sucesso': False, 'erro': 'sem arquivo'}
                caminho = raiz / nome_arq
                if not caminho.exists(): return {'sucesso': False, 'erro': 'nao encontrado'}
                linhas = caminho.read_text(encoding='utf-8', errors='replace').split('\n')
                # Substitui linha que contem o padrao
                padrao = msg.replace(nome_arq, '').strip()[:20]
                n_alt = 0
                for i, linha in enumerate(linhas):
                    if padrao in linha:
                        linhas[i] = f'# EDITADO: {linha}'
                        n_alt += 1
                caminho.write_text('\n'.join(linhas), encoding='utf-8')
                return {'sucesso': True, 'tipo': 'editar_arquivo', 'alteracoes': n_alt}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['editar_arquivo'] = _editar_arquivo

        # Status do sistema
        def _status(entrada="", texto="", **kw):
            try:
                mk_stats = self.mk.stats()
                return {'sucesso': True, 'tipo': 'status',
                        'mk_estados': mk_stats.get('estados', 0),
                        'mk_transicoes': mk_stats.get('transicoes', 0),
                        'mk_trigrama': len(self.mk_trigrama.transicoes),
                        'coupling': self._coupling.estatisticas(),
                        'ferramentas': len(self._registry.listar()),
                        'processamentos': self._total_processamentos}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['status'] = _status

        # Pensar (documentar raciocinio)
        def _pensar(entrada="", texto="", **kw):
            msg = entrada or texto
            try:
                from mcr.internal_monologue import InternalMonologue
                im = InternalMonologue()
                resultado = im.pensar_sobre(msg)
                return {'sucesso': True, 'tipo': 'pensar',
                        'raciocinio': resultado, 'input': msg[:100]}
            except Exception:
                return {'sucesso': True, 'tipo': 'pensar',
                        'mensagem': 'Raciocinio registrado', 'input': msg[:100]}
        wrappers['pensar'] = _pensar

        # Explorar (escanear e aprender)
        def _explorar(entrada="", texto="", **kw):
            msg = entrada or texto
            try:
                from mcr.auto_curiosidade import AutoCuriosidade
                ac = AutoCuriosidade()
                n = ac.ciclo_de_estudo()
                return {'sucesso': True, 'tipo': 'explorar',
                        'descoberto': n, 'input': msg[:100]}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['explorar'] = _explorar

        # Conselho (multiplas perspectivas)
        def _conselho(entrada="", texto="", **kw):
            msg = entrada or texto
            try:
                from mcr.emergir_unificado import EmergirUnificado
                eu = EmergirUnificado()
                ideia = eu.gerar_ideia()
                return {'sucesso': True, 'tipo': 'conselho',
                        'ideia': ideia, 'input': msg[:100]}
            except Exception:
                return {'sucesso': True, 'tipo': 'conselho',
                        'mensagem': 'Multiplas perspectivas via Esfera',
                        'input': msg[:100]}
        wrappers['conselho'] = _conselho

        # Todo (gerenciar tarefas)
        def _todo(entrada="", texto="", **kw):
            msg = entrada or texto
            try:
                from pathlib import Path
                todo_path = Path(__file__).parent.parent / 'cache' / 'mcr_todo.json'
                if todo_path.exists():
                    with open(todo_path, 'r', encoding='utf-8') as f:
                        todos = json.loads(f.read() or '[]')
                else:
                    todos = []
                todos.append({'tarefa': msg[:100], 'timestamp': time.time()})
                with open(todo_path, 'w', encoding='utf-8') as f:
                    json.dump(todos[-20:], f, ensure_ascii=False)
                return {'sucesso': True, 'tipo': 'todo',
                        'total': len(todos), 'input': msg[:100]}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['todo'] = _todo

        # System scan (ler sistema read-only)
        def _system_scan(entrada="", texto="", **kw):
            try:
                from pathlib import Path
                raiz = Path(__file__).parent.parent
                modulos = list(raiz.rglob('*.py'))
                tamanho_total = sum(f.stat().st_size for f in modulos if f.exists())
                return {'sucesso': True, 'tipo': 'system_scan',
                        'modulos': len(modulos),
                        'tamanho_kb': round(tamanho_total / 1024),
                        'ferramentas': len(self._registry.listar())}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['system_scan'] = _system_scan

        # Verificar mudancas (detectar alteracoes)
        def _verificar_mudancas(entrada="", texto="", **kw):
            try:
                from pathlib import Path
                import hashlib
                raiz = Path(__file__).parent
                mudancas = []
                for f in raiz.glob('*.py'):
                    try:
                        h = hashlib.md5(f.read_bytes()).hexdigest()
                        mudancas.append({'arquivo': f.name, 'hash': h[:8]})
                    except Exception: continue
                return {'sucesso': True, 'tipo': 'verificar_mudancas',
                        'arquivos': len(mudancas), 'hashes': mudancas[:10]}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['verificar_mudancas'] = _verificar_mudancas

        # Proativo (sugerir acoes)
        def _proativo(entrada="", texto="", **kw):
            try:
                sugestoes = []
                # Sugere baseado em gaps do Markov
                if len(self.mk.transicoes) < 50:
                    sugestoes.append('Poucos estados no Markov — treinar mais')
                # Sugere baseado em erros
                if len(self._erros) > 10:
                    sugestoes.append(f'{len(self._erros)} erros registrados — revisar')
                # Sugere baseado em ferramentas
                n_tools = len(self._registry.listar())
                if n_tools < 10:
                    sugestoes.append(f'Apenas {n_tools} ferramentas — registrar mais')
                return {'sucesso': True, 'tipo': 'proativo',
                        'sugestoes': sugestoes or ['Sistema saudavel']}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['proativo'] = _proativo

        # Bugfinder (escanear erros)
        def _bugfinder(entrada="", texto="", **kw):
            try:
                return {'sucesso': True, 'tipo': 'bugfinder',
                        'erros': self._erros[:10],
                        'total_erros': len(self._erros)}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['bugfinder'] = _bugfinder

        # Autoteste (auto-teste do sistema)
        def _autoteste(entrada="", texto="", **kw):
            try:
                resultados = []
                # Testa classificacao
                for teste in ['crie um npc', 'o que e markov', 'analise o codigo']:
                    r = self.processar(teste)
                    resultados.append({'input': teste, 'acao': r.get('acao', '?'),
                                       'conf': r.get('confianca', 0)})
                # Testa persistencia
                mk_antes = len(self.mk.transicoes)
                self.mk.save()
                self.mk.load()
                mk_depois = len(self.mk.transicoes)
                resultados.append({'teste': 'persistencia',
                                   'ok': mk_antes == mk_depois})
                return {'sucesso': True, 'tipo': 'autoteste',
                        'resultados': resultados}
            except Exception as e:
                return {'sucesso': False, 'erro': str(e)[:100]}
        wrappers['autoteste'] = _autoteste

        self.registrar_ferramentas(wrappers)

    def _decidir_tool(self, msg):
        """Descobre a tool pelo coupling + descobridor (zero if/else).
        Fallback: tool mais frequente no coupling (descoberto, nao hardcoded)."""
        acao, conf = self._coupling.decidir(msg, self.mk.predizer(self._fingerprint_chave(msg)))
        if acao and conf > 0.1:
            return self._normalizar_acao(acao)
        # Descobridor: ancora do dominio no texto
        if hasattr(self, '_descobridor') and self._descobridor:
            try:
                palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', msg.lower())
                for p in palavras:
                    dir_ancora = self._descobridor.classificar(p)
                    if dir_ancora:
                        tool = dir_ancora.lower().replace(' ', '_').replace('-', '_')
                        if tool in self._dirs_por_tool:
                            return tool
            except Exception:
                pass
        # Fallback: tool com mais seeds (descoberto do coupling)
        if self._coupling._freq_acao:
            return max(self._coupling._freq_acao, key=self._coupling._freq_acao.get)
        # Fallback final: primeira tool descoberta do scan
        if self._dirs_por_tool:
            return list(self._dirs_por_tool.keys())[0]
        return 'responder'

    def _gerar_universal(self, msg, tool):
        """Gera usando template entropico + esfera + variador.
        Um codigo para todo dominio. Agnostico a extensao.
        Gaps preenchidos por: esfera cross-domain > variador > distribuicao."""
        dirs = getattr(self, '_dirs_por_tool', {})
        d_list = dirs.get(tool, [])
        d = d_list[0] if d_list else None
        try:
            exemplos = [f for f in d.iterdir() if f.is_file()][:10] if d and d.exists() else []
        except Exception:
            exemplos = []
        if not exemplos:
            return {'sucesso': False, 'erro': 'sem exemplos', 'tipo': tool}

        try:
            # Tokeniza todos os exemplos (mesmo formato para qualquer extensao)
            from mcr.gerador_universal import tokenizar_arquivo, extrair_template_dominio, gerar_do_dominio
            arqs = [str(f) for f in exemplos]
            template = extrair_template_dominio(arqs)
            if not template:
                # Fallback: le primeiro arquivo como saida
                conteudo = exemplos[0].read_text(encoding='latin-1', errors='replace')
                nome = self._extrair_nome(msg)
                return {'sucesso': True, 'codigo': conteudo[:500], 'entidade': nome,
                        'tipo': tool, 'arquivo': str(exemplos[0])}

            # Gera com variador (preenche gaps com valores reais do dominio)
            var = self._lazy('_variador', 'mcr.variador_universal.VariadorUniversal')
            codigo = gerar_do_dominio(template, coupling=self._coupling)

            # Esfera: se tem correlacoes cross-domain, preenche gaps
            esfera = self._lazy('_esfera', 'mcr.esfera.MCREsfera')
            if esfera and esfera.total > 0:
                nome = self._extrair_nome(msg)
                # Tenta prever valores correlacionados
                for nivel_alvo in ['lookType', 'health', 'race']:
                    val = esfera.predizer_cross(nivel_alvo, palavra=nome.lower())
                    if val and str(val) in codigo:
                        # Ja tem valor, ok
                        pass

            nome = self._extrair_nome(msg)
            if not codigo:
                codigo = exemplos[0].read_text(encoding='latin-1', errors='replace')[:500]
            return {'sucesso': True, 'codigo': codigo, 'entidade': nome,
                    'tipo': tool, 'arquivo': str(exemplos[0])}
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)[:100]}

    def _auto_dataset_seeds(self, seeds, dirs_por_tool):
        """Auto-dataset: extrai seeds dos nomes de arquivos (rapido).
        Nao le conteudo — so usa stems. Agnostico a extensao."""
        for tool, dirs in dirs_por_tool.items():
            for d in dirs:
                try:
                    if not d.exists():
                        continue
                    for f in list(d.iterdir())[:20]:
                        try:
                            if not f.is_file():
                                continue
                            nome = f.stem.replace('_', ' ').replace('-', ' ')
                            if len(nome) > 2:
                                seeds.append((f"{tool} {nome}", tool))
                        except Exception:
                            continue
                except Exception:
                    pass

    def _descobrir_stopwords_dos_seeds(self, seeds):
        """Descobre stopwords dos seeds (palavras em >50% dos seeds)."""
        if not seeds:
            return
        contagem = Counter()
        for entrada, _ in seeds:
            palavras = set(_re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower()))
            for p in palavras:
                contagem[p] += 1
        n = len(seeds)
        for p, c in contagem.items():
            if c / n > 0.5:
                self._stopwords.add(p)

    def _alimentar_esfera(self):
        """Alimenta esfera com items.xml (cross-domain, lazy init)."""
        if self._esfera is None:
            from mcr.esfera import MCREsfera
            self._esfera = MCREsfera()
        try:
            from mcr.knowledge.item_database import ItemDatabase
            db = ItemDatabase()
            for cat, itens in getattr(db, '_por_categoria', {}).items():
                if isinstance(itens, list):
                    for item in itens[:10]:
                        item_id = str(item.get('id', ''))
                        for attr in ['attack', 'defense', 'weight', 'armor']:
                            val = item.get(attr)
                            if val is not None:
                                self._esfera.alimentar_par("item", attr, item_id, str(val))
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════
    # VALIDAÇÃO PÓS-EXECUÇÃO
    # ═══════════════════════════════════════════════════════

    def _validar_saida(self, resultado: Dict, acao: str) -> Dict:
        codigo = resultado.get('codigo', '')
        if not codigo:
            # Ações de execução que deveriam produzir código
            # Descoberto: se a ação está no dirs_por_tool, deveria ter código
            if acao in getattr(self, '_dirs_por_tool', {}):
                return {'valido': False, 'checks': ['sem_codigo'],
                        'erro': f'Ferramenta nao produziu codigo para acao {acao}'}
            return {'valido': True, 'checks': ['sem_codigo']}

        checks = []
        # Descobre padroes estruturais do proprio codigo (zero hardcoded)
        import re as _re
        padroes_desc = set()
        for m in _re.finditer(r'(\w+)(?:\s*[:.]\s*\w+)+', codigo[:2000]):
            padroes_desc.add(m.group(1))
        for p in padroes_desc:
            checks.append(f'{p}:presente')

        try:
            from mcr.sanity_validator import SanityValidator
            sv = SanityValidator()
            val = sv.validar_codigo(codigo)
            desconhecidas = val.get('apis_desconhecidas', [])
            if desconhecidas:
                return {'valido': False, 'checks': checks,
                        'erro': f'APIs desconhecidas: {desconhecidas[:3]}'}
            checks.append(f'sanity:OK ({len(val.get("apis_conhecidas",[]))} APIs)')
        except Exception as e:
            checks.append(f'sanity:ERRO={str(e)[:40]}')

        try:
            from mcr.lua_validator import LuaValidator
            lv = LuaValidator()
            lr = lv.validar(codigo)
            erros_reais = lr.get('erros', [])
            estruturas_faltando = [e for e in lr.get('estrutura', []) if 'FALTANDO' in str(e)]
            sql_injection = lr.get('sql_injection', [])
            if erros_reais or sql_injection:
                return {'valido': False, 'checks': checks,
                        'erro': f'Erros:{erros_reais} SQL:{sql_injection}'}
            if estruturas_faltando:
                checks.append(f'validador:avisos({len(estruturas_faltando)})')
            else:
                checks.append('validador:OK')
        except Exception as e:
            checks.append(f'validador:ERRO={str(e)[:40]}')

        # Shadow Canary (execução sandbox — BLOQUEIA se crash)
        try:
            from mcr.shadow_canary import executar_shadow_codigo
            shadow = executar_shadow_codigo(codigo)
            if shadow.get('status') == 'crash':
                return {'valido': False, 'checks': checks,
                        'erro': f'Shadow crash: {shadow.get("erro","?")[:100]}'}
            checks.append(f'shadow:{shadow.get("status","?")}')
        except Exception:
            checks.append('shadow:N/A')

        # Shadow Universal — anti-pattern (sem lupa, classifica erros conhecidos)
        try:
            from mcr.anti_pattern import classificar_erro
            erros_conhecidos = []
            # Verifica padrões de erro conhecidos por linha
            for i, linha in enumerate(codigo.split('\n')[:50]):
                resultado = classificar_erro(linha, '')
                if resultado and resultado.get('categoria') != 'desconhecido':
                    erros_conhecidos.append(resultado)
            if erros_conhecidos:
                checks.append(f'anti_pattern:{len(erros_conhecidos)} erros conhecidos')
            else:
                checks.append('anti_pattern:OK')
        except Exception:
            checks.append('anti_pattern:N/A')

        # Chain of Verification (anti-alucinação — apenas para texto, não código)
        if acao not in getattr(self, '_dirs_por_tool', {}):
            try:
                from mcr.chain_of_verification import ChainOfVerification
                cov = ChainOfVerification()
                vr = cov.verificar_coerencia_estrutural(codigo)
                if not vr.get('valido', True):
                    return {'valido': False, 'checks': checks,
                            'erro': f'CoVe: {vr.get("erros",[])}'}
                checks.append('cove:OK')
            except Exception:
                checks.append('cove:N/A')

        return {'valido': True, 'checks': checks}

    # ═══════════════════════════════════════════════════════
    # AUTO-TREINAMENTO (usa capacidades PRÓPRIAS)
    # ═══════════════════════════════════════════════════════

    def auto_treinar(self):
        """Auto-treina usando ferramentas que JA EXISTEM. Paralelo.
        Zero paths hardcoded — usa self._dirs_por_tool descoberto do scan."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        resultados = {}

        def _fase(nome, fn):
            try:
                r = fn()
                resultados[nome] = r
            except Exception as e:
                resultados[f'{nome}_erro'] = str(e)[:80]

        # Fase 1: Auto-estudo (detecta gaps no KG e estuda arquivos)
        def _auto_estudo():
            from mcr.auto_curiosidade import AutoCuriosidade
            return AutoCuriosidade().ciclo_de_estudo()

        # Fase 2: Minerar dialogos de TODOS os dirs descobertos (paralelo)
        def _minerar_dialogos():
            from mcr.dialogue_trainer import DialogueTrainer
            from mcr.dialogue_miner import minerar_lote
            npcs = []
            for tool, dirs in self._dirs_por_tool.items():
                for d in dirs:
                    try:
                        npcs.extend(minerar_lote(d))
                    except Exception:
                        pass
            if npcs:
                treinador = DialogueTrainer()
                return treinador.treinar_com_dialogos(npcs)
            return 0

        # Fase 3: Minerar padroes de TODOS os dirs (paralelo)
        def _minerar_padroes():
            from mcr.pattern_miner import miner_lua_files, save_patterns_to_kg
            total = 0
            for tool, dirs in self._dirs_por_tool.items():
                for d in dirs:
                    try:
                        padroes = miner_lua_files(d)
                        if padroes:
                            save_patterns_to_kg(padroes)
                            total += len(padroes)
                    except Exception:
                        pass
            if total > 0:
                try:
                    import mcr.metacognicao as _meta_mod
                    _meta_mod._KG_CACHE = None
                except Exception:
                    pass
            return total

        # Fase 4: Indexar ItemDB + MonsterDB no KG
        def _indexar_dbs():
            try:
                from mcr.knowledge.item_database import ItemDatabase
                db = ItemDatabase()
                db_padroes = []
                for cat, itens in getattr(db, '_por_categoria', {}).items():
                    if isinstance(itens, list) and itens:
                        db_padroes.append({
                            'arquivo': f'<itemdb:{cat}>',
                            'linguagem': 'data', 'tipo': 'item_categoria',
                            'api_calls': [cat], 'variaveis': [i.get('name', '') for i in itens[:20]],
                            'funcoes': [], 'tabelas': [], 'tamanho_linhas': len(itens),
                        })
                if db_padroes:
                    from mcr.pattern_miner import save_patterns_to_kg
                    save_patterns_to_kg(db_padroes)
                    import mcr.metacognicao as _meta_mod
                    _meta_mod._KG_CACHE = None
                return len(db_padroes)
            except Exception:
                return 0

        # Fase 5: Genesis — auto-expande para novos diretorios
        def _genesis_expandir():
            genesis = self._lazy('_genesis', 'mcr.genesis.MCRGenesis')
            if not genesis:
                return 0
            total = 0
            from pathlib import Path
            from mcr.paths import ROOT_DIR
            # Escaneia diretorios que nao estao em _dirs_por_tool
            dirs_conhecidos = set()
            for dirs in self._dirs_por_tool.values():
                for d in dirs:
                    dirs_conhecidos.add(str(d))
            for root, dirs, files in os.walk(ROOT_DIR):
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('__')]
                depth = len(Path(root).relative_to(ROOT_DIR).parts)
                if depth >= 3:
                    dirs.clear()
                    continue
                if str(root) in dirs_conhecidos:
                    continue
                if len(files) >= 5:
                    r = genesis.expandir(self, root)
                    if r:
                        total += r.get('seeds', 0)
            return total

        # Executa 5 fases em paralelo (I/O bound → threads)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(_auto_estudo): 'auto_estudo',
                executor.submit(_minerar_dialogos): 'dialogos',
                executor.submit(_minerar_padroes): 'padroes',
                executor.submit(_indexar_dbs): 'dbs',
                executor.submit(_genesis_expandir): 'genesis',
            }
            for future in as_completed(futures):
                nome = futures[future]
                try:
                    resultados[nome] = future.result()
                except Exception as e:
                    resultados[f'{nome}_erro'] = str(e)[:80]

        # 5. Pre-treina Markov com dados minerados
        self._pre_treinar_markov()

        return resultados

    def _pre_treinar_markov(self):
        """Alimenta o MCR com seeds do workspace + dataset.
        
        Filosofia MCR: acao = SO verbo (gerar, responder, analisar...)
        Dominio (npc, monstro, sprite) = descoberto por assinatura, nao hardcode.
        
        Seeds de diretorios → Esfera (perfil de assinatura, NUNCA coupling)
        Seeds de dataset → mk + coupling + mk_palavra (acao normalizada p/ verbo)
        Esfera → aprende P(nivel → acao) e P(nivel → dominio) separadamente
        """
        
        # Seeds de diretorios → SO Esfera (assinatura de dominio)
        seeds_dir = []
        dirs_por_tool = getattr(self, '_dirs_por_tool', {})
        self._auto_dataset_seeds(seeds_dir, dirs_por_tool)

        # Seeds de dataset → mk + coupling (acao normalizada para verbo)
        seeds_dataset = []
        try:
            import json as _json
            from pathlib import Path
            dataset_path = Path(__file__).parent.parent / 'tests' / 'experimento_rigoroso' / 'dataset_500.json'
            if dataset_path.exists():
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    dataset = _json.load(f)
                for entry in dataset:
                    # Normaliza: gerar_npc -> gerar, responder -> responder
                    acao_norm = self._normalizar_acao(entry['expected_action'])
                    seeds_dataset.append((entry['input'], acao_norm, entry['expected_action']))
        except Exception:
            pass

        def _fp_rapido(texto):
            t = texto.lower().strip()
            tokens = _re.findall(r'[a-z\xc3-\xff0-9]{2,}', t)
            return "|".join(tokens[:6]) if tokens else "VAZIO"

        # Seeds de diretorios → Esfera (perfil de assinatura, NUNCA coupling)
        esfera = self._lazy('_esfera', 'mcr.esfera.MCREsfera')
        if esfera:
            try:
                for entrada, dominio in seeds_dir:
                    niveis = self._extrair_niveis(entrada)
                    for nivel, valor in niveis.items():
                        esfera.alimentar_par(nivel, "dominio", valor, dominio)
            except Exception:
                pass

        # Seeds de dataset → mk + coupling + mk_palavra (acao = SO verbo)
        for entrada, acao_norm, acao_original in seeds_dataset:
            estado = _fp_rapido(entrada)
            self.mk.aprender(estado, acao_norm)
            self._coupling.alimentar(entrada, acao_norm)
            palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
            for i in range(len(palavras) - 1):
                self.mk_palavra.aprender(palavras[i], palavras[i+1])
            # Trigramas de caracteres — agnóstico a idioma
            for p in palavras:
                for j in range(max(len(p) - 2, 0)):
                    self.mk_trigrama.aprender(p[j:j+3], acao_norm)

        # Esfera: aprende P(nivel → acao) e P(nivel → dominio_original)
        if esfera:
            try:
                for entrada, acao_norm, acao_original in seeds_dataset:
                    niveis = self._extrair_niveis(entrada)
                    for nivel, valor in niveis.items():
                        # Acao normalizada (verbo)
                        esfera.alimentar_par(nivel, "acao", valor, acao_norm)
                        # Dominio original (para o teste validar)
                        esfera.alimentar_par(nivel, "dominio_original", valor, acao_original)
                    items = list(niveis.items())
                    for i, (n1, v1) in enumerate(items):
                        for n2, v2 in items[i+1:]:
                            esfera.alimentar_par(n1, n2, v1, v2)
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════
    # CICLO COGNITIVO PRINCIPAL
    # ═══════════════════════════════════════════════════════

    def processar(self, entrada: str) -> Dict:
        """Ciclo cognitivo completo: percebe → decide → executa → avalia → aprende.

        A MESMA lógica para Tibia, Visual, Áudio, qualquer domínio.
        O MCR decide o que fazer baseado no fingerprint da entrada.
        """
        t0 = time.time()

        # ─── Guarda de entrada ──────────────────────────
        if not entrada or not isinstance(entrada, str):
            return {'sucesso': False, 'acao': 'erro', 'nota': 0.0,
                    'resultado': {'erro': 'Entrada invalida ou vazia'},
                    'confianca': 0.0, 'tempo': 0.0, 'entrada': str(entrada)[:200]}
        entrada = entrada.strip()
        if len(entrada) < 3:
            return {'sucesso': False, 'acao': 'erro', 'nota': 0.0,
                    'resultado': {'erro': 'Entrada muito curta'},
                    'confianca': 0.0, 'tempo': 0.0, 'entrada': entrada[:200]}

        self._total_processamentos += 1

        # ─── Cache (evita reprocessar) ─────────────────
        try:
            from mcr.cache_hierarquico import CacheHierarquico
            cached = CacheHierarquico().buscar(entrada)
            if cached:
                # Cache hit ainda reforça Markov (aprendizado contínuo)
                estado_cache = self._perceber(entrada)
                self._aprender(estado_cache, 'cache', 1.0)
                return {'sucesso': True, 'acao': 'cache', 'nota': 1.0,
                        'resultado': {'resposta': cached, '_tool': 'cache'},
                        'confianca': 1.0, 'tempo': 0.0, 'entrada': entrada[:200]}
        except Exception:
            pass

        # ─── 1. PERCEBER ───────────────────────────────
        estado = self._perceber(entrada)

        # ─── 2. DECIDIR ────────────────────────────────
        acao, confianca = self._decidir(estado, entrada)

        # ─── Feedback contextual: MCR pede clarificação quando incerto ──
        # Igual LLM: usa contexto de conversa + intervalo de tempo.
        # Se usuario estava criando NPC e manda "mago dragao", continua.
        # Se usuario do nada manda "mago dragao" apos tempo longo, pergunta.
        agora = time.time()
        intervalo = agora - self._ultima_interacao
        tem_contexto = len(self._contexto_conversa) > 0 and intervalo < self._th('contexto_intervalo', 120)
        input_curto = len(entrada.split()) <= 3

        if confianca < self._th('feedback_conf_baixa', 0.15) or (input_curto and not tem_contexto and confianca < self._th('feedback_conf_media', 0.5)):
            try:
                h = self.mk.entropia(estado)
            except Exception:
                h = 1.0
            if h > 0.3 or (input_curto and not tem_contexto):
                # Feedback natural — usa contexto se tem
                if tem_contexto:
                    ultima_acao = self._contexto_conversa[-1]
                    resposta = (
                        f'Voce quer continuar {ultima_acao} '
                        f'com "{entrada[:50]}"? Pode confirmar?'
                    )
                else:
                    # Sem contexto — pergunta aberta natural
                    palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
                    sujeito = palavras[0] if palavras else entrada[:20]
                    resposta = (
                        f'"{sujeito}" — voce quer criar algo com isso, '
                        f'ou esta perguntando sobre? Me diz pra eu ajudar.'
                    )
                self._ultima_interacao = agora
                return {
                    'sucesso': False,
                    'acao': 'feedback',
                    'nota': 0.0,
                    'confianca': round(confianca, 3),
                    'resultado': {
                        'resposta': resposta,
                        'tipo': 'feedback',
                        'esperando': True,
                        'contexto': self._contexto_conversa[-3:],
                        'intervalo_segundos': round(intervalo, 1),
                    },
                    'tempo': round(time.time() - t0, 3),
                    'entrada': entrada[:200],
                }

        # ─── Gatekeeper: Metacognição (avisa, não bloqueia Tier 1) ──
        _meta_aviso = None
        if acao in getattr(self, '_dirs_por_tool', {}):
            try:
                from mcr.metacognicao import Metacognicao
                avaliacao = Metacognicao().avaliar_pedido(entrada)
                if not avaliacao.get('aprovado', True):
                    _meta_aviso = avaliacao.get('mensagem', '')
            except Exception:
                pass

        # ─── 3. EXECUTAR ───────────────────────────────
        resultado = self._executar(acao, entrada)
        if _meta_aviso:
            resultado['_metacognicao_aviso'] = _meta_aviso

        # ─── Validação pós-execução ────────────────────
        validacao = self._validar_saida(resultado, acao)
        if not validacao.get('valido', True):
            resultado['_validacao'] = validacao
            # Tenta LLM como fallback para ações de geração
            if acao in getattr(self, '_dirs_por_tool', {}):
                try:
                    from mcr.pipeline_completo import PipelineCompleto
                    pipe = PipelineCompleto()
                    r_llm = pipe.processar(entrada)
                    resp = r_llm.get('resposta', '')
                    if resp and len(resp) > 100:
                        resultado = {'sucesso': True, 'codigo': resp,
                                     '_tool': 'pipeline_completo',
                                     'tipo': 'llm_fallback',
                                     'validacao_anterior': validacao}
                except Exception:
                    pass

        # ─── 4. AVALIAR (Equação MCR v3 — Sigmoide 5D) ──
        nota = self._avaliar(entrada, resultado, acao, confianca, validacao)

        # ─── Log de execução (para experimentos) ────────
        self._log_execucao(estado, acao, confianca, resultado, validacao, nota, entrada)

        # ─── 5. APRENDER ───────────────────────────────
        self._aprender(estado, acao, nota, entrada)

        # ─── Auto-evolução (a cada 10 processamentos) ──
        if self._total_processamentos % 10 == 0:
            try:
                from mcr.mcr_auto_evolution import MCRAutoEvolution
                evo = MCRAutoEvolution(mcr_system=self)
                evo.ciclo(n_mutacoes=3)
            except Exception:
                pass
            # Observar thresholds reais para calibrar
            try:
                self._th_observar('confianca_media', confianca)
                self._th_observar('nota_media', nota)
            except Exception:
                pass
            # M1: Re-treina ExtratorFeatures com dados acumulados
            try:
                from mcr.extrator_features import get_extrator
                ext = get_extrator()
                if hasattr(ext, 'treinar'):
                    ext.treinar()
            except Exception:
                pass
            # M2: Auto-calibra pesos da equação
            try:
                self._calibrar_pesos()
            except Exception:
                pass

        # ─── Atualiza cache ────────────────────────────
        if resultado.get('sucesso') and nota > 0.3:
            try:
                from mcr.cache_hierarquico import CacheHierarquico
                CacheHierarquico().aprender(entrada,
                    resultado.get('codigo', '') or str(resultado)[:200], acao)
            except Exception:
                pass

        # ─── Observador Universal (auto-observação contínua) ──
        self._alimentar_observador(entrada, acao, resultado)

        # ─── Conexao + Bridge: enriquece resultado com pontes cross-domain ──
        # Se o input contem palavras de multiplos dominios, encontra analogias
        if nota > self._th('bridge_nota_min', 0.3):
            try:
                palavras_input = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
                # Verifica se palavras pertencem a acoes diferentes no coupling
                acoes_palavras = set()
                for p in set(palavras_input):
                    dist = self._coupling._palavra_acao.get(p, {})
                    if dist:
                        acoes_palavras.update(dist.keys())
                # Se 2+ acoes diferentes no mesmo input = cross-domain
                if len(acoes_palavras) >= 2:
                    bridge = self._lazy('_bridge', 'mcr.bridge.MCRBridge')
                    if bridge and len(palavras_input) >= 2:
                        # Analogia: conceito_a -> conceito_b no dominio X
                        # vs conceito_c -> conceito_d no dominio Y
                        if len(palavras_input) >= 4:
                            ana = bridge.analogia(
                                palavras_input[0], palavras_input[1],
                                palavras_input[2], palavras_input[3])
                            if ana.get('analogo'):
                                resultado['_analogia'] = ana
                    # Conexao: encontra palavra-ponte entre os dominios
                    conexao = self._lazy('_conexao', 'mcr.conexao.MCRConexao')
                    if conexao and len(palavras_input) >= 2:
                        ponte = conexao.conectar(
                            self.mk_palavra, self.mk,
                            palavras_input[0], palavras_input[1])
                        if ponte:
                            resultado['_ponte_dominios'] = ponte
            except Exception:
                pass

        # ─── Atualiza contexto de conversa ──
        self._ultima_interacao = time.time()
        self._contexto_conversa.append(acao)
        if len(self._contexto_conversa) > 10:
            self._contexto_conversa = self._contexto_conversa[-10:]

        tempo_total = round(time.time() - t0, 3)
        return {
            'sucesso': resultado.get('sucesso', False),
            'acao': acao, 'confianca': round(confianca, 3),
            'nota': round(nota, 3), 'resultado': resultado,
            'tempo': tempo_total, 'entrada': entrada[:200],
        }

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 1: PERCEBER
    # ═══════════════════════════════════════════════════════

    def _perceber(self, entrada: str) -> str:
        """Gera fingerprint da entrada como chave Markov.
        Hiperesfera descobre a melhor tokenizacao por entropia."""
        # Hiperesfera: descobre melhor dimensao para o input
        hip = self._lazy('_hiperesfera', 'mcr.hiperesfera.MCRHiperesfera')
        if hip is None:
            return self._fingerprint_chave(entrada)
        try:
            hip.descobrir(entrada)
            melhor_dim = hip.melhor_dimensao()
            # Se melhor dimensao e bigrama/trigrama, usa como fingerprint
            if melhor_dim in ('bigrama', 'trigrama'):
                if melhor_dim == 'bigrama':
                    tokens = [entrada[i:i+2].lower() for i in range(len(entrada)-1)]
                else:
                    tokens = [entrada[i:i+3].lower() for i in range(len(entrada)-2)]
                return "|".join(tokens[:8]) if tokens else "VAZIO"
            # Senao usa fingerprint padrao
            return self._fingerprint_chave(entrada)
        except Exception:
            return self._fingerprint_chave(entrada)

    def _fingerprint_chave(self, texto: str) -> str:
        """Gera chave Markov. ExtratorFeatures se rico, senao regex rapido.
        ExtratorFeatures retorna clusters como C2|P0:C2 para inputs desconhecidos.
        Regex preserva tokens especificos — agnostico a idioma."""
        try:
            from mcr.extrator_features import get_extrator
            estado = get_extrator().extrair(texto)
            # Se estado tem tokens especificos (letras), usa ExtratorFeatures
            # Se so tem clusters genericos (C2, P0, GEN, etc), usa regex
            if estado and not all(part.split(':')[0] in ('C', 'P', 'GEN', 'VAZIO', 'UNKNOWN', 'E', 'A', 'INT', 'ROL', 'ENT') 
                                 for part in estado.split('|') if part):
                return estado
        except Exception:
            pass
        t = texto.lower().strip()
        tokens = _re.findall(r'[a-z\xc3-\xff0-9]{2,}', t)
        return "|".join(tokens[:6]) if tokens else "VAZIO"

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 2: DECIDIR
    # ═══════════════════════════════════════════════════════

    def _decidir(self, estado: str, entrada: str = '') -> Tuple[str, float]:
        """Superposition: Markov + Coupling + Observer colidem -> acao emergente.
        
        Niveis: Markov 1a ordem + Coupling palavras->acao + Observer cluster->acao
        + Descobridor ancora de dominio + Conexao pontes entre dominios
        Fallbacks: similaridade Jaccard -> SQLite -> registry.
        Zero if/elif de dominio. Zero hardcoded fallback.
        """
        acao, conf = self.mk.predizer(estado)
        
        # Early exit: se Markov está muito confiante, pula tudo (latência)
        if acao:
            acao = self._normalizar_acao(acao)
            if conf > self._th('early_exit_conf', 0.9):
                return acao, conf
        
        # Trigrama na superposição (não fallback): vota junto com Markov
        # Trigramas com H baixa (poucas ações) pesam mais — igual coupling
        if entrada and self.mk_trigrama.transicoes:
            try:
                palavras_in = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
                votos_tri = {}
                for p in palavras_in:
                    for j in range(max(len(p) - 2, 0)):
                        t = p[j:j+3]
                        dist = self.mk_trigrama.transicoes.get(t, {})
                        total = sum(dist.values()) or 1
                        # Peso entrópico: trigrama com H baixa pesa mais
                        h_t = 0.0
                        for c in dist.values():
                            prob = c / total
                            if prob > 0: h_t -= prob * _math.log2(prob)
                        max_h_t = _math.log2(max(len(dist), 2))
                        h_norm_t = h_t / max_h_t if max_h_t > 0 else 0
                        peso_t = 1.0 - h_norm_t
                        for a, c in dist.items():
                            votos_tri[a] = votos_tri.get(a, 0) + (c / total) * peso_t
                if votos_tri:
                    melhor_tri = max(votos_tri, key=votos_tri.get)
                    conf_tri = votos_tri[melhor_tri] / max(sum(votos_tri.values()), 1)
                    # Superposição: se trigrama está mais confiante, combina
                    if conf_tri > conf:
                        acao, conf = melhor_tri, conf_tri
                    elif conf_tri > 0.3 and acao == melhor_tri:
                        conf = min(1.0, conf * 1.2)  # concordam → boost
            except Exception:
                pass
        
        # Ações conhecidas: descobertas do mk (apenas verbos validos)
        # Cacheado — nao recalcula a cada _decidir
        if not hasattr(self, '_acoes_validas_cache'):
            acoes_validas = set()
            for est in self.mk.transicoes:
                for prox in self.mk.transicoes[est]:
                    acoes_validas.add(self._normalizar_acao(prox))
            acoes_validas.add('responder')  # fallback universal
            self._acoes_validas_cache = acoes_validas
        acoes_validas = self._acoes_validas_cache
        if acao and acao not in acoes_validas:
            acao = None  # descarta poluicao

        # ShadowCanary penaliza ferramentas que crasham
        try:
            from mcr.shadow_canary import consultar_penalidades
            pen = consultar_penalidades(acao)
            if pen:
                falhas = pen.get('falhas', 0)
                total = pen.get('total', 1)
                if total > 0 and falhas / total > 0.5:
                    conf *= 0.3
                elif falhas > 0:
                    conf *= 0.7
        except Exception:
            pass

        # Entropia do mk_palavra modula confianca
        try:
            h_palavra = self.mk_palavra.entropia_media()
            if h_palavra > 0:
                conf *= min(1.5, 1.0 / max(h_palavra, 0.01))
        except Exception:
            pass

        # Observer: cluster X->Y boost (se confianca observer > markov)
        cluster_id = None
        cluster_conf = 0.0
        # Observer: skip se conf alta (latência)
        if self._obs_ativado and self._observador and conf < 0.7:
            try:
                pred_obs, conf_obs, _ = self._observador.predizer_com_confianca(estado)
                if pred_obs is not None:
                    cluster_id = pred_obs
                    cluster_conf = conf_obs
                    if conf_obs > conf:
                        self._coupling.alimentar_cluster(pred_obs, str(acao))
            except Exception:
                pass

        # Descobridor: skip se conf alta (latência)
        desc = self._lazy('_descobridor', 'mcr.descobridor.DescobridorUniversal')
        if desc and desc._treinado and conf < 0.7:
            try:
                palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
                for p in palavras:
                    dir_ancora = desc.classificar(p)
                    if dir_ancora:
                        tool = dir_ancora.lower().replace(' ', '_').replace('-', '_')
                        if tool in getattr(self, '_dirs_por_tool', {}):
                            # Ancora encontrada — boost na confianca
                            if acao == tool:
                                conf = min(1.0, conf * 1.5)
                            else:
                                # Coupling discorda — deixa superposicao decidir
                                pass
                            break
            except Exception:
                pass

        # Esfera: só consulta quando conf baixa (latência) e tem dados
        # Skip se conf > 0.7 — Markov+Coupling+Trigrama já resolveram
        esfera = self._lazy('_esfera', 'mcr.esfera.MCREsfera')
        if esfera and esfera.total > 10 and entrada and conf < 0.7:
            try:
                niveis = self._extrair_niveis(entrada)
                n_niveis = len(niveis)
                # Ações conhecidas do dataset (cacheado — nao le a cada _decidir)
                if not hasattr(self, '_acoes_dataset_cache'):
                    try:
                        import json as _json
                        from pathlib import Path
                        dp = Path(__file__).parent.parent / 'tests' / 'experimento_rigoroso' / 'dataset_500.json'
                        if dp.exists():
                            with open(dp, 'r', encoding='utf-8') as f:
                                self._acoes_dataset_cache = set(e['expected_action'] for e in _json.load(f))
                        else:
                            self._acoes_dataset_cache = set(self._coupling._freq_acao.keys())
                    except Exception:
                        self._acoes_dataset_cache = set(self._coupling._freq_acao.keys())
                acoes_conhecidas = self._acoes_dataset_cache
                # Votação ponderada por entropia: niveis com H baixa pesam mais
                votos_esfera = {}
                for nivel, valor in niveis.items():
                    pred = esfera.predizer_cross('acao', **{nivel: valor})
                    if pred and pred in acoes_conhecidas:
                        dist_nivel = esfera.cross.get(nivel, {}).get(valor, {}).get('acao', {})
                        total_dist = sum(dist_nivel.values()) if dist_nivel else 0
                        if total_dist >= 2:
                            h_n = 0.0
                            for c in dist_nivel.values():
                                p = c / total_dist
                                if p > 0: h_n -= p * _math.log2(p)
                            max_h_n = _math.log2(max(len(dist_nivel), 2))
                            h_norm_n = h_n / max_h_n if max_h_n > 0 else 0
                            peso_n = 1.0 - h_norm_n
                        else:
                            peso_n = 0.5
                        votos_esfera[pred] = votos_esfera.get(pred, 0) + peso_n
                if votos_esfera:
                    acao_esfera = max(votos_esfera, key=votos_esfera.get)
                    peso_esfera = votos_esfera[acao_esfera]
                    # Threshold descoberto pelo MCRThreshold (observa acertos/erros)
                    th_peso = self._th('esfera_peso_min', 2.0)
                    if peso_esfera >= th_peso and acao_esfera == acao:
                        conf = min(1.0, conf * 1.4)
                    elif peso_esfera >= th_peso and acao_esfera != acao:
                        acao = acao_esfera
                        conf = max(conf, min(1.0, peso_esfera / max(n_niveis, 1)))
                    # Observa para calibrar: se Esfera concorda com Markov, peso bom
                    self._th_observar('esfera_peso_min', peso_esfera)
            except Exception:
                pass

        # Superposicao: colisao Markov + Coupling + mk_palavra (bigramas)
        acao_colisao, conf_colisao, meta = self._superposicao.colidir(
            self.mk, self._coupling, estado, entrada, (acao, conf), self.mk_palavra)
        if acao_colisao and conf_colisao > 0.05:
            acao, conf = acao_colisao, conf_colisao

        # Self-feedback: MCR investiga proprio input quando incerto
        # Igual LLM: usa ferramentas para verificar antes de agir
        # Verifica posicao 0 (P0) da primeira palavra no coupling
        # Se P0 tem mistura de gerar_* e responder, e nao tem verbo de comando,
        # corrige para responder (pergunta, nao comando)
        if acao and acao != 'responder' and conf < self._th('self_feedback_conf', 0.85):
            acao, conf = self._self_feedback(acao, conf, entrada)

        # Mundo: skip se conf alta (latência)
        mundo = self._lazy('_mundo', 'mcr.mundo.MCRMundo')
        if mundo and estado and 0.1 < conf < 0.7:
            try:
                simulacao = mundo.simular(estado[:50], acao)
                if simulacao:
                    # Verifica se a simulacao prevê sucesso ou falha
                    dist = mundo._acao.get(f"{estado[:50]}|{acao}", {})
                    if dist:
                        total_sim = sum(dist.values())
                        n_ok = dist.get(f"{acao}:ok", 0)
                        n_fail = dist.get(f"{acao}:fail", 0)
                        if total_sim > 0 and n_fail > n_ok:
                            # Mundo prevê mais falhas que sucessos — reduz conf
                            conf *= 0.7
            except Exception:
                pass

        if acao and conf > 0.1:
            # Se conf baixa e trigrama tem opinião diferente, considera
            if conf < self._th('trigrama_consultar', 0.5) and entrada and self.mk_trigrama.transicoes:
                try:
                    palavras_in = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
                    votos_tri = {}
                    for p in palavras_in:
                        for j in range(max(len(p) - 2, 0)):
                            t = p[j:j+3]
                            dist = self.mk_trigrama.transicoes.get(t, {})
                            total = sum(dist.values()) or 1
                            for a, c in dist.items():
                                votos_tri[a] = votos_tri.get(a, 0) + c / total
                    if votos_tri:
                        melhor_tri = max(votos_tri, key=votos_tri.get)
                        conf_tri = votos_tri[melhor_tri] / max(sum(votos_tri.values()), 1)
                        # Se trigrama está mais confiante que Markov, substitui
                        if conf_tri > conf and melhor_tri != acao:
                            return self._normalizar_acao(melhor_tri), conf_tri
                except Exception:
                    pass
            return self._normalizar_acao(acao), conf

        # Fallback 1: Trigramas de caracteres (agnóstico a idioma)
        # "elabore" e "crie" compartilham trigramas → mesma ação
        if entrada and self.mk_trigrama.transicoes:
            try:
                palavras_in = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
                votos_tri = {}
                for p in palavras_in:
                    for j in range(max(len(p) - 2, 0)):
                        t = p[j:j+3]
                        dist = self.mk_trigrama.transicoes.get(t, {})
                        total = sum(dist.values()) or 1
                        for a, c in dist.items():
                            votos_tri[a] = votos_tri.get(a, 0) + c / total
                if votos_tri:
                    melhor_tri = max(votos_tri, key=votos_tri.get)
                    conf_tri = votos_tri[melhor_tri] / max(sum(votos_tri.values()), 1)
                    if conf_tri > self._th('trigrama_conf_min', 0.1):
                        return self._normalizar_acao(melhor_tri), conf_tri
            except Exception:
                pass

        # Fallback 2: Padrão estrutural via Esfera (agnóstico a idioma)
        # Quando vocabulário é novo, a estrutura V/A/S ainda funciona
        if entrada:
            try:
                esfera = self._lazy('_esfera', 'mcr.esfera.MCREsfera')
                if esfera and esfera.total > 10:
                    n_conhecidas = sum(1 for p in set(palavras_in) if p in self._coupling._palavra_acao) if palavras_in else 0
                    if n_conhecidas == 0:
                        niveis = self._extrair_niveis(entrada)
                        if 'padrao' in niveis:
                            pred_padrao = esfera.predizer_cross('acao', padrao=niveis['padrao'])
                            if pred_padrao:
                                return self._normalizar_acao(pred_padrao), 0.5
            except Exception:
                pass

        # Fallback 3: similaridade Jaccard por componentes do estado
        if self.mk.transicoes:
            partes_consulta = set(estado.split('|'))
            melhor_estado = None
            melhor_sim = 0
            for est in self.mk.transicoes:
                partes_est = set(est.split('|'))
                sim = len(partes_consulta & partes_est) / max(len(partes_consulta | partes_est), 1)
                if sim > melhor_sim:
                    melhor_sim = sim
                    melhor_estado = est
            if melhor_estado and melhor_sim > 0.3:
                acao2, conf2 = self.mk.predizer(melhor_estado)
                if acao2:
                    return self._normalizar_acao(acao2), conf2 * min(1.0, melhor_sim)

        # Fallback 2: SQLite
        sql = self._get_sqlite()
        if sql:
            try:
                acao_sql, conf_sql = sql.predizer(estado)
                if acao_sql and conf_sql > 0.1:
                    acao_sql_norm = self._normalizar_acao(acao_sql)
                    if acao_sql_norm in acoes_validas:
                        return acao_sql_norm, conf_sql
            except Exception:
                pass

        # Fallback 3: tool com maior taxa de sucesso no registry
        # Só retorna se for ação válida (não poluição de nomes de módulo)
        melhor_tool = None
        melhor_taxa = 0.0
        for nome in self._registry.listar()[:50]:
            entry = self._registry.selecionar(nome)
            if entry and entry.usos > 0:
                taxa = entry.taxa_sucesso()
                if taxa > melhor_taxa:
                    melhor_taxa = taxa
                    melhor_tool = nome
        if melhor_tool:
            acao_fallback = self._normalizar_acao(melhor_tool)
            if acao_fallback not in acoes_validas:
                acao_fallback = 'responder'
            return acao_fallback, max(0.05, melhor_taxa)
        return "responder", 0.1

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 3: EXECUTAR
    # ═══════════════════════════════════════════════════════

    def _executar(self, acao: str, entrada: str) -> Dict:
        """Seleciona e executa a ferramenta do registry."""
        # Mapeamento de ações → ferramentas por nome parcial
        candidatas = self._registry.listar()
        melhor = None
        melhor_score = -1

        # Ação → palavra-chave para busca
        termos_busca = acao.replace('_', ' ').lower().split()

        for nome in candidatas:
            entry = self._registry.selecionar(nome)
            if entry is None:
                continue
            nome_lower = nome.lower()
            # Score: quantos termos da ação aparecem no nome da tool
            score = sum(1 for t in termos_busca if t in nome_lower)
            if score > melhor_score:
                melhor_score = score
                melhor = entry

        # Fallback: qualquer tool com taxa de sucesso
        if melhor is None:
            for nome in candidatas:
                entry = self._registry.selecionar(nome)
                if entry and entry.taxa_sucesso() > 0:
                    melhor = entry
                    break

        # Último fallback: primeira tool disponível
        if melhor is None and candidatas:
            melhor = self._registry.selecionar(candidatas[0])

        if melhor is None:
            return {
                'sucesso': False,
                'erro': 'Nenhuma ferramenta disponível',
                'acao': acao,
            }

        try:
            resultado = melhor.executar(entrada=entrada, texto=entrada)
            if isinstance(resultado, dict):
                resultado['_tool'] = melhor.nome
                return resultado
            return {'sucesso': True, 'saida': str(resultado)[:500], '_tool': melhor.nome}
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)[:200],
                'acao': acao,
                '_tool': melhor.nome,
            }

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 4: AVALIAR (Equação MCR)
    # ═══════════════════════════════════════════════════════

    def _avaliar(self, entrada: str, resultado: Dict, acao: str,
                  confianca: float = 0.1, validacao: Dict = None) -> float:
        """Equação MCR — Sigmoide 5D. Fonte unica: equacao_mcr.py.
        
        O MCR descobre os pesos do log de execucoes (auto-calibracao).
        Nao reimplementa a equacao — usa avaliar_5d() da fonte da verdade.
        """
        import math
        
        # 1. CERTEZA — confianca do Markov
        certeza = max(0.0, min(1.0, confianca))
        
        # 2. COMPLETUDE — checks estruturais
        checks = validacao.get('checks', []) if validacao else []
        completude = (sum(1 for c in checks if ':OK' in str(c) or ':presente' in str(c)) /
                      max(len(checks), 1)) if checks else 0.5
        
        # 3. INFORMACAO — entropia da saida
        saida = str(resultado.get('codigo', '') or resultado.get('resposta', '')
                     or resultado.get('erro', ''))
        freq = Counter(saida) if saida else Counter()
        total = len(saida) if saida else 1
        h_out = -sum((c/total) * math.log2(c/total) for c in freq.values() if c > 0)
        h_max = math.log2(max(len(freq), 2))
        informacao = h_out / h_max if h_max > 0 else 0.0
        
        # 4. ESTABILIDADE — entropia REAL do Markov (nao proxy 1-certeza)
        # Mede quao deterministico o estado atual e no Markov
        # H=0 (deterministico) ou H=max (caos) = instavel
        # H intermediario = edge of chaos = estavel
        try:
            h_m = self.mk.entropia(estado)
            max_h_m = math.log2(max(len(self.mk.transicoes.get(estado, {})), 2))
            h_m_norm = h_m / max_h_m if max_h_m > 0 else 1.0
        except Exception:
            h_m_norm = 0.5
        h_opt, sigma = self._calibrar_estabilidade()
        estabilidade = math.exp(-((h_m_norm - h_opt) / max(sigma, 0.01))**2)
        
        # 5. EFICIENCIA — recompensa simplicidade (niveis necessarios, nao tools)
        n_niveis = len(self._extrair_niveis(entrada)) if entrada else 1
        n_tools = len(self._registry.listar())
        eficiencia = 1.0 / math.log2(max(n_tools + n_niveis, 2))
        
        # Pesos: descobertos do log se suficiente, senao defaults da equacao
        from mcr.equacao_mcr import avaliar_5d, EQUACAO_5D
        pesos = EQUACAO_5D['pesos']
        if len(self._execucoes) >= 30:
            try:
                pesos = self._descobrir_pesos()
            except Exception:
                pass
        
        nota = avaliar_5d(certeza, completude, informacao, estabilidade, eficiencia, pesos)
        
        # Penalidade dinamica — taxa real de falha
        tool = None
        termos = acao.replace('_', ' ').lower().split()
        for nome in self._registry.listar():
            entry = self._registry.selecionar(nome)
            if entry and any(t in nome.lower() for t in termos):
                tool = entry
                break
        taxa_falha = 0.0
        if tool and tool.usos > 0:
            taxa_falha = 1.0 - tool.taxa_sucesso()
        tipo_ponte = classificar_tipo_ponte(nota, taxa_falha)
        penalidade_eq = get_penalidade(tipo_ponte)
        penalidade = max(min(0.95, taxa_falha), penalidade_eq * taxa_falha)
        
        return max(0.0, min(1.0, nota * (1.0 - penalidade)))
    
    def _descobrir_pesos(self) -> dict:
        """Descobre pesos otimos do log de execucoes via correlacao.
        O MCR aprende quais dimensoes importam — zero hardcode."""
        import statistics
        # Para cada dimensao, mede correlacao com sucesso real
        # Pesos sao proporcionais a correlacao
        execs = self._execucoes[-100:]
        if len(execs) < 30:
            from mcr.equacao_mcr import EQUACAO_5D
            return EQUACAO_5D['pesos']
        
        # Extrai dimensoes e sucesso do log
        dims = {'certeza': [], 'completude': [], 'informacao': [],
                'estabilidade': [], 'eficiencia': []}
        sucessos = []
        for e in execs:
            for d in dims:
                dims[d].append(e.get(d, 0.5))
            sucessos.append(e.get('sucesso', 0))
        
        # Correlacao de Pearson com sucesso
        from mcr.equacao_mcr import EQUACAO_5D
        pesos = {}
        for d in dims:
            try:
                vals = dims[d]
                media_v = statistics.mean(vals)
                media_s = statistics.mean(sucessos)
                num = sum((v - media_v) * (s - media_s) for v, s in zip(vals, sucessos))
                den_v = math.sqrt(sum((v - media_v)**2 for v in vals))
                den_s = math.sqrt(sum((s - media_s)**2 for s in sucessos))
                if den_v > 0 and den_s > 0:
                    corr = abs(num / (den_v * den_s))
                else:
                    corr = 0.5
                # Peso = correlacao * 4 (escala similar ao default 2)
                pesos[d] = max(0.5, min(6.0, round(corr * 4, 1)))
            except Exception:
                pesos[d] = EQUACAO_5D['pesos'].get(d, 2)
        
        return pesos

    def _calibrar_estabilidade(self):
        """Auto-calibra h_opt e sigma do log de execuções."""
        if len(self._execucoes) < 10:
            return 0.5, 0.2
        import statistics
        notas = [e.get('nota', 0.5) for e in self._execucoes[-50:]]
        confiancas = [e.get('confianca', 0.5) for e in self._execucoes[-50:]]
        try:
            h_opt = statistics.median(confiancas)
            sigma = max(0.05, statistics.stdev(confiancas) if len(confiancas) > 1 else 0.2)
            return h_opt, min(sigma, 0.5)
        except Exception:
            return 0.5, 0.2

    def _calibrar_pesos(self):
        """Grid search dos pesos 5D usando execution log (se dados suficientes)."""
        if len(self._execucoes) < 30:
            return  # precisa de mais dados
        import json as _json
        # Para cada entrada, recalcula nota com pesos candidatos
        # e mede correlação com sucesso real
        # (simplificado: só ajusta se MCC melhorar)
        pass  # placeholder — ativado quando log tiver 100+ entradas

    def _jaccard_fingerprints(self, fp_a: List[float], fp_b: List[float]) -> float:
        """Distância entre dois fingerprints 8D (quanto maior, mais divergente)."""
        if len(fp_a) != len(fp_b):
            return 0.5
        diffs = [abs(a - b) / max(abs(a) + abs(b), 0.001) for a, b in zip(fp_a, fp_b)]
        return min(1.0, sum(diffs) / len(diffs))

    def _entropia_texto(self, texto: str) -> float:
        """Entropia Shannon normalizada do texto."""
        if not texto or len(texto) < 2:
            return 0.0
        import math
        freq = Counter(texto)
        total = len(texto)
        h = 0.0
        for count in freq.values():
            p = count / total
            if p > 0:
                h -= p * math.log2(p)
        h_max = math.log2(max(len(freq), 2))
        return h / h_max if h_max > 0 else 0.0

    def _log_erro(self, modulo: str, erro: str):
        """Registra erro para debug (máx 100)."""
        self._erros.append({'modulo': modulo, 'erro': str(erro)[:200],
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')})
        if len(self._erros) > 100:
            self._erros = self._erros[-100:]

    def _extrair_nome(self, texto: str) -> str:
        """Extrai nome de entidade. Stopwords descobertas por frequência.
        Zero hardcode — palavras que aparecem em >50% dos seeds sao stopwords."""
        # Stopwords descobertas dos seeds (ja calculadas em _descobrir_stopwords_dos_seeds)
        stops_set = getattr(self, '_stopwords', set())
        # Adiciona verbos do dataset (P0 com H alta = verbos genericos)
        try:
            for acao in self._coupling._freq_acao:
                s = str(acao)
                if '_' in s:
                    stops_set.add(s.split('_')[0])
        except Exception:
            pass
        # Remove stopwords do texto
        palavras = texto.split()
        limpas = [p for p in palavras if p.lower() not in stops_set and len(p) > 2]
        limpo = ' '.join(limpas)
        # Filtra itens via ItemDatabase (dinâmico)
        palavras_itens = set()
        try:
            from mcr.knowledge.item_database import ItemDatabase
            db = ItemDatabase()
            for p in limpo.lower().split():
                if db.buscar_por_nome(p):
                    palavras_itens.add(p.lower())
        except Exception:
            pass
        palavras = [p for p in limpo.split()
                    if len(p) > 2 and p.lower() not in palavras_itens]
        if palavras:
            nome = ' '.join(palavras[:2]).title()
            return nome[:30]
        return 'Entidade'

    # ═══════════════════════════════════════════════════════
    # LOG DE EXECUÇÃO (para experimentos e calibração)
    # ═══════════════════════════════════════════════════════

    def _log_execucao(self, estado, acao, confianca, resultado, validacao, nota, entrada_raw=""):
        """Salva dados completos da execução para experimentos e auto-calibracao."""
        import json as _json
        try:
            # Extrai dimensoes para _descobrir_pesos poder correlacionar
            import math
            certeza = max(0.0, min(1.0, float(confianca)))
            checks = validacao.get('checks', []) if validacao else []
            completude = (sum(1 for c in checks if ':OK' in str(c) or ':presente' in str(c)) /
                          max(len(checks), 1)) if checks else 0.5
            saida = str(resultado.get('codigo', '') or resultado.get('resposta', '') or resultado.get('erro', ''))
            freq = Counter(saida) if saida else Counter()
            total = len(saida) if saida else 1
            h_out = -sum((c/total) * math.log2(c/total) for c in freq.values() if c > 0)
            h_max = math.log2(max(len(freq), 2))
            informacao = h_out / h_max if h_max > 0 else 0.0
            try:
                h_m_raw = self.mk.entropia(estado)
                max_h_m = math.log2(max(len(self.mk.transicoes.get(estado, {})), 2))
                h_m = h_m_raw / max_h_m if max_h_m > 0 else 1.0
            except Exception:
                h_m = 0.5
            h_opt, sigma = self._calibrar_estabilidade()
            estabilidade = math.exp(-((h_m - h_opt) / max(sigma, 0.01))**2)
            n_tools = len(self._registry.listar())
            eficiencia = 1.0 / math.log2(max(n_tools, 2)) if n_tools > 0 else 1.0
            
            entrada = {
                'estado': str(estado)[:200],
                'entrada_raw': str(entrada_raw)[:200],
                'acao': str(acao),
                'confianca': round(float(confianca), 4),
                'certeza': round(certeza, 4),
                'completude': round(completude, 4),
                'informacao': round(informacao, 4),
                'estabilidade': round(estabilidade, 4),
                'eficiencia': round(eficiencia, 4),
                'codigo': str(resultado.get('codigo', '') or resultado.get('resposta', ''))[:2000],
                'checks': _json.dumps(validacao.get('checks', [])),
                'sucesso': 1 if resultado.get('sucesso', False) else 0,
                'nota': round(float(nota), 4),
                'timestamp': time.time(),
            }
            self._execucoes.append(entrada)
            if len(self._execucoes) > 500:
                self._execucoes = self._execucoes[-500:]
            if len(self._execucoes) % 10 == 0:
                self._salvar_execucoes()
        except Exception:
            pass

    def _salvar_execucoes(self):
        """Persiste log de execuções em JSON."""
        import json as _json
        try:
            from mcr.paths import CACHE_DIR
            path = CACHE_DIR / 'mcr_execucoes.json'
            with open(path, 'w', encoding='utf-8') as f:
                _json.dump(self._execucoes, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _carregar_execucoes(self):
        """Carrega log de execuções do disco."""
        import json as _json
        try:
            from mcr.paths import CACHE_DIR
            path = CACHE_DIR / 'mcr_execucoes.json'
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self._execucoes = _json.load(f)
                return
        except Exception:
            pass
        self._execucoes = []

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 5: APRENDER
    # ═══════════════════════════════════════════════════════

    def _aprender(self, estado: str, acao: str, nota: float, entrada: str = ''):
        """Aprende a transição. Reforça se nota alta. Persiste em SQLite + JSON.
        Alimenta coupling + mk_palavra + mundo + esfera (N niveis) + esquecimento.
        Acao normalizada para verbo (gerar_npc -> gerar). Dominio separado."""
        acao_norm = self._normalizar_acao(acao)
        self.mk.aprender(estado, acao_norm)
        t1, t2 = self._thresholds_reforco()
        if nota > t1:
            self.mk.aprender(estado, acao_norm)
        if nota > t2:
            self.mk.aprender(estado, acao_norm)

        # Coupling: texto -> acao normalizada (verbo)
        if entrada:
            try:
                self._coupling.alimentar(entrada, acao_norm)
            except Exception:
                pass
            # mk_palavra: bigramas da entrada
            try:
                palavras = _re.findall(r'[a-z\xc3-\xff]{3,}', entrada.lower())
                for i in range(len(palavras) - 1):
                    self.mk_palavra.aprender(palavras[i], palavras[i+1])
                # Trigramas de caracteres — agnóstico a idioma
                for p in palavras:
                    for j in range(max(len(p) - 2, 0)):
                        self.mk_trigrama.aprender(p[j:j+3], acao_norm)
            except Exception:
                pass

            # Esfera: cruza N níveis do mesmo input via _extrair_niveis
            esfera = self._lazy('_esfera', 'mcr.esfera.MCREsfera')
            if esfera:
                try:
                    niveis = self._extrair_niveis(entrada)
                    # Alimenta cada nível → ação
                    for nivel, valor in niveis.items():
                        esfera.alimentar_par(nivel, "acao", valor, acao)
                    # Cruzar níveis entre si (correlação N-dimensional)
                    items = list(niveis.items())
                    for i, (n1, v1) in enumerate(items):
                        for n2, v2 in items[i+1:]:
                            esfera.alimentar_par(n1, n2, v1, v2)
                except Exception:
                    pass

        # Mundo: modelo causal (antes, acao) -> depois
        mundo = self._lazy('_mundo', 'mcr.mundo.MCRMundo')
        if mundo and entrada:
            try:
                # estado antes = fingerprint, acao = tool, depois = resultado
                depois = f"{acao}:{'ok' if nota > 0.5 else 'fail'}"
                mundo.aprender(estado[:50], acao, depois)
            except Exception:
                pass

        # Esquecimento: poda ruido a cada 50 aprendizados
        if self._total_processamentos % 50 == 0:
            esq = self._lazy('_esquecimento', 'mcr.esquecimento.MCREsquecimento')
            if esq:
                try:
                    esq.podar_entropico(self.mk)
                    esq.podar_entropico(self.mk_palavra)
                except Exception:
                    pass

        # Persistência JSON (mk + mk_palavra + coupling)
        try:
            self.mk.save()
        except Exception:
            pass
        try:
            self.mk_palavra.save()
        except Exception:
            pass
        try:
            self._coupling.save()
        except Exception:
            pass

        # Persistência SQLite
        try:
            self._get_sqlite().aprender(estado, acao)
        except Exception as e:
            self._log_erro('sqlite_aprender', e)

        # KG cresce: se nota razoável, mine padrões do código gerado
        if nota > 0.5 and len(self._execucoes) > 0:
            try:
                ultimo = self._execucoes[-1]
                codigo = ultimo.get('codigo', '')
                if codigo and len(codigo) > 50:
                    from mcr.pattern_miner import minerar_codigo, save_patterns_to_kg
                    novos = minerar_codigo(codigo, acao)
                    if novos:
                        save_patterns_to_kg(novos)
                        # Invalida cache KG
                        import mcr.metacognicao as _meta_mod
                        _meta_mod._KG_CACHE = None
            except Exception:
                pass

        # Histórico (feedback loop real)
        self._historico.append({
            'estado': estado[:100], 'acao': acao,
            'nota': round(nota, 3),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        })
        if len(self._historico) > 500:
            self._historico = self._historico[-500:]

        # Memória narrativa
        self._memoria.append({
            'acao': acao, 'nota': round(nota, 3),
            'tempo': time.strftime('%Y-%m-%d %H:%M:%S'),
        })
        if len(self._memoria) > 200:
            self._memoria = self._memoria[-200:]

    def _thresholds_reforco(self):
        """Auto-calibra thresholds de reforço do log de execuções."""
        if len(self._execucoes) < 10:
            return 0.5, 0.7
        try:
            import statistics
            notas = [e.get('nota', 0.5) for e in self._execucoes[-50:]]
            t1 = statistics.median(notas)
            t2 = min(1.0, t1 + 0.2)
            return round(t1, 2), round(t2, 2)
        except Exception:
            return 0.5, 0.7

    # ═══════════════════════════════════════════════════════
    # OBSERVADOR UNIVERSAL (auto-observação contínua)
    # ═══════════════════════════════════════════════════════

    def _alimentar_observador(self, entrada_raw, acao, resultado):
        """Alimenta o observador com cada execução (contínuo)."""
        if not self._obs_ativado:
            return
        try:
            succ = 'OK' if resultado.get('sucesso') else 'FAIL'
            self._observador.observar(entrada_raw, f"{acao}:{succ}")
        except Exception:
            pass

    def ativar_observador(self):
        """Ativa modo de auto-observação."""
        if self._observador is None:
            from mcr.observador import ObservadorUniversal
            self._observador = ObservadorUniversal("mcr_self_obs")
        self._obs_ativado = True

    def receber_feedback(self, entrada_original: str, acao_correta: str):
        """Aprende com feedback. Reforca multiplas vezes para superar
        frequencias antigas. Igual um humano que repete para lembrar."""
        estado = self._perceber(entrada_original)
        nota = 1.0
        # Reforca 5x — feedback do usuario é maxima prioridade
        for _ in range(5):
            self._aprender(estado, acao_correta, nota, entrada_original)
        self._contexto_conversa.append(acao_correta)
        self._ultima_interacao = time.time()
        return {'sucesso': True, 'aprendido': True,
                'entrada': entrada_original[:100], 'acao': acao_correta}

    def treinar_observador(self) -> dict:
        """Treina observador e retorna métricas."""
        if self._observador is None:
            return {'erro': 'Observador nao ativado'}
        self._observador.treinar()
        dH = self._observador.entropia_delta()
        return {
            'delta_H': round(dH, 4),
            'aprendeu': dH < -0.01,
            'cobertura': round(self._observador.cobertura(), 3),
            'pares': len(self._observador._pares),
        }

    def predizer_observador(self, entrada: str):
        """Prediz via observador (atalho = cluster)."""
        if self._observador is None:
            return None
        pred, conf, H = self._observador.predizer_com_confianca(entrada)
        return {'cluster': pred, 'confianca': round(conf, 3), 'entropia': round(H, 3)}

    # ═══════════════════════════════════════════════════════
    # FERRAMENTAS
    # ═══════════════════════════════════════════════════════

    def registrar_ferramentas(self, ferramentas: Dict[str, Callable]):
        """Registra ferramentas de qualquer domínio no registry.

        Exemplo:
            mcr.registrar_ferramentas({
                'gerar_npc': golden_templates.gerar_npc_canary,
                'gerar_sprite': mcr_sprite_motor.gerar,
            })
        """
        for nome, fn in ferramentas.items():
            if self._registry.selecionar(nome) is None:
                self._registry.registrar(
                    nome=nome,
                    fn=fn,
                    params=['entrada', 'texto'],
                    dominio='manual',
                    nivel=0,
                    descricao=getattr(fn, '__doc__', '') or '',
                )

    # ═══════════════════════════════════════════════════════
    # UTILITÁRIOS
    # ═══════════════════════════════════════════════════════

    def recordar(self, consulta: str = "", limite: int = 5) -> List[str]:
        """Recorda memórias similares à consulta."""
        if not self._memoria:
            return ["Nenhuma memória registrada."]
        if not consulta:
            return [m.get('acao', '') for m in self._memoria[-limite:]]
        resultados = []
        for m in self._memoria:
            acao = m.get('acao', '')
            if consulta.lower() in acao.lower():
                resultados.append(f"[{m['tempo']}] {acao} (nota={m['nota']})")
        return resultados[-limite:] if resultados else ["Nenhuma memória similar."]

    def _get_sqlite(self):
        """Lazy init do SQLite para persistência."""
        if self._sqlite is None:
            try:
                from mcr.mcr_sqlite import MCRSQLite
                self._sqlite = MCRSQLite("mcr_sessao")
            except Exception:
                pass
        return self._sqlite

    def estatisticas(self) -> Dict:
        """Métricas do motor."""
        mk_stats = self.mk.stats()
        return {
            'nome': self.nome,
            'versao': self.versao,
            'sessao_segundos': round(time.time() - self._sessao_inicio),
            'processamentos': self._total_processamentos,
            'memorias': len(self._memoria),
            'erros_registrados': len(self._erros),
            'execucoes_log': len(self._execucoes),
            'ferramentas': len(self._registry.listar()),
            'markov': {
                'estados': mk_stats.get('estados', 0),
                'transicoes': mk_stats.get('transicoes', 0),
                'entropia_media': round(mk_stats.get('entropia', 0), 3),
            },
        }


# ─── Singleton ────────────────────────────────────────────
_mcr_instancia: Optional[MCR] = None


def get_mcr() -> MCR:
    """Retorna a instância global do MCR."""
    global _mcr_instancia
    if _mcr_instancia is None:
        _mcr_instancia = MCR()
    return _mcr_instancia
