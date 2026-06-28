"""
MEMORIA PERMANENTE — MCR-DevIA
Download completo → arquivo em disco → Context Infinity fragmenta → KG referencia
"""
import subprocess, sys, os, json, time, urllib.request, re

MCR = [sys.executable, os.path.join("E:\\Projeto MCR", "scripts", "mcr_devia", "mcr_devia.py")]
KG_PATH = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
WEBLEARN_DIR = "E:\\Modelos IA\\weblearn"
os.makedirs(WEBLEARN_DIR, exist_ok=True)
os.makedirs(os.path.join(WEBLEARN_DIR, "raw"), exist_ok=True)
os.makedirs(os.path.join(WEBLEARN_DIR, "fragments"), exist_ok=True)

# MESMAS 53 FONTES (do plano_aprendizado)
FONTES = [
    ("Python_Tutorial", "https://docs.python.org/3/tutorial/", 1),
    ("Python_Library", "https://docs.python.org/3/library/", 1),
    ("Python_Awesome", "https://github.com/vinta/awesome-python", 1),
    ("Python_Cookbook", "https://github.com/dabeaz/python-cookbook", 1),
    ("Lua_Manual", "https://www.lua.org/manual/5.4/", 1),
    ("Lua_PIL_Book", "https://www.lua.org/pil/", 1),
    ("Lua_Awesome", "https://github.com/LewisJEllis/awesome-lua", 1),
    ("CPP_Reference", "https://en.cppreference.com/w/", 1),
    ("CPP_Awesome", "https://github.com/fffaraz/awesome-cpp", 1),
    ("CPP_Guidelines", "https://github.com/isocpp/CppCoreGuidelines", 1),
    ("MDN_JS_Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", 1),
    ("MDN_JS_Ref", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference", 1),
    ("TS_Handbook", "https://www.typescriptlang.org/docs/handbook/", 1),
    ("JS_Awesome", "https://github.com/sorrycc/awesome-javascript", 1),
    ("Postgres_Tutorial", "https://www.postgresql.org/docs/current/tutorial.html", 1),
    ("Go_Tour", "https://go.dev/tour/", 2),
    ("Go_Docs", "https://go.dev/doc/", 2),
    ("Go_Awesome", "https://github.com/avelino/awesome-go", 2),
    ("Rust_Book", "https://doc.rust-lang.org/book/", 2),
    ("Rust_Ref", "https://doc.rust-lang.org/reference/", 2),
    ("Rust_Awesome", "https://github.com/rust-unofficial/awesome-rust", 2),
    ("C_Reference", "https://en.cppreference.com/w/c", 2),
    ("GNU_C_Manual", "https://www.gnu.org/software/gnu-c-manual/", 2),
    ("Java_Tutorials", "https://docs.oracle.com/javase/tutorial/", 3),
    ("Java_Awesome", "https://github.com/akullpp/awesome-java", 3),
    ("CSharp_Docs", "https://learn.microsoft.com/en-us/dotnet/csharp/", 3),
    ("CSharp_Awesome", "https://github.com/quozd/awesome-dotnet", 3),
    ("PHP_Manual", "https://www.php.net/manual/en/", 3),
    ("PHP_Awesome", "https://github.com/ziadoz/awesome-php", 3),
    ("Ruby_Docs", "https://www.ruby-lang.org/en/documentation/", 3),
    ("Ruby_Awesome", "https://github.com/markets/awesome-ruby", 3),
    ("Kotlin_Docs", "https://kotlinlang.org/docs/home.html", 4),
    ("Kotlin_Awesome", "https://github.com/KotlinBy/awesome-kotlin", 4),
    ("Swift_Book", "https://docs.swift.org/swift-book/", 4),
    ("Swift_Awesome", "https://github.com/matteocrippa/awesome-swift", 4),
    ("Dart_Guides", "https://dart.dev/guides", 4),
    ("Flutter_Docs", "https://docs.flutter.dev/", 4),
    ("Elixir_Docs", "https://elixir-lang.org/docs.html", 4),
    ("Elixir_Awesome", "https://github.com/h4cc/awesome-elixir", 4),
    ("Haskell_Docs", "https://www.haskell.org/documentation/", 4),
    ("Haskell_Awesome", "https://github.com/krispo/awesome-haskell", 4),
    ("Git_SCM", "https://git-scm.com/doc", 5),
    ("Pro_Git_Book", "https://git-scm.com/book/en/v2", 5),
    ("Docker_Docs", "https://docs.docker.com/", 5),
    ("Bash_Manual", "https://www.gnu.org/software/bash/manual/", 5),
    ("Bash_Awesome", "https://github.com/awesome-lists/awesome-bash", 5),
    ("Canary", "https://github.com/opentibiabr/canary", 6),
    ("OTClient", "https://github.com/edubart/otclient", 6),
    ("TFS", "https://github.com/otland/forgottenserver", 6),
    ("Redis", "https://github.com/redis/redis", 6),
    ("SQLite", "https://github.com/sqlite/sqlite", 6),
    ("LuaJIT", "https://github.com/LuaJIT/LuaJIT", 6),
    ("nginx", "https://github.com/nginx/nginx", 6),
]

def mcr(*args, timeout=30):
    inicio = time.time()
    try:
        r = subprocess.run(MCR + list(args), capture_output=True, timeout=timeout)
        return r.stdout.decode('utf-8', errors='replace')[:500], round(time.time()-inicio, 1)
    except:
        return "[ERRO]", round(time.time()-inicio, 1)

def salvar_fragmentos(nome, texto_base, raw_path):
    """Fragmenta o texto em buffers e salva cada um como arquivo."""
    TAM = 5000
    partes = [texto_base[i:i+TAM] for i in range(0, len(texto_base), TAM)]
    frag_dir = os.path.join(WEBLEARN_DIR, "fragments", nome)
    os.makedirs(frag_dir, exist_ok=True)
    
    for i, parte in enumerate(partes):
        if not parte.strip():
            continue
        frag_path = os.path.join(frag_dir, f"{i:04d}.txt")
        with open(frag_path, "w", encoding="utf-8") as f:
            f.write(parte)
    
    return len(partes)

print("=" * 70)
print("MEMORIA PERMANENTE — MCR-DevIA")
print("=" * 70)

for idx, (nome, url, fase) in enumerate(FONTES, 1):
    print(f"\n[{idx}/53] Fase {fase} | {nome}")
    
    # 1. Download completo
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=60)
        raw_html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  ERRO DOWNLOAD: {e}")
        continue
    
    # 2. Salva RAW (HTML original)
    raw_path = os.path.join(WEBLEARN_DIR, "raw", f"{nome}.html")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(raw_html)
    
    # 3. Limpa HTML
    texto_limpo = re.sub(r'<[^>]+>', ' ', raw_html)
    texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
    
    # 4. Salva texto limpo completo
    txt_path = os.path.join(WEBLEARN_DIR, "raw", f"{nome}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(texto_limpo)
    
    # 5. Fragmenta em buffers de 5K e salva cada um
    num_frag = salvar_fragmentos(nome, texto_limpo, raw_path)
    
    print(f"  RAW: {len(raw_html)//1000}KB | TXT: {len(texto_limpo)//1000}KB | Fragmentos: {num_frag}")
    
    # 6. Registra no KG (resumo + referencia)
    resumo = f"WebLearn: {nome} | URL: {url} | RAW: {raw_path} | TXT: {txt_path} | Fragmentos: {num_frag} | Fase: {fase}"
    saida, tempo = mcr("ensinar", f"WebLearn: {nome}", f"Memoria permanente em {txt_path}", resumo, "weblearn_permanente")

print(f"\n\nMemoria permanente salva em: {WEBLEARN_DIR}")

# Estatisticas finais
raw_size = sum(os.path.getsize(os.path.join(WEBLEARN_DIR, "raw", f)) for f in os.listdir(os.path.join(WEBLEARN_DIR, "raw")) if f.endswith(('.html','.txt')))
frag_count = sum(len(files) for _, _, files in os.walk(os.path.join(WEBLEARN_DIR, "fragments")))
print(f"\nRAW: {raw_size//1024//1024}MB")
print(f"Fragmentos: {frag_count}")
print(f"KG: lessons de weblearn registradas")
