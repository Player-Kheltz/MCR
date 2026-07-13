"""Comando: aprender_conceito - APRENDE QUALQUER CONCEITO do projeto (codigo + docs).
Usa Orquestrador Universal para sintese de conhecimento.
Busca em TODO o projeto: src/, data/, scripts/, Docs/, config/, sandbox/, raiz."""
import os, re, sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SANDBOX = os.path.join(BASE, 'sandbox')

EXT_CODIGO = ('.py', '.lua', '.cpp', '.hpp', '.h', '.c', '.cs', '.java', '.js', '.ts', '.sql')
EXT_DOCS = ('.md', '.txt', '.cfg', '.yaml', '.yml', '.ini', '.toml', '.json', '.xml', '.cfgx', '.conf')
EXT_TODAS = EXT_CODIGO + EXT_DOCS

def register():
    return {
        "name": "aprender_conceito",
        "desc": "APRENDE QUALQUER CONCEITO do projeto (codigo + docs) e salva como conhecimento conceitual no KG. Universal.",
        "handler": execute,
        "args": [{"name": "conceito", "type": "str", "required": True}],
        "categoria": "kg",
    }

def execute(kg, ia, args, ctx_crew=None):
    if not args or not kg:
        print('[Conceito] Uso: aprender_conceito <conceito>')
        return True
    
    conceito = ' '.join(args)
    print(f'[MCR-DevIA] Aprendendo conceito: {conceito}')
    termo = conceito.strip().lower()
    
    # Buscar em TODO o projeto
    arquivos_rel = []
    base_dirs = [
        os.path.join(BASE, 'src'), os.path.join(BASE, 'data'),
        os.path.join(BASE, 'scripts'), os.path.join(BASE, 'docs'),
        os.path.join(BASE, 'config'), os.path.join(BASE, 'sandbox'),
        os.path.join(SANDBOX, '.mcr_devia', 'weblearn'), BASE,
    ]
    
    for bd in base_dirs:
        if not os.path.isdir(bd): continue
        for root, dirs, files in os.walk(bd):
            dirs[:] = [d for d in dirs if not d.startswith(('.', 'vcpkg', '__pycache__',
                       'node_modules', 'build', 'bin', 'obj', '.git', 'tmp'))]
            for f in files:
                if not f.endswith(EXT_TODAS): continue
                if f.endswith('.md') and 'changelog' in f.lower(): continue
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                        conteudo = fp.read(50000)
                    cnt = conteudo.lower().count(termo)
                    if cnt > 0:
                        arquivos_rel.append((cnt, fpath, len(conteudo)))
                except Exception: pass
    
    if not arquivos_rel:
        print(f'  [Conceito] Nenhum arquivo encontrado para "{conceito}"')
        return True
    
    PESO_DIR = {
        'docs': 100, 'scripts': 10, 'sandbox': 5,
        'weblearn': 3, 'src': 2, 'data': 1,
    }
    arquivos_rank = []
    for cnt, fpath, tam in arquivos_rel:
        fpath_lower = fpath.lower()
        dir_peso = 1
        for chave, p in PESO_DIR.items():
            if chave in fpath_lower.split(os.sep):
                dir_peso = p; break
        densidade_relativa = cnt / max(tam, 1) * 10000
        peso = densidade_relativa * dir_peso
        if dir_peso >= 100 and fpath.endswith(('.md', '.txt')):
            peso *= 3
        arquivos_rank.append((peso, cnt, fpath, tam))
    
    arquivos_rank.sort(key=lambda x: -x[0])
    
    print(f'  [Conceito] {len(arquivos_rank)} arquivos encontrados. Top 5:')
    for i, (peso, cnt, fpath, tam) in enumerate(arquivos_rank):
        rel = os.path.relpath(fpath, BASE)
        print(f'    #{i+1} peso={peso:.1f} ocorr={cnt} tam={tam} {rel}')
    
    # Monta contexto dos top 6 arquivos
    from context_infinity import OrquestradorContexto, FragmentoContexto
    from modulos.util import _get_modelo
    orq = OrquestradorContexto(modelo=_get_modelo("leve")["modelo"])
    
    for idx, (peso, cnt, fpath, tam) in enumerate(arquivos_rank):
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                conteudo = fp.read(50000)
        except Exception:
            continue
        if tam <= 3000:
            snippet = conteudo
        else:
            meio = tam // 2
            snippet = conteudo + '\n...\n' + conteudo[meio:meio+1500]
        rel = os.path.relpath(fpath, BASE)
        tipo = "codigo" if fpath.endswith(EXT_CODIGO) else "texto"
        frag = FragmentoContexto(
            id=f"conceito_{conceito}_{idx}",
            conteudo=f"--- {rel} ({tipo.upper()}) ---\n{snippet}",
            origem=rel, prioridade=max(10, 80 - idx * 10), tipo=tipo
        )
        orq.adicionar(frag)
    
    contexto = ''
    tokens_alvo = orq.ctx_max - 500
    partes = []
    tokens_usados = 0
    for frag in sorted(orq.fragmentos.values(), key=lambda f: -f.prioridade):
        if tokens_usados + frag.tokens <= tokens_alvo:
            partes.append(frag.conteudo)
            tokens_usados += frag.tokens
    if not partes:
        print(f'  [Conceito] Contexto vazio apos filtragem')
        return True
    contexto = '\n\n'.join(partes)
    
    # ORQUESTRADOR UNIVERSAL: gera o prompt de sintese sob demanda
    if ia and hasattr(ia, 'orquestrar'):
        r = ia.orquestrar("conceito", {
            "conceito": conceito,
            "contexto": contexto,
        }, consulta=conceito, temp=0.3)
    else:
        # Fallback via IA direta
        prompt_ia = (
            f"O projeto MCR e um servidor CUSTOMIZADO de Tibia baseado em Canary (OTServ).\n"
            f"SPA = Sistema de Progressao do Aventureiro, SHC = Sistema de Habilidades Contextuais.\n"
            f"Analise o CODIGO e a DOCUMENTACAO abaixo e extraia conhecimento CONCEITUAL sobre '{conceito}'.\n\n"
            f"NAO use significados genericos da sigla.\n"
            f"Explique o CONCEITO - o que e, como funciona, para que serve.\n"
            f"Inclua detalhes tecnicos e especificos da documentacao.\n\n"
            f"Contexto:\n{contexto}\n\n"
            f"Produza um paragrafo conciso (3-5 frases)."
        )
        if ia:
            r = ia.gerar(prompt_ia, 0.3)
        else:
            from modulos.util import gerar as _gerar_ac
            r = _gerar_ac(prompt_ia, 0.3, "conceito")
    
    if r and len(r) > 30:
        print(f'\n[Conceito] {r}')
        kg.aprender(
            erro=f"O que e {conceito}?",
            causa=f"Analise de codigo fonte e documentacao do projeto MCR ({len(arquivos_rel)} arquivos encontrados)",
            solucao=r.strip(),
            ctx="conceito_projeto"
        )
        print(f'  [Conceito] Salvo no KG')
    else:
        print(f'  [Conceito] Falha ao sintetizar')
    
    return True
