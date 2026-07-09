"""CanaryIndexer — Indexador do ecossistema Canary (NPCs, Schema DB, API).

Varre NPCs do servidor, extrai padrões e constrói base de conhecimento
para geração inteligente de scripts. Base da arquitetura AGI do MCR-DevIA.

Uso:
    from modulos.canary_indexer import CanaryIndexer
    idx = CanaryIndexer()
    idx.indexar()  # Varre tudo
    resultados = idx.buscar("ferreiro que vende espadas")
"""
import os, re, json, glob as _glob
from typing import List, Dict, Optional
from difflib import SequenceMatcher

# ============================================================
# CONSTANTES
# ============================================================

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')

# Diretórios de NPCs
NPC_DIRS = [
    os.path.join(BASE, 'Canary', 'data-otservbr-global', 'npc'),
    os.path.join(BASE, 'Canary', 'data-canary', 'scripts', 'MCR'),
    os.path.join(BASE, 'Canary', 'data', 'npc'),
    os.path.join(BASE, 'Canary', 'data', 'scripts', 'actions', 'npc'),
]

# Diretórios de lib (API do servidor)
LIB_DIRS = [
    os.path.join(BASE, 'Canary', 'data'),
    os.path.join(BASE, 'Canary', 'data-otservbr-global', 'lib'),
    os.path.join(BASE, 'Canary', 'data-otservbr-global', 'lib', 'core'),
    os.path.join(BASE, 'Canary', 'data-otservbr-global', 'lib', 'functions'),
    os.path.join(BASE, 'Canary', 'data-otservbr-global', 'lib', 'others'),
]

# Arquivo de saída do índice
INDEX_PATH = os.path.join(SANDBOX, 'canary_index.json')
SCHEMA_PATH = os.path.join(SANDBOX, 'canary_schema.json')

# ============================================================
# TIPOS DE NPC
# ============================================================

TIPOS_NPC = {
    'shop':   'Vende ou compra itens',
    'quest':  'Dá quests, verifica progresso, recompensa',
    'bank':   'Depósito e saque de gold',
    'gate':   'Acesso por level/item/quest',
    'trainer':'Ensina spells ou skills',
    'dialogue':'Apenas diálogo (lore, dicas, informações)',
    'account':'Gerenciamento de conta (oráculo)',
    'other':  'Outro / desconhecido',
}

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

# ============================================================
# SINÔNIMOS PT-EN para busca semântica
# ============================================================

SINONIMOS = {
    # Profissões
    'ferreiro': 'blacksmith smith weaponshop',
    'ferreira': 'blacksmith smith',
    'mercador': 'merchant trader vendor',
    'vendedor': 'seller vendor merchant trader',
    'armeiro': 'weaponsmith blacksmith',
    
    # Ações
    'vende': 'sell trade shop',
    'compra': 'buy purchase trade',
    'vender': 'sell trade',
    'comprar': 'buy purchase trade',
    
    # Itens
    'arma': 'weapon sword axe mace',
    'armas': 'weapons swords axes maces',
    'espada': 'sword blade',
    'espadas': 'swords blades',
    'armadura': 'armor shield',
    'armaduras': 'armors shields',
    'pocao': 'potion flask',
    'pocoes': 'potions flasks',
    'anel': 'ring',
    'aneis': 'rings',
    'amuletos': 'amulets necklace',
    'amuleto': 'amulet necklace',
    'ferramenta': 'tool pickaxe shovel rope',
    'ferramentas': 'tools picks shovels ropes',
    
    # Locais
    'banco': 'bank deposit withdraw gold',
    'templo': 'temple priest heal',
    'treinador': 'trainer train skill spell',
    
    # Missões
    'missao': 'quest mission',
    'missoes': 'quests missions',
    'recompensa': 'reward prize',
    
    # Diversos
    'comida': 'food bread meat fish',
    'bebida': 'drink water beer wine',
    'magia': 'spell magic rune',
    'magias': 'spells magic runes',
    'runas': 'runes magic',
    'runa': 'rune spell magic',
}

def _expandir_termos(consulta: str) -> str:
    """Expande termos PT para incluir sinônimos em EN."""
    palavras = re.findall(r'\b[a-zà-ú]+\b', consulta.lower())
    extras = []
    for p in palavras:
        if p in SINONIMOS:
            extras.append(SINONIMOS[p])
    return consulta + ' ' + ' '.join(extras)


def _extrair_nome_npc(conteudo: str) -> str:
    """Extrai o nome interno do NPC do código."""
    m = re.search(r'(?:local\s+)?(?:internalNpcName|npcName)\s*=\s*"([^"]+)"', conteudo)
    if m:
        return m.group(1)
    # Fallback: primeiro nome mencionado no config
    m = re.search(r'name\s*=\s*"([^"]+)"', conteudo)
    if m:
        return m.group(1)
    return "unknown"


def _extrair_descricao(conteudo: str) -> str:
    """Extrai a descrição do NPC."""
    m = re.search(r'description\s*=\s*"([^"]+)"', conteudo)
    return m.group(1) if m else ""


def _extrair_looktype(conteudo: str) -> Optional[int]:
    """Extrai o lookType do outfit."""
    m = re.search(r'lookType\s*=\s*(\d+)', conteudo)
    return int(m.group(1)) if m else None


def _extrair_tipo(conteudo: str, nome: str) -> str:
    """Detecta o tipo do NPC baseado no código."""
    s_lower = conteudo.lower()
    
    # Shop: config shop com itens
    if 'npcconfig.shop' in s_lower:
        return 'shop'
    if 'stdmodule.shop' in s_lower:
        return 'shop'
    
    # Account: gerenciamento de conta
    if re.search(r'account|senha|password|criar\s*conta|registra', s_lower):
        if 'ngi' not in s_lower:  # Evita "AccountManager" genérico
            return 'account'
    
    # Quest: storage + mission/reward
    if re.search(r'storagevalue.*(?:mission|reward|quest)', s_lower):
        return 'quest'
    if 'stdmodule.quest' in s_lower:
        return 'quest'
    # Quest também pode ser detectado por múltiplos setTopic com recompensa
    topicos = set(re.findall(r'npchandler:settopic\([^,]+,\s*(\d+)\)', s_lower))
    if len(topicos) >= 3 and re.search(r'additem|removeitem|removeMoney|removeMoneyBank', s_lower):
        return 'quest'
    
    # Bank: operações bancárias
    if re.search(r'deposit|withdraw|bank|balance', s_lower):
        if re.search(r'your\s*balance|gold|money', s_lower):
            return 'bank'
    
    # Gate: restrição de acesso
    if re.search(r'getlevel|getstorage|storagevalue.*gate|access.*denied|blocked', s_lower):
        return 'gate'
    
    # Trainer: ensina spells
    if re.search(r'spell|train|skill|learn|teach', s_lower):
        return 'trainer'
    
    # Dialogue: tem handler de conversa
    if re.search(r'creaturesaycallback|keywordhandler:new|addkeyword', s_lower):
        return 'dialogue'
    
    return 'other'


def _extrair_itens_shop(conteudo: str) -> List[Dict]:
    """Extrai lista de itens vendidos/comprados."""
    itens = []
    # Encontra cada item individual { itemName = ..., clientId = ... }
    for item_match in re.finditer(
        r'\{\s*itemName\s*=\s*"([^"]*)"\s*,\s*clientId\s*=\s*(\d+)([^}]*)\}',
        conteudo
    ):
        item = {
            'nome': item_match.group(1),
            'client_id': int(item_match.group(2)),
        }
        bloco = item_match.group(3)
        if 'buy' in bloco:
            buy_m = re.search(r'buy\s*=\s*(\d+)', bloco)
            if buy_m:
                item['buy'] = int(buy_m.group(1))
        if 'sell' in bloco:
            sell_m = re.search(r'sell\s*=\s*(\d+)', bloco)
            if sell_m:
                item['sell'] = int(sell_m.group(1))
        itens.append(item)
    return itens


def _extrair_queries(conteudo: str) -> List[str]:
    """Extrai queries SQL do código."""
    queries = []
    for m in re.finditer(
        r'(?:db\.(?:storeQuery|query|asyncQuery)\s*\(\s*)([^)]+)\)',
        conteudo
    ):
        query = m.group(1).strip()
        if query and len(query) > 10:
            queries.append(query)
    return queries


def _extrair_topicos(conteudo: str) -> int:
    """Conta quantos tópicos (estados) o NPC tem."""
    return len(set(re.findall(r'npcHandler:setTopic\([^,]+,\s*(\d+)\)', conteudo)))


def _extrair_palavras_chave(conteudo: str) -> List[str]:
    """Extrai palavras-chave registradas no KeywordHandler."""
    palavras = []
    for m in re.finditer(r'addKeyword\(\s*\{([^}]+)\}', conteudo):
        texto = m.group(1)
        for palavra in re.findall(r'"([^"]+)"', texto):
            if palavra and len(palavra) > 2:
                palavras.append(palavra)
    return palavras


def _extrair_mensagens(conteudo: str) -> Dict[str, str]:
    """Extrai mensagens padrão (GREET, FAREWELL, etc)."""
    msgs = {}
    for m in re.finditer(r'setMessage\(MESSAGE_(\w+),\s*"([^"]+)"\)', conteudo):
        msgs[m.group(1)] = m.group(2)
    return msgs


def _extrair_tamanho(conteudo: str) -> int:
    """Retorna número de linhas do NPC."""
    return conteudo.count('\n') + 1


# ============================================================
# CANARY INDEXER
# ============================================================

class CanaryIndexer:
    """Indexador do ecossistema Canary.
    
    Escaneia diretórios de NPC, extrai metadados, detecta padrões,
    e permite busca semântica por similaridade.
    """
    
    def __init__(self):
        self.npcs: List[Dict] = []
        self.schema: Dict = {}
        self.api_patterns: Dict = {}
        self._carregado = False
    
    def indexar(self, forcar: bool = False) -> Dict:
        """Indexa (ou carrega) todos os NPCs + schema DB + API.
        
        Args:
            forcar: Se True, re-indexa do zero. Se False, carrega cache.
        
        Returns:
            Dict com estatísticas do índice
        """
        if not forcar and os.path.exists(INDEX_PATH):
            return self._carregar_cache()
        
        stats = {'npcs': 0, 'shops': 0, 'quests': 0, 'queries': 0}
        
        # --- Indexar NPCs ---
        for diretorio in NPC_DIRS:
            if not os.path.isdir(diretorio):
                continue
            for arquivo in sorted(_glob.glob(os.path.join(diretorio, '*.lua'))):
                try:
                    with open(arquivo, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read()
                except Exception:
                    continue
                
                info = self._analisar_npc(arquivo, conteudo)
                self.npcs.append(info)
                stats['npcs'] += 1
                if info['tipo'] == 'shop':
                    stats['shops'] += 1
                elif info['tipo'] == 'quest':
                    stats['quests'] += 1
                stats['queries'] += len(info['queries'])
        
        # --- Indexar Schema DB ---
        self._extrair_schema()
        
        # --- Indexar API patterns ---
        self._extrair_api()
        
        # Salvar cache
        self._salvar_cache()
        
        stats['total_queries'] = stats['queries']
        self._carregado = True
        return stats
    
    def _analisar_npc(self, caminho: str, conteudo: str) -> Dict:
        """Analisa um arquivo NPC e extrai metadados."""
        nome = _extrair_nome_npc(conteudo)
        
        info = {
            'arquivo': caminho,
            'nome': nome,
            'nome_arquivo': os.path.basename(caminho),
            'tamanho_linhas': _extrair_tamanho(conteudo),
            'tipo': _extrair_tipo(conteudo, nome),
            'descricao': _extrair_descricao(conteudo),
            'looktype': _extrair_looktype(conteudo),
            'topicos': _extrair_topicos(conteudo),
            'itens_shop': _extrair_itens_shop(conteudo),
            'queries': _extrair_queries(conteudo),
            'palavras_chave': _extrair_palavras_chave(conteudo),
            'mensagens': _extrair_mensagens(conteudo),
            'tem_npchandler': 'NpcHandler:new' in conteudo,
            'tem_keywordhandler': 'KeywordHandler:new' in conteudo,
            'tem_creaturesaycallback': 'CALLBACK_MESSAGE_DEFAULT' in conteudo,
            'tem_shop_config': 'npcConfig.shop' in conteudo,
            'tem_onbuyitem': 'onBuyItem' in conteudo,
            'tem_onsellitem': 'onSellItem' in conteudo,
            'tem_storage': 'getStorageValue' in conteudo,
            'tem_db': 'db.' in conteudo,
            'conteudo_resumido': conteudo,  # Para busca RAG
        }
        return info
    
    def _extrair_schema(self):
        """Extrai schema do banco de dados a partir das queries."""
        tabelas = {}
        for npc in self.npcs:
            for query in npc['queries']:
                for m in re.finditer(
                    r'(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+(\w+)',
                    query, re.IGNORECASE
                ):
                    tabela = m.group(1).lower()
                    if tabela not in tabelas:
                        tabelas[tabela] = {'exemplos': [], 'colunas': set()}
                    if query not in tabelas[tabela]['exemplos']:
                        tabelas[tabela]['exemplos'].append(query)
                    # Extrai colunas
                    for col in re.finditer(r'(\w+)\s*=', query):
                        tabelas[tabela]['colunas'].add(col.group(1).lower())
        self.schema = {
            'tabelas': {k: {
                'exemplos': v['exemplos'],
                'colunas': sorted(v['colunas'])
            } for k, v in tabelas.items()}
        }
    
    def _extrair_api(self):
        """Extrai padrões de API do servidor (lib/)."""
        padroes = {}
        for diretorio in LIB_DIRS:
            if not os.path.isdir(diretorio):
                continue
            for arquivo in sorted(_glob.glob(os.path.join(diretorio, '*.lua'))):
                try:
                    with open(arquivo, 'r', encoding='utf-8', errors='replace') as f:
                        conteudo = f.read()
                except Exception:
                    continue
                nome = os.path.basename(arquivo).replace('.lua', '')
                # Extrai funções definidas
                funcoes = re.findall(r'(?:function\s+(\w+)[.(])', conteudo)
                if funcoes:
                    padroes[nome] = funcoes
        self.api_patterns = padroes
    
    def _tokenizar(self, texto: str) -> set:
        """Tokeniza texto em palavras relevantes (min 3 chars)."""
        return set(re.findall(r'\b[a-zà-ú]{3,}\b', texto.lower()))
    
    def buscar(self, consulta: str, limite: int = 5) -> List[Dict]:
        """Busca NPCs por similaridade textual com a consulta.
        
        Usa token matching sobre nome, descrição, palavras-chave, itens.
        Quanto mais tokens da consulta aparecem no NPC, maior o score.
        
        Args:
            consulta: Termo de busca (ex: "ferreiro que vende espadas")
            limite: Máximo de resultados
        
        Returns:
            Lista de NPCs ordenados por relevância
        """
        if not self._carregado:
            self.indexar()
        
        consulta_expandida = _expandir_termos(consulta)
        tokens_consulta = self._tokenizar(consulta_expandida)
        if not tokens_consulta:
            return []
        
        resultados = []
        
        for npc in self.npcs:
            # Monta corpus pesquisável do NPC
            corpus = self._tokenizar(npc['nome'])
            corpus.update(self._tokenizar(npc.get('descricao', '')))
            for kw in npc.get('palavras_chave', []):
                corpus.update(self._tokenizar(kw))
            for item in npc.get('itens_shop', []):
                corpus.update(self._tokenizar(item['nome']))
            # Inclui conteúdo do arquivo se disponível
            if 'conteudo_resumido' in npc and npc['conteudo_resumido']:
                corpus.update(self._tokenizar(npc['conteudo_resumido']))
            
            # Score = proporção de tokens da consulta que aparecem no corpus
            if corpus:
                match = tokens_consulta & corpus
                if match:
                    score = len(match) / len(tokens_consulta) * 50
                    # Bônus por match no nome
                    nome_tokens = self._tokenizar(npc['nome'])
                    if tokens_consulta & nome_tokens:
                        score += 20
                    # Bônus por match em itens (com expansão)
                    for item in npc.get('itens_shop', []):
                        item_texto = _expandir_termos(item['nome'])
                        item_tokens = self._tokenizar(item_texto)
                        if tokens_consulta & item_tokens:
                            score += 20 + len(tokens_consulta & item_tokens) * 5
                    
                    score = round(score, 1)
                    resultados.append({'score': score, **npc})
        
        resultados.sort(key=lambda x: x['score'], reverse=True)
        return resultados
    
    def buscar_por_tipo(self, tipo: str) -> List[Dict]:
        """Retorna NPCs de um tipo específico."""
        if not self._carregado:
            self.indexar()
        return [n for n in self.npcs if n['tipo'] == tipo]
    
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas do índice."""
        if not self._carregado:
            self.indexar()
        
        tipos = {}
        for n in self.npcs:
            t = n['tipo']
            tipos[t] = tipos.get(t, 0) + 1
        
        return {
            'total_npcs': len(self.npcs),
            'tipos': tipos,
            'total_queries_db': sum(len(n['queries']) for n in self.npcs),
            'tabelas_db': len(self.schema.get('tabelas', {})),
            'api_modulos': len(self.api_patterns),
            'tamanho_medio_linhas': sum(n['tamanho_linhas'] for n in self.npcs) // max(len(self.npcs), 1),
        }
    
    def _salvar_cache(self):
        """Salva o índice em disco."""
        os.makedirs(SANDBOX, exist_ok=True)
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            # Mantém conteúdo resumido truncado (primeiros 2000 chars) para busca
            npcs_save = []
            for n in self.npcs:
                entry = dict(n)
                if 'conteudo_resumido' in entry and len(entry['conteudo_resumido']) > 2000:
                    entry['conteudo_resumido'] = entry['conteudo_resumido']
                npcs_save.append(entry)
            json.dump({'npcs': npcs_save, 'schema': self.schema, 'api': self.api_patterns}, 
                      f, ensure_ascii=False, indent=2)
    
    def _carregar_cache(self) -> Dict:
        """Carrega o índice do disco."""
        with open(INDEX_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.npcs = data.get('npcs', [])
        self.schema = data.get('schema', {})
        self.api_patterns = data.get('api', {})
        self._carregado = True
        return {'npcs': len(self.npcs), 'cache': True}
    
    def iniciar(self, forcar=False):
        """Inicialização rápida para integração com kernel."""
        return self.indexar(forcar=forcar)


# ============================================================
# PONTO DE ENTRADA
# ============================================================

if __name__ == '__main__':
    import time
    t0 = time.time()
    idx = CanaryIndexer()
    stats = idx.indexar(forcar=True)
    print(f"Indexado em {time.time()-t0:.1f}s")
    print(f"NPCs: {stats['npcs']} | Shops: {stats['shops']} | Quests: {stats['quests']}")
    print(f"Queries DB: {stats['queries']}")
    
    # Teste de busca
    print("\n--- Busca: 'ferreiro que vende espadas' ---")
    resultados = idx.buscar("ferreiro que vende espadas")
    for r in resultados:
        print(f"  [{r['score']}] {r['nome']} ({r['tipo']}, {r['tamanho_linhas']} linhas)")
    
    print("\n--- Estatísticas ---")
    est = idx.obter_estatisticas()
    for k, v in est.items():
        print(f"  {k}: {v}")
    
    if est.get('tabelas_db'):
        print(f"\n--- Tabelas DB ({est['tabelas_db']}) ---")
        for tbl in list(idx.schema.get('tabelas', {}).keys()):
            print(f"  - {tbl}")
