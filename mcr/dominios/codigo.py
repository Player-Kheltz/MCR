"""Dominio CODIGO — PipelineUniversal.

Tokenizer: raw_token_set (do mcr-universal, sem parser).
Validator: entropia + estado.
Builder: salva como .txt.
"""
import sys
sys.path.insert(0, r'E:\MCR')
sys.path.insert(0, r'E:\MCR\prototypes\mcr-universal')


def tokenizer(codigo: str) -> list:
    """Tokeniza codigo: usa delimitadores universais, preserva ordem."""
    import re
    delim = re.compile(r'[\s{}();.,:\[\]"\'' + "'" + r'`/\\#<>!=+\-*%&|^~@?]+')
    if isinstance(codigo, str):
        tokens = delim.split(codigo)
        return [t.strip().lower() for t in tokens if t.strip()]
    return [str(codigo)]


def validator(sequencia: list) -> dict:
    """Valida codigo: score baseado em entropia e tokens."""
    if not sequencia:
        return {'score': 0.0}
    unicos = len(set(sequencia))
    return {'score': min(1.0, unicos / max(len(sequencia), 1))}


def builder(sequencia: list, path: str):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sequencia))


DOMINIO = {
    'tokenizer': tokenizer,
    'validator': validator,
    'builder': builder,
    'descricao': 'Codigo fonte — tokens brutos sem parser',
}
