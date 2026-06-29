# EXPERIMENTAL — Use agent_loop como pipeline principal.
# MetaCreator foi construido como pipeline universal Think->Act->Observe->Learn
# paralelo ao agent_loop. A correcao de ~30 linhas no agent_loop
# torna este modulo redundante. Mantido como referencia arquitetural.
# Veja docs/PLANO_REFATORACAO.md.
"""MetaCreator — Ponto de entrada unico para criacao de QUALQUER coisa.

Pipeline universal:
  1. TaskAnalyzer → classifica o input (criacao, analise, pergunta, etc)
  2. GapDetector → detecta o que esta faltando
  3. Executor → preenche gaps com estrategias (indexer > xml > web > llm > humano)
  4. Gerador → gera o artefato final (NPC, codigo, site, etc)
  5. Validador → valida o resultado (semantica + sintaxe)
  6. Learner → registra aprendizado no KG

Uso:
    from engine.meta_creator import MetaCreator
    mc = MetaCreator()
    resultado = mc.criar("cria um ferreiro em Eridanus")
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import os, sys, json, time

_MCR_DEVIA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _MCR_DEVIA not in sys.path:
    sys.path.insert(0, _MCR_DEVIA)

from engine.task_analyzer import TaskAnalyzer, TaskType, TaskAnalysis
from engine.executor import Executor, ExecutorResult
from engine.gap_detector import GapDetector


# ============================================================
# RESULTADO DO META CREATOR
# ============================================================

@dataclass
class MetacreatorResult:
    """Resultado completo da operacao do MetaCreator."""
    sucesso: bool = False
    tipo: str = ""
    subtipo: str = ""
    descricao: str = ""
    execucao: Optional[ExecutorResult] = None
    codigo_gerado: str = ""
    arquivo: str = ""
    erros: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    tempo_total: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'sucesso': self.sucesso,
            'tipo': self.tipo,
            'subtipo': self.subtipo,
            'descricao': self.descricao[:100],
            'gaps': f"{self.execucao.gaps_preenchidos if self.execucao else 0}/"
                    f"{self.execucao.gaps_total if self.execucao else 0}",
            'tempo': f"{self.tempo_total:.1f}s",
            'arquivo': self.arquivo,
            'erros': self.erros[:3],
            'avisos': self.avisos[:3],
        }


# ============================================================
# META CREATOR
# ============================================================

class MetaCreator:
    """Motor universal de criacao."""
    
    def __init__(self):
        self.task_analyzer = TaskAnalyzer()
        self.executor = Executor()
    
    def criar(self, input_usuario: str) -> MetacreatorResult:
        """Ponto de entrada unico: aceita QUALQUER input.
        
        Args:
            input_usuario: Descricao do que criar (ex: "cria ferreiro em Eridanus")
        
        Returns:
            MetacreatorResult com o resultado completo
        """
        inicio = time.time()
        resultado = MetacreatorResult(
            descricao=input_usuario,
        )
        
        # 1. ANALISAR TAREFA
        analise = self.task_analyzer.analisar(input_usuario)
        resultado.tipo = analise.tipo.value
        resultado.subtipo = analise.subtipo
        
        if analise.tipo == TaskType.DESCONHECIDO:
            resultado.erros.append("Nao foi possivel classificar a tarefa")
            resultado.tempo_total = time.time() - inicio
            return resultado
        
        # Roteamento por tipo
        dispatch = {
            TaskType.CRIACAO: self._processar_criacao,
            TaskType.ANALISE: self._processar_analise,
            TaskType.PERGUNTA: self._processar_pergunta,
            TaskType.CORRECAO: self._processar_correcao,
            TaskType.EXPLORACAO: self._processar_exploracao,
            TaskType.EXECUCAO: self._processar_execucao,
            TaskType.META: self._processar_meta,
        }
        
        handler = dispatch.get(analise.tipo)
        if handler:
            handler(resultado, analise)
        else:
            resultado.erros.append(f"Tipo de tarefa nao suportado: {analise.tipo}")
        
        resultado.tempo_total = time.time() - inicio
        return resultado
    
    def _processar_criacao(self, resultado: MetacreatorResult, analise: TaskAnalysis):
        """Processa uma tarefa de CRIACAO."""
        subtipo = analise.subtipo
        params = analise.parametros
        
        # NPC creation
        if subtipo in ('npc_shop', 'npc_quest', 'npc_bank', 'npc_gate',
                        'npc_trainer', 'npc_dialogue', 'npc'):
            self._criar_npc(resultado, analise)
        
        # Website creation
        elif subtipo == 'website':
            resultado.avisos.append("Criacao de websites nao implementada ainda")
        
        # Script creation
        elif subtipo == 'script':
            resultado.avisos.append("Criacao de scripts nao implementada ainda")
        
        else:
            # Tenta como NPC generico
            self._criar_npc(resultado, analise)
    
    def _processar_analise(self, resultado: MetacreatorResult, analise: TaskAnalysis):
        """Processa uma tarefa de ANALISE."""
        resultado.avisos.append("Analise de codigo redirecionada para o comando analisar")
    
    def _processar_pergunta(self, resultado: MetacreatorResult, analise: TaskAnalysis):
        """Processa uma tarefa de PERGUNTA."""
        resultado.avisos.append("Pergunta redirecionada para o comando perguntar")
    
    def _processar_correcao(self, resultado: MetacreatorResult, analise: TaskAnalysis):
        """Processa uma tarefa de CORRECAO."""
        resultado.avisos.append("Correcao redirecionada para o comando analisar")
    
    def _processar_exploracao(self, resultado: MetacreatorResult, analise: TaskAnalysis):
        """Processa uma tarefa de EXPLORACAO."""
        resultado.avisos.append("Exploracao redirecionada para o comando perguntar")
    
    def _processar_execucao(self, resultado: MetacreatorResult, analise: TaskAnalysis):
        """Processa uma tarefa de EXECUCAO."""
        subtipo = analise.subtipo
        if subtipo == 'teste':
            resultado.avisos.append("Teste redirecionado para cmd_autoteste")
        elif subtipo == 'compilacao':
            resultado.avisos.append("Compilacao redirecionada para o build do Canary")
        else:
            resultado.avisos.append(f"Execucao '{subtipo}' nao implementada")
    
    def _processar_meta(self, resultado: MetacreatorResult, analise: TaskAnalysis):
        """Processa uma tarefa META (pergunta sobre o sistema)."""
        from knowledge.tool_registry import get_registry
        reg = get_registry()
        ferramentas = reg.listar()
        
        info = [
            f"Sou o MetaCreator, o motor universal de criacao do MCR.",
            f"Tenho {len(ferramentas)} ferramentas disponiveis em {len(set(t.categoria for t in ferramentas))} categorias.",
            f"Posso criar NPCs (shop/quest/bank/gate/trainer/dialogue), analisar codigo, responder perguntas, e muito mais.",
            "",
            "Exemplos de uso:",
            '  "cria um ferreiro em Eridanus"',
            '  "faz um banco em Venore"',
            '  "analisa esse codigo"',
            '  "o que e SPA?"',
        ]
        resultado.codigo_gerado = '\n'.join(info)
        resultado.sucesso = True
    
    def _criar_npc(self, resultado: MetacreatorResult, analise: TaskAnalysis):
        """Cria um NPC usando o pipeline completo."""
        params = analise.parametros
        
        # Determinar tipo NPC
        tipo_npc = params.get('tipo_npc', 'shop')
        if analise.subtipo in ('npc_shop', 'npc_quest', 'npc_bank',
                                'npc_gate', 'npc_trainer', 'npc_dialogue'):
            tipo_npc = analise.subtipo.replace('npc_', '')
        
        # Montar contexto
        contexto = {
            'profissao': params.get('profissao', tipo_npc),
            'local': params.get('local', ''),
            'tipo_npc': tipo_npc,
            'item': params.get('item', ''),
            'palavras_chave': analise.tokens_importantes,
        }
        
        # 2. EXECUTOR: preencher gaps
        exec_result = self.executor.executar(tipo_npc, contexto)
        resultado.execucao = exec_result
        
        if exec_result.erros:
            resultado.erros.extend(exec_result.erros)
        
        # 3. GERAR CODIGO com NPCGenerator
        codigo, arquivo = self._gerar_codigo_npc(
            tipo_npc,
            exec_result.placeholders_preenchidos,
            params,
            analise.descricao,
        )
        
        resultado.codigo_gerado = codigo
        resultado.arquivo = arquivo
        resultado.sucesso = bool(codigo)
    
    def _gerar_codigo_npc(self, tipo_npc: str, placeholders_preenchidos: Dict,
                           params: Dict, descricao: str) -> tuple:
        """Gera codigo Lua do NPC usando placeholders preenchidos.
        
        Diferente do NPCGenerator.gerar(), este metodo NAO gera placeholders
        genericos — usa os valores preenchidos pelas estrategias.
        """
        try:
            from modulos.npc_generator import NPCGenerator, TEMPLATES, TEMPLATE_BASE
            
            gen = NPCGenerator()
            template = TEMPLATES.get(tipo_npc)
            if not template:
                return "", ""
            
            nome = (params.get('nome_npc') or 
                    placeholders_preenchidos.get('nome', '') or 
                    gen._gerar_nome(descricao, tipo_npc))
            
            # 1. Construir placeholders finais (preenchidos + defaults)
            placeholders = dict(placeholders_preenchidos)
            placeholders.setdefault('nome', nome)
            placeholders.setdefault('looktype', 130)
            
            # Placeholders com aninhamento: primeiro define valor bruto do template
            desc_raw = template.get('descricao', '{nome}')
            saud_raw = template.get('saudacao', 'Hello!')
            placeholders.setdefault('descricao', desc_raw)
            placeholders.setdefault('saudacao', saud_raw)
            
            # 2. Resolver placeholders aninhados (loop igual NPCGenerator)
            for _ in range(3):
                alterado = False
                for k, v in list(placeholders.items()):
                    if isinstance(v, str) and '{' in v:
                        try:
                            novo = v.format(**placeholders)
                            if novo != v:
                                placeholders[k] = novo
                                alterado = True
                        except KeyError:
                            pass
                if not alterado:
                    break
            
            # 3. Montar codigo direto
            shop_config = template.get('shop_part', '')
            if shop_config:
                try:
                    shop_config = shop_config.format(**placeholders)
                except KeyError:
                    shop_config = ''
            
            handler_part = template.get('handler_part', '')
            conteudo_custom = ''
            if handler_part:
                try:
                    conteudo_custom = handler_part.format(**placeholders)
                except KeyError as e:
                    conteudo_custom = '-- [[ Placeholder faltando: %s ]]\n' % e
            
            callbacks = ''
            if conteudo_custom and 'setCallback' not in conteudo_custom:
                callbacks = 'npcHandler:setCallback(CALLBACK_MESSAGE_DEFAULT, creatureSayCallback)'
            
            # Usar placeholders ja resolvidos
            codigo = TEMPLATE_BASE.format(
                nome=placeholders.get('nome', 'NPC'),
                descricao=placeholders.get('descricao', ''),
                looktype=placeholders.get('looktype', 130),
                saudacao=placeholders.get('saudacao', 'Hello!'),
                shop_config=shop_config,
                conteudo_custom=conteudo_custom,
                callbacks=callbacks,
            )
            
            # 3. Salvar
            nome_arquivo = nome.lower().replace(' ', '_').replace("'", '')
            caminho = os.path.join(
                os.path.dirname(__file__), '..', '..', '..', 'sandbox',
                '%s.lua' % nome_arquivo
            )
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(codigo)
            
            return codigo, caminho
        
        except Exception as e:
            return "", ""


# ============================================================
# FUNCAO UNICA DE ENTRADA
# ============================================================

def criar(input_usuario: str) -> MetacreatorResult:
    """Funcao unica de entrada para o MetaCreator."""
    mc = MetaCreator()
    return mc.criar(input_usuario)


# ============================================================
# TESTE
# ============================================================

if __name__ == '__main__':
    import json
    
    print("=== TESTE META CREATOR ===\n")
    
    # Garantir que estrategias estao carregadas
    import strategies.local
    import strategies.items_xml
    import strategies.web
    import strategies.llm
    import strategies.human
    
    testes = [
        "cria um ferreiro em Eridanus",
        "faz um banco em Venore",
        "o que voce sabe fazer?",
        "cria uma conversa com um andarilho",
    ]
    
    for teste in testes:
        print(f"\n--- Input: '{teste}' ---")
        resultado = criar(teste)
        info = resultado.to_dict()
        print(json.dumps(info, indent=2, ensure_ascii=False))
        
        if resultado.codigo_gerado:
            linhas = resultado.codigo_gerado.split('\n')
            print(f"  Codigo gerado: {len(linhas)} linhas")
            if resultado.arquivo:
                print(f"  Arquivo: {resultado.arquivo}")
        
        if resultado.erros:
            for e in resultado.erros[:3]:
                print(f"  Erro: {e}")
        if resultado.avisos:
            for a in resultado.avisos[:3]:
                print(f"  Aviso: {a}")
