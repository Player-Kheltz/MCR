"""Teste isolado: Comparativo entre 3 abordagens para a MESMA pergunta.

Abordagem A: 14b puro (atual)
Abordagem B: FAST + ContextTools (KG + Cache + Identity)   
Abordagem C: FAST puro (controle)

Pergunta: "Explique o que e o SessionCache no MCR-DevIA e como ele difere de uma cache tradicional"

Objetivo: Validar se FAST + ContextTools consegue QUALIDADE igual ou superior ao 14b,
mas com 4x menos tempo.
"""
import sys, os, time, json

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))
sys.path.insert(0, os.path.join(BASE))

from modulos.ia import IA
from modulos.kg import KnowledgeGraph
from modulos.decider import Decider
from context_infinity import SessionCache
from context_crew import ContextCrew

PERGUNTA = "Explique o que e o SessionCache no MCR-DevIA e como ele difere de uma cache tradicional"

ia = IA()
kg = KnowledgeGraph()
cache = SessionCache()
decider = Decider(ia)

# IDs dos arquivos para salvar respostas
RESPOSTAS_DIR = os.path.join(BASE, 'sandbox', '_teste_comparativo')
os.makedirs(RESPOSTAS_DIR, exist_ok=True)

# ============================================================
# ABORDAGEM A: 14b puro (atual)
# ============================================================
print("=" * 70)
print("  ABORDAGEM A - 14b Puro (atual)")
print("=" * 70)

t0 = time.time()
resposta_a = ia.gerar(PERGUNTA, 0.4, 'pesado') or "[ERRO]"
tempo_a = time.time() - t0

with open(os.path.join(RESPOSTAS_DIR, 'a_14b_puro.txt'), 'w', encoding='utf-8') as f:
    f.write(f"TEMPO: {tempo_a:.1f}s\n\n{resposta_a}")

print(f"  Tempo: {tempo_a:.1f}s")
print(f"  Resposta: {resposta_a[:150]}...")
print()

# ============================================================
# ABORDAGEM B: FAST + ContextTools (proposto)
# ============================================================
print("=" * 70)
print("  ABORDAGEM B - FAST + ContextTools")
print("=" * 70)

# 1. Pre-carrega SessionCache com conhecimento do KG
n = cache.precarregar(kg=kg, request=PERGUNTA)
#print(f"  Pre-carregados {n} fragmentos")

# 2. Coleta contexto
contexto_coletado = []

# KG keyword
for l in kg.buscar(PERGUNTA, max_r=5):
    contexto_coletado.append(('KG', l.get('solucao', '')[:300]))

# KG embedding
try:
    for l in kg.buscar_por_embedding(PERGUNTA, n=3):
        sol = l.get('solucao', '')[:300]
        if sol not in [c[1] for c in contexto_coletado]:
            contexto_coletado.append(('KG-sem', sol))
except: pass

# SessionCache
for frag in cache.pescar(pergunta=PERGUNTA, tipos=['contexto'], max_tokens=500, n=3):
    contexto_coletado.append(('Cache', frag.conteudo[:200]))

# ContextCrew
try:
    for texto, fonte in ContextCrew().buscar(PERGUNTA, max_r=2):
        contexto_coletado.append(('Crew', texto[:300]))
except: pass

# MCR_Identity
IDENTITY = """CONTEXTO DO PROJETO MCR:
- MCR = servidor CUSTOMIZADO de Tibia baseado em Canary (OTServ)
- SessionCache = cache de sessao que absorve tudo sem limite, pesca sob demanda
- MasterAgent = orquestrador universal que faz QUALQUER coisa
- Decider = classificador universal via FAST model
- KG = Knowledge Graph com licoes aprendidas"""

# 3. Monta prompt com contexto
contexto_str = '\n'.join(f"[{f}] {t}" for f, t in contexto_coletado[:8])
prompt_b = (
    f"{IDENTITY}\n\n"
    f"Contexto:\n{contexto_str}\n\n"
    f"Com base no contexto ACIMA, responda a pergunta abaixo de forma "
    f"ESPECIFICA. Nao seja generico.\n\n"
    f"Pergunta: {PERGUNTA}"
)

t0 = time.time()
resposta_b = ia.fast(prompt_b, 0.3, 'leve') or "[ERRO]"
tempo_b = time.time() - t0

with open(os.path.join(RESPOSTAS_DIR, 'b_fast_contexttools.txt'), 'w', encoding='utf-8') as f:
    f.write(f"TEMPO: {tempo_b:.1f}s\n\n{resposta_b}")

print(f"  Tempo: {tempo_b:.1f}s")
print(f"  Resposta: {resposta_b[:150]}...")
print()

# ============================================================
# ABORDAGEM C: FAST puro (controle - sem contexto)
# ============================================================
print("=" * 70)
print("  ABORDAGEM C - FAST Puro (controle)")
print("=" * 70)

t0 = time.time()
resposta_c = ia.fast(PERGUNTA, 0.3, 'leve') or "[ERRO]"
tempo_c = time.time() - t0

with open(os.path.join(RESPOSTAS_DIR, 'c_fast_puro.txt'), 'w', encoding='utf-8') as f:
    f.write(f"TEMPO: {tempo_c:.1f}s\n\n{resposta_c}")

print(f"  Tempo: {tempo_c:.1f}s")
print(f"  Resposta: {resposta_c[:150]}...")
print()

# ============================================================
# MÉTRICAS
# ============================================================
def medir_especificidade(texto):
    """Mede quantos termos do ecossistema MCR a resposta menciona."""
    termos_mcr = [
        'sessioncache', 'session', 'cache', 'absorver', 'pescar', 'fragmento',
        'orquestrador', 'contexto', 'infinito', 'mcr', 'tibia', 'masteragent',
        'decider', 'knowledge graph', 'kg', 'memoria', 'episodica',
        'ferramenta', 'tool', 'validador', 'canary', 'otserv', 'servidor'
    ]
    texto_lower = texto.lower()
    return sum(1 for t in termos_mcr if t in texto_lower)

def medir_tamanho(texto):
    """Retorna numero de caracteres."""
    return len(texto)

def detectar_generico(texto):
    """Detecta se resposta parece generica."""
    padroes_genericos = [
        'é um componente', 'é uma técnica', 'pode ser usado',
        'é importante', 'é fundamental', 'é essencial',
        'em resumo', 'de forma geral', 'basicamente',
        'consiste em', 'trata-se de', 'refere-se a'
    ]
    texto_lower = texto.lower()
    return sum(1 for p in padroes_genericos if p in texto_lower)

metricas = {
    'A (14b puro)': {
        'tempo': round(tempo_a, 1),
        'tamanho': medir_tamanho(resposta_a),
        'termos_mcr': medir_especificidade(resposta_a),
        'generico': detectar_generico(resposta_a),
    },
    'B (FAST + ContextTools)': {
        'tempo': round(tempo_b, 1),
        'tamanho': medir_tamanho(resposta_b),
        'termos_mcr': medir_especificidade(resposta_b),
        'generico': detectar_generico(resposta_b),
    },
    'C (FAST puro)': {
        'tempo': round(tempo_c, 1),
        'tamanho': medir_tamanho(resposta_c),
        'termos_mcr': medir_especificidade(resposta_c),
        'generico': detectar_generico(resposta_c),
    },
}

# ============================================================
# RELATORIO COMPARATIVO
# ============================================================
print("\n\n" + "=" * 70)
print("  RELATORIO COMPARATIVO")
print("=" * 70)

print(f"\n  {'Metrica':<25s} {'A (14b)':<15s} {'B (FAST+CT)':<15s} {'C (FAST)':<15s}")
print(f"  {'-'*25} {'-'*15} {'-'*15} {'-'*15}")
for metrica in ['tempo', 'tamanho', 'termos_mcr', 'generico']:
    print(f"  {metrica:<25s} {metricas['A (14b puro)'][metrica]:<15} {metricas['B (FAST + ContextTools)'][metrica]:<15} {metricas['C (FAST puro)'][metrica]:<15}")

print(f"\n  Proporcao tempo (B vs A): {tempo_b/tempo_a:.1f}x")
print(f"  Proporcao tempo (C vs A): {tempo_c/tempo_a:.1f}x")
print(f"\n  Termos MCR = mais ESPECIFICO (quanto maior, melhor)")
print(f"  Generico = mais GENERICO (quanto menor, melhor)")

# Salva relatorio
relatorio = {
    'pergunta': PERGUNTA,
    'metricas': metricas,
    'tempo_proporcao_b_vs_a': round(tempo_b/tempo_a, 2),
    'tempo_proporcao_c_vs_a': round(tempo_c/tempo_a, 2),
}
with open(os.path.join(RESPOSTAS_DIR, 'relatorio.json'), 'w', encoding='utf-8') as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)

print(f"\n[Relatorio salvo em {RESPOSTAS_DIR}/relatorio.json]")
print(f"\n[Respostas salvas em {RESPOSTAS_DIR}/]")
print(f"\n  a_14b_puro.txt         - Abordagem A")
print(f"  b_fast_contexttools.txt - Abordagem B")
print(f"  c_fast_puro.txt         - Abordagem C")
print(f"\n  Leia os arquivos e julgue QUAL resposta tem MELHOR QUALIDADE!")
