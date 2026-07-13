"""motor — Núcleo Markoviano. Matemática pura, zero dependências.

engine.py  → MCR (Markov 1ª ordem)
signature.py → MCRFingerprint, MCRSignature
"""
from .engine import MCR, MCRBridge, MarkovUniversal
from .signature import MCRFingerprint, MCRSignature
