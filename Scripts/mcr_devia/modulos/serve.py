"""Serve — re-export do modulo pipeline/serve.py para compatibilidade com kernel.py."""
import sys, os
_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent not in sys.path:
    sys.path.insert(0, _parent)
from pipeline.serve import Serve
