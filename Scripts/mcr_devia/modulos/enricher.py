"""Enricher — Atalho para Conselho (fundido).

Todas as funcionalidades foram movidas para conselho.py para evitar
duplicacao. Este arquivo permanece como atalho de compatibilidade
para imports existentes.

Uso (antigo, ainda funciona):
    from modulos.enricher import Enricher
    e = Enricher(ia, kg, ctx)

Uso (recomendado):
    from modulos.conselho import Conselho
    c = Conselho(kg=kg, ia=ia)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Conselho tem TUDO que o Enricher tinha + personalidades + memoria + router
from modulos.conselho import (
    Conselho,
    tree_of_thought,
    extrair_termos_criticos,
    validar_relevancia,
    PromptCache,
)

# Mantido para compatibilidade com imports existentes
Enricher = Conselho
