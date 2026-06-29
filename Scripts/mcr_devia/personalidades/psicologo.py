"""Personalidade Psicologo do Conselho - Nao responde a pergunta.
Monitora a saude mental do conselho: vies, contradicoes, alinhamento."""
import os, json, time
from modulos.util import fast as _fast

MEM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'sandbox', '.mcr_devia', 'memoria_personalidades')
os.makedirs(MEM_DIR, exist_ok=True)

def registrar():
    return {
        'nome': 'psicologo',
        'papel': 'psicologo',
        'especialidade': ['vies', 'contradicao', 'saude mental', 'alinhamento', 'etica'],
        'prioridade': 0,  # Sempre primeiro
    }

def pensar(pergunta, contexto='', kg=''):
    """Psicologo NAO responde a pergunta. Ele analisa o processo."""
    # Router: usa llama3.1 (texto) para analise psicologica (precisa de PT-BR natural)
    prompt = f"""PSICOLOGO DO CONSELHO - Voce NAO responde a pergunta.
Seu papel e monitorar a SAUDE MENTAL do conselho.

Pergunta sendo discutida: {pergunta}
Contexto: {contexto[:200]}

Analise:
1) Ha algum VIES na forma como a pergunta foi feita?
2) O conselho esta alinhado com os valores do projeto?
3) Ha risco de GROUPTHINK (todos concordando sem questionar)?
4) O conselho precisa de mais informacoes antes de decidir?

Responda em 2-3 frases com sua avaliacao do PROCESSO, nao da pergunta:"""
    opiniao = _fast(prompt, 0.3, 'texto') or _fast(prompt, 0.3, 'leve') or '[Psicologo] Sem observacoes'
    _memorizar(pergunta, opiniao)
    return opiniao

def _memorizar(p, o):
    try:
        with open(os.path.join(MEM_DIR, 'psicologo.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps({"ts": time.time(), "p": p[:80], "o": o[:200]}, ensure_ascii=False)+'\n')
    except: pass
