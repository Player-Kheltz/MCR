"""Toolkit MCR-DevIA - Inventario completo de ferramentas.
Gera contexto sobre todas as capacidades para injetar nos prompts."""
import os, json

TOOLKIT = {
    "comandos": {
        "status": "Metricas do KG (licoes, versoes, geracoes)",
        "perguntar": "V12 Contexto Agregado: responde perguntas factuais usando KG + Fast expand",
        "conselho": "Conselho V8: resposta inteligente com 4 personalidades + auto-revisao + honorarios",
        "grep": "Busca texto em arquivos (--literal, --max, --ctx, --type)",
        "read": "Le arquivo com offset/limit (--offset N, --limit N)",
        "edit": "Edita linha especifica de arquivo (path, linha, novo_conteudo)",
        "write": "Escreve conteudo em arquivo (path, conteudo)",
        "patch": "Edita funcao com IA (identifica funcao e substitui)",
        "glob": "Busca arquivos por nome (auto-adiciona * se sem wildcard)",
        "build": "Cria codigo via Pipeline Dinamica (fragmentos sob medida)",
        "fast": "Classificacao rapida IA (SIM/NAO, extracoes, temperaturas modulares)",
        "ensinar": "Registra aprendizado no KG (erro, causa, solucao, ctx)",
        "aprender_conceito": "Le codigo fonte, IA extrai conhecimento conceitual e salva no KG",
        "memoria": "Consulta historico de comandos (--stats, --timeline, --cmd X)",
        "pensar": "Documenta raciocinio do usuario no .mcr_conversa.jsonl",
        "explorar": "Escaneia docs/codigo/web, IA interpreta, buffer detecta contradicoes, comita no KG",
        "fix_excepts": "Corrige except: genericos para except Exception as e: em scripts",
        "gerar_componentes": "Pre-gera personagens, locais, artefatos para historias (salva no KG)",
        "revisar_docs": "Verifica se AGENTS.md e docs/rules estao sincronizados com o codigo real",
        "webfetch": "Busca conteudo de uma URL (para pesquisar/referenciar)",
        "analisar": "Analisa codigo com IA (AST + funcoes + chamadas)",
        "extract": "Extrai dados de XML, JSON, CSV, Lua, C++",
        "plan": "Planejamento multi-abordagem com riscos",
        "debate": "2 sub-agentes discutem topicos",
        "loop": "Loop OODA continuo com auto-diagnostico",
        "intencao": "Interpreta intencao real do usuario",
        "processar": "Processa entrada via pipeline (fragmenta + IA + monta)",
        "compilar": "Compila Canary (VS2022) ou OTClient (VS2026)",
        "system": "Info de CPU, RAM, GPU, processos",
        "system_scan": "Escaneia linguagens/bibliotecas instaladas",
        "bugfinder": "Escaneia logs e registra erros no KG",
        "review": "Revisa dados extraidos item por item",
        "revisar": "Revisor por pares: valida mudancas",
        "question": "Pergunta algo ao usuario e aguarda resposta",
        "task": "Delega execucao para scripts do sandbox",
        "todo": "Gerenciador de tarefas",
        "gerar": "Gera NPC, monster, quest, item, spell para o jogo",
        "lore": "Gera lore de RPG",
        "conectar": "Busca conexoes entre dominios no KG",
        "estrategia": "Estrategista: planeja e executa",
        "builderx": "Builder por blocos",
        "proativo": "Modo proativo",
        "refresh": "Recarrega todos os comandos (hot-reload)",
    },
    "modulos": {
        "kg": "Knowledge Graph: armazena e busca lessons (ctx=identidade=1.0, conceito_codigo=0.9, etc)",
        "ia": "Interface Ollama: fast() para rapido, gerar() para completo, modelos configuraveis",
        "supervisor": "V12: classifica pergunta + busca KG + Fast expand",
        "conselho": "V8: 4 fixos (analista, critico, estrategista, arquiteto) + psicologo + honorarios sob demanda + auto-revisao",
        "memoria": "Memoria fragmentada por dia, compactada gzip, NUNCA deletada, consulta por --stats",
        "dashboard": "Interface web http://localhost:8765 com chat + status em tempo real",
        "diagnostico": "Auto-diagnostico: KG, codigo, performance, sandbox",
        "fragmentador": "Gera codigo sob medida com fragmentos sob demanda (0 IA para estimar)",
        "watchdog": "Monitora comandos/ reativamente (só acorda quando o diretorio muda)",
        "serve": "Modo servidor persistente",
        "compilador": "Compilacao VS2022 (Canary) e VS2026 (OTClient)",
        "pipeline": "Pipeline inteligente: classifica pergunta -> 5 tipos de pipeline -> contexto flutuante -> expansao",
        "lessons_buffer": "Buffer de conhecimento: detecta contradicoes, IA resolve, so comita verdade no KG",
        "toolkit": "Este inventario de ferramentas",
    },
    "personalidades": {
        "analista": "Fixo - Dados, metricas, fatos, analise logica",
        "critico": "Fixo - Riscos, falhas, pontos cegos, seguranca",
        "estrategista": "Fixo - Planejamento curto/medio/longo prazo, acoes concretas",
        "arquiteto": "Fixo - Arquitetura, design, tecnologias, metricas",
        "psicologo": "Psicologo do conselho - Monitora saude mental, vies, alinhamento (nao responde a pergunta)",
        "contadordehistorias": "Honorario - Lore, narrativa, criatividade, worldbuilding",
        "seletor": "Seleciona personalidades por topico (lore/codigo/arquitetura/estrategia/factual)",
    },
    "fontes_contexto": {
        "KG": "Knowledge Graph - lessons curadas (confianca por ctx: identidade=1.0, conceito_codigo=0.9, etc)",
        "WebLearn": "1084+ fragmentos de web aprendidos",
        "Docs": "Arquivos .md em docs/ - documentacao do projeto",
        "Codigo": "Grep no src/ do Canary + scripts/ - codigo fonte real",
        "Web": "Wikipedia e outras fontes via API (LGPD safe, sem dados pessoais)",
    },
    "modelos_ia": {
        "qwen2.5-coder:7b": "Padrao - codigo e tarefas tecnicas (disponivel local)",
        "llama3.1:8b": "Opcional - texto PT-BR e criatividade (ollama pull, ~4.7GB)",
        "mistral:7b": "Opcional - equilibrio geral (ollama pull, ~4.1GB)",
    },
}

def gerar_contexto():
    """Gera texto de contexto completo sobre o toolkit do MCR-DevIA."""
    texto = "=== TOOLKIT MCR-DEVIA ===\n\n"
    
    texto += "--- COMANDOS DISPONIVEIS ---\n"
    for nome, desc in sorted(TOOLKIT['comandos'].items()):
        texto += f"  {nome}: {desc}\n"
    
    texto += "\n--- MODULOS DISPONIVEIS ---\n"
    for nome, desc in sorted(TOOLKIT['modulos'].items()):
        texto += f"  {nome}: {desc}\n"
    
    texto += "\n--- PERSONALIDADES DO CONSELHO ---\n"
    for nome, desc in sorted(TOOLKIT['personalidades'].items()):
        texto += f"  {nome}: {desc}\n"
    
    texto += "\n--- FONTES DE CONTEXTO (ContextCrew) ---\n"
    for nome, desc in sorted(TOOLKIT['fontes_contexto'].items()):
        texto += f"  {nome}: {desc}\n"
    
    texto += "\n--- MODELOS IA DISPONIVEIS ---\n"
    for nome, desc in sorted(TOOLKIT['modelos_ia'].items()):
        texto += f"  {nome}: {desc}\n"
    
    return texto

def resumo_rapido():
    """Resumo de uma linha para injetar em prompts."""
    return (f"MCR-DevIA tem {len(TOOLKIT['comandos'])} comandos, "
            f"{len(TOOLKIT['modulos'])} modulos, "
            f"{len(TOOLKIT['personalidades'])} personalidades, "
            f"e busca contexto em {len(TOOLKIT['fontes_contexto'])} fontes. "
            f"Modelos: {', '.join(TOOLKIT['modelos_ia'].keys())}.")
