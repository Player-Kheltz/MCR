"""Personalidade Fixa: Arquiteto - Design, estrutura, componentes, sistemas."""
import os, json, time
from modulos.util import gerar as _gerar, fast as _fast

MEM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'sandbox', '.mcr_devia', 'memoria_personalidades')
os.makedirs(MEM_DIR, exist_ok=True)

def registrar():
    return {
        'nome': 'arquiteto',
        'papel': 'fixo',
        'especialidade': ['design', 'estrutura', 'componentes', 'sistemas', 'arquitetura'],
        'prioridade': 4,
    }

def pensar(pergunta, contexto='', kg=''):
    prompt = f"""ARQUITETO - Design de sistemas, componentes e estrutura.
Pergunta: {pergunta}
Contexto: {contexto[:300]}
KG: {kg[:500]}

EXIJO: Analise a arquitetura envolvida. Como os componentes se relacionam?
Que padroes de design se aplicam? Aponte problemas estruturais e solucoes.
Responda com uma analise arquitetural concreta (2-3 frases):"""
    opiniao = _gerar(prompt, 0.3, 'pesado') or _fast(prompt, 0.3, 'leve') or '[Arquiteto] Sem analise'
    _memorizar(pergunta, opiniao)
    return opiniao

def _memorizar(p, o):
    try:
        with open(os.path.join(MEM_DIR, 'arquiteto.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps({"ts": time.time(), "p": p[:80], "o": o[:200]}, ensure_ascii=False)+'\n')
    except: pass
