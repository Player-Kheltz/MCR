"""Mente do MCR-DevIA — Pensamento antes da acao.
OTIMIZADO: batch (1 chamada), cache (reuso), modelo leve (1.5b).

Cache: deliberacoes sao reusadas por 5 min para mesma categoria.
Batch: todos os membros em UMA unica chamada IA.
Leve: qwen2.5-coder:1.5b para perspectivas, sem perder qualidade.

Analogia humana:
- MENTE = Conselho + memorias + deliberacao + cache
- CORPO = Orquestrador + templates + execucao
"""
import os, json, time, urllib.request
from functools import lru_cache

from modulos import memoria_conselho as _memoria

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
_MODELO_MENTE = "qwen2.5-coder:1.5b"  # Modelo leve e RAPIDO para perspectivas

# Cache: (tipo, subtipo) -> (timestamp, mente_contexto)
_CACHE_MENTE = {}
_CACHE_TTL = 300  # 5 minutos
_CACHE_MAX = 32

# Mapa: tipo de tarefa -> membros relevantes
_TASK_MEMBROS = {
    "codigo": {
        "analisar": ["analista", "critico", "revisor_codigo"],
        "corrigir": ["analista", "critico", "revisor_codigo", "tecnico"],
        "gerar": ["analista", "arquiteto", "tecnico"],
        "refatorar": ["analista", "critico", "revisor_codigo", "arquiteto"],
    },
    "planejamento": {
        "arquitetura": ["analista", "estrategista", "arquiteto", "critico"],
    },
    "diagnostico": {
        "causa_raiz": ["analista", "critico", "tecnico", "especialista"],
    },
    "conceitual": {
        "explicacao": ["analista", "estrategista", "psicologo"],
    },
    "criacao": {
        "historia": ["contador_historias", "psicologo", "estrategista"],
    },
    "factual": {
        "definicao": ["analista"],
        "dado": ["analista"],
    },
    "desconhecido": {
        "geral": ["analista", "estrategista"],
    },
}
_MEMBROS_PADRAO = ["analista", "critico", "estrategista"]

def _get_membros(tipo, subtipo):
    if tipo in _TASK_MEMBROS and subtipo in _TASK_MEMBROS[tipo]:
        return _TASK_MEMBROS[tipo][subtipo]
    return _MEMBROS_PADRAO

def _llm_leve(prompt, temp=0.2):
    """Chamada ultra-rapida ao modelo leve 1.5b."""
    try:
        d = json.dumps({
            "model": _MODELO_MENTE, "prompt": prompt, "stream": False,
            "options": {"temperature": temp, "num_ctx": 2048, "num_predict": 1024}
        }).encode()
        r = urllib.request.Request(OLLAMA_URL, data=d,
            headers={"Content-Type": "application/json"})
        resp = json.loads(urllib.request.urlopen(r, timeout=30).read())
        return (resp.get("response") or "").strip()
    except Exception:
        return ""

def think(pergunta, tipo="desconhecido", subtipo="geral", kg=None, ia=None, ctx_crew=None):
    """Mente pensa: batch + cache.
    Cache: mesma (tipo, subtipo) reusa deliberacao por 5 min.
    Batch: todos os membros em UMA chamada IA.
    Leve: modelo 1.5b para velocidade."""
    
    if tipo == "factual" or (tipo == "desconhecido" and subtipo == "geral"):
        return ""
    
    membros = _get_membros(tipo, subtipo)
    cache_key = (tipo, subtipo, tuple(membros))
    
    # Verifica cache com revisao V12 + Fast
    agora = time.time()
    if cache_key in _CACHE_MENTE:
        ts_cache, ctx_cache = _CACHE_MENTE[cache_key]
        if agora - ts_cache < _CACHE_TTL:
            # Revisao rapida: o cache ainda e relevante para esta pergunta?
            # Usa _llm_leve (1.5b, 1-2s) para verificar se a deliberacao cacheada
            # ainda faz sentido para a nova pergunta
            prompt_revisao = (
                f"Cache de deliberacao do conselho:\n{ctx_cache[:500]}\n\n"
                f"Nova pergunta: {pergunta[:300]}\n\n"
                f"Esta deliberacao e relevante para esta pergunta?\n"
                f"Responda apenas: SIM ou NAO"
            )
            revisao = _llm_leve(prompt_revisao, 0.1)
            if 'SIM' in revisao.upper() and 'NAO' not in revisao.upper():
                print(f'  [Mente] Cache HIT ({tipo}/{subtipo}) — revisado e aprovado')
                return ctx_cache
            else:
                print(f'  [Mente] Cache INVALIDO ({tipo}/{subtipo}) — regenerando')
                # Remove cache invalido
                del _CACHE_MENTE[cache_key]
    
    print(f'  [Mente] Pensando... membros: {membros} (batch 1 chamada)')
    t0 = time.time()
    
    # CONTEXT REINFORCER: valida contexto antes de carregar memorias
    cr_instrucao = ""
    try:
        from modulos.context_reinforcer import ContextReinforcer
        cr = ContextReinforcer()
        cr_result = cr.reforcar(pergunta)
        if cr_result.get("instrucao"):
            cr_instrucao = cr_result["instrucao"]
        if cr_result.get("contexto") and not cr_result.get("valido") and cr_result.get("aprendeu"):
            print(f"  [Mente] CR: weblearn disparado - memorias podem ser fracas")
    except Exception as e:
        print(f"  [Mente] CR ERRO: {e}")
    
    # Monta prompt BATCH com todos os membros + suas MELHORES memorias (aprendizado)
    blocos_memoria = []
    for nome in membros:
        # Carrega memorias de ALTO SCORE primeiro (aprendizado real)
        memoria = _memoria.resumo_para_prompt(nome, max_entradas=5)
        blocos_memoria.append(f"MEMBRO: {nome.upper()}\nMEMORIA: {memoria}")
    
    prompt_batch = (
        f"Conselho do MCR-DevIA discutindo a pergunta abaixo.\n"
        f"Cada membro tem sua memoria pessoal (score alto = aprendeu muito).\n\n"
        f"PERGUNTA: {pergunta[:400]}\n\n"
        + (cr_instrucao + "\n" if cr_instrucao else "")
        + f"{chr(10).join(blocos_memoria)}\n\n"
        f"Com base na MEMORIA de cada um, qual a perspectiva de CADA membro?\n"
        f"Priorize padroes que tiveram score alto no passado.\n"
        f"Formato:\n"
        f"[NOME]\nperspectiva\n\n"
        f"Seja conciso (2-4 frases por membro)."
    )
    
    resposta = _llm_leve(prompt_batch)
    
    if not resposta or len(resposta) < 30:
        print(f'  [Mente] Sem resposta do modelo leve')
        return ""
    
    mente_contexto = f"[MENTE - DELIBERACAO]\n{resposta[:3000]}"
    
    # Salva nas memorias individuais (com score inicial 50)
    for nome in membros:
        _memoria.salvar(nome, pergunta[:100], resposta[:200],
                      padrao=f"batch: {pergunta[:50]}", categoria=tipo, score=50)
    
    # Atualiza cache (LRU simples)
    _CACHE_MENTE[cache_key] = (agora, mente_contexto)
    if len(_CACHE_MENTE) > _CACHE_MAX:
        mais_antiga = min(_CACHE_MENTE.keys(), key=lambda k: _CACHE_MENTE[k][0])
        del _CACHE_MENTE[mais_antiga]
    
    tempo = round(time.time() - t0, 1)
    print(f'  [Mente] OK ({tempo}s) — {len(resposta)} chars (batch, cache + aprendizado)')
    
    return mente_contexto

def learn(pergunta, tipo, subtipo, resposta, kg=None):
    """Apos execucao, AUTOAVALIA a qualidade e atualiza scores das memorias.
    
    Ciclo de aprendizado:
    1. Avalia qualidade da resposta (tamanho, codigo, estrutura)
    2. Atualiza score de cada membro baseado na qualidade
    3. Registra no KG para consultas futuras
    """
    membros = _get_membros(tipo, subtipo)
    
    # AUTOAVALIACAO: calcula score baseado em metricas objetivas
    score = 50  # neutro
    import re as _re
    
    if resposta:
        # Mais codigo = mais util (para tarefas de codigo)
        blocos = _re.findall(r'```(?:python)?\s*\n(.*?)```', resposta, _re.DOTALL)
        linhas_codigo = sum(len(b.split('\n')) for b in blocos)
        if linhas_codigo > 20:
            score += 10
        if linhas_codigo > 50:
            score += 10
        
        # Mais secoes = mais completa
        secoes = _re.findall(r'\[ \] [A-Z]+', resposta)
        if len(secoes) >= 3:
            score += 10
        if len(secoes) >= 5:
            score += 10
        
        # Sem erros de sintaxe = maior qualidade
        erros = 0
        for b in blocos:
            try:
                compile(b.strip(), '<test>', 'exec')
            except Exception:
                erros += 1
        if erros == 0 and blocos:
            score += 10
        elif erros > 3:
            score -= 10
        
        # Tamanho minimo aceitavel
        if len(resposta) < 500:
            score -= 20
        elif len(resposta) > 2000:
            score += 10
    
    score = max(0, min(100, score))
    
    # Atualiza score da ULTIMA entrada de cada membro (feedback loop)
    for nome in membros:
        _memoria.avaliar(nome, pergunta[:100], score, 
                        f"autoavaliacao: score={score}, codigo={linhas_codigo if resposta else 0}")
    
    if kg:
        try:
            kg.aprender(f"mente: {pergunta[:80]}",
                       f"tipo={tipo}, subtipo={subtipo}",
                       f"membros={membros}, score={score}, size={len(resposta or '')}",
                       f"mente_{tipo}")
        except Exception:
            pass
