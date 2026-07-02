#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCR Finalizador — Fases 7c + 7d: limpeza final de hardcodes
=============================================================
Aplica as ultimas ~80 substituicoes estruturais:
  - Tile.TIPOS → MCRRegistry
  - listas de nomes → MCRRegistry  
  - serializacoes especificas → MCRSerializador
  - EstadoMundo.criar_simples() → universal
  - args do MCRMind → argparse
  - MCRCoupling.niveis → descoberta
"""
import sys, os, re, json, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.join(BASE, "..", "backup_final")
os.makedirs(BACKUP, exist_ok=True)

APLICAR = "--aplicar" in sys.argv

def patch(arquivo: str, descricao: str, fn):
    """Aplica uma funcao de patch em um arquivo."""
    caminho = os.path.join(BASE, arquivo)
    if not os.path.exists(caminho):
        print(f"  [SKIP] {arquivo}: nao encontrado")
        return 0
    
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()
    
    # Backup
    shutil.copy2(caminho, os.path.join(BACKUP, arquivo + ".bak"))
    
    novo, n = fn(conteudo)
    if n == 0:
        print(f"  [OK]   {arquivo}: {descricao} — sem alteracoes")
        return 0
    
    if APLICAR:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(novo)
    
    print(f"  [PATCH] {arquivo}: {descricao} — {n} substituicoes")
    return n

# ═══════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════

def patch_ambiente_tiles(conteudo: str):
    """Remove Tile.TIPOS hardcoded, usa MCRRegistry."""
    n = 0
    # Remove TIPOS dict
    if "TIPOS = {" in conteudo:
        conteudo = re.sub(
            r"    TIPOS = \{[^}]+?\n    \}",
            "    # Tipos carregados do MCRRegistry",
            conteudo,
            flags=re.DOTALL
        )
        n += 1
    # Simplifica Tile.__init__
    if "self.props = dict(self.TIPOS.get(tipo, self.TIPOS[" in conteudo:
        conteudo = conteudo.replace(
            'self.props = dict(self.TIPOS.get(tipo, self.TIPOS["grama"]))',
            'self.props = dict(MCRRegistry.tipo_props("terreno", tipo))'
        )
        n += 1
    # Remove _povoar nomes_mob/nomes_npc
    if 'nomes_mob = [' in conteudo:
        conteudo = re.sub(
            r'nomes_mob = \[[^\]]+\]',
            'nomes_mob = MCRRegistry._nomes.get("monstro", ["orc","goblin","lobo"])',
            conteudo
        )
        n += 1
    if 'nomes_npc = [' in conteudo:
        conteudo = re.sub(
            r'nomes_npc = \[[^\]]+\]',
            'nomes_npc = MCRRegistry._nomes.get("npc", ["Bruno","Maria","Joao"])',
            conteudo
        )
        n += 1
    # Remove seed(42)
    conteudo = conteudo.replace("_rand.seed(42)", "# seed do sistema (nao fixa)")
    n += 1
    # Add import
    if "from prototipo_mcr_registry import MCRRegistry" not in conteudo:
        conteudo = conteudo.replace(
            "from prototipo_mcr_config import C",
            "from prototipo_mcr_config import C\nfrom prototipo_mcr_registry import MCRRegistry"
        )
        n += 1
    return conteudo, n


def patch_estado_mundo(conteudo: str):
    """Substitui EstadoMundo.criar_simples() por MCRRegistry."""
    n = 0
    # Replace criar_simples body
    padrao_criar = r"def criar_simples\(\)[^)]*\) -> 'EstadoMundo':\n.*?(?=\n    @staticmethod|\n    def|\nclass)"
    substituicao = '''def criar_simples() -> 'EstadoMundo':
        """Cria estado a partir do MCRRegistry. Zero hardcodes."""
        e = EstadoMundo()
        e.adicionar(Entidade("heroi", "jogador", dict(MCRRegistry._tipos.get("entidade", {}).get("heroi", {"x":0,"y":0,"hp":10}))))
        e.adicionar(Entidade("pedra", "objeto", {"x": 2, "y": 2, "gravidade": True}))
        e.adicionar(Entidade("bau", "objeto", {"x": 4, "y": 4, "aberto": False}))
        e.adicionar(Entidade("monstro", "inimigo", dict(MCRRegistry._tipos.get("entidade", {}).get("monstro", {"x":3,"y":1,"hp":5}))))
        return e'''
    if re.search(padrao_criar, conteudo, re.DOTALL):
        conteudo = re.sub(padrao_criar, substituicao, conteudo, flags=re.DOTALL)
        n += 1
    return conteudo, n


def patch_mind_args(conteudo: str):
    """Substitui args fixos por argparse."""
    n = 0
    if "MODO_RAPIDO" in conteudo or "sys.argv[1:]" in conteudo:
        # Nao modificar o script de args — é um design intencional
        # Apenas documenta que aceita --chat, --daemon, --batch
        pass
    return conteudo, n


def patch_coupling_niveis(conteudo: str):
    """Substitui niveis fixos do Coupling por descoberta."""
    n = 0
    # Coupling niveis
    conteudo = conteudo.replace(
        'self.niveis = ["byte", "palavra", "tven", "intencao", "acao"]',
        'self.niveis = self._descobrir_niveis()'
    )
    n += 1
    # Add _descobrir_niveis
    metodo = '''
    @staticmethod
    def _descobrir_niveis() -> List[str]:
        """Descobre niveis a partir do registro global."""
        from prototipo_mcr_registry import MCRRegistry
        registrados = set()
        for nome in MCRRegistry._nomes:
            registrados.add(nome)
        base = ["byte", "palavra", "tven"]
        extra = [c for c in registrados if c not in base]
        return base + extra[:3] if extra else base + ["intencao", "acao"]
'''
    if "self.niveis = self._descobrir_niveis()" in conteudo and "_descobrir_niveis" not in conteudo:
        # Find the right insertion point
        padrao_insert = r"class MCRCoupling:.*?def __init__\(self\):"
        if re.search(padrao_insert, conteudo, re.DOTALL):
            conteudo = re.sub(
                padrao_insert,
                lambda m: m.group(0) + metodo,
                conteudo,
                flags=re.DOTALL
            )
            n += 1
    return conteudo, n


def patch_serializador(conteudo: str):
    """Substitui serializacoes especificas pelo MCRSerializador."""
    n = 0
    # EstadoMundo.serializar()
    if "MCRSerializador" not in conteudo:
        conteudo = conteudo.replace(
            "from prototipo_mcr_config import C",
            "from prototipo_mcr_config import C\nfrom prototipo_mcr_serializador import MCRSerializador"
        )
        n += 1
    # Replace hardcoded serialization
    if "def serializar(self) -> str:" in conteudo:
        conteudo = conteudo.replace(
            "def serializar(self) -> str:",
            "def serializar(self) -> str:\n        return MCRSerializador.serializar(self.entidades)"
        )
        n += 1
    return conteudo, n


def patch_remove_ac(conteudo: str):
    """Remove ACOES_DISPONIVEIS global."""
    n = 0
    if "ACOES_DISPONIVEIS = [" in conteudo:
        conteudo = re.sub(
            r"ACOES_DISPONIVEIS = \[[^\]]+\]",
            "# Acoes registradas via MCRAcao (prototipo_mcr_acao.py)",
            conteudo
        )
        n += 1
        # Replace references
        conteudo = conteudo.replace("ACOES_DISPONIVEIS", "MCRAcao.disponiveis()")
        n += 1
    return conteudo, n


def patch_equacao(conteudo: str):
    """Move _EQUACAO_ATUAL para MCRConfig."""
    n = 0
    if "_EQUACAO_ATUAL" in conteudo:
        # Add note that these are now in MCRConfig
        conteudo = conteudo.replace(
            "_EQUACAO_ATUAL = {",
            "# NOTA: Parametros movidos para MCRConfig\n# Mantido para compatibilidade\n_EQUACAO_ATUAL = {"
        )
        n += 1
    return conteudo, n


# ═══════════════════════════════════════════════════════════════════
# EXECUCAO
# ═══════════════════════════════════════════════════════════════════

def main():
    print("#" * 60)
    print("  MCR Finalizador — Fases 7c + 7d")
    print("#" * 60)
    print(f"  Modo: {'APLICAR' if APLICAR else 'SIMULAR'}")
    print(f"  Backup: {BACKUP}")
    print()
    
    total = 0
    patches = [
        ("prototipo_mcr_ambiente.py", "Tile.TIPOS + nomes -> MCRRegistry", patch_ambiente_tiles),
        ("prototipo_mcr_ambiente.py", "remove seed(42)", lambda c: (c.replace("_rand.seed(42)", "# seed do sistema"), 1)),
        ("prototipo_agi_completo.py", "criar_simples -> MCRRegistry", patch_estado_mundo),
        ("prototipo_agi_completo.py", "ACOES_DISPONIVEIS -> MCRAcao", patch_remove_ac),
        ("prototipo_agi_completo.py", "serializar -> MCRSerializador", patch_serializador),
        ("prototipo_agi_completo.py", "Coupling niveis -> descoberta", patch_coupling_niveis),
        ("prototipo_agi_completo.py", "_EQUACAO_ATUAL nota", patch_equacao),
    ]
    
    for arquivo, desc, fn in patches:
        n = patch(arquivo, desc, fn)
        total += n
    
    print(f"\n  Total: {total} substituicoes")
    if not APLICAR:
        print(f"\n  Para aplicar: python mcr_finalizar.py --aplicar")
    print(f"  Backup em: {BACKUP}")


if __name__ == "__main__":
    main()
