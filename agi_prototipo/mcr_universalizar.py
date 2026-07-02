#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCR Universalizador — Substitui TODOS os hardcodes por MCRConfig
=================================================================
Escaneia cada arquivo, encontra padroes de numeros magicos,
if/elif chains, listas fixas, e substitui por chamadas ao MCRConfig.

Uso:
    python mcr_universalizar.py              # mostra o que vai mudar
    python mcr_universalizar.py --aplicar    # aplica as mudancas
    python mcr_universalizar.py --reverter   # reverte do backup
"""
import sys, os, re, shutil, json
from typing import Dict, List, Tuple

BASE = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(BASE, "..", "backup_universal")
os.makedirs(BACKUP_DIR, exist_ok=True)

MODO_APLICAR = "--aplicar" in sys.argv
MODO_REVERTER = "--reverter" in sys.argv
MODO_VERBOSE = "--verbose" in sys.argv


def log(msg):
    if MODO_VERBOSE or not MODO_APLICAR:
        print(msg)


# ═══════════════════════════════════════════════════════════════════
# REGRAS DE SUBSTITUICAO
# ═══════════════════════════════════════════════════════════════════

class Regra:
    """Uma regra de substituicao: encontra um padrao e substitui."""
    def __init__(self, arquivo: str, padrao: str, substituicao: str,
                 descricao: str = ""):
        self.arquivo = arquivo
        self.padrao = padrao  # regex ou string
        self.substituicao = substituicao
        self.descricao = descricao
        self.is_regex = not padrao.startswith("EXATO:")

    def aplicar(self, conteudo: str) -> Tuple[str, int]:
        if self.is_regex:
            novo, n = re.subn(self.padrao, self.substituicao, conteudo)
        else:
            exato = self.padrao.replace("EXATO:", "", 1)
            n = conteudo.count(exato)
            novo = conteudo.replace(exato, self.substituicao)
        return novo, n


def fingerprint_dim_8(arquivo: str) -> List[Regra]:
    """Substitui fingerprint(..., 8) e dim_fp = 8 por C('dim_fingerprint')"""
    return [
        Regra(arquivo, r'fingerprint\(([^)]*?),\s*8\s*\)',
              r'fingerprint(\1, C("dim_fingerprint"))',
              "fingerprint dim 8 -> C('dim_fingerprint')"),
        Regra(arquivo, r'delta_fingerprint\(([^)]*?),\s*8\s*\)',
              r'delta_fingerprint(\1, C("dim_fingerprint"))',
              "delta_fingerprint dim 8"),
        Regra(arquivo, r'self\.dim_fp\s*=\s*8',
              'self.dim_fp = C("dim_fingerprint")',
              "self.dim_fp = 8"),
        Regra(arquivo, r'fingerprint\(8\)',
              'fingerprint(C("dim_fingerprint"))',
              "fingerprint(8) curto"),
    ]


def thresholds(arquivo: str) -> List[Regra]:
    """Substitui thresholds fixos por C()"""
    return [
        Regra(arquivo, r'conf\s*>\s*0\.01', 'conf > C("conf_min")', "conf>0.01"),
        Regra(arquivo, r'conf\s*>\s*0\.15', 'conf > C("conf_min")', "conf>0.15"),
        Regra(arquivo, r'conf\s*>\s*0\.1\b(?!\d)', 'conf > C("conf_min")', "conf>0.1"),
        Regra(arquivo, r'conf\s*>\s*0\.2(?!\d)', 'conf > C("conf_media")', "conf>0.2"),
        Regra(arquivo, r'conf\s*>\s*0\.3(?!\d)', 'conf > C("conf_media")', "conf>0.3"),
        Regra(arquivo, r'score\s*>\s*0\.5\b(?!\d)', 'score > C("conf_alta")', "score>0.5"),
        Regra(arquivo, r'(?<!["\'])0\.5(?!["\'])(?![.\d])(?<!\.)(?<!\d)',
              'C("conf_alta")', "0.5 generico"),
    ]


def passos_iter(arquivo: str) -> List[Regra]:
    """Substitui passos/iteracoes fixos"""
    return [
        Regra(arquivo, r'(?<![.\w])passos\s*=\s*10(?!\d)',
              'passos = C("passos_planejar")', "passos=10"),
        Regra(arquivo, r'(?<![.\w])passos\s*=\s*6(?!\d)',
              'passos = C("passos_gerar")', "passos=6"),
        Regra(arquivo, r'(?<![.\w])passos\s*=\s*8(?!\d)',
              'passos = C("passos_gerar")', "passos=8"),
        Regra(arquivo, r'(?<![.\w])passos\s*=\s*4(?!\d)',
              'passos = max(2, C("passos_gerar") // 2)', "passos=4"),
        Regra(arquivo, r'max_iter\s*=\s*10\b(?!\d)',
              'max_iter = C("max_iter")', "max_iter=10"),
        Regra(arquivo, r'max_iter\s*=\s*3\b(?!\d)',
              'max_iter = C("max_iter") // 3', "max_iter=3"),
        Regra(arquivo, r'max_iter\s*=\s*5\b(?!\d)',
              'max_iter = C("max_iter") // 2', "max_iter=5"),
        Regra(arquivo, r'max_iter\s*=\s*8\b(?!\d)',
              'max_iter = C("max_iter")', "max_iter=8"),
        Regra(arquivo, r'max_passos\s*=\s*20\b(?!\d)',
              'max_passos = C("passos_planejar") * 2', "max_passos=20"),
        Regra(arquivo, r'max_passos\s*=\s*30\b(?!\d)',
              'max_passos = C("passos_planejar") * 3', "max_passos=30"),
        Regra(arquivo, r'max_passos\s*=\s*15\b(?!\d)',
              'max_passos = C("passos_planejar") + 5', "max_passos=15"),
        Regra(arquivo, r'range\(3\)', 'range(C("max_ciclos") // 3)', "range(3)"),
        Regra(arquivo, r'range\(5\)(?!\d)', 'range(C("top_k") + 2)', "range(5)"),
    ]


def limites_busca(arquivo: str) -> List[Regra]:
    """Substitui limites de busca e slices"""
    return [
        Regra(arquivo, r'limite\s*=\s*10', 'limite = C("limite_busca")', "limite=10"),
        Regra(arquivo, r'limite\s*=\s*5\b(?!\d)',
              'limite = C("top_k") + 2', "limite=5"),
        Regra(arquivo, r'\b5\b(?=[^;]*limite)', 'C("limite_busca") // 2', "limite 5"),
        Regra(arquivo, r'\[:5\]', '[:C("top_k") + 2]', "[:5]"),
        Regra(arquivo, r'\[:3\]', '[:C("top_k")]', "[:3]"),
        Regra(arquivo, r'\[:10\]', '[:C("limite_busca")]', "[:10]"),
        Regra(arquivo, r'\[:50\]', '[:C("historico_max") // 2]', "[:50]"),
        Regra(arquivo, r'\[:100\]', '[:C("historico_max")]', "[:100]"),
        Regra(arquivo, r'\[-50:\]', '[-C("historico_max") // 2:]', "[-50:]"),
        Regra(arquivo, r'\[-10:\]', '[-C("janela_entropia"):]', "[-10:]"),
        Regra(arquivo, r'\[-5:\]', '[-C("janela_recente"):]', "[-5:]"),
        Regra(arquivo, r'\blimite\s*=\s*1000\b', 'limite = C("memoria_restore_causais")', "limite=1000"),
        Regra(arquivo, r'\blimite\s*=\s*100\b(?!\d)', 'limite = C("memoria_restore_planos")', "limite=100"),
    ]


def rl_hyperparams(arquivo: str) -> List[Regra]:
    """Substitui hiperparametros do RL"""
    return [
        Regra(arquivo, r'gamma:\s*float\s*=\s*0\.9',
              'gamma: float = C("rl_gamma")', "gamma=0.9"),
        Regra(arquivo, r'alpha:\s*float\s*=\s*0\.3',
              'alpha: float = C("rl_alpha")', "alpha=0.3"),
        Regra(arquivo, r'epsilon:\s*float\s*=\s*0\.2',
              'epsilon: float = C("rl_epsilon_inicial")', "epsilon=0.2"),
        Regra(arquivo, r'max\(0\.05,\s*0\.2',
              'max(C("rl_epsilon_min"), C("rl_epsilon_inicial")', "epsilon decay"),
        Regra(arquivo, r'0\.01\)', 'C("rl_epsilon_decay"))', "epsilon decay rate"),
        Regra(arquivo, r'r\s*\+=\s*2\.0(?!\d)', 'r += C("rl_recompensa_sucesso")', "reward=2.0"),
        Regra(arquivo, r'r\s*\+=\s*0\.5(?!\d)', 'r += C("rl_recompensa_novidade")', "reward=0.5"),
        Regra(arquivo, r'r\s*\+=\s*1\.0(?!\d)', 'r += C("rl_recompensa_mudanca")', "reward=1.0"),
        Regra(arquivo, r'sim_obj\s*>\s*0\.95(?!\d)', 'sim_obj > C("conf_maxima")', "sim>0.95"),
    ]


def genesis_gaps(arquivo: str) -> List[Regra]:
    """Substitui thresholds de deteccao de gaps"""
    return [
        Regra(arquivo, r'mk_palavra\.total\s*<\s*10\b',
              'mk_palavra.total < C("genesis_min_palavras")', "gap palavras<10"),
        Regra(arquivo, r'mk_plano\.total\s*<\s*5\b',
              'mk_plano.total < C("genesis_min_planos")', "gap planos<5"),
        Regra(arquivo, r'h\s*>\s*0\.5\b(?!\d)',
              'h > C("gap_entropia_alta")', "gap h>0.5"),
        Regra(arquivo, r'peso\(o,\s*d\)\s*<\s*0\.1\b',
              'peso(o, d) < C("gap_coupling_fraco")', "gap coupling<0.1"),
        Regra(arquivo, r'acoplamentos_fracos\s*>\s*10\b',
              'acoplamentos_fracos > C("gap_coupling_count")', "gap acoplamentos>10"),
        Regra(arquivo, r'len\(hc\)\s*>\s*3\b',
              'len(hc) > C("gap_hardcode_count")', "gap hardcodes>3"),
        Regra(arquivo, r'nota_teste\s*>=\s*5\.0\b',
              'nota_teste >= C("genesis_nota_integracao")', "nota_teste>=5"),
    ]


def ambiente(arquivo: str) -> List[Regra]:
    """Substitui parametros do ambiente"""
    return [
        Regra(arquivo, r'% 100\b', '% C("ambiente_ticks_por_dia")', "tick%100"),
        Regra(arquivo, r'min\(50,', 'min(C("ambiente_entidades_por_tick"),', "min 50"),
        Regra(arquivo, r'range\(500\)', 'range(C("limite_busca") * 50)', "range(500)"),
        Regra(arquivo, r'raio\s*=\s*10\b', 'raio = C("top_k") + 7', "raio=10"),
    ]


def bridge(arquivo: str) -> List[Regra]:
    """Substitui thresholds da bridge"""
    return [
        Regra(arquivo, r'sim\s*>\s*0\.7\b(?!\d)',
              'sim > C("bridge_sim_transferencia")', "sim>0.7"),
        Regra(arquivo, r'nota_analogia\s*>\s*0\.5\b',
              'nota_analogia > C("bridge_nota_analogia")', "nota_analogia>0.5"),
        Regra(arquivo, r'self\.dim\s*=\s*8\b',
              'self.dim = C("dim_fingerprint")', "bridge dim=8"),
    ]


def todos(arquivo: str) -> List[Regra]:
    """Todas as regras para um arquivo."""
    regras = []
    for gerador in [fingerprint_dim_8, thresholds, passos_iter, limites_busca,
                    rl_hyperparams, genesis_gaps, ambiente, bridge]:
        regras.extend(gerador(arquivo))
    return regras


# ═══════════════════════════════════════════════════════════════════
# IMPORT ADICIONAL
# ═══════════════════════════════════════════════════════════════════

IMPORT_LINHA = 'from prototipo_mcr_config import C\n'

ARQUIVOS_ALVO = [
    "prototipo_agi_completo.py",
    "prototipo_mcr_hq.py",
    "prototipo_mcr_codex.py",
    "prototipo_mcr_rl.py",
    "prototipo_mcr_ambiente.py",
    "prototipo_mcr_bridge.py",
    "prototipo_mcr_genesis.py",
    "prototipo_mcr_mind.py",
]


def adicionar_import(conteudo: str) -> Tuple[str, bool]:
    """Adiciona import do MCRConfig se nao existir, respeitando imports multilinha."""
    if "from prototipo_mcr_config import" in conteudo:
        return conteudo, False

    linhas = conteudo.split("\n")
    dentro_import = False
    ultimo_import_idx = -1

    for i, linha in enumerate(linhas):
        if linha.startswith("import ") or linha.startswith("from "):
            ultimo_import_idx = i
            if "(" in linha and ")" not in linha:
                dentro_import = True
            else:
                dentro_import = False
        elif dentro_import:
            if ")" in linha:
                ultimo_import_idx = i
                dentro_import = False
            else:
                ultimo_import_idx = i

    if ultimo_import_idx >= 0:
        linhas.insert(ultimo_import_idx + 1, IMPORT_LINHA.strip())
    else:
        linhas.insert(0, IMPORT_LINHA.strip())

    return "\n".join(linhas), True


# ═══════════════════════════════════════════════════════════════════
# PROCESSADOR
# ═══════════════════════════════════════════════════════════════════

def processar_arquivo(nome: str) -> Dict:
    caminho = os.path.join(BASE, nome)
    if not os.path.exists(caminho):
        return {"arquivo": nome, "status": "nao encontrado", "substituicoes": 0}

    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Backup
    backup_path = os.path.join(BACKUP_DIR, nome + ".bak")
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(conteudo)

    # Adiciona import
    conteudo, import_adicionado = adicionar_import(conteudo)

    # Aplica regras
    regras = todos(nome)
    total_substituicoes = 0
    substituicoes = []

    for regra in regras:
        novo, n = regra.aplicar(conteudo)
        if n > 0:
            conteudo = novo
            total_substituicoes += n
            substituicoes.append({
                "descricao": regra.descricao,
                "n": n,
            })
            log(f"    {regra.descricao}: {n}x")

    if total_substituicoes == 0 and not import_adicionado:
        return {"arquivo": nome, "status": "sem alteracoes", "substituicoes": 0}

    # Salva se modo aplicar
    if MODO_APLICAR:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        status = f"modificado ({total_substituicoes} subts)"
    else:
        status = f"simulado ({total_substituicoes} substituicoes)"

    return {
        "arquivo": nome,
        "status": status,
        "substituicoes": total_substituicoes,
        "import_adicionado": import_adicionado,
        "detalhes": substituicoes[:10],
    }


def reverter():
    """Restaura todos os arquivos do backup."""
    for nome in ARQUIVOS_ALVO:
        backup_path = os.path.join(BACKUP_DIR, nome + ".bak")
        caminho = os.path.join(BASE, nome)
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, caminho)
            log(f"  Revertido: {nome}")
    log("\nTodos os arquivos restaurados do backup.")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("#" * 60)
    print("  MCR Universalizador")
    print("#" * 60)

    if MODO_REVERTER:
        print("\nRevertendo backups...")
        reverter()
        return

    print(f"\nModo: {'APLICAR' if MODO_APLICAR else 'SIMULAR'}")
    print(f"Arquivos: {len(ARQUIVOS_ALVO)}")
    print(f"Regras por arquivo: ~{len(todos('x'))}")
    print()

    total_subst = 0
    resultados = []

    for nome in ARQUIVOS_ALVO:
        log(f"\n[{nome}]")
        r = processar_arquivo(nome)
        resultados.append(r)
        total_subst += r["substituicoes"]

    print(f"\n{'=' * 60}")
    print(f"  RESUMO")
    print(f"{'=' * 60}")
    for r in resultados:
        print(f"  {r['arquivo']:35s}: {r['status']}")
    print(f"\n  Total de substituicoes: {total_subst}")
    print(f"  Backup em: {BACKUP_DIR}")

    if not MODO_APLICAR:
        print(f"\n  Para aplicar: python mcr_universalizar.py --aplicar")
        print(f"  Para reverter: python mcr_universalizar.py --reverter")

    # Salva relatorio
    rel = {
        "timestamp": __import__("time").time(),
        "modo": "aplicar" if MODO_APLICAR else "simular",
        "total_substituicoes": total_subst,
        "resultados": resultados,
    }
    rel_path = os.path.join(BASE, "..", "cache", "universalizar_report.json")
    os.makedirs(os.path.dirname(rel_path), exist_ok=True)
    with open(rel_path, "w", encoding="utf-8") as f:
        json.dump(rel, f, indent=2)
    print(f"\n  Relatorio: {rel_path}")


if __name__ == "__main__":
    main()
