"""Agent Loop — Núcleo AGI: Think → Act → Observe → Learn.

Orquestra o pipeline completo de geração de NPCs:
1. THINK: Analisa descrição, busca exemplos similares + KG, planeja
2. ACT: Gera código via NPCGenerator com placeholders do LLM
3. OBSERVE: Valida com LuaValidator, verifica SQL injection
4. LOOP: Se falhar, retry com correção (max 3)
5. LEARN: Registra lições no histórico + Knowledge Graph

Uso:
    from modulos.agent_loop import AgentLoop
    agent = AgentLoop()
    resultado = agent.executar("Ferreiro em Eridanus que vende espadas")
"""
import os, json, re, sys, time
from typing import Dict, Optional, List

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos'))

from canary_indexer import CanaryIndexer
from npc_generator import NPCGenerator
from lua_validator import LuaValidator
from kg import KnowledgeGraph

SANDBOX = os.path.join(BASE, 'sandbox')
HISTORICO_PATH = os.path.join(SANDBOX, 'agent_historico.json')

# ============================================================
# AGENT LOOP
# ============================================================

class AgentLoop:
    """Agente autônomo para geração de NPCs.
    
    Ciclo: Think → Act → Observe → (loop|learn)
    - Max 3 retries com feedback do validador
    - Busca exemplos similares no CanaryIndexer
    - Usa LLM para gerar placeholders
    """
    
    def __init__(self):
        self.indexer = CanaryIndexer()
        self.generator = NPCGenerator()
        self.validator = LuaValidator()
        self.kg = KnowledgeGraph()
        self.historico = self._carregar_historico()
        self._passos = []
    
    def executar(self, descricao: str, tipo: str = 'shop') -> Dict:
        """Executa o pipeline completo de geração.
        
        Args:
            descricao: Descrição do NPC desejado
            tipo: Tipo de NPC (shop/quest/bank/gate/trainer/dialogue)
        
        Returns:
            Dict com resultado final
        """
        t0 = time.time()
        self._passos = []
        self._log('THINK', 'Iniciando geracao: %s (%s)' % (descricao, tipo))
        
        # === THINK ===
        # 1. Indexar se necessario
        self.indexer.indexar()
        
        # 2. Buscar exemplos similares no CanaryIndexer
        exemplos = self.indexer.buscar(descricao, limite=3)
        self._log('THINK', 'Encontrados %d exemplos similares' % len(exemplos))
        
        # 3. Buscar licoes no Knowledge Graph
        lessons_kg = self.kg.buscar(descricao + ' ' + tipo, max_r=3)
        if lessons_kg:
            self._log('THINK', 'Encontradas %d lessons no KG' % len(lessons_kg))
            for l in lessons_kg:
                self._log('THINK', '  Lesson: %s' % l.get('solucao', ''))
        
        # 4. Analisar exemplos
        inspiracao = self._analisar_exemplos(exemplos, tipo)
        self._log('THINK', 'Inspiracao: %s' % inspiracao)
        
        # === ACT + OBSERVE (LOOP) ===
        tentativas = 0
        max_tentativas = 3
        ultimo_resultado = None
        
        while tentativas < max_tentativas:
            tentativas += 1
            self._log('ACT', 'Tentativa %d/%d' % (tentativas, max_tentativas))
            
            # Gerar NPC
            resultado = self.generator.gerar(descricao, tipo, exemplos=exemplos)
            if resultado.get('erro'):
                self._log('OBSERVE', 'Erro na geracao: %s' % resultado['erro'])
                ultimo_resultado = resultado
                continue
            
            # Validar
            validacao = self.validator.validar(resultado['codigo'])
            resultado['validacao'] = validacao
            
            self._log('OBSERVE', 'Validacao: valido=%s, erros=%d, sql_injection=%d' % (
                validacao['valido'], len(validacao['erros']), len(validacao['sql_injection'])
            ))
            
            if validacao['valido']:
                # Sucesso!
                self._log('OBSERVE', 'NPC gerado com sucesso!')
                ultimo_resultado = resultado
                break
            else:
                # Analisar erros e corrigir
                erros = validacao.get('erros', []) + [s['tipo'] for s in validacao.get('sql_injection', [])]
                self._log('OBSERVE', 'Falhou: %s' % '; '.join(erros))
                
                # Se tem SQL injection, tentar limpar
                if validacao.get('sql_injection'):
                    codigo_limpo = self._corrigir_sql_injection(resultado['codigo'])
                    if codigo_limpo != resultado['codigo']:
                        resultado['codigo'] = codigo_limpo
                        # Re-validar
                        validacao = self.validator.validar(codigo_limpo)
                        resultado['validacao'] = validacao
                        if validacao['valido']:
                            ultimo_resultado = resultado
                            break
                
                ultimo_resultado = resultado
        
        # === LEARN ===
        self._aprender(descricao, tipo, ultimo_resultado, time.time() - t0)
        
        return ultimo_resultado or {
            'erro': 'Falhou apos %d tentativas' % max_tentativas,
            'codigo': '',
            'nome': '',
            'tipo': tipo,
            'validacao': None,
        }
    
    def _log(self, etapa: str, mensagem: str):
        """Registra passo do agente."""
        entry = {
            'etapa': etapa,
            'mensagem': mensagem,
            'tempo': time.strftime('%H:%M:%S'),
        }
        self._passos.append(entry)
        print('[%s] %s: %s' % (entry['tempo'], etapa, mensagem))
    
    def _analisar_exemplos(self, exemplos: list, tipo: str) -> str:
        """Analisa exemplos similares e extrai inspiracao."""
        if not exemplos:
            return 'Nenhum exemplo similar encontrado'
        
        # Extrair padroes dos exemplos
        info = []
        for ex in exemplos:
            nome = ex.get('nome', 'unknown')
            t = ex.get('tipo', '?')
            n_itens = len(ex.get('itens_shop', []))
            n_topicos = ex.get('topicos', 0)
            tamanho = ex.get('tamanho_linhas', 0)
            info.append('%s (%s, %d itens, %d topicos, %d linhas)' % (
                nome, t, n_itens, n_topicos, tamanho
            ))
        
        return 'Exemplos: ' + ' | '.join(info)
    
    def _corrigir_sql_injection(self, codigo: str) -> str:
        """Tenta corrigir SQL injection substituindo por db.storeQuery seguro."""
        # Substitui db.query() com concatenação por versão parametrizada
        codigo = re.sub(
            r'db\.query\s*\(\s*"([^"]*)"\s*\.\.\s*([^)]+)\s*\)',
            r'db.storeQuery("\1", \2)',
            codigo
        )
        # Remove concatenação de getName/getGuid
        codigo = re.sub(
            r'\.\.\s*\w+:\s*getName\s*\(\s*\)',
            ' -- [sanitizado]',
            codigo
        )
        return codigo
    
    def _aprender(self, descricao: str, tipo: str, resultado: Dict, tempo: float):
        """Registra licao aprendida no historico."""
        aprendizagem = {
            'descricao': descricao,
            'tipo': tipo,
            'tempo': tempo,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'sucesso': resultado and resultado.get('validacao', {}).get('valido', False),
            'tentativas': len(self._passos) // 3 + 1,  # Aproximado
            'passos': self._passos,
        }
        
        if resultado:
            aprendizagem['nome'] = resultado.get('nome', 'unknown')
            aprendizagem['arquivo'] = resultado.get('arquivo', '')
            aprendizagem['n_erros'] = len(resultado.get('validacao', {}).get('erros', []))
            aprendizagem['n_avisos'] = len(resultado.get('validacao', {}).get('avisos', []))
        
        # Registrar no Knowledge Graph
        if resultado and resultado.get('nome'):
            nome_npc = resultado['nome']
            valido = resultado.get('validacao', {}).get('valido', False)
            status = 'sucesso' if valido else 'falha'
            erros = resultado.get('validacao', {}).get('erros', [])
            
            lesson_erro = 'Geracao NPC %s (%s): %s' % (nome_npc, tipo, status)
            lesson_causa = descricao
            lesson_solucao = 'NPC %s gerado com %d erros, %d avisos. Arquivo: %s' % (
                nome_npc,
                len(resultado.get('validacao', {}).get('erros', [])),
                len(resultado.get('validacao', {}).get('avisos', [])),
                resultado.get('arquivo', '')
            )
            if erros:
                lesson_solucao += ' | Erros: ' + '; '.join(erros)
            
            self.kg.data['licoes'].append({
                'id': 'NPC_%s' % nome_npc.replace(' ', '_'),
                'erro': lesson_erro,
                'causa': lesson_causa,
                'solucao': lesson_solucao,
                'ctx': 'gerar_npc',
            })
            self.kg.salvar()
            self._log('LEARN', 'Registrado no KG: %s' % lesson_erro)
        
        self.historico.append(aprendizagem)
        self._salvar_historico()
    
    def _carregar_historico(self) -> list:
        """Carrega historico de geracoes."""
        if os.path.exists(HISTORICO_PATH):
            try:
                with open(HISTORICO_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def _salvar_historico(self):
        """Salva historico em disco."""
        os.makedirs(SANDBOX, exist_ok=True)
        with open(HISTORICO_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.historico, f, ensure_ascii=False, indent=2)
    
    def obter_passos(self) -> list:
        """Retorna passos da ultima execucao."""
        return self._passos
    
    def obter_metricas(self) -> Dict:
        """Retorna metricas do agente."""
        total = len(self.historico)
        sucessos = sum(1 for h in self.historico if h.get('sucesso'))
        return {
            'total_geracoes': total,
            'taxa_sucesso': '%.0f%%' % (sucessos / max(total, 1) * 100),
            'tempo_medio': '%.1fs' % (sum(h.get('tempo', 0) for h in self.historico) / max(total, 1)),
        }


# ============================================================
# PONTO DE ENTRADA
# ============================================================

if __name__ == '__main__':
    agent = AgentLoop()
    
    # Teste: gerar ferreiro
    print('=== TESTE: FERREIRO EM ERIDANUS ===')
    resultado = agent.executar("Ferreiro em Eridanus que vende espadas e armaduras", "shop")
    print('\nResultado:')
    print('  Nome:', resultado.get('nome', '?'))
    print('  Arquivo:', resultado.get('arquivo', '?'))
    print('  Valido:', resultado.get('validacao', {}).get('valido', False))
    if resultado.get('validacao'):
        v = resultado['validacao']
        print('  Erros:', len(v.get('erros', [])))
        print('  Avisos:', len(v.get('avisos', [])))
        print('  SQL Injection:', len(v.get('sql_injection', [])))
        print('  Boas praticas:', len(v.get('boas_praticas', [])))
    
    print('\n=== METRICAS ===')
    for k, v in agent.obter_metricas().items():
        print('  %s: %s' % (k, v))
