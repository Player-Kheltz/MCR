"""Diagnostico rapido: gera resposta via fragmentador e inspeciona."""
import os, sys, json, time, re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

from modulos.master_agent import MasterAgent

ma = MasterAgent()

# Pega topicos
topicos = ma._amostrar_topicos_distantes(n=3)
print(f'Topicos: {len(topicos)}')
for t in topicos:
    print(f'  [{t.get("ctx","?")}] {t.get("erro","")[:60]}')

# Gera pergunta
pergunta = ma._gerar_pergunta_emergente(topicos)
print(f'\nPergunta: {pergunta[:100]}')

# ContextCrew
from context_crew import ContextCrew
cc = ContextCrew()
ctx_enriquecido = ""
for t in topicos:
    ctx = cc.executar(t.get('erro', '')) or ""
    if ctx:
        ctx_enriquecido += f"--- {t.get('erro','')} ---\n{ctx[:800]}\n"
print(f'ContextCrew: {len(ctx_enriquecido)} chars')

# Gera resposta fragmentada
print('\nGerando resposta fragmentada...')
t0 = time.time()
resposta = ma._gerar_emergencia_fragmentada(pergunta, topicos, ctx_enriquecido)
tempo = time.time() - t0

print(f'\nTempo: {tempo:.1f}s')
print(f'Tamanho: {len(resposta)} chars')
print(f'Secoes (###): {len(re.findall(r"###\s", resposta))}')

# Salva para inspecao
out_path = os.path.join(os.path.dirname(__file__), '.emergir_v3_response.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(resposta)
print(f'\nSalvo em: {out_path}')

# Verifica SIGLAS
proibidos = [
    (r'FAST\s*\([^)]*FastAPI', 'FAST=FastAPI'),
    (r'FAST\s*\([^)]*Authentication', 'FAST=Authentication'),
    (r'SPA\s*\([^)]*Single\s*Page', 'SPA=SinglePage'),
    (r'SHC\s*\([^)]*Sistema\s*Hospitalar', 'SHC=Hospitalar'),
    (r'SHC\s*\([^)]*Health', 'SHC=Health'),
    (r'minecraft', 'Minecraft'),
]
print('\n--- VERIFICACAO DE SIGLAS ---')
encontrou = False
for padrao, nome in proibidos:
    if re.search(padrao, resposta, re.IGNORECASE):
        # Encontra o trecho
        m = re.search(padrao, resposta, re.IGNORECASE)
        inicio = max(0, m.start() - 40)
        fim = min(len(resposta), m.end() + 40)
        print(f'  ❌ {nome}: ...{resposta[inicio:fim]}...')
        encontrou = True
    else:
        print(f'  ✅ {nome}: nao encontrado')

if not encontrou:
    print('  ✅ NENHUMA alucinacao de sigla detectada por regex!')
    print('  ⚠ Se o FAST bloqueou, pode ser FALSO POSITIVO do 1.5b')

# Mostra inicio da resposta
print('\n--- INICIO DA RESPOSTA ---')
print(resposta[:600])
