# EXPERIMENTAL — Use agent_loop como pipeline principal.
# task_analyzer foi construido como frontend do MetaCreator.
# O TaskAnalyzer em si e util (classifica inputs), mas o fluxo
# ideal e: TaskAnalyzer -> agent_loop (nao MetaCreator -> executor).
# Mantido como referencia.
"""TaskAnalyzer — Classificador universal de inputs do usuario.

Determina o TIPO de qualquer tarefa: criacao, analise, pergunta,
correcao, exploracao, execucao, ou meta.
Extrai parametros, subtipo, urgencia, e ferramentas relevantes.

Uso:
    from engine.task_analyzer import TaskAnalyzer
    analise = TaskAnalyzer.analisar("cria um ferreiro em Eridanus")
    print(analise.tipo)  # TaskType.CRIACAO
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import re, os, sys

# Path setup: engine/../ = Scripts/mcr_devia/
_MCR_DEVIA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _MCR_DEVIA not in sys.path:
    sys.path.insert(0, _MCR_DEVIA)

from knowledge.tool_registry import get_registry, Tool


# ============================================================
# TIPOS DE TAREFA
# ============================================================

class TaskType(Enum):
    CRIACAO = "criacao"         # "cria um ferreiro", "faz um site"
    ANALISE = "analise"         # "analisa esse codigo", "o que ha de errado?"
    PERGUNTA = "pergunta"       # "o que e SPA?", "como funciona o SHC?"
    CORRECAO = "correcao"       # "corrige esse bug", "arruma isso"
    EXPLORACAO = "exploracao"   # "como funciona o sistema de quests?"
    EXECUCAO = "execucao"       # "roda o autoteste", "compila o servidor"
    META = "meta"               # "o que voce sabe fazer?", "quais ferramentas tem?"
    DESCONHECIDO = "desconhecido"


# ============================================================
# SUBTIPOS (dominios especificos)
# ============================================================

SUBTIPOS_NPC = ['npc_shop', 'npc_quest', 'npc_bank', 'npc_gate', 
                'npc_trainer', 'npc_dialogue', 'npc']

SUBTIPOS_CRIACAO = SUBTIPOS_NPC + ['item', 'spell', 'monster', 'quest',
                                     'website', 'app', 'bot', 'script', 'talkaction']

SUBTIPOS_ANALISE = ['codigo', 'bug', 'projeto', 'performance', 'seguranca']

MAPA_SINONIMOS_SUBTIPO = {
    'loja': 'npc_shop',
    'shop': 'npc_shop',
    'vendedor': 'npc_shop',
    'mercador': 'npc_shop',
    'ferreiro': 'npc_shop',  # Ferreiro é um shop que vende armas
    'arma': 'npc_shop',
    'missao': 'npc_quest',
    'quest': 'npc_quest',
    'banco': 'npc_bank',
    'porteiro': 'npc_gate',
    'guarda': 'npc_gate',
    'treinador': 'npc_trainer',
    'mestre': 'npc_trainer',
    'dialogo': 'npc_dialogue',
    'conversa': 'npc_dialogue',
    'site': 'website',
    'pagina': 'website',
    'bot': 'bot',
    'app': 'app',
    'aplicativo': 'app',
    'spell': 'spell',
    'magia': 'spell',
    'item': 'item',
    'monstro': 'monster',
    'monster': 'monster',
    'talkaction': 'talkaction',
    'comando': 'talkaction',
}


# ============================================================
# VERBOS DE ACAO
# ============================================================

VERBOS_CRIACAO = [
    'cria', 'crie', 'criar', 'faca', 'faz', 'fazer', 'gera', 'gerar',
    'produz', 'produzir', 'constroi', 'construir', 'monta', 'montar',
    'elabora', 'elaborar', 'desenvolve', 'desenvolver', 'criação',
]

VERBOS_ANALISE = [
    'analisa', 'analise', 'analisar', 'examina', 'examinar', 'revisa',
    'revisar', 'avalia', 'avaliar', 'inspeciona', 'inspecionar',
    'estuda', 'estudar', 'investiga', 'investigar', 'diagnostica',
    'diagnosticar', 'análise', 'revisão',
]

VERBOS_PERGUNTA = [
    'o que', 'o que é', 'o que sao', 'o que são',
    'como', 'como funciona', 'como fazer',
    'por que', 'qual', 'quais', 'quem', 'quando', 'onde',
    'explique', 'explica', 'explicar', 'defina', 'definir',
    'significa', 'diferenca', 'qual a',
]

VERBOS_CORRECAO = [
    'corrige', 'corrija', 'corrigir', 'arruma', 'arrumar',
    'conserta', 'concertar', 'resolve', 'resolver',
    'repara', 'reparar', 'correção', 'bug', 'erro',
]

VERBOS_EXPLORACAO = [
    'explora', 'explorar', 'navega', 'navegar', 'mapeia',
    'mapear', 'descobre', 'descobrir', 'entende', 'entender',
    'como funciona o', 'como é', 'mostra', 'mostrar',
]

VERBOS_EXECUCAO = [
    'roda', 'rodar', 'executa', 'executar', 'compila',
    'compilar', 'build', 'buildar', 'inicia', 'iniciar',
    'ativa', 'ativar', 'liga', 'ligar',
]

VERBOS_META = [
    'o que voce', 'o que sabe', 'quais ferramentas',
    'quais capacidades', 'o que pode', 'como funciona o sistema',
    'o que faz', 'quem e voce', 'apresente-se',
    'ajuda', 'help', 'comandos',
]


# ============================================================
# ANALISADOR DE TAREFA
# ============================================================

@dataclass
class TaskAnalysis:
    """Resultado da analise de uma tarefa."""
    tipo: TaskType
    subtipo: str = ""                    # "npc_shop", "codigo", etc
    descricao: str = ""                  # Input original
    parametros: Dict[str, Any] = field(default_factory=dict)  # Extraidos
    urgencia: float = 0.5                # 0.0 a 1.0
    ferramentas_relevantes: List[Tool] = field(default_factory=list)
    confianca: float = 0.0               # 0.0 a 1.0
    tokens_importantes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'tipo': self.tipo.value,
            'subtipo': self.subtipo,
            'descricao': self.descricao[:100],
            'parametros': self.parametros,
            'urgencia': self.urgencia,
            'ferramentas': [t.nome for t in self.ferramentas_relevantes[:5]],
            'confianca': self.confianca,
        }


class TaskAnalyzer:
    """Analisa e classifica qualquer input do usuario."""
    
    @staticmethod
    def analisar(input_usuario: str) -> TaskAnalysis:
        """Analisa o input e retorna uma TaskAnalysis completa."""
        texto = input_usuario.strip()
        texto_lower = texto.lower()
        
        resultado = TaskAnalysis(
            tipo=TaskType.DESCONHECIDO,
            descricao=texto,
            confianca=0.0,
        )
        
        # Extrair tokens importantes
        resultado.tokens_importantes = list(set(
            re.findall(r'\b[a-zà-ú]{3,}\b', texto_lower)
        ))
        
        # Extrair parametros (nome, local, tipo)
        resultado.parametros = TaskAnalyzer._extrair_parametros(texto)
        
        # Classificar tipo
        tipo, confianca = TaskAnalyzer._classificar_tipo(texto_lower)
        resultado.tipo = tipo
        resultado.confianca = confianca
        
        # Detectar subtipo
        resultado.subtipo = TaskAnalyzer._detectar_subtipo(tipo, texto_lower)
        
        # Detectar urgencia
        resultado.urgencia = TaskAnalyzer._detectar_urgencia(texto_lower)
        
        # Buscar ferramentas relevantes
        reg = get_registry()
        resultado.ferramentas_relevantes = reg.buscar_por_palavras_chave(texto)
        
        # Se não encontrou ferramentas, tenta por categoria
        if not resultado.ferramentas_relevantes:
            mapa_categoria = {
                TaskType.CRIACAO: "geracao",
                TaskType.ANALISE: "analise",
                TaskType.PERGUNTA: "analise",
                TaskType.CORRECAO: "analise",
                TaskType.EXPLORACAO: "busca",
                TaskType.EXECUCAO: "sistema",
                TaskType.META: "meta",
            }
            cat = mapa_categoria.get(tipo)
            if cat:
                resultado.ferramentas_relevantes = reg.listar(categoria=cat)[:3]
        
        return resultado
    
    @staticmethod
    def _classificar_tipo(texto_lower: str) -> tuple:
        """Classifica o tipo da tarefa baseado no texto."""
        scores = {}
        
        # Verifica verbos de cada categoria
        for tipo, verbos in [
            (TaskType.CRIACAO, VERBOS_CRIACAO),
            (TaskType.ANALISE, VERBOS_ANALISE),
            (TaskType.PERGUNTA, VERBOS_PERGUNTA),
            (TaskType.CORRECAO, VERBOS_CORRECAO),
            (TaskType.EXPLORACAO, VERBOS_EXPLORACAO),
            (TaskType.EXECUCAO, VERBOS_EXECUCAO),
            (TaskType.META, VERBOS_META),
        ]:
            score = 0
            for verbo in verbos:
                if texto_lower.startswith(verbo) or f' {verbo} ' in f' {texto_lower} ':
                    score += 3
                if verbo in texto_lower:
                    score += 1
            
            # Bônus para padrões específicos
            if tipo == TaskType.PERGUNTA:
                if texto_lower.endswith('?'):
                    score += 2
                if re.search(r'^(o que|como|qual|quais|quem)', texto_lower):
                    score += 2
            
            if tipo == TaskType.CRIACAO:
                if any(p in texto_lower for p in ['um ', 'uma ', 'um ']):
                    score += 1
            
            if score > 0:
                scores[tipo] = score
        
        # Verifica comandos diretos
        comandos_map = {
            'status': TaskType.EXECUCAO,
            'help': TaskType.META,
            'ajuda': TaskType.META,
            'teste': TaskType.EXECUCAO,
            'autoteste': TaskType.EXECUCAO,
        }
        for cmd, tipo in comandos_map.items():
            if texto_lower.strip() == cmd or texto_lower.startswith(cmd + ' '):
                return tipo, 0.95
        
        if not scores:
            # Fallback: pergunta genérica
            return TaskType.PERGUNTA, 0.40
        
        # Pega o tipo com maior score
        melhor_tipo = max(scores, key=scores.get)
        max_score = scores[melhor_tipo]
        
        # Normaliza confiança
        confianca = min(0.50 + max_score * 0.10, 0.98)
        
        return melhor_tipo, confianca
    
    @staticmethod
    def _detectar_subtipo(tipo: TaskType, texto_lower: str) -> str:
        """Detecta o subtipo especifico da tarefa."""
        if tipo == TaskType.CRIACAO:
            # Procura por sinonimos de subtipo
            for palavra, subtipo in MAPA_SINONIMOS_SUBTIPO.items():
                if palavra in texto_lower:
                    return subtipo
            return "generico"
        
        elif tipo == TaskType.ANALISE:
            if 'código' in texto_lower or 'codigo' in texto_lower or '.lua' in texto_lower or '.py' in texto_lower:
                return 'codigo'
            if 'bug' in texto_lower or 'erro' in texto_lower:
                return 'bug'
            if 'projeto' in texto_lower or 'sistema' in texto_lower:
                return 'projeto'
            if 'segurança' in texto_lower or 'sql' in texto_lower:
                return 'seguranca'
            return 'generico'
        
        elif tipo == TaskType.CORRECAO:
            if 'lua' in texto_lower or '.lua' in texto_lower:
                return 'codigo_lua'
            if 'npc' in texto_lower:
                return 'npc'
            return 'generico'
        
        elif tipo == TaskType.PERGUNTA:
            if 'npc' in texto_lower:
                return 'sobre_npc'
            if 'spa' in texto_lower or 'shc' in texto_lower:
                return 'sobre_sistema'
            if 'como funciona' in texto_lower:
                return 'explicacao'
            return 'generico'
        
        elif tipo == TaskType.EXECUCAO:
            if 'compila' in texto_lower or 'build' in texto_lower:
                return 'compilacao'
            if 'teste' in texto_lower or 'autoteste' in texto_lower:
                return 'teste'
            if 'inicia' in texto_lower or 'liga' in texto_lower:
                return 'inicializacao'
            return 'generico'
        
        elif tipo == TaskType.META:
            if 'ferramenta' in texto_lower or 'capacidade' in texto_lower:
                return 'capacidades'
            if 'como funciona' in texto_lower:
                return 'explicacao_sistema'
            return 'generico'
        
        return ""
    
    @staticmethod
    def _extrair_parametros(texto: str) -> Dict[str, Any]:
        """Extrai parametros uteis do texto."""
        params = {}
        texto_lower = texto.lower()
        
        # Nome proprio (primeira palavra depois do verbo)
        # "cria um ferreiro em Eridanus" → nome="ferreiro", local="Eridanus"
        
        # Local/destino
        locais = ['eridanus', 'venore', 'thais', 'carlin', 'kazordoon',
                   "ab'dendriel", 'darashia', 'ankrahmun', 'liberty bay',
                   'port hope', 'yalahar', 'svargrond', 'farmine']
        for local in locais:
            if local in texto_lower:
                params['local'] = local.capitalize()
                break
        
        # Tipo de NPC
        tipos = ['shop', 'quest', 'bank', 'gate', 'trainer', 'dialogue']
        palavras_texto = set(re.findall(r'\b[a-zà-ú]+\b', texto_lower))
        
        if 'npc' in palavras_texto or any(t in texto_lower for t in ['ferreiro', 'vendedor', 'mercador', 'loja']):
            for t in tipos:
                if t in texto_lower:
                    params['tipo_npc'] = t
                    break
            if 'tipo_npc' not in params:
                # Detecta por palavra-chave
                palavra_para_tipo = {
                    'ferreiro': 'shop', 'arma': 'shop', 'vende': 'shop', 'loja': 'shop',
                    'missao': 'quest', 'quest': 'quest',
                    'banco': 'bank', 'depositar': 'bank',
                    'porteiro': 'gate', 'guarda': 'gate', 'passagem': 'gate',
                    'treinador': 'trainer', 'ensina': 'trainer',
                    'conversa': 'dialogue', 'informacao': 'dialogue',
                }
                for palavra, tipo in palavra_para_tipo.items():
                    if palavra in texto_lower:
                        params['tipo_npc'] = tipo
                        break
        
        # Profissão/tema
        profissoes = ['ferreiro', 'alquimista', 'mercador', 'bibliotecario',
                       'guarda', 'mago', 'guerreiro', 'druida', 'paladino',
                       'anão', 'anao', 'elfo', 'orc', 'humano']
        for prof in profissoes:
            if prof in texto_lower:
                params['profissao'] = prof.capitalize()
                break
        
        # Item especifico
        itens = ['espada', 'armadura', 'pocao', 'anel', 'amuleto', 'escudo',
                  'arco', 'varinha', 'cajado', 'machado', 'martelo']
        for item in itens:
            if item in texto_lower:
                params['item'] = item
                break
        
        # Arquivo (se parece com caminho)
        caminhos = re.findall(r'[\w/\\]+\.[a-z]+', texto)
        if caminhos:
            params['arquivo'] = caminhos[0]
        
        return params
    
    @staticmethod
    def _detectar_urgencia(texto_lower: str) -> float:
        """Detecta nivel de urgencia (0.0 a 1.0)."""
        urgencia = 0.5  # Padrão
        
        # Palavras que indicam urgencia
        if any(p in texto_lower for p in ['urgente', 'rápido', 'rapido', 'agora', 'já', 'ja', 'corre']):
            urgencia += 0.3
        
        # Palavras que indicam baixa urgencia
        if any(p in texto_lower for p in ['quando der', 'depois', 'sem pressa', 'sem pressa']):
            urgencia -= 0.2
        
        return min(max(urgencia, 0.0), 1.0)


# ============================================================
# FUNÇÃO Única para uso externo
# ============================================================

def analisar_tarefa(input_usuario: str) -> TaskAnalysis:
    """Funcao unica de entrada para analise de tarefa."""
    return TaskAnalyzer.analisar(input_usuario)


# ============================================================
# TESTE
# ============================================================

if __name__ == '__main__':
    testes = [
        "cria um ferreiro em Eridanus",
        "analisa esse codigo Lua",
        "o que e SPA?",
        "corrige o bug do NPC",
        "como funciona o sistema de quests?",
        "roda o autoteste ciclo 3",
        "o que voce sabe fazer?",
        "faz um site de busca de itens",
        "compila o servidor",
        "um banco em Venore",
    ]
    
    print("=== TESTE TASK ANALYZER ===\n")
    for teste in testes:
        analise = analisar_tarefa(teste)
        print(f"Input: {teste}")
        print(f"  Tipo: {analise.tipo.value} (confianca: {analise.confianca:.2f})")
        print(f"  Subtipo: {analise.subtipo}")
        if analise.parametros:
            print(f"  Parametros: {analise.parametros}")
        if analise.ferramentas_relevantes:
            print(f"  Ferramentas: {[t.nome for t in analise.ferramentas_relevantes[:4]]}")
        print()
