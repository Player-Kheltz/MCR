"""mcr.descobridor — Descoberta Universal de Domínios.

Filosofia MCR: ZERO hardcode. ZERO conhecimento de domínio.

Estratégia: para cada diretório de entrada, descobre âncoras
(tokens que aparecem muito neste diretório e pouco nos outros).
Âncoras são os "marcadores" que definem o domínio.

Aplica-se a qualquer tipo de arquivo em qualquer diretório.
"""
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple, Optional


class DescobridorUniversal:
    """Descobre âncoras de domínio por frequência diferencial."""

    def __init__(self, max_arquivos_por_dir: int = 100):
        self._max = max_arquivos_por_dir
        self._freq_por_dir: Dict[Path, Counter] = {}       # dir → Counter(token→count)
        self._n_arquivos_por_dir: Dict[Path, int] = {}      # dir → total files
        self._ancoras: Dict[str, List[Path]] = defaultdict(list)  # token → [dirs onde é âncora]
        self._todas_ancoras: Set[str] = set()
        self._treinado = False

    _STOP_TOKENS = {
        # Tokens ultra-comuns em qualquer linguagem de programação
        # (auto-descobertos como top-N globais. Mantidos como fallback.)
        'local','function','end','if','then','else','elseif','return','for',
        'do','while','nil','true','false','and','or','not','in','self',
    }

    def _descobrir_stop_tokens(self, todos_arquivos: List) -> set:
        """Descobre stop tokens automaticamente (top-N mais frequentes globalmente)."""
        freq_global = Counter()
        for _, token_freq in todos_arquivos:
            for token in token_freq:
                freq_global[token] += 1
        # Top 30 tokens globais → provavelmente ruído estrutural
        return {t for t, _ in freq_global.most_common(30)}

    def _tokenizar(self, conteudo: str) -> Counter:
        """Extrai tokens e conta frequência, removendo stopwords."""
        tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', conteudo)
        freq = Counter()
        for t in tokens:
            tlow = t.lower()
            if tlow not in self._STOP_TOKENS and len(tlow) >= 3:
                freq[tlow] += 1
        return freq

    def _ler_diretorio(self, diretorio: Path) -> List[Tuple[Path, Counter]]:
        arquivos = []
        if not diretorio.exists():
            return arquivos
        for f in diretorio.glob('*'):
            if f.is_file() and f.suffix in ('.lua','.sql','.py','.cpp','.h','.txt','.xml','.json','.cfg','.css','.js','.ts','.html','.md'):
                try:
                    c = f.read_text(encoding='utf-8', errors='replace')[:8000]
                except Exception:
                    try:
                        c = f.read_text(encoding='latin-1', errors='replace')[:8000]
                    except Exception:
                        continue
                arquivos.append((f, self._tokenizar(c)))
                if len(arquivos) >= self._max:
                    break
        return arquivos

    def descobrir(self, diretorios: List[Path], min_razao: float = 5.0,
                  min_freq: float = 0.3):
        """Pipeline completo de descoberta.

        Para cada diretório, descobre tokens que são âncoras
        (muito mais frequentes aqui que nos outros diretórios).

        Args:
            diretorios: lista de Paths para diretórios
            min_razao: razão mínima entre frequência neste dir vs média dos outros
            min_freq: frequência mínima no diretório para ser considerado
        """
        # 1. Lê todos os diretórios
        todos_arquivos = {}
        for d in diretorios:
            arquivos = self._ler_diretorio(d)
            if arquivos:
                freq_geral = Counter()
                for _, token_freq in arquivos:
                    # Presença (binária): token aparece ou não no arquivo
                    for token in token_freq:
                        freq_geral[token] += 1
                self._freq_por_dir[d] = freq_geral
                self._n_arquivos_por_dir[d] = len(arquivos)
                todos_arquivos[d] = arquivos

        if len(self._freq_por_dir) < 2:
            self._treinado = True
            return self

        # 2. Para cada diretório, descobre âncoras
        for d in self._freq_por_dir:
            n_d = self._n_arquivos_por_dir[d]
            freq_d = self._freq_por_dir[d]

            # Calcula frequência média nos OUTROS diretórios
            freq_outros = Counter()
            n_outros_total = 0
            for outro_d in self._freq_por_dir:
                if outro_d == d:
                    continue
                n_outros_total += self._n_arquivos_por_dir[outro_d]

            for outro_d in self._freq_por_dir:
                if outro_d == d:
                    continue
                freq_o = self._freq_por_dir[outro_d]
                n_o = self._n_arquivos_por_dir[outro_d]
                for token, count in freq_o.items():
                    freq_outros[token] += count

            # Descobre âncoras
            for token, count in freq_d.most_common(300):
                freq_aqui = count / n_d
                if freq_aqui < min_freq:
                    continue

                count_fora = freq_outros.get(token, 0)
                freq_fora = count_fora / max(n_outros_total, 1)
                # Razão: quantas vezes mais frequente aqui
                razao = freq_aqui / max(freq_fora, 0.001)

                if razao > min_razao:
                    self._ancoras[token].append(d)
                    self._todas_ancoras.add(token)

        self._treinado = True
        return self

    def classificar(self, token: str) -> Optional[str]:
        """Retorna nome do diretório onde este token é âncora."""
        token_lower = token.lower()
        dirs = self._ancoras.get(token_lower, [])
        if dirs:
            return dirs[0].name  # primeiro diretório onde é âncora
        return None

    def ancoras_do_diretorio(self, diretorio: Path) -> List[Tuple[str, float]]:
        """Retorna âncoras de um diretório com suas razões."""
        resultado = []
        n = self._n_arquivos_por_dir.get(diretorio, 1)
        freq = self._freq_por_dir.get(diretorio, Counter())
        for token, dirs in self._ancoras.items():
            if diretorio in dirs:
                freq_aqui = freq.get(token, 0) / n
                resultado.append((token, round(freq_aqui, 3)))
        resultado.sort(key=lambda x: -x[1])
        return resultado

    def estatisticas(self) -> Dict:
        return {
            'diretorios': len(self._freq_por_dir),
            'arquivos_total': sum(self._n_arquivos_por_dir.values()),
            'ancoras_total': len(self._todas_ancoras),
            'ancoras_por_dir': {
                str(d): len(self.ancoras_do_diretorio(d))
                for d in self._freq_por_dir
            },
        }

    # ═══════════════════════════════════════════════════════
    # API GENERALIZADA: Descobre em qualquer Dict[str, List]
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def descobrir_em_dados(grupos: Dict[str, List[List]],
                           min_freq: float = 0.25,
                           min_razao: float = 3.0) -> Dict[str, Dict]:
        """Descobre âncoras em dados arbitrários, não apenas arquivos.

        Args:
            grupos: {nome_do_grupo: [ [unidades_do_membro1], [unidades_do_membro2], ... ]}

        Returns:
            {nome_do_grupo: {
                'ancoras': [(token, freq_no_grupo), ...],
                'total': n_membros
            }}
        """
        resultado = {}
        nomes = list(grupos.keys())

        # Conta frequência de cada token em cada grupo
        freq_por_grupo = {}
        n_por_grupo = {}
        for nome, membros in grupos.items():
            freq = Counter()
            for unidades in membros:
                for u in set(unidades):  # presença binária
                    freq[str(u)] += 1
            freq_por_grupo[nome] = freq
            n_por_grupo[nome] = len(membros)

        # Para cada grupo, descobre âncoras
        for nome in nomes:
            freq_grupo = freq_por_grupo[nome]
            n_grupo = n_por_grupo[nome]
            if n_grupo == 0:
                resultado[nome] = {'ancoras': [], 'total': 0}
                continue

            # Frequência nos outros grupos
            freq_outros = Counter()
            n_outros = 0
            for outro in nomes:
                if outro != nome:
                    n_outros += n_por_grupo[outro]
            for outro in nomes:
                if outro != nome:
                    for token, count in freq_por_grupo[outro].items():
                        freq_outros[token] += count

            # Seleciona âncoras
            ancoras = []
            for token, count in freq_grupo.most_common(100):
                freq_aqui = count / n_grupo
                if freq_aqui < min_freq:
                    continue
                freq_fora = freq_outros.get(token, 0) / max(n_outros, 1)
                razao = freq_aqui / max(freq_fora, 0.001)
                if razao > min_razao:
                    ancoras.append((token, round(freq_aqui, 3)))

            resultado[nome] = {
                'ancoras': ancoras[:20],
                'total': n_grupo,
                'nome_automatico': '_'.join([a[0] for a in ancoras[:3]]) if ancoras else f'GRUPO_{nome}'
            }

        return resultado
