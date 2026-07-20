"""mcr.auto_expansao — Curiosidade dirigida por entropia.

O MCR identifica onde sua entropia é maior (maior incerteza) e
ativamente busca novos dados para reduzi-la.

Princípio: curiosidade = busca por máxima redução de entropia.
- Onde H(P(acao|palavra)) é alta → MCR está incerto →好奇
- Após aprender, H deve diminuir → curiosidade satisfeita

5 capacidades:
1. Identificar gaps — palavras/áreas com entropia máxima
2. Gerar perguntas — queries baseadas em palavras de alta entropia
3. Buscar conhecimento — vasculhar fontes de texto disponíveis
4. Aprender — alimentar coupling com novos exemplos
5. Verificar — medir redução de entropia (ganho de informação)

Tudo Markov + entropia. Zero GPU, zero dependências externas.
"""
import re
import math
import os
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any, Set
from pathlib import Path


class AutoExpansao:
    """Curiosidade dirigida por entropia.

    O MCR observa seu próprio modelo e identifica onde está mais incerto.
    Gera perguntas sobre essas áreas, busca texto em fontes disponíveis,
    aprende com o que encontra, e verifica se a entropia diminuiu.

    Uso:
        ae = AutoExpansao(coupling)
        ae.adicionar_fonte("caminho/arquivo.txt")
        ae.adicionar_fonteTexto("conteúdo direto")
        resultado = ae.ciclo_curiosidade()
    """

    def __init__(self, coupling):
        self._coupling = coupling
        self._fontes_texto: List[str] = []  # conteúdo direto
        self._fontes_arquivo: List[str] = []  # caminhos de arquivos
        self._diretorios: List[str] = []  # diretórios para vasculhar
        # Histórico de exploração
        self._n_ciclos = 0
        self._n_exemplos_aprendidos = 0
        self._reducoes_entropia: List[Tuple[str, float, float]] = []
        # Palavras já exploradas (evita reexplorar)
        self._exploradas: Set[str] = set()
        # Histórico de entropia por palavra (para detectar convergência)
        self._historico_h: Dict[str, List[float]] = defaultdict(list)

    # ═══════════════════════════════════════════════════════════════
    # FONTES DE CONHECIMENTO
    # ═══════════════════════════════════════════════════════════════

    def adicionar_fonte(self, caminho_ou_texto: str) -> None:
        """Adiciona uma fonte de conhecimento.

        Se é um caminho de arquivo válido, registra como arquivo.
        Se é um diretório, registra para vasculhar.
        Senão, trata como texto direto.
        """
        if os.path.isfile(caminho_ou_texto):
            self._fontes_arquivo.append(caminho_ou_texto)
        elif os.path.isdir(caminho_ou_texto):
            self._diretorios.append(caminho_ou_texto)
        else:
            self._fontes_texto.append(caminho_ou_texto)

    def adicionar_diretorio(self, caminho: str,
                            extensoes: Tuple[str, ...] = ('.txt', '.md', '.py')
                            ) -> None:
        """Adiciona um diretório para vasculhar em busca de conhecimento."""
        self._diretorios.append(caminho)
        self._extensoes = extensoes

    # ═══════════════════════════════════════════════════════════════
    # 1. IDENTIFICAR GAPS POR ENTROPIA
    # ═══════════════════════════════════════════════════════════════

    def identificar_gaps(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Identifica palavras com maior entropia (maior incerteza).

        Cada palavra no vocabulário tem uma distribuição P(acao|palavra).
        Palavras com H alta = MCR não sabe qual ação associar = gap.

        Retorna lista ordenada por entropia (maior primeiro).
        """
        gaps = []

        for palavra, dist in self._coupling._palavra_acao.items():
            total = sum(dist.values())
            if total < 2:
                continue  # poucos exemplos — não é gap, é novidade

            h = self._entropia_dist(dist)
            max_h = math.log2(max(len(dist), 2))
            h_norm = h / max_h if max_h > 0 else 0

            # Potencial de redução: se H é alta e temos poucos exemplos,
            # aprender mais pode reduzir H significativamente
            potencial = h_norm * (1.0 / math.log2(max(total, 2) + 1))

            # Pular se já foi explorada e H não reduziu (convergida)
            if palavra in self._exploradas:
                hist = self._historico_h.get(palavra, [])
                if len(hist) >= 3:
                    # Se H não mudou nas últimas 3 explorações, pular
                    delta = abs(hist[-1] - hist[-3])
                    if delta < 0.01:
                        continue

            gaps.append({
                'palavra': palavra,
                'entropia': round(h_norm, 4),
                'potencial_reducao': round(potencial, 4),
                'n_exemplos': total,
                'n_acoes': len(dist),
                'acoes': dict(dist),
            })

        gaps.sort(key=lambda x: -x['potencial_reducao'])
        return gaps[:top_n]

    # ═══════════════════════════════════════════════════════════════
    # 2. GERAR PERGUNTAS
    # ═══════════════════════════════════════════════════════════════

    def gerar_perguntas(self, gap: Dict[str, Any], top_k: int = 5
                        ) -> List[str]:
        """Gera queries de busca para um gap identificado.

        Para uma palavra de alta entropia, gera:
        1. A própria palavra (busca direta)
        2. Palavras que co-ocorrem com ela (via _transicao_palavra)
        3. Palavras similares (via NMI de assinaturas)
        4. Bigramas que contêm a palavra
        """
        palavra = gap['palavra']
        queries = [palavra]

        # Co-ocorrências (palavras que aparecem depois de `palavra`)
        vizinhos = self._coupling._transicao_palavra.get(palavra, {})
        for v, _ in sorted(vizinhos.items(), key=lambda x: -x[1])[:3]:
            queries.append(f"{palavra} {v}")

        # Palavras similares via NMI
        sig_p = self._coupling._assinatura_palavra(palavra)
        if sig_p:
            similares = []
            for outra in self._coupling._palavra_acao:
                if outra == palavra:
                    continue
                sig_o = self._coupling._assinatura_palavra(outra)
                if sig_o:
                    nmi = self._coupling._nmi(sig_p, sig_o)
                    if nmi > 0.3:
                        similares.append((outra, nmi))
            similares.sort(key=lambda x: -x[1])
            for s, _ in similares[:3]:
                queries.append(s)

        return queries[:top_k]

    # ═══════════════════════════════════════════════════════════════
    # 3. BUSCAR CONHECIMENTO
    # ═══════════════════════════════════════════════════════════════

    def buscar_conhecimento(self, queries: List[str],
                            max_fragmentos: int = 20
                            ) -> List[Tuple[str, str]]:
        """Vasculha fontes disponíveis em busca de fragmentos relevantes.

        Returns:
            Lista de (fragmento, query_que_match) ordenado por relevância.
        """
        fragmentos = []

        # Texto direto
        for texto in self._fontes_texto:
            frags = self._extrair_fragmentos(texto, queries)
            fragmentos.extend(frags)

        # Arquivos
        for caminho in self._fontes_arquivo:
            try:
                with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                    conteudo = f.read()
                frags = self._extrair_fragmentos(conteudo, queries)
                fragmentos.extend(frags)
            except Exception:
                pass

        # Diretórios
        for diretorio in self._diretorios:
            frags = self._vasculhar_diretorio(diretorio, queries)
            fragmentos.extend(frags)

        # Ordenar por relevância (número de queries que match)
        fragmentos.sort(key=lambda x: -len(x[1]))
        return fragmentos[:max_fragmentos]

    def _extrair_fragmentos(self, texto: str,
                            queries: List[str]) -> List[Tuple[str, str]]:
        """Extrai fragmentos de texto que contêm as queries."""
        # Split em frases (por pontuação ou newlines)
        frases = re.split(r'[.!?;\n]+', texto)
        resultado = []

        for frase in frases:
            frase = frase.strip()
            if len(frase) < 5:
                continue
            frase_lower = frase.lower()
            queries_match = []
            for q in queries:
                if q.lower() in frase_lower:
                    queries_match.append(q)
            if queries_match:
                resultado.append((frase, queries_match))

        return resultado

    def _vasculhar_diretorio(self, diretorio: str,
                             queries: List[str],
                             max_arquivos: int = 50
                             ) -> List[Tuple[str, str]]:
        """Vasculha um diretório em busca de arquivos relevantes."""
        fragmentos = []
        exts = getattr(self, '_extensoes', ('.txt', '.md', '.py'))

        try:
            arquivos = []
            for raiz, _, nomes in os.walk(diretorio):
                for nome in nomes:
                    if any(nome.endswith(ext) for ext in exts):
                        arquivos.append(os.path.join(raiz, nome))
                if len(arquivos) >= max_arquivos:
                    break

            for caminho in arquivos[:max_arquivos]:
                try:
                    with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read(5000)  # limitar leitura
                    frags = self._extrair_fragmentos(conteudo, queries)
                    fragmentos.extend(frags)
                except Exception:
                    pass
        except Exception:
            pass

        return fragmentos

    # ═══════════════════════════════════════════════════════════════
    # 4. APRENDER
    # ═══════════════════════════════════════════════════════════════

    def aprender_fragmentos(self, fragmentos: List[Tuple[str, str]],
                            gap: Dict[str, Any]) -> int:
        """Alimenta o coupling com fragmentos encontrados.

        Para cada fragmento, infere a ação via decidir() e alimenta.
        Se o fragmento contém a palavra do gap, reforça o aprendizado.

        Returns: número de exemplos aprendidos.
        """
        n_aprendidos = 0
        palavra_gap = gap['palavra']

        for fragmento, _ in fragmentos:
            # Inferir ação do fragmento via o próprio MCR
            acao, conf = self._coupling.decidir(fragmento, (None, 0.0))

            # Se confiança muito baixa, tentar usar a ação mais provável
            # do gap original (a que tem mais count na distribuição)
            if conf < 0.1:
                dist = gap.get('acoes', {})
                if dist:
                    acao = max(dist, key=dist.get)

            # Sem acao viavel → ignora (Pilar 9: honesto, sem veto hardcoded)
            if not acao:
                continue

            # Alimentar
            self._coupling.alimentar(fragmento, acao)
            n_aprendidos += 1

        self._n_exemplos_aprendidos += n_aprendidos
        return n_aprendidos

    # ═══════════════════════════════════════════════════════════════
    # 5. VERIFICAR — medir redução de entropia
    # ═══════════════════════════════════════════════════════════════

    def verificar_reducao(self, palavra: str) -> Tuple[float, float]:
        """Mede entropia atual vs anterior para uma palavra.

        Returns:
            (h_anterior, h_atual) — se h_atual < h_anterior, curiosidade satisfeita.
        """
        dist = self._coupling._palavra_acao.get(palavra, {})
        total = sum(dist.values())
        if total < 2:
            return 0.0, 0.0

        h = self._entropia_dist(dist)
        max_h = math.log2(max(len(dist), 2))
        h_norm = h / max_h if max_h > 0 else 0

        hist = self._historico_h.get(palavra, [])
        h_anterior = hist[-1] if hist else h_norm

        self._historico_h[palavra].append(h_norm)
        return h_anterior, h_norm

    # ═══════════════════════════════════════════════════════════════
    # CICLO COMPLETO DE CURIOSIDADE
    # ═══════════════════════════════════════════════════════════════

    def ciclo_curiosidade(self, max_gaps: int = 3) -> Dict[str, Any]:
        """Executa um ciclo completo de curiosidade dirigida.

        1. Identifica gaps (palavras de alta entropia)
        2. Para cada gap: gera perguntas → busca → aprende → verifica
        3. Retorna relatório do ciclo

        Returns:
            dict com 'gaps_explorados', 'exemplos_aprendidos', 'reducoes'
        """
        self._n_ciclos += 1
        gaps = self.identificar_gaps(top_n=max_gaps)

        if not gaps:
            return {
                'ciclo': self._n_ciclos,
                'gaps_encontrados': 0,
                'gaps_explorados': 0,
                'exemplos_aprendidos': 0,
                'reducoes': [],
                'status': 'sem_gaps',
            }

        resultados = []

        for gap in gaps:
            palavra = gap['palavra']

            # Registrar H anterior
            h_antes = gap['entropia']
            self._historico_h[palavra].append(h_antes)

            # Gerar perguntas
            queries = self.gerar_perguntas(gap)

            # Buscar conhecimento
            fragmentos = self.buscar_conhecimento(queries)

            if not fragmentos:
                self._exploradas.add(palavra)
                resultados.append({
                    'palavra': palavra,
                    'h_antes': h_antes,
                    'h_depois': h_antes,
                    'delta': 0.0,
                    'exemplos': 0,
                    'status': 'sem_fontes',
                })
                continue

            # Aprender
            n = self.aprender_fragmentos(fragmentos, gap)

            # Verificar redução
            h_antes_verif, h_depois = self.verificar_reducao(palavra)
            delta = h_antes - h_depois

            self._exploradas.add(palavra)

            if delta > 0.01:
                self._reducoes_entropia.append((palavra, h_antes, h_depois))

            resultados.append({
                'palavra': palavra,
                'h_antes': round(h_antes, 4),
                'h_depois': round(h_depois, 4),
                'delta': round(delta, 4),
                'exemplos': n,
                'status': 'reduziu' if delta > 0.01 else 'estavel',
            })

        # Status geral
        reducoes = [r for r in resultados if r['status'] == 'reduziu']
        status = 'aprendeu' if reducoes else 'estavel'

        return {
            'ciclo': self._n_ciclos,
            'gaps_encontrados': len(gaps),
            'gaps_explorados': len(resultados),
            'exemplos_aprendidos': sum(r['exemplos'] for r in resultados),
            'reducoes': resultados,
            'status': status,
        }

    # ═══════════════════════════════════════════════════════════════
    # ESTATÍSTICAS
    # ═══════════════════════════════════════════════════════════════

    def estatisticas(self) -> Dict[str, Any]:
        """Estatísticas da exploração curiosa."""
        return {
            'n_ciclos': self._n_ciclos,
            'n_exemplos_aprendidos': self._n_exemplos_aprendidos,
            'n_palavras_exploradas': len(self._exploradas),
            'n_reducoes_entropia': len(self._reducoes_entropia),
            'fontes_texto': len(self._fontes_texto),
            'fontes_arquivo': len(self._fontes_arquivo),
            'diretorios': len(self._diretorios),
        }

    def entropia_vocabulario(self) -> float:
        """Entropia média de todo o vocabulário (saúde cognitiva).

        0 = perfeitamente determinístico (sabe tudo)
        1 = perfeitamente uniforme (nada sabe)
        """
        entropias = []
        for palavra, dist in self._coupling._palavra_acao.items():
            total = sum(dist.values())
            if total < 2:
                continue
            h = self._entropia_dist(dist)
            max_h = math.log2(max(len(dist), 2))
            h_norm = h / max_h if max_h > 0 else 0
            entropias.append(h_norm)
        if not entropias:
            return 0.0
        return sum(entropias) / len(entropias)

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _entropia_dist(dist: Dict[str, int]) -> float:
        """Entropia Shannon de uma distribuição de contagens."""
        total = sum(dist.values())
        if total <= 0:
            return 0.0
        h = 0.0
        for v in dist.values():
            pr = v / total
            if pr > 0:
                h -= pr * math.log2(pr)
        return h
