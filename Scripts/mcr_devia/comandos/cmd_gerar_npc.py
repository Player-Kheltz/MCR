"""Comando: gerar_npc - Gera NPCs Lua para Canary via pipeline AGI.

Pipeline completo:
1. THINK: Indexa NPCs existentes, busca exemplos similares, consulta KG
2. ACT: Gera codigo via templates + placeholders
3. OBSERVE: Valida sintaxe, SQL injection, boas praticas
4. LOOP: Auto-correcao (max 3 tentativas)
5. LEARN: Registra licao no KG e historico

Uso (JSON IPC):
  {"cmd": "gerar_npc", "args": ["Ferreiro em Eridanus"]}
  {"cmd": "gerar_npc", "args": ["Ferreiro em Eridanus", "--tipo", "shop"]}
  {"cmd": "gerar_npc", "args": ["Ferreiro em Eridanus", "--tipo", "quest"]}
  {"cmd": "gerar_npc", "args": ["--tipos"]}  # Lista tipos disponiveis
  {"cmd": "gerar_npc", "args": ["--status"]}  # Metricas do agente
"""
import os, sys, json

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia', 'modulos'))

from agent_loop import AgentLoop

SANDBOX = os.path.join(BASE, 'sandbox')

TIPOS_DISPONIVEIS = {
    'shop': 'Vende ou compra itens',
    'quest': 'Da missoes com reward',
    'bank': 'Deposito e saque de gold',
    'gate': 'Controle de acesso por level',
    'trainer': 'Ensina spells e skills',
    'dialogue': 'Dialogo com lore e dicas',
}


def init_module(contexto):
    """Inicializa modulo."""
    contexto['agent_npc'] = AgentLoop()
    return 'gerar_npc', None


def executar(args):
    """Executa o comando gerar_npc.
    
    Args:
        args: Lista de argumentos
    
    Returns:
        Dict com resultado
    """
    if not args:
        return {
            'erro': 'Uso: gerar_npc \"<descricao>\" [--tipo <tipo>] [--status] [--tipos]',
            'ajuda': True
        }
    
    # Comandos de metadados
    if args[0] == '--tipos':
        return {'tipos': TIPOS_DISPONIVEIS}
    
    if args[0] == '--status':
        agent = AgentLoop()
        return {'metricas': agent.obter_metricas(), 'historico': agent.historico}
    
    # Parse args
    descricao = args[0]
    tipo = 'shop'
    
    if '--tipo' in args:
        idx_tipo = args.index('--tipo')
        if idx_tipo + 1 < len(args):
            tipo = args[idx_tipo + 1]
    
    if tipo not in TIPOS_DISPONIVEIS:
        return {'erro': 'Tipo invalido: %s. Tipos: %s' % (tipo, ', '.join(TIPOS_DISPONIVEIS.keys()))}
    
    # Executar pipeline
    agent = AgentLoop()
    resultado = agent.executar(descricao, tipo)
    
    # Montar resposta
    resposta = {
        'nome': resultado.get('nome', '?'),
        'tipo': tipo,
        'arquivo': resultado.get('arquivo', ''),
        'valido': resultado.get('validacao', {}).get('valido', False),
        'erros': resultado.get('validacao', {}).get('erros', []),
        'avisos': resultado.get('validacao', {}).get('avisos', []),
        'sql_injection': [s['tipo'] for s in resultado.get('validacao', {}).get('sql_injection', [])],
        'boas_praticas': len(resultado.get('validacao', {}).get('boas_praticas', [])),
        'tempo': '%.1fs' % sum(h.get('tempo', 0) for h in agent.historico[-1:]) if agent.historico else '?',
        'passos': agent.obter_passos(),
        'codigo': resultado.get('codigo', ''),
    }
    
    # Salvar resposta para IPC
    resposta_path = os.path.join(SANDBOX, '.mcr_resposta.txt')
    with open(resposta_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(resposta, ensure_ascii=False, indent=2))
    
    return resposta


# ============================================================
# PONTO DE ENTRADA DIRETA
# ============================================================

if __name__ == '__main__':
    import sys
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    resultado = executar(args)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
