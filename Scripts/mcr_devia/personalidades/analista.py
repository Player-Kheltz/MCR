"""Personalidade Fixa: Analista - Adaptativo ao tipo de pergunta."""
import os, json, time
from modulos.util import fast as _fast

MEM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'sandbox', '.mcr_devia', 'memoria_personalidades')
os.makedirs(MEM_DIR, exist_ok=True)

def registrar():
    return {
        'nome': 'analista',
        'papel': 'fixo',
        'especialidade': ['dados', 'metricas', 'fatos', 'logica', 'analise'],
        'prioridade': 1,
    }

def pensar(pergunta, contexto='', kg='', tipo='estrategico'):
    kg_info = kg[:1500] if kg else ''
    header = ("CONTEXTO DO PROJETO MCR: MCR = servidor de Tibia (Canary). "
              "SPA = Sistema de Progressao do Aventureiro. "
              "SHC = Sistema de Habilidades Contextuais. "
              "Eridanus = cidade inicial.\n")
    # Prompt ADAPTATIVO ao tipo de pergunta
    # Router: narrativa usa llama3.1 (texto), tecnico/estrategico usa qwen (leve)
    tarefa_router = 'texto' if tipo == 'narrativa' else 'leve'
    prompts = {
        'narrativa': f"""{header}ANALISTA (modo narrativa) - Verifique a CONSISTENCIA da historia.
KG: {kg_info}
Pergunta: {pergunta}
EXIJO: Analise se a historia e consistente com o lore existente do projeto. 
Aponte fatos do KG que corroboram ou contradizem. Responda com dados concretos (2-3 frases):""",
        'tecnico': f"""{header}ANALISTA (modo tecnico) - DADOS e METRICAS.
KG: {kg_info}
Pergunta: {pergunta}
EXIJO: Numeros, metricas, dados especificos do KG. Performance, versoes, licoes.
Responda com FATOS CONCRETOS (2-3 frases):""",
        'estrategico': f"""{header}ANALISTA (modo estrategico) - FATOS E DADOS.
KG: {kg_info}
Pergunta: {pergunta}
EXIJO: Dados concretos, metricas, evidencias. Nada generico.
Responda com FATOS DO PROJETO (2-3 frases):""",
    }
    prompt = prompts.get(tipo, prompts['estrategico'])
    opiniao = _fast(prompt, 0.15, tarefa_router) or '[Analista] Sem dados'
    _memorizar(pergunta, opiniao)
    return opiniao

def _memorizar(p, o):
    try:
        with open(os.path.join(MEM_DIR, 'analista.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps({"ts": time.time(), "p": p[:80], "o": o[:200]}, ensure_ascii=False)+'\n')
    except: pass
