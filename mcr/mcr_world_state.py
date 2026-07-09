"""mcr.mcr_world_state — Estado do Mundo (World State).
Registra tudo que o MCR ja criou: NPCs, monstros, lores, etc.
Serve como memoria persistente para o MCR expandir o mundo sem
reescrever do zero."""
import json
from typing import Dict, List, Optional
from mcr.paths import DEVIA_DIR

WORLD_STATE_FILE = DEVIA_DIR / "world_state.json"


def _carregar() -> dict:
    if WORLD_STATE_FILE.exists():
        try:
            with open(WORLD_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"npcs": {}, "monstros": {}, "lores": {}}


def _salvar(estado: dict):
    WORLD_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WORLD_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)


def registrar_entidade(tipo: str, nome: str, dados: dict):
    """Registra uma entidade no Estado do Mundo.
    tipo: 'npc', 'monster', ou 'lore'
    dados: dict com informacoes da entidade (file, role, quests, etc.)
    """
    estado = _carregar()
    if tipo == 'npc':
        chave = 'npcs'
    elif tipo == 'monster':
        chave = 'monstros'
    else:
        chave = 'lores'
    if chave not in estado:
        estado[chave] = {}
    if nome in estado[chave]:
        estado[chave][nome].update(dados)
    else:
        estado[chave][nome] = dados
    _salvar(estado)
    print('[WorldState] Registrado: %s/%s' % (chave, nome))


def obter_entidade(tipo: str, nome: str) -> Optional[dict]:
    """Retorna dados de uma entidade registrada."""
    estado = _carregar()
    if tipo == 'npc':
        chave = 'npcs'
    elif tipo == 'monster':
        chave = 'monstros'
    else:
        chave = 'lores'
    return estado.get(chave, {}).get(nome)


def listar_entidades(tipo: str = '') -> list:
    """Lista entidades registradas. Se tipo vazio, lista todas."""
    estado = _carregar()
    if tipo:
        if tipo == 'npc':
            chave = 'npcs'
        elif tipo == 'monster':
            chave = 'monstros'
        else:
            chave = 'lores'
        return list(estado.get(chave, {}).keys())
    resultado = {}
    for chave in ('npcs', 'monstros', 'lores'):
        resultado[chave] = list(estado.get(chave, {}).keys())
    return resultado


def salvar_foundation(seed: dict):
    """Salva o WorldSeed atual no estado do mundo (chave current_foundation)."""
    estado = _carregar()
    estado['current_foundation'] = seed
    _salvar(estado)
    print('[WorldState] Fundacao salva: %s' % seed.get('world_name', 'sem nome'))


def carregar_foundation() -> dict:
    """Retorna o WorldSeed atual ou dict vazio."""
    estado = _carregar()
    return estado.get('current_foundation', {})
