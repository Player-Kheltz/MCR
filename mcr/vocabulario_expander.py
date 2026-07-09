"""mcr.vocabulario_expander — O Alimentador de Vocabulario.
Unico modulo que fala com o LLM (Ollama). Gera frases sobre um tema
e alimenta o MCR (Sistema 1). O LLM nunca ve a conversa."""
import json
import re
import urllib.request
from typing import List, Optional

OLLAMA_CHAT = "http://localhost:11434/api/generate"
MODELO = "qwen2.5-coder:7b"

# MCRCadeia para geracao estruturada (carregado sob demanda)
_MCR_CADEIA = None


def _get_cadeia():
    global _MCR_CADEIA
    if _MCR_CADEIA is not None:
        return _MCR_CADEIA
    try:
        import sys as _sys
        from pathlib import Path as _P
        _sys.path.insert(0, str(_P(__file__).parent.parent / 'devia' / 'kernel'))
        import MCR as _M
        if not hasattr(_M, 'MCRBridge'):
            class _MB:
                def __init__(self): self._descobriu = True
                def descobrir(self): return {'modulos': 48, 'comandos': 52}
            _M.MCRBridge = _MB
        from MCR import MCRCadeia, MCRConector
        _MCR_CADEIA = MCRCadeia(MCRConector())
    except Exception as e:
        _MCR_CADEIA = False  # Marca como falha permanente
    return _MCR_CADEIA


def expandir(tema: str) -> List[str]:
    """Gera frases sobre um tema para alimentar o vocabulario do MCR.
    
    O LLM nunca ve a conversa. So recebe um tema e gera frases.
    
    Returns:
        Lista de strings (cada uma e uma frase).
    """
    if not tema or not tema.strip():
        return []

    prompt = (
        "Gere 20 frases curtas e variadas em portugues sobre o tema '%s'.\n"
        "Escreva em primeira pessoa.\n"
        "Nao use linguagem de assistente. Seja direto.\n"
        "Cada frase deve ser autonoma e significar algo completo.\n"
        "Separe cada frase por uma nova linha.\n"
        "Nao numerar. Nao usar marcadores.\n"
        "So as frases, sem introducao.\n\n"
        "Frases:" % tema
    )

    try:
        payload = json.dumps({
            "model": MODELO,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.8, "max_tokens": 500}
        }).encode()
        req = urllib.request.Request(OLLAMA_CHAT, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
        texto = resp.get('response', '').strip()
    except Exception as e:
        print('[VocabExpander] Erro no Ollama: %s' % e)
        return []

    if not texto:
        return []

    # Divide em frases
    # Tenta separar por newline primeiro, depois por ponto
    frases_brutas = texto.split('\n')
    frases = []
    for f in frases_brutas:
        f = f.strip()
        # Remove numeracao ou marcadores
        f = re.sub(r'^\d+[\.\)]\s*', '', f)
        f = re.sub(r'^[\-\*]\s*', '', f)
        f = re.sub(r'^["\'](.*)["\']$', r'\1', f)
        if f and len(f) > 10 and len(f) < 300:
            frases.append(f)

    # Se nao conseguiu separar por newline, tenta por ponto
    if len(frases) < 3:
        frases_brutas = texto.split('.')
        for f in frases_brutas:
            f = f.strip()
            if f and len(f) > 10:
                frases.append(f + '.')

    # Remove duplicatas mantendo ordem
    vistas = set()
    unicas = []
    for f in frases:
        chave = f.lower().strip()
        if chave not in vistas:
            vistas.add(chave)
            unicas.append(f)

    print('[VocabExpander] %d frases geradas sobre "%s"' % (len(unicas), tema))
    return unicas


def _alimentar_mcr(mcr_system, frases: List[str], tema: str) -> int:
    """Alimenta o MCR com as frases geradas. Chame apos expandir()."""
    if not mcr_system or not hasattr(mcr_system, 'mk_palavra') or not frases:
        return 0

    count = 0
    for frase in frases:
        palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', frase.lower())
        if len(palavras) < 2:
            continue
        # Alimenta bigramas
        for i in range(len(palavras) - 1):
            try:
                for _ in range(3):  # Reforco
                    mcr_system.mk_palavra.aprender(palavras[i], palavras[i + 1])
                count += 1
            except Exception:
                pass
        # Alimenta tema -> primeira palavra (reforco de contexto)
        try:
            for _ in range(5):
                mcr_system.mk_palavra.aprender(tema.lower(), palavras[0])
        except Exception:
            pass

    return count
