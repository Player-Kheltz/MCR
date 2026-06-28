"""
APRENDIZADO AUTONOMO — MCR-DevIA + Web Learner
Executa o plano completo de 53 fontes automaticamente.
Para cada fonte: download -> IA le e entende -> Context Infinity fragmenta -> KG guarda
"""
import subprocess, sys, os, json, time, urllib.request, re

MCR = [sys.executable, os.path.join("E:\\Projeto MCR", "scripts", "mcr_devia", "mcr_devia.py")]
KG_PATH = "E:\\Projeto MCR\\sandbox\\.mcr_devia\\knowledge.json"
REPORT_PATH = "E:\\Projeto MCR\\sandbox\\testes_extensivos\\relatorio_aprendizado.json"

# === TODAS AS 53 FONTES ===
FONTES = [
    # FASE 1: Linguagens Principais (15 fontes)
    ("Python Tutorial", "https://docs.python.org/3/tutorial/", 1),
    ("Python Library", "https://docs.python.org/3/library/", 1),
    ("Python Awesome", "https://github.com/vinta/awesome-python", 1),
    ("Python Cookbook", "https://github.com/dabeaz/python-cookbook", 1),
    ("Lua Manual 5.4", "https://www.lua.org/manual/5.4/", 1),
    ("Lua PIL Book", "https://www.lua.org/pil/", 1),
    ("Lua Awesome", "https://github.com/LewisJEllis/awesome-lua", 1),
    ("C++ Reference", "https://en.cppreference.com/w/", 1),
    ("C++ Awesome", "https://github.com/fffaraz/awesome-cpp", 1),
    ("C++ Guidelines", "https://github.com/isocpp/CppCoreGuidelines", 1),
    ("MDN JS Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", 1),
    ("MDN JS Reference", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference", 1),
    ("TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/", 1),
    ("JS Awesome", "https://github.com/sorrycc/awesome-javascript", 1),
    ("PostgreSQL Tutorial", "https://www.postgresql.org/docs/current/tutorial.html", 1),

    # FASE 2: Linguagens de Sistema (8 fontes)
    ("Go Tour", "https://go.dev/tour/", 2),
    ("Go Docs", "https://go.dev/doc/", 2),
    ("Go Awesome", "https://github.com/avelino/awesome-go", 2),
    ("Rust Book", "https://doc.rust-lang.org/book/", 2),
    ("Rust Reference", "https://doc.rust-lang.org/reference/", 2),
    ("Rust Awesome", "https://github.com/rust-unofficial/awesome-rust", 2),
    ("C Reference", "https://en.cppreference.com/w/c", 2),
    ("GNU C Manual", "https://www.gnu.org/software/gnu-c-manual/", 2),

    # FASE 3: Linguagens de Plataforma (8 fontes)
    ("Java Tutorials", "https://docs.oracle.com/javase/tutorial/", 3),
    ("Java Awesome", "https://github.com/akullpp/awesome-java", 3),
    ("C# Docs", "https://learn.microsoft.com/en-us/dotnet/csharp/", 3),
    ("C# Awesome", "https://github.com/quozd/awesome-dotnet", 3),
    ("PHP Manual", "https://www.php.net/manual/en/", 3),
    ("PHP Awesome", "https://github.com/ziadoz/awesome-php", 3),
    ("Ruby Docs", "https://www.ruby-lang.org/en/documentation/", 3),
    ("Ruby Awesome", "https://github.com/markets/awesome-ruby", 3),

    # FASE 4: Mobile e Modernas (10 fontes)
    ("Kotlin Docs", "https://kotlinlang.org/docs/home.html", 4),
    ("Kotlin Awesome", "https://github.com/KotlinBy/awesome-kotlin", 4),
    ("Swift Book", "https://docs.swift.org/swift-book/", 4),
    ("Swift Awesome", "https://github.com/matteocrippa/awesome-swift", 4),
    ("Dart Guides", "https://dart.dev/guides", 4),
    ("Flutter Docs", "https://docs.flutter.dev/", 4),
    ("Elixir Docs", "https://elixir-lang.org/docs.html", 4),
    ("Elixir Awesome", "https://github.com/h4cc/awesome-elixir", 4),
    ("Haskell Docs", "https://www.haskell.org/documentation/", 4),
    ("Haskell Awesome", "https://github.com/krispo/awesome-haskell", 4),

    # FASE 5: DevOps e Ferramentas (5 fontes)
    ("Git SCM Docs", "https://git-scm.com/doc", 5),
    ("Pro Git Book", "https://git-scm.com/book/en/v2", 5),
    ("Docker Docs", "https://docs.docker.com/", 5),
    ("Bash Manual", "https://www.gnu.org/software/bash/manual/", 5),
    ("Bash Awesome", "https://github.com/awesome-lists/awesome-bash", 5),

    # FASE 6: Projetos Reais (7 fontes)
    ("Canary Server", "https://github.com/opentibiabr/canary", 6),
    ("OTClient", "https://github.com/edubart/otclient", 6),
    ("TFS Original", "https://github.com/otland/forgottenserver", 6),
    ("Redis Source", "https://github.com/redis/redis", 6),
    ("SQLite Source", "https://github.com/sqlite/sqlite", 6),
    ("LuaJIT", "https://github.com/LuaJIT/LuaJIT", 6),
    ("nginx", "https://github.com/nginx/nginx", 6),
]

def mcr(*args, timeout=60):
    inicio = time.time()
    try:
        r = subprocess.run(MCR + list(args), capture_output=True, timeout=timeout)
        saida = r.stdout.decode('utf-8', errors='replace')[:500]
        return saida, round(time.time()-inicio, 1)
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", round(time.time()-inicio, 1)
    except Exception as e:
        return f"[ERRO] {e}", round(time.time()-inicio, 1)

print("=" * 70)
print("APRENDIZADO AUTONOMO — MCR-DevIA")
print(f"Total de fontes: {len(FONTES)}")
print("=" * 70)

resultados = []

for idx, (nome, url, fase) in enumerate(FONTES, 1):
    print(f"\n{'─'*50}")
    print(f"[{idx}/{len(FONTES)}] Fase {fase} | {nome}")
    print(f"  URL: {url[:80]}")
    print(f"{'─'*50}")
    
    # 1. Download COMPLETO + limpeza
    print(f"  Download...", end=" ")
    sys.stdout.flush()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=60)
        raw = resp.read().decode('utf-8', errors='replace')
        # Limpa HTML
        texto_limpo = re.sub(r'<[^>]+>', ' ', raw)
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
        print(f"OK ({len(raw)} raw -> {len(texto_limpo)} chars)")
    except Exception as e:
        print(f"ERRO: {e}")
        resultados.append({"nome": nome, "status": "ERRO_DOWNLOAD", "erro": str(e)[:100]})
        continue
    
    # 2. Fragmentar em buffers de ~5000 chars e ensinar cada um
    TAM_BUFFER = 5000
    buffers = [texto_limpo[i:i+TAM_BUFFER] for i in range(0, len(texto_limpo), TAM_BUFFER)]
    print(f"  Fragmentado em {len(buffers)} buffers de ~{TAM_BUFFER} chars")
    
    buffers_ok = 0
    for bi, buffer in enumerate(buffers):
        if not buffer.strip():
            continue
        saida, tempo = mcr("ensinar", 
            f"WebLearn: {nome} [parte {bi+1}/{len(buffers)}]", 
            f"Fonte: {url} | buffer {bi+1}",
            f"{buffer}",
            "weblearn")
        if "APRENDIDO" in saida:
            buffers_ok += 1
    
    print(f"  Buffers aprendidos: {buffers_ok}/{len(buffers)}")
    
    # 3. Registrar resultado
    resultados.append({
        "nome": nome, "url": url[:80], "fase": fase,
        "status": "OK" if buffers_ok > 0 else "FALHA",
        "buffers": len(buffers),
        "buffers_ok": buffers_ok,
        "chars_total": len(texto_limpo)
    })

# ================================================================
# RELATORIO FINAL
# ================================================================
print(f"\n\n{'='*70}")
print("RELATORIO FINAL DO APRENDIZADO AUTONOMO")
print(f"{'='*70}")

ok_count = sum(1 for r in resultados if r["status"] == "OK")
erro_count = sum(1 for r in resultados if r["status"] != "OK")

print(f"\nTotal: {len(resultados)}")
print(f"OK: {ok_count}")
print(f"ERRO: {erro_count}")
print(f"Taxa: {ok_count*100//len(resultados)}%")

if erro_count > 0:
    print(f"\nERROS:")
    for r in resultados:
        if r["status"] != "OK":
            print(f"  [{r['nome']}] {r.get('erro','?')}")

# Salvar
with open(REPORT_PATH, "w", encoding="utf-8") as f:
    json.dump({"fontes": resultados, "total": len(resultados), "ok": ok_count, "erro": erro_count}, 
              f, indent=2, ensure_ascii=False)
print(f"\nRelatorio salvo: {REPORT_PATH}")

# Stats do KG
if os.path.exists(KG_PATH):
    kg = json.load(open(KG_PATH, "r", encoding="utf-8"))
    lessons_weblearn = sum(1 for l in kg["licoes"] if l.get("ctx") == "weblearn")
    print(f"\nKG: {len(kg['licoes'])} lessons ({lessons_weblearn} weblearn)")
