"""Dominio SPRITE — PipelineUniversal.

Motor: MCRSpriteMotor (3 niveis paralelos: byte/palavra/token).
Igual ao MCRMotor para codigo.
PipelineUniversal usa este motor nos 6 estagios.
"""
import sys, numpy as np
from collections import Counter
sys.path.insert(0, r'E:\MCR')

from mcr.mcr_sprite_motor import MCRSpriteMotor
from mcr.sprite_corpus import carregar_categoria, extrair_grid_papel

# Motor global (compartilhado entre chamadas)
_motor = None


def _get_motor():
    global _motor
    if _motor is None:
        _motor = MCRSpriteMotor()
    return _motor


def tokenizer(arr: np.ndarray) -> list:
    """Treina o motor e retorna tokens de regiao.

    O motor treina 3 niveis em paralelo (byte/palavra/token).
    O tokenizer retorna apenas os tokens de palavra (regioes)
    para o PipelineUniversal usar como sequencia base.
    """
    motor = _get_motor()
    motor.treinar([arr])

    # Extrair tokens de regiao para o pipeline
    gp, gc = extrair_grid_papel(arr)
    from mcr.tokenizador_hierarquico import extrair_regioes, ordenar_regioes
    regioes = extrair_regioes(gp, modo='papel')
    regioes = ordenar_regioes(regioes)

    tokens = []
    for r in regioes:
        cx = int(r['centroide'][0])
        cy = int(r['centroide'][1])
        area = r['area']
        bw = r['bbox'][2] - r['bbox'][0] + 1
        bh = r['bbox'][3] - r['bbox'][1] + 1
        orient = int(r['orientacao']) if r['orientacao'] >= 0 else 0
        tokens.append('%s_%d-%d_%d_%dx%d_%d' % (
            r['papel'], cx, cy, area, bw, bh, orient))

    return tokens if tokens else ['F']


def validator(tokens: list) -> dict:
    """Valida usando o motor multi-nivel (NOTA byte+palavra+token)."""
    motor = _get_motor()
    return motor.avaliar(tokens)


def builder(tokens: list, path: str):
    """Renderiza usando o motor multi-nivel (banco de regioes reais)."""
    from PIL import Image
    import numpy as np

    motor = _get_motor()
    arr = motor.renderizar(tokens)
    Image.fromarray(arr, 'RGBA').save(path)


def loader(categoria: str) -> list:
    """Carrega sprites e ja treina o motor."""
    sprites = carregar_categoria(categoria, max_sprites=10)
    if not sprites:
        raise ValueError('Categoria vazia: %s' % categoria)

    motor = _get_motor()
    motor.treinar(sprites, categoria)

    return sprites


def filler_multinivel(template: dict, temperatura: float = 0.8) -> list:
    """Gera usando o motor multi-nivel (substitui gerar_do_template)."""
    motor = _get_motor()
    resultados = motor.gerar(n=1, temperatura=temperatura)
    if resultados:
        return resultados[0].get('regioes', resultados[0])
    return []


DOMINIO = {
    'tokenizer': tokenizer,
    'validator': validator,
    'builder': builder,
    'loader': loader,
    'template_engine': None,
    'filler': filler_multinivel,
    'descricao': 'Sprites — motor 3 niveis (byte+palavra+token) igual codigo',
}
