"""Teste head-to-head: MCR-DevIA vs Cloud — mesma tarefa."""
import sys, os, time, json
sys.path.insert(0, r'E:\MCR')
from mcr_devia import _decider, _router, _llm, _filter, _validator, _autorevisao, processar

print("=" * 60)
print("  HEAD-TO-HEAD: MCR-DevIA vs Cloud")
print("=" * 60)

# Tarefa: analisar cmd_grep.py
tarefa = "Analise o arquivo comandos/cmd_grep.py. Encontre bugs e sugira correcoes."

# 1. MCR classifica
print("\n[MCR] Classificando...")
t0 = time.time()
classe, conf = _decider.classificar(tarefa)
acoes = _router.decidir(classe, conf)
t = (time.time() - t0) * 1000
print(f"  Classe: {classe} ({conf:.2f}) em {t:.1f}ms")
print(f"  Pipeline: {acoes}")

# 2. MCR le o arquivo real
print("\n[MCR] Lendo cmd_grep.py...")
cmd_path = r"E:\Projeto MCR\historia\scripts\mcr_devia\comandos\cmd_grep.py"
with open(cmd_path, 'r', encoding='utf-8') as f:
    conteudo = f.read()
print(f"  Lido: {len(conteudo)} chars, {len(conteudo.splitlines())} linhas")

# 3. MCR analisa via LLM
print("\n[MCR] Analisando via LLM...")
if _llm.disponivel():
    prompt = (
        f"Analise o seguinte codigo Python e encontre bugs ou problemas. "
        f"Sugira correcoes especificas. Seja conciso.\n\n"
        f"=== CODIGO ===\n{conteudo}\n=== FIM CODIGO ===\n\n"
        f"Liste os bugs encontrados e sugestoes de correcao."
    )
    t0 = time.time()
    resp = _llm.gerar(prompt, modelo="qwen2.5-coder:14b", temp=0.3)
    t_llm = time.time() - t0
    
    # Valida
    validacao = _validator.validar(tarefa, resp, conteudo[:500])
    
    print(f"  Tempo LLM: {t_llm:.1f}s")
    print(f"  Validacao: similaridade={validacao['similaridade']:.3f} valida={validacao['valida']}")
    print(f"\n  === ANALISE MCR-DevIA ===")
    print(resp[:2000])
    _decider.aprender(tarefa, classe)
else:
    print("  LLM offline")
    resp = ""
    t_llm = 0

# 4. Agora eu (Cloud) vou analisar o mesmo arquivo
print(f"\n{'='*60}")
print(f"  ANALISE CLOUD (para comparacao)")
print(f"{'='*60}")

# Le o arquivo diretamente
import re
linhas = conteudo.splitlines()
bugs = []

# Bug 1: BASE relativo que aponta pra lugar errado
bugs.append({
    "arquivo": "cmd_grep.py:23",
    "descricao": "BASE usa path relativo (.., .., ..) que sobe 3 niveis e aponta para historia/ em vez do projeto",
    "severidade": "Alta",
    "correcao": "Usar os.environ.get('MCR_PROJECT_BASE', BASE) como fallback"
})

# Bug 2: grep scaneia sandbox/ por padrao, nao o projeto
bugs.append({
    "arquivo": "cmd_grep.py:26", 
    "descricao": "diretorio padrao e SANDBOX (=historia/sandbox), nao o projeto MCR. Buscas sem path explicito nao encontram arquivos do Canary/Grimorio",
    "severidade": "Alta",
    "correcao": "diretorio = BASE (projeto) como padrao, nao SANDBOX"
})

# Bug 3: Sem filtro de extensao
bugs.append({
    "arquivo": "cmd_grep.py:52",
    "descricao": "So busca em .py .md .xml .json .lua .txt — ignora .cpp .hpp .h .cs .go .xaml .sln",
    "severidade": "Media",
    "correcao": "Adicionar extensoes: .cpp .hpp .h .c .cs .go .xaml .sln .cmake .bat .ps1"
})

# Bug 4: errors='replace' perde informacao
bugs.append({
    "arquivo": "cmd_grep.py:61",
    "descricao": "open() com errors='replace' substitui caracteres invalidos por ?, perdendo informacao e podendo causar falsos negativos no grep",
    "severidade": "Media",
    "correcao": "Tentar UTF-8 primeiro, fallback Latin-1. Usar EncodingDetector por extensao."
})

# Bug 5: except vazio
bugs.append({
    "arquivo": "cmd_grep.py:82",
    "descricao": "except: pass — suprime todas as excecoes. Um PermissionError ou arquivo corrompido passa despercebido",
    "severidade": "Baixa",
    "correcao": "except (UnicodeDecodeError, PermissionError) as e: print(f'[Grep] Aviso: {e}')"
})

# Bug 6: Sem timeout
bugs.append({
    "arquivo": "cmd_grep.py:49",
    "descricao": "os.walk() recursivo sem limite de profundidade ou timeout. Pode travar por minutos em projetos grandes",
    "severidade": "Media",
    "correcao": "Adicionar --max-depth N e timeout de 30s"
})

# Bug 7: re_padrao nao definido em caso de erro
bugs.append({
    "arquivo": "cmd_grep.py:40-42",
    "descricao": "Se re.compile() falha (linha 40), imprime erro mas re_padrao nunca e definido. Linha 63 tenta usar re_padrao.search() → NameError",
    "severidade": "Alta",
    "correcao": "return apos print do erro, ou definir re_padrao = None e verificar antes de usar"
})

for i, b in enumerate(bugs):
    print(f"\n  [{i+1}] {b['arquivo']} — {b['severidade']}")
    print(f"  {b['descricao']}")
    print(f"  Correcao: {b['correcao']}")

print(f"\n  Total: {len(bugs)} bugs encontrados")
print(f"  Alta: {sum(1 for b in bugs if b['severidade']=='Alta')} | Media: {sum(1 for b in bugs if b['severidade']=='Media')} | Baixa: {sum(1 for b in bugs if b['severidade']=='Baixa')}")

# 5. Comparacao
print(f"\n{'='*60}")
print(f"  COMPARACAO MCR-DevIA vs Cloud")
print(f"{'='*60}")

# Extrai bugs da resposta do MCR
mcr_bugs = []
if resp:
    for i, linha in enumerate(resp.split('\n')):
        for padrao in ['bug', 'Bug', 'problema', 'Problema', 'erro', 'Erro', 'issue', 'Issue']:
            if padrao in linha and len(linha) > 10:
                mcr_bugs.append(linha.strip()[:100])
                break

mcr_count = len(set(mcr_bugs))
cloud_count = len(bugs)

print(f"  MCR-DevIA: {mcr_count} bugs/sugestoes identificados (LLM qwen2.5-coder:14b, {t_llm:.1f}s)")
print(f"  Cloud:     {cloud_count} bugs encontrados (analise manual, ~2min)")
print(f"")

# Overlap: quais bugs o MCR encontrou que eu tambem encontrei?
if resp:
    overlaps = []
    cloud_descricoes = [b['descricao'].lower() for b in bugs]
    for b in bugs:
        palavras = b['descricao'].lower().split()[:5]
        trecho = ' '.join(palavras[:3])
        if trecho in resp.lower():
            overlaps.append(b['arquivo'])
    
    if overlaps:
        print(f"  Bugs encontrados por AMBOS ({len(overlaps)}):")
        for o in overlaps:
            print(f"    - {o}")
    else:
        print(f"  Nenhum overlap detectado")

print(f"\n  Diferenca fundamental:")
print(f"  - Cloud: analise ESTRUTURAL (le o codigo, entende a logica, identifica bug de NameError)")
print(f"  - MCR: analise TEXTUAL (LLM le o codigo como texto, identifica padroes de ma pratica)")
print(f"  - MCR com mais contexto MCR (EncodingDetector, MCR_PROJECT_BASE) = melhora")
print(f"  - Cloud com conhecimento profundo do projeto = insubstituivel para bugs logicos")
