import sys, os, importlib
_nichos_path = os.path.join(os.path.dirname(__file__), '..', 'nichos', 'tibia', 'mcr')
if _nichos_path not in sys.path:
    sys.path.insert(0, _nichos_path)
_mod = importlib.import_module('npc_criativo')
globals().update({k: v for k, v in vars(_mod).items() if not k.startswith('_')})
