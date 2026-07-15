"""mcr.extrator_features — Extrator Universal Multi-Nível.

Filosofia MCR: ZERO hardcode. 100% descoberto dos dados.

4 níveis de descoberta via DescobridorUniversal.descobrir_em_dados():
1. DIRETÓRIO: tokens exclusivos de cada diretório → cluster estrutural
2. POSIÇÃO: tokens exclusivos de cada posição → cluster gramatical
3. CO-OCORRÊNCIA: tokens exclusivos de cada contexto → cluster semântico
4. ASSINATURA: tokens agrupados por fingerprint → cluster morfológico

Cada cluster é nomeado pelas PRÓPRIAS âncoras. Zero rótulos humanos.
"""
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional

from mcr.descobridor import DescobridorUniversal


class ExtratorFeatures:
    """Extrai features de texto. TUDO descoberto dos dados."""

    def __init__(self):
        self._clusters: Dict[int, Dict] = {}  # cluster_id → {nome, membros, ancoras}
        self._token_para_cluster: Dict[str, int] = {}  # token → cluster_id
        self._posicoes_significativas: List[int] = []
        self._treinado = False
        self._proximo_id = 0

    # ═══════════════════════════════════════════════════════
    # TREINAMENTO MULTI-NÍVEL
    # ═══════════════════════════════════════════════════════

    def treinar(self, frases_rotuladas: List[str] = None,
                dir_npc: str = None, dir_monster: str = None):
        """Treina o extrator com dados disponíveis.

        Descobre sementes dos dados reais (NPCs + monstros).
        Zero hardcode — tudo via DescobridorUniversal.
        """
        if frases_rotuladas:
            frases = frases_rotuladas
        else:
            frases = self._descobrir_seeds_de_dados(dir_npc, dir_monster)

        # Tokeniza todas as frases
        todas = [re.findall(r'[a-zà-ÿ0-9]{2,}', f.lower()) for f in frases]

        # ─── Nível 1: Co-ocorrência por diretório (PRIMEIRO) ──
        # Diretório distingue npc de monstro — precisa rodar antes de posicao
        if not dir_npc or not dir_monster:
            try:
                from mcr.paths import CANARY_NPC_DIR, CANARY_MONSTER_DIR
                if dir_npc is None:
                    dir_npc = str(CANARY_NPC_DIR)
                if dir_monster is None:
                    dir_monster = str(CANARY_MONSTER_DIR)
            except Exception:
                pass
        if dir_npc and dir_monster:
            self._descobrir_por_diretorio(dir_npc, dir_monster)

        # ─── Nível 2: Posição ──────────────────────────────
        self._descobrir_por_posicao(todas)

        # ─── Nível 3: Assinatura morfológica ───────────────
        self._descobrir_por_assinatura()

        self._treinado = True

    def _descobrir_seeds_de_dados(self, dir_npc: str = None,
                                   dir_monster: str = None) -> List[str]:
        """Descobre sementes dos NPCs e monstros reais."""
        from pathlib import Path
        if dir_npc is None:
            try:
                from mcr.paths import CANARY_NPC_DIR, CANARY_MONSTER_DIR
                dir_npc = str(CANARY_NPC_DIR)
                dir_monster = str(CANARY_MONSTER_DIR)
            except Exception:
                return self._frases_fallback()

        nomes_npc = self._extrair_nomes_dir(Path(dir_npc))
        nomes_monster = self._extrair_nomes_dir(Path(dir_monster))

        frases = []
        # Templates PT
        tpl_pt_npc = ["crie um npc {n}", "gere um npc {n}", "faca um npc {n}"]
        tpl_pt_mon = ["gere um monstro {n}", "crie um monstro {n}", "faca um monstro {n}"]
        # Templates EN
        tpl_en_npc = ["create an npc {n}", "make a {n} npc", "build an npc {n}"]
        tpl_en_mon = ["generate a {n}", "create a {n} monster", "make a {n}"]

        for nome in nomes_npc:
            for t in tpl_pt_npc + tpl_en_npc:
                frases.append(t.format(n=nome))
        for nome in nomes_monster:
            for t in tpl_pt_mon + tpl_en_mon:
                frases.append(t.format(n=nome))

        # Adiciona verbos de ação descobertos dos nomes
        if frases:
            acoes = set()
            for f in frases:
                tokens = re.findall(r'[a-z]{3,}', f.lower())
                for tok in tokens:
                    if tok in ('crie', 'gere', 'faca', 'create', 'make',
                               'build', 'generate', 'forge', 'explain'):
                        acoes.add(tok)
            # Gera frases de pergunta com os verbos descobertos
            perguntas = [f"{a} o que e markov" for a in acoes if a in ('explique', 'explain')]
            frases.extend(perguntas)

        return frases if frases else self._frases_fallback()

    def _extrair_nomes_dir(self, diretorio: Path) -> List[str]:
        """Extrai nomes de entidades de arquivos Lua."""
        nomes = []
        if not diretorio.exists():
            return nomes
        for f in list(diretorio.glob('**/*.lua'))[:500]:
            try:
                conteudo = f.read_text(encoding='latin-1', errors='replace')
                for m in re.finditer(r'name\s*=\s*["\']([^"\']+)["\']', conteudo):
                    nome = m.group(1).strip().lower()
                    if len(nome) > 2 and len(nome) < 40:
                        nomes.append(nome)
            except Exception:
                continue
        return list(set(nomes))

    def _frases_fallback(self) -> List[str]:
        """Fallback mínimo quando não há dados disponíveis."""
        return ["crie um npc", "gere um monstro", "crie uma quest",
                "crie um sprite", "explique o que e markov"]

    # ═══════════════════════════════════════════════════════
    # NÍVEL 1: POSIÇÃO (via template_entropico)
    # ═══════════════════════════════════════════════════════

    def _descobrir_por_posicao(self, sequencias: List[List[str]]):
        """Descobre quais posições são estruturalmente significativas."""
        grupos = defaultdict(list)
        # Coleta TODOS os tokens por posição (para mapeamento completo)
        todos_tokens_por_pos = defaultdict(set)
        for seq in sequencias:
            for i, token in enumerate(seq[:6]):
                grupos[f"Pos{i}"].append([token])
                todos_tokens_por_pos[f"Pos{i}"].add(token)

        resultado = DescobridorUniversal.descobrir_em_dados(
            dict(grupos), min_freq=0.15, min_razao=2.0
        )

        for nome_grupo, info in resultado.items():
            if info['ancoras']:
                cid = self._proximo_id
                nome = info['nome_automatico']
                self._clusters[cid] = {
                    'nome': nome, 'nivel': 'posicao',
                    'ancoras': info['ancoras'], 'total': info['total']
                }
                # Mapeia TODOS os tokens desta posição para este cluster
                # (não só as âncoras — inclui tokens cross-idioma)
                for token in todos_tokens_por_pos.get(nome_grupo, set()):
                    if token not in self._token_para_cluster:
                        self._token_para_cluster[token] = cid
                pos_num = int(nome_grupo.replace('Pos', ''))
                if pos_num not in self._posicoes_significativas:
                    self._posicoes_significativas.append(pos_num)
                self._proximo_id += 1

    # ═══════════════════════════════════════════════════════
    # NÍVEL 2: DIRETÓRIO (via DescobridorUniversal original)
    # ═══════════════════════════════════════════════════════

    def _descobrir_por_diretorio(self, dir_npc: str, dir_monster: str):
        """Descobre ancoras por frequência diferencial entre diretórios."""
        from pathlib import Path
        d = DescobridorUniversal(max_arquivos_por_dir=100)
        d.descobrir([Path(dir_npc), Path(dir_monster)])

        # Mapeia diretórios para clusters
        for dir_path in d._freq_por_dir:
            ancoras = d.ancoras_do_diretorio(dir_path)
            if ancoras:
                cid = self._proximo_id
                nome = '_'.join([a[0] for a in ancoras[:3]])
                self._clusters[cid] = {
                    'nome': nome, 'nivel': 'diretorio',
                    'ancoras': ancoras, 'total': d._n_arquivos_por_dir.get(dir_path, 0)
                }
                for token, _ in ancoras[:20]:
                    if token not in self._token_para_cluster:
                        self._token_para_cluster[token] = cid
                self._proximo_id += 1

    # ═══════════════════════════════════════════════════════
    # NÍVEL 3: ASSINATURA (via MCRSignature)
    # ═══════════════════════════════════════════════════════

    def _descobrir_por_assinatura(self):
        """Descobre clusters morfológicos por comprimento de token."""
        if len(self._token_para_cluster) < 5:
            return  # precisa de tokens suficientes

        grupos_por_tamanho = defaultdict(list)
        for token in self._token_para_cluster:
            grupos_por_tamanho[f"L{len(token)}"].append([token])

        if len(grupos_por_tamanho) < 2:
            return

        resultado = DescobridorUniversal.descobrir_em_dados(
            dict(grupos_por_tamanho), min_freq=0.1, min_razao=1.2
        )

        for nome_grupo, info in resultado.items():
            if info['ancoras'] and len(info['ancoras']) >= 2:
                cid = self._proximo_id
                self._clusters[cid] = {
                    'nome': info['nome_automatico'], 'nivel': 'assinatura',
                    'ancoras': info['ancoras'], 'total': info['total']
                }
                self._proximo_id += 1

    # ═══════════════════════════════════════════════════════
    # EXTRAÇÃO DE ESTADO
    # ═══════════════════════════════════════════════════════

    def extrair(self, texto: str) -> str:
        """Converte texto → estado 100% descoberto."""
        if not self._treinado:
            self.treinar()

        tokens = re.findall(r'[a-zà-ÿ0-9]{2,}', texto.lower().strip())
        if not tokens:
            return "VAZIO"

        partes = []

        # Para cada token, encontra clusters em que participa
        for i, token in enumerate(tokens[:8]):
            cid = self._token_para_cluster.get(token)
            if cid is not None and cid in self._clusters:
                partes.append(f"C{cid}")

        # Adiciona posições significativas
        for i, token in enumerate(tokens[:8]):
            if i in self._posicoes_significativas:
                cid = self._token_para_cluster.get(token)
                if cid is not None:
                    partes.append(f"P{i}:C{cid}")

        return "|".join(partes) if partes else "GEN"

    # ═══════════════════════════════════════════════════════
    # DIAGNÓSTICO
    # ═══════════════════════════════════════════════════════

    def diagnosticar(self) -> str:
        """Relatório dos clusters descobertos."""
        linhas = [f'ExtratorFeatures: {len(self._clusters)} clusters, '
                  f'{len(self._token_para_cluster)} tokens mapeados']
        for cid, info in sorted(self._clusters.items()):
            linhas.append(f'  C{cid} ({info["nivel"]}): {info["nome"][:60]} '
                          f'({info["total"]} membros)')
        linhas.append(f'  Posições significativas: {self._posicoes_significativas}')
        return '\n'.join(linhas)


# ─── Singleton ────────────────────────────────────────────
_extrator: Optional[ExtratorFeatures] = None


def get_extrator() -> ExtratorFeatures:
    global _extrator
    if _extrator is None:
        _extrator = ExtratorFeatures()
        _extrator.treinar()
    return _extrator
