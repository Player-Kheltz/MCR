"""Dominio TEXTO — PipelineUniversal.

Tokenizer: split() em palavras (MCR nivel 'palavra').
Validator: MCR entropia da sequencia.
Builder: salva como .txt.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def tokenizer(texto: str):
    """Tokeniza texto: palavras."""
    if isinstance(texto, str):
        return texto.split()
    if isinstance(texto, list):
        # Se for lista de textos, pegar o primeiro
        return texto[0].split() if texto else ['vazio']
    return [str(texto)]


def validator(sequencia: list) -> dict:
    """Valida sequencia de palavras: score = 1 se gerou algo, 0 se vazio."""
    if not sequencia:
        return {'score': 0.0}
    return {'score': min(1.0, len(set(sequencia)) / max(len(sequencia), 1))}


def builder(sequencia: list, path: str):
    """Salva sequencia como .txt."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(' '.join(sequencia))


def loader(dados: str):
    """Carrega texto."""
    return dados


DOMINIO = {
    'tokenizer': tokenizer,
    'validator': validator,
    'builder': builder,
    'descricao': 'Texto — palavras como tokens',
}
