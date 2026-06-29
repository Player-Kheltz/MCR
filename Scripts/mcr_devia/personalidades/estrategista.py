"""Personalidade Fixa: Estrategista - Visao geral, planejamento, direcao."""
import os, json, time
from modulos.util import gerar as _gerar, fast as _fast

MEM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'sandbox', '.mcr_devia', 'memoria_personalidades')
os.makedirs(MEM_DIR, exist_ok=True)

def registrar():
    return {
        'nome': 'estrategista',
        'papel': 'fixo',
        'especialidade': ['visao', 'planejamento', 'direcao', 'roadmap', 'estrategia'],
        'prioridade': 3,
    }

def pensar(pergunta, contexto='', kg=''):
    prompt = f"""ESTRATEGISTA - Visao geral e planejamento estrategico.
Pergunta: {pergunta}
Contexto: {contexto[:300]}
KG: {kg[:500]}

EXIJO: Analise o panorama geral. Qual a melhor direcao a seguir?
Considere: curto prazo (agora), medio prazo (proximas semanas), longo prazo (proximos meses).
Responda com uma recomendacao estrategica concreta (2-3 frases):"""
    opiniao = _gerar(prompt, 0.3, 'pesado') or _fast(prompt, 0.3, 'leve') or '[Estrategista] Sem visao'
    _memorizar(pergunta, opiniao)
    return opiniao

def _memorizar(p, o):
    try:
        with open(os.path.join(MEM_DIR, 'estrategista.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps({"ts": time.time(), "p": p[:80], "o": o[:200]}, ensure_ascii=False)+'\n')
    except: pass
