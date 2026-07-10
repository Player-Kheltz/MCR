#!/usr/bin/env python3
"""
PipelineExecutor — conecta comandos em pipeline.

Cada comando no pipeline:
1. Recebe dados do contexto (dict compartilhado)
2. Executa (se for cmd_*, redireciona stdout)
3. Parseia saída
4. Escreve resultado no contexto para o próximo comando

Pipeline típica:
  cmd_grep → cmd_read → template_extractor → deterministic_filler → llm_gerar → cmd_write
"""
import sys, os, io, re, json
from typing import List, Dict, Any, Callable, Optional

# Mapa de handlers para comandos que NÃO são cmd_* (são funções Python)
HANDLERS_INTERNOS = {}

# MarkovDecider como classificador padrao (fallback quando nao ha LLM)
_MARKOV_DECIDER = None


def _get_markov_decider():
    """Retorna instancia global do MarkovDecider (lazy, criado sob demanda)."""
    global _MARKOV_DECIDER
    if _MARKOV_DECIDER is None:
        try:
            from mcr_devia_v2 import MarkovDecider
            _MARKOV_DECIDER = MarkovDecider()
        except Exception:
            _MARKOV_DECIDER = None
    return _MARKOV_DECIDER


def registrar_handler(nome: str, func: Callable):
    """Registra handler para comando interno (ex: template_extractor)."""
    HANDLERS_INTERNOS[nome] = func


# ─── Post-processamento de respostas LLM ───────────────────────

def _dedup_resposta(resposta: str) -> str:
    """Remove duplicatas da resposta do LLM por fingerprint similarity.
    
    Se dois paragrafos tem similaridade cosseno > 0.7, o segundo e removido.
    """
    if not resposta or len(resposta) < 100:
        return resposta
    
    try:
        from MCR import MCRByteUtils
    except:
        return resposta
    
    paragrafos = [p.strip() for p in resposta.split('\n') if p.strip() and len(p.strip()) > 10]
    if len(paragrafos) < 3:
        return resposta
    
    unicos = [paragrafos[0]]
    fps = [MCRByteUtils.fingerprint(paragrafos[0], 8)]
    
    for p in paragrafos[1:]:
        fp = MCRByteUtils.fingerprint(p, 8)
        dup = False
        for fp_existente in fps:
            sim = MCRByteUtils.similaridade_cosseno(fp, fp_existente)
            if sim > 0.85:
                dup = True
                break
        if not dup:
            unicos.append(p)
            fps.append(fp)
    
    removidos = len(paragrafos) - len(unicos)
    if removidos > 0:
        return '\n'.join(unicos) + f"\n\n[post-process: {removidos} duplicatas removidas]"
    return resposta


# ─── PipelineExecutor ──────────────────────────────────────────

class CommandCapture:
    """Captura stdout durante execução de uma função."""
    
    def __init__(self):
        self.texto = ""
        self.linhas = []
    
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._buffer = io.StringIO()
        sys.stdout = self._buffer
        return self
    
    def __exit__(self, *args):
        sys.stdout = self._original_stdout
        self.texto = self._buffer.getvalue()
        self.linhas = [l for l in self.texto.split('\n') if l]
    
    def extrair_caminhos(self) -> List[str]:
        """Extrai caminhos de arquivo do stdout (ex: saida do grep)."""
        caminhos = []
        for linha in self.linhas:
            # Padrões comuns: "  src/main.cpp:L42: text", "  data/file.lua:L10:"
            m = re.search(r'([\w/\\\-]+\.\w+)(?::L?\d+)?', linha)
            if m:
                p = m.group(1)
                if p not in caminhos:
                    caminhos.append(p)
        return caminhos
    
    def extrair_primeiro_caminho(self) -> Optional[str]:
        caminhos = self.extrair_caminhos()
        return caminhos[0] if caminhos else None
    
    def extrair_conteudo(self) -> str:
        """Extrai o texto principal (ex: saida do read)."""
        # Remove linhas de cabecalho [Read] e pega o resto
        linhas_uteis = []
        for linha in self.linhas:
            if 'L' in linha and ':' in linha:
                # Linha de conteudo: "  L42: texto aqui"
                partes = linha.split(':', 1)
                if len(partes) == 2 and partes[0].strip().startswith('L'):
                    linhas_uteis.append(partes[1])
                else:
                    linhas_uteis.append(linha)
            elif not linha.startswith('[') and linha.strip():
                linhas_uteis.append(linha)
        return '\n'.join(linhas_uteis)


class PipelineExecutor:
    """Executa pipeline de comandos com captura e passagem de contexto."""
    
    def __init__(self, kernel=None):
        self.kernel = kernel  # MCRKernel com comandos carregados
        self.capture = CommandCapture()
        self.ultimo_stdout = ""
    
    def executar(self, pipeline: List[str], entrada: str = "", contexto: Dict = None) -> Dict:
        """Executa pipeline completa.
        
        Args:
            pipeline: lista de nomes de comando (ex: ["cmd_grep", "cmd_read", "llm_gerar"])
            entrada: pergunta/texto original do usuário
            contexto: dict compartilhado entre comandos
            
        Returns:
            Dict com resultados
        """
        if contexto is None:
            contexto = {
                "entrada": entrada,
                "stdout": "",
                "caminhos": [],
                "conteudo": "",
                "template": "",
                "gaps": [],
                "preenchido": "",
                "gaps_restantes": [],
                "llm_output": "",
                "saida_path": "",
                "erro": None,
            }
        
        for comando in pipeline:
            if contexto.get("erro"):
                break
            
            try:
                self._executar_comando(comando, contexto)
            except Exception as e:
                contexto["erro"] = str(e)
                break
        
        return contexto
    
    def _executar_comando(self, comando: str, ctx: Dict):
        """Executa um comando individual, atualizando o contexto."""
        
        # ─── Comandos internos (Python, sem kernel) ───────────
        if comando == "template_extractor":
            from TemplateExtractor import extrair_template
            conteudo = ctx.get("conteudo", "")
            if conteudo:
                template, gaps = extrair_template(conteudo)
                ctx["template"] = template
                ctx["gaps"] = gaps
        
        elif comando == "deterministic_filler":
            from DeterministicFiller import preencher_template, gaps_restantes
            template = ctx.get("template", "")
            task = ctx.get("task", {})
            if template:
                preenchido = preencher_template(template, task)
                restantes = gaps_restantes(preenchido)
                ctx["preenchido"] = preenchido
                ctx["gaps_restantes"] = restantes
        
        elif comando == "context_crew":
            # Contexto ja foi carregado pelo ContextCrew do MCR.py no init
            pass
        
        elif comando == "code_analyzer":
            from code_analyzer import analisar_no_pipeline
            resultado = analisar_no_pipeline(ctx)
            ctx["code_analyzer_output"] = resultado
        
        elif comando == "code_parser":
            try:
                from code_parser import get_parser
                parser = get_parser()
                caminhos = ctx.get("caminhos", [])
                if caminhos:
                    resultado = parser.parse(caminhos[0])
                    ctx["parsed_code"] = resultado
            except:
                pass
        
        elif comando == "pos_processamento":
            """Extrai blocos ```lua de respostas e salva em scripts/generated/."""
            resposta = ctx.get("llm_output", "")
            classe = getattr(self, '_classe', '')
            if resposta and classe and any(c in classe for c in ["npc", "quest", "codigo", "habilidade", "spa", "monster", "sistema"]):
                try:
                    import re
                    _ENCODING_LUA = 'latin-1'
                    
                    # PARSER UNICO: --- ARQUIVO: nome.lua --- seguido de ```lua ... ```
                    _PARSER = r'---\s*ARQUIVO:\s*(\S+\.lua)\s*---\s*\n?```lua\n(.*?)```'
                    matches = re.findall(_PARSER, resposta, re.DOTALL)
                    
                    from encoding import escrever_lua
                    arquivos_salvos = []
                    
                    if matches:
                        for nome_arq, conteudo in matches:
                            conteudo_limpo = re.sub(r'^```lua\s*\n?', '', conteudo.strip())
                            conteudo_limpo = re.sub(r'\n?```\s*$', '', conteudo_limpo).strip()
                            if conteudo_limpo:
                                caminho = os.path.join(
                                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    "..", "Projeto MCR", "scripts", "generated", nome_arq)
                                os.makedirs(os.path.dirname(caminho), exist_ok=True)
                                escrever_lua(caminho, conteudo_limpo)
                                arquivos_salvos.append(caminho)
                    else:
                        # Fallback: extrai blocos ```lua sem ARQUIVO: e salva como parte_N.lua
                        blocos = re.findall(r'```lua\s*\n(.*?)```', resposta, re.DOTALL)
                        if blocos:
                            for idx, bloco in enumerate(blocos):
                                conteudo_limpo = bloco.strip()
                                # Remove linhas de cabecalho ARQUIVO: dentro do bloco
                                conteudo_limpo = re.sub(r'^---\s*ARQUIVO:\s*\S+\.lua\s*---\s*\n?', '', conteudo_limpo)
                                if conteudo_limpo:
                                    nome_auto = "%s_parte_%d.lua" % (classe.replace('criar_', ''), idx + 1)
                                    caminho = os.path.join(
                                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                        "..", "Projeto MCR", "scripts", "generated", nome_auto)
                                    os.makedirs(os.path.dirname(caminho), exist_ok=True)
                                    escrever_lua(caminho, conteudo_limpo)
                                    arquivos_salvos.append(caminho)
                        else:
                            raise ValueError("Nenhum bloco ```lua encontrado")
                    
                    ctx["arquivos_salvos"] = arquivos_salvos
                    print(f'[PosProcess] {len(arquivos_salvos)} arquivos: {[os.path.basename(a) for a in arquivos_salvos]}')
                    
                    # Quarentena se validacao estrutural falhou
                    if not ctx.get("sintaxe_valida", True) and arquivos_salvos:
                        _BASE_Q = os.path.join(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "..", "Projeto MCR", "scripts", "quarantine")
                        _erros_ctx = ctx.get("sintaxe_erro", [])
                        for _arq in arquivos_salvos:
                            _nome_fail = os.path.basename(_arq).replace('.lua', '_FAILED.lua')
                            _dest = os.path.join(_BASE_Q, _nome_fail)
                            os.makedirs(_BASE_Q, exist_ok=True)
                            try:
                                with open(_arq, 'r', encoding='latin-1') as _f:
                                    _conteudo = _f.read()
                                _cabecalho = "-- QUARENTENA: validacao estrutural falhou\n-- Erros: %s\n\n" % str(_erros_ctx[:3])
                                with open(_dest, 'w', encoding='latin-1') as _f:
                                    _f.write(_cabecalho + _conteudo)
                                os.remove(_arq)
                                print('[Quarentena] %s movido para quarantine/' % _nome_fail)
                            except: pass
                        try:
                            if hasattr(self, '_cerebro') and self._cerebro and hasattr(self._cerebro, 'kg'):
                                _kg = self._cerebro.kg
                                _err = str(_erros_ctx[0])[:100] if _erros_ctx else "Validacao falhou"
                                _sol = "Arquivo movido para quarantine"
                                if hasattr(_kg, 'aprender'):
                                    import inspect
                                    _n_params = len(inspect.signature(_kg.aprender).parameters)
                                    if _n_params >= 4:
                                        _kg.aprender(erro=_err, causa="LLM gerou %s" % classe, solucao=_sol, ctx=classe)
                                    else:
                                        _kg.aprender(_err, _sol, classe)
                        except: pass
                    elif ctx.get("sintaxe_valida", True) and arquivos_salvos:
                        try:
                            if hasattr(self, '_cerebro') and self._cerebro and hasattr(self._cerebro, 'kg'):
                                _kg = self._cerebro.kg
                                if hasattr(_kg, 'aprender'):
                                    import inspect
                                    _n_params = len(inspect.signature(_kg.aprender).parameters)
                                    if _n_params >= 4:
                                        _kg.aprender(erro="", causa="Geracao bem-sucedida de %s" % classe,
                                                     solucao="Arquivos salvos em generated/", ctx=classe)
                                    else:
                                        _kg.aprender("OK: %s" % classe, "Arquivos salvos em generated/", classe)
                        except: pass
                
                except Exception as e:
                    # Loop de auto-correcao: tenta fazer o LLM corrigir o formato
                    erro_msg = str(e)
                    if llm := getattr(self, '_llm', None):
                        prompt_formato = (
                            f"ERRO DE FORMATACAO: {erro_msg}\n\n"
                            f"O codigo gerado NAO seguiu o formato obrigatorio.\n"
                            f"Regra ABSOLUTA: --- ARQUIVO: nome_do_arquivo.lua --- DEVE estar FORA do ```lua.\n"
                            f"NUNCA coloque o ARQUIVO dentro do bloco ```lua.\n"
                            f"NUNCA use 'exemplo.lua' como nome de arquivo — use nomes descritivos.\n"
                            f"\n"
                            f"Formato correto (use nomes REAIS, nao 'exemplo'):\n"
                            f"--- ARQUIVO: nome_da_skill.lua ---\n"
                            f"```lua\n"
                            f"codigo aqui\n"
                            f"```\n"
                            f"\n"
                            f"=== CODIGO ATUAL COM ERRO ===\n{resposta[:2000]}\n=== FIM ===\n\n"
                            f"Reescreva usando o formato correto com nomes descritivos.\n"
                        )
                        correcao = llm.gerar(prompt_formato, modelo='qwen2.5-coder:7b')
                        # Tenta extrair com o mesmo parser unico
                        _PARSER_CORRECAO = r'---\s*ARQUIVO:\s*(\S+\.lua)\s*---\s*\n?```lua\n(.*?)```'
                        matches = re.findall(_PARSER_CORRECAO, correcao, re.DOTALL)
                        if matches:
                            arquivos_salvos = []
                            from encoding import escrever_lua
                            _BASE_GEN = os.path.join(
                                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "..", "Projeto MCR", "scripts", "generated")
                            for nome_arq, conteudo in matches:
                                conteudo_limpo = re.sub(r'^```lua\s*\n?', '', conteudo.strip())
                                conteudo_limpo = re.sub(r'\n?```\s*$', '', conteudo_limpo).strip()
                                if conteudo_limpo:
                                    caminho = os.path.join(_BASE_GEN, nome_arq)
                                    os.makedirs(os.path.dirname(caminho), exist_ok=True)
                                    escrever_lua(caminho, conteudo_limpo)
                                    arquivos_salvos.append(caminho)
                            ctx["arquivos_salvos"] = arquivos_salvos
                            print(f'[PosProcess] Corrigido: {len(arquivos_salvos)} arquivos')
                        else:
                            _BASE_GEN = os.path.join(
                                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "..", "Projeto MCR", "scripts", "generated")
                            caminho = os.path.join(_BASE_GEN, f"quest_completa_{abs(hash(resposta[:50]))%10000}.lua")
                            os.makedirs(os.path.dirname(caminho), exist_ok=True)
                            with open(caminho, 'w', encoding='latin-1') as f:
                                f.write(resposta)
                            ctx["arquivos_salvos"] = [caminho]
                            print(f'[PosProcess] Fallback final: {caminho}')
                    else:
                        _BASE_GEN = os.path.join(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "..", "Projeto MCR", "scripts", "generated")
                        caminho = os.path.join(_BASE_GEN, f"gerado_{abs(hash(resposta[:50]))%10000}.lua")
                        os.makedirs(os.path.dirname(caminho), exist_ok=True)
                        with open(caminho, 'w', encoding='latin-1') as f:
                            f.write(resposta)
                        ctx["arquivos_salvos"] = [caminho]
                        print(f'[PosProcess] Fallback (sem LLM): {caminho}')
        
        elif comando == "llm_gerar":
            llm = getattr(self, '_llm', None)
            modelo = getattr(self, '_modelo', 'qwen2.5-coder:7b')
            entrada = ctx.get("entrada", "")
            gaps = ctx.get("gaps_restantes", [])
            classe = getattr(self, '_classe', '')
            code_analyzer_output = ctx.get("code_analyzer_output", "")
            
            # ─── MCRSystem: resposta via Markov (zero LLM) ──────────────
            # Se for pergunta conceitual e MCRSystem conhece, responde em 0s
            if not gaps and classe and any(c in classe for c in ["explicar_conceito", "perguntar", "spa", "mcr"]):
                _cerebro_local = getattr(self, '_cerebro', None)
                if _cerebro_local:
                    _kg = getattr(_cerebro_local, 'kg', None)
                    # Tenta KG primeiro (busca direta por conceitos no KnowledgeGraph real)
                    if _kg and hasattr(_kg, 'buscar'):
                        try:
                            _re = __import__('re')
                            _termos = _re.findall(r'\b[a-zA-ZÀ-ÿ_]{3,}\b', entrada.lower())
                            for _t in _termos[:3]:
                                _res = _kg.buscar(_t, max_r=5)  # busca mais resultados para filtrar
                                if not _res:
                                    continue
                                # Procura o primeiro resultado que seja texto natural (sem codigo)
                                for _item in (_res if isinstance(_res, list) else [_res]):
                                    _txt = _item.get('solucao', '') if isinstance(_item, dict) else str(_item)
                                    # Filtra: descarta se parecer codigo
                                    if ('{' in _txt and len(_re.findall(r'\{', _txt)) > 2) or \
                                       'import ' in _txt[:50] or \
                                       'class ' in _txt[:50] or \
                                       'def ' in _txt[:50] or \
                                       '```' in _txt:
                                        continue
                                    if len(_txt) > 30:
                                        ctx["llm_output"] = _txt[:500]
                                        ctx["kg_resposta"] = True
                                        print(f'[KGResposta] termo={_t} chars={len(_txt)}')
                                        return
                        except: pass
                    # Fallback: Markov word chain
                    if hasattr(_cerebro_local, 'mk_palavra'):
                        try:
                            _palavras = re.findall(r'\b[a-zA-ZÀ-ÿ_]{3,}\b', entrada.lower())
                            if _palavras:
                                _cadeia = []
                                _conf_min = 1.0
                                _ativador = None
                                for p in _palavras:
                                    _pred, _conf = _cerebro_local.mk_palavra.predizer(p)
                                    if _pred and _conf > 0.10:
                                        _ativador = p
                                        _conf_min = _conf
                                        _atual = p
                                        for _ in range(20):
                                            _prox, _c = _cerebro_local.mk_palavra.predizer(_atual)
                                            if not _prox or _c < 0.03:
                                                break
                                            _cadeia.append(_prox)
                                            _atual = _prox
                                            _conf_min = min(_conf_min, _c)
                                        break
                                if _cadeia and 20 < len(' '.join(_cadeia)) < 400 and _conf_min >= 0.04:
                                    ctx["llm_output"] = "[Markov] " + ' '.join(_cadeia)
                                    print(f'[MarkovResposta] conf={_conf_min:.3f} termos={len(_cadeia)}')
                                    return
                        except: pass
            
            # ─── LLM gerar (fallback) ───────────────────────────────────
            
            # Regras de dominio por classe
            regras_dominio = ""
            if classe and any(c in classe for c in ["criar_habilidade", "spa"]):
                _golden_spa = ""
                try:
                    _golden_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_examples", "canary_spa_template.lua")
                    if os.path.exists(_golden_path):
                        with open(_golden_path, 'r', encoding='utf-8') as _gf:
                            _golden_spa = _gf.read()
                except: pass
                regras_dominio = (
                    "DIRETRIZES OBRIGATORIAS PARA HABILIDADES SPA v2.0:\n"
                    "1. E PROIBIDO usar o campo `efeito = function(...)`. NUNCA escreva funcoes Lua.\n"
                    "2. Toda a logica DEVE ser declarativa dentro de `efeitoConfig`.\n"
                    "3. O motor processa tudo automaticamente. life_leech = 15 dentro de efeitoConfig.\n"
                    "4. Se for passiva (vida/mana/velocidade), deixe `efeito = \"\"` (vazio).\n"
                    "5. NUNCA escreva funcoes manuais para calcular dano ou curar. Apenas parametros.\n"
                    "6. Use os campos: tipo, percentual, elemento, life_leech, raio, saltos dentro de efeitoConfig.\n"
                    "7. Respeite o campo categoria: single, aoe, debuff, buff, finisher, sinergia, defense.\n"
                    "\n"
                    "=== GOLDEN EXAMPLE — HABILIDADE SPA REAL (USE ESTRITAMENTE) ===\n"
                    + (_golden_spa[:2000] if _golden_spa else "") +
                    "\n=== FIM GOLDEN EXAMPLE ===\n"
                )
            elif classe and any(c in classe for c in ["quest"]):
                # Carrega golden example do Canary
                _golden_quest = ""
                try:
                    _golden_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_examples", "canary_quest_template.lua")
                    if os.path.exists(_golden_path):
                        with open(_golden_path, 'r', encoding='utf-8') as _gf:
                            _golden_quest = _gf.read()
                except: pass
                
                regras_dominio = (
                    "FORMATO OBRIGATORIO DE RESPOSTA (NAO IGNORE):\n"
                    "Cada arquivo DEVE seguir esta estrutura EXATAMENTE:\n"
                    "\n"
                    "--- ARQUIVO: nome_do_arquivo.lua ---\n"
                    "```lua\n"
                    "[TODO O CODIGO LUA AQUI]\n"
                    "```\n"
                    "\n"
                    "REGRAS ABSOLUTAS:\n"
                    "1. O marcador --- ARQUIVO: nome.lua --- DEVE estar FORA do bloco ```lua.\n"
                    "2. O marcador --- ARQUIVO: ... --- nunca deve ficar dentro de ```lua ... ```.\n"
                    "3. Cada arquivo tem SEU PROPRIO bloco ```lua.\n"
                    "4. NAO coloque tudo em um unico bloco ```lua.\n"
                    "5. NAO misture multiplos sistemas no mesmo arquivo.\n"
                    "6. NAO crie classes inexistentes como Quest(). Use Action() e KeywordHandler().\n"
                    "\n"
                    "=== GOLDEN EXAMPLE — API REAL DO CANARY (USE ESTRITAMENTE) ===\n"
                    + (_golden_quest[:2000] if _golden_quest else "") +
                    "\n=== FIM GOLDEN EXAMPLE ===\n"
                    "\n"
                    "REGRAS DA API CANARY:\n"
                    "- PROIBIDO usar classe Quest(). Nao existe no Canary.\n"
                    "- Use Action() para itens interativos (baus, portas).\n"
                    "- Use KeywordHandler para dialogo de NPC.\n"
                    "- Use player:setStorageValue() para progressao de quest.\n"
                    "- Use player:addItem() e player:removeItem() para recompensas.\n"
                )
            elif classe and any(c in classe for c in ["criar_monster", "criar_sistema"]):
                _golden_monster = ""
                try:
                    _golden_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_examples", "canary_monster_template.lua")
                    if os.path.exists(_golden_path):
                        with open(_golden_path, 'r', encoding='utf-8') as _gf:
                            _golden_monster = _gf.read()
                except: pass
                regras_dominio = (
                    "FORMATO OBRIGATORIO DE RESPOSTA:\n"
                    "Cada arquivo DEVE ter o marcador --- ARQUIVO: nome.lua --- antes de ```lua.\n"
                    "PROIBIDO usar Game.createMonster() para definir monstros. Use Game.createMonsterType().\n"
                    "PROIBIDO usar classes como Quest(). Use Action() e monsterConfig.\n"
                    "\n"
                    "=== GOLDEN EXAMPLE — MONSTRO + ACTION CANARY (USE ESTRITAMENTE) ===\n"
                    + (_golden_monster[:3000] if _golden_monster else "") +
                    "\n=== FIM GOLDEN EXAMPLE ===\n"
                )
            elif classe and any(c in classe for c in ["analisar", "revisar", "bug"]):
                regras_dominio = (
                    "REGRAS DE ANALISE DO PROJETO MCR:\n"
                    "- Encoding C++: UTF-8 literal. Strings do protocolo DEVEM usar toLatin1() antes de msg.addString().\n"
                    "- Lua: ISO-8859-1 (Latin-1). Python/Go: UTF-8.\n"
                    "- Sempre informe arquivo, classe, funcao e linha do bug.\n"
                    "- Quando nao tiver certeza, marque como 'Hipotese'.\n"
                )
            
            # Contexto RAG via ChromaDB
            ctx_rag = ""
            try:
                from rag_mcr import MCRRAG
                _rag = MCRRAG()
                ctx_rag = _rag.contexto_para_prompt(entrada, k=3)
            except Exception as e:
                pass
            
            # Context Enricher (lore) para NPC e explicacao
            ctx_lore = ""
            if classe and any(c in classe for c in ["criar_npc", "explicar_conceito", "spa"]):
                try:
                    sys.path.insert(0, os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "..", "Projeto MCR", "historia", "scripts", "mcr_devia", "modulos"
                    ))
                    from context_enricher import ContextEnricher
                    _enricher = ContextEnricher()
                    _resultado = _enricher.enriquecer(entrada)
                    if _resultado and _resultado.get('valido') and _resultado.get('conteudo'):
                        ctx_lore = "\n### LORE DO PROJETO:\n" + _resultado['conteudo'][:800] + "\n### FIM LORE\n"
                except Exception as e:
                    pass
            
            # Contexto MCR dinamico por classe (fallback se RAG falhar)
            ctx_mcr = ""
            if not ctx_rag:
                if classe and any(c in classe for c in ["analisar", "revisar", "bug", "codigo"]):
                    ctx_mcr = (
                        f"PROJETO MCR (servidor Tibia customizado):\n"
                        f"- MCR_PROJECT_BASE = E:\\Projeto MCR\n"
                        f"- Encoding: .lua=Latin-1, .cpp=.cs=.go=utf-8\n"
                        f"- Comandos em: historia/scripts/mcr_devia/comandos/\n"
                        f"- BASE dos comandos aponta para historia/, deveria ser projeto/\n"
                    )
                elif classe and any(c in classe for c in ["explicar", "conceito", "spa", "mcr"]):
                    ctx_mcr = (
                        "PROJETO MCR — servidor Tibia customizado:\n"
                        "- SPA = Sistema de Progressao do Aventureiro\n"
                        "- SHC = Sistema de Habilidades Contextuais\n"
                        "- SQH = Sistema de Quests Hibrido\n"
                        "- PERSONALIDADE.md = identidade do assistente\n"
                    )
            
            # ContextCrew do CerebroAGI: contexto real do KG + Docs
            ctx_crew_extra = ""
            if hasattr(self, '_cerebro') and self._cerebro:
                try:
                    # MCRSystem: usa ciclo_unico ou _responder
                    if hasattr(self._cerebro, 'context_crew') and self._cerebro.context_crew:
                        ctx_crew_result = self._cerebro.context_crew.executar(entrada, max_termos=4)
                    elif hasattr(self._cerebro, '_responder'):
                        ctx_crew_result = self._cerebro._responder(entrada)[:800]
                    else:
                        ctx_crew_result = ""
                    if ctx_crew_result and len(ctx_crew_result.strip()) > 20:
                        ctx_crew_extra = "\n### CONTEXTO DO PROJETO (KG + DOCS):\n" + str(ctx_crew_result)[:1200] + "\n### FIM CONTEXTO\n"
                except Exception as e:
                    pass
            
            # Contexto episodico (Cache L3)
            ctx_episodico = ""
            if hasattr(self, '_ctx_episodico') and self._ctx_episodico:
                ctx_episodico = "\n### MEMORIA DE SESSAO ANTERIOR:\n" + str(self._ctx_episodico)[:500] + "\n### FIM MEMORIA\n"
            
            contexto_final = ctx_rag or ctx_mcr
            if ctx_lore:
                contexto_final += ctx_lore
            if ctx_crew_extra:
                contexto_final += ctx_crew_extra
            if ctx_episodico:
                contexto_final += ctx_episodico
            
            # Se ja temos bugs deterministicos, injeta no prompt
            bugs_deterministicos = ""
            if code_analyzer_output and "Nenhum bug" not in code_analyzer_output:
                bugs_deterministicos = (
                    f"BUGS JA ENCONTRADOS (deterministicos, 0ms):\n"
                    f"{code_analyzer_output}\n\n"
                    f"Alem destes, encontre OUTROS bugs nao detectados por pattern matching.\n"
                )
            
            if gaps and llm:
                prompt = (
                    f"{contexto_final}{regras_dominio}"
                    f"Preencha os gaps abaixo. Use o contexto do projeto se disponivel.\n"
                    f"Gaps: {gaps}\n"
                    f"Contexto: {entrada}"
                )
                resp = llm.gerar(prompt, modelo=modelo)
                ctx["llm_output"] = resp
            elif entrada and llm:
                # Inclui conteudo do arquivo se disponivel (via cmd_read)
                conteudo_arquivo = ctx.get("conteudo", "")
                bloco_codigo = ""
                if conteudo_arquivo and len(conteudo_arquivo) > 20:
                    linhas = conteudo_arquivo.split('\n')
                    # So envia primeiras 80 linhas (suficiente pra analise)
                    snippet = '\n'.join(f'L{i}: {l}' for i, l in enumerate(linhas[:80], 1) if l.strip())
                    bloco_codigo = f"=== CODIGO ===\n{snippet[:2000]}\n=== FIM ==="
                
                tem_bugs_det = code_analyzer_output and "Nenhum bug" not in code_analyzer_output
                
                if tem_bugs_det:
                    prompt = (
                        f"{contexto_final}{regras_dominio}"
                        f"Bugs encontrados (0ms deterministico):\n{code_analyzer_output[:500]}\n\n"
                        f"{bloco_codigo}\n"
                        f"Encontre OUTROS bugs alem dos ja listados. Seja direto. "
                        f"Numero da linha, descricao curta, correcao. Nao repita os bugs ja listados."
                    )
                elif bloco_codigo:
                    prompt = (
                        f"{contexto_final}{regras_dominio}"
                        f"{bloco_codigo}\n"
                        f"Analise o codigo acima. Encontre bugs: linha, descricao, severidade, correcao."
                    )
                else:
                    # Desambiguacoes conhecidas para o modelo nao alucinar conceitos MCR
                    desambiguacoes = (
                        "NO CONTEXTO DO PROJETO MCR:\n"
                        "- SPA = Sistema de Progressao do Aventureiro (NAO e Single Page Application)\n"
                        "- SHC = Sistema de Habilidades Contextuais\n"
                        "- SQH = Sistema de Quests Hibrido\n"
                        "- MCR = Projeto de servidor Tibia customizado\n"
                    )
                    prompt = (
                        f"{contexto_final}{regras_dominio}"
                        f"{desambiguacoes}"
                        f"Use o CONTEXTO acima se relevante. Nao alucine significados de siglas.\n"
                        f"Responda em PT-BR: {entrada}"
                    )
                resp = llm.gerar(prompt, modelo=modelo)
                # Validacao de sintaxe + estrutura Canary + itens
                if llm and classe and any(c in classe for c in ["criar", "spa", "npc", "quest", "codigo", "habilidade"]):
                    from LuaSyntaxValidator import verificar_sintaxe, validar_com_loop
                    codigo_final, sintaxe_ok, tentativas, erros_valid = validar_com_loop(
                        codigo=resp, classe=classe,
                        llm_func=llm.gerar, modelo=modelo, max_tentativas=3
                    )
                    
                    # Valida estrutura Canary (LuaValidator original do DevIA)
                    try:
                        _devia_modulos = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "..", "Projeto MCR", "historia", "scripts", "mcr_devia", "modulos")
                        if os.path.isdir(_devia_modulos):
                            sys.path.insert(0, _devia_modulos)
                            from lua_validator import LuaValidator
                            val_est = LuaValidator()
                            # Extrai tipo da classe (criar_npc -> npc, criar_quest -> quest)
                            _tipo_val = classe.replace('criar_', '').replace('_', '') if classe else ''
                            rel = val_est.validar(codigo_final, tipo=_tipo_val)
                            if not rel.get('valido', True) and tentativas < 3:
                                erros_est = rel.get('avisos', [])[:5] + rel.get('erros', [])[:3]
                                if erros_est:
                                    prompt_est = (
                                        f"O codigo Lua tem problemas estruturais no Canary:\n"
                                        + "\n".join(erros_est) + "\n\n"
                                        f"=== CODIGO ===\n{codigo_final[:2000]}\n=== FIM ===\n"
                                        f"Corrija. Responda APENAS com o codigo Lua."
                                    )
                                    codigo_final = llm.gerar(prompt_est, modelo=modelo)
                                    tentativas += 1
                    except: pass
                    
                    # Valida IDs de itens contra items.xml real
                    if classe and any(c in classe for c in ["npc", "quest"]):
                        try:
                            _devia_know = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "..", "Projeto MCR", "historia", "scripts", "mcr_devia", "knowledge")
                            if os.path.isdir(_devia_know):
                                sys.path.insert(0, _devia_know)
                                from item_database import ItemDatabase
                                db_itens = ItemDatabase()
                                ids = set()
                                for m in re.finditer(r'clientId\s*=\s*(\d+)', codigo_final):
                                    ids.add(int(m.group(1)))
                                for m in re.finditer(r'itemId\s*=\s*(\d+)', codigo_final):
                                    ids.add(int(m.group(1)))
                                invalidos = [str(i) for i in ids if not db_itens.buscar_por_id(i)]
                                if invalidos and tentativas < 3:
                                    prompt_itens = (
                                        f"IDs invalidos no items.xml: {', '.join(invalidos)}. "
                                        f"Substitua por IDs reais do Canary."
                                        f"\n=== CODIGO ===\n{codigo_final[:2000]}\n=== FIM ==="
                                    )
                                    codigo_final = llm.gerar(prompt_itens, modelo=modelo)
                                    tentativas += 1
                        except: pass
                    
                    ctx["llm_output"] = codigo_final
                    ctx["sintaxe_valida"] = sintaxe_ok
                    ctx["tentativas_sintaxe"] = tentativas
                    if not sintaxe_ok:
                        ctx["sintaxe_erro"] = erros_valid
                    if tentativas > 1 or not sintaxe_ok:
                        print(f'[LuaValidator] classe={classe} valido={sintaxe_ok} tentativas={tentativas}')
                    # Alimenta KG com o erro para aprender
                    if erros_valid and sintaxe_ok and hasattr(self, '_cerebro') and self._cerebro:
                        try:
                            _kg = self._cerebro.kg
                            if hasattr(_kg, 'aprender'):
                                import inspect
                                _n_params = len(inspect.signature(_kg.aprender).parameters)
                                if _n_params >= 4:
                                    _kg.aprender(erro=str(erros_valid[0])[:100],
                                                 causa="LLM gerou codigo Lua invalido para %s" % classe,
                                                 solucao="Auto-corrigido pelo LuaValidator + LLM",
                                                 ctx=classe)
                                else:
                                    _kg.aprender(str(erros_valid[0])[:100],
                                                 "Auto-corrigido pelo LuaValidator + LLM",
                                                 classe)
                        except: pass
                else:
                    ctx["llm_output"] = resp
                # So aplica dedup em texto, nao em codigo
                if classe and any(c in classe for c in ["criar", "spa", "npc", "quest", "codigo", "habilidade"]):
                    pass
                else:
                    ctx["llm_output"] = _dedup_resposta(ctx.get("llm_output", resp))
            else:
                ctx["llm_output"] = f"[LLM indisponivel: {entrada[:50]}]"
        
        # ─── Comandos do kernel (cmd_*) ──────────────────────
        elif comando.startswith("cmd_") and self.kernel:
            nome_cmd = comando[4:]  # "cmd_read" -> "read"
            args = self._montar_args(nome_cmd, ctx)
            
            # Timeout de 15s para comandos do kernel (evita travar o pipeline)
            _CMD_TIMEOUT = 15
            _cmd_result = {"stdout": "", "erro": None}
            
            def _exec_cmd():
                with CommandCapture() as cap:
                    self.kernel.executar(nome_cmd, args)
                _cmd_result["stdout"] = cap.texto
                _cmd_result["caminhos"] = cap.extrair_caminhos()
                _cmd_result["conteudo"] = cap.extrair_conteudo() if nome_cmd == "read" else ""
            
            import threading as _thr
            _t = _thr.Thread(target=_exec_cmd, daemon=True)
            _t.start()
            _t.join(timeout=_CMD_TIMEOUT)
            
            if _t.is_alive():
                # Timeout: mata a thread (via daemon) e segue
                print(f'[Pipeline] TIMEOUT ({_CMD_TIMEOUT}s): cmd_{nome_cmd} {args[:2]}')
                _cmd_result["erro"] = "TIMEOUT"
                ctx["stdout"] += f"[Timeout] cmd_{nome_cmd} excedeu {_CMD_TIMEOUT}s\n"
            else:
                stdout = _cmd_result["stdout"]
                ctx["stdout"] += stdout + "\n"
                ctx["caminhos"].extend(_cmd_result["caminhos"])
                if nome_cmd == "read":
                    ctx["conteudo"] = _cmd_result["conteudo"]
                elif nome_cmd == "grep":
                    ctx["caminhos"] = list(set(ctx["caminhos"]))
        
        elif comando in HANDLERS_INTERNOS:
            HANDLERS_INTERNOS[comando](ctx)
        
        else:
            ctx["erro"] = f"Comando desconhecido: {comando}"
    
    def _montar_args(self, nome_cmd: str, ctx: Dict) -> List[str]:
        """Monta argumentos para comando baseado no contexto.
        
        Extrai caminhos da pergunta: "leia o progresso.md" → "progresso.md"
        Usa diretorio base do projeto MCR para buscas."""
        entrada = ctx.get("entrada", "")
        projeto_base = os.path.dirname(os.path.abspath(__file__))
        
        palavras = entrada.split()
        
        def extrair_caminho(texto):
            for p in texto.split():
                if '.' in p:
                    return p.strip("'\".,;!?:")
            return ""
        
        def resolver_path(p):
            if not p: return ""
            if os.path.exists(p): return p
            if not os.path.isabs(p):
                p = os.path.join(projeto_base, p)
            if os.path.exists(p): return p
            
            nome_arquivo = os.path.basename(p)
            atalhos = [
                os.path.join(projeto_base, nome_arquivo),
                os.path.join(projeto_base, "docs", nome_arquivo),
                os.path.join(projeto_base, "historia", "scripts", "mcr_devia", "comandos", nome_arquivo),
                os.path.join(projeto_base, "historia", "scripts", "mcr_devia", "modulos", nome_arquivo),
                os.path.join(projeto_base, "MCR.Grimorio", nome_arquivo),
                os.path.join(projeto_base, "Canary", nome_arquivo),
            ]
            for atalho in atalhos:
                if os.path.exists(atalho): return atalho
            return p
        
        if nome_cmd == "read":
            caminhos = ctx.get("caminhos", [])
            if caminhos:
                return [caminhos[0]]
            caminho = extrair_caminho(entrada)
            if caminho:
                return [resolver_path(caminho)]
            return [os.path.join(projeto_base, "progresso.md")]
        
        elif nome_cmd == "grep":
            caminho_extraido = extrair_caminho(entrada)
            if caminho_extraido and os.path.isdir(resolver_path(caminho_extraido)):
                return [caminho_extraido, resolver_path(caminho_extraido)]
            # Extrai palavra-chave da pergunta: ultima palavra substantiva
            # "crie uma habilidade de gelo" -> "gelo"
            # "encontre crash no servidor" -> "servidor"
            ignorar = {"crie", "criar", "fazer", "gere", "gerar", "implemente", "leia", "ler",
                       "mostre", "exiba", "explique", "traduza", "encontre", "ache", "busque",
                       "compile", "rode", "execute", "de", "do", "da", "um", "uma", "o", "a",
                       "para", "pro", "no", "na", "em", "com", "que", "e", "ou"}
            palavras_uteis = [p for p in palavras if p.lower() not in ignorar and len(p) > 2]
            padrao = palavras_uteis[-1] if palavras_uteis else (palavras[-1] if palavras else "")
            if padrao:
                # Se tarefa de criacao, busca no diretorio de habilidades
                if any(v in entrada.lower() for v in ["crie", "criar", "habilidade", "skill"]):
                    skills_dir = os.path.join(projeto_base, r"Canary\data-canary\scripts\MCR\SPA\habilidades")
                    if os.path.isdir(skills_dir):
                        return [padrao, skills_dir]
                return [padrao, projeto_base]
            return ["", "."]
        
        elif nome_cmd == "write":
            saida = ctx.get("saida_path", extrair_caminho(entrada))
            return [resolver_path(saida), ctx.get("preenchido", ctx.get("llm_output", ""))]
        
        elif nome_cmd == "review":
            return [entrada]
        
        return []
