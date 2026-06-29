"""Personalidade Fixa: Critico - Riscos, falhas, pontos cegos."""
import os, json, time
from modulos.util import fast as _fast

MEM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'sandbox', '.mcr_devia', 'memoria_personalidades')
os.makedirs(MEM_DIR, exist_ok=True)

def registrar():
    return {
        'nome': 'critico',
        'papel': 'fixo',
        'especialidade': ['riscos', 'falhas', 'seguranca', 'problemas', 'limitacoes'],
        'prioridade': 2,
    }

def pensar(pergunta, contexto='', kg=''):
    # Router: se pergunta for de lore/narrativa, usa llama3.1 (texto), senao qwen (leve)
    p_lower = pergunta.lower()
    tarefa = 'texto' if any(w in p_lower for w in ['historia', 'lore', 'conto', 'personagem', 'narrativa']) else 'leve'
    prompt = f"""CRITICO - Identifique RISCOS E PROBLEMAS.
Pergunta: {pergunta}
Contexto: {contexto[:200]}
EXIJO: Riscos especificos, nao genericos. O que pode dar ERRADO?
Responda em 2-3 frases com riscos concretos:"""
    opiniao = _fast(prompt, 0.25, tarefa) or '[Critico] Sem riscos'
    _memorizar(pergunta, opiniao)
    return opiniao

def _memorizar(p, o):
    try:
        with open(os.path.join(MEM_DIR, 'critico.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps({"ts": time.time(), "p": p[:80], "o": o[:200]}, ensure_ascii=False)+'\n')
    except: pass
