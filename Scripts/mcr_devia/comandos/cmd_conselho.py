"""Comando: conselho - Conselho V7 para respostas inteligentes."""
import os, sys, time, json

def register():
    return {
        "name": "conselho",
        "desc": "Conselho V7: resposta inteligente com personalidades + auto-revisao",
        "handler": execute,
        "args": [{"name": "pergunta", "type": "str", "required": True}],
        "categoria": "ia",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[Conselho] Uso: conselho <pergunta>')
        return True
    
    pergunta = ' '.join(args)
    
    # Importa e executa Conselho V7
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    try:
        from modulos.conselho import Conselho
        import context_crew as _cc
        ctx = _cc.ContextCrew()
        
        c = Conselho(kg=kg, ia=ia, ctx_crew=ctx)
        r = c.deliberar(pergunta)
        veredito = r.get('veredito', 'Sem resposta')
        print(veredito)
        
        # Registra no KG SOMENTE se a resposta parece valida (evita poluir KG com alucinacoes)
        if kg:
            # Validacao simples: detectar alucinacoes comuns
            veredito_lower = veredito.lower()
            alucinou = any(termo in veredito_lower for termo in [
                'single page application', 'minecraft', 'mundo criativo real',
                'microserviço', 'microservicos', 'docker', 'kubernetes', 'aws',
                'wow', 'world of warcraft', 'd&d', 'dungeons and dragons',
                'react', 'vue.js', 'angular', 'node.js', 'nodejs',
                'api rest', 'restful', 'cloud computing',
            ])
            if not alucinou and len(veredito) > 100:
                kg.aprender(f"Pergunta: {pergunta[:80]}",
                           f"Conselho V7 com {r.get('personalidades', 0)} personalidades",
                           veredito[:500], 'conceito_projeto')
            else:
                print(f'  [Conselho] Resposta NAO registrada no KG (deteccao de alucinacao ou muito curta)')
    except Exception as e:
        print(f'[Conselho] ERRO: {e}')
        # Fallback: V12
        if kg:
            ctx = kg.buscar(pergunta, max_r=3)
            if ctx:
                for l in ctx[:2]:
                    print(l.get('solucao', '')[:300])
                    return True
        print('Nao foi possivel responder.')
    
    return True
