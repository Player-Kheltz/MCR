"""Testa import do bridge_auto e router."""
import sys, json
sys.path.insert(0, r"E:\Projeto MCR\scripts")
sys.path.insert(0, r"E:\Projeto MCR\Scripts")

try:
    from bridge_auto import route_intent, format_item_response, save_to_history, load_history, search_history
    print("Import OK")
    
    # Test router
    result = route_intent("o que e a War Hammer?")
    print("Router result:", result)
    print("Intent:", repr(result.get("intent")))
    print("Entity:", repr(result.get("entity")))
    
except Exception as e:
    import traceback
    print("ERRO:", e)
    traceback.print_exc()
