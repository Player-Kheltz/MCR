"""KGCleaner — Marca lessons poluentes como inactive no startup.

Lessons poluentes sao auto-geradas pelo pipeline e nao representam
conhecimento conceitual. Elas poluem o KG Weaver (que encontra
lessons por fingerprint) e devem ser marcadas como inactive.

Categorias de lessons a manter (NAO sao poluentes):
  - conceito: definicoes e conceitos do projeto
  - arquitetura, refatoracao: licoes de arquitetura
  - correcoes_externas, decomp_recursiva: licoes uteis
  - auto_melhoria: auto-melhorias registradas
"""
import os, sys, json
from collections import Counter

# Categorias que DEVEM ser mantidas (nao marcar como inactive)
_CATEGORIAS_MANTER = {
    'conceito', 'arquitetura', 'refatoracao', 'auto_melhoria',
    '10_10', 'auto_revisor', 'correcoes_externas', 'decomp_recursiva',
    'dashboard_sse', 'emergir_v4', 'entropia_normal', 'fase2_turbo',
    'fenix_unificacao', 'fragmentacao_v3', 'gatekeeper', 'infra',
    'legacy_rescue', 'mente_multimodal', 'planejamento',
    'pipeline_completa', 'sessao_completa', 'teste_10_10',
    'v12_genero', 'veritas', 'veritas_v2', 'weaver_v2',
    'anti_hardcoded', 'combinador_v2',
}

# Categorias que SAO poluentes (serao marcadas como inactive)
_CATEGORIAS_POLUENTES = {
    'resposta_llm', 'resposta_tool', 'resposta_kg', 'resposta_pi',
    'resposta_react', 'resposta_fallback',
    'runtime', 'self_knowledge', 'sugestao_melhoria',
    'emergente', 'super_test', 'compilar', 'exec_projeto',
    'teste_ctx',
}


def limpar(kg=None, verbose=True):
    """Limpa lessons poluentes do KG. Roda no startup.
    
    Args:
        kg: Instancia de KnowledgeGraph. Se None, cria uma.
        verbose: Se True, imprime relatorio.
    Returns:
        (total_marcadas, total_ativas_restantes)
    """
    if kg is None:
        from modulos.kg import KnowledgeGraph
        kg = KnowledgeGraph()
    
    licoes = kg._get_licoes()
    total_antes = len(licoes)
    ativas_antes = sum(1 for l in licoes if not l.get('inactive'))
    
    marcadas = 0
    ctx_antes = Counter(l.get('ctx', 'sem_ctx') for l in licoes if not l.get('inactive'))
    
    for l in licoes:
        if l.get('inactive'):
            continue
        ctx = l.get('ctx', '')
        if ctx in _CATEGORIAS_POLUENTES:
            l['inactive'] = True
            marcadas += 1
        elif ctx not in _CATEGORIAS_MANTER and ctx not in _CATEGORIAS_POLUENTES:
            # Se nao esta em nenhuma lista, verifica pelo nome da lesson
            erro = str(l.get('erro', ''))
            sol = str(l.get('solucao', ''))
            # Lessons muito curtas ou com resultado de comando = poluente
            if 'resultado: True' in sol or 'resultado: False' in sol:
                l['inactive'] = True
                marcadas += 1
            # Lessons de auto-conhecimento com JSON enorme
            elif erro.startswith('Auto-conhecimento:') or erro.startswith('Sugestao de melhoria:'):
                l['inactive'] = True
                marcadas += 1
    
    # Salva alteracoes (salvar() le as licoes modificadas internamente)
    kg.salvar()
    
    ativas_depois = sum(1 for l in licoes if not l.get('inactive'))
    
    if verbose:
        print(f'  [KGCleaner] {marcadas} lessons marcadas como inactive')
        print(f'  [KGCleaner] {ativas_antes} -> {ativas_depois} ativas ({total_antes} total)')
    
    return marcadas, ativas_depois


def executar():
    """Entry point para chamada externa."""
    return limpar(verbose=True)


if __name__ == '__main__':
    executar()
