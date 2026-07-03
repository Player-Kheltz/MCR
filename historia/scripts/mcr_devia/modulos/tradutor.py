"""Tradutor - Traduz respostas de IA para PT-BR.
Libera as IAs para pensar na lingua nativa delas (ingles).
A traducao para PT-BR e feita apos o pensamento/geracao.

Uso:
    from modulos.tradutor import traduzir
    pt_br = traduzir(texto_em_ingles)
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from modulos.ia import IA

# Cache simples: se o texto ja foi traduzido nesta sessao, reusa
_cache = {}

def traduzir(texto, ia=None, temp=0.3, forcar=False):
    """Traduz texto para portugues brasileiro usando llama3.1:8b.
    
    Args:
        texto: str - Texto em qualquer idioma para traduzir
        ia: IA opcional - Instancia de IA (cria uma se None)
        temp: float - Temperatura (0.3 = preciso, 0.7 = criativo)
        forcar: bool - Se True, ignora cache e forc a traducao
    
    Returns:
        str - Texto traduzido para PT-BR
    """
    if not texto or not texto.strip():
        return texto
    
    # Cache: textos iguais retornam mesma traducao
    chave = hash(texto) if len(texto) > 200 else hash(texto)
    if not forcar and chave in _cache:
        return _cache[chave]
    
    if ia is None:
        ia = IA()
    
    # Detecta se tem codigo (``` blocks) - se tiver, preserva intacto
    tem_codigo = "```" in texto
    
    prompt = (
        "TRADUZA o texto abaixo para portugues brasileiro.\n"
        "Se o texto ja estiver em portugues, retorne-o como esta.\n"
        "Se estiver em ingles ou qualquer outro idioma, TRADUZA IMEDIATAMENTE.\n"
        "REGRAS:\n"
        "- Preserve nomes proprios, termos tecnicos, numeros e codigo INALTERADOS\n"
        "- Mantenha o tom e estilo do original\n"
        "- Nao invente informacoes que nao estao no texto\n"
        "- Saida: APENAS a traducao, sem comentarios, sem explicacoes\n"
    )
    if tem_codigo:
        prompt += (
            "- O texto contem blocos de codigo ```...```. Traduza APENAS o texto "
            "ao redor, deixando o codigo intacto\n"
        )
    
    prompt += f"\nTexto:\n{texto}\n\nTraducao para PT-BR:"
    
    try:
        traducao = ia.gerar(prompt, temp=temp, tarefa="texto")
        if traducao and traducao.strip():
            _cache[chave] = traducao
            return traducao
    except Exception as e:
        print(f"[Tradutor] ERRO: {e}")
    
    return texto  # fallback: retorna original

def traduzir_opinioes(opinioes, ia=None):
    """Traduz um dicionario de opinioes {nome: texto} para PT-BR.
    
    Args:
        opinioes: list of (nome, texto) tuples
        ia: IA opcional
    
    Returns:
        list of (nome, texto_traduzido) tuples
    """
    resultado = []
    for nome, opiniao in opinioes:
        traduzida = traduzir(opiniao, ia=ia)
        resultado.append((nome, traduzida))
    return resultado
