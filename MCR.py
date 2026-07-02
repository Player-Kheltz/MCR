#!/usr/bin/env python3
"""MCR — Modelo Cognitivo de Reconhecimento.
1 algoritmo, N níveis, memória, cache, sessão, emergência.

Unifica:
  - Núcleo Markov (MCR, ByteUtils)
  - Emergência (Conexao, Motor, AutoLoop)
  - Memória (Session, Buffer)
  - Cache adaptativo (Threshold, Entropia)
  - Fragmentação (Fragmento, Fragmentador)
  - 8 níveis registrados

Equação MCR:
    NOTA = (BYTE + PALAVRA + TOKEN) × PENALIDADE
    PONTE_OTIMA = divergencia×5 + especificidade×3 + profundidade×2

Uso:
    motor = MCRMotor()
    motor.alimentar("SPA é progressão", "spa")
    auto = MCRAutoLoop(motor)
    resultado = auto.loop("spa", "arvore_natal")
"""
import os, json, math, hashlib, re, time as _time
from collections import Counter
from typing import Dict, List, Tuple, Optional, Set, Any
from statistics import median

# ═══════════════════════════════════════════════════════════════
# CONSTANTES GLOBAIS
# ═══════════════════════════════════════════════════════════════

CONECTORES = {
    'a', 'e', 'o', 'de', 'da', 'do', 'em', 'com', 'para', 'por',
    'se', 'no', 'na', 'um', 'uma', 'os', 'as', 'ao', 'aos', 'das',
    'dos', 'num', 'numa', 'pelo', 'pela', 'pelos', 'pelas', 'que',
    'como', 'mas', 'mais', 'ou', 'nem', 'tambem', 'so', 'só',
    'ja', 'já', 'la', 'lá', 'ca', 'cá', 'ali', 'aqui',
}

_NIVEIS: Dict[str, dict] = {}

def registrar_nivel(nome: str, config: dict):
    _NIVEIS[nome] = {
        'nome': config.get('nome', nome),
        'tokenizar': config.get('tokenizar', lambda d: [str(d)]),
        'comparar': config.get('comparar', lambda a, b: 1.0 if a == b else 0.0),
    }

# ─── 8 NÍVEIS ────────────────────────────────────────────────

registrar_nivel("byte", {
    'nome': 'byte',
    'tokenizar': lambda d: [f"B:{b:02x}" for b in (d.encode() if isinstance(d, str) else d)],
})
registrar_nivel("palavra", {
    'nome': 'palavra',
    'tokenizar': lambda t: t.split() if isinstance(t, str) else [str(t)],
})
registrar_nivel("token", {
    'nome': 'token',
    'tokenizar': lambda t: [p[0].upper() for p in t.split() if p] if isinstance(t, str) else [str(t)[:1]],
})
registrar_nivel("intencao", {
    'nome': 'intencao',
    'tokenizar': lambda e: [str(e)],
})
registrar_nivel("decisao", {
    'nome': 'decisao',
    'tokenizar': lambda e: [str(e)],
})
registrar_nivel("acao", {
    'nome': 'acao',
    'tokenizar': lambda e: [str(e)],
})
registrar_nivel("assinatura", {
    'nome': 'assinatura',
    'tokenizar': lambda d: (
        [f"B:{b:02x}" for b in (d.encode() if isinstance(d, str) else bytes(d)[:2000])]
        if d else []
    ),
})
registrar_nivel("qualidade", {
    'nome': 'qualidade',
    'tokenizar': lambda sol: (
        [f"B:{b:02x}" for b in (sol.encode() if isinstance(sol, str) else bytes(sol)[:200])]
        if sol else []
    ),
})

# ═══════════════════════════════════════════════════════════════
# MCR — Markov Universal
# ═══════════════════════════════════════════════════════════════

class MCR:
    """Cadeia de Markov universal para QUALQUER nível.
    1 classe, N níveis, 0 hardcode."""
    def __init__(self, nome: str = ""):
        self.nome = nome
        self.transicoes: Dict[str, Dict[str, int]] = {}
        self.freq: Dict[str, int] = {}
        self.total: int = 0
        self._entropia_cache: Dict[str, float] = {}

    def aprender(self, a: str, b: str):
        a, b = str(a), str(b)
        if a not in self.transicoes:
            self.transicoes[a] = {}
            self.freq[a] = 0
        self.transicoes[a][b] = self.transicoes[a].get(b, 0) + 1
        self.freq[a] += 1
        self.total += 1
        self._entropia_cache.pop(a, None)

    def aprender_sequencia(self, seq: List[str]):
        for i in range(len(seq) - 1):
            self.aprender(seq[i], seq[i + 1])

    def aprender_batch(self, sequencias: List[List[str]]):
        temp: Dict[str, Dict[str, int]] = {}
        temp_freq: Dict[str, int] = {}
        for seq in sequencias:
            for i in range(len(seq) - 1):
                a, b = str(seq[i]), str(seq[i + 1])
                if a not in temp:
                    temp[a] = {}
                    temp_freq[a] = 0
                temp[a][b] = temp[a].get(b, 0) + 1
                temp_freq[a] += 1
        for a, prox in temp.items():
            if a not in self.transicoes:
                self.transicoes[a] = {}
                self.freq[a] = 0
            for b, count in prox.items():
                self.transicoes[a][b] = self.transicoes[a].get(b, 0) + count
                self.freq[a] += count
                self.total += count
            self._entropia_cache.pop(a, None)

    def predizer(self, a: str) -> Tuple[Optional[str], float]:
        a = str(a)
        if a not in self.transicoes or not self.transicoes[a]:
            return (None, 0.0)
        melhor = max(self.transicoes[a], key=self.transicoes[a].get)
        conf = self.transicoes[a][melhor] / self.freq[a]
        return (melhor, conf)

    def predizer_n(self, a: str, n: int = 3) -> List[Tuple[str, float]]:
        a = str(a)
        if a not in self.transicoes:
            return []
        ordenados = sorted(self.transicoes[a].items(), key=lambda x: -x[1])
        total = self.freq[a]
        return [(tok, cnt / total) for tok, cnt in ordenados[:n]]

    def gerar(self, semente: str, passos: int = 10) -> List[str]:
        seq = [semente]
        atual = semente
        for _ in range(passos):
            prox, conf = self.predizer(atual)
            if prox is None or conf < 0.01:
                break
            seq.append(prox)
            atual = prox
        return seq

    def entropia(self, a: str) -> float:
        a = str(a)
        if a in self._entropia_cache:
            return self._entropia_cache[a]
        if a not in self.transicoes or not self.transicoes[a]:
            return 1.0
        total = self.freq[a]
        h = -sum((c / total) * math.log2(c / total) for c in self.transicoes[a].values())
        self._entropia_cache[a] = h
        return h

    def entropia_media(self) -> float:
        if not self.freq:
            return 1.0
        return sum(self.entropia(e) for e in self.freq) / len(self.freq)

    def jaccard(self, outra: 'MCR') -> float:
        ea = set(self.freq.keys())
        eb = set(outra.freq.keys())
        if not ea or not eb:
            return 0.0
        inter = ea & eb; uniao = ea | eb
        return len(inter) / len(uniao)

    def jaccard_transicoes(self, outra: 'MCR') -> float:
        ta = set(f"{a}→{b}" for a in self.transicoes for b in self.transicoes[a])
        tb = set(f"{a}→{b}" for a in outra.transicoes for b in outra.transicoes[a])
        if not ta or not tb:
            return 0.0
        inter = ta & tb; uniao = ta | tb
        return len(inter) / len(uniao)

    def stats(self) -> Dict:
        return {
            'nome': self.nome,
            'estados': len(self.freq),
            'transicoes': sum(len(t) for t in self.transicoes.values()),
            'total_observacoes': self.total,
            'entropia_media': round(self.entropia_media(), 3),
        }

    def __repr__(self) -> str:
        s = self.stats()
        return f"MCR[{self.nome}]: {s['estados']} estados, {s['transicoes']} transicoes, H={s['entropia_media']}"


# ═══════════════════════════════════════════════════════════════
# MCRByteUtils — Utilitários de byte
# ═══════════════════════════════════════════════════════════════

class MCRByteUtils:
    @staticmethod
    def transicoes_bytes(texto: str, max_bytes: int = 500) -> Set[str]:
        dados = texto.encode('utf-8')[:max_bytes]
        return {f"{dados[i]:02x}→{dados[i+1]:02x}" for i in range(len(dados) - 1)}

    @staticmethod
    def jaccard_bytes(texto_a: str, texto_b: str) -> float:
        ta = MCRByteUtils.transicoes_bytes(texto_a)
        tb = MCRByteUtils.transicoes_bytes(texto_b)
        if not ta or not tb:
            return 0.0
        inter = ta & tb; uniao = ta | tb
        return len(inter) / len(uniao)

    @staticmethod
    def similaridade_cosseno(texto_a: str, texto_b: str, max_bytes: int = 500) -> float:
        ba = texto_a.encode('utf-8')[:max_bytes]
        bb = texto_b.encode('utf-8')[:max_bytes]
        fa: Dict[str, int] = {}
        fb: Dict[str, int] = {}
        for i in range(len(ba) - 1):
            t = f"{ba[i]:02x}→{ba[i+1]:02x}"; fa[t] = fa.get(t, 0) + 1
        for i in range(len(bb) - 1):
            t = f"{bb[i]:02x}→{bb[i+1]:02x}"; fb[t] = fb.get(t, 0) + 1
        todas = set(fa.keys()) | set(fb.keys())
        dot = sum(fa.get(t, 0) * fb.get(t, 0) for t in todas)
        na = math.sqrt(sum(v * v for v in fa.values()))
        nb = math.sqrt(sum(v * v for v in fb.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    @staticmethod
    def entropia_bytes(dados) -> float:
        if isinstance(dados, str):
            dados = dados.encode('utf-8')[:500]
        else:
            dados = bytes(dados)[:500]
        if len(dados) < 2:
            return 0.0
        freq = Counter(dados)
        n = len(dados)
        return -sum((c / n) * math.log2(c / n) for c in freq.values())

    @staticmethod
    def fingerprint(texto: str, dimensoes: int = 8) -> List[float]:
        dados = texto.encode('utf-8')[:500]
        if not dados:
            return [0.0] * dimensoes
        buckets = [0.0] * dimensoes
        for b in dados:
            buckets[b % dimensoes] += 1.0
        total = sum(buckets) or 1
        return [round(b / total * 10, 3) for b in buckets]


# ═══════════════════════════════════════════════════════════════
# MCRSignatureMultidimensional — Assinatura N-dimensional
# ═══════════════════════════════════════════════════════════════

class MCRSignatureMultidimensional:
    """Assinatura N-dimensional de QUALQUER evento.

    Captura todas as dimensoes de uma ocorrencia simultaneamente:
      byte, contexto, entropia, frequencia, posicao, fonte, ciclo

    O fingerprint nao e uma projecao 1D do byte.
    E um vetor N-dimensional que carrega todas as dimensoes
    da realidade daquele evento.

    Uso:
        sig = MCRSignatureMultidimensional.extrair(byte_val, offset, total, mk_byte)
        sig2 = MCRSignatureMultidimensional.extrair(outro_byte, ...)
        sim = MCRSignatureMultidimensional.similaridade(sig, sig2)
    """

    DIMENSOES = [
        'byte_freq',       # 0: frequencia relativa do byte (0-1)
        'byte_entropia',   # 1: entropia local do byte (0-1)
        'byte_transicoes', # 2: quantas saidas o byte tem (0-1)
        'offset_normal',   # 3: posicao normalizada na sequencia (0-1)
        'contexto_anterior',# 4: byte anterior normalizado (0-1)
        'contexto_proximo',# 5: byte proximo normalizado (0-1)
        'ciclo',           # 6: ciclo de processamento (0-1)
        'fonte',           # 7: tipo de fonte (0-1)
    ]

    N_DIMS = len(DIMENSOES)

    @staticmethod
    def extrair(valor_byte: int, offset: int = 0, total: int = 1,
                mk_byte: MCR = None, byte_anterior: int = None,
                byte_proximo: int = None, ciclo: int = 0,
                fonte: str = 'desconhecida') -> List[float]:
        """Extrai assinatura N-dim de um unico byte num contexto."""
        sig = [0.0] * MCRSignatureMultidimensional.N_DIMS

        # D0: frequencia relativa
        estado = f"B:{valor_byte:02x}"
        if mk_byte and estado in mk_byte.freq:
            sig[0] = mk_byte.freq[estado] / max(mk_byte.total, 1)

        # D1: entropia local (imprevisibilidade)
        if mk_byte and estado in mk_byte.transicoes:
            sig[1] = mk_byte.entropia(estado) / 8.0

        # D2: diversidade de transicoes
        if mk_byte and estado in mk_byte.transicoes:
            sig[2] = len(mk_byte.transicoes[estado]) / 256.0

        # D3: posicao na sequencia
        sig[3] = offset / max(total, 1)

        # D4: byte anterior (contexto imediato)
        if byte_anterior is not None:
            sig[4] = byte_anterior / 255.0

        # D5: byte proximo (contexto imediato)
        if byte_proximo is not None:
            sig[5] = byte_proximo / 255.0

        # D6: ciclo de processamento
        sig[6] = min(1.0, ciclo / 100.0)

        # D7: tipo de fonte (hash normalizado)
        sig[7] = (hash(fonte) % 10000) / 10000.0

        return sig

    @staticmethod
    def extrair_sequencia(sequencia: bytes, mk_byte: MCR = None,
                          ciclo: int = 0, fonte: str = '') -> List[List[float]]:
        """Extrai assinatura N-dim para CADA byte de uma sequencia."""
        n = len(sequencia)
        assinaturas = []
        for i in range(n):
            ant = sequencia[i - 1] if i > 0 else None
            prox = sequencia[i + 1] if i < n - 1 else None
            sig = MCRSignatureMultidimensional.extrair(
                sequencia[i], i, n, mk_byte, ant, prox, ciclo, fonte)
            assinaturas.append(sig)
        return assinaturas

    @staticmethod
    def similaridade(sig_a: List[float], sig_b: List[float]) -> float:
        """Cosseno entre duas assinaturas N-dim.
        Vetores identicos (inclusive zero) retornam 1.0."""
        if len(sig_a) != len(sig_b):
            return 0.0
        dot = sum(a * b for a, b in zip(sig_a, sig_b))
        na = math.sqrt(sum(a * a for a in sig_a))
        nb = math.sqrt(sum(b * b for b in sig_b))
        if na == 0 and nb == 0:
            return 1.0  # ambos zero = identicos
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    @staticmethod
    def similaridade_sequencia(ass_a: List[List[float]],
                                ass_b: List[List[float]]) -> float:
        """Similaridade media entre duas sequencias de assinaturas."""
        if not ass_a or not ass_b:
            return 0.0
        min_len = min(len(ass_a), len(ass_b))
        if min_len == 0:
            return 0.0
        sims = [MCRSignatureMultidimensional.similaridade(ass_a[i], ass_b[i])
                for i in range(min_len)]
        return sum(sims) / len(sims)

    @staticmethod
    def fingerprint_sequencia(assinaturas: List[List[float]]) -> List[float]:
        """Reduz N assinaturas a um unico fingerprint N-dim (media)."""
        if not assinaturas:
            return [0.0] * MCRSignatureMultidimensional.N_DIMS
        n = len(assinaturas)
        return [sum(sig[d] for sig in assinaturas) / n
                for d in range(MCRSignatureMultidimensional.N_DIMS)]


# ═══════════════════════════════════════════════════════════════
# MCRThreshold — Thresholds adaptativos
# ═══════════════════════════════════════════════════════════════

class MCRThreshold:
    """Threshold descoberto por MEDIANA dos dados, nunca fixo."""
    def __init__(self, nome: str = "threshold"):
        self.mk = MCR(nome)
        self.observacoes: List[float] = []

    def observar(self, valor: float):
        self.observacoes.append(valor)
        self.mk.aprender(f"VAL:{int(valor*100)}", "OBS")

    def calcular(self, multiplicador: float = 1.0) -> float:
        if len(self.observacoes) < 3:
            return 0.5
        return median(self.observacoes) * multiplicador

    def obter(self, chave: str, fallback: float = 0.5) -> float:
        pred = self.mk.predizer(f"THR:{chave}")
        if pred[0] is not None and pred[1] > 0.3:
            try:
                return int(pred[0]) / 100.0
            except (ValueError, TypeError):
                pass
        if len(self.observacoes) >= 3:
            return median(self.observacoes)
        return fallback

    def aprender(self, chave: str, valor: float):
        self.mk.aprender(f"THR:{chave}", f"{int(valor*100)}")
        self.observar(valor)


# ═══════════════════════════════════════════════════════════════
# MCREntropia — Detector de loops
# ═══════════════════════════════════════════════════════════════

class MCREntropia:
    """Detecta loops. Internamente usa MCR."""
    def __init__(self, nome: str = "entropia"):
        self.mk = MCR(nome)
        self.historico: List[float] = []

    def alimentar(self, token: str):
        self.mk.aprender(f"T:{str(token)[:50]}", "V")
        h = self.mk.entropia(f"T:{str(token)[:50]}")
        self.historico.append(h)
        if len(self.historico) > 100:
            self.historico = self.historico[-50:]

    def _entropia_local(self) -> float:
        if len(self.historico) < 3:
            return 1.0
        return sum(self.historico[-10:]) / min(10, len(self.historico))

    def esta_em_loop(self) -> bool:
        return self._entropia_local() < 0.3

    def variacao(self) -> float:
        if len(self.historico) < 5:
            return 1.0
        recentes = self.historico[-5:]
        return max(recentes) - min(recentes) if max(recentes) > 0 else 0


# ═══════════════════════════════════════════════════════════════
# MCRBuffer — Buffer de operações
# ═══════════════════════════════════════════════════════════════

class MCRBuffer:
    """Buffer de operações. Acumula e persiste em lote.
    Evita operações individuais frequentes no armazenamento."""
    def __init__(self, nome: str = "buffer", limite: int = 20):
        self.nome = nome
        self._buffer: List[Dict] = []
        self.limite = limite
        self.mk = MCR(f"buffer_{nome}")
        self.total_operacoes = 0
        self.total_flushes = 0

    def adicionar(self, item: Dict):
        self._buffer.append(item)
        self.total_operacoes += 1
        self.mk.aprender("BUF:ADD", f"size:{len(self._buffer)}")
        if len(self._buffer) >= self.limite:
            return self.flush()
        return False

    def flush(self) -> bool:
        if not self._buffer:
            return False
        n = len(self._buffer)
        self.mk.aprender("BUF:FLUSH", f"{n} itens")
        self._buffer.clear()
        self.total_flushes += 1
        return True

    def pendentes(self) -> int:
        return len(self._buffer)

    def stats(self) -> Dict:
        return {
            'nome': self.nome,
            'buffer_atual': len(self._buffer),
            'limite': self.limite,
            'total_operacoes': self.total_operacoes,
            'total_flushes': self.total_flushes,
        }


# ═══════════════════════════════════════════════════════════════
# MCRSession — Memória de sessão
# ═══════════════════════════════════════════════════════════════

class MCRSession:
    """Memória de sessão: histórico, checkpoint, auto-retomada.

    Armazena:
      - .mcr_conversa.jsonl (histórico de interações)
      - .mcr_estado.json (checkpoint para resume)
    """
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(__file__), '..', 'cache')
        self._base = base_dir
        self._conv_path = os.path.join(self._base, '.mcr_conversa.jsonl')
        self._estado_path = os.path.join(self._base, '.mcr_estado.json')
        self._historico: List[Dict] = []
        self._ultima_pergunta = ''
        self._ultima_resposta = ''
        self.mk = MCR("session")

    def registrar(self, pergunta: str, resposta: str, metadados: Dict = None):
        """Registra uma interação no histórico + arquivo de conversa."""
        entry = {
            'pergunta': pergunta,
            'resposta': resposta[:200],
            'timestamp': _time.time(),
            'metadados': metadados or {},
        }
        self._ultima_pergunta = pergunta
        self._ultima_resposta = resposta
        self._historico.append(entry)

        os.makedirs(self._base, exist_ok=True)
        try:
            with open(self._conv_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except (OSError, IOError):
            pass

        self.mk.aprender(f"CONV:{pergunta[:30]}", f"len:{len(resposta)}")

    def salvar_checkpoint(self, estado_extra: Dict = None):
        """Salva checkpoint completo da sessão."""
        estado = {
            'timestamp': _time.time(),
            'ultima_pergunta': self._ultima_pergunta,
            'ultima_resposta': self._ultima_resposta,
            'n_historico': len(self._historico),
            'estado_extra': estado_extra or {},
        }
        os.makedirs(self._base, exist_ok=True)
        try:
            with open(self._estado_path, 'w', encoding='utf-8') as f:
                json.dump(estado, f, ensure_ascii=False, indent=2)
            self.mk.aprender("CHECKPOINT", f"ok:{len(self._historico)}")
            return True
        except (OSError, IOError):
            return False

    def carregar_checkpoint(self) -> Optional[Dict]:
        """Carrega checkpoint da última sessão."""
        if not os.path.exists(self._estado_path):
            return None
        try:
            with open(self._estado_path, 'r', encoding='utf-8') as f:
                estado = json.load(f)
            self._ultima_pergunta = estado.get('ultima_pergunta', '')
            self._ultima_resposta = estado.get('ultima_resposta', '')
            return estado
        except (OSError, IOError, json.JSONDecodeError):
            return None

    def auto_retomar(self) -> Optional[Dict]:
        """Auto-retomada: se havia checkpoint, carrega e retorna."""
        estado = self.carregar_checkpoint()
        if estado:
            self.mk.aprender("RETOMADA", f"pergunta:{estado.get('ultima_pergunta','')[:30]}")
        return estado

    def historico_recente(self, n: int = 5) -> List[Dict]:
        return self._historico[-n:]

    def stats(self) -> Dict:
        return {
            'total_interacoes': len(self._historico),
            'ultima_pergunta': self._ultima_pergunta[:40],
            'checkpoint_existe': os.path.exists(self._estado_path),
            'conversa_tamanho': os.path.getsize(self._conv_path) if os.path.exists(self._conv_path) else 0,
        }


# ═══════════════════════════════════════════════════════════════
# MCRFragmento / MCRFragmentador — Execução fragmentada
# ═══════════════════════════════════════════════════════════════

class MCRFragmento:
    """Um fragmento de processamento independente."""
    def __init__(self, nome: str, funcao, args: Dict = None):
        self.nome = nome
        self.funcao = funcao
        self.args = args or {}
        self.resultado = None
        self.erro = None
        self.tempo = 0.0
        self.sucesso = False

    def executar(self):
        t0 = _time.time()
        try:
            self.resultado = self.funcao(**self.args)
            self.sucesso = True
        except Exception as e:
            self.erro = str(e)[:200]
        self.tempo = _time.time() - t0
        return self.sucesso


class MCRFragmentador:
    """Fragmenta um ciclo em partes executáveis e rastreáveis."""
    def __init__(self, nome: str = "fragmentador"):
        self.fragmentos: List[MCRFragmento] = []
        self.mk = MCR(nome)
        self.tempo_total = 0.0
        self.total_sucesso = 0
        self.total_falha = 0

    def adicionar(self, nome: str, funcao, args: Dict = None):
        self.fragmentos.append(MCRFragmento(nome, funcao, args))

    def executar_todos(self) -> List[MCRFragmento]:
        self.tempo_total = 0.0
        for f in self.fragmentos:
            f.executar()
            self.tempo_total += f.tempo
            if f.sucesso:
                self.total_sucesso += 1
            else:
                self.total_falha += 1
            self.mk.aprender(
                f"FRAG:{f.nome}",
                f"{'OK' if f.sucesso else 'FALHA'}:{f.tempo:.2f}s"
            )
        return self.fragmentos

    def limpar(self):
        self.fragmentos.clear()

    def stats(self) -> Dict:
        return {
            'fragmentos': len(self.fragmentos),
            'tempo_total': round(self.tempo_total, 3),
            'sucesso': self.total_sucesso,
            'falha': self.total_falha,
            'taxa': round(self.total_sucesso / max(self.total_sucesso + self.total_falha, 1), 3),
        }


# ═══════════════════════════════════════════════════════════════
# MCRConexao — MarkovCruzado (ponte ótima entre cadeias)
# ═══════════════════════════════════════════════════════════════

class MCRConexao:
    """Analisa entropia cruzada entre cadeias de Markov.

    Encontra a PONTE ÓTIMA que MAXIMIZA:
        divergencia × especificidade × profundidade
    """
    def __init__(self, motor: 'MCRMotor'):
        self.motor = motor

    def analisar(self, topico_a: str, topico_b: str) -> Dict:
        if topico_a not in self.motor.topicos or topico_b not in self.motor.topicos:
            return {'erro': 'topico nao encontrado', 'pontes': [], 'melhor': None}

        conteudo_a = self.motor.topicos[topico_a].get('conteudo', set())
        conteudo_b = self.motor.topicos[topico_b].get('conteudo', set())
        candidatas = conteudo_a & conteudo_b

        if not candidatas:
            return self._analisar_sem_compartilhadas(topico_a, topico_b)

        pontes = []
        for palavra in candidatas:
            score, detalhes = self._avaliar_ponte(topico_a, topico_b, palavra)
            pontes.append({'palavra': palavra, 'score': round(score, 2), **detalhes})

        pontes.sort(key=lambda x: -x['score'])
        return {
            'total_candidatas': len(candidatas),
            'divergencia_media': round(
                sum(p.get('divergencia', 0) for p in pontes) / len(pontes), 3
            ) if pontes else 0,
            'pontes': pontes,
            'melhor': pontes[0] if pontes else None,
        }

    def melhor_ponte(self, topico_a: str, topico_b: str) -> Optional[Dict]:
        return self.analisar(topico_a, topico_b).get('melhor')

    def _avaliar_ponte(self, topico_a: str, topico_b: str, palavra: str
                       ) -> Tuple[float, Dict]:
        mk_a = self.motor.topicos[topico_a].get('markov_palavra')
        mk_b = self.motor.topicos[topico_b].get('markov_palavra')
        if not mk_a or not mk_b:
            return 0.0, {'erro': 'no markov_palavra'}

        # DIVERGÊNCIA (peso 5)
        trans_a = set(mk_a.transicoes.get(palavra, {}).keys())
        trans_b = set(mk_b.transicoes.get(palavra, {}).keys())
        if not trans_a and not trans_b:
            divergencia = 0.0
        elif not trans_a or not trans_b:
            divergencia = 1.0
        else:
            inter = trans_a & trans_b; uniao = trans_a | trans_b
            divergencia = 1.0 - (len(inter) / len(uniao) if uniao else 0)

        # ESPECIFICIDADE (peso 3)
        freq_global = len([
            t for t, d in self.motor.topicos.items()
            if palavra in d.get('conteudo', set())
        ])
        especificidade = 1.0 - min(1.0, freq_global / max(1, len(self.motor.topicos) * 0.5))

        # PROFUNDIDADE (peso 2)
        cadeia_a = len(mk_a.gerar(palavra, passos=5))
        cadeia_b = len(mk_b.gerar(palavra, passos=5))
        profundidade = min(1.0, (cadeia_a + cadeia_b) / 10)

        score = (divergencia * 5 + especificidade * 3 + profundidade * 2) / 10
        h_a = mk_a.entropia(palavra) if palavra in mk_a.freq else 0
        h_b = mk_b.entropia(palavra) if palavra in mk_b.freq else 0
        score += min(0.5, (h_a + h_b) / 2 * 0.2) / 10
        score = min(1.0, score)

        return score, {
            'divergencia': round(divergencia, 3),
            'especificidade': round(especificidade, 3),
            'profundidade': round(profundidade, 3),
            'cadeia_a': cadeia_a, 'cadeia_b': cadeia_b,
        }

    def _analisar_sem_compartilhadas(self, topico_a: str, topico_b: str) -> Dict:
        texto_a = self.motor.topicos[topico_a]['texto'].encode('utf-8')
        texto_b = self.motor.topicos[topico_b]['texto'].encode('utf-8')
        bytes_comuns = set(texto_a) & set(texto_b)

        pontes = []
        for byte_val in bytes_comuns:
            pal_a = self._palavra_por_byte(self.motor, topico_a, byte_val)
            pal_b = self._palavra_por_byte(self.motor, topico_b, byte_val)
            if not pal_a or not pal_b or pal_a.lower() == pal_b.lower():
                continue
            score, det = self._avaliar_ponte(topico_a, topico_b, pal_a)
            score *= 0.7
            det['palavra_a'] = pal_a; det['palavra_b'] = pal_b
            pontes.append({'palavra': f"{pal_a}↔{pal_b}", 'score': round(score, 2), **det})

        pontes.sort(key=lambda x: -x['score'])
        return {
            'total_candidatas': len(pontes),
            'tipo': 'byte_bridge',
            'pontes': pontes[:8],
            'melhor': pontes[0] if pontes else None,
        }

    @staticmethod
    def _palavra_por_byte(motor, topico: str, byte_val: int) -> Optional[str]:
        dados = motor.topicos[topico]['texto'].encode('utf-8')
        for i, b in enumerate(dados):
            if b == byte_val:
                inicio, fim = i, i
                while inicio > 0 and dados[inicio - 1] != 32:
                    inicio -= 1
                while fim < len(dados) and dados[fim] != 32:
                    fim += 1
                pal = dados[inicio:fim].decode('utf-8', errors='replace')
                if len(pal) >= 4:
                    return pal
        return None

    def relatorio(self, topico_a: str, topico_b: str) -> str:
        r = self.analisar(topico_a, topico_b)
        if 'erro' in r:
            return f"ERRO: {r['erro']}"
        m = r.get('melhor')
        if not m:
            return f"Nenhuma ponte entre {topico_a} e {topico_b}"
        return (
            f"MCRConexao: {topico_a} <-> {topico_b}\n"
            f"  Melhor ponte: '{m['palavra']}' score={m['score']:.1f}\n"
            f"  Divergência: {m['divergencia']:.3f}\n"
            f"  Especificidade: {m['especificidade']:.3f}\n"
            f"  Profundidade: {m['profundidade']:.3f}\n"
            f"  Cadeias: A={m['cadeia_a']} B={m['cadeia_b']}"
        )


# ═══════════════════════════════════════════════════════════════
# MCRMotor — Motor multinível integrado
# ═══════════════════════════════════════════════════════════════

class MCRMotor:
    """Motor de emergência MULTINÍVEL.

    Opera em 3 níveis simultaneamente (byte + palavra + token)
    para encontrar e validar conexões entre tópicos distantes.

    Equação MCR:
        NOTA = (BYTE + PALAVRA + TOKEN) × PENALIDADE
        PENALIDADE: compartilhado=1.0, parcial=0.7, byte=0.3, none=0.1
    """
    def __init__(self):
        self.mk_byte = MCR("byte_global")
        self.mk_palavra = MCR("palavra_global")
        self.mk_token = MCR("token_global")
        self.topicos: Dict[str, Dict] = {}
        self.conexoes_feitas: Set[str] = set()
        self.total_conexoes = 0
        self.threshold = MCRThreshold("motor")

    # ─── ALIMENTAÇÃO ────────────────────────────────────────

    def alimentar(self, texto: str, nome_topico: str = None) -> str:
        if nome_topico is None:
            nome_topico = f"topico_{len(self.topicos) + 1}"

        dados = texto.encode('utf-8')
        palavras = texto.split()

        for i in range(len(dados) - 1):
            self.mk_byte.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")
        for i in range(len(palavras) - 1):
            self.mk_palavra.aprender(palavras[i], palavras[i + 1])
        for i in range(len(palavras) - 1):
            ta = palavras[i][0].upper() if palavras[i] else '?'
            tb = palavras[i + 1][0].upper() if palavras[i + 1] else '?'
            self.mk_token.aprender(ta, tb)

        mk_topico = MCR(nome_topico)
        for i in range(len(dados) - 1):
            mk_topico.aprender(f"B:{dados[i]:02x}", f"B:{dados[i+1]:02x}")

        mk_pal = MCR(f"{nome_topico}_palavra")
        for i in range(len(palavras) - 1):
            mk_pal.aprender(palavras[i], palavras[i + 1])

        self.topicos[nome_topico] = {
            'texto': texto, 'markov': mk_topico,
            'markov_palavra': mk_pal, 'palavras': palavras,
            'bytes': len(dados), 'n_palavras': len(palavras),
            'conteudo': {p.lower() for p in palavras
                         if len(p) >= 4 and p.lower() not in CONECTORES},
        }
        return nome_topico

    def alimentar_json(self, arquivo: str) -> int:
        if not os.path.exists(arquivo):
            return 0
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        itens = dados.get('topicos', dados if isinstance(dados, list) else [])
        count = 0
        for item in itens:
            if isinstance(item, dict) and 'texto' in item:
                self.alimentar(item['texto'], item.get('nome'))
                count += 1
            elif isinstance(item, str):
                self.alimentar(item); count += 1
        return count

    # ─── PONTES ─────────────────────────────────────────────

    @staticmethod
    def _palavras_conteudo(texto: str) -> Set[str]:
        return {p.lower() for p in texto.split()
                if len(p) >= 4 and p.lower() not in CONECTORES}

    def _encontrar_ponte(self, topico_a: str, topico_b: str
                         ) -> Tuple[Optional[str], str, str, str]:
        mc = MCRConexao(self)
        melhor = mc.melhor_ponte(topico_a, topico_b)

        if melhor:
            palavra = melhor.get('palavra', '')
            score = melhor.get('score', 0)
            pal_a = melhor.get('palavra_a', palavra) or palavra
            pal_b = melhor.get('palavra_b', palavra) or palavra
            texto_a = self.topicos[topico_a]['texto']
            idx = texto_a.lower().find(pal_a.lower())
            byte_p = f"B:{texto_a.encode('utf-8')[max(0, idx)]:02x}" if idx >= 0 else (
                f"B:{texto_a.encode('utf-8')[0]:02x}")
            tipo = ('conteudo_compartilhado' if score >= 0.6
                    else 'conteudo_mas_parcial' if score >= 0.3
                    else 'byte_only')
            return byte_p, tipo, pal_a, pal_b

        # Fallback: palavra compartilhada
        ca = self._palavras_conteudo(self.topicos[topico_a]['texto'])
        cb = self._palavras_conteudo(self.topicos[topico_b]['texto'])
        comp = ca & cb
        if comp:
            pal = max(comp, key=len)
            ta = self.topicos[topico_a]['texto']
            idx = ta.lower().find(pal)
            if idx >= 0:
                return f"B:{ta.encode('utf-8')[idx]:02x}", 'conteudo_mas_parcial', pal, pal

        return self._byte_bridge(topico_a, topico_b)

    def _byte_bridge(self, topico_a: str, topico_b: str
                     ) -> Tuple[Optional[str], str, str, str]:
        mk_a = self.topicos[topico_a]['markov']
        mk_b = self.topicos[topico_b]['markov']
        texto_a = self.topicos[topico_a]['texto']
        seq_a = mk_a.gerar(f"B:{texto_a.encode('utf-8')[0]:02x}", passos=8)
        estados_b = set(mk_b.freq.keys())
        for e in seq_a:
            if e in estados_b:
                return e, 'byte_only', '', ''
        for e in seq_a:
            if e in self.mk_byte.freq:
                p, _ = self.mk_byte.predizer(e)
                if p and p in estados_b:
                    return e, 'byte_only', '', ''
        return None, 'none', '', ''

    # ─── CONEXÃO ────────────────────────────────────────────

    def _hash_conexao(self, a: str, b: str) -> str:
        return hashlib.md5(f"{min(a,b)}|{max(a,b)}".encode()).hexdigest()[:12]

    def conectar(self, topico_a: str, topico_b: str, forcar: bool = False) -> Optional[Dict]:
        if topico_a not in self.topicos or topico_b not in self.topicos:
            return None

        ta = self.topicos[topico_a]
        tb = self.topicos[topico_b]
        hash_c = self._hash_conexao(topico_a, topico_b)
        if not forcar and hash_c in self.conexoes_feitas:
            return None

        byte_p, tipo_p, pal_a, pal_b = self._encontrar_ponte(topico_a, topico_b)

        sequencia = ''

        # Geração por palavra (se ponte de conteúdo)
        if tipo_p in ('conteudo_compartilhado', 'conteudo_mas_parcial'):
            mk_pal_a = ta['markov_palavra']
            mk_pal_b = tb['markov_palavra']
            palavras_a = ta['palavras']
            semente = palavras_a[0] if palavras_a else 'O'
            seq_gerada = []
            atual = semente
            atingiu = False
            for _ in range(14):
                seq_gerada.append(atual)
                if not atingiu and atual.lower() == pal_a.lower():
                    atingiu = True
                    atual = pal_b
                    continue
                mk_atual = mk_pal_b if atingiu else mk_pal_a
                prox, conf = mk_atual.predizer(atual)
                if prox is None or conf < 0.01:
                    break
                atual = prox
            if not atingiu:
                seq_gerada = mk_pal_a.gerar(semente, passos=10)
            sequencia = ' '.join(seq_gerada)
            if len(sequencia.strip()) < 10:
                sequencia = ''

        # Fallback: geração por byte
        if not sequencia:
            mk_a = ta['markov']
            mk_b = tb['markov']
            inicio_a = f"B:{ta['texto'].encode('utf-8')[0]:02x}"
            seq_a = mk_a.gerar(inicio_a, passos=8)
            estados_b = set(mk_b.freq.keys())
            ponte = None
            for e in seq_a:
                if e in estados_b:
                    ponte = e; break
            if ponte is None:
                for e in seq_a:
                    if e in self.mk_byte.freq:
                        p, _ = self.mk_byte.predizer(e)
                        if p and p in estados_b:
                            ponte = e; break
            if ponte is None:
                return None
            seq_b = mk_b.gerar(ponte, passos=8)
            sequencia = self._reconstruir(seq_a, seq_b)

        if not sequencia or len(sequencia.strip()) < 3:
            return None

        nota, detalhes = self._autoavaliar(sequencia, ta['texto'], tb['texto'], tipo_p)
        self.conexoes_feitas.add(hash_c)
        self.total_conexoes += 1

        return {
            'hash': hash_c,
            'topico_a': topico_a,
            'topico_b': topico_b,
            'tipo_ponte': tipo_p,
            'palavra_a': pal_a,
            'palavra_b': pal_b,
            'sequencia': sequencia,
            'nota': round(nota, 2),
            'detalhes': detalhes,
            'nivel': self._nivel(nota),
        }

    @staticmethod
    def _reconstruir(seq_a: List[str], seq_b: List[str]) -> str:
        def para_texto(seq):
            chars = []
            for s in seq:
                if s.startswith('B:'):
                    try:
                        chars.append(chr(int(s[2:], 16)))
                    except:
                        chars.append('?')
                else:
                    chars.append(s[:1] if s else ' ')
            return ''.join(chars)
        return re.sub(r'\s+', ' ', (para_texto(seq_a) + para_texto(seq_b))).strip()

    # ─── EQUAÇÃO MCR ────────────────────────────────────────
    #
    # NOTA = (BYTE + PALAVRA + TOKEN) × PENALIDADE
    #
    # BYTE   = diff_A(0.5) + diff_B(0.5) + coer_byte(1.0)
    # PALAVRA = existe(1.0) + cont_A(1.5) + cont_B(1.5) + coer(1.0)
    # TOKEN  = tem_A(0.5) + tem_B(0.5) + coer_token(2.0)
    #
    # PENALIDADE:
    #   conteudo_compartilhado → 1.0
    #   conteudo_mas_parcial   → 0.7
    #   byte_only              → 0.3
    #   none                   → 0.1
    # ─────────────────────────────────────────────────────────

    def _coerencia_byte(self, seq: str) -> float:
        dados = seq.encode('utf-8')[:200]
        if len(dados) < 2:
            return 0.0
        ok = sum(1 for i in range(len(dados) - 1)
                 if f"B:{dados[i]:02x}" in self.mk_byte.transicoes
                 and f"B:{dados[i+1]:02x}" in self.mk_byte.transicoes.get(f"B:{dados[i]:02x}", {}))
        return ok / (len(dados) - 1)

    def _coerencia_palavra(self, seq: str) -> float:
        pal = seq.split()
        if not pal:
            return 0.0
        return sum(1 for p in pal if p in self.mk_palavra.freq) / len(pal)

    def _coerencia_token(self, seq: str) -> float:
        pal = seq.split()
        if len(pal) < 2:
            return 0.0
        ok = 0
        for i in range(len(pal) - 1):
            ta = pal[i][0].upper() if pal[i] else '?'
            tb = pal[i + 1][0].upper() if pal[i + 1] else '?'
            if ta in self.mk_token.transicoes and tb in self.mk_token.transicoes.get(ta, {}):
                ok += 1
        return ok / (len(pal) - 1)

    def _autoavaliar(self, sequencia: str, texto_a: str, texto_b: str, tipo_ponte: str
                     ) -> Tuple[float, Dict]:
        if not sequencia or len(sequencia.strip()) < 3:
            return 0.0, {'erro': 'vazia'}

        # NÍVEL BYTE (2 pts)
        j_a = MCRByteUtils.jaccard_bytes(sequencia, texto_a)
        j_b = MCRByteUtils.jaccard_bytes(sequencia, texto_b)
        c_byte = self._coerencia_byte(sequencia)
        nb_a = 0.5 if j_a < 0.3 else 0.0
        nb_b = 0.5 if j_b < 0.3 else 0.0
        nb_c = 1.0 if c_byte > 0.5 else (c_byte * 2 if c_byte > 0 else 0)
        nota_byte = nb_a + nb_b + nb_c

        # NÍVEL PALAVRA (5 pts)
        c_pal = self._coerencia_palavra(sequencia)
        ca = self._palavras_conteudo(texto_a)
        cb = self._palavras_conteudo(texto_b)
        cs = self._palavras_conteudo(sequencia)
        np_existe = 1.0 if c_pal > 0 else 0.0
        np_ca = min(1.5, len(cs & ca) * 0.5)
        np_cb = min(1.5, len(cs & cb) * 0.5)
        np_coer = 1.0 if c_pal > 0.3 else (c_pal * 3 if c_pal > 0 else 0)
        nota_palavra = np_existe + np_ca + np_cb + np_coer

        # NÍVEL TOKEN (3 pts)
        c_tok = self._coerencia_token(sequencia)
        tipos_a = {p[0].upper() for p in texto_a.split() if p}
        tipos_b = {p[0].upper() for p in texto_b.split() if p}
        tipos_seq = {p[0].upper() for p in sequencia.split() if p}
        nt_a = 0.5 if tipos_seq & tipos_a else 0.0
        nt_b = 0.5 if tipos_seq & tipos_b else 0.0
        nt_c = 2.0 if c_tok > 0.3 else (c_tok * 6 if c_tok > 0 else 0)
        nota_token = nt_a + nt_b + nt_c

        # PENALIDADE
        # Valor = quanto descontar (0.0 = nada, 0.7 = 70%% de corte)
        penalidade = {'conteudo_compartilhado': 0.0,
                      'conteudo_mas_parcial': 0.3,
                      'byte_only': 0.7}.get(tipo_ponte, 0.9)

        nota = (nota_byte + nota_palavra + nota_token) * (1 - penalidade)
        nota = min(10.0, max(0.0, nota))
        self.threshold.observar(nota)

        desconto_pct = int(penalidade * 100)

        return nota, {
            'byte': round(nota_byte, 2),
            'palavra': round(nota_palavra, 2),
            'token': round(nota_token, 2),
            'penalidade': penalidade,
            'desconto': f"{desconto_pct}%%",
            'jaccard_a': round(j_a, 3),
            'jaccard_b': round(j_b, 3),
            'coerencia_byte': round(c_byte, 3),
            'coerencia_palavra': round(c_pal, 3),
            'nota_final': round(nota, 2),
            'equacao': f"({nota_byte:.1f}+{nota_palavra:.1f}+{nota_token:.1f})x(1-{penalidade:.1f})={nota:.1f}",
        }

    @staticmethod
    def _nivel(nota: float) -> str:
        if nota >= 8.0: return "EMERGENTE_FORTE"
        if nota >= 5.0: return "EMERGENTE_MEDIO"
        if nota >= 3.0: return "EMERGENTE_FRACO"
        return "SEM_CONEXAO"

    # ─── EQUAÇÃO MCR SIG-NATURE ──────────────────────────────
    #
    # A assinatura N-dimensional captura TODAS as dimensoes
    # de um evento simultaneamente:
    #   byte, contexto, entropia, frequencia, posicao, fonte
    #
    # A Equacao MCR mede a COERENCIA DA ASSINATURA como um todo,
    # sem separar byte/palavra/token em pesos fixos.
    # ─────────────────────────────────────────────────────────

    def _assinatura_sequencia(self, seq_texto: str, fonte: str = '',
                               ciclo: int = 0) -> List[List[float]]:
        """Extrai assinaturas N-dim de cada byte da sequencia."""
        dados = seq_texto.encode('utf-8')[:500]
        return MCRSignatureMultidimensional.extrair_sequencia(
            dados, self.mk_byte, ciclo, fonte)

    def _autoavaliar_por_assinatura(self, sequencia: str, texto_a: str = '',
                                     texto_b: str = '',
                                     tipo_ponte: str = 'byte_only') -> Tuple[float, Dict]:
        """Autoavalia usando assinatura N-dimensional.

        Em vez de medir byte/palavra/token separadamente,
        extrai a assinatura N-dim da sequencia gerada e compara
        com as assinaturas dos textos de referencia.

        A nota final reflete a COERENCIA GLOBAL da assinatura:
        - Quanto mais proxima das assinaturas conhecidas, maior a nota
        - Penalidade por tipo de ponte (igual a Equacao MCR)
        """
        if not sequencia or len(sequencia.strip()) < 3:
            return 0.0, {'erro': 'sequencia vazia'}

        # Assinatura N-dim da sequencia gerada
        ass_seq = self._assinatura_sequencia(sequencia)
        fp_seq = MCRSignatureMultidimensional.fingerprint_sequencia(ass_seq)

        # Assinatura dos textos de referencia
        ass_a = self._assinatura_sequencia(texto_a, 'ref_a') if texto_a else []
        ass_b = self._assinatura_sequencia(texto_b, 'ref_b') if texto_b else []

        fp_a = MCRSignatureMultidimensional.fingerprint_sequencia(ass_a) if ass_a else None
        fp_b = MCRSignatureMultidimensional.fingerprint_sequencia(ass_b) if ass_b else None

        # Similaridade entre fingerprints N-dim
        sim_a = MCRSignatureMultidimensional.similaridade(fp_seq, fp_a) if fp_a else 0
        sim_b = MCRSignatureMultidimensional.similaridade(fp_seq, fp_b) if fp_b else 0

        # Quanto mais DIFERENTE das referencias, melhor (inovacao)
        diff_a = max(0, 1 - sim_a)
        diff_b = max(0, 1 - sim_b)

        # Coerencia interna: similaridade entre metades da sequencia
        n = len(ass_seq)
        if n >= 4:
            metade = n // 2
            fp_1 = MCRSignatureMultidimensional.fingerprint_sequencia(ass_seq[:metade])
            fp_2 = MCRSignatureMultidimensional.fingerprint_sequencia(ass_seq[metade:])
            coerencia = MCRSignatureMultidimensional.similaridade(fp_1, fp_2)
        else:
            coerencia = 0.5

        # PENALIDADE (mesma da Equacao MCR)
        penalidade = {'conteudo_compartilhado': 0.0,
                      'conteudo_mas_parcial': 0.3,
                      'byte_only': 0.7}.get(tipo_ponte, 0.9)

        # NOTA = inovacao × coerencia × (1 - penalidade)
        inovacao = (diff_a + diff_b) / 2
        nota = (inovacao * 5 + coerencia * 5) * (1 - penalidade)
        nota = min(10.0, max(0.0, nota))

        return nota, {
            'sim_a': round(sim_a, 3),
            'sim_b': round(sim_b, 3),
            'coerencia': round(coerencia, 3),
            'inovacao': round(inovacao, 3),
            'penalidade': penalidade,
            'nota_final': round(nota, 2),
            'fingerprint': [round(v, 3) for v in fp_seq],
        }

    # ─── EXPLORAÇÃO ─────────────────────────────────────────

    def explorar_todos(self) -> List[Dict]:
        nomes = list(self.topicos.keys())
        return [
            c for i in range(len(nomes))
            for j in range(i + 1, len(nomes))
            if (c := self.conectar(nomes[i], nomes[j])) is not None
        ]

    # ─── GERAÇÃO POR ASSINATURA ──────────────────────────────
    #
    # Em vez de Markov P(prox | ultimo), pergunta:
    #   "Qual próximo token MAXIMIZA a assinatura
    #    (Equação MCR) com toda a sequência?"
    #
    # Usa byte + palavra + token SIMULTANEAMENTE para escolher.
    # ─────────────────────────────────────────────────────────

    def _coletar_candidatos(self, palavras: List[str], max_candidatos: int = 10) -> List[str]:
        """Junta candidatos dos 3 níveis: palavra, token, byte.
        Filtra palavras repetidas nos últimos 3 passos.
        Se a última palavra não está no modelo, tenta a penúltima.
        """
        candidatos: List[str] = []
        vistos: Set[str] = set()

        if not palavras:
            return candidatos

        # Palavras recentes (evitar repetição imediata)
        recentes = set(palavras[-3:])

        # Encontra a última palavra que ESTÁ no modelo
        semente = palavras[-1]
        for offset in range(min(len(palavras), 3)):
            teste = palavras[-1 - offset]
            if teste in self.mk_palavra.freq:
                semente = teste
                break

        # Nível palavra: top N mais prováveis
        for p, conf in self.mk_palavra.predizer_n(semente, max_candidatos):
            if (p not in vistos and p not in recentes
                    and p != semente and conf > 0.01):
                candidatos.append(p)
                vistos.add(p)

        # Nível token: candidatos por tipo (primeira letra)
        if semente:
            tipo = semente[0].upper()
            for p, conf in self.mk_token.predizer_n(tipo, max_candidatos // 2):
                if conf < 0.01:
                    continue
                for pp, _ in self.mk_palavra.predizer_n(p.lower(), 3):
                    if pp not in vistos and pp not in recentes and pp != semente:
                        candidatos.append(pp)
                        vistos.add(pp)

        return candidatos[:max_candidatos]

    def _escolher_por_assinatura(self, palavras: List[str], candidatos: List[str]) -> Optional[str]:
        """Aplica Equação MCR em cada candidato, retorna o que maximiza.
        
        Quanto maior a assinatura, mais o candidato "se encaixa"
        no padrão da sequência atual em TODOS os níveis.
        """
        if not candidatos:
            return None

        texto_base = ' '.join(palavras)
        melhor_candidato = None
        melhor_nota = 0.0

        for cand in candidatos:
            texto_teste = f"{texto_base} {cand}" if texto_base else cand

            # Nível BYTE (0-2): coerência de transições byte
            c_byte = self._coerencia_byte(texto_teste)

            # Nível PALAVRA (0-5): coerência + palavras de conteúdo existentes
            c_pal = self._coerencia_palavra(texto_teste)
            pal_existe = 1.0 if c_pal > 0 else 0.0
            pal_coer = 1.0 if c_pal > 0.3 else (c_pal * 3 if c_pal > 0 else 0)
            nota_palavra = pal_existe + pal_coer

            # Nível TOKEN (0-3): coerência de tipos
            c_tok = self._coerencia_token(texto_teste)
            nota_token = 2.0 if c_tok > 0.3 else (c_tok * 6 if c_tok > 0 else 0)

            # Assinatura total: normalizada 0-1
            # byte(2) + palavra(5?) + token(3) = max 10? nao, byte max 2 + palavra max 2 + token max 2
            # Vamos normalizar assim:
            nota_byte = c_byte * 2  # 0-2
            nota_ass = (nota_byte + nota_palavra + nota_token) / 7.0  # normaliza 0-1
            nota_ass = min(1.0, nota_ass)

            if nota_ass > melhor_nota:
                melhor_nota = nota_ass
                melhor_candidato = cand

        return melhor_candidato

    def gerar_por_assinatura(self, texto: str, passos: int = 10,
                             conf_min: float = 0.15) -> str:
        """Gera sequência escolhendo cada token por assinatura MCR.
        
        Diferente de MCR.gerar() (Markov puro), aqui CADA passo
        avalia múltiplos candidatos pela Equação MCR e escolhe
        o que MAXIMIZA a assinatura em byte + palavra + token.
        
        Args:
            texto: semente inicial
            passos: máximo de tokens a gerar
            conf_min: nota mínima para aceitar um token
        Returns:
            texto original + tokens gerados
        """
        palavras = texto.split()
        if not palavras:
            return texto

        for _ in range(passos):
            candidatos = self._coletar_candidatos(palavras)
            if not candidatos:
                break

            melhor = self._escolher_por_assinatura(palavras, candidatos)
            if melhor is None:
                break

            # Verifica nota do melhor candidato
            texto_teste = f"{' '.join(palavras)} {melhor}"
            c_byte = self._coerencia_byte(texto_teste)
            nota = (c_byte * 2 + 1.0) / 7.0  # estimativa rápida
            if nota < conf_min:
                break

            palavras.append(melhor)

            # Critério de parada: repetição consecutiva
            if len(palavras) >= 3 and palavras[-1] == palavras[-2] == palavras[-3]:
                break

        return ' '.join(palavras)

    def relatorio(self) -> str:
        return (
            f"MCR MOTOR\n"
            f"  Byte: {self.mk_byte.stats()}\n"
            f"  Palavra: {self.mk_palavra.stats()}\n"
            f"  Token: {self.mk_token.stats()}\n"
            f"  Topicos: {len(self.topicos)}\n"
            f"  Conexoes: {self.total_conexoes}"
        )


# ═══════════════════════════════════════════════════════════════
# MCRAutoLoop — Loop de melhoria contínua
# ═══════════════════════════════════════════════════════════════

class MCRAutoLoop:
    """Auto-Loop: executa → avalia → expande → checkpoint.

    Integra:
      - MCRMotor para emergência
      - MCRSession para checkpoint e histórico
      - MCRBuffer para buffer de operações
      - MCREntropia para detecção de loops
      - MCRFragmentador para execução rastreável
    """
    def __init__(self, motor: MCRMotor = None, base_dir: str = None):
        self.motor = motor or MCRMotor()
        self.session = MCRSession(base_dir)
        self.buffer = MCRBuffer("auto_loop")
        self.entropia = MCREntropia("auto_loop")
        self.fragmentador = MCRFragmentador("auto_loop")
        self.historico: List[Dict] = []

    def carregar_dados(self, arquivo: str) -> int:
        n = self.motor.alimentar_json(arquivo)
        self.session.registrar("carregar_dados", f"{n} topicos")
        return n

    def _tentar_conexao(self, a: str, b: str) -> Dict:
        resultado = self.motor.conectar(a, b, forcar=True)
        if resultado is None:
            return {'conectou': False, 'nota': 0.0, 'sequencia': '(sem conexao)'}
        return {
            'conectou': True,
            'nota': resultado['nota'],
            'sequencia': resultado['sequencia'],
            'palavra_a': resultado.get('palavra_a', ''),
            'palavra_b': resultado.get('palavra_b', ''),
            'tipo_ponte': resultado.get('tipo_ponte', ''),
            'equacao': resultado.get('detalhes', {}).get('equacao', ''),
        }

    def loop(self, topico_a: str, topico_b: str,
             max_iter: int = 12, expansoes: List[Dict] = None) -> Dict:
        """Executa o ciclo completo: tenta → avalia → expande → checkpoint."""
        expansoes = expansoes or []
        exp_idx = 0
        melhor_nota = 0.0

        # Tenta retomar sessão anterior
        checkpoint = self.session.auto_retomar()
        if checkpoint:
            print(f"  Sessão retomada: {checkpoint.get('ultima_pergunta', '')[:40]}")

        for ciclo in range(1, max_iter + 1):
            print(f"\n  --- Ciclo {ciclo} ---")

            # Fragmenta e executa
            self.fragmentador.limpar()
            self.fragmentador.adicionar("conectar", self._tentar_conexao,
                                        {'a': topico_a, 'b': topico_b})
            resultados = self.fragmentador.executar_todos()
            frag = resultados[0] if resultados else None
            res = frag.resultado if frag and frag.sucesso else {'conectou': False, 'nota': 0.0}

            nota = res['nota']
            self.entropia.alimentar(f"{nota:.1f}")

            entry = {
                'ciclo': ciclo,
                'nota': nota,
                'conectou': res['conectou'],
                'sequencia': res['sequencia'][:80] if res['conectou'] else '(sem)',
                'topicos': len(self.motor.topicos),
            }
            self.historico.append(entry)

            print(f"  Nota: {nota:.1f}/10" + (f" | {res['sequencia'][:60]}" if res['conectou'] else ""))

            if nota > melhor_nota:
                melhor_nota = nota
                print(f"  >>> Melhor nota: {melhor_nota:.1f}/10")

            # Buffer e sessão
            self.buffer.adicionar({'ciclo': ciclo, 'resultado': res})
            self.session.registrar(
                f"{topico_a}+{topico_b} ciclo {ciclo}",
                res['sequencia'][:100] if res['conectou'] else 'sem conexao',
                {'nota': nota}
            )

            # Critérios de parada
            if nota >= 10.0:
                print(f"\n  >>> 10/10 ATINGIDO no ciclo {ciclo}! <<<")
                self.session.salvar_checkpoint({'nota_final': nota, 'motivo': '10/10'})
                break

            if self.entropia.esta_em_loop() and nota < 3.0 and ciclo > 3:
                print(f"  Loop detectado (H={self.entropia._entropia_local():.2f}). Interrompendo.")
                self.session.salvar_checkpoint({'nota_final': nota, 'motivo': 'loop'})
                break

            # Expansão
            if exp_idx < len(expansoes):
                exp = expansoes[exp_idx]
                self.motor.alimentar(exp.get('texto', ''), exp.get('nome', f"exp_{exp_idx}"))
                exp_idx += 1
                print(f"  Expandido: +1 topico ({len(self.motor.topicos)} total)")
            else:
                self._combinar_topicos()

        # Finalização
        self.buffer.flush()
        self.session.salvar_checkpoint({'nota_final': melhor_nota, 'ciclos': ciclo})

        return {
            'historico': self.historico,
            'melhor_nota': melhor_nota,
            'ciclos': ciclo,
            'atingiu_10': self.historico[-1]['nota'] >= 10.0 if self.historico else False,
        }

    def _combinar_topicos(self):
        nomes = list(self.motor.topicos.keys())
        if len(nomes) < 4:
            return
        for i in range(0, len(nomes) - 1, 2):
            a, b = nomes[i], nomes[i + 1]
            ta = self.motor.topicos[a]['texto']
            tb = self.motor.topicos[b]['texto']
            combinado = f"{ta[:len(ta)//2]} {tb[len(tb)//2:]}"
            nome = f"comb_{a}_{b}"
            if nome not in self.motor.topicos:
                self.motor.alimentar(combinado, nome)
                print(f"  Combinado: {nome} ({len(combinado)} chars)")
                return


# ═══════════════════════════════════════════════════════════════
# MCRPiEngine — Preditor universal de padrões
# ═══════════════════════════════════════════════════════════════

class MCRPiEngine:
    """Preditor universal de padrões baseado no MCR.

    Decide qual nível usar baseado na entropia do texto:
      - < 0.4:  Markov nível PALAVRA (extrapolação direta, alta confiança)
      - 0.4-0.65: Markov nível BYTE (busca ponte entre bytes no repertório)
      - > 0.65: MCRConexao (emergência entre tópicos, baixa confiança)

    Substitui pi_engine.py sem depender de PatternEngine ou Knowledge Graph.
    """
    THRESHOLD_MARKOV = 0.4
    THRESHOLD_BYTE = 0.65

    @staticmethod
    def avaliar_entropia(texto: str) -> float:
        """Entropia do texto normalizada (0-1). Quanto menor, mais previsível.
        
        Divide por log2(256) = 8 para normalizar entropia de bytes 0-1.
        """
        if not texto or len(texto) < 3:
            return 0.5
        return min(1.0, MCRByteUtils.entropia_bytes(texto) / 8.0)

    @staticmethod
    def decidir_metodo(texto: str) -> str:
        """Decide qual método usar: 'markov', 'byte', ou 'emergencia'."""
        h = MCRPiEngine.avaliar_entropia(texto)
        if h < MCRPiEngine.THRESHOLD_MARKOV:
            return 'markov'
        elif h < MCRPiEngine.THRESHOLD_BYTE:
            return 'byte'
        else:
            return 'emergencia'

    @staticmethod
    def continuar_padrao(texto: str, motor: MCRMotor, max_passos: int = 10) -> str:
        """Continua um padrão usando o melhor método para a entropia atual.

        Args:
            texto: texto inicial para continuar
            motor: MCRMotor com o repertório carregado
            max_passos: máximo de tokens a gerar
        Returns:
            texto original + continuação prevista
        """
        if not texto:
            return texto
        metodo = MCRPiEngine.decidir_metodo(texto)

        if metodo == 'markov':
            return MCRPiEngine._modo_markov(texto, motor, max_passos)
        elif metodo == 'byte':
            return MCRPiEngine._modo_byte(texto, motor, max_passos)
        else:
            return MCRPiEngine._modo_emergencia(texto, motor, max_passos)

    # ─── MODO MARKOV (entropia baixa) ─────────────────────────

    @staticmethod
    def _modo_markov(texto: str, motor: MCRMotor, passos: int) -> str:
        """Gera por ASSINATURA MCR (byte + palavra + token simultaneamente).
        
        Substitui o Markov ordem 1 puro por seleção do token que
        maximiza a Equação MCR na sequência completa.
        """
        return motor.gerar_por_assinatura(texto, passos)

    # ─── MODO BYTE (entropia média) ──────────────────────────

    @staticmethod
    def _modo_byte(texto: str, motor: MCRMotor, passos: int) -> str:
        """Busca ponte byte entre o texto e tópicos conhecidos."""
        nome_temp = f"_pi_b_{int(_time.time() * 1000000) % 99999}"
        motor.alimentar(texto, nome_temp)

        try:
            melhor_conexao = None
            melhor_nota = 3.0
            for nome in list(motor.topicos.keys()):
                if nome == nome_temp:
                    continue
                c = motor.conectar(nome_temp, nome, forcar=True)
                if c and c['nota'] > melhor_nota:
                    melhor_conexao = c
                    melhor_nota = c['nota']

            if melhor_conexao:
                seq = melhor_conexao.get('sequencia', '')
                if seq and len(seq) > 5:
                    return texto + ' ' + seq
        finally:
            motor.topicos.pop(nome_temp, None)

        return MCRPiEngine._modo_markov(texto, motor, passos)

    # ─── MODO EMERGÊNCIA (entropia alta) ─────────────────────

    @staticmethod
    def _modo_emergencia(texto: str, motor: MCRMotor, passos: int) -> str:
        """Usa MCRConexao para encontrar ponte emergente entre tópicos."""
        nome_temp = f"_pi_e_{int(_time.time() * 1000000) % 99999}"
        motor.alimentar(texto, nome_temp)

        try:
            cx = MCRConexao(motor)
            melhor_nome = None
            melhor_score = 0.5

            for nome in list(motor.topicos.keys()):
                if nome == nome_temp:
                    continue
                r = cx.analisar(nome_temp, nome)
                m = r.get('melhor')
                if m and m.get('score', 0) > melhor_score:
                    melhor_nome = nome
                    melhor_score = m['score']

            if melhor_nome:
                c = motor.conectar(nome_temp, melhor_nome, forcar=True)
                if c:
                    seq = c.get('sequencia', '')
                    if seq and len(seq) > 5:
                        return texto + ' ' + seq
        finally:
            motor.topicos.pop(nome_temp, None)

        return MCRPiEngine._modo_byte(texto, motor, passos)

    @staticmethod
    def relatorio(motor: MCRMotor) -> str:
        """Estatísticas do PiEngine sobre o motor atual."""
        n = len(motor.topicos)
        h_byte = motor.mk_byte.entropia_media()
        h_pal = motor.mk_palavra.entropia_media()
        return (
            f"MCR PiEngine\n"
            f"  Topicos: {n}\n"
            f"  Entropia byte media: {h_byte:.3f}\n"
            f"  Entropia palavra media: {h_pal:.3f}\n"
            f"  Modo predominante: "
            f"{'markov' if h_byte < 0.4 else 'byte' if h_byte < 0.65 else 'emergencia'}"
        )


# ═══════════════════════════════════════════════════════════════
# MCRBusca — Orquestrador de busca + geracao por assinatura
# ═══════════════════════════════════════════════════════════════

class MCRBusca:
    """Orquestrador de busca multi-fonte + geracao por assinatura.

    Dada uma pergunta:
      1. Avalia entropia — se baixa, gera direto
      2. Busca em todas as fontes disponiveis (sessao, topicos, arquivos)
      3. Ranqueia por Jaccard de bytes
      4. Alimenta conhecimento no motor
      5. Gera resposta maximizando Equacao MCR
      6. Autoavalia — se nota baixa, busca mais e regenera
      7. Aprende — registra na sessao

    Uso:
        motor = MCRMotor()
        motor.alimentar_json("dados.json")
        session = MCRSession()
        busca = MCRBusca()
        resposta = busca.perguntar("Explique o que e SPA", motor, session)
    """

    def __init__(self):
        self.fragmentador = MCRFragmentador("busca")
        self.total_consultas = 0

    def perguntar(self, texto: str, motor: MCRMotor,
                  session: MCRSession = None, max_iter: int = 3) -> Dict:
        """Responde a uma pergunta usando busca + geracao por assinatura.

        Fluxo:
          1. Entropia baixa (< 0.4): gera direto por assinatura
          2. Entropia media/alta: busca em fontes, ranqueia, alimenta, gera
          3. Autoavalia — se nota < 5, expande busca e regenera
          4. Registra na sessao

        Returns:
            {'resposta': str, 'nota': float, 'fontes': List[str], 'ciclos': int}
        """
        self.total_consultas += 1
        fontes_usadas = []
        resposta = ""
        melhor_nota = 0.0

        for ciclo in range(max_iter):
            self.fragmentador.limpar()

            # 1. Avalia entropia
            h = MCRPiEngine.avaliar_entropia(texto)

            if h < 0.4:
                # Entropia baixa: gera direto
                self.fragmentador.adicionar("gerar_direto",
                    MCRPiEngine._modo_markov, {'texto': texto, 'motor': motor, 'passos': 12})
                self.fragmentador.executar_todos()
                frag = self.fragmentador.fragmentos[0]
                if frag.sucesso and frag.resultado:
                    resposta = frag.resultado
                    fontes_usadas.append('geracao_direta')
            else:
                # 2. Busca em multiplas fontes
                resultados = self._buscar_tudo(texto, motor, session)

                # 3. Ranqueia por assinatura (Jaccard)
                top = self._ranquear(texto, resultados)

                # 4. Alimenta os melhores no motor
                for r in top[:3]:
                    nome_fonte = f"busca_{r['fonte']}_{self.total_consultas}"
                    if nome_fonte not in motor.topicos:
                        motor.alimentar(r['texto'], nome_fonte)
                        fontes_usadas.append(r['fonte'])

                # 5. Gera resposta por assinatura
                self.fragmentador.adicionar("gerar_resposta",
                    motor.gerar_por_assinatura, {'texto': texto, 'passos': 15})
                self.fragmentador.executar_todos()
                frag = self.fragmentador.fragmentos[0]
                if frag.sucesso and frag.resultado:
                    resposta = frag.resultado

            # 6. Autoavalia
            nota = self._autoavaliar_resposta(texto, resposta, motor)
            if nota > melhor_nota:
                melhor_nota = nota

            # Se ja esta bom, entrega
            if nota >= 5.0 or resposta == texto:
                break

            # Se nota baixa, expande a pergunta com o que ja gerou
            if ciclo < max_iter - 1 and resposta and len(resposta) > len(texto):
                texto = resposta

        result = {
            'resposta': resposta if resposta and resposta != texto else texto,
            'nota': round(melhor_nota, 2),
            'fontes': list(set(fontes_usadas)),
            'ciclos': ciclo + 1,
        }

        # 7. Aprende
        if session:
            session.registrar(texto, result['resposta'], {'nota': result['nota']})

        return result

    def _buscar_tudo(self, texto: str, motor: MCRMotor,
                     session: MCRSession = None) -> List[Dict]:
        """Busca em todas as fontes disponiveis."""
        resultados = []

        # Fonte 1: topicos carregados no motor
        for nome, dados in motor.topicos.items():
            resultados.append({
                'texto': dados['texto'],
                'fonte': f"topico:{nome}",
                '_peso': 3,
            })

        # Fonte 2: historico da sessao
        if session:
            for h in session.historico_recente(15):
                if h.get('resposta') and len(h['resposta']) > 20:
                    resultados.append({
                        'texto': h['resposta'],
                        'fonte': 'sessao',
                        '_peso': 2,
                    })

        # Fonte 3: arquivos .txt no diretorio atual
        try:
            import glob as _glob
            for fpath in _glob.glob("*.txt")[:5]:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    conteudo = f.read(2000)
                if len(conteudo) > 50:
                    resultados.append({
                        'texto': conteudo,
                        'fonte': f"arquivo:{os.path.basename(fpath)}",
                        '_peso': 1,
                    })
        except Exception:
            pass

        return resultados

    @staticmethod
    def _ranquear(texto: str, resultados: List[Dict]) -> List[Dict]:
        """Ranqueia resultados por similaridade de assinatura de bytes."""
        for r in resultados:
            j = MCRByteUtils.jaccard_bytes(texto[:500], r['texto'][:500])
            c = MCRByteUtils.similaridade_cosseno(texto[:500], r['texto'][:500])
            r['_score'] = round(j * 0.6 + c * 0.4 + r.get('_peso', 1) * 0.05, 4)
        return sorted(resultados, key=lambda x: -x['_score'])

    @staticmethod
    def _autoavaliar_resposta(pergunta: str, resposta: str, motor: MCRMotor) -> float:
        """Autoavalia a resposta usando Equacao MCR.

        Usa jaccard entre pergunta e resposta como proxy de relevancia,
        e coerencia Markov para medir fluencia.
        """
        if not resposta or len(resposta) < 10:
            return 0.0

        j = MCRByteUtils.jaccard_bytes(pergunta, resposta)
        coer = motor._coerencia_palavra(resposta) if hasattr(motor, '_coerencia_palavra') else 0.5

        nota = (j * 5 + coer * 3)
        if len(resposta) > 100:
            nota += 2
        return min(10, max(0, nota))
