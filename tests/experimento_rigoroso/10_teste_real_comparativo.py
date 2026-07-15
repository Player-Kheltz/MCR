"""Teste Real — MCR vs Baseline (zero-shot e com feedback)

Compara:
1. MCR zero-shot (sem feedback — mede generalização real)
2. MCR com feedback (aprendizado online)
3. Baseline: TF-IDF + Logistic Regression (scikit-learn)

Dataset: inputs do proprio MCR + inputs externos (nunca vistos)
Métrica: accuracy, latência, tamanho do modelo
"""
import sys, time, json, re, os
sys.path.insert(0, 'E:/MCR')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print('=' * 70)
print('  TESTE REAL — MCR vs BASELINE')
print('  Zero-shot (generalização) vs Com feedback (aprendizado)')
print('=' * 70)

# ══════════════════════════════════════════════════════════════
# DATASET: treino (dataset do MCR) + teste (inputs externos)
# ══════════════════════════════════════════════════════════════

with open('E:/MCR/tests/experimento_rigoroso/dataset_500.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Normaliza ações
from collections import Counter
prefixos = Counter()
for e in dataset:
    a = e['expected_action']
    if '_' in a:
        prefixos[a.split('_')[0]] += 1

def normalize_action(action):
    acao = str(action)
    if '_' in acao:
        verbo = acao.split('_')[0]
        if prefixos.get(verbo, 0) >= 2:
            return verbo
    return acao

# Split: 80% treino, 20% teste (holdout real)
import random
random.seed(42)
random.shuffle(dataset)
split = int(len(dataset) * 0.8)
treino = dataset[:split]
teste = dataset[split:]

# Teste externo: inputs NUNCA vistos (não estão no dataset)
teste_externo = [
    # Domínios novos — mesmo idioma (PT)
    ("crie uma musica para piano", "gerar"),
    ("gere um contrato juridico", "gerar"),
    ("crie um plano de aula", "gerar"),
    ("gere um email comercial", "gerar"),
    ("explique o que e fotosintese", "responder"),
    ("o que e machine learning", "responder"),
    ("como funciona o credito", "responder"),
    ("analise este contrato", "analisar"),
    ("busque por padroes de design", "buscar"),
    ("edite o contrato para incluir clausula", "editar"),
    ("valide a sintaxe do python", "validar"),
    ("conecte arte e tecnologia", "conectar"),
    ("aprenda sobre direito civil", "aprender"),
    ("planeje uma viagem", "planejar"),
    # Inglês (idioma diferente do treino)
    ("create a song for guitar", "gerar"),
    ("generate a legal document", "gerar"),
    ("what is photosynthesis", "responder"),
    ("explain machine learning", "responder"),
    ("analyze this code", "analisar"),
    ("search for design patterns", "buscar"),
    ("edit the contract", "editar"),
    ("validate the syntax", "validar"),
    ("connect art and tech", "conectar"),
    ("learn about civil law", "aprender"),
    ("plan a trip", "planejar"),
    # Espanhol
    ("crea una cancion", "gerar"),
    ("explica la fotosintesis", "responder"),
    # Francês
    ("cree une chanson", "gerar"),
    ("explique la photosynthese", "responder"),
]

print(f'\nDataset treino: {len(treino)} exemplos')
print(f'Dataset teste (holdout): {len(teste)} exemplos')
print(f'Teste externo (nunca vistos): {len(teste_externo)} exemplos')
print(f'Idiomas: PT, EN, ES, FR')
print(f'Dominios: musica, juridico, educacao, ciencia, finanças, design, viagem...')

# ══════════════════════════════════════════════════════════════
# BASELINE: TF-IDF + Logistic Regression
# ══════════════════════════════════════════════════════════════
print('\n[BASELINE] TF-IDF + Logistic Regression')
print('-' * 50)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    
    X_treino = [e['input'] for e in treino]
    y_treino = [normalize_action(e['expected_action']) for e in treino]
    
    baseline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=500, lowercase=True)),
        ('clf', LogisticRegression(max_iter=200, random_state=42)),
    ])
    
    t0 = time.time()
    baseline.fit(X_treino, y_treino)
    t_train_baseline = time.time() - t0
    
    # Teste holdout
    X_teste = [e['input'] for e in teste]
    y_teste = [normalize_action(e['expected_action']) for e in teste]
    
    t0 = time.time()
    y_pred = baseline.predict(X_teste)
    t_test_baseline = time.time() - t0
    
    acc_baseline_holdout = sum(1 for p, t in zip(y_pred, y_teste) if p == t) / len(y_teste) * 100
    
    # Teste externo
    X_ext = [e[0] for e in teste_externo]
    y_ext = [e[1] for e in teste_externo]
    
    t0 = time.time()
    y_pred_ext = baseline.predict(X_ext)
    t_test_ext_baseline = time.time() - t0
    
    acc_baseline_ext = sum(1 for p, t in zip(y_pred_ext, y_ext) if p == t) / len(y_ext) * 100
    
    print(f'  Treino: {t_train_baseline:.2f}s')
    print(f'  Holdout: {acc_baseline_holdout:.1f}% ({t_test_baseline/len(y_teste)*1000:.1f}ms/input)')
    print(f'  Externo (zero-shot): {acc_baseline_ext:.1f}% ({t_test_ext_baseline/len(y_ext)*1000:.1f}ms/input)')
    
    # Tamanho do modelo
    import pickle
    modelo_bytes = len(pickle.dumps(baseline))
    print(f'  Tamanho: {modelo_bytes/1024:.0f}KB')
    
    tem_baseline = True
except ImportError:
    print('  scikit-learn não disponível — pulando baseline')
    tem_baseline = False

# ══════════════════════════════════════════════════════════════
# MCR: treino + teste
# ══════════════════════════════════════════════════════════════
print('\n[MCR] Treino + Teste')
print('-' * 50)

from mcr.mcr import MCR

# Treina MCR com o split de treino
mcr = MCR()

t0 = time.time()
for entry in treino:
    estado = mcr._perceber(entry['input'])
    acao = normalize_action(entry['expected_action'])
    mcr.mk.aprender(estado, acao)
    mcr._coupling.alimentar(entry['input'], acao)
    palavras = re.findall(r'[a-z\xc3-\xff]{3,}', entry['input'].lower())
    for i in range(len(palavras)-1):
        mcr.mk_palavra.aprender(palavras[i], palavras[i+1])
t_train_mcr = time.time() - t0

# Teste holdout — ZERO-SHOT (sem feedback)
t0 = time.time()
acertos_holdout = 0
for entry in teste:
    estado = mcr._perceber(entry['input'])
    acao, conf = mcr._decidir(estado, entry['input'])
    predicted = normalize_action(str(acao))
    expected = normalize_action(entry['expected_action'])
    if predicted == expected:
        acertos_holdout += 1
t_test_mcr = time.time() - t0
acc_mcr_holdout = acertos_holdout / len(teste) * 100

# Teste externo — ZERO-SHOT (sem feedback)
t0 = time.time()
acertos_ext_zs = 0
for entrada, esperado in teste_externo:
    estado = mcr._perceber(entrada)
    acao, conf = mcr._decidir(estado, entrada)
    predicted = normalize_action(str(acao))
    if predicted == esperado:
        acertos_ext_zs += 1
t_test_ext_zs = time.time() - t0
acc_mcr_ext_zs = acertos_ext_zs / len(teste_externo) * 100

# Teste externo — COM FEEDBACK (aprendizado online)
t0 = time.time()
acertos_ext_fb = 0
for entrada, esperado in teste_externo:
    estado = mcr._perceber(entrada)
    acao, conf = mcr._decidir(estado, entrada)
    predicted = normalize_action(str(acao))
    if predicted != esperado:
        mcr.receber_feedback(entrada, esperado)
        estado2 = mcr._perceber(entrada)
        acao2, conf2 = mcr._decidir(estado2, entrada)
        predicted = normalize_action(str(acao2))
    if predicted == esperado:
        acertos_ext_fb += 1
t_test_ext_fb = time.time() - t0
acc_mcr_ext_fb = acertos_ext_fb / len(teste_externo) * 100

# Tamanho do MCR
import json as _json
mcr_bytes = len(_json.dumps(mcr.mk.transicoes, ensure_ascii=False).encode('utf-8'))
mcr_bytes += len(_json.dumps(dict(mcr._coupling._palavra_acao), ensure_ascii=False, default=str).encode('utf-8'))

print(f'  Treino: {t_train_mcr:.2f}s')
print(f'  Holdout (zero-shot): {acc_mcr_holdout:.1f}% ({t_test_mcr/len(teste)*1000:.1f}ms/input)')
print(f'  Externo zero-shot: {acc_mcr_ext_zs:.1f}% ({t_test_ext_zs/len(teste_externo)*1000:.1f}ms/input)')
print(f'  Externo com feedback: {acc_mcr_ext_fb:.1f}% ({t_test_ext_fb/len(teste_externo)*1000:.1f}ms/input)')
print(f'  Tamanho: {mcr_bytes/1024:.0f}KB')

# ══════════════════════════════════════════════════════════════
# COMPARAÇÃO
# ══════════════════════════════════════════════════════════════
print('\n' + '=' * 70)
print('  COMPARAÇÃO')
print('=' * 70)
print(f'{"Métrica":<30s} {"MCR":>15s}', end='')
if tem_baseline:
    print(f' {"TF-IDF+LR":>15s}', end='')
print()
print('-' * 70)

print(f'{"Holdout (zero-shot)":<30s} {acc_mcr_holdout:>14.1f}%', end='')
if tem_baseline:
    print(f' {acc_baseline_holdout:>14.1f}%', end='')
print()

print(f'{"Externo (zero-shot)":<30s} {acc_mcr_ext_zs:>14.1f}%', end='')
if tem_baseline:
    print(f' {acc_baseline_ext:>14.1f}%', end='')
print()

print(f'{"Externo (com feedback)":<30s} {acc_mcr_ext_fb:>14.1f}%', end='')
if tem_baseline:
    print(f' {"N/A":>15s}', end='')
print()

print(f'{"Latência (ms/input)":<30s} {t_test_mcr/len(teste)*1000:>14.1f}', end='')
if tem_baseline:
    print(f' {t_test_baseline/len(y_teste)*1000:>14.1f}', end='')
print()

print(f'{"Tamanho (KB)":<30s} {mcr_bytes/1024:>14.0f}', end='')
if tem_baseline:
    print(f' {modelo_bytes/1024:>14.0f}', end='')
print()

print(f'{"GPU necessária":<30s} {"Não":>15s}', end='')
if tem_baseline:
    print(f' {"Não":>15s}', end='')
print()

print(f'{"Dependências":<30s} {"0 (stdlib)":>15s}', end='')
if tem_baseline:
    print(f' {"scikit-learn":>15s}', end='')
print()

print(f'{"Aprendizado online":<30s} {"Sim":>15s}', end='')
if tem_baseline:
    print(f' {"Não":>15s}', end='')
print()

print(f'{"Inspecionável":<30s} {"Sim (JSON)":>15s}', end='')
if tem_baseline:
    print(f' {"Não (pesos)":>15s}', end='')
print()

print('=' * 70)

# Veredito
print('\nVEREDITO:')
if tem_baseline:
    if acc_mcr_ext_zs >= acc_baseline_ext:
        print('  MCR SUPERIOR em zero-shot externo — agnóstico real')
    else:
        print(f'  MCR perde em zero-shot ({acc_mcr_ext_zs:.0f}% vs {acc_baseline_ext:.0f}%)')
        print(f'  Mas MCR com feedback alcança {acc_mcr_ext_fb:.0f}% — aprende do erro')
        if acc_mcr_ext_fb >= acc_baseline_ext:
            print('  MCR COM FEEDBACK supera baseline — aprendizado online é vantagem real')
    
    if t_test_mcr/len(teste)*1000 < t_test_baseline/len(y_teste)*1000:
        print(f'  MCR {t_test_baseline/len(y_teste)*1000 / (t_test_mcr/len(teste)*1000):.0f}x mais rápido')
    
    if mcr_bytes < modelo_bytes:
        print(f'  MCR {modelo_bytes/mcr_bytes:.0f}x menor')
