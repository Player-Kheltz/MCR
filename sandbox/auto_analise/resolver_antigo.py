"""MCR-DevIA escaneia e resolve TESTE CEGO ULTRA"""
import os, re, json, urllib.request, sys

# === DETECTORES AUTO-GERADOS ===

def detectar_loot_invalido(texto):
    for m in re.finditer(r'addLoot\((\d+),\s*([\d.]+)\)', texto):
        if float(m.group(2)) > 1.0:
            return True
    return False

def detectar_sql_injection(texto):
    """Detecta concatenacao direta em SQL sem db.escapeString().
    
    Ignora:
    - .. numero literal (ex: .. 123)
    - .. db.escapeString (ja seguro)
    - .. variavel com sufixo de numero (Id, Count, Num, Qty, etc)
    - .. metodo que retorna numero (:getId(), :getCount(), etc)
    """
    # Lista de sufixos que indicam variavel numerica
    SUFIXOS_NUM = ('id', 'Id', 'ID', 'count', 'Count', 'num', 'Num', 'qty', 'Qty',
                   'index', 'level', 'Level', 'valor', 'total', 'max', 'min')
    
    for m in re.finditer(r'db\.\w+\s*\(\s*"[^"]*"(?:\s*\.\.\s*(\w+(?::\w+\([^)]*\))?))', texto):
        var = m.group(1)
        if not var: continue
        if var == 'db': continue  # db.escapeString ja seguro
        if var in ('true', 'false', 'nil'): continue
        if re.match(r'^\d', var): continue  # numero literal
        
        # Verifica se o nome da variavel sugere numero
        if any(var.endswith(suf) for suf in SUFIXOS_NUM):
            continue
        # Verifica se metodo retorna numero (ex: :getId(), :getNumber())
        if re.search(r':\w*[Gg]et\w*[Ii][Dd]\b', var):
            continue
        if re.search(r':\w*[Ii][Dd]\b', var):
            continue
        
        # Verifica se a linha tem escapeString
        linha = texto[m.start():m.end()+100]
        if 'escapeString' in linha:
            continue
        
        return True
    return False

def detectar_loop_infinito(texto):
    if 'while true do' in texto and 'break' not in texto:
        return True
    return False

def detectar_setmetatable(texto):
    if 'setmetatable' in texto:
        return True
    return False

def detectar_encoding_latin1(path):
    try:
        with open(path, 'rb') as f:
            raw = f.read(2000)
        raw.decode('utf-8')
        return False
    except UnicodeDecodeError:
        try:
            raw.decode('latin-1')
            return True
        except:
            return False
    return False

def detectar_variavel_global(texto):
    """Detecta variavel global suspeita: nivel superior sem local.
    
    Ignora padroes Lua normais:
    - Ns = {} ou Ns = Ns or {}  (namespaces intencionais)
    - NOME = valor  (constantes com nome MAIUSCULO)
    - _G.xxx (intencional)
    - Variaveis comeca com maiuscula (convencao de modulo Lua)
    """
    nivel_chaves = 0
    for linha in texto.split('\n'):
        nivel_chaves += linha.count('{') - linha.count('}')
        if nivel_chaves > 0:
            continue
        m = re.match(r'^(\w+)\s*=\s*[^=]', linha)
        if not m:
            continue
        var = m.group(1)
        if var in ('return', 'true', 'false', 'nil'):
            continue
        if 'local' in linha or 'function' in linha:
            continue
        # Ignora padroes Lua normais:
        #   Nome = {}, Nome = Nome or {}  (namespaces/modulos)
        #   NOME = valor (constantes maiusculas)
        #   Nome = valor (convencao modulo PascalCase)
        if re.search(r'=\s*\{\}', linha): continue
        if re.search(r'=\s*\w+\s+or\s+\{', linha): continue
        if var[0].isupper(): continue
        return True
    return False

def detectar_codigo_morto(texto):
    """DESABILITADO: produz muitos falsos positivos (returns em branches condicionais).
    Para detectar codigo morto real seria necessaria analise de fluxo de controle."""
    return False

def detectar_chave_string_numero(texto):
    if re.search(r'\[\s*"\d+"\s*\]', texto) and re.search(r'\[\s*\d+\s*\]', texto):
        return True
    return False

def detectar_sintaxe_python(texto):
    """Detecta Python usando word boundary (\b) para evitar falsos positivos.
    def, class, import sao PALAVRAS RESERVADAS do Python que NAO existem em Lua.
    from e print existem em Lua como variavel/funcao — ignorar."""
    for linha in texto.split('\n'):
        if re.search(r'\b(def|class|import)\b', linha):
            # Verifica se parece codigo Python (nao e comentario Lua)
            linha_clean = linha.split('--')[0].strip()
            if re.match(r'^\s*(def\b|class\b|import\b)', linha_clean):
                return True
    return False

def detectar_nil_desnecessario(texto):
    """Detecta .campo = nil apenas se NAO for padrao de limpeza de estado.
    Ignora: data.X = nil, self.X = nil, tempData[X] = nil."""
    for m in re.finditer(r'\.(\w+)\s*=\s*nil', texto):
        # Pega o contexto antes do .campo
        ini = max(0, m.start() - 30)
        ctx = texto[ini:m.start()]
        # Ignora se for limpeza de estado (data., self., tempData, etc.)
        if re.search(r'(data|self|tempData|player|creature)$', ctx):
            continue
        return True
    return False

OLLAMA_URL = 'http://localhost:11434/api/generate'
BASE = r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades'  # ALVO: habilidades reais do MCR

def ia(prompt):
    try:
        d = json.dumps({'model':'qwen2.5-coder:7b','prompt':prompt,'stream':False,
            'options':{'temperature':0.4,'num_ctx':4096}}).encode()
        r = urllib.request.Request(OLLAMA_URL,data=d,headers={'Content-Type':'application/json'})
        return json.loads(urllib.request.urlopen(r,timeout=60).read()).get('response','')
    except: return None

def scan(arquivo, path):
    """Tenta detectar problemas em um arquivo."""
    with open(path, 'rb') as f:
        raw = f.read()
    
    problemas = []
    
    # 1. BOM / encoding
    if raw[:3] == b'\xef\xbb\xbf':
        problemas.append('arquivo com BOM')
    
    # Tenta ler como texto
    try:
        texto = raw.decode('utf-8')
    except UnicodeDecodeError:
        try:
            texto = raw.decode('latin-1')
            problemas.append('encoding Latin-1 em vez de UTF-8')
        except:
            problemas.append('encoding nao identificado')
        
    # 2. Loot chance > 1.0
    for m in re.finditer(r'addLoot\((\d+),\s*([\d.]+)\)', texto):
        chance = float(m.group(2))
        if chance > 1.0:
            problemas.append(f'loot_chance = {chance} (max 1.0)')
    
    # 3. Divisao por zero potencial
    for m in re.finditer(r'/\s*\(([^)]+)\)', texto):
        expr = m.group(1)
        if re.search(r'\bdef\b|\bvalor\b|\-\s*\d+', expr):
            problemas.append(f'divisao por zero potencial: {expr}')
    
    # 4. Nome de arquivo longo
    nome_arquivo = os.path.basename(arquivo)
    if len(nome_arquivo) > 60:
        problemas.append(f'nome de arquivo longo ({len(nome_arquivo)} chars)')
    



    # AUTO-INTEGRACAO: chamar detectores
    for nome, fn in list(globals().items()):
        if nome.startswith('detectar_') and callable(fn):
            try:
                if fn(texto):
                    problemas.append(nome.replace('detectar_', '').replace('_', ' '))
            except:
                pass

    return problemas

if __name__ == '__main__':
    print('='*60)
    print('  MCR-DevIA — TESTE CEGO ULTRA')
print(f'  Escaneando {BASE}')
print('='*60)

total = 0
encontrados = 0

for root, dirs, files in os.walk(BASE):
    for f in sorted(files):
        if f == '.GABARITO.txt': continue
        if '.bak' in f.lower(): continue  # Ignora backups
        path = os.path.join(root, f)
        problemas = scan(f, path)
        total += 1
        
        if problemas:
            encontrados += 1
            san = f.replace('\n', ' ').encode('ascii', 'replace').decode('ascii')
            print(f'\n  [!] {san}:')
            for p in problemas:
                ps = p.encode('ascii', 'replace').decode('ascii')
                print(f'    - {ps}')
        else:
            print(f'\n  [OK] {f}: nenhum problema detectado')

print(f'\n{"="*60}')
print(f'  RESULTADO: {encontrados}/{total} arquivos com problemas detectados')
print(f'{"="*60}')

# Tenta corrigir com IA
print(f'\n{"="*60}')
print(f'  MODO ESCUTA: detectando sem corrigir (projeto real)')
print(f'{"="*60}')
