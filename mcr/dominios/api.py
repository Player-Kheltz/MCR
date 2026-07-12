"""Dominio API — PipelineUniversal.

Tokenizer: raw_token_set (extrai chamadas de funcao sem parser).
Validator: entropia + cobertura.
Builder: salva como JSON.
"""
import sys, json
sys.path.insert(0, r'E:\MCR')
sys.path.insert(0, r'E:\MCR\prototypes\mcr-universal')


def tokenizer(arquivo: str) -> list:
    """Tokeniza API: delimitadores universais, preserva ordem."""
    import re
    delim = re.compile(r'[\s{}();.,:\[\]"\'' + "'" + r'`/\\#<>!=+\-*%&|^~@?]+')

    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
    except Exception:
        if isinstance(arquivo, str):
            conteudo = arquivo
        else:
            return [str(arquivo)]

    tokens = delim.split(conteudo)
    return [t.strip().lower() for t in tokens if t.strip()]


def validator(sequencia: list) -> dict:
    if not sequencia:
        return {'score': 0.0}
    unicos = len(set(sequencia))
    return {'score': min(1.0, unicos / max(len(sequencia) * 0.5, 1))}


def builder(sequencia: list, path: str):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(set(sequencia))))


DOMINIO = {
    'tokenizer': tokenizer,
    'validator': validator,
    'builder': builder,
    'descricao': 'API — tokens de chamadas de funcao',
}
