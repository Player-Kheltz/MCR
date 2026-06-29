"""Chamada direta ao MCR-DevIA via IA.gerar() com a pergunta Kheltz."""
import sys, os, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Scripts', 'mcr_devia'))

# Carrega a pergunta do .mcr_cmd.json
with open(os.path.join(os.path.dirname(__file__), '.mcr_cmd.json'), encoding='utf-8') as f:
    cmd = json.load(f)
pergunta = cmd['args'][0]

# Usa IA direta com identidade
from modulos.ia import IA

ia = IA()
identidade = ""
id_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'MCR_IDENTITY.md')
try:
    if os.path.exists(id_path):
        with open(id_path, 'r', encoding='utf-8') as f:
            identidade = f.read()[:500].strip()
except:
    pass

print("=" * 70)
print("PERGUNTA ENVIADA AO MCR-DevIA:")
print("=" * 70)
# Mostra apenas o comeco da pergunta
print(pergunta[:200] + "...")
print()

print("=" * 70)
print("AGUARDANDO RESPOSTA DO MCR-DevIA...")
print("=" * 70)

prompt = f"{identidade}\n\n{pergunta}"
resposta = ia.gerar(prompt, 0.3)

print()
print("=" * 70)
print("RESPOSTA DO MCR-DevIA:")
print("=" * 70)
print(resposta)

# Salva resposta completa
out_path = os.path.join(os.path.dirname(__file__), '.mcr_resposta_kheltz.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(resposta if resposta else "(sem resposta)")

print()
print(f"Resposta salva em: {out_path}")
print(f"Tamanho: {len(resposta) if resposta else 0} caracteres")
