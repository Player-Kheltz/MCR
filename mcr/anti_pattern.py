"""mcr.anti_pattern — Catalogador de Falhas.
Classifica erros do LogWatcher e registra Anti-Patterns no Knowledge Graph."""
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from mcr.paths import KG_DIR

# Padroes de erro do Canary para classificacao
_PADROES_ERRO = [
    # api_inexistente: chamou funcao que nao existe no objeto
    (r"attempt to call method '(\w+)' \(a nil value\)", 'api_inexistente',
     lambda m: m.group(1)),
    (r"attempt to call a nil value \(method '(\w+)'\)", 'api_inexistente',
     lambda m: m.group(1)),
    (r"attempt to call a nil value \(field '(\w+)'\)", 'api_inexistente',
     lambda m: m.group(1)),
    # tipo_errado: chamou API no objeto errado
    (r"attempt to index a nil value \(global '(\w+)'\)", 'tipo_errado',
     lambda m: m.group(1)),
    (r"bad argument #\d+ to '(\w+)'", 'tipo_errado',
     lambda m: m.group(1)),
    # stack overflow / memory
    (r"stack overflow", 'runtime', lambda m: 'stack'),
    (r"out of memory", 'runtime', lambda m: 'memory'),
    # syntax error (runtime detection)
    (r"'(.*?)' expected near '(.*?)'", 'sintaxe_valida_runtime_erro',
     lambda m: '%s expected near %s' % (m.group(1), m.group(2))),
    (r"unexpected symbol near '(.*?)'", 'sintaxe_valida_runtime_erro',
     lambda m: m.group(1)),
    # lua error generico
    (r"Lua Script Error.*?(?:\n|$)", 'desconhecido', lambda m: 'lua_script_error'),
    # monsters
    (r"Monsters::getMonsterType.*?Monster with name (\w+)", 'desconhecido',
     lambda m: 'monster:%s' % m.group(1)),
]

# Solucoes sugeridas para APIs problematicas conhecidas
_SUGESTOES = {
    'getMana': 'Use getMana() na classe Player, nao no Item. Player tem getMana(), Item nao.',
    'addItem': 'Use player:addItem(itemId, count) em um objeto Player, nao em Monster ou NPC.',
    'getStorageValue': 'Use player:getStorageValue(id) — retorna o valor ou -1 se nao definido.',
    'setStorageValue': 'Use player:setStorageValue(id, value) — aceita inteiros.',
    'getPosition': 'Use player:getPosition() ou item:getPosition() — ambos tem este metodo.',
    'sendTextMessage': 'Use player:sendTextMessage(MESSAGE_TYPE, "texto"). Mensagens vao para o Player.',
    'getHealth': 'Use creature:getHealth() — disponivel em Player e Monster, nao em Item.',
    'register': 'Use npcType:register(npcConfig) ou action:register(). Nao use .register = funcao.',
    'uid': 'Use action:uid(numero) — metodo com dois-pontos, nao assign action.uid = numero.',
}


def classificar_erro(linha_erro: str, arquivo_origem: str = '') -> Dict:
    """Classifica uma linha de erro do log do Canary.
    
    Returns:
        dict com 'categoria', 'api_problematica', 'arquivo', 'mensagem_original', 'solucao_sugerida'
    """
    resultado = {
        'categoria': 'desconhecido',
        'api_problematica': '',
        'arquivo': arquivo_origem,
        'mensagem_original': linha_erro.strip(),
        'solucao_sugerida': '',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    for padrao, categoria, extrator in _PADROES_ERRO:
        m = re.search(padrao, linha_erro, re.IGNORECASE)
        if m:
            resultado['categoria'] = categoria
            api_problematica = extrator(m)
            resultado['api_problematica'] = api_problematica
            # Busca sugestao
            for chave, sugestao in _SUGESTOES.items():
                if chave.lower() in api_problematica.lower():
                    resultado['solucao_sugerida'] = sugestao
                    break
            if not resultado['solucao_sugerida']:
                resultado['solucao_sugerida'] = (
                    f'Revise o uso de {api_problematica}. '
                    f'Verifique se a funcao existe no objeto correto.'
                )
            break

    return resultado


def registrar_anti_pattern(erro: Dict, kg_dir: Optional[Path] = None) -> bool:
    """Registra um erro classificado como Anti-Pattern no KG.
    
    Se o mesmo anti-pattern ja existe (mesma API + mesma categoria),
    apenas incrementa o contador 'ocorrencias'.
    
    Returns:
        True se registrado/atualizado com sucesso.
    """
    kg_dir = kg_dir or KG_DIR
    if not kg_dir.exists():
        kg_dir.mkdir(parents=True, exist_ok=True)

    # Carrega KG
    kg_path = _get_kg_path(kg_dir)
    dados = _carregar_kg(kg_path)

    if 'anti_patterns' not in dados:
        dados['anti_patterns'] = []

    # Verifica se ja existe
    chave_busca = (erro.get('api_problematica', '').lower(),
                   erro.get('categoria', ''))
    encontrado = False
    for ap in dados['anti_patterns']:
        if (ap.get('api_problematica', '').lower() == chave_busca[0] and
                ap.get('categoria', '') == chave_busca[1]):
            ap['ocorrencias'] = ap.get('ocorrencias', 1) + 1
            ap['ultimo_timestamp'] = erro.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))
            ap['ultimo_arquivo'] = erro.get('arquivo', '')
            encontrado = True
            break

    if not encontrado:
        erro['ocorrencias'] = 1
        dados['anti_patterns'].append(erro)

    # Salva
    with open(kg_path, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    if encontrado:
        print(f'[AntiPattern] Incrementado: {chave_busca[0]} ({chave_busca[1]}) '
              f'-> {_buscar_ocorrencias(dados["anti_patterns"], chave_busca)}x')
    else:
        print(f'[AntiPattern] Novo: {chave_busca[0]} ({chave_busca[1]})')

    return True


def _get_kg_path(kg_dir: Path) -> Path:
    """Retorna o caminho do KG (ultimo patterns_*.json ou cria novo)."""
    arquivos = sorted(kg_dir.glob('patterns_*.json'))
    if arquivos:
        return arquivos[-1]
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    return kg_dir / f'patterns_{timestamp}.json'


def _carregar_kg(kg_path: Path) -> Dict:
    """Carrega o arquivo KG ou retorna dict vazio."""
    if not kg_path.exists():
        return {'metadata': {'criado': time.strftime('%Y-%m-%d %H:%M:%S')}, 'padroes': [], 'anti_patterns': []}
    try:
        with open(kg_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        if 'anti_patterns' not in dados:
            dados['anti_patterns'] = []
        return dados
    except Exception:
        return {'metadata': {}, 'padroes': [], 'anti_patterns': []}


def _buscar_ocorrencias(anti_patterns: List[Dict], chave: tuple) -> int:
    """Busca o contador de ocorrencias para uma chave."""
    for ap in anti_patterns:
        if (ap.get('api_problematica', '').lower() == chave[0] and
                ap.get('categoria', '') == chave[1]):
            return ap.get('ocorrencias', 0)
    return 0
