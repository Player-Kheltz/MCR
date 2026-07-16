#!/usr/bin/env python3
"""
scripts/treinar_tudo.py — FASE 2: Treina MCR com TODOS os dados disponiveis.

Fontes de dados:
  1. cache/npc_knowledge.json       (132K linhas, 13.751 dialogos, 1163 NPCs)
  2. devia/knowledge/dialogos_npc.json (20.8K linhas)
  3. cache/cerebro.json             (6.227 topicos)
  4. E:\Coisas\sandbox\.mcr_devia\kg\ (52+ arquivos KG)
  5. data/generated/sql_corpus/     (4 dominios SQL)
  6. golden_examples/               (3 templates Lua)
  7. devia/knowledge/autobiography.json (1.1K linhas self-knowledge)

Destinos:
  - MCRSQLite: conversa + codigo
  - SDM: topicos + conceitos
  - KG unificado: todos os conhecimentos

Uso:
    python scripts/treinar_tudo.py              # Treina tudo
    python scripts/treinar_tudo.py --dry-run     # Apenas verifica dados
    python scripts/treinar_tudo.py --conversa    # Apenas conversa
    python scripts/treinar_tudo.py --codigo      # Apenas codigo
"""
import sys
import os
import json
import re
import time
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

sys.path.insert(0, _BASE)

from mcr.paths import CACHE_DIR, KG_DIR, GOLDEN_EXAMPLES_DIR
from mcr.mcr_sqlite import MCRSQLite

DB_CONVERSA = CACHE_DIR / 'mcr_conversa.db'
DB_CODIGO = CACHE_DIR / 'mcr_codigo.db'
RESULTADO_PATH = CACHE_DIR / 'treinamento_fase2.json'

# ─── SDM (simplificado embutido para nao depender de import) ───
class MiniSDM:
    """SDM simplificado para indexacao de topicos."""
    def __init__(self, dim=200, n_enderecos=500):
        self.dim = dim
        self.n_enderecos = n_enderecos
        self.enderecos = []
        self.conteudo = []
        self._hash_cache = {}

    def _hash_vec(self, texto: str) -> List[int]:
        if texto in self._hash_cache:
            return self._hash_cache[texto]
        import random
        rng = random.Random(hash(texto) & 0xFFFFFFFF)
        vec = [1 if rng.random() < 0.5 else -1 for _ in range(self.dim)]
        self._hash_cache[texto] = vec
        return vec

    def store(self, texto: str):
        if len(self.enderecos) < self.n_enderecos:
            import random as _r
            self.enderecos.append([1 if _r.random() < 0.5 else -1 for _ in range(self.dim)])
            self.conteudo.append([0] * self.dim)

        v = self._hash_vec(texto)
        for i, end in enumerate(self.enderecos):
            dot = sum(v[j] * end[j] for j in range(self.dim))
            if dot > self.dim * 0.25:
                for j in range(self.dim):
                    self.conteudo[i][j] += v[j]

    def retrieve(self, texto: str) -> Tuple[Optional[List[int]], float]:
        if not self.enderecos:
            return None, 0.0
        v = self._hash_vec(texto)
        soma = [0] * self.dim
        ativos = 0
        for i, end in enumerate(self.enderecos):
            dot = sum(v[j] * end[j] for j in range(self.dim))
            if dot > self.dim * 0.25:
                for j in range(self.dim):
                    soma[j] += self.conteudo[i][j]
                ativos += 1
        if ativos == 0:
            return None, 0.0
        recon = [1 if s > 0 else -1 for s in soma]
        concordancia = sum(1 for j in range(self.dim) if abs(soma[j]) > 0)
        fidelidade = concordancia / self.dim
        return recon, fidelidade


def _palavras(texto: str, min_len: int = 3) -> List[str]:
    return re.findall(rf'\b[a-zA-ZÀ-ÿ]+{{{min_len},}}\b', texto.lower())


# ═══════════════════════════════════════════════════════════
# TREINAMENTO: CONVERSA
# ═══════════════════════════════════════════════════════════

def treinar_conversa(db_path: str = None) -> Dict:
    """Treina MCRSQLite com os dialogos de NPC."""
    db_path = db_path or str(DB_CONVERSA)
    if os.path.exists(db_path):
        os.remove(db_path)

    mcr = MCRSQLite(db_path, n_max=5, identidade='conversa')
    stats = {'total_dialogos': 0, 'total_palavras': 0, 'total_npcs': 0, 'arquivos': []}
    sequencias_treinadas = 0

    # Fonte 1: npc_knowledge.json (132K linhas, mais completo)
    npc_knowledge = CACHE_DIR / 'npc_knowledge.json'
    if npc_knowledge.exists():
        print(f'  Carregando npc_knowledge.json...')
        with open(npc_knowledge, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        dialogos = dados.get('dialogos', {})
        npcs = dados.get('npcs', {})
        print(f'  NPCs: {dados.get("total_npcs", 0)}, '
              f'Dialogos: {dados.get("total_dialogos", 0)}')
        stats['total_npcs'] = dados.get('total_npcs', 0)
        stats['total_dialogos'] = dados.get('total_dialogos', 0)

        sequencias = []
        # Processa TODOS os dialogos (keyword -> [texto, npc_name, count])
        for keyword, respostas in dialogos.items():
            for resp in respostas:
                if isinstance(resp, list) and len(resp) >= 1:
                    texto = resp[0] if isinstance(resp[0], str) else str(resp[0])
                    palavras = _palavras(texto, min_len=2)
                    if len(palavras) >= 3:
                        sequencias.append(palavras)
                        stats['total_palavras'] += len(palavras)

        # Processa npcs (nome_npc -> {dialogos: [...]})
        for nome_npc, npc_data in npcs.items():
            npc_dialogos = npc_data.get('dialogos', []) if isinstance(npc_data, dict) else []
            for d in npc_dialogos:
                texto = ''
                if isinstance(d, str):
                    texto = d
                elif isinstance(d, dict):
                    texto = d.get('texto', '') or d.get('text', '') or d.get('response', '')
                elif isinstance(d, list) and len(d) >= 1:
                    texto = str(d[0])
                palavras = _palavras(texto, min_len=2)
                if len(palavras) >= 3:
                    sequencias.append(palavras)

        print(f'  Sequencias extraidas: {len(sequencias)}')
        if sequencias:
            batch_size = 1000
            for i in range(0, len(sequencias), batch_size):
                batch = sequencias[i:i + batch_size]
                mcr.aprender_batch(batch)
                sequencias_treinadas += len(batch)
            mcr.conn.commit()

        stats['arquivos'].append('npc_knowledge.json')

    # Fonte 2: dialogos_npc.json (20.8K linhas)
    dialogos_npc = KG_DIR / 'dialogos_npc.json'
    if dialogos_npc.exists():
        print(f'  Carregando dialogos_npc.json...')
        with open(dialogos_npc, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        npcs = dados if isinstance(dados, list) else dados.get('npcs', [])
        sequencias = []
        for npc in npcs:
            dialogos_npc_list = npc.get('dialogos', [])
            for d in dialogos_npc_list:
                texto = d.get('texto', '') or d.get('response', '') or str(d)
                palavras = _palavras(texto, min_len=2)
                if len(palavras) >= 3:
                    sequencias.append(palavras)

        print(f'  Sequencias extraidas: {len(sequencias)}')
        for i in range(0, len(sequencias), 5000):
            mcr.aprender_batch(sequencias[i:i + 5000])
            sequencias_treinadas += min(5000, len(sequencias) - i)
        stats['arquivos'].append('dialogos_npc.json')

    # Fonte 3: autobiography.json (self-knowledge)
    auto_path = KG_DIR / 'autobiography.json'
    if auto_path.exists():
        with open(auto_path, 'r', encoding='utf-8') as f:
            auto = json.load(f)
        memorias = auto.get('memorias', [])
        sequencias = []
        for m in memorias:
            texto = m.get('summary', '') + ' ' + m.get('detalhes', '')
            palavras = _palavras(texto, min_len=2)
            if len(palavras) >= 2:
                sequencias.append(palavras)
        if sequencias:
            mcr.aprender_batch(sequencias)
            sequencias_treinadas += len(sequencias)
            stats['arquivos'].append('autobiography.json')

    stats['sequencias_treinadas'] = sequencias_treinadas
    stats['estados_unicos'] = len(mcr.conn.execute(
        "SELECT COUNT(DISTINCT key) FROM trans").fetchone()[0])
    stats['transicoes_total'] = mcr.conn.execute(
        "SELECT COUNT(*) FROM trans").fetchone()[0]
    stats['entropia_media'] = round(mcr.entropia_media(), 4)
    stats['db_path'] = db_path

    mcr.conn.close()
    return stats


# ═══════════════════════════════════════════════════════════
# TREINAMENTO: CODIGO
# ═══════════════════════════════════════════════════════════

def treinar_codigo(db_path: str = None) -> Dict:
    """Treina MCRSQLite com codigo (Lua + SQL + Python)."""
    db_path = db_path or str(DB_CODIGO)
    if os.path.exists(db_path):
        os.remove(db_path)

    mcr = MCRSQLite(db_path, n_max=10, identidade='codigo')
    stats = {'arquivos_treinados': 0, 'total_linhas': 0, 'total_tokens': 0}

    # Fonte 1: Golden templates (Lua)
    for gf in GOLDEN_EXAMPLES_DIR.glob('*.lua'):
        with open(gf, 'r', encoding='utf-8') as f:
            codigo = f.read()
        tokens = tokenizar_codigo(codigo)
        if len(tokens) >= 3:
            mcr.aprender_sequencia(tokens)
            stats['total_linhas'] += codigo.count('\n')
            stats['total_tokens'] += len(tokens)
            stats['arquivos_treinados'] += 1

    # Fonte 2: SQL corpus (4 dominios)
    sql_corpus = Path(_BASE) / 'data' / 'generated' / 'sql_corpus'
    if sql_corpus.exists():
        for sql_file in sql_corpus.glob('*/*.sql'):
            with open(sql_file, 'r', encoding='utf-8') as f:
                codigo = f.read()
            tokens = tokenizar_codigo(codigo)
            if len(tokens) >= 3:
                mcr.aprender_sequencia(tokens)
                stats['total_linhas'] += codigo.count('\n')
                stats['total_tokens'] += len(tokens)
                stats['arquivos_treinados'] += 1

    # Fonte 3: Codigo Lua gerado pelo pipeline_universal
    pipeline_lua = Path(_BASE) / 'poc_output' / 'pipeline_universal'
    if pipeline_lua.exists():
        for lua_file in list(pipeline_lua.glob('*.lua'))[:20]:
            with open(lua_file, 'r', encoding='utf-8') as f:
                codigo = f.read()
            tokens = tokenizar_codigo(codigo)
            if len(tokens) >= 3:
                mcr.aprender_sequencia(tokens)
                stats['total_linhas'] += codigo.count('\n')
                stats['total_tokens'] += len(tokens)
                stats['arquivos_treinados'] += 1

    stats['estados_unicos'] = len(mcr.conn.execute(
        "SELECT COUNT(DISTINCT key) FROM trans").fetchone()[0])
    stats['transicoes_total'] = mcr.conn.execute(
        "SELECT COUNT(*) FROM trans").fetchone()[0]
    stats['entropia_media'] = round(mcr.entropia_media(), 4)
    stats['db_path'] = db_path

    mcr.conn.close()
    return stats


def tokenizar_codigo(codigo: str) -> List[str]:
    """Tokeniza codigo preservando palavras, simbolos e numeros."""
    return re.findall(r'[a-zA-Z_]\w*|\d+|[^\s\w]', codigo)


# ═══════════════════════════════════════════════════════════
# TREINAMENTO: SDM (Topicos)
# ═══════════════════════════════════════════════════════════

def treinar_sdm() -> Dict:
    """Popula SDM com topicos do cerebro.json e KG."""
    sdm = MiniSDM(dim=200, n_enderecos=500)
    stats = {'topicos_indexados': 0, 'palavras_indexadas': 0, 'fidelidade_media': 0.0}

    # Fonte 1: cerebro.json (6.227 topicos)
    cerebro_path = CACHE_DIR / 'cerebro.json'
    if cerebro_path.exists():
        print(f'  Indexando cerebro.json...')
        with open(cerebro_path, 'r', encoding='utf-8') as f:
            cerebro = json.load(f)
        topicos = cerebro.get('topicos', {})
        for nome, dados in topicos.items():
            texto = str(nome)
            if isinstance(dados, dict):
                texto += ' ' + dados.get('texto', '') + ' '
                texto += ' '.join(dados.get('palavras', [])[:10])
            palavras = _palavras(texto, min_len=2)
            for p in palavras:
                sdm.store(p)
                stats['palavras_indexadas'] += 1
            sdm.store(texto[:200])
            stats['topicos_indexados'] += 1
        print(f'  Topicos: {stats["topicos_indexados"]}, '
              f'Palavras: {stats["palavras_indexadas"]}')

    # Fonte 2: 52 arquivos KG do E:\Coisas
    kg_dir = Path(r'E:\Coisas\sandbox\.mcr_devia\kg')
    if kg_dir.exists():
        print(f'  Indexando arquivos KG...')
        kg_arquivos = list(kg_dir.glob('*.json'))
        for kgf in kg_arquivos[:20]:  # Limitar a 20 para performance
            try:
                with open(kgf, 'r', encoding='utf-8') as f:
                    kg_data = json.load(f)
                if isinstance(kg_data, dict):
                    for chave, valor in kg_data.items():
                        texto = str(chave) + ' ' + str(valor)[:500]
                        sdm.store(texto[:200])
                        stats['topicos_indexados'] += 1
                elif isinstance(kg_data, list):
                    for item in kg_data[:500]:
                        texto = str(item)[:200]
                        sdm.store(texto)
                        stats['topicos_indexados'] += 1
            except Exception:
                pass

    # Medir fidelidade
    fidelidades = []
    for _ in range(10):
        _, fid = sdm.retrieve('dragao')
        if fid > 0:
            fidelidades.append(fid)
    stats['fidelidade_media'] = round(
        sum(fidelidades) / len(fidelidades), 3) if fidelidades else 0.0

    return stats


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main(dry_run=False, apenas_conversa=False, apenas_codigo=False):
    print('=' * 60)
    print('  FASE 2 — Treinamento Completo do MCR')
    print('=' * 60)

    if dry_run:
        print('\n[DRY RUN] Apenas verificando fontes de dados...\n')
        fontes = [
            ('cache/npc_knowledge.json', CACHE_DIR / 'npc_knowledge.json'),
            ('devia/knowledge/dialogos_npc.json', KG_DIR / 'dialogos_npc.json'),
            ('cache/cerebro.json', CACHE_DIR / 'cerebro.json'),
            ('devia/knowledge/autobiography.json', KG_DIR / 'autobiography.json'),
            ('E:\\Coisas\\sandbox\\.mcr_devia\\kg\\', Path(r'E:\Coisas\sandbox\.mcr_devia\kg')),
            ('data/generated/sql_corpus/', Path(_BASE) / 'data' / 'generated' / 'sql_corpus'),
            ('golden_examples/', GOLDEN_EXAMPLES_DIR),
        ]
        for nome, path in fontes:
            existe = path.exists()
            size = ''
            if existe:
                if path.is_dir():
                    size = f'{len(list(path.glob("**/*")))} arquivos'
                else:
                    size = f'{path.stat().st_size / 1024:.0f}KB'
            print(f'  [{"OK" if existe else "X"}] {nome} {size}')
        return

    resultado = {}
    t0 = time.time()

    if not apenas_codigo:
        print('\n[1/3] Treinando conversa...')
        stats_conv = treinar_conversa()
        resultado['conversa'] = stats_conv
        print(f'  Estados: {stats_conv["estados_unicos"]}, '
              f'Transicoes: {stats_conv["transicoes_total"]}, '
              f'Entropia: {stats_conv["entropia_media"]}')

    if not apenas_conversa:
        print('\n[2/3] Treinando codigo...')
        stats_cod = treinar_codigo()
        resultado['codigo'] = stats_cod
        print(f'  Arquivos: {stats_cod["arquivos_treinados"]}, '
              f'Estados: {stats_cod["estados_unicos"]}, '
              f'Entropia: {stats_cod["entropia_media"]}')

    print('\n[3/3] Indexando SDM...')
    stats_sdm = treinar_sdm()
    resultado['sdm'] = stats_sdm
    print(f'  Topicos: {stats_sdm["topicos_indexados"]}, '
          f'Fidelidade: {stats_sdm["fidelidade_media"]}')

    resultado['tempo_total'] = round(time.time() - t0, 2)

    # Salvar resultado
    with open(RESULTADO_PATH, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f'\n[OK] Resultados salvos em {RESULTADO_PATH}')
    print(f'[OK] Tempo total: {resultado["tempo_total"]}s')
    return resultado


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--conversa', action='store_true')
    parser.add_argument('--codigo', action='store_true')
    args = parser.parse_args()

    main(dry_run=args.dry_run,
         apenas_conversa=args.conversa,
         apenas_codigo=args.codigo)
