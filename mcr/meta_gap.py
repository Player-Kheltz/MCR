"""mcr.meta_gap — Detector de Lacunas de Conhecimento.
Compara o que o sistema sabe (KG) contra o que deveria saber (codigo-fonte do Canary)."""
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

from mcr.paths import KG_DIR, CANARY_SRC_DIR, CANARY_DATA_DIR, CANARY_SCRIPTS_DIR
from mcr.encoding import read_file

# Temas conhecidos do Canary (por diretorio/padrao de nome)
_TEMAS_POR_DIRETORIO = {
    'pvp': 'combate entre jogadores',
    'guild': 'sistema de guildas',
    'house': 'sistema de casas',
    'quest': 'sistema de missoes',
    'raid': 'invasao de monstros em massa',
    'spell': 'magias e habilidades',
    'mount': 'sistema de montarias',
    'imbuement': 'sistema de imbuements',
    'forge': 'sistema de forja',
    'hireling': 'sistema de serventes',
    'bosstiary': 'sistema de bestiario de bosses',
    'charm': 'sistema de charms',
    'concoction': 'pocoes e concoctions',
    'achievement': 'sistema de conquistas',
    'tier': 'sistema de tiers de itens',
    'monster': 'monstros e criaturas',
    'npc': 'personagens nao jogaveis',
    'action': 'acoes de itens (baus, alavancas)',
    'creatureevent': 'eventos de criaturas',
    'globalevent': 'eventos globais do servidor',
    'movement': 'eventos de movimento',
    'talkaction': 'acoes de fala',
    'weapon': 'sistema de armas',
}

# Palavras-chave para detectar temas em nomes de arquivo
_TEMAS_PALAVRAS_CHAVE = [
    ('pvp', 'pvp'), ('guild', 'guild'), ('house', 'house'), ('quest', 'quest'),
    ('raid', 'raid'), ('spell', 'spell'), ('mount', 'mount'), ('imbuement', 'imbuement'),
    ('forge', 'forge'), ('hireling', 'hireling'), ('bosstiary', 'bosstiary'),
    ('charm', 'charm'), ('concoction', 'concoction'), ('achievement', 'achievement'),
    ('tier', 'tier'), ('rank', 'ranking'), ('arena', 'arena'),
    ('party', 'party'), ('bless', 'bless'), ('death', 'death'),
    ('hire', 'hire'), ('store', 'store'), ('premium', 'premium'),
    ('vip', 'vip'), ('invite', 'invite'), ('ban', 'banishment'),
    ('tile', 'tile'), ('teleport', 'teleport'), ('door', 'door'),
]


class MetaGap:
    """Detecta lacunas entre o conhecimento do KG e o codigo-fonte do Canary."""

    def __init__(self):
        self.conhecidos: Set[str] = set()
        self._carregar_conhecidos()

    def _carregar_conhecidos(self):
        """Carrega os temas que o KG ja conhece."""
        if not KG_DIR.exists():
            return

        for fpath in KG_DIR.glob('patterns_*.json'):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                for p in dados.get('padroes', dados if isinstance(dados, list) else []):
                    tipo = p.get('tipo', '')
                    if tipo:
                        self.conhecidos.add(tipo.lower())
                    for api in p.get('api_calls', []):
                        partes = re.split(r'[.:]', api.lower())
                        for parte in partes:
                            if len(parte) > 3:
                                for tema, _ in _TEMAS_PALAVRAS_CHAVE:
                                    if tema in parte:
                                        self.conhecidos.add(tema)
            except Exception:
                pass
        print(f'[MetaGap] Conhecidos: {len(self.conhecidos)} temas')

    def detectar_lacunas(self) -> List[Dict]:
        """Varre o codigo-fonte do Canary e detecta lacunas no KG.
        
        Returns:
            lista de dicts com 'tema', 'descricao', 'arquivos', 'motivo'
        """
        lacunas = []

        # 1. Varre diretorios do CANARY_SRC_DIR
        if CANARY_SRC_DIR.exists():
            for diretorio in sorted(CANARY_SRC_DIR.iterdir()):
                if not diretorio.is_dir() or diretorio.name.startswith('.'):
                    continue
                tema = diretorio.name.lower()
                if tema in _TEMAS_POR_DIRETORIO and tema not in self.conhecidos:
                    arquivos = list(diretorio.rglob('*.cpp')) + list(diretorio.rglob('*.h'))
                    if arquivos:
                        lacunas.append({
                            'tema': tema,
                            'descricao': _TEMAS_POR_DIRETORIO.get(tema, ''),
                            'arquivos': [str(a) for a in arquivos[:10]],
                            'motivo': f'Nenhum padrao de {tema} no KG',
                            'fonte': 'src/' + diretorio.name,
                        })

        # 2. Varre subdiretorios de scripts
        if CANARY_DATA_DIR.exists():
            scripts_dirs = [
                CANARY_DATA_DIR / 'scripts',
                CANARY_DATA_DIR / 'scripts' / 'actions',
                CANARY_DATA_DIR / 'scripts' / 'spells',
                CANARY_DATA_DIR / 'scripts' / 'creaturescripts',
                CANARY_DATA_DIR / 'scripts' / 'globalevents',
                CANARY_DATA_DIR / 'scripts' / 'movements',
                CANARY_DATA_DIR / 'scripts' / 'talkactions',
                CANARY_DATA_DIR / 'scripts' / 'weapons',
            ]
            for sd in scripts_dirs:
                if sd.exists():
                    for f in sd.iterdir():
                        if f.suffix in ('.lua', '.py'):
                            for tema, desc in _TEMAS_POR_DIRETORIO.items():
                                if tema in f.stem.lower() and tema not in self.conhecidos:
                                    # Evita duplicatas
                                    if not any(l['tema'] == tema for l in lacunas):
                                        lacunas.append({
                                            'tema': tema,
                                            'descricao': desc,
                                            'arquivos': [str(f)],
                                            'motivo': f'Nenhum padrao de {tema} no KG',
                                            'fonte': 'scripts/' + sd.name + '/' + f.name,
                                        })

        # 3. Varre por palavras-chave em nomes de arquivo
        for tema, palavra in _TEMAS_PALAVRAS_CHAVE:
            if tema in self.conhecidos:
                continue
            if any(l['tema'] == tema for l in lacunas):
                continue
            # Procura em src/ recursivo
            if CANARY_SRC_DIR.exists():
                matches = list(CANARY_SRC_DIR.rglob(f'*{palavra}*.*'))
                if matches:
                    lacunas.append({
                        'tema': tema,
                        'descricao': f'Sistema de {tema}',
                        'arquivos': [str(m) for m in matches[:5]],
                        'motivo': 'Nenhum padrao de %s no KG' % tema,
                        'fonte': 'src/ (keyword match)',
                    })

        # Remove duplicatas e ordena
        vistos = set()
        unicos = []
        for l in lacunas:
            chave = l['tema']
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(l)

        print(f'[MetaGap] Lacunas detectadas: {len(unicos)}')
        for l in unicos[:10]:
            print(f'  - {l["tema"]}: {len(l["arquivos"])} arquivo(s) ({l["fonte"]})')
        if len(unicos) > 10:
            print(f'  ... e mais {len(unicos)-10} lacunas')

        return unicos

    @staticmethod
    def sugerir_estudo(lacuna: Dict) -> str:
        """Retorna uma instrucao de estudo para uma lacuna."""
        if not lacuna['arquivos']:
            return f'Nenhum arquivo encontrado para estudar sobre {lacuna["tema"]}.'
        primeiro = lacuna['arquivos'][0]
        return (
            f"Lacuna detectada: {lacuna['tema']} ({lacuna['descricao']})\n"
            f"Motivo: {lacuna['motivo']}\n"
            f"Instrucao: Vá para {primeiro} e leia o codigo-fonte.\n"
            f"Extraia a estrutura AST, identifique as APIs utilizadas,\n"
            f"e registre os padroes no Knowledge Graph."
        )

    def estatisticas(self) -> Dict:
        return {
            'conhecidos': len(self.conhecidos),
            'conhecidos_lista': sorted(self.conhecidos),
        }
