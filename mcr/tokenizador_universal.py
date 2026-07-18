"""TokenizadorUniversal — qualquer stream → string canônica → estados.

Pilar 1: TUDO é P(b|a). O motor não pergunta origem.
Pilar 3: MESMO motor, N domínios. Texto, imagem, áudio, sensor — mesmo caminho.
Pilar 7: P(feature|conceito) é a ponte universal.

O coupling opera sobre strings (extrai features de bytes, chars, tokens, ngramas).
Este módulo converte QUALQUER input (str, bytes, list, dict) em uma string
canônica que o coupling processa uniformemente.

Sem if/else de domínio. Sem hardcode de modalidade.
Apenas conversão de tipo → string canônica → P(b|a).

Uso:
    from mcr.tokenizador_universal import tokenizar
    canon = tokenizar("criar dragão")        # texto → texto normalizado
    canon = tokenizar(b'\\x89PNG\\r\\n...')   # bytes → hex string
    canon = tokenizar([255, 128, 0, 64])     # lista de int → hex string
    canon = tokenizar({"temp": 23.5})        # dict → json string
    coupling.alimentar(canon, acao)
    acao, conf = coupling.decidir(canon, (None, 0.0))
"""
import json
from typing import Union, List, Any


def _bytes_para_hex(data: bytes) -> str:
    """Converte bytes para string hex lowercase sem separadores.

    Ex: b'\\x89PNG' → '89504e47'
    Cada par hex vira um 'token' de 2 chars na string canônica.
    O coupling extrai features de byte, char, ngrama disso naturalmente.
    """
    return data.hex()


def _ints_para_hex(valores: List[int]) -> str:
    """Converte lista de inteiros (0-255) para hex string.

    Útil para samples de áudio, pixels grayscale, leituras de sensor.
    """
    return ''.join(f'{v & 0xFF:02x}' for v in valores)


def tokenizar(stream: Any) -> str:
    """Converte qualquer stream em string canônica para o coupling.

    Sem if/else de domínio. Apenas conversão de tipo:
    - str → normaliza (lowercase, preserva unicode)
    - bytes → hex string
    - list[int] (0-255) → hex string
    - dict/list/other → json string

    O coupling não sabe (nem pergunta) de onde veio.
    P(b|a) opera sobre a string canônica universalmente.

    Args:
        stream: texto, bytes, lista de ints, dict, ou qualquer objeto
                serializável.

    Returns:
        String canônica pronta para coupling.alimentar() ou decidir().
    """
    if isinstance(stream, str):
        return stream.lower()

    if isinstance(stream, bytes):
        return _bytes_para_hex(stream)

    if isinstance(stream, (bytearray, memoryview)):
        return _bytes_para_hex(bytes(stream))

    if isinstance(stream, list) and stream and all(isinstance(x, int) for x in stream):
        return _ints_para_hex(stream)

    try:
        return json.dumps(stream, ensure_ascii=False, default=str).lower()
    except (TypeError, ValueError):
        return str(stream).lower()


def tokenizar_texto(texto: str) -> List[str]:
    """Tokeniza texto em palavras (compatível com coupling existente).

    Mantém o comportamento atual de extração de palavras para o coupling.
    Não é para bytes — para bytes, usar tokenizar() e deixar o coupling
    extrair features de byte/char/ngrama.
    """
    import re
    return re.findall(r'[a-zà-ÿ0-9]{2,}', texto.lower())


def modularidade_bytes(data: bytes, n: int = 2) -> List[str]:
    """Extrai n-gramas de bytes como tokens nomeados.

    Pilar 1: P(byte_n | byte_n-1) — transição entre bytes consecutivos.
    Pilar 7: correlação universal via n-gramas de bytes.

    Args:
        data: bytes brutos (pixel, áudio, sensor, texto UTF-8)
        n: tamanho do n-grama (2=bigrama, 3=trigrama)

    Returns:
        Lista de tokens no formato 'bxNN_NN' (hex dos bytes).
    """
    raw = bytes(data)
    if len(raw) < n:
        return []
    return [f"bx{'_'.join(f'{b:02x}' for b in raw[i:i+n])}"
            for i in range(len(raw) - n + 1)]
