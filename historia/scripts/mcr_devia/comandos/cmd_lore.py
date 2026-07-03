"""Comando: lore - Gera lore PT-BR usando Orquestrador Universal (prompt gerado sob demanda)."""
import os, sys, json, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.util import BASE as _BASE, SANDBOX as _SANDBOX

def register():
    return {
        "name": "lore",
        "desc": "Gera lore PT-BR usando Orquestrador Universal (prompt sob demanda)",
        "handler": execute,
        "args": [],
        "categoria": "comando",
    }

def execute(kg, ia, args, ctx_crew=None):
    """Uso: lore <topico> [detalhes]
    Gera texto narrativo/lore em PT-BR. Usa Orquestrador para gerar prompt
    com contexto do ContextCrew + ContextInfinity + KG.
    """
    topico = args[0]
    detalhes = ' '.join(args[1:]) if len(args) > 1 else ''
    
    # Orquestrador Universal: gera o prompt sob demanda
    from modulos.orquestrador import Orquestrador
    orq = Orquestrador(kg=kg, ia=ia, ctx_crew=ctx_crew)
    
    params = {"topico": topico}
    if detalhes:
        params["detalhes"] = detalhes
    
    resultado = orq.executar("lore", params, consulta=topico, temp=0.8)
    
    if resultado["sucesso"]:
        resposta = resultado["resposta"]
        print(f"\n--- Lore: {topico} ---\n{resposta}\n")
        salvar_path = os.path.join(_SANDBOX, f"lore_{topico.replace(' ', '_')}.txt")
        with open(salvar_path, 'w', encoding='utf-8') as f:
            f.write(resposta)
        print(f"[Lore] Salvo em: {salvar_path}")
    else:
        print(f"[Lore] Falhou: {resultado.get('erro', 'desconhecido')}")
    return True
