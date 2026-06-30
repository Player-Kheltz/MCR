"""Comando: perguntar - V12 Contexto Agregado + Roteador Inteligente Universal."""
import os, sys

# Le identidade do projeto (se disponivel)
_IDENTIDADE = ""
_ID_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        '..', '..', 'docs', 'MCR_IDENTITY.md')
try:
    if os.path.exists(_ID_PATH):
        with open(_ID_PATH, 'r', encoding='utf-8') as f:
            _IDENTIDADE = f.read().strip()
except:
    pass

def register():
    return {
        "name": "perguntar",
        "desc": "Responde perguntas usando roteador inteligente: V12, Orquestrador, ou IA direta. Detecta automaticamente se e codigo, criacao, diagnostico, etc.",
        "handler": execute,
        "args": [{"name": "pergunta", "type": "str", "required": True}],
        "categoria": "ia",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args:
        print('[Perguntar] Uso: perguntar <pergunta>')
        return True
    
    texto = ' '.join(args)
    identidade = _IDENTIDADE or ""
    
    # Tenta Supervisor com Orquestrador (roteador inteligente)
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modulos'))
        from supervisor import Supervisor
        from orquestrador import Orquestrador
        
        # Cria Orquestrador com contexto do projeto
        orq = Orquestrador(kg=kg, ia=ia, ctx_crew=ctx_crew)
        
        # Supervisor com acesso ao Orquestrador + identidade
        sup = Supervisor(ia, kg, ctx_crew=ctx_crew,
                        orquestrador=orq,
                        identidade=identidade)
        resposta = sup.perguntar(texto)
        if resposta:
            # Salva resposta completa em arquivo para consulta
            try:
                _rp = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   '..', '..', 'sandbox', '.mcr_resposta.txt')
                with open(_rp, 'w', encoding='utf-8') as _f:
                    _f.write(resposta)
            except:
                pass
            print(f'\n{resposta}')
            if kg:
                kg.aprender(texto, f'perguntou: {texto}', resposta, 'v12_genero')
            return True
    except ImportError as e:
        print(f'[Perguntar] Supervisor indisponivel: {e}')
    except Exception as e:
        print(f'[Perguntar] ERRO: {e}')
    
    # Fallbacks removidos — o pipeline ReAct no Kernel é o fluxo principal agora
    return True
