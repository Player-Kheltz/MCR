#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
print("1", flush=True)
from modulos.MCR import MCRPesoNota
print("2 MCRPesoNota OK", flush=True)
from modulos.MCR import MCRMetaGap
print("3 MCRMetaGap OK", flush=True)
from modulos.MCR import MCRWebLearn
print("4 MCRWebLearn OK", flush=True)
from modulos.MCR import MCRFeedback
print("5 MCRFeedback OK", flush=True)
from modulos.MCR import MCRSignature
print("6 MCRSignature OK", flush=True)
from modulos.MCR import MCRDecisor
print("7 MCRDecisor OK", flush=True)
from modulos.MCR import MCREntropia
print("8 MCREntropia OK", flush=True)

# Now test Threshold
from modulos.MCR import _MCR_THRESHOLD_CONF
print("9 Threshold OK", flush=True)

t = _MCR_THRESHOLD_CONF.obter('teste', 0.5)
print(f"10 obter={t}", flush=True)
_MCR_THRESHOLD_CONF.aprender('teste', 0.8)
_MCR_THRESHOLD_CONF.aprender('teste', 0.9)
t2 = _MCR_THRESHOLD_CONF.obter('teste', 0.5)
print(f"11 apos aprender={t2}", flush=True)
assert t2 > 0.7, f"Threshold: {t2}"
print("ALL OK", flush=True)
