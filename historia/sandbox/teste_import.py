#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
print("1: import basico...", flush=True)
import modulos.MCR
print("2: import OK", flush=True)

from modulos.MCR import MCRThreshold
print("3: MCRThreshold OK", flush=True)

from modulos.MCR import AutoavaliadorSemantico
print("4: AutoavaliadorSemantico OK", flush=True)

from modulos.MCR import MCRConector
print("5: MCRConector OK", flush=True)

from modulos.MCR import MCRCadeia
print("6: MCRCadeia OK", flush=True)

from modulos.MCR import MCRPergunta
print("7: MCRPergunta OK", flush=True)

from modulos.MCR import _classificar_token
print("8: _classificar_token OK", flush=True)

from modulos.MCR import _MCR_THRESHOLD_CONF
print("9: _MCR_THRESHOLD_CONF OK", flush=True)

print("ALL OK", flush=True)
