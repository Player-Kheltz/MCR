import sys, os, importlib
_knowledge_path = os.path.join(os.path.dirname(__file__), 'knowledge')
if _knowledge_path not in sys.path:
    sys.path.insert(0, _knowledge_path)
_mod = importlib.import_module('episodic_memory')
EpisodicMemory = _mod.EpisodicMemory
