#!/usr/bin/env python
"""Alias para mcr_devia.py (legado) - mantido para compatibilidade."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from mcr_devia import main
if __name__ == '__main__':
    main()
