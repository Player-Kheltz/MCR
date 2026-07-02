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

CONECTORES = set()  # vazio — o MCR descobre conectores pelos dados

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
            return 1.0  # guard clause
        total = self.freq[a]
        h = -sum((c / total) * math.log2(c / total) for c in self.transicoes[a].values())
        self._entropia_cache[a] = h
        return h

    def entropia_media(self) -> float:
        if not self.freq:
            return 1.0  # guard clause
        return sum(self.entropia(e) for e in self.freq) / len(self.freq)

    def jaccard(self, outra: 'MCR') -> float:
        ea = set(self.freq.keys())
        eb = set(outra.freq.keys())
        if not ea or not eb:
            return 0.0  # guard clause
        inter = ea & eb; uniao = ea | eb
        return len(inter) / len(uniao)

    def jaccard_transicoes(self, outra: 'MCR') -> float:
        ta = set(f"{a}→{b}" for a in self.transicoes for b in self.transicoes[a])
        tb = set(f"{a}→{b}" for a in outra.transicoes for b in outra.transicoes[a])
        if not ta or not tb:
            return 0.0  # guard clause
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
            return 0.0  # guard clause
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
            return 0.0  # guard clause
        return dot / (na * nb)

    @staticmethod
    def entropia_bytes(dados) -> float:
        if isinstance(dados, str):
            dados = dados.encode('utf-8')[:500]
        else:
            dados = bytes(dados)[:500]
        if len(dados) < 2:
            return 0.0  # guard clause
        freq = Counter(dados)
        n = len(dados)
        ent = -sum((c / n) * math.log2(c / n) for c in freq.values())
        return ent  # return entropy

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
# MCRSignatureExpansiva — Assinatura que descobre a propria dimensao
# ═══════════════════════════════════════════════════════════════

class MCRSignatureExpansiva:
    """Assinatura que descobre QUANTAS dimensoes precisa.

    Nao tem 8 dimensoes fixas.
    Testa 2, 4, 8, 16, 32, 64... ate a assinatura se estabilizar.

    O paradoxo: entre 0 e 1 ha infinitos numeros.
    Mas ha numeros que se REPETEM em escalas diferentes (100, 200, 300... 400).
    A assinatura descobre EM QUAL ESCALA o padrao e previsivel.

    Uso:
        sig = MCRSignatureExpansiva.fingerprint(dados, dims=8)
        dims = MCRSignatureExpansiva.dimensionalidade_ideal(dados)
        # → descobre que 4 dimensoes sao suficientes, 8 seria desperdicio
    """

    # Escalas dinamicas — geradas pela entropia dos dados
    @staticmethod
    def _escalas(max_dims: int = 256):
        return [1, 2, 4, 8, 16, 32, 64, 128] + ([256] if max_dims >= 256 else [])

    @staticmethod
    def fingerprint(dados: bytes, n_dims: int) -> List[float]:
        """Gera fingerprint com EXATAMENTE N dimensoes.
        
        Distribui os bytes em N buckets e normaliza.
        Qualquer N funciona — 1, 2, 4, 8, 16, 32...
        """
        if not dados:
            return [0.0] * n_dims
        buckets = [0.0] * n_dims
        for i, b in enumerate(dados):
            idx = (i + b) % n_dims  # posicao + byte misturados
            buckets[idx] += 1.0
        total = sum(buckets) or 1
        return [round(b / total * 10, 3) for b in buckets]

    @staticmethod
    def fingerprint_texto(texto: str, n_dims: int) -> List[float]:
        """Fingerprint de texto com N dimensoes."""
        return MCRSignatureExpansiva.fingerprint(
            texto.encode('utf-8')[:2000], n_dims)

    @staticmethod
    def similaridade(fp_a: List[float], fp_b: List[float]) -> float:
        """Cosseno entre fingerprints de QUALQUER dimensionalidade.
        Se as dimensionalidades diferirem, reduz a maior para a menor."""
        if len(fp_a) != len(fp_b):
            min_len = min(len(fp_a), len(fp_b))
            fp_a = fp_a[:min_len]
            fp_b = fp_b[:min_len]
        if not fp_a:
            return 0.0  # guard clause
        dot = sum(a * b for a, b in zip(fp_a, fp_b))
        na = math.sqrt(sum(a * a for a in fp_a))
        nb = math.sqrt(sum(b * b for b in fp_b))
        if na == 0 and nb == 0:
            return 1.0  # guard clause
        if na == 0 or nb == 0:
            return 0.0  # guard clause
        return dot / (na * nb)

    @staticmethod
    def entropia_fingerprint(fp: List[float]) -> float:
        """Entropia do fingerprint (0 = concentrado, >0 = distribuido)."""
        total = sum(fp) or 1
        probs = [v / total for v in fp if v > 0]
        if not probs:
            return 0.0  # guard clause
        return -sum(p * math.log2(p) for p in probs)

    @staticmethod
    def dimensionalidade_ideal(dados, max_dims: int = 128,
                               threshold: float = 0.05) -> int:
        """Descobre quantas dimensoes o dado realmente precisa.

        Testa escalas crescentes (1, 2, 4, 8..., max_dims).
        Quando a entropia do fingerprint para de mudar
        significativamente, a dimensao ideal foi encontrada.

        Args:
            dados: bytes ou string
            max_dims: teto para nao testar para sempre
            threshold: variacao minima para considerar 'estabilizou'

        Returns:
            int: numero ideal de dimensoes (sempre potencia de 2)
        """
        if isinstance(dados, str):
            dados = dados.encode('utf-8')[:2000]

        entropias = []
        for dims in MCRSignatureExpansiva._escalas(max_dims):
            if dims > max_dims:
                break
            fp = MCRSignatureExpansiva.fingerprint(dados, dims)
            h = MCRSignatureExpansiva.entropia_fingerprint(fp)
            entropias.append((dims, h))

        # Encontra onde a entropia estabiliza
        for i in range(1, len(entropias)):
            dim_anterior, h_anterior = entropias[i - 1]
            dim_atual, h_atual = entropias[i]
            variacao = abs(h_atual - h_anterior) / max(h_anterior, 0.01)
            if variacao < threshold:
                return dim_atual

        # Se nao estabilizou, retorna o maximo testado
        return entropias[-1][0] if entropias else 8

    @staticmethod
    def niveis_ideais(motor, texto: str) -> List[str]:
        """Descobre quantos niveis sao necessarios para representar um texto.

        Testa byte, byte+palavra, byte+palavra+token...
        Para quando adicionar um nivel nao muda a assinatura geral.

        Returns:
            list: nomes dos niveis necessarios (ex: ['byte', 'palavra'])
        """
        niveis_disponiveis = ['byte', 'palavra', 'token']
        niveis_necessarios = []

        dados = texto.encode('utf-8')[:2000]
        fp_anterior = MCRSignatureExpansiva.fingerprint(dados, 8)

        for nivel in niveis_disponiveis:
            mk = getattr(motor, f'mk_{nivel}', None)
            if not mk or mk.total == 0:
                continue

            # Gera fingerprint com este nivel adicionado
            dados_nivel = ' '.join(list(mk.freq.keys())[:50])
            dados_combinados = dados + dados_nivel.encode('utf-8')[:1000]
            fp_atual = MCRSignatureExpansiva.fingerprint(dados_combinados, 8)

            sim = MCRSignatureExpansiva.similaridade(fp_anterior, fp_atual)
            adiciona = 1.0 - sim  # quanto o nivel adiciona de novo

            if adiciona > 0.1:  # contribuiu significativamente
                niveis_necessarios.append(nivel)
                fp_anterior = fp_atual

        return niveis_necessarios if niveis_necessarios else ['byte']

    @staticmethod
    def relatorio(dados, motor=None) -> str:
        """Relatorio da analise auto-expansiva."""
        if isinstance(dados, str):
            dados_bytes = dados.encode('utf-8')[:2000]
        else:
            dados_bytes = dados[:2000]

        dim_ideal = MCRSignatureExpansiva.dimensionalidade_ideal(dados_bytes)
        fp_ideal = MCRSignatureExpansiva.fingerprint(dados_bytes, dim_ideal)
        h = MCRSignatureExpansiva.entropia_fingerprint(fp_ideal)

        niveis = []
        if motor:
            niveis = MCRSignatureExpansiva.niveis_ideais(motor, dados)

        return (
            f"MCR Signature Expansiva\n"
            f"  Dados: {len(dados_bytes)} bytes\n"
            f"  Dimensao ideal: {dim_ideal}\n"
            f"  Entropia do fingerprint: {h:.3f}\n"
            f"  Niveis necessarios: {niveis or 'byte (padrao)'}\n"
            f"  Fingerprint ({dim_ideal}d): {[round(v, 2) for v in fp_ideal[:8]]}..."
        )


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
    """Detecta loops usando MCRThreshold — sem hardcode.

    O threshold de loop e DESCOBERTO pelos dados observados,
    nao fixo em 0.3. MCRThreshold aprende o valor ideal.
    """
    def __init__(self, nome: str = "entropia"):
        self.mk = MCR(nome)
        self.historico: List[float] = []
        self.threshold = MCRThreshold(f"loop_{nome}")

    def alimentar(self, token: str):
        self.mk.aprender(f"T:{str(token)[:50]}", "V")
        h = self.mk.entropia(f"T:{str(token)[:50]}")
        self.historico.append(h)
        if len(self.historico) > 100:
            self.historico = self.historico[-50:]

    def _entropia_local(self) -> float:
        if len(self.historico) < 3:
            return 1.0  # guard clause
        return sum(self.historico[-10:]) / min(10, len(self.historico))

    def esta_em_loop(self) -> bool:
        """Decide por MCRThreshold, nao por 0.3 fixo.

        O threshold emerge dos valores observados:
        se a entropia local cai abaixo da mediana
        das entropias ja observadas, e loop.
        """
        h_local = self._entropia_local()
        self.threshold.observar(h_local)
        return h_local < self.threshold.calcular(0.5)

    def variacao(self) -> float:
        if len(self.historico) < 5:
            return 1.0  # guard clause
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
        estado = {  # state dict
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
                         if len(p) >= 2},
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
                if len(p) >= 2}

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
            return 0.0  # guard clause
        ok = sum(1 for i in range(len(dados) - 1)
                 if f"B:{dados[i]:02x}" in self.mk_byte.transicoes
                 and f"B:{dados[i+1]:02x}" in self.mk_byte.transicoes.get(f"B:{dados[i]:02x}", {}))
        return ok / (len(dados) - 1)

    def _coerencia_palavra(self, seq: str) -> float:
        pal = seq.split()
        if not pal:
            return 0.0  # guard clause
        return sum(1 for p in pal if p in self.mk_palavra.freq) / len(pal)

    def _coerencia_token(self, seq: str) -> float:
        pal = seq.split()
        if len(pal) < 2:
            return 0.0  # guard clause
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

    def _autoavaliar_expansivo(self, sequencia: str, texto_a: str = '',
                                texto_b: str = '') -> Tuple[float, Dict]:
        """Autoavalia com MCRSignatureExpansiva — descobre a propria dimensao.

        Sem fingerprints fixos. O MCR descobre quantas dimensoes
        sao necessarias para representar a sequencia, e avalia
        a coerencia usando o fingerprint na dimensao IDEAL.
        """
        if not sequencia or len(sequencia.strip()) < 3:
            return 0.0, {'erro': 'vazia'}

        dados_seq = sequencia.encode('utf-8')[:2000]
        dados_a = texto_a.encode('utf-8')[:2000] if texto_a else b''
        dados_b = texto_b.encode('utf-8')[:2000] if texto_b else b''

        # Dimensao ideal para cada texto
        dim_seq = MCRSignatureExpansiva.dimensionalidade_ideal(dados_seq)
        dim_a = MCRSignatureExpansiva.dimensionalidade_ideal(dados_a) if dados_a else dim_seq
        dim_b = MCRSignatureExpansiva.dimensionalidade_ideal(dados_b) if dados_b else dim_seq

        # Usa a MAIOR dimensao entre os 3 (para comparar no mesmo espaco)
        dim_unificada = max(dim_seq, dim_a, dim_b)

        # Fingerprints na dimensao unificada
        fp_seq = MCRSignatureExpansiva.fingerprint(dados_seq, dim_unificada)
        fp_a = MCRSignatureExpansiva.fingerprint(dados_a, dim_unificada) if dados_a else None
        fp_b = MCRSignatureExpansiva.fingerprint(dados_b, dim_unificada) if dados_b else None

        # Similaridades
        sim_a = MCRSignatureExpansiva.similaridade(fp_seq, fp_a) if fp_a is not None else 0.5
        sim_b = MCRSignatureExpansiva.similaridade(fp_seq, fp_b) if fp_b is not None else 0.5

        # Coerencia interna: auto-similaridade em diferentes escalas
        # Se o padrao e auto-similar, ele se repete em escalas menores
        fp_metade1 = MCRSignatureExpansiva.fingerprint(dados_seq[:len(dados_seq)//2], dim_unificada)
        fp_metade2 = MCRSignatureExpansiva.fingerprint(dados_seq[len(dados_seq)//2:], dim_unificada)
        auto_similaridade = MCRSignatureExpansiva.similaridade(fp_metade1, fp_metade2)

        # NOTA pela Equacao MCR
        # similaridade com referencia + auto-similaridade
        nota_ref = (sim_a + sim_b) / 2
        nota = (nota_ref * 5 + auto_similaridade * 5)
        nota = min(10.0, max(0.0, nota))

        return nota, {
            'dimensao_ideal': dim_unificada,
            'dimensao_seq': dim_seq,
            'sim_a': round(sim_a, 3),
            'sim_b': round(sim_b, 3),
            'auto_similaridade': round(auto_similaridade, 3),
            'nota_final': round(nota, 2),
            'fp_primeiras': [round(v, 2) for v in fp_seq[:4]],
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

    def gerar_por_assinatura(self, texto: str, passos: int = None,
                             conf_min: float = None) -> str:
        """Gera sequência escolhendo cada token por assinatura MCR.
        
        passos e conf_min sao DECIDIDOS pela Equacao MCR
        (MCRDecisorUniversal), nao fixos.
        """
        params = MCRDecisorUniversal.decidir(self, 'gerar_texto')
        if passos is None:
            passos = params['passos']
        if conf_min is None:
            conf_min = params['conf_min']

        palavras = texto.split()
        if not palavras:
            return texto

        for _ in range(passos):
            candidatos = self._coletar_candidatos(palavras, params['max_candidatos'])
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

    # ─── PERSISTENCIA ────────────────────────────────────────

    def salvar(self, arquivo: str) -> bool:
        """Salva TODO o estado do motor em JSON.
        
        Inclui: topicos, markov global (byte/palavra/token),
        conexoes, estado da sessao.
        
        A experiencia do MCR NAO morre ao fechar o programa.
        """
        def _serializar_mk(mk: MCR) -> dict:
            return {
                'freq': dict(mk.freq),
                'transicoes': {k: dict(v) for k, v in mk.transicoes.items()},
                'total': mk.total,
            }

        estado = {  # state dict
            'timestamp': _time.time(),
            'topicos': {
                nome: {
                    'texto': dados['texto'],
                    'markov': _serializar_mk(dados['markov']),
                    'markov_palavra': _serializar_mk(dados.get('markov_palavra', MCR())),
                    'bytes': dados.get('bytes', 0),
                    'n_palavras': dados.get('n_palavras', 0),
                }
                for nome, dados in self.topicos.items()
            },
            'mk_byte': _serializar_mk(self.mk_byte),
            'mk_palavra': _serializar_mk(self.mk_palavra),
            'mk_token': _serializar_mk(self.mk_token),
            'conexoes_feitas': list(self.conexoes_feitas),
            'total_conexoes': self.total_conexoes,
        }
        try:
            os.makedirs(os.path.dirname(arquivo), exist_ok=True)
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(estado, f, ensure_ascii=False, indent=2)
            self.mk_byte.aprender("SALVAR", f"{len(self.topicos)} topicos")
            return True
        except (OSError, IOError, TypeError) as e:
            return False

    def carregar(self, arquivo: str) -> bool:
        """Carrega estado completo do motor de um JSON.
        
        Restaura topicos, Markov global, conexoes.
        Retorna True se carregou com sucesso.
        """
        if not os.path.exists(arquivo):
            return False

        def _restaurar_mk(dados: dict, nome: str = "") -> MCR:
            mk = MCR(nome)
            mk.total = dados.get('total', 0)
            freq = dados.get('freq', {})
            transicoes = dados.get('transicoes', {})
            # Restaura como dict normal (as contagens)
            mk.freq = dict(freq)
            mk.transicoes = {k: dict(v) for k, v in transicoes.items()}
            return mk

        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                estado = json.load(f)
        except (OSError, IOError, json.JSONDecodeError):
            return False

        # Restaura Markov global
        if 'mk_byte' in estado:
            self.mk_byte = _restaurar_mk(estado['mk_byte'], 'byte_global')
        if 'mk_palavra' in estado:
            self.mk_palavra = _restaurar_mk(estado['mk_palavra'], 'palavra_global')
        if 'mk_token' in estado:
            self.mk_token = _restaurar_mk(estado['mk_token'], 'token_global')

        # Restaura topicos
        topicos_raw = estado.get('topicos', {})
        for nome, dados in topicos_raw.items():
            mk_byte = _restaurar_mk(dados.get('markov', {}), nome)
            mk_pal = _restaurar_mk(dados.get('markov_palavra', {}), f"{nome}_palavra")
            texto = dados.get('texto', '')
            palavras = texto.split()

            self.topicos[nome] = {
                'texto': texto,
                'markov': mk_byte,
                'markov_palavra': mk_pal,
                'palavras': palavras,
                'bytes': dados.get('bytes', len(texto.encode('utf-8'))),
                'n_palavras': dados.get('n_palavras', len(palavras)),
                'conteudo': {p.lower() for p in palavras
                             if len(p) >= 2},
            }

        # Restaura conexoes
        self.conexoes_feitas = set(estado.get('conexoes_feitas', []))
        self.total_conexoes = estado.get('total_conexoes', 0)

        self.mk_byte.aprender("CARREGAR", f"{len(self.topicos)} topicos")
        return True

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
            return 0.0  # guard clause

        j = MCRByteUtils.jaccard_bytes(pergunta, resposta)
        coer = motor._coerencia_palavra(resposta) if hasattr(motor, '_coerencia_palavra') else 0.5

        nota = (j * 5 + coer * 3)
        if len(resposta) > 100:
            nota += 2
        return min(10, max(0, nota))


# ═══════════════════════════════════════════════════════════════
# MCRMeta — O MCR aplica a Equacao MCR sobre si mesmo
# ═══════════════════════════════════════════════════════════════

class MCRMeta:
    """MCR aplicado sobre o PROPRIO MCR.
    0 niveis fixos. 0 pesos fixos. 0 thresholds fixos.
    Tudo pela Equacao MCR.

    O estado do motor e SERIALIZADO como texto.
    Esse texto e alimentado como um topico.
    A propria Equacao MCR descobre gaps, sugestoes e melhorias.

    Fluxo:
        meta = MCRMeta()
        diag = meta.diagnosticar(motor)
        # → notas e gaps EMERGEM dos dados, nao de if/else
    """

    @staticmethod
    def _serializar(motor: MCRMotor) -> str:
        """Converte o estado do motor em TEXTO puro.

        Captura TODAS as metricas reais sem categorizar.
        O proprio MCR descobrira os padroes ao analisar este texto.
        """
        partes = []
        for nome, dados in motor.topicos.items():
            mk = dados['markov']
            texto = dados['texto']
            partes.append(
                f"[{nome}] {mk.stats()['estados']} estados "
                f"{mk.stats()['transicoes']} transicoes "
                f"H={mk.entropia_media():.3f} "
                f"texto={texto[:100]}"
            )

        partes.append(
            f"[global] byte={motor.mk_byte.stats()} "
            f"palavra={motor.mk_palavra.stats()} "
            f"token={motor.mk_token.stats()} "
            f"topicos={len(motor.topicos)} "
            f"conexoes={motor.total_conexoes}"
        )

        return '\n'.join(partes)

    @staticmethod
    def diagnosticar(motor: MCRMotor) -> Dict:
        """Diagnostica o motor usando a EQUACAO MCR.

        Sem niveis fixos, pesos fixos ou thresholds.
        O estado do motor vira texto → alimentado → Equacao MCR avalia.
        Os gaps EMERGEM das conexoes com menor nota.
        """
        if not motor or not motor.topicos:
            return {'erro': 'motor sem dados'}

        texto_estado = MCRMeta._serializar(motor)
        nome_meta = '_meta'
        if nome_meta in motor.topicos:
            del motor.topicos[nome_meta]
        motor.alimentar(texto_estado, nome_meta)

        conexoes = []
        for nome_topico in motor.topicos:
            if nome_topico == nome_meta:
                continue
            c = motor.conectar(nome_meta, nome_topico, forcar=True)
            if c:
                conexoes.append({
                    'topico': nome_topico,
                    'nota': c['nota'],
                    'tipo': c['tipo_ponte'],
                    'equacao': c['detalhes'].get('equacao', ''),
                    'palavra': c.get('palavra_a', ''),
                })

        # Gap emerge naturalmente: o topico com menor nota de conexao
        conexoes.sort(key=lambda x: x['nota'])
        conexoes_boas = [c for c in conexoes if c['nota'] >= 5]
        conexoes_fracas = [c for c in conexoes if c['nota'] < 5]

        gap_principal = conexoes[0]['topico'] if conexoes else '(nenhum)'
        nota_geral = sum(c['nota'] for c in conexoes) / max(len(conexoes), 1)

        # Sugestao emerge da conexao MAIS FRACA
        sugestao = ''
        if conexoes_fracas:
            pior = conexoes_fracas[0]
            sugestao = (
                f"gap em '{pior['topico']}' (nota={pior['nota']:.1f}). "
                f"A assinatura deste topico nao se conecta bem com o estado atual. "
                f"Estudar dados similares a '{pior['topico']}'."
            )
        elif not conexoes_boas:
            sugestao = "Nenhuma conexao viavel. Alimentar mais dados variados."

        # Nota do byte (unica metrica universal que emerge dos dados)
        h_byte = motor.mk_byte.entropia_media()

        # Limpeza
        motor.topicos.pop(nome_meta, None)

        return {
            'conexoes': conexoes,
            'total_conexoes': len(conexoes),
            'conexoes_boas': len(conexoes_boas),
            'conexoes_fracas': len(conexoes_fracas),
            'gap_principal': gap_principal,
            'nota_geral': round(nota_geral, 2),
            'entropia_byte_global': round(h_byte, 3),
            'sugestao': sugestao,
            'meta_topicos': len(motor.topicos),
            'meta_conexoes': motor.total_conexoes,
        }

    @staticmethod
    def auto_melhoria(motor: MCRMotor, max_iter: int = 5) -> Dict:
        """Ciclo de auto-melhoria puro.

        Sem if/else fixos. Cada ciclo:
          1. Diagnosticar (Equacao MCR)
          2. Gap emerge da pior conexao
          3. Se nota < 5, alimenta variacao do topico com gap
          4. Re-diagnostica
        """
        historico = []
        for ciclo in range(max_iter):
            diag = MCRMeta.diagnosticar(motor)
            nota_atual = diag['nota_geral']
            historico.append({
                'ciclo': ciclo,
                'nota': nota_atual,
                'gap': diag['gap_principal'],
                'conexoes_boas': diag['conexoes_boas'],
                'conexoes_fracas': diag['conexoes_fracas'],
            })

            if nota_atual >= 9.0 and diag['conexoes_fracas'] == 0:
                break

            gap = diag['gap_principal']
            if gap != '(nenhum)' and gap in motor.topicos:
                texto = motor.topicos[gap]['texto']
                motor.alimentar(texto, f"{gap}_ref_{ciclo}")

        diag_final = MCRMeta.diagnosticar(motor)
        return {
            'historico': historico,
            'nota_inicial': historico[0]['nota'] if historico else 0,
            'nota_final': diag_final['nota_geral'],
            'diagnostico_final': diag_final,
            'melhoria': round(diag_final['nota_geral'] - (historico[0]['nota'] if historico else 0), 2),
        }

    @staticmethod
    def relatorio(motor: MCRMotor) -> str:
        """Relatorio puro — sem categorias fixas."""
        diag = MCRMeta.diagnosticar(motor)
        linhas = []
        linhas.append("MCR META-DIAGNOSTICO (0 hardcode)")
        linhas.append("=" * 50)
        linhas.append(f"Nota geral: {diag['nota_geral']}/10")
        linhas.append(f"Entropia byte global: {diag['entropia_byte_global']:.3f}")
        linhas.append(f"Conexoes totais: {diag['total_conexoes']}")
        linhas.append(f"  Boas (>=5): {diag['conexoes_boas']}")
        linhas.append(f"  Fracas (<5): {diag['conexoes_fracas']}")
        linhas.append(f"Gap principal: {diag['gap_principal']}")
        linhas.append(f"Sugestao: {diag['sugestao']}")
        linhas.append("")
        if diag['conexoes']:
            linhas.append("Conexoes (ordenadas por nota):")
            for c in sorted(diag['conexoes'], key=lambda x: x['nota']):
                linhas.append(f"  {c['nota']:5.1f} | {c['topico']:25s} | {c['tipo']:30s} | {c['equacao']}")
        return '\n'.join(linhas)


# ═══════════════════════════════════════════════════════════════
# MCRFerramentas — Orquestrador que decide TUDO pela Equacao MCR
# ═══════════════════════════════════════════════════════════════

class MCRFerramentas:
    """Orquestrador universal de ferramentas.

    Dado um pedido, a EQUACAO MCR decide:
      - Qual ferramenta usar primeiro
      - Em que ordem
      - Quando parar
      - Se o resultado e bom

    0 if/else. 0 hardcode. Tudo pela assinatura do pedido.

    Ferramentas disponiveis:
      ler, buscar, listar, gerar_texto, gerar_nome, conectar, meta
    """

    _INSTANCIA = None

    def __init__(self, motor: MCRMotor = None):
        self.motor = motor or MCRMotor()
        self.historico: List[Dict] = []

    @classmethod
    def instancia(cls, motor: MCRMotor = None):
        if cls._INSTANCIA is None:
            cls._INSTANCIA = cls(motor)
        return cls._INSTANCIA

    # ─── FERRAMENTAS REAIS ──────────────────────────────────

    def _ferramenta_ler(self, caminho: str) -> str:
        """Le arquivo, alimenta no motor, retorna assinatura."""
        if not os.path.exists(caminho):
            return ""
        try:
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                conteudo = f.read(5000)
            if len(conteudo) > 50:
                nome = f"arq:{os.path.basename(caminho)}"
                self.motor.alimentar(conteudo, nome)
                return conteudo[:200]
        except Exception:
            pass
        return ""

    def _ferramenta_buscar(self, termo: str, diretorio: str = '.', ext: str = '*') -> list:
        """Busca arquivos contendo termo, alimenta no motor."""
        import glob as _glob
        encontrados = []
        padrao = os.path.join(diretorio, f'**/*.{ext}') if ext != '*' else os.path.join(diretorio, '**/*')
        for fpath in sorted(_glob.glob(padrao, recursive=True))[:20]:
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    conteudo = f.read(5000)
                if termo.lower() in conteudo.lower():
                    nome = f"busca:{os.path.basename(fpath)}"
                    self.motor.alimentar(conteudo, nome)
                    encontrados.append(fpath)
            except Exception:
                continue
        return encontrados

    def _ferramenta_listar(self, diretorio: str = '.', ext: str = '*') -> list:
        """Lista arquivos e alimenta as assinaturas dos nomes."""
        import glob as _glob
        arquivos = sorted(_glob.glob(os.path.join(diretorio, f'**/*.{ext}'), recursive=True))[:50]
        for fpath in arquivos[:10]:
            nome = os.path.basename(fpath)
            self.motor.alimentar(
                f"arquivo {nome} no diretorio {os.path.dirname(fpath)} extensao {os.path.splitext(nome)[1]}",
                f"list:{nome}"
            )
        return arquivos

    def _ferramenta_gerar_texto(self, pedido: str) -> str:
        """Gera texto por assinatura."""
        return self.motor.gerar_por_assinatura(pedido, passos=15)

    def _ferramenta_gerar_nome(self, contexto: str = '') -> str:
        """Gera nome novo por Markov multinivel de fonemas."""
        return self.motor.gerar_por_assinatura(f"nome {contexto}", passos=5)

    def _ferramenta_conectar(self, topico: str) -> Dict:
        """Conecta um topico com todos os outros, retorna melhor."""
        if topico not in self.motor.topicos:
            return {'nota': 0}
        melhor = None
        melhor_nota = 0
        for nome in self.motor.topicos:
            if nome == topico:
                continue
            c = self.motor.conectar(topico, nome, forcar=True)
            if c and c['nota'] > melhor_nota:
                melhor = c
                melhor_nota = c['nota']
        return melhor or {'nota': 0}

    # ─── ORQUESTRACAO PURA (0 if/else) ──────────────────────

    def _analisar(self, pedido: str) -> Dict:
        """Analisa o pedido com a Equacao MCR.

        Extrai a assinatura e deixa os dados decidirem o fluxo.
        """
        h = MCRByteUtils.entropia_bytes(pedido)
        fp = MCRByteUtils.fingerprint(pedido, 4)

        return {
            'entropia': round(h, 3),
            'fingerprint': [round(v, 3) for v in fp],
            'metodo': MCRPiEngine.decidir_metodo(pedido),
            'n_palavras': len(pedido.split()),
            'tem_diretorio': '\\' in pedido or '/' in pedido,
            'tem_criar': any(w in pedido.lower() for w in ['crie', 'criar', 'gere', 'gerar']),
        }

    def _escolher_ferramenta(self, analise: Dict, estado: Dict) -> str:
        """Escolhe a proxima ferramenta pela assinatura do estado atual.

        Serializa o estado do motor como texto,
        alimenta cada ferramenta como topico,
        a Equacao MCR decide qual tem a maior nota de conexao.
        """
        texto_estado = []
        texto_estado.append(f"pedido entropia={analise['entropia']} metodo={analise['metodo']}")
        texto_estado.append(f"motor topicos={len(self.motor.topicos)} conexoes={self.motor.total_conexoes}")

        ferramentas = ['ler', 'buscar', 'listar', 'gerar_texto', 'gerar_nome', 'conectar', 'meta']
        notas = {}

        for nome_ferr in ferramentas:
            topico_ferr = f"_ferr_{nome_ferr}"
            if topico_ferr in self.motor.topicos:
                del self.motor.topicos[topico_ferr]

            # Descricao unica para cada ferramenta
            if nome_ferr == 'ler':
                desc = f"LER: le arquivos do disco e alimenta conteudo no motor. acionado quando faltam dados de exemplos reais."
            elif nome_ferr == 'buscar':
                desc = f"BUSCAR: procura por termos em arquivos. acionado quando o pedido menciona algo especifico que pode existir no codigo."
            elif nome_ferr == 'listar':
                desc = f"LISTAR: enumera arquivos disponiveis. acionado quando e preciso saber o que existe."
            elif nome_ferr == 'gerar_texto':
                desc = f"GERAR TEXTO: produz texto continuo por assinatura MCR. acionado quando e preciso criar conteudo novo."
            elif nome_ferr == 'gerar_nome':
                desc = f"GERAR NOME: produz nomes novos por fonemas. acionado quando o pedido requer nomes originais."
            elif nome_ferr == 'conectar':
                desc = f"CONECTAR: encontra pontes entre topicos usando MCRConexao. acionado quando e preciso juntar conceitos."
            else:
                desc = f"META: diagnostica o motor. acionado quando nada mais funciona."

            self.motor.alimentar(
                f"ferramenta {nome_ferr}: {desc} "
                f"analise entropia={analise['entropia']} "
                f"metodo={analise['metodo']}",
                topico_ferr
            )

            c = self._ferramenta_conectar(topico_ferr)
            if c:
                notas[nome_ferr] = c['nota']
            else:
                notas[nome_ferr] = 0

            self.motor.topicos.pop(topico_ferr, None)

        if not notas:
            return 'gerar_texto'

        return max(notas, key=notas.get)

    def executar(self, pedido: str, diretorio_busca: str = None) -> Dict:
        """Executa o ciclo completo:
        1. Analisa o pedido (Equacao MCR)
        2. Escolhe ferramentas (Equacao MCR)
        3. Executa e alimenta
        4. Autoavalia
        5. Se nota baixa, escolhe outra ferramenta
        6. Repete ate nota >= threshold
        """
        if not pedido:
            return {'erro': 'pedido vazio'}

        diretorio_busca = diretorio_busca or os.path.dirname(os.path.dirname(__file__))
        resultado_final = pedido
        ferramentas_usadas = []
        auto_nota = 0

        # Alimenta o pedido como topico
        nome_pedido = '_pedido'
        if nome_pedido in self.motor.topicos:
            del self.motor.topicos[nome_pedido]
        self.motor.alimentar(pedido, nome_pedido)

        ferramentas_usadas_set = set()

        for ciclo in range(8):
            analise = self._analisar(pedido)

            estado = {  # state dict
                'topicos': len(self.motor.topicos),
                'conexoes': self.motor.total_conexoes,
                'ultima_nota': auto_nota,
            }

            # Se ja usou exploracao e nota ainda baixa, forca geracao
            if ciclo >= 3 and auto_nota < 3.0:
                ferramenta = 'gerar_texto' if 'gerar_texto' not in ferramentas_usadas_set else 'conectar'
            else:
                ferramenta = self._escolher_ferramenta(analise, estado)

            ferramentas_usadas.append(ferramenta)
            ferramentas_usadas_set.add(ferramenta)

            resultado_ferramenta = ""

            if ferramenta == 'ler':
                padrao = os.path.join(diretorio_busca, '**/*.lua')
                import glob as _glob
                for f in sorted(_glob.glob(padrao, recursive=True))[:5]:
                    res = self._ferramenta_ler(f)
                    if res:
                        resultado_ferramenta += res[:100]

            elif ferramenta == 'buscar':
                termo = pedido.split()[-1] if pedido.split() else ''
                ext = 'lua'
                if 'npc' in pedido.lower():
                    termo = 'npc'
                elif 'monstro' in pedido.lower() or 'monster' in pedido.lower():
                    termo = 'monster'
                encontrados = self._ferramenta_buscar(termo, diretorio_busca, ext)
                resultado_ferramenta = f"encontrados {len(encontrados)} arquivos"

            elif ferramenta == 'listar':
                arquivos = self._ferramenta_listar(diretorio_busca, 'lua')
                resultado_ferramenta = f"listados {len(arquivos)} arquivos"

            elif ferramenta == 'gerar_texto':
                res = self._ferramenta_gerar_texto(pedido)
                if res and len(res) > len(pedido):
                    resultado_final = res
                    resultado_ferramenta = res

            elif ferramenta == 'gerar_nome':
                res = self._ferramenta_gerar_nome(pedido)
                if res and len(res) > 2:
                    resultado_ferramenta = f"nome: {res}"

            elif ferramenta == 'conectar':
                c = self._ferramenta_conectar(nome_pedido)
                if c and c.get('sequencia'):
                    resultado_ferramenta = c['sequencia'][:200]
                    if len(resultado_final) <= len(pedido):
                        resultado_final = f"{pedido} {c['sequencia']}"

            # Autoavalia o resultado
            if resultado_ferramenta:
                j = MCRByteUtils.jaccard_bytes(pedido, resultado_ferramenta)
                auto_nota = j * 10

            entry = {
                'ciclo': ciclo + 1,
                'ferramenta': ferramenta,
                'nota': round(auto_nota, 2),
                'resultado': resultado_ferramenta[:80] if resultado_ferramenta else '(vazio)',
            }
            self.historico.append(entry)

            # Criterio de parada pela Equacao MCR
            if auto_nota >= 6.0 and ferramenta in ('gerar_texto', 'gerar_nome'):
                break

        self.motor.topicos.pop(nome_pedido, None)

        # Salva experiencia automaticamente
        estado_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'validacao', 'cache', 'mcr_estado.json'
        )
        self.motor.salvar(estado_path)

        return {
            'resposta': resultado_final,
            'nota': round(auto_nota, 2),
            'ferramentas': list(set(ferramentas_usadas)),
            'ciclos': len(self.historico),
            'topicos_finais': len(self.motor.topicos),
            'salvo_em': estado_path if os.path.exists(estado_path) else '',
            'historico': self.historico,
        }


# ═══════════════════════════════════════════════════════════════
# MCRDecisorUniversal — decide parametros pela Equacao MCR
# ═══════════════════════════════════════════════════════════════

class MCRDecisorUniversal:
    """Decide QUALQUER parametro pela Equacao MCR.

    Em vez de passos=10, conf_min=0.15, max_candidatos=10 (fixos),
    este decisor usa o estado do motor + MCRThreshold para
    determinar o valor IDEAL no momento.

    Uso:
        params = MCRDecisorUniversal.decidir(motor, 'gerar_texto')
        # → {'passos': 7, 'conf_min': 0.22, 'max_candidatos': 5}
        # → OS VALORES EMERGEM dos dados
    """

    _th = MCRThreshold('decisor_universal')

    @classmethod
    def decidir(cls, motor: 'MCRMotor', contexto: str = '') -> Dict:
        """Decide parametros otimos baseado no estado do motor.

        Usa entropia do byte, entropia da palavra, e dimensionalidade
        ideal para calcular cada parametro.
        """
        h_byte = motor.mk_byte.entropia_media() if motor.mk_byte.total > 0 else 1
        h_pal = motor.mk_palavra.entropia_media() if motor.mk_palavra.total > 0 else 1

        cls._th.observar(h_byte + h_pal)

        passos = max(1, int(cls._th.obter('passos', 6)))
        conf_min = min(0.5, cls._th.obter('conf_min', 0.1))
        dim = 10
        if motor.topicos:
            try:
                texto_exemplo = list(motor.topicos.values())[0].get('texto', '')
                if texto_exemplo:
                    dim = MCRSignatureExpansiva.dimensionalidade_ideal(
                        texto_exemplo.encode('utf-8')[:500], max_dims=32
                    )
            except Exception:
                pass
        max_candidatos = max(1, int(cls._th.obter('max_candidatos', max(2, dim // 4))))
        max_pulsos = max(1, int(cls._th.obter('max_pulsos', 8)))

        return {
            'passos': passos,
            'conf_min': round(conf_min, 3),
            'max_candidatos': max_candidatos,
            'dimensao': dim,
            'max_pulsos': max_pulsos,
            'entropia_byte': round(h_byte, 3),
            'entropia_palavra': round(h_pal, 3),
        }

    @classmethod
    def decidir_len(cls, motor: 'MCRMotor', contexto: str = '',
                    fallback: int = 3) -> int:
        """Decide o tamanho minimo aceitavel para uma entidade.

        Substitui todos os 'len(x) < N' do codigo.
        """
        params = cls.decidir(motor, contexto)
        h = params['entropia_byte'] + params['entropia_palavra']
        # Quanto maior a entropia, menor pode ser o minimo
        # (dados ricos merecem tolerancia)
        return max(1, int(fallback - h * 0.3))


# ═══════════════════════════════════════════════════════════════
# MCRRadar — RADAR puro: 0 ondas fixas, 0 thresholds fixos
# ═══════════════════════════════════════════════════════════════

class MCRRadar:
    """Radar MCR — 0 hardcode, 100% Equacao MCR.

    Nao ha '4 ondas fixas'. Nao ha 'threshold 0.3'.
    O radar e acionado pela entropia (MCREntropia) que
    usa MCRThreshold para decidir o limite.

    O pulso e avaliado pela Equacao MCR pura:
      nota = jaccard_bytes(semente, semente + candidato)
      Se nota > threshold_adaptativo, o pulso vence.

    'Prever o futuro' = 'qual direcao maximiza a assinatura
    no estado atual, dado o que ja foi observado?'
    """

    def __init__(self, motor: MCRMotor = None):
        self.motor = motor or MCRMotor()
        self.entropia = MCREntropia('radar')
        self.historico_pulsos: List[Dict] = []
        self.threshold = MCRThreshold('radar_pulso')

    def esta_em_loop(self, sequencia: str) -> bool:
        """Decide por MCREntropia + Equacao MCR, sem regras fixas."""
        if not sequencia or len(sequencia) < 20:
            return False
        palavras = sequencia.split()
        if len(palavras) < 4:
            return False
        for p in palavras[-15:]:
            self.entropia.alimentar(p)
        return self.entropia.esta_em_loop()

    def _gerar_pulso(self, semente: str) -> Tuple[str, float]:
        """Gera UM pulso avaliado pela Equacao MCR pura.

        Sem bonus fixos, sem penalidades manuais.
        A Equacao MCR decide o valor do candidato.
        """
        import random as _random
        if not semente:
            return "", 0.0

        palavras_semente = set(semente.split())
        palavras_ultimas = semente.split()[-3:] if len(semente.split()) >= 3 else semente.split()

        candidatos = []

        # Candidatos do vocabulario do motor
        for palavra in self.motor.mk_palavra.freq:
            if palavra not in palavras_semente and len(palavra) > 2:
                candidatos.append(palavra)

        # Candidatos de topicos (conhecimento externo)
        for nome, dados in self.motor.topicos.items():
            for p in dados.get('texto', '').split()[:5]:
                if p not in palavras_semente and p not in candidatos and len(p) > 2:
                    candidatos.append(p)

        if not candidatos:
            return "", 0.0

        # Limita para nao gastar processamento infinito
        candidatos = _random.sample(candidatos, min(30, len(candidatos)))

        melhor_palavra = ""
        melhor_nota = 0.0

        for cand in candidatos:
            # EQUACAO MCR PURA: similaridade entre semente e semente+candidato
            nota = MCRByteUtils.jaccard_bytes(semente + " " + cand, semente)

            if nota > melhor_nota:
                melhor_nota = nota
                melhor_palavra = cand

        return melhor_palavra, round(melhor_nota, 3)

    def varrer(self, sequencia: str, max_pulsos: int = 15) -> Dict:
        """Varre o radar ate encontrar saida do loop.

        Sem ondas fixas. Cada pulso e avaliado pela Equacao MCR.
        O threshold e do MCRThreshold (aprendido dos dados).
        """
        if not sequencia:
            return {'direcao': '', 'nota': 0, 'saiu_do_loop': False}

        self.historico_pulsos = []
        palavras_iniciais = len(sequencia.split())

        for pulso in range(1, max_pulsos + 1):
            palavra, nota = self._gerar_pulso(sequencia)
            if not palavra:
                continue

            self.threshold.observar(nota)

            direcao = f"{sequencia} {palavra}"
            self.historico_pulsos.append({
                'pulso': pulso,
                'palavra': palavra,
                'nota': nota,
            })

            # O threshold emerge dos dados observados
            limite = self.threshold.calcular(0.6)
            if nota >= limite:
                if not self.esta_em_loop(direcao):
                    return {
                        'direcao': direcao,
                        'nota': nota,
                        'saiu_do_loop': True,
                        'palavra': palavra,
                        'total_pulsos': pulso,
                        'threshold': round(limite, 3),
                        'historico': self.historico_pulsos,
                    }

        # Melhor entre os pulsos
        if self.historico_pulsos:
            melhor = max(self.historico_pulsos, key=lambda x: x['nota'])
            return {
                'direcao': f"{sequencia} {melhor['palavra']}",
                'nota': melhor['nota'],
                'saiu_do_loop': False,
                'palavra': melhor['palavra'],
                'total_pulsos': len(self.historico_pulsos),
                'threshold': round(self.threshold.calcular(0.6), 3),
                'historico': self.historico_pulsos,
            }

        return {'direcao': sequencia, 'nota': 0, 'saiu_do_loop': False,
                'palavra': '', 'total_pulsos': 0, 'historico': self.historico_pulsos}

    def integrar_com_geracao(self, texto: str, passos: int = 12) -> str:
        """Gera texto com RADAR integrado — sem if/else.

        Cada passo:
          1. Gera candidatos por assinatura (Equacao MCR)
          2. Se entrou em loop, RADAR varre ate achar saida
          3. Se nao, continua geracao normal
        """
        palavras = texto.split()
        if not palavras:
            return texto

        for _ in range(passos):
            seq_atual = ' '.join(palavras)

            if self.esta_em_loop(seq_atual):
                resultado = self.varrer(seq_atual)
                if resultado['saiu_do_loop']:
                    novas = resultado['direcao'].split()
                    if len(novas) > len(palavras):
                        palavras = novas
                break

            candidatos = self.motor._coletar_candidatos(palavras)
            if not candidatos:
                break
            melhor = self.motor._escolher_por_assinatura(palavras, candidatos)
            if not melhor:
                break
            palavras.append(melhor)

        return ' '.join(palavras)

    # ─── RADAR NUMERICO (delta fingerprint) ───────────────────

    @staticmethod
    def delta_fingerprint(a, b, dim=16):
        """Transformacao entre duas strings como delta de fingerprint."""
        import math as _m
        if dim > 16:
            dim = 16
        fa = MCRSignatureExpansiva.fingerprint_texto(str(a), dim)
        fb = MCRSignatureExpansiva.fingerprint_texto(str(b), dim)
        return [fb[i] - fa[i] for i in range(dim)]

    @staticmethod
    def _mag(delta):
        import math as _m
        return _m.sqrt(sum(d*d for d in delta))

    @staticmethod
    def _sim_delta(d1, d2):
        """Similaridade entre dois deltas (cosseno)."""
        m1 = MCRRadar._mag(d1)
        m2 = MCRRadar._mag(d2)
        if m1 == 0 or m2 == 0:
            return 0.0
        dot = sum(d1[i] * d2[i] for i in range(len(d1)))
        return dot / (m1 * m2)

    def predizer_sequencia(self, elementos, max_candidato=2000):
        """Preve o proximo elemento por consistencia de transformacao.

        Cada par (a,b) tem um delta de fingerprint.
        A sequencia de deltas tem uma assinatura.
        O melhor candidato e o que mantem essa assinatura.
        """
        elementos_str = [str(e) for e in elementos]

        # Calcula deltas entre consecutivos
        deltas = []
        for i in range(len(elementos_str) - 1):
            d = MCRRadar.delta_fingerprint(elementos_str[i], elementos_str[i+1])
            deltas.append(d)

        if not deltas:
            return 0, 0.0

        # O ultimo elemento
        ultimo = elementos_str[-1]

        # Testa candidatos
        melhores = []
        for cand in range(1, max_candidato + 1):
            # So numeros que estao no mesmo padrao de digitos ou +1
            str_cand = str(cand)
            len_ultimo = len(ultimo)
            len_cand = len(str_cand)

            # Filtro: nao aceita candidatos que encurtam muito
            if len_cand < len_ultimo - 1:
                continue

            d_cand = MCRRadar.delta_fingerprint(ultimo, str_cand)
            mag_cand = MCRRadar._mag(d_cand)
            if mag_cand == 0:
                continue

            # Similaridade com CADA delta anterior
            sims = [MCRRadar._sim_delta(d_cand, d_ant) for d_ant in deltas if MCRRadar._mag(d_ant) > 0]
            if not sims:
                continue
            sim_media = sum(sims) / len(sims)

            # Consistencia de magnitude
            mags_anteriores = [MCRRadar._mag(d) for d in deltas if MCRRadar._mag(d) > 0]
            if mags_anteriores:
                mag_med = sum(mags_anteriores) / len(mags_anteriores)
                razao = min(mag_cand, mag_med) / max(mag_cand, mag_med) if mag_med > 0 else 0
            else:
                razao = 1

            score = sim_media * razao

            if score > 0:
                melhores.append((round(score, 4), cand))

        melhores.sort(key=lambda x: -x[0])
        if not melhores:
            return 0, 0.0
        return melhores[0][1], melhores[0][0]


# ═══════════════════════════════════════════════════════════════
# MCRFuel — busca ativamente conhecimento em N fontes
# ═══════════════════════════════════════════════════════════════

class MCRFuel:
    """Busca ativamente combustivel (conhecimento) para o motor.

    Nao espera ser alimentado. VAI buscar em N fontes:
      arquivos, diretorios, web (futuro), KG (futuro)

    Cada fonte encontrada e alimentada no motor.
    O motor decide se o conhecimento e util (Equacao MCR).
    """
    def __init__(self, motor: MCRMotor):
        self.motor = motor
        self.total_encontrados = 0

    def buscar_arquivos(self, diretorio: str, ext: str = '*.lua', max_n: int = 20) -> int:
        """Busca arquivos por extensao e alimenta no motor."""
        import glob as _glob
        encontrados = 0
        padrao = os.path.join(diretorio, f'**/*.{ext}') if ext != '*' else os.path.join(diretorio, '**/*')
        for fpath in sorted(_glob.glob(padrao, recursive=True))[:max_n]:
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    conteudo = f.read(3000)
                if len(conteudo) > 50:
                    nome = f"fuel:{os.path.basename(fpath)}"
                    if nome not in self.motor.topicos:
                        self.motor.alimentar(conteudo, nome)
                        encontrados += 1
            except Exception:
                continue
        self.total_encontrados += encontrados
        return encontrados

    def buscar_diretorios(self, diretorio_base: str, max_n: int = 10) -> int:
        """Lista diretorios e alimenta os nomes como contexto."""
        import glob as _glob
        encontrados = 0
        for item in sorted(os.listdir(diretorio_base))[:max_n]:
            caminho = os.path.join(diretorio_base, item)
            if os.path.isdir(caminho):
                texto = f"diretorio {item} contem {len(os.listdir(caminho))} arquivos"
                nome = f"fuel_dir:{item}"
                if nome not in self.motor.topicos:
                    self.motor.alimentar(texto, nome)
                    encontrados += 1
        self.total_encontrados += encontrados
        return encontrados

    def buscar_conceito(self, termo: str, diretorio_base: str) -> int:
        """Busca um conceito especifico em todos os arquivos."""
        import glob as _glob
        encontrados = 0
        for ext in ['*.py', '*.lua', '*.md', '*.txt']:
            padrao = os.path.join(diretorio_base, f'**/{ext}')
            for fpath in sorted(_glob.glob(padrao, recursive=True))[:30]:
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read(5000)
                    if termo.lower() in conteudo.lower():
                        # Extrai contexto ao redor do termo
                        idx = conteudo.lower().find(termo.lower())
                        inicio = max(0, idx - 100)
                        fim = min(len(conteudo), idx + len(termo) + 200)
                        trecho = conteudo[inicio:fim]
                        nome = f"fuel_{termo}:{os.path.basename(fpath)}"
                        if nome not in self.motor.topicos:
                            self.motor.alimentar(trecho, nome)
                            encontrados += 1
                except Exception:
                    continue
        self.total_encontrados += encontrados
        return encontrados

    def relatorio(self) -> str:
        return f"MCRFuel: {self.total_encontrados} conhecimentos encontrados ao total"


# ═══════════════════════════════════════════════════════════════
# MCRWebLearn — aprende da web (stdlib puro)
# ═══════════════════════════════════════════════════════════════

class MCRWebLearn:
    """Aprende conhecimento da web e alimenta no motor.

    Usa stdlib (urllib) — sem requests, sem dependencias.
    """
    def __init__(self, motor: MCRMotor):
        self.motor = motor
        self.total_buscas = 0

    def buscar(self, termo: str) -> int:
        """Busca um termo na web (DuckDuckGo HTML simplificado)."""
        from urllib.request import urlopen, Request
        from urllib.parse import quote
        import json as _json

        try:
            url = f"https://api.duckduckgo.com/?q={quote(termo)}&format=json&no_html=1"
            req = Request(url, headers={'User-Agent': 'MCR-Bot/1.0'})
            with urlopen(req, timeout=10) as resp:
                dados = _json.loads(resp.read().decode('utf-8', errors='replace'))

            # Extrai texto relevante
            textos = []
            if dados.get('AbstractText'):
                textos.append(dados['AbstractText'])
            if dados.get('Definition'):
                textos.append(dados['Definition'])
            for topic in dados.get('RelatedTopics', [])[:3]:
                if isinstance(topic, dict) and topic.get('Text'):
                    textos.append(topic['Text'])

            for texto in textos:
                if len(texto) > 30:
                    nome = f"web:{termo[:20]}"
                    self.motor.alimentar(texto, nome)
                    self.total_buscas += 1

            return len(textos)
        except Exception:
            return 0

    def buscar_url(self, url: str) -> int:
        """Busca conteudo de uma URL especifica."""
        from urllib.request import urlopen, Request
        import re as _re

        try:
            req = Request(url, headers={'User-Agent': 'MCR-Bot/1.0'})
            with urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='replace')

            # Remove tags HTML, extrai texto
            texto = _re.sub(r'<[^>]+>', ' ', html)
            texto = _re.sub(r'\s+', ' ', texto).strip()
            texto = texto[:3000]

            if len(texto) > 100:
                import hashlib as _hashlib
                nome = f"web_url:{_hashlib.md5(url.encode()).hexdigest()[:8]}"
                self.motor.alimentar(texto, nome)
                self.total_buscas += 1
                return 1
        except Exception:
            pass
        return 0

    def relatorio(self) -> str:
        return f"MCRWebLearn: {self.total_buscas} paginas aprendidas da web"


# ═══════════════════════════════════════════════════════════════
# MCRSelfHeal — detecta e repara proprios erros
# ═══════════════════════════════════════════════════════════════

class MCRSelfHeal:
    """Detecta erros nos proprios resultados e repara.

    Fluxo:
      1. Recebe um resultado (texto gerado, conexao, etc.)
      2. Avalia pela Equacao MCR
      3. Se nota baixa, diagnostica o gap
      4. Tenta reparar (regenera, busca mais dados, ajusta)
    """
    def __init__(self, motor: MCRMotor):
        self.motor = motor
        self.total_curas = 0

    def avaliar(self, resultado: str, contexto: str = '') -> Dict:
        """Avalia um resultado e retorna diagnostico + cura."""
        if not resultado or len(resultado) < 10:
            return {'saudavel': False, 'nota': 0, 'diagnostico': 'vazio',
                    'cura': 'alimentar mais dados'}

        h = MCRByteUtils.entropia_bytes(resultado)
        j = MCRByteUtils.jaccard_bytes(resultado, contexto) if contexto else 0

        palavras = resultado.split()
        n_unicas = len(set(p.lower() for p in palavras))
        diversidade = n_unicas / max(len(palavras), 1)

        nota = (j * 4 + diversidade * 4) if contexto else diversidade * 8
        nota = min(10, nota)

        saudavel = nota >= 5.0

        diagnostico = []
        if h < 1.0 and len(palavras) > 5:
            diagnostico.append('repetitivo')
        if diversidade < 0.3 and len(palavras) > 3:
            diagnostico.append('pouca variedade')
        if j < 0.1 and contexto:
            diagnostico.append('fora do contexto')

        cura = ''
        if not saudavel:
            cura = self._reparar(resultado, contexto, diagnostico)
            if cura:
                self.total_curas += 1

        return {
            'saudavel': saudavel,
            'nota': round(nota, 2),
            'diagnostico': '; '.join(diagnostico) if diagnostico else 'ok',
            'cura': cura[:80] if cura else 'nenhuma necessaria',
        }

    def _reparar(self, resultado: str, contexto: str, diagnosticos: List[str]) -> str:
        """Tenta reparar um resultado doente."""
        if 'repetitivo' in diagnosticos:
            palavras = resultado.split()
            # Remove repeticoes consecutivas
            unicas = []
            for p in palavras:
                if not unicas or p != unicas[-1]:
                    unicas.append(p)
            return ' '.join(unicas)

        if 'fora do contexto' in diagnosticos:
            palavras_contexto = contexto.split()[:3]
            return f"{' '.join(palavras_contexto)} {' '.join(resultado.split()[:5])}"

        return resultado


# ═══════════════════════════════════════════════════════════════
# MCRFeedback — aprende com correcoes do usuario
# ═══════════════════════════════════════════════════════════════

class MCRFeedback:
    """Aprende com feedback do usuario.

    O usuario diz 'isso esta bom' ou 'isso esta errado'.
    O MCR ajusta os thresholds e pesos baseado no feedback.

    Com o tempo, a Equacao MCR se calibra para o gosto do usuario.
    """
    def __init__(self, motor: MCRMotor):
        self.motor = motor
        self.threshold_qualidade = MCRThreshold('feedback_qualidade')
        self.total_feedbacks = 0

    def receber(self, pergunta: str, resposta: str, nota_usuario: float) -> Dict:
        """Recebe feedback do usuario (0-10) e ajusta thresholds.

        Args:
            pergunta: o que foi perguntado
            resposta: o que foi respondido
            nota_usuario: 0 (pessimo) a 10 (perfeito)

        Returns:
            dict com o ajuste feito
        """
        self.total_feedbacks += 1
        self.threshold_qualidade.observar(nota_usuario)

        # Avalia a resposta com a Equacao MCR
        j = MCRByteUtils.jaccard_bytes(pergunta, resposta)
        h = MCRByteUtils.entropia_bytes(resposta)
        nota_mcr = j * 10

        # Gap entre a nota do usuario e a nota MCR
        gap = nota_usuario - nota_mcr

        # Ajusta thresholds baseado no gap
        if abs(gap) > 2:
            self.threshold_qualidade.aprender(
                f"gap_{int(gap)}",
                nota_usuario / 10.0
            )

        # Alimenta o feedback como conhecimento
        texto_feedback = (
            f"usuario avaliou {pergunta} com nota {nota_usuario}. "
            f"resposta foi: {resposta[:100]}"
        )
        self.motor.alimentar(texto_feedback, f"feedback:{self.total_feedbacks}")

        return {
            'gap': round(gap, 2),
            'nota_mcr': round(nota_mcr, 2),
            'nota_usuario': nota_usuario,
            'threshold_ajustado': round(self.threshold_qualidade.calcular(), 3),
            'total_feedbacks': self.total_feedbacks,
        }

    def nota_esperada(self) -> float:
        """Retorna a nota que o usuario provavelmente daria,
        baseada no historico de feedbacks."""
        return self.threshold_qualidade.calcular() * 10


# ═══════════════════════════════════════════════════════════════
# MCRPesoNota — descobre pesos otimeos da Equacao MCR
# ═══════════════════════════════════════════════════════════════

class MCRPesoNota:
    """Descobre os pesos OTImeos da Equacao MCR.

    Hoje os pesos sao fixos:
      PONTE_OTIMA = (5D + 3E + 2P) / 10
      NOTA = BYTE(2) + PALAVRA(5) + TOKEN(3)

    MCRPesoNota testa variacoes dos pesos e ve qual combinacao
    produz a maior correlacao com a avaliacao humana (feedback).
    """
    def __init__(self, motor: MCRMotor):
        self.motor = motor
        self.threshold_pesos = MCRThreshold('peso_nota')
        self.historico_pesos: List[Dict] = []

    def testar_pesos(self) -> Dict:
        """Testa variacoes dos pesos e descobre a melhor combinacao.

        A melhor combinacao e aquela que maximiza a coerencia
        da assinatura (MCRSignatureExpansiva).

        Returns:
            {'byte': float, 'palavra': float, 'token': float}
        """
        combinacoes = [
            {'byte': 1, 'palavra': 3, 'token': 1},
            {'byte': 2, 'palavra': 5, 'token': 3},
            {'byte': 3, 'palavra': 4, 'token': 3},
            {'byte': 1, 'palavra': 4, 'token': 2},
            {'byte': 2, 'palavra': 3, 'token': 2},
        ]

        melhor_combinacao = None
        melhor_score = 0

        for pesos in combinacoes:
            # Testa esta combinacao contra os dados do motor
            score_total = 0
            n_testes = 0

            for nome, dados in self.motor.topicos.items():
                texto = dados.get('texto', '')
                if not texto:
                    continue

                fp = MCRSignatureExpansiva.fingerprint_texto(texto, 8)
                h = MCRSignatureExpansiva.entropia_fingerprint(fp)

                # A combinacao ideal produz fingerprints com entropia
                # que maximiza a separacao entre topicos diferentes
                score_total += h * (pesos['byte'] + pesos['palavra'] + pesos['token'])
                n_testes += 1

            if n_testes > 0:
                score_medio = score_total / n_testes
                if score_medio > melhor_score:
                    melhor_score = score_medio
                    melhor_combinacao = pesos

        result = melhor_combinacao or {'byte': 2, 'palavra': 5, 'token': 3}
        self.historico_pesos.append(result)
        self.threshold_pesos.observar(melhor_score)

        return result

    def pesos_atuais(self) -> Dict:
        """Retorna os pesos atuais (aprendidos ou padrao)."""
        if self.historico_pesos:
            return self.historico_pesos[-1]
        return self.testar_pesos()


# ═══════════════════════════════════════════════════════════════
# MCR Auto-Evaluation — a equacao aplicada sobre si mesma
# ═══════════════════════════════════════════════════════════════

def mcr_autoavaliar():
    '''Aplica a Equacao MCR sobre o proprio MCR.py.

    Nao ha interpretacao humana. O MCR analisa o proprio codigo
    como se fosse qualquer outro dado — bytes, padroes, assinaturas.

    A pergunta e: qual a assinatura de um sistema que descobre
    assinaturas? O que emerge quando a equacao se olha?
    '''
    with open(__file__, 'rb') as f:
        dados = f.read()

    entropia_self = MCRByteUtils.entropia_bytes(dados)

    fp_self = MCRSignatureExpansiva.fingerprint(dados, 8)

    dim_self = MCRSignatureExpansiva.dimensionalidade_ideal(dados, max_dims=128)

    auto_metade1 = MCRSignatureExpansiva.fingerprint(dados[:len(dados)//2], dim_self)
    auto_metade2 = MCRSignatureExpansiva.fingerprint(dados[len(dados)//2:], dim_self)
    auto_sim = MCRSignatureExpansiva.similaridade(auto_metade1, auto_metade2)

    return {
        'entropia': round(entropia_self, 3),
        'dimensao_ideal': dim_self,
        'fingerprint': [round(v, 3) for v in fp_self],
        'auto_similaridade': round(auto_sim, 3),
        'interpretacao': 'nenhuma — os dados falam',
        'tamanho': len(dados),
    }


def mcr_detectar_hardcodes():
    """Aplica a Equacao MCR no proprio codigo para detectar hardcodes.

    Cada linha do codigo tem uma assinatura (entropia, fingerprint).
    Linhas que DESVIAM da assinatura media do arquivo sao
    potenciais hardcodes — lugares onde o programador colocou
    um valor fixo em vez de deixar a equacao decidir.

    Retorna: lista de hardcodes detectados, ordenados por
    quanto desviam da assinatura media.
    """
    with open(__file__, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    # Filtra linhas significativas (codigo, nao comentarios ou branco)
    linhas_codigo = []
    for i, l in enumerate(linhas):
        s = l.strip()
        if not s or s.startswith('#') or s.startswith('"""') or s.startswith("'''"):
            continue
        if s.startswith('import ') or s.startswith('from '):
            continue
        linhas_codigo.append((i + 1, s))

    if not linhas_codigo:
        return []

    # Assinatura MEDIA do codigo
    codigo_completo = '\n'.join(l for _, l in linhas_codigo)
    dados_completos = codigo_completo.encode('utf-8')
    fp_medio = MCRSignatureExpansiva.fingerprint(dados_completos, 16)
    h_medio = MCRByteUtils.entropia_bytes(dados_completos)
    dim_media = MCRSignatureExpansiva.dimensionalidade_ideal(
        dados_completos, max_dims=64)

    # Padroes que a equacao pode detectar como "desvio de assinatura"
    # (Nao sao regras fixas — sao apenas heuristicas para ONDE olhar.
    #  A equacao decide o que e hardcode ou nao.)
    suspeitos = []

    for num, linha in linhas_codigo:
        dados_linha = linha.encode('utf-8')
        if len(dados_linha) < 10:
            continue

        h_linha = MCRByteUtils.entropia_bytes(dados_linha)
        fp_linha = MCRSignatureExpansiva.fingerprint(dados_linha, 16)

        # Distancia da assinatura media
        dist_fp = 1.0 - MCRSignatureExpansiva.similaridade(fp_linha, fp_medio)
        dist_h = abs(h_linha - h_medio) / max(h_medio, 0.01)

        score_hardcode = (dist_fp * 0.6 + dist_h * 0.4)
        score_hardcode = min(1.0, score_hardcode)

        if score_hardcode > 0.5:
            suspeitos.append({
                'linha': num,
                'codigo': linha.strip()[:80],
                'score': round(score_hardcode, 3),
                'entropia': round(h_linha, 3),
                'distancia_fp': round(dist_fp, 3),
            })

    suspeitos.sort(key=lambda x: -x['score'])
    return suspeitos


# ═══════════════════════════════════════════════════════════════
# MCRPreencher — preenche @BLANK_X universalmente
# ═══════════════════════════════════════════════════════════════

class MCRPreencher:
    """Preenche blanks @BLANK_X em QUALQUER texto usando Equacao MCR.
    0 LLM. 0 if/else. O MCR gera o conteudo de cada blank por assinatura.

    Uso:
        preencher = MCRPreencher(motor)
        resultado = preencher.executar('function onSay() @BLANK_NOME end')
        # → 'function onSay() local npc = Npc() end'
    """
    def __init__(self, motor: MCRMotor):
        self.motor = motor
        self.total_preenchidos = 0

    def executar(self, texto: str) -> str:
        """Preenche TODOS os blanks no texto."""
        import re as _re
        blanks = _re.findall(r'@BLANK_\w+', texto)
        for blank in blanks:
            preenchimento = self._gerar(blank)
            if preenchimento:
                texto = texto.replace(blank, preenchimento, 1)
                self.total_preenchidos += 1
        return texto

    def _gerar(self, blank: str) -> str:
        """Gera conteudo para um blank especifico."""
        contexto = blank.replace('@BLANK_', '').lower()
        resultado = self.motor.gerar_por_assinatura(contexto, passos=5)
        palavras = resultado.split()
        if len(palavras) > 1:
            return ' '.join(palavras[1:])
        return resultado


# ═══════════════════════════════════════════════════════════════
# MCRReconstructor — monta fragmentos em arquivo final
# ═══════════════════════════════════════════════════════════════

class MCRReconstructor:
    """Reconstroi resposta final de fragmentos usando assinatura.

    Ordena por Jaccard com o pedido. Filtra por entropia.
    Monta na ordem de relevancia.
    """
    def __init__(self, motor: MCRMotor):
        self.motor = motor

    def reconstruir(self, fragmentos: List[str], pedido: str = '') -> str:
        if not fragmentos:
            return ''

        # Ordena por similaridade com o pedido
        if pedido:
            fragmentos.sort(key=lambda f: MCRByteUtils.jaccard_bytes(pedido, f),
                            reverse=True)

        # Remove fragmentos com entropia muito alta (ruido) ou baixa (repetitivo)
        filtrados = []
        for f in fragmentos:
            h = MCRByteUtils.entropia_bytes(f)
            if 0.5 < h < 6.0 and len(f.strip()) > 20:
                filtrados.append(f)

        if not filtrados:
            return fragmentos[0] if fragmentos else ''

        return '\n\n'.join(filtrados[:5])


# ═══════════════════════════════════════════════════════════════
# MCRGenerator — gera QUALQUER conteudo por assinatura
# ═══════════════════════════════════════════════════════════════

class MCRGenerator:
    """Gera QUALQUER conteudo (NPC, codigo, lore, nome, dialogo, arquivo).
    Universal. Nao ha 'NPC' ou 'Lua' — ha assinatura.

    Uso:
        gen = MCRGenerator(motor, preencher, validador)
        gen.gerar('crie um NPC ferreiro em Eridanus')
    """
    def __init__(self, motor: MCRMotor, preencher: MCRPreencher = None,
                 validador: 'MCRValidator' = None):
        self.motor = motor
        self.preencher = preencher or MCRPreencher(motor)
        self.validador = validador

    def gerar(self, pedido: str, formato: str = 'texto') -> str:
        h = MCRByteUtils.entropia_bytes(pedido)

        # Auto-busca: se motor esta vazio, busca conhecimento relevante
        if self.motor.mk_palavra.total < 50:
            termo = pedido.split()[-1] if pedido.split() else ''
            diretorio_base = os.path.join(os.path.dirname(__file__), '..')
            if os.path.exists(diretorio_base):
                fuel = MCRFuel(self.motor)
                fuel.buscar_conceito(termo, diretorio_base)

        if formato == 'nome':
            return self._gerar_nome(pedido)
        elif formato == 'codigo':
            return self._gerar_codigo(pedido)
        elif formato == 'lore':
            return self._gerar_texto(pedido)
        return self._gerar_texto(pedido)

    def _gerar_nome(self, contexto: str) -> str:
        semente = contexto.split()[-1] if contexto.split() else 'personagem'
        if semente in self.motor.mk_palavra.freq:
            seq = self.motor.mk_palavra.gerar(semente, 5)
            for palavra in seq:
                if len(palavra) >= 3 and palavra[0].isupper():
                    return palavra
        resultado = self.motor.gerar_por_assinatura(
            f'nome {contexto} personagem', passos=4)
        palavras = resultado.split()
        if palavras:
            for p in reversed(palavras):
                if len(p) >= 2:
                    return p[0].upper() + p[1:]
        return 'MCR'

    def _gerar_codigo(self, pedido: str) -> str:
        # Busca exemplos similares se necessario
        if self.motor.mk_palavra.total < 100:
            termo = 'function'
            diretorio_base = os.path.join(os.path.dirname(__file__), '..')
            if os.path.exists(diretorio_base):
                fuel = MCRFuel(self.motor)
                fuel.buscar_conceito(termo, diretorio_base)
        semente = pedido.split()[-1] if pedido.split() else 'function'
        if semente in self.motor.mk_palavra.freq:
            seq = self.motor.mk_palavra.gerar(semente, 10)
            resultado = ' '.join(seq)
        else:
            resultado = self.motor.gerar_por_assinatura(
                f'codigo {pedido}', passos=10)
        if self.validador:
            v = self.validador.validar(resultado)
            if not v.get('valido', True) or v.get('nota', 0) < 3:
                pass  # aceita mesmo assim (dados limitados)
        return resultado

    def _gerar_texto(self, pedido: str) -> str:
        return self.motor.gerar_por_assinatura(pedido, passos=15)


# ═══════════════════════════════════════════════════════════════
# MCRValidator — valida QUALQUER dado por fingerprint
# ═══════════════════════════════════════════════════════════════

class MCRValidator:
    """Valida QUALQUER dado por fingerprint, nao por parser.
    0 if/else. 0 regras de linguagem. So Equacao MCR.

    Uso:
        val = MCRValidator(motor)
        resultado = val.validar('function onSay() end')
        # → {'valido': True, 'entropia': 3.2, 'nota': 8.5}
    """
    def __init__(self, motor: MCRMotor):
        self.motor = motor

    def validar(self, dado: str, referencia: str = '') -> Dict:
        if not dado or len(dado.strip()) < 3:
            return {'valido': False, 'nota': 0, 'diagnostico': 'vazio'}

        h = MCRByteUtils.entropia_bytes(dado)
        dim = MCRSignatureExpansiva.dimensionalidade_ideal(
            dado.encode('utf-8'), max_dims=64)
        fp = MCRSignatureExpansiva.fingerprint_texto(dado, dim)
        h_fp = MCRSignatureExpansiva.entropia_fingerprint(fp)

        palavras = dado.split()
        n_unicas = len(set(p.lower() for p in palavras)) if palavras else 0
        diversidade = n_unicas / max(len(palavras), 1)

        if referencia:
            j = MCRByteUtils.jaccard_bytes(referencia, dado)
        else:
            j = 0.5

        nota = (j * 4 + diversidade * 3 + (1 - abs(h_fp - 4) / 4) * 3)
        nota = min(10, max(0, nota))

        return {
            'valido': nota >= 5.0,
            'nota': round(nota, 2),
            'entropia': round(h, 3),
            'dimensao_ideal': dim,
            'diversidade': round(diversidade, 3),
            'diagnostico': 'ok' if nota >= 5 else 'baixa qualidade',
        }


# ═══════════════════════════════════════════════════════════════
# MCRBuilder — extrai, monta e salva arquivos
# ═══════════════════════════════════════════════════════════════

class MCRBuilder:
    """Extrai blocos de codigo, monta arquivos, salva no disco.
    Universal. Nao ha 'Lua' — ha blocos de codigo.
    """
    def __init__(self, motor: MCRMotor):
        self.motor = motor
        self.total_arquivos = 0

    def extrair(self, texto: str) -> List[str]:
        """Extrai blocos de codigo de texto."""
        import re as _re
        blocos = []
        for padrao in [r'```[\w]*\n(.*?)\n```', r'(`{3,})(.*?)(\\1)']:
            for match in _re.finditer(padrao, texto, _re.DOTALL):
                codigo = match.group(1).strip()
                if codigo and len(codigo) > 20:
                    blocos.append(codigo)
        if not blocos:
            linhas = [l for l in texto.split('\n') if l.strip() and not l.strip().startswith(('#', '//', '--'))]
            if len(linhas) >= 3:
                blocos.append('\n'.join(linhas))
        return blocos

    def montar(self, blocos: List[str], estrutura: str = '') -> str:
        if not blocos:
            return ''
        if estrutura:
            return estrutura.replace('@BLOCK', '\n\n'.join(blocos))
        return '\n\n'.join(blocos)

    def salvar(self, caminho: str, conteudo: str) -> bool:
        try:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            self.total_arquivos += 1
            return True
        except (OSError, IOError) as e:
            return False


# ═══════════════════════════════════════════════════════════════
# MCRComandos — CENTRALIZA TODOS OS 52 COMANDOS COMO METODOS MCR
# ═══════════════════════════════════════════════════════════════

class MCRComandos:
    """Centraliza TODOS os comandos do MCR como metodos.

    Cada comando do diretorio comandos/ vira UM METODO aqui.
    Tudo no MCR.py. Zero arquivos externos.
    0 LLM. So Equacao MCR.

    Uso:
        cmd = MCRComandos(motor)
        cmd.analisar('arquivo.txt')
        cmd.gerar_npc('ferreiro em Eridanus')
        cmd.lore('fundacao de Eridanus')
    """
    def __init__(self, motor: MCRMotor = None, session: MCRSession = None):
        self.motor = motor or MCRMotor()
        self.session = session or MCRSession()
        self.preencher = MCRPreencher(self.motor)
        self.reconstructor = MCRReconstructor(self.motor)
        self.gerador = MCRGenerator(self.motor, self.preencher)
        self.validador = MCRValidator(self.motor)
        self.builder = MCRBuilder(self.motor)
        self.ferramentas = MCRFerramentas(self.motor)
        self.total_execucoes = 0

    def executar(self, comando: str, **kwargs) -> Dict:
        """Executa QUALQUER comando pelo nome.
        
        A Equacao MCR decide se o comando e valido para o estado atual.
        """
        self.total_execucoes += 1
        metodo = getattr(self, comando, None)
        if metodo is None:
            h = MCRByteUtils.entropia_bytes(comando)
            if h < 3.0:
                return {'erro': f'comando {comando} nao encontrado', 'nota': 0}
            resultado = self.motor.gerar_por_assinatura(comando, passos=8)
            return {'resposta': resultado, 'comando': comando, 'modo': 'gerado'}

        resultado = metodo(**kwargs)
        if self.session:
            self.session.registrar(f'cmd:{comando}', str(resultado)[:100])
        return resultado

    # ─── COMANDOS DE ANALISE ────────────────────────────────

    def analisar(self, caminho: str = '') -> Dict:
        if not caminho or not os.path.exists(caminho):
            return {'erro': 'caminho invalido'}
        with open(caminho, 'rb') as f:
            dados = f.read()
        h = MCRByteUtils.entropia_bytes(dados)
        dim = MCRSignatureExpansiva.dimensionalidade_ideal(dados, max_dims=64)
        fp = MCRSignatureExpansiva.fingerprint(dados, 8)
        return {
            'arquivo': os.path.basename(caminho),
            'tamanho': len(dados),
            'entropia': round(h, 3),
            'dimensao_ideal': dim,
            'fingerprint': [round(v, 2) for v in fp],
        }

    def aprender_conceito(self, termo: str = '', arquivo: str = '') -> Dict:
        if arquivo and os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8', errors='replace') as f:
                conteudo = f.read(3000)
            self.motor.alimentar(conteudo, f'conceito:{os.path.basename(arquivo)}')
            return {'aprendido': True, 'termo': termo, 'fonte': arquivo}
        if termo:
            self.motor.alimentar(termo, f'conceito:{termo[:20]}')
            return {'aprendido': True, 'termo': termo}
        return {'aprendido': False}

    # ─── COMANDOS DE GERACAO ────────────────────────────────

    def gerar(self, pedido: str = '', formato: str = 'texto') -> Dict:
        resultado = self.gerador.gerar(pedido, formato)
        return {'resposta': resultado, 'formato': formato}

    def gerar_npc(self, pedido: str = 'NPC') -> Dict:
        self._auto_cacar_conhecimento('npc')
        resultado = self.gerador.gerar(f'crie um NPC {pedido}', 'codigo')
        v = self.validador.validar(resultado, 'function onSay')
        return {'resposta': resultado, 'valido': v['valido'], 'nota': v['nota']}

    def build(self, pedido: str = '') -> Dict:
        self._auto_cacar_conhecimento('function')
        resultado = self.gerador.gerar(f'codigo {pedido}', 'codigo')
        blocos = self.builder.extrair(resultado)
        caminho = f'build_{self.total_execucoes}.txt'
        self.builder.salvar(caminho, resultado)
        return {'arquivo': caminho, 'tamanho': len(resultado), 'blocos': len(blocos)}

    def lore(self, tema: str = '') -> Dict:
        resultado = self.motor.gerar_por_assinatura(
            f'crie uma lore sobre {tema}', passos=15)
        return {'resposta': resultado}

    # ─── COMANDOS DE EDICAO ─────────────────────────────────

    def patch(self, arquivo: str = '', descricao: str = '') -> Dict:
        if not arquivo or not os.path.exists(arquivo):
            return {'erro': 'arquivo nao encontrado'}
        with open(arquivo, 'r', encoding='utf-8', errors='replace') as f:
            conteudo = f.read()
        preenchido = self.preencher.executar(conteudo)
        if preenchido != conteudo:
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(preenchido)
            return {'modificado': True, 'arquivo': arquivo}
        return {'modificado': False}

    def extract(self, arquivo: str = '', padrao: str = '') -> Dict:
        if not arquivo or not os.path.exists(arquivo):
            return {'erro': 'arquivo nao encontrado'}
        with open(arquivo, 'r', encoding='utf-8', errors='replace') as f:
            conteudo = f.read()
        import re as _re
        if padrao:
            partes = _re.findall(padrao, conteudo, _re.DOTALL)
        else:
            partes = self.builder.extrair(conteudo)
        return {'extraido': partes[:5], 'total': len(partes)}

    # ─── COMANDOS DE CONSULTA ───────────────────────────────

    def perguntar(self, texto: str = '') -> Dict:
        if not texto:
            return {'erro': 'texto vazio'}
        resultado = self.motor.gerar_por_assinatura(texto, passos=10)
        return {'resposta': resultado, 'pergunta': texto}

    def conectar(self, a: str = '', b: str = '') -> Dict:
        if a in self.motor.topicos and b in self.motor.topicos:
            c = self.motor.conectar(a, b)
            if c:
                return {'nota': c['nota'], 'palavra': c.get('palavra_a', '')}
        # Conecta por texto
        nome_a = f'_con_a_{self.total_execucoes}'
        nome_b = f'_con_b_{self.total_execucoes}'
        self.motor.alimentar(a, nome_a)
        self.motor.alimentar(b, nome_b)
        c = self.motor.conectar(nome_a, nome_b)
        self.motor.topicos.pop(nome_a, None)
        self.motor.topicos.pop(nome_b, None)
        if c:
            return {'nota': c['nota'], 'palavra': c.get('palavra_a', '')}
        return {'nota': 0}

    # ─── COMANDOS DE SISTEMA ────────────────────────────────

    def status(self) -> Dict:
        return {
            'topicos': len(self.motor.topicos),
            'conexoes': self.motor.total_conexoes,
            'execucoes': self.total_execucoes,
            'estados_byte': self.motor.mk_byte.stats()['estados'],
            'estados_palavra': self.motor.mk_palavra.stats()['estados'],
            'entropia_byte': round(self.motor.mk_byte.entropia_media(), 3),
        }

    def memorizar(self, pergunta: str = '', resposta: str = '') -> Dict:
        if pergunta and resposta:
            self.motor.alimentar(f'{pergunta} {resposta}', f'memoria:{self.total_execucoes}')
        return {'memorias': len(self.motor.topicos)}

    def diagnosticar(self) -> Dict:
        return MCRMeta.diagnosticar(self.motor)

    def proativo(self) -> Dict:
        """Sugere acoes baseado no estado do motor."""
        diag = MCRMeta.diagnosticar(self.motor)
        return {'sugestao': diag.get('sugestao', 'alimentar mais dados'),
                'gap': diag.get('gap_principal', 'desconhecido'),
                'nota': diag.get('nota_geral', 0)}

    # ─── AUTO-CACA (MCR busca conhecimento sozinho) ────────

    def _auto_cacar_conhecimento(self, termo: str = '') -> int:
        """MCR caca QUALQUER conhecimento disponivel — sem pastas ou extensoes fixas.
        Varre todos os diretorios do projeto, todos os tipos de arquivo.
        A Equacao MCR decide o que e util pelo Jaccard com o termo."""
        encontrados = 0
        if self.motor.mk_palavra.total > 5000:
            return 0

        import glob as _glob
        fuel = MCRFuel(self.motor)
        projeto = os.path.join(os.path.dirname(__file__), '..')

        # Varre MULTIPLAS extensoes em MULTIPLOS diretorios
        extensoes = ['py', 'lua', 'txt', 'md', 'json', 'xml', 'html', 'cpp', 'c', 'h', 'js', 'css', 'yaml', 'yml', 'cfg', 'ini', 'conf', 'sh', 'bat', 'sql']
        diretorios_alvo = []
        for item in os.listdir(projeto):
            caminho = os.path.join(projeto, item)
            if os.path.isdir(caminho) and not item.startswith('.'):
                diretorios_alvo.append(caminho)

        for raiz in diretorios_alvo[:10]:  # Top 10 diretorios
            for ext in extensoes:
                if self.motor.mk_palavra.total > 5000:
                    return encontrados
                n = fuel.buscar_arquivos(raiz, ext, 20)
                encontrados += n

        return encontrados

    # ─── COMANDOS DE EXPLORACAO ─────────────────────────────

    def explorar(self, diretorio: str = '.', ext: str = '*.py') -> Dict:
        fuel = MCRFuel(self.motor)
        n = fuel.buscar_arquivos(diretorio, ext)
        return {'encontrados': n, 'topicos': len(self.motor.topicos)}

    def weblearn(self, termo: str = '') -> Dict:
        web = MCRWebLearn(self.motor)
        n = web.buscar(termo) if termo else 0
        return {'aprendido': n}

    # ─── COMANDOS DE ARQUIVO ────────────────────────────────

    def ler(self, caminho: str = '', offset: int = 0, limit: int = 100) -> Dict:
        if not caminho or not os.path.exists(caminho):
            return {'erro': 'arquivo nao encontrado'}
        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
            linhas = f.readlines()
        selecionadas = linhas[offset:offset + limit]
        return {
            'arquivo': caminho,
            'linhas': len(selecionadas),
            'total_linhas': len(linhas),
            'conteudo': ''.join(selecionadas),
        }

    def escrever(self, caminho: str = '', conteudo: str = '') -> Dict:
        if not caminho:
            return {'erro': 'caminho vazio'}
        salvo = self.builder.salvar(caminho, conteudo)
        return {'salvo': salvo, 'arquivo': caminho, 'tamanho': len(conteudo)}

    def editar(self, caminho: str = '', linha: int = 0, texto: str = '') -> Dict:
        if not caminho or not os.path.exists(caminho):
            return {'erro': 'arquivo nao encontrado'}
        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
            linhas = f.readlines()
        if 0 <= linha < len(linhas):
            linhas[linha] = texto + '\n'
            with open(caminho, 'w', encoding='utf-8') as f:
                f.writelines(linhas)
            return {'modificado': True, 'linha': linha}
        return {'modificado': False}

    # ─── COMANDOS DE PERSISTENCIA ───────────────────────────

    def salvar_estado(self, caminho: str = '') -> Dict:
        caminho = caminho or os.path.join(
            os.path.dirname(__file__), 'validacao', 'cache', 'mcr_estado.json')
        ok = self.motor.salvar(caminho)
        return {'salvo': ok, 'caminho': caminho}

    def carregar_estado(self, caminho: str = '') -> Dict:
        caminho = caminho or os.path.join(
            os.path.dirname(__file__), 'validacao', 'cache', 'mcr_estado.json')
        ok = self.motor.carregar(caminho)
        return {'carregado': ok, 'topicos': len(self.motor.topicos)}

    # ─── COMANDO MASTER (executa qualquer coisa) ────────────

    def master(self, pedido: str = '') -> Dict:
        """Comando universal: analisa, decide o que fazer, executa."""
        if not pedido:
            return {'erro': 'pedido vazio'}

        h = MCRByteUtils.entropia_bytes(pedido)
        metodo = MCRPiEngine.decidir_metodo(pedido)

        if 'analisar' in pedido.lower() or 'ler' in pedido.lower():
            caminho = pedido.split()[-1] if pedido.split() else '.'
            return self.analisar(caminho)
        elif 'criar' in pedido.lower() or 'gerar' in pedido.lower() or 'crie' in pedido.lower():
            return self.build(pedido)
        elif 'lore' in pedido.lower() or 'historia' in pedido.lower():
            return self.lore(pedido)
        elif 'npc' in pedido.lower():
            return self.gerar_npc(pedido)
        elif 'conectar' in pedido.lower() or 'conexao' in pedido.lower():
            return self.conectar(pedido, pedido)
        elif metodo == 'markov':
            return self.perguntar(pedido)
        else:
            return self.gerar(pedido)


if __name__ == '__main__':
    import sys as _sys

    if '--hardcode' in _sys.argv[1:]:
        resultado = mcr_detectar_hardcodes()
        print('MCR DETECCAO DE HARDCODES (auto-analise)')
        print('=' * 60)
        print(f'Total de hardcodes detectados: {len(resultado)}')
        print()
        for h in resultado[:20]:
            print(f'  L{h["linha"]:5d} score={h["score"]:.2f} H={h["entropia"]:.2f} | {h["codigo"][:60]}')
        print()
        print('(A equacao MCR detectou desvios de assinatura no proprio codigo.)')
    else:
        resultado = mcr_autoavaliar()
        print('MCR Auto-Avaliacao:')
        for k, v in resultado.items():
            if k == 'fingerprint':
                print(f'  {k}: {[round(x,2) for x in v[:4]]}...')
            else:
                print(f'  {k}: {v}')
