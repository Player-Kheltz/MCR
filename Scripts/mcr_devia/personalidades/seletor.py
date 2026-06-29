"""Seletor de ferramentas - Escolhe a melhor ferramenta para cada pergunta."""
import re

def classificar(pergunta):
    """Classifica a pergunta e retorna a melhor ferramenta para responder.
    
    Retorna: (tipo, ferramenta, confianca)
    """
    p = pergunta.lower()
    
    # CODIGO: perguntas sobre programacao, debug, implementacao
    if any(w in p for w in ['codigo', 'funcao', 'classe', 'metodo', 'bug', 'erro',
                            'python', 'lua', 'cpp', 'implementar', 'programar',
                            'compilar', 'sintaxe', 'log', 'stack trace']):
        return ('codigo', 'analisar', 0.9)
    
    # LORE/CRIATIVO: historias, personagens, narrativa
    if any(w in p for w in ['historia', 'conto', 'lore', 'narrativa', 'personagem',
                            'criativo', 'inventar', 'imaginar', 'mitologia',
                            'era', 'reino', 'batalha', 'heroi']):
        return ('criativo', 'conselho', 0.9)
    
    # ARQUITETURA/SISTEMA: design, estrutura, planejamento
    if any(w in p for w in ['arquitetura', 'sistema', 'infra', 'servidor', 'rede',
                            'banco', 'dados', 'design', 'estrutura', 'componente',
                            'distribuido', 'escalabilidade', 'performance']):
        return ('tecnico', 'conselho', 0.9)
    
    # FATOS/KG: perguntas factuais sobre o projeto MCR
    if any(w in p for w in ['o que e', 'quem', 'quando', 'onde', 'como funciona',
                            'significa', 'definicao', 'conceito', 'o que sao',
                            'quanto', 'qual a diferenca']):
        return ('factual', 'perguntar', 0.8)
    
    # ESTRATEGIA: planejamento, decisoes, riscos
    if any(w in p for w in ['estrategia', 'planejar', 'plano', 'projeto', 'migrar',
                            'prioridade', 'risco', 'decisao', 'qual o melhor',
                            'deveriamos', 'recomenda']):
        return ('estrategia', 'conselho', 0.8)
    
    # GENERICO: qualquer outra coisa - usa conselho com contexto
    return ('generico', 'conselho', 0.6)
