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
from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Tuple

from mcr.paths import CACHE_DIR, ensure_dirs

# ─── Motor Markov (intacto) ─────────────────────────────────
from devia.kernel.mcr_kernel.engine import MCR as MarkovEngine
from devia.kernel.mcr_kernel.signature import MCRFingerprint

# ─── Equação MCR (intacta) ──────────────────────────────────
from mcr.equacao_mcr import calcular_ponte, classificar_tipo_ponte, get_penalidade

# ─── Registry (intacto) ─────────────────────────────────────
from mcr.registry import get_registry, MCRRegistry, ToolEntry


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
        self.fp = MCRFingerprint()

        # ─── Registry ───────────────────────────────────
        self._registry = get_registry()

        # ─── Estado interno ─────────────────────────────
        self._historico: List[Dict] = []
        self._memoria: List[Dict] = []
        self._total_processamentos = 0
        self._sessao_inicio = time.time()

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

        # ─── Bootstrap silencioso ───────────────────────
        self._bootstrap()

    # ═══════════════════════════════════════════════════════
    # BOOTSTRAP
    # ═══════════════════════════════════════════════════════

    def _bootstrap(self):
        """Inicializa o registry se vazio e registra ferramentas padrão."""
        try:
            from mcr.bootstrap import inicializar
            if len(self._registry.listar()) < 10:
                inicializar(self._registry)
        except Exception:
            pass

        self._registrar_wrappers()
        self._pre_treinar_markov()

    def _registrar_wrappers(self):
        """Cria wrappers que adaptam ferramentas reais ao padrão (entrada, texto)."""
        wrappers = {}

        # ─── Tibia: NPC ──────────────────────────────
        try:
            from mcr.golden_templates import gerar_npc_canary, salvar_npc_parametrizado
            def _gerar_npc(entrada="", texto="", **kw):
                nome = self._extrair_nome(entrada or texto)
                params = {'name': nome, 'health': 150, 'looktype': 128,
                          'greeting': 'Ola, como posso ajudar?',
                          'job_desc': f'Trabalho por aqui.'}
                codigo = gerar_npc_canary(params)
                return {'sucesso': True, 'codigo': codigo, 'entidade': nome, 'tipo': 'npc'}
            wrappers['gerar_npc_lua'] = _gerar_npc
        except Exception:
            pass

        # ─── Tibia: Monstro ──────────────────────────
        try:
            from mcr.golden_templates import gerar_monstro_parametrizado
            def _gerar_monstro(entrada="", texto="", **kw):
                nome = self._extrair_nome(entrada or texto)
                params = {'name': nome, 'health': 500, 'experience': 1000,
                          'speed': 200, 'looktype': 100, 'race': 'blood'}
                codigo = gerar_monstro_parametrizado(params)
                return {'sucesso': True, 'codigo': codigo, 'entidade': nome, 'tipo': 'monstro'}
            wrappers['gerar_monstro_lua'] = _gerar_monstro
        except Exception:
            pass

        # ─── Visual: Sprite ──────────────────────────
        try:
            from mcr.meus_olhos import MCRDiscriminador
            def _avaliar_sprite(entrada="", texto="", **kw):
                disc = MCRDiscriminador()
                return {'sucesso': True, 'discriminador': 'MCRDiscriminador pronto',
                        'descricao': 'Avaliador de qualidade de sprites'}
            wrappers['avaliar_sprite'] = _avaliar_sprite
        except Exception:
            pass

        # ─── Diálogo: Responder ──────────────────────
        try:
            def _responder(entrada="", texto="", **kw):
                msg = entrada or texto
                if not msg:
                    return {'sucesso': False, 'erro': 'Sem entrada'}
                palavras = msg.lower().split()
                return {'sucesso': True, 'resposta': f'Entendido sobre: {msg[:100]}',
                        'palavras': len(palavras)}
            wrappers['responder'] = _responder
        except Exception:
            pass

        self.registrar_ferramentas(wrappers)

    def _extrair_nome(self, texto: str) -> str:
        """Extrai nome de entidade de texto natural."""
        import re
        padroes = [
            r'(?:crie|gerar|criar|gere|novo)\s+(?:um\s+|uma\s+)?(?:npc|monstro|quest|sprite)\s+(?:de\s+|do\s+|da\s+)?["\']?(\w[\w\s]{2,30}?\w)["\']?',
            r'(?:crie|gerar|criar|gere)\s+["\']?(\w[\w\s]{2,30}?\w)["\']?',
        ]
        for padrao in padroes:
            m = re.search(padrao, texto, re.IGNORECASE)
            if m:
                nome = m.group(1).strip().title()
                return nome[:30]
        palavras = texto.split()
        for i, p in enumerate(palavras):
            if p.lower() in ('crie', 'gerar', 'criar', 'gere', 'novo', 'nova'):
                restantes = palavras[i+1:i+5]
                nomes = [w for w in restantes if w[0].isupper() or len(w) > 3]
                if nomes:
                    return ' '.join(nomes).title()[:30]
        return 'Entidade'

    # ═══════════════════════════════════════════════════════
    # AUTO-TREINAMENTO (usa capacidades PRÓPRIAS)
    # ═══════════════════════════════════════════════════════

    def auto_treinar(self):
        """Auto-treina usando módulos que JÁ EXISTEM. Zero código novo."""
        resultados = {}

        # 1. Auto-estudo: detecta gaps no KG e estuda arquivos
        try:
            from mcr.auto_curiosidade import AutoCuriosidade
            curiosidade = AutoCuriosidade()
            n = curiosidade.ciclo_de_estudo()
            resultados['auto_estudo'] = n
        except Exception as e:
            resultados['auto_estudo_erro'] = str(e)[:80]

        # 2. Treino de diálogos: alimenta Markov com falas de NPC
        try:
            from mcr.dialogue_trainer import DialogueTrainer
            from mcr.dialogue_miner import minerar_lote, salvar_dialogos
            from mcr.paths import CANARY_NPC_DIR
            npcs = minerar_lote(CANARY_NPC_DIR)
            if npcs:
                salvar_dialogos(npcs)
                treinador = DialogueTrainer()
                stats = treinador.treinar_com_dialogos(npcs)
                resultados['dialogos'] = stats
        except Exception as e:
            resultados['dialogos_erro'] = str(e)[:80]

        # 3. Mineração de padrões: extrai estruturas de código
        try:
            from mcr.pattern_miner import miner_lua_files
            from mcr.paths import CANARY_NPC_DIR
            padroes = miner_lua_files(CANARY_NPC_DIR)
            if padroes:
                resultados['padroes_extraidos'] = len(padroes)
        except Exception as e:
            resultados['padroes_erro'] = str(e)[:80]

        # 4. Pré-treina o Markov com dados minerados
        self._pre_treinar_markov()

        return resultados

    def _pre_treinar_markov(self):
        """Alimenta o MCR com exemplos DIVERSOS usando estados compostos.

        O MCR aprende SOZINHO:
        - "tipo=npc" + qualquer tema → gerar_npc
        - "tipo=monstro" + qualquer tema → gerar_monstro
        - Sem tipo explícito: tema=dragao/ork → gerar_monstro
        - Sem tipo explícito: tema=ferreiro/vendedor → gerar_npc
        """
        seeds = [
            # ─── Tipo EXPLÍCITO: NPC (sempre gerar_npc) ───
            ("crie um npc ferreiro", "gerar_npc"),
            ("crie um npc dragao", "gerar_npc"),
            ("crie um npc vendedor", "gerar_npc"),
            ("crie um npc guarda", "gerar_npc"),
            ("crie um npc mago", "gerar_npc"),
            ("gere um npc dragao", "gerar_npc"),
            ("gere um npc mercador", "gerar_npc"),
            ("faca um npc orc", "gerar_npc"),
            ("faca um npc demonio", "gerar_npc"),

            # ─── Tipo EXPLÍCITO: Monstro (sempre gerar_monstro) ───
            ("crie um monstro dragao", "gerar_monstro"),
            ("crie um monstro vendedor", "gerar_monstro"),
            ("crie um monstro orc", "gerar_monstro"),
            ("gere um monstro ferreiro", "gerar_monstro"),
            ("gere um monstro demonio", "gerar_monstro"),
            ("faca um monstro guarda", "gerar_monstro"),

            # ─── Tipo EXPLÍCITO: Quest ───
            ("crie uma quest", "gerar_quest"),
            ("crie uma quest para o ferreiro", "gerar_quest"),
            ("gere uma quest", "gerar_quest"),
            ("nova quest", "gerar_quest"),

            # ─── Tipo EXPLÍCITO: Sprite ───
            ("crie um sprite de espada", "gerar_sprite"),
            ("crie um sprite", "gerar_sprite"),
            ("gere um sprite de escudo", "gerar_sprite"),
            ("gere uma imagem", "gerar_sprite"),

            # ─── SEM tipo explícito: tema decide ───
            # Temas de MONSTRO
            ("crie um dragao", "gerar_monstro"),
            ("crie um dragao de fogo", "gerar_monstro"),
            ("gere um dragao", "gerar_monstro"),
            ("gere um dragao de fogo", "gerar_monstro"),
            ("faca um dragao", "gerar_monstro"),
            ("gere um orc", "gerar_monstro"),
            ("faca um orc guerreiro", "gerar_monstro"),
            ("crie um demonio", "gerar_monstro"),
            ("gere um demonio de fogo", "gerar_monstro"),

            # Temas de NPC
            ("crie um ferreiro", "gerar_npc"),
            ("crie um ferreiro anao", "gerar_npc"),
            ("gere um vendedor", "gerar_npc"),
            ("faca um guarda", "gerar_npc"),
            ("crie um mago", "gerar_npc"),
            ("crie um mercador elfico", "gerar_npc"),
            ("gere um bibliotecario", "gerar_npc"),

            # ─── Perguntas ───
            ("explique o que e markov", "responder"),
            ("o que e entropia", "responder"),
            ("como funciona o mcr", "responder"),
            ("qual a diferenca entre npc e monstro", "responder"),
        ]

        for entrada, acao in seeds:
            estado = self._fingerprint_chave(entrada)
            for _ in range(3):
                self.mk.aprender(estado, acao)

    # ═══════════════════════════════════════════════════════
    # CICLO COGNITIVO PRINCIPAL
    # ═══════════════════════════════════════════════════════

    def processar(self, entrada: str) -> Dict:
        """Ciclo cognitivo completo: percebe → decide → executa → avalia → aprende.

        A MESMA lógica para Tibia, Visual, Áudio, qualquer domínio.
        O MCR decide o que fazer baseado no fingerprint da entrada.
        """
        t0 = time.time()
        self._total_processamentos += 1

        # ─── 1. PERCEBER ───────────────────────────────
        estado = self._perceber(entrada)

        # ─── 2. DECIDIR ────────────────────────────────
        acao, confianca = self._decidir(estado)

        # ─── 3. EXECUTAR ───────────────────────────────
        resultado = self._executar(acao, entrada)

        # ─── 4. AVALIAR (Equação MCR) ──────────────────
        nota = self._avaliar(entrada, resultado, acao)

        # ─── 5. APRENDER ───────────────────────────────
        self._aprender(estado, acao, nota)

        # ─── Montar resposta ───────────────────────────
        tempo_total = round(time.time() - t0, 3)

        return {
            'sucesso': resultado.get('sucesso', False),
            'acao': acao,
            'confianca': round(confianca, 3),
            'nota': round(nota, 3),
            'resultado': resultado,
            'tempo': tempo_total,
            'entrada': entrada[:200],
        }

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 1: PERCEBER
    # ═══════════════════════════════════════════════════════

    def _perceber(self, entrada: str) -> str:
        """Gera fingerprint da entrada como chave Markov."""
        return self._fingerprint_chave(entrada)

    def _fingerprint_chave(self, texto: str) -> str:
        """Gera chave Markov composta: fingerprint + palavras extraídas.
        
        Usa compose_state para criar estado rico com múltiplos sinais.
        O MCR aprende sozinho quais combinações → qual ação.
        """
        import re
        t = texto.lower().strip()
        
        # Sinal 1: fingerprint 8D (estrutura do texto)
        fp = MCRFingerprint.gerar(t)
        fp_compact = ".".join(str(round(x, 1)) for x in fp[:4])
        
        # Sinal 2: palavras extraídas (comando + tipo de entidade)
        palavras = re.findall(r'[a-zà-ÿ0-9]{2,}', t)
        
        # Sinal 3: tipo de entidade explícito (npc, monstro, quest, sprite)
        tipo_explicito = ""
        for i, p in enumerate(palavras):
            if p in ('npc', 'monstro', 'monster', 'quest', 'missao', 'sprite', 'imagem'):
                tipo_explicito = p
                break
        
        # Sinal 4: primeira palavra substantiva longa (provavelmente o tema)
        tema = ""
        stopwords = {'crie', 'criar', 'gere', 'gerar', 'faca', 'fazer', 'um', 'uma',
                     'novo', 'nova', 'para', 'com', 'que', 'venda', 'de', 'do', 'da'}
        for p in palavras:
            if p not in stopwords and len(p) > 3:
                tema = p
                break
        
        # Compõe estado: todos os sinais juntos
        # O Markov aprende quais combinações importam
        ctx = {
            'cmd': palavras[0] if palavras else '',
            'tipo': tipo_explicito,
            'tema': tema,
            'fp': fp_compact,
        }
        
        # Estado composto: Markov vê todas as combinações
        # Ex: "crie|npc|ferreiro|5.2.1.8.0.3.2.1" → gerar_npc
        # Ex: "gere||dragao|3.4.2.1.0.8.4.2" → gerar_monstro
        estado = f"{ctx['cmd']}|{ctx['tipo']}|{ctx['tema']}|{ctx['fp']}"
        return estado

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 2: DECIDIR
    # ═══════════════════════════════════════════════════════

    def _decidir(self, estado: str) -> Tuple[str, float]:
        """Markov decide a ação. Se confiança baixa, busca estado similar."""
        acao, conf = self.mk.predizer(estado)

        if acao and conf > 0.15:
            return str(acao), conf

        # Fallback: busca estado mais similar por componentes
        if self.mk.transicoes:
            partes_consulta = estado.split('|')
            melhor_estado = None
            melhor_sim = 0
            
            for est in self.mk.transicoes:
                partes_est = est.split('|')
                # Similaridade por componentes compartilhados
                if len(partes_consulta) >= 3 and len(partes_est) >= 3:
                    # cmd match: 20%
                    cmd_match = 1.0 if partes_consulta[0] == partes_est[0] else 0.0
                    # tipo match: 50% (MUITO importante)
                    tipo_match = 1.0 if partes_consulta[1] == partes_est[1] else 0.0
                    # tema match: 30%
                    tema_match = 1.0 if partes_consulta[2] == partes_est[2] else 0.0
                    
                    sim = 0.2 * cmd_match + 0.5 * tipo_match + 0.3 * tema_match
                    if sim > melhor_sim:
                        melhor_sim = sim
                        melhor_estado = est
            
            if melhor_estado and melhor_sim > 0.4:
                acao2, conf2 = self.mk.predizer(melhor_estado)
                if acao2:
                    return str(acao2), conf2 * melhor_sim

        return "gerar_npc", 0.1

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

    def _avaliar(self, entrada: str, resultado: Dict, acao: str) -> float:
        """Avalia o resultado usando a Equação MCR.

        divergência: quão único/novo é o resultado
        especificidade: quão preciso/detalhado é
        profundidade: quão complexo/profundo é
        """
        saida = str(resultado.get('saida', resultado.get('erro', '')))

        # Divergência: diferença entre entrada e saída (Jaccard)
        fp_entrada = MCRFingerprint.gerar(entrada)
        fp_saida = MCRFingerprint.gerar(saida)
        divergencia = self._jaccard_fingerprints(fp_entrada, fp_saida)

        # Especificidade: mais caracteres = mais específico
        especificidade = min(1.0, len(saida) / 2000.0)

        # Profundidade: entropia da saída (mais diversidade = mais profundo)
        profundidade = self._entropia_texto(saida)

        # Equação MCR
        nota = calcular_ponte(divergencia, especificidade, profundidade)
        tipo = classificar_tipo_ponte(nota)
        penalidade = get_penalidade(tipo)
        nota_final = nota * (1.0 - penalidade)

        return max(0.0, min(1.0, nota_final))

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

    def _extrair_nome(self, texto: str) -> str:
        """Extrai nome de entidade de texto natural."""
        import re
        # Remove palavras de comando primeiro
        cmd = r'\b(crie|criar|gere|gerar|um|uma|novo|nova|npc|monstro|monster|quest|sprite|de|do|da|que|venda|com|para)\b'
        limpo = re.sub(cmd, ' ', texto, flags=re.IGNORECASE)
        limpo = re.sub(r'\s+', ' ', limpo).strip()
        palavras = [p for p in limpo.split() if len(p) > 2]
        if palavras:
            nome = ' '.join(palavras[:4]).title()
            return nome[:30]
        return 'Entidade'

    # ═══════════════════════════════════════════════════════
    # ESTÁGIO 5: APRENDER
    # ═══════════════════════════════════════════════════════

    def _aprender(self, estado: str, acao: str, nota: float):
        """Aprende a transição. Reforça se nota alta."""
        self.mk.aprender(estado, acao)
        if nota > 0.5:
            self.mk.aprender(estado, acao)
        if nota > 0.7:
            self.mk.aprender(estado, acao)

        # Registra no histórico
        self._historico.append({
            'estado': estado[:100],
            'acao': acao,
            'nota': round(nota, 3),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        })
        if len(self._historico) > 500:
            self._historico = self._historico[-500:]

        # Memória narrativa
        self._memoria.append({
            'acao': acao,
            'nota': round(nota, 3),
            'tempo': time.strftime('%Y-%m-%d %H:%M:%S'),
        })
        if len(self._memoria) > 200:
            self._memoria = self._memoria[-200:]

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

    def estatisticas(self) -> Dict:
        """Métricas do motor."""
        mk_stats = self.mk.stats()
        return {
            'nome': self.nome,
            'versao': self.versao,
            'sessao_segundos': round(time.time() - self._sessao_inicio),
            'processamentos': self._total_processamentos,
            'memorias': len(self._memoria),
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
