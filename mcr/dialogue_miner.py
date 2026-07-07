"""mcr.dialogue_miner — Extrai falas de NPCs do Canary a partir de arquivos .lua.
Usa regex para capturar textos em chamadas StdModule.say e keywordHandler:addKeyword."""
import re
import json
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

from mcr.encoding import read_file
from mcr.paths import CANARY_NPC_DIR

# Padroes para extrair dialogos
_PADRAO_NOME = re.compile(r'local\s+internalNpcName\s*=\s*"([^"]+)"')
_PADRAO_FALA = re.compile(
    r'text\s*=\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
    re.IGNORECASE
)
_PADRAO_KEYWORD = re.compile(
    r'keywordHandler:addKeyword\s*\(\s*\{([^}]+)\}',
    re.IGNORECASE
)
_PADRAO_KEYWORD_LIST = re.compile(r'"([^"]+)"')

# Palavras de cortesia/filler que queremos filtrar
_STOP_KEYWORDS = {'yes', 'no', 'hello', 'bye', 'hi', 'goodbye', 'ok', 'thanks',
                  'thank', 'help', 'info', 'information', 'quest', 'trade',
                  'job', 'name', 'time', 'offer', 'who', 'what', 'where',
                  'when', 'why', 'how', 'see', 'go', 'come', 'stop', 'wait',
                  'follow', 'leave', 'stay', 'move', 'open', 'close', 'use'}


def minerar_npc(caminho: Path) -> Dict:
    """Extrai dialogos de um arquivo NPC .lua.
    
    Returns:
        dict com 'npc_name', 'arquivo', 'dialogos'
        ou None se nao conseguir extrair.
    """
    try:
        codigo = read_file(caminho)
    except Exception:
        return None

    if not codigo or len(codigo) < 50:
        return None

    # Nome
    m_nome = _PADRAO_NOME.search(codigo)
    npc_name = m_nome.group(1) if m_nome else caminho.stem

    # Dialogos
    dialogos = []
    falas = _PADRAO_FALA.findall(codigo)

    for texto in falas:
        if texto and len(texto) > 5:
            # Tenta encontrar a keyword associada (busca antes do text=)
            pos = codigo.find('text = "%s"' % texto)
            if pos < 0:
                pos = codigo.find('text = "%s"' % texto.replace('"', '\\"'))
            keyword = ''
            if pos > 0:
                trecho_anterior = codigo[max(0, pos - 300):pos]
                kw_match = _PADRAO_KEYWORD.search(trecho_anterior)
                if kw_match:
                    keywords_list = _PADRAO_KEYWORD_LIST.findall(kw_match.group(1))
                    if keywords_list:
                        keyword = keywords_list[0].lower()

            dialogos.append({
                'keyword': keyword,
                'response': texto,
            })

    if not dialogos:
        return None

    return {
        'npc_name': npc_name,
        'arquivo': str(caminho),
        'dialogos': dialogos,
    }


def minerar_lote(diretorio: Path = None) -> List[Dict]:
    """Minera dialogos de todos os NPCs em um diretorio."""
    diretorio = diretorio or CANARY_NPC_DIR
    if not diretorio.exists():
        print('[DialogueMiner] Diretorio nao encontrado: %s' % diretorio)
        return []

    npcs = []
    arquivos = list(diretorio.glob('*.lua'))
    print('[DialogueMiner] Varrendo %d arquivos NPC...' % len(arquivos))

    for fpath in arquivos:
        npc = minerar_npc(fpath)
        if npc and npc.get('dialogos'):
            npcs.append(npc)

    total_dialogos = sum(len(n.get('dialogos', [])) for n in npcs)
    print('[DialogueMiner] Extraidos: %d NPCs, %d dialogos' % (len(npcs), total_dialogos))
    return npcs


def salvar_dialogos(npcs: List[Dict], output_path: Path = None) -> Path:
    """Salva dialogos extraidos em JSON."""
    if output_path is None:
        from mcr.paths import KG_DIR
        KG_DIR.mkdir(parents=True, exist_ok=True)
        output_path = KG_DIR / 'dialogos_npc.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'npcs': npcs, 'total': len(npcs)}, f, ensure_ascii=False, indent=2)

    print('[DialogueMiner] Salvo em: %s (%d KB)' % (output_path, output_path.stat().st_size / 1024))
    return output_path


if __name__ == '__main__':
    npcs = minerar_lote()
    if npcs:
        salvar_dialogos(npcs)
    print('[DialogueMiner] Concluido')
