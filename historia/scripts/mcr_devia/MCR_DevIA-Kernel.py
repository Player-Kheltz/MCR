#!/usr/bin/env python
"""MCR-DevIA Kernel - Entry point CLI.
Importa kernel.py e delega.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == '__main__':
    from kernel import main_kernel
    main_kernel()
