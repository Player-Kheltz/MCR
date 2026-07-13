"""Comando: explorar - Escaneia e aprende com IA minima + Orquestrador Universal."""
import os, re, json, hashlib, time, sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def register():
    return {
        "name": "explorar",
        "desc": "Escaneia projeto e aprende. Usa Orquestrador Universal para nomes desconhecidos.",
        "handler": execute,
        "args": [{"name": "alvo", "type": "str", "required": False}],
        "categoria": "kg",
    }

_CACHE_NOMES = {}

def _categorizar_nome(nome):
    nome_lower = nome.lower()
    if nome_lower.startswith('_'): return 'define/macro'
    if nome_lower.endswith(('manager','handler')): return 'gerenciador'
    if nome_lower.endswith(('factory','builder')): return 'construtor'
    if nome_lower.endswith(('repository','dao')): return 'dados'
    if nome_lower.endswith('service'): return 'servico'
    if nome_lower.endswith('controller'): return 'controle'
    if nome_lower.endswith('config'): return 'configuracao'
    if nome_lower.endswith(('test','spec')): return 'teste'
    if nome_lower.endswith(('exception','error')): return 'erro'
    if nome_lower.endswith(('util','helper')): return 'utilitario'
    if nome_lower.endswith(('model','entity')): return 'modelo'
    return 'desconhecido'

def execute(kg, ia, args, ctx_crew=None):
    if not kg:
        print('[Explorar] KG nao disponivel')
        return True
    
    alvo = args[0] if args else 'tudo'
    total = 0
    
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from modulos.lessons_buffer import LessonsBuffer
    buf = LessonsBuffer(kg)
    MANIFEST_PATH = os.path.join(BASE, 'sandbox', '.mcr_devia', 'file_manifest.json')
    
    manifest = {}
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception: pass
    
    if alvo in ('codigo', 'tudo'):
        print('[Explorar] Escaneando scripts/...')
        src_dir = os.path.join(BASE, 'scripts')
        novos_nomes = {}
        
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__', 'vcpkg'))]
            for f in files:
                if not f.endswith('.py'): continue
                fpath = os.path.join(root, f)
                rel = os.path.relpath(fpath, BASE)
                try:
                    with open(fpath, 'rb') as fh:
                        h = hashlib.sha256(fh.read()).hexdigest()
                except Exception: continue
                if rel in manifest and manifest.get(rel) == h: continue
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                        content = fh.read(3000)
                    nomes = re.findall(r'(?:class|def)\s+(\w+)', content)
                    for nome in nomes:
                        if nome not in novos_nomes: novos_nomes[nome] = []
                        novos_nomes[nome].append(rel)
                except Exception: pass
        
        print(f'  {len(novos_nomes)} nomes novos em {sum(1 for v in novos_nomes.values() for _ in v)} arquivos')
        
        for nome, arquivos in sorted(novos_nomes.items()):
            categoria = _categorizar_nome(nome)
            buf.adicionar(erro=f"Code: {nome}", causa=f"Arquivos: {', '.join(arquivos)}",
                          solucao=f"Categoria: {categoria}. Encontrado em {arquivos[0]}",
                          ctx="conhecimento", fonte=arquivos[0])
            total += 1
        
        # Usa Orquestrador para nomes desconhecidos
        desconhecidos = [n for n in novos_nomes if _categorizar_nome(n) == 'desconhecido']
        if desconhecidos and ia and hasattr(ia, 'orquestrar') and len(desconhecidos) <= 20:
            print(f'  Orquestrador interpretando {len(desconhecidos)} nomes desconhecidos...')
            lote = ', '.join(desconhecidos)
            r = ia.orquestrar("classificar_nomes", {"itens": lote},
                            consulta="classificar nomes", temp=0.2)
            if r:
                print(f'    Classificacao: {r}')
        elif desconhecidos and ia and len(desconhecidos) <= 20:
            print(f'  IA interpretando {len(desconhecidos)} nomes desconhecidos...')
            lote = ', '.join(desconhecidos)
            r = ia.fast(
                f"Classifique cada item em UMA palavra: gerenciador, dados, servico, controle, modelo, util, outro.\n{lote}",
                0.2
            ) or ''
        
        novo_manifest = {}
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__', 'vcpkg'))]
            for f in files:
                if not f.endswith('.py'): continue
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, 'rb') as fh:
                        novo_manifest[os.path.relpath(fpath, BASE)] = hashlib.sha256(fh.read()).hexdigest()
                except Exception: pass
        os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(novo_manifest, f, ensure_ascii=False, indent=2)
    
    if total > 0:
        print(f'[Explorar] {total} ao buffer')
        contradicoes = buf.verificar_contradicoes()
        if contradicoes:
            print(f'[Explorar] {len(contradicoes)} contradicoes')
            buf.resolver_contradicoes()
        comitadas = buf.comitar()
        print(f'[Explorar] {comitadas} commitadas')
    else:
        print('[Explorar] Nenhum arquivo novo')
    
    return True
