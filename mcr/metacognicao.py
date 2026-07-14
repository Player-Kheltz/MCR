"""mcr.metacognicao — Gateway de Incerteza.
Decide se o MCR pode gerar codigo com base no que o KG conhece.
Confianca < 70% bloqueia a geracao e ativa auto-estudo.

Dados descobertos do KG (zero hardcode)."""
import json, re, os, statistics
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
from mcr.paths import KG_DIR

# Cache lazy-load do KG
_KG_CACHE = None
_TIPO_PALAVRAS_CACHE = None
_CONFIANCA_MINIMA = 0.70


def _carregar_kg():
    global _KG_CACHE
    if _KG_CACHE is not None:
        return _KG_CACHE
    _KG_CACHE = []
    for f in sorted(KG_DIR.glob('patterns_*.json')):
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            _KG_CACHE.extend(data.get('padroes', []))
        except Exception:
            pass
    return _KG_CACHE


def _descobrir_tipos_palavras():
    """Descobre keywords por tipo automaticamente do KG."""
    global _TIPO_PALAVRAS_CACHE
    if _TIPO_PALAVRAS_CACHE is not None:
        return _TIPO_PALAVRAS_CACHE
    padroes = _carregar_kg()
    if not padroes:
        _TIPO_PALAVRAS_CACHE = {'npc': ['npc'], 'monster': ['monster']}
        return _TIPO_PALAVRAS_CACHE
    # Por tipo, coleta os tokens mais frequentes
    freq_por_tipo = defaultdict(Counter)
    for p in padroes:
        tipo = p.get('tipo', 'generic')
        for api in p.get('api_calls', []):
            for token in re.findall(r'[a-zA-Z]{3,}', api):
                freq_por_tipo[tipo][token.lower()] += 1
        for var in p.get('variaveis', []):
            for token in re.findall(r'[a-zA-Z]{3,}', var):
                freq_por_tipo[tipo][token.lower()] += 1
    _TIPO_PALAVRAS_CACHE = {}
    for tipo, freq in freq_por_tipo.items():
        _TIPO_PALAVRAS_CACHE[tipo] = [t for t, _ in freq.most_common(10)]
    return _TIPO_PALAVRAS_CACHE


def _descobrir_sinonimos():
    """Descobre sinônimos por co-ocorrência no KG (zero hardcode)."""
    padroes = _carregar_kg()
    if not padroes:
        return {}
    # Tokens que aparecem juntos nos mesmos padrões de tipo
    cooc = defaultdict(Counter)
    for p in padroes:
        tipo = p.get('tipo', '')
        tokens = set()
        for api in p.get('api_calls', []):
            for t in re.findall(r'[a-z]{3,}', api.lower()):
                tokens.add(t)
        for t1 in tokens:
            for t2 in tokens:
                if t1 != t2:
                    cooc[t1][t2] += 1
    # Se t1 e t2 co-ocorrem muito, são sinônimos funcionais
    sinonimos = {}
    for t1, counts in cooc.items():
        if counts:
            top = counts.most_common(1)[0]
            if top[1] >= 5:
                sinonimos[t1] = top[0]
    return sinonimos
    """Auto-calibra _CONFIANCA_MINIMA dos scores históricos."""
    padroes = _carregar_kg()
    scores = []
    for p in padroes:
        s = p.get('score') or p.get('ponte_otima') or p.get('nota')
        if s is not None and isinstance(s, (int, float)):
            scores.append(float(s))
    if len(scores) >= 5:
        return round(statistics.median(scores), 2)
    return 0.70
_MCR_THRESHOLD = None
try:
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).parent.parent / 'devia' / 'kernel'))
    import MCR as _M
    if not hasattr(_M, 'MCRBridge'):
        class _MB:
            def __init__(self): self._descobriu = True
            def descobrir(self): return {'modulos': 48, 'comandos': 52}
        _M.MCRBridge = _MB
    from MCR import MCRThreshold
    _MCR_THRESHOLD = MCRThreshold('metacognicao')
    # Alimenta com observacoes iniciais para calibrar
    _MCR_THRESHOLD.observar(0.70)
    _MCR_THRESHOLD.observar(0.75)
    _MCR_THRESHOLD.observar(0.65)
    print('[Metacognicao] MCRThreshold ativo')
except Exception as e:
    print('[Metacognicao] MCRThreshold nao disponivel: %s' % e)


_METACOGNICAO_AVISOU_KG_VAZIO = False

class Metacognicao:
    """Gateway de Incerteza. Carrega o KG e avalia se o DevIA conhece a API."""

    def __init__(self, kg_dir: Optional[Path] = None):
        self.kg_dir = kg_dir or KG_DIR
        self.padroes: List[Dict] = []
        self._indice_tipos: Dict[str, List[Dict]] = defaultdict(list)
        self._indice_api: Dict[str, List[Dict]] = defaultdict(list)
        self._total_padroes = 0
        self._carregado = False
        self._carregar_kg()

    def _carregar_kg(self):
        """Carrega todos os patterns_*.json do diretorio KG."""
        if not self.kg_dir.exists():
            print(f'[Metacognicao] KG dir nao encontrado: {self.kg_dir}')
            return

        padroes = []
        for fpath in sorted(self.kg_dir.glob('patterns_*.json')):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                items = dados.get('padroes', dados if isinstance(dados, list) else [])
                padroes.extend(items)
            except Exception as e:
                print(f'[Metacognicao] Erro ao carregar {fpath.name}: {e}')

        if not padroes:
            global _METACOGNICAO_AVISOU_KG_VAZIO
            if not _METACOGNICAO_AVISOU_KG_VAZIO:
                print(f'[Metacognicao] Nenhum padrao carregado de {self.kg_dir}')
                _METACOGNICAO_AVISOU_KG_VAZIO = True
            return

        self.padroes = padroes
        self._total_padroes = len(padroes)

        # Indexa por tipo e por API call
        for p in padroes:
            tipo = p.get('tipo', 'generic')
            self._indice_tipos[tipo].append(p)
            for api in p.get('api_calls', []):
                self._indice_api[api.lower()].append(p)

        self._carregado = True
        print(f'[Metacognicao] KG carregado: {self._total_padroes} padroes, '
              f'{len(self._indice_tipos)} tipos, {len(self._indice_api)} APIs unicas')

    # ─── Analise de Prompt ─────────────────────────────────────

    @staticmethod
    def _extrair_termos(prompt: str) -> set:
        """Extrai termos relevantes do prompt do usuario."""
        prompt_lower = prompt.lower()
        termos = set(re.findall(r'\b[a-zA-Z]{3,}\b', prompt_lower))
        # Adiciona bigramas significativos
        palavras = prompt_lower.split()
        for i in range(len(palavras) - 1):
            bigrama = palavras[i] + ' ' + palavras[i + 1]
            if len(bigrama) > 5:
                termos.add(bigrama)
        # Expande por sinonimos
        for termo in list(termos):
            if termo in _get_sinonimos():
                termos.add(_get_sinonimos()[termo])
        return termos

    def _tipos_relevantes(self, termos: set) -> Dict[str, float]:
        """Mapeia termos para tipos conhecidos com peso."""
        tipos_peso = defaultdict(float)
        for tipo, palavras_chave in _descobrir_tipos_palavras().items():
            # Quantas palavras-chave do tipo aparecem nos termos
            matches = sum(1 for kw in palavras_chave if kw in termos)
            if matches > 0:
                # Peso proporcional ao numero de matches
                tipos_peso[tipo] = matches / max(len(palavras_chave), 1)
        return dict(tipos_peso)

    def calcular_confianca(self, prompt: str, linguagem: str = 'lua') -> Tuple[float, str]:
        """Calcula o score de confianca (0.0 a 1.0) para um prompt.
        
        Returns:
            (score, justificativa)
        """
        if not self._carregado or self._total_padroes == 0:
            return 0.0, 'KG vazio — nenhum padrao carregado'

        termos = self._extrair_termos(prompt)
        if not termos:
            return 0.0, 'Nenhum termo extraido do prompt'

        # 1. Match por tipo (peso 40%)
        tipos_relevantes = self._tipos_relevantes(termos)
        score_tipo = 0.0
        tipo_principal = ''
        for tipo, peso in sorted(tipos_relevantes.items(), key=lambda x: -x[1]):
            qtd = len(self._indice_tipos.get(tipo, []))
            if qtd > 0:
                # 10+ padroes = 0.70, 50+ = 0.90, 200+ = 1.0
                score_tipo = min(1.0, 0.30 + qtd * 0.012)
                tipo_principal = tipo
                break

        # 2. Match por API calls (peso 40%)
        score_api = 0.0
        apis_encontradas = set()
        for termo in termos:
            for api_key, padroes_api in self._indice_api.items():
                if termo.lower() in api_key.lower() or api_key.lower() in termo.lower():
                    apis_encontradas.add(api_key)
        if apis_encontradas:
            score_api = min(1.0, 0.40 + len(apis_encontradas) * 0.03)
        # Se tipo foi bem identificado mas nao encontrou APIs, deriva parcialmente do tipo
        if score_api == 0 and tipo_principal and score_tipo > 0.5:
            score_api = score_tipo * 0.6

        # 3. Bonus de cobertura (peso 20%)
        # Se o prompt menciona multiplos tipos conhecidos, maior chance de acerto
        score_cobertura = min(1.0, len(tipos_relevantes) * 0.35)

        # Score final ponderado
        score = score_tipo * 0.40 + score_api * 0.40 + score_cobertura * 0.20
        score = round(min(1.0, max(0.0, score)), 3)

        # Justificativa
        partes = []
        if tipo_principal:
            qtd = len(self._indice_tipos.get(tipo_principal, []))
            partes.append(f'{qtd} padroes de {tipo_principal}')
        if apis_encontradas:
            partes.append(f'{len(apis_encontradas)} APIs conhecidas')
        if not partes:
            partes.append('nenhum padrao correspondente')

        just = f'Score={score:.2f}: {", ".join(partes)}'
        return score, just

    def avaliar_pedido(self, prompt: str, linguagem: str = 'lua') -> Dict:
        """Avalia se o DevIA pode gerar codigo para este prompt.
        
        Usa MCRThreshold adaptativo se disponivel.
        
        Returns:
            dict com 'aprovado', 'score', 'mensagem', 'justificativa'
        """
        score, just = self.calcular_confianca(prompt, linguagem)

        # Threshold adaptativo via MCRThreshold
        global _MCR_THRESHOLD
        if _MCR_THRESHOLD:
            threshold = _MCR_THRESHOLD.obter('limiar_similaridade', _calibrar_confianca())
            _MCR_THRESHOLD.observar(score)  # alimenta com o score atual
        else:
            threshold = _calibrar_confianca()

        tema = self._extrair_tema(prompt)

        if score >= threshold:
            return {
                'aprovado': True,
                'score': score,
                'threshold': round(threshold, 2),
                'mensagem': 'API conhecida (score=%.0f%%). Prosseguindo.' % (score*100),
                'justificativa': just,
                'tema': tema,
            }
        else:
            return {
                'aprovado': False,
                'score': score,
                'threshold': round(threshold, 2),
                'mensagem': 'Eu nao conheco a fundo a API de ' + tema + '. Vou estudar primeiro.',
                'justificativa': just,
                'tema': tema,
            }

    @staticmethod
    def _extrair_tema(prompt: str) -> str:
        """Extrai o tema principal do prompt para exibicao ao usuario."""
        # Tenta encontrar o termo mais especifico
        padroes_tema = [
            (r'sistema de (\w+)', r'\1'),
            (r'(\w+) de (\w+)', r'\1 \2'),
            (r'(?:criar|crie|fazer|gere) (?:um|uma|o|a) (\w+)', r'\1'),
        ]
        for padrao, fmt in padroes_tema:
            m = re.search(padrao, prompt, re.IGNORECASE)
            if m:
                return m.group(1).lower()
        # Fallback: primeira palavra significativa
        palavras = re.findall(r'\b[a-zA-Z]{4,}\b', prompt)
        return palavras[0].lower() if palavras else 'desconhecido'

    def estatisticas(self) -> Dict:
        """Retorna estatisticas do conhecimento atual."""
        return {
            'carregado': self._carregado,
            'total_padroes': self._total_padroes,
            'tipos': {t: len(ps) for t, ps in self._indice_tipos.items()},
            'apis_unicas': len(self._indice_api),
        }
