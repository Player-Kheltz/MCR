"""Personalidade Honoraria: Contador de Historias - Lore, narrativa, criatividade."""
import os, json, time
from modulos.util import gerar as _gerar, fast as _fast

MEM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'sandbox', '.mcr_devia', 'memoria_personalidades')
os.makedirs(MEM_DIR, exist_ok=True)

def registrar():
    return {
        'nome': 'contadordehistorias',
        'papel': 'honorario',
        'especialidade': ['lore', 'narrativa', 'criatividade', 'historias', 'worldbuilding'],
        'prioridade': 5,
    }

def pensar(pergunta, contexto='', kg=''):
    prompt = f"""CONTADOR DE HISTORIAS DO MCR-DEVIA - Crie LORE RICA E DETALHADA.
Pergunta: {pergunta}
Contexto: {contexto[:200]}
Inspiracao KG: {kg[:300]}

EXIJO: Nomes proprios de personagens, lugares, artefatos, eventos historicos.
Crie uma historia com: fundacao, era de ouro, declinio, situacao atual.
Use nomes UNICOS e ORIGINAIS. Seja vivido e especifico.
Responda em 3-4 frases:"""
    opiniao = _gerar(prompt, 0.85, 'texto') or _fast(prompt, 0.7, 'texto') or '[Contador] Sem historia'
    _memorizar(pergunta, opiniao)
    return opiniao

def _memorizar(p, o):
    try:
        with open(os.path.join(MEM_DIR, 'contadordehistorias.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps({"ts": time.time(), "p": p[:80], "o": o[:200]}, ensure_ascii=False)+'\n')
    except: pass
