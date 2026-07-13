"""modulos.MCR — Redireciona para devia.kernel.mcr_kernel.decisor."""
from devia.kernel.mcr_kernel.decisor import (
    MCRDecisor,
    MCRThreshold,
    MCREntropia,
    MCRRuido,
    MCRPeso,
)
from devia.kernel.mcr_kernel.engine import MCR, MCRBridge
from devia.kernel.MCR_legacy import MCR as _MCRLegacy
from devia.kernel.MCR_legacy import MCRThreshold as _MCRThresholdLegacy

try:
    def _classificar_token(token):
        d = MCRDecisor()
        return d.classificar(token)
except Exception:
    def _classificar_token(token):
        return 'desconhecido'
