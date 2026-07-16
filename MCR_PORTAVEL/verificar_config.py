import json
with open("E:\\MCR\\opencode.json") as f:
    cfg = json.load(f)
print("JSON valido")
print(f"Modelo: {cfg['model']}")
print(f"Provider ollama: {list(cfg['provider']['ollama'].keys())}")
print(f"Models listados: {list(cfg['provider']['ollama']['models'].keys())}")
print(f"Agent code: {cfg['agent']['code']['model']}")
print(f"Agent quick: {cfg['agent']['quick']['model']}")
print(f"Comandos: {list(cfg['command'].keys())}")
