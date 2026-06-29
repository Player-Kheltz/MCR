"""ToolRegistry — Catálogo de TODAS as capacidades do MCR-DevIA.

Cada ferramenta sabe: o que faz, quando usar, o que precisa.
Usado pelo MetaCreator para planejamento e roteamento inteligente.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
import re, os, json, inspect


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class Parametro:
    nome: str
    tipo: str  # "string" | "int" | "float" | "bool" | "list" | "dict"
    descricao: str
    obrigatorio: bool = True
    default: Any = None


@dataclass
class Tool:
    """Uma capacidade do sistema."""
    nome: str
    descricao: str
    categoria: str  # "busca" | "analise" | "geracao" | "validacao" | "web" | "aprendizado" | "sistema" | "meta"
    comandos: List[str]  # Nomes dos comandos que implementam
    modulos: List[str]   # Módulos envolvidos
    parametros: List[Parametro]
    saida: str
    fontes: List[str]          # "canary_indexer" | "items_xml" | "kg" | "web" | "llm"
    requisitos: List[str]      # "indexer_carregado" | "ollama_rodando"
    confianca_padrao: float    # 0.0 a 1.0
    palavras_chave: List[str]  # Para matching com descrição do usuário
    exemplo_uso: str = ""
    ativa: bool = True


class ToolRegistry:
    """Catálogo vivo de todas as capacidades do MCR-DevIA."""
    
    def __init__(self):
        self._ferramentas: Dict[str, Tool] = {}
        self._carregar_todas()
    
    def _carregar_todas(self):
        """Registra todas as ferramentas do sistema."""
        tools = []
        
        # ================================================================
        # BUSCA
        # ================================================================
        tools.append(Tool(
            nome="buscar_npc",
            descricao="Busca NPCs similares no servidor Canary por descricao ou tipo",
            categoria="busca",
            comandos=["cmd_gerar_npc", "cmd_explorar"],
            modulos=["canary_indexer"],
            parametros=[
                Parametro("descricao", "string", "Descricao do NPC desejado"),
                Parametro("tipo", "string", "Tipo do NPC (shop/quest/bank/gate/trainer/dialogue)", obrigatorio=False, default=""),
            ],
            saida="lista de NPCs com nome, tipo, itens, score de relevancia",
            fontes=["canary_indexer"],
            requisitos=["indexer_carregado"],
            confianca_padrao=0.95,
            palavras_chave=["npc", "buscar", "encontrar", "personagem", "shop", "loja"],
            exemplo_uso='buscar_npc(descricao="ferreiro que vende espadas", tipo="shop")',
        ))
        
        tools.append(Tool(
            nome="buscar_item",
            descricao="Busca itens no items.xml por nome ou categoria",
            categoria="busca",
            comandos=["cmd_gerar_npc", "cmd_explorar"],
            modulos=["item_database"],  # Será criado
            parametros=[
                Parametro("nome", "string", "Nome do item (parcial ou completo)", obrigatorio=False),
                Parametro("categoria", "string", "Categoria primaria (ex: sword weapons)", obrigatorio=False),
                Parametro("id", "int", "ID numerico do item", obrigatorio=False),
            ],
            saida="informacoes do item (id, nome, categoria, atributos)",
            fontes=["items_xml"],
            requisitos=["items_xml_carregado"],
            confianca_padrao=0.98,
            palavras_chave=["item", "buscar", "id", "clientid", "nome", "categoria"],
            exemplo_uso='buscar_item(nome="giant sword")',
        ))
        
        tools.append(Tool(
            nome="buscar_codigo",
            descricao="Busca trechos de codigo fonte no projeto",
            categoria="busca",
            comandos=["cmd_grep", "cmd_glob", "cmd_explorar"],
            modulos=["util"],
            parametros=[
                Parametro("padrao", "string", "Regex ou texto para buscar"),
                Parametro("caminho", "string", "Diretorio para buscar", obrigatorio=False, default="."),
                Parametro("incluir", "string", "Padrao de arquivo (ex: *.lua)", obrigatorio=False),
            ],
            saida="linhas de codigo correspondentes",
            fontes=["codigo_fonte"],
            requisitos=[],
            confianca_padrao=1.0,
            palavras_chave=["codigo", "buscar", "grep", "procurar", "encontrar"],
            exemplo_uso='buscar_codigo(padrao="npcType:register", incluir="*.lua")',
        ))
        
        tools.append(Tool(
            nome="buscar_kg",
            descricao="Busca conhecimento no Knowledge Graph do projeto",
            categoria="busca",
            comandos=["cmd_perguntar", "cmd_ensinar", "cmd_aprender_conceito"],
            modulos=["kg"],
            parametros=[
                Parametro("texto", "string", "Texto para buscar similaridade"),
                Parametro("max_r", "int", "Maximo de resultados", obrigatorio=False, default=5),
            ],
            saida="licoes do KG relevantes ao texto",
            fontes=["kg"],
            requisitos=[],
            confianca_padrao=0.90,
            palavras_chave=["kg", "conhecimento", "licao", "saber", "aprender"],
            exemplo_uso='buscar_kg(texto="ferreiro NPC")',
        ))
        
        tools.append(Tool(
            nome="buscar_docs",
            descricao="Busca documentacao do projeto",
            categoria="busca",
            comandos=["cmd_explorar"],
            modulos=["context_reinforcer"],
            parametros=[
                Parametro("consulta", "string", "O que buscar"),
            ],
            saida="trechos de documentacao relevante",
            fontes=["documentacao"],
            requisitos=[],
            confianca_padrao=0.85,
            palavras_chave=["doc", "documentacao", "manual", "ajuda"],
            exemplo_uso='buscar_docs(consulta="NPC sistema de loja")',
        ))
        
        # ================================================================
        # ANÁLISE
        # ================================================================
        tools.append(Tool(
            nome="analisar_codigo",
            descricao="Analisa codigo fonte e aponta problemas, sugestoes e melhorias",
            categoria="analise",
            comandos=["cmd_analisar", "cmd_revisar"],
            modulos=["auto_revisor", "ia"],
            parametros=[
                Parametro("caminho", "string", "Arquivo ou diretorio para analisar"),
                Parametro("profundidade", "string", "rapida/completa", obrigatorio=False, default="completa"),
            ],
            saida="relatorio de analise com problemas encontrados",
            fontes=["codigo_fonte", "llm"],
            requisitos=["ollama_rodando"],
            confianca_padrao=0.80,
            palavras_chave=["analisar", "revisar", "codigo", "bug", "erro", "problema"],
            exemplo_uso='analisar_codigo(caminho="npc/ferreiro.lua")',
        ))
        
        tools.append(Tool(
            nome="analisar_bug",
            descricao="Analisa e diagnostica bugs em tempo de execucao",
            categoria="analise",
            comandos=["cmd_bugfinder"],
            modulos=["diagnostico", "ia"],
            parametros=[
                Parametro("descricao", "string", "Descricao do bug ou sintoma"),
                Parametro("arquivos", "list", "Arquivos relevantes", obrigatorio=False),
            ],
            saida="diagnostico com causa raiz e sugestao de correcao",
            fontes=["codigo_fonte", "kg", "llm"],
            requisitos=["ollama_rodando"],
            confianca_padrao=0.75,
            palavras_chave=["bug", "erro", "problema", "falha", "crash", "exception"],
            exemplo_uso='analisar_bug(descricao="NPC nao abre loja")',
        ))
        
        tools.append(Tool(
            nome="analisar_projeto",
            descricao="Analisa estrutura geral do projeto, metricas e saude",
            categoria="analise",
            comandos=["cmd_system_scan"],
            modulos=["diagnostico"],
            parametros=[
                Parametro("escopo", "string", "geral/codigo/dependencias", obrigatorio=False, default="geral"),
            ],
            saida="relatorio com metricas do projeto",
            fontes=["codigo_fonte"],
            requisitos=[],
            confianca_padrao=0.95,
            palavras_chave=["projeto", "estrutura", "metricas", "scan", "mapear"],
            exemplo_uso='analisar_projeto(escopo="geral")',
        ))
        
        # ================================================================
        # GERAÇÃO
        # ================================================================
        tools.append(Tool(
            nome="gerar_npc",
            descricao="Gera script Lua de NPC para Canary usando templates + estrategias de preenchimento",
            categoria="geracao",
            comandos=["cmd_gerar_npc"],
            modulos=["npc_generator", "agent_loop", "canary_indexer", "lua_validator"],
            parametros=[
                Parametro("descricao", "string", "Descricao do NPC desejado"),
                Parametro("tipo", "string", "shop/quest/bank/gate/trainer/dialogue", obrigatorio=False, default="shop"),
            ],
            saida="arquivo .lua com NPC completo e validado",
            fontes=["canary_indexer", "items_xml", "kg", "web", "llm"],
            requisitos=[],
            confianca_padrao=0.95,
            palavras_chave=["npc", "criar", "gerar", "personagem", "lua", "script"],
            exemplo_uso='gerar_npc(descricao="Ferreiro em Eridanus", tipo="shop")',
        ))
        
        tools.append(Tool(
            nome="gerar_codigo",
            descricao="Gera codigo a partir de template + placeholders preenchidos",
            categoria="geracao",
            comandos=["cmd_gerar", "cmd_gerar_componentes"],
            modulos=["npc_generator", "ia"],
            parametros=[
                Parametro("template", "string", "Nome do template ou caminho"),
                Parametro("placeholders", "dict", "Dicionario com valores para preencher"),
            ],
            saida="codigo gerado",
            fontes=["llm", "templates"],
            requisitos=["ollama_rodando"],
            confianca_padrao=0.70,
            palavras_chave=["gerar", "criar", "codigo", "template"],
            exemplo_uso='gerar_codigo(template="npc_shop", placeholders={"nome": "Joao"})',
        ))
        
        tools.append(Tool(
            nome="gerar_conceito",
            descricao="Aprende e registra um conceito do codigo fonte no KG",
            categoria="geracao",
            comandos=["cmd_aprender_conceito"],
            modulos=["ia", "kg"],
            parametros=[
                Parametro("conceito", "string", "Nome do conceito para aprender"),
            ],
            saida="licao registrada no KG",
            fontes=["codigo_fonte", "llm", "kg"],
            requisitos=["ollama_rodando"],
            confianca_padrao=0.80,
            palavras_chave=["aprender", "conceito", "ensinar", "kg"],
            exemplo_uso='gerar_conceito(conceito="SHC")',
        ))
        
        # ================================================================
        # WEB
        # ================================================================
        tools.append(Tool(
            nome="pesquisar_web",
            descricao="Pesquisa informacao atualizada na web e salva no KG",
            categoria="web",
            comandos=["cmd_weblearn"],
            modulos=["ia"],
            parametros=[
                Parametro("query", "string", "Termo de busca"),
            ],
            saida="resultado da pesquisa sintetizado",
            fontes=["web"],
            requisitos=["internet"],
            confianca_padrao=0.70,
            palavras_chave=["web", "pesquisar", "google", "buscar", "internet", "aprender"],
            exemplo_uso='pesquisar_web(query="Tibia fire sword clientId")',
        ))
        
        tools.append(Tool(
            nome="buscar_url",
            descricao="Faz fetch de uma URL especifica e retorna conteudo",
            categoria="web",
            comandos=["cmd_webfetch"],
            modulos=[],
            parametros=[
                Parametro("url", "string", "URL completa para buscar"),
                Parametro("formato", "string", "markdown/text/html", obrigatorio=False, default="markdown"),
            ],
            saida="conteudo da URL no formato solicitado",
            fontes=["web"],
            requisitos=["internet"],
            confianca_padrao=0.80,
            palavras_chave=["url", "fetch", "baixar", "pagina", "site"],
            exemplo_uso='buscar_url(url="https://tibia.fandom.com/wiki/Fire_Sword")',
        ))
        
        # ================================================================
        # VALIDAÇÃO
        # ================================================================
        tools.append(Tool(
            nome="validar_lua",
            descricao="Valida script Lua do Canary (sintaxe, SQL injection, boas praticas, estrutura)",
            categoria="validacao",
            comandos=["cmd_gerar_npc", "cmd_revisar"],
            modulos=["lua_validator"],
            parametros=[
                Parametro("codigo", "string", "Codigo Lua para validar"),
            ],
            saida="resultado da validacao com erros/avisos",
            fontes=["lua_validator"],
            requisitos=[],
            confianca_padrao=0.95,
            palavras_chave=["validar", "lua", "sintaxe", "sql", "injection"],
            exemplo_uso='validar_lua(codigo="...")',
        ))
        
        tools.append(Tool(
            nome="validar_projeto",
            descricao="Valida estrutura e consistencia do projeto",
            categoria="validacao",
            comandos=["cmd_revisar_docs"],
            modulos=["auto_revisor"],
            parametros=[
                Parametro("escopo", "string", "docs/codigo/tudo", obrigatorio=False, default="tudo"),
            ],
            saida="relatorio de validacao",
            fontes=["codigo_fonte", "documentacao"],
            requisitos=[],
            confianca_padrao=0.85,
            palavras_chave=["validar", "revisar", "docs", "documentacao"],
            exemplo_uso='validar_projeto(escopo="docs")',
        ))
        
        # ================================================================
        # PERGUNTA / RESPOSTA
        # ================================================================
        tools.append(Tool(
            nome="perguntar",
            descricao="Responde perguntas gerais ou especificas do MCR usando pipeline completo",
            categoria="analise",
            comandos=["cmd_perguntar"],
            modulos=["orquestrador", "pipeline_executor", "mente", "conselho", "ia", "kg"],
            parametros=[
                Parametro("pergunta", "string", "Pergunta do usuario"),
            ],
            saida="resposta completa e contextualizada",
            fontes=["kg", "codigo_fonte", "documentacao", "web", "llm"],
            requisitos=["ollama_rodando"],
            confianca_padrao=0.85,
            palavras_chave=["perguntar", "o que", "como", "por que", "explique"],
            exemplo_uso='perguntar(pergunta="O que e SPA?")',
        ))
        
        # ================================================================
        # SISTEMA / EXECUÇÃO
        # ================================================================
        tools.append(Tool(
            nome="autoteste",
            descricao="Executa auto-teste do MCR-DevIA com geracao de perguntas, pipeline e avaliacao",
            categoria="sistema",
            comandos=["cmd_autoteste"],
            modulos=["pipeline_executor", "ia", "progress_tracker"],
            parametros=[
                Parametro("ciclo", "int", "Numero do ciclo", obrigatorio=False, default=1),
                Parametro("fast", "bool", "Skip ToT", obrigatorio=False, default=False),
                Parametro("paralelo", "bool", "Execucao paralela", obrigatorio=False, default=False),
            ],
            saida="relatorio do autoteste",
            fontes=["sistema"],
            requisitos=["ollama_rodando"],
            confianca_padrao=0.90,
            palavras_chave=["teste", "autoteste", "avaliar", "testar", "ciclo"],
            exemplo_uso='autoteste(ciclo=1, fast=True)',
        ))
        
        tools.append(Tool(
            nome="compilar",
            descricao="Compila projetos do servidor (Canary, OTClient)",
            categoria="sistema",
            comandos=["cmd_compilar", "cmd_build"],
            modulos=["compilador"],
            parametros=[
                Parametro("projeto", "string", "canary/otclient/ambos", obrigatorio=False, default="canary"),
                Parametro("config", "string", "Debug/Release", obrigatorio=False, default="Release"),
            ],
            saida="log da compilacao",
            fontes=["sistema"],
            requisitos=["msbuild_disponivel"],
            confianca_padrao=0.85,
            palavras_chave=["compilar", "build", "compilacao", "canary", "otclient"],
            exemplo_uso='compilar(projeto="canary", config="Release")',
        ))
        
        tools.append(Tool(
            nome="status_sistema",
            descricao="Mostra estado atual do MCR-DevIA, processos, recursos",
            categoria="sistema",
            comandos=["cmd_status"],
            modulos=["watchdog"],
            parametros=[],
            saida="status detalhado do sistema",
            fontes=["sistema"],
            requisitos=[],
            confianca_padrao=1.0,
            palavras_chave=["status", "estado", "saude", "processos"],
            exemplo_uso='status_sistema()',
        ))
        
        # ================================================================
        # APRENDIZADO
        # ================================================================
        tools.append(Tool(
            nome="ensinar_kg",
            descricao="Regista uma licao no Knowledge Graph",
            categoria="aprendizado",
            comandos=["cmd_ensinar"],
            modulos=["kg"],
            parametros=[
                Parametro("oque", "string", "O que foi aprendido"),
                Parametro("contexto", "string", "Contexto do aprendizado"),
                Parametro("solucao", "string", "Solucao ou detalhes"),
                Parametro("categoria", "string", "Categoria para organizacao", obrigatorio=False, default="geral"),
            ],
            saida="licao registrada",
            fontes=["kg"],
            requisitos=[],
            confianca_padrao=1.0,
            palavras_chave=["ensinar", "aprender", "kg", "registrar", "licao"],
            exemplo_uso='ensinar_kg(oque="SQL injection detectado", contexto="NPC oraculo", solucao="Usar db.storeQuery")',
        ))
        
        tools.append(Tool(
            nome="aprender_conceito",
            descricao="Escaneia codigo fonte e sintetiza conhecimento conceitual no KG",
            categoria="aprendizado",
            comandos=["cmd_aprender_conceito"],
            modulos=["ia", "kg"],
            parametros=[
                Parametro("conceito", "string", "Conceito para aprender"),
            ],
            saida="conceito aprendido e registrado",
            fontes=["codigo_fonte", "kg", "llm"],
            requisitos=["ollama_rodando"],
            confianca_padrao=0.80,
            palavras_chave=["aprender", "conceito", "escaneiar", "codigo"],
            exemplo_uso='aprender_conceito(conceito="SPA")',
        ))
        
        # ================================================================
        # META
        # ================================================================
        tools.append(Tool(
            nome="meta_listar_ferramentas",
            descricao="Lista todas as ferramentas disponiveis no sistema",
            categoria="meta",
            comandos=["cmd_system"],
            modulos=[],
            parametros=[
                Parametro("categoria", "string", "Filtrar por categoria", obrigatorio=False),
                Parametro("busca", "string", "Buscar por nome/descricao", obrigatorio=False),
            ],
            saida="lista de ferramentas",
            fontes=[],
            requisitos=[],
            confianca_padrao=1.0,
            palavras_chave=["ferramentas", "capacidades", "o que sabe", "ajuda"],
            exemplo_uso='meta_listar_ferramentas(categoria="busca")',
        ))
        
        tools.append(Tool(
            nome="meta_planejar",
            descricao="Planeja como executar uma tarefa, mostrando etapas e lacunas",
            categoria="meta",
            comandos=["cmd_plan", "cmd_estrategia"],
            modulos=["engine.planner"],
            parametros=[
                Parametro("descricao", "string", "Descricao da tarefa"),
            ],
            saida="plano de acao com etapas",
            fontes=[],
            requisitos=[],
            confianca_padrao=0.90,
            palavras_chave=["planejar", "plano", "estratégia", "como fazer"],
            exemplo_uso='meta_planejar(descricao="criar um ferreiro")',
        ))
        
        # ================================================================
        # NOVAS FERRAMENTAS (a serem implementadas)
        # ================================================================
        tools.append(Tool(
            nome="criar_universal",
            descricao="Ponto de entrada universal para QUALQUER criacao (NPC, site, app, script, etc)",
            categoria="geracao",
            comandos=["cmd_criar", "cmd_fazer"],  # A criar
            modulos=["engine.meta_creator"],
            parametros=[
                Parametro("descricao", "string", "Descricao do que criar"),
            ],
            saida="resultado da criacao (arquivo, codigo, etc)",
            fontes=["tudo"],  # Usa todas as fontes disponiveis
            requisitos=[],
            confianca_padrao=0.85,
            palavras_chave=["criar", "fazer", "gerar", "produzir", "desenvolver"],
            exemplo_uso='criar_universal(descricao="um ferreiro em Eridanus")',
            ativa=False,  # Ainda nao implementado
        ))
        
        # ================================================================
        # Indexar por nome
        # ================================================================
        for tool in tools:
            self._ferramentas[tool.nome] = tool
    
    # ================================================================
    # API PUBLICA
    # ================================================================
    
    def listar(self, categoria: Optional[str] = None, busca: Optional[str] = None) -> List[Tool]:
        """Lista ferramentas com filtros opcionais."""
        resultados = list(self._ferramentas.values())
        
        if categoria:
            resultados = [t for t in resultados if t.categoria == categoria]
        
        if busca:
            busca_lower = busca.lower()
            resultados = [
                t for t in resultados 
                if busca_lower in t.nome.lower() or busca_lower in t.descricao.lower()
            ]
        
        return resultados
    
    def get(self, nome: str) -> Optional[Tool]:
        """Obtem ferramenta por nome."""
        return self._ferramentas.get(nome)
    
    def buscar_por_palavras_chave(self, texto: str) -> List[Tool]:
        """Busca ferramentas relevantes para um texto descritivo."""
        texto_lower = texto.lower()
        palavras = set(re.findall(r'\b[a-zà-ú]{3,}\b', texto_lower))
        
        scores = []
        for tool in self._ferramentas.values():
            if not tool.ativa:
                continue
            score = 0
            
            # Match por palavra-chave
            for kw in tool.palavras_chave:
                if kw.lower() in texto_lower:
                    score += 10
                if any(p in kw.lower() for p in palavras):
                    score += 5
            
            # Match por nome
            if tool.nome.lower() in texto_lower:
                score += 15
            
            # Match por descricao
            for p in palavras:
                if p in tool.descricao.lower():
                    score += 3
            
            if score > 0:
                scores.append((score, tool))
        
        scores.sort(key=lambda x: -x[0])
        return [t for _, t in scores[:10]]
    
    def buscar_por_categoria_e_tipo(self, categoria: str, texto: str) -> List[Tool]:
        """Filtra por categoria + relevancia textual."""
        tools = self.listar(categoria=categoria)
        texto_lower = texto.lower()
        
        scores = []
        for tool in tools:
            score = 0
            for kw in tool.palavras_chave:
                if kw.lower() in texto_lower:
                    score += 5
            if score > 0:
                scores.append((score, tool))
        
        scores.sort(key=lambda x: -x[0])
        return [t for _, t in scores[:5]]
    
    def categorias(self) -> Dict[str, int]:
        """Retorna todas as categorias com contagem."""
        cats = {}
        for t in self._ferramentas.values():
            cats[t.categoria] = cats.get(t.categoria, 0) + 1
        return cats
    
    def estatisticas(self) -> Dict:
        """Estatisticas do registry."""
        return {
            'total': len(self._ferramentas),
            'ativas': sum(1 for t in self._ferramentas.values() if t.ativa),
            'categorias': self.categorias(),
            'ferramentas_por_categoria': {
                cat: [t.nome for t in self._ferramentas.values() if t.categoria == cat]
                for cat in set(t.categoria for t in self._ferramentas.values())
            }
        }


# ============================================================
# SINGLETON
# ============================================================

_registry_instance: Optional[ToolRegistry] = None

def get_registry() -> ToolRegistry:
    """Retorna instancia unica do ToolRegistry."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance


# ============================================================
# TESTE
# ============================================================

if __name__ == '__main__':
    reg = get_registry()
    print("=== TOOL REGISTRY ===")
    print("Total:", reg.estatisticas()['total'], "ferramentas")
    print("Ativas:", reg.estatisticas()['ativas'])
    print("\nCategorias:")
    for cat, qtd in reg.categorias().items():
        print(f"  {cat}: {qtd}")
    
    print("\n--- Busca: 'ferreiro' ---")
    for t in reg.buscar_por_palavras_chave("ferreiro"):
        print(f"  {t.nome} ({t.categoria}) - {t.confianca_padrao}")
    
    print("\n--- Busca: 'analisar codigo' ---")
    for t in reg.buscar_por_palavras_chave("analisar codigo bug"):
        print(f"  {t.nome} ({t.categoria}) - {t.descricao[:60]}")
