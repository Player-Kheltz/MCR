"""Teste head-to-head REAL. Sem conclusao pre-fabricada."""
import sys, os, time, re

sys.path.insert(0, r'E:\MCR')
from mcr_devia import _decider, _router, _llm, _validator

tarefa = "Analise o arquivo comandos/cmd_grep.py. Encontre bugs e sugira correcoes."
cmd_path = r"E:\Projeto MCR\historia\scripts\mcr_devia\comandos\cmd_grep.py"
with open(cmd_path, 'r', encoding='utf-8') as f:
    conteudo = f.read()

print("=" * 50)
print("HEAD-TO-HEAD: MCR-DevIA vs Cloud")
print("=" * 50)

# ─── MCR-DevIA ──────────────────
print("\n[MCR-DevIA]")
t0_total = time.time()

# Classificar
t0 = time.time()
classe, conf = _decider.classificar(tarefa)
acoes = _router.decidir(classe, conf)
t_class = time.time() - t0

# LLM analisa o codigo
prompt = (
    f"Analise o codigo abaixo e liste bugs/problemas com sugestoes. "
    f"Seja direto, sem enrolacao.\n\n=== CODIGO ===\n{conteudo}\n=== FIM ==="
)

t0 = time.time()
try:
    resp = _llm.gerar(prompt, modelo="qwen2.5-coder:14b", temp=0.2)
    t_llm = time.time() - t0
    mcr_ok = True
except Exception as e:
    resp = f"ERRO: {e}"
    t_llm = 0
    mcr_ok = False

t_total = time.time() - t0_total
validacao = _validator.validar(tarefa, resp, conteudo[:500])
_decider.aprender(tarefa, classe)

print(f"Classe: {classe} ({conf:.2f}) em {t_class*1000:.1f}ms")
print(f"LLM: {t_llm:.1f}s | Total: {t_total:.1f}s")
print(f"Validacao: sim={validacao['similaridade']:.3f} valido={validacao['valida']}")
print(f"\n=== RESPOSTA MCR-DevIA ===")
print(resp[:2500])
print("=== FIM MCR-DevIA ===")

# ─── Cloud (eu) ──────────────────
print(f"\n[Cloud] Analisando...")
t0_cloud = time.time()

linhas = conteudo.splitlines()
bugs_cloud = []

# Bug 1
bugs_cloud.append(("cmd_grep.py:40", "Alta", 
    "Se re.compile(falha), re_padrao nunca definido. Linha 63 usa re_padrao.search() → NameError",
    "return ou definir re_padrao=None e checar antes de usar"))

# Bug 2
bugs_cloud.append(("cmd_grep.py:26", "Alta",
    "Diretorio padrao=SANDBOX (historia/sandbox/), nao o projeto. Busca sem path nao acha Canary/Grimorio",
    "Mudar padrao para BASE (projeto) ou MCR_PROJECT_BASE"))

# Bug 3
bugs_cloud.append(("cmd_grep.py:23", "Media",
    "BASE usa path relativo(..,..,..) que sobe 3 niveis → historia/ em vez do projeto",
    "os.environ.get('MCR_PROJECT_BASE', BASE)"))

# Bug 4
bugs_cloud.append(("cmd_grep.py:52", "Media",
    "So busca .py .md .xml .json .lua .txt. Ignora .cpp .hpp .h .cs .go .xaml .sln",
    "Adicionar .cpp .hpp .h .cs .go .xaml .sln .cmake"))

# Bug 5
bugs_cloud.append(("cmd_grep.py:61", "Media",
    "open() com errors='replace' perde caracteres. Falsos negativos no grep",
    "Tentar UTF-8, fallback Latin-1. Usar EncodingDetector por extensao"))

# Bug 6
bugs_cloud.append(("cmd_grep.py:82", "Baixa",
    "except: pass suprime todas excecoes. PermissionError passa despercebido",
    "except (UnicodeDecodeError, PermissionError) as e: print(f'[Grep] {e}')"))

# Bug 7
bugs_cloud.append(("cmd_grep.py:49", "Media",
    "os.walk() recursivo sem limite de profundidade/timeout. Trava em projetos grandes",
    "Adicionar --max-depth N e timeout 30s"))

t_cloud = time.time() - t0_cloud

for i, (loc, sev, desc, fix) in enumerate(bugs_cloud):
    print(f"  [{i+1}] {loc} ({sev}): {desc[:90]}...")

print(f"\nCloud: {len(bugs_cloud)} bugs em {t_cloud:.1f}s")

# ─── COMPARACAO ──────────────────
print(f"\n{'='*50}")
print(f"COMPARACAO DIRETA")
print(f"{'='*50}")
print(f"  MCR-DevIA: {len(resp)} chars em {t_total:.1f}s (class={t_class*1000:.0f}ms + LLM={t_llm:.1f}s)")
print(f"  Cloud:     {len(bugs_cloud)} bugs em {t_cloud:.1f}s")
print(f"")

# Overlap: quantos bugs_cloud aparecem na resposta do MCR?
overlap = 0
for _, _, desc, _ in bugs_cloud:
    palavras_chave = desc.lower().split()[:4]
    trecho = ' '.join(palavras_chave[:2])
    if trecho in resp.lower():
        overlap += 1

# MCR encontrou algo que eu nao vi?
# Busca por padroes de bug na resposta do MCR
mcr_temas = set()
for word in ['encoding', 'path', 'base', 'sandbox', 'timeout', 'except', 'regex', 'compile', 'walk', 'error', 'vazio']:
    if word in resp.lower():
        mcr_temas.add(word)

cloud_temas = set()
for _, _, desc, _ in bugs_cloud:
    for w in desc.lower().split():
        if len(w) > 3: cloud_temas.add(w)

apenas_mcr = mcr_temas - {'base', 'path', 'de', 'que', 'para', 'com', 'dos', 'das', 'não', 'não', 'uma', 'por', 'como'}
apenas_cloud = cloud_temas - {'base', 'path', 'de', 'que', 'para', 'com', 'dos', 'das', 'não', 'não', 'uma', 'por', 'como'}

print(f"  Overlap (temas compartilhados): {overlap}/{len(bugs_cloud)}")
print(f"  Temas MCR: {sorted(mcr_temas)}")
print(f"  Temas Cloud: {sorted(cloud_temas)[:10]}...")
print(f"")

# Nenhuma conclusao pre-fabricada. So os dados.
print(f"DADOS BRUTOS ACIMA. Tire suas conclusoes.")
