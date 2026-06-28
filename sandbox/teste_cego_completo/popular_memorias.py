#!/usr/bin/env python3
"""Popula as memorias individuais dos membros do conselho com lessons reais do KG.
Cada membro recebe lessons relevantes a sua especialidade.

Mapeamento:
- analista: fatos, metricas, versoes, numeros
- critico: riscos, problemas, erros, falhas
- estrategista: planejamento, roadmap, decisoes
- arquiteto: design, arquitetura, componentes
- contador_historias: lore, nomes, personagens, lugares
- psicologo: vieses, processo, dinâmica
- revisor_codigo: bugs, code review, problemas tecnicos
- tecnico: implementacao, comandos, ferramentas
- especialista: conhecimento profundo, dominios
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'mcr_devia'))
from modulos import memoria_conselho as _memoria

# Mapeamento: categoria KG -> lista de membros que recebem a lesson
CATEGORIA_MEMBROS = {
    "bugfix": ["analista", "revisor_codigo", "tecnico"],
    "seguranca": ["critico", "revisor_codigo"],
    "sessao": ["analista", "estrategista"],
    "runtime": ["analista", "tecnico"],
    "feature": ["estrategista", "arquiteto", "tecnico"],
    "v12_genero": ["analista", "psicologo"],
    "conceito_codigo": ["analista", "tecnico", "especialista"],
    "identidade": ["analista", "estrategista", "psicologo"],
    "weblearn": ["analista", "estrategista"],
    "geral": ["analista"],
    "teste_cego": ["analista", "critico", "estrategista"],
    "conselho": ["psicologo", "estrategista"],
}

def popular():
    """Le o KG e popula as memorias."""
    kg_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sandbox', '.mcr_devia', 'knowledge.json')
    
    if not os.path.exists(kg_path):
        print(f'KG nao encontrado em: {kg_path}')
        return
    
    with open(kg_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    licoes = data.get('licoes', [])
    print(f'KG: {len(licoes)} lessons encontradas')
    
    contadores = {nome: 0 for nome in _memoria.MEMBROS}
    
    for l in licoes[:200]:  # Limite de 200 lessons para nao poluir
        ctx = l.get('ctx', 'geral')
        erro = l.get('erro', '')
        solucao = l.get('solucao', '')
        if not erro or not solucao:
            continue
        
        # Determina quais membros recebem esta lesson
        membros_alvo = CATEGORIA_MEMBROS.get(ctx, ["analista"])
        
        for nome in membros_alvo:
            if contadores[nome] >= 30:
                continue  # Limite de 30 entradas por membro
            
            _memoria.salvar(
                nome,
                erro[:100],
                solucao[:300],
                padrao=f"[{ctx}] {erro[:80]}",
                categoria=ctx
            )
            contadores[nome] += 1
    
    print("\nMemorias populadas:")
    for nome, total in contadores.items():
        print(f"  {nome}: {total} entradas")
    
    # Estatisticas finais
    stats = _memoria.estatisticas()
    print("\nTotal por membro:")
    for nome, s in stats.items():
        print(f"  {nome}: {s['total']} entradas, categorias={s['categorias'][:5]}")

if __name__ == "__main__":
    popular()
