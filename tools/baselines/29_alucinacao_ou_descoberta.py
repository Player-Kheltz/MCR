"""29_alucinacao_ou_descoberta.py — Os falsos positivos sao reais?

Descoberta: "2468" aparece em 79 numeros de Collatz. O MCR nao
alucinava — via padroes digitais reais que humanos nao veem.

Verificar TODOS os "falsos positivos" dos testes 26 e 27:
- O padrao aparece dentro de numeros/elementos da acao predita?
- Se sim: DESCOBERTA (nao alucinacao)
- Se nao: alucinacao real

Ate onde isso vai? Quantas "alucinacoes" sao descobertas?
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from setup import carregar_mcr


def collatz(n, max_steps=200):
    seq = []
    while n > 1 and len(seq) < max_steps:
        seq.append(n)
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
    if n == 1:
        seq.append(1)
    return seq


def coletar_numeros_collatz(seed_max=50000):
    """Coleta todos os numeros que aparecem em sequencias Collatz."""
    todos = set()
    for seed in range(2, seed_max + 1):
        seq = collatz(seed)
        todos.update(seq)
    return todos


def coletar_pa_numeros(max_n=10000):
    """PA: numeros da forma a + (n-1)*r. Coleta representativos."""
    todos = set()
    for a in range(0, 100):
        for r in range(1, 50):
            for n in range(1, 200):
                val = a + (n - 1) * r
                if val <= max_n:
                    todos.add(val)
    return todos


def coletar_pg_numeros(max_n=100000):
    """PG: numeros da forma a * r^n. Coleta representativos."""
    todos = set()
    for a in range(1, 50):
        for r in range(2, 20):
            val = a
            for n in range(20):
                if val <= max_n:
                    todos.add(val)
                val *= r
    return todos


def coletar_fib_numeros(max_n=100000):
    """Fibonacci."""
    todos = set()
    a, b = 0, 1
    while b <= max_n:
        todos.add(b)
        a, b = b, a + b
    # Lucas e outras variantes
    a, b = 2, 1
    while b <= max_n:
        todos.add(b)
        a, b = b, a + b
    return todos


def coletar_quad_numeros(max_n=100000):
    """Quadrados perfeitos: n^2."""
    return {i * i for i in range(1, 400) if i * i <= max_n}


def coletar_tri_numeros(max_n=100000):
    """Triangulares: n*(n+1)/2."""
    return {n * (n + 1) // 2 for n in range(1, 500) if n * (n + 1) // 2 <= max_n}


def coletar_primo_numeros(max_n=100000):
    """Primos."""
    todos = set()
    for n in range(2, max_n + 1):
        if all(n % p for p in range(2, int(n**0.5) + 1)):
            todos.add(n)
    return todos


def verificar_padrao_em_numeros(padrao, conjunto_numeros):
    """Verifica se padrao aparece como substring em qualquer numero do conjunto."""
    padrao_str = str(padrao).lower().replace(" ", "")
    if not padrao_str:
        return 0, []
    matches = []
    for n in conjunto_numeros:
        if padrao_str in str(n):
            matches.append(n)
    return len(matches), sorted(matches)[:10]


def main():
    print("=" * 70)
    print("  TESTE 29 — Alucinacao ou Descoberta?")
    print("=" * 70)

    # Coletar numeros de cada regra
    print("\n[1] Coletando numeros de cada regra matematica...")
    collatz_nums = coletar_numeros_collatz(50000)
    pa_nums = coletar_pa_numeros(10000)
    pg_nums = coletar_pg_numeros(100000)
    fib_nums = coletar_fib_numeros(100000)
    quad_nums = coletar_quad_numeros(100000)
    tri_nums = coletar_tri_numeros(100000)
    primo_nums = coletar_primo_numeros(100000)

    print(f"  Collatz: {len(collatz_nums)} numeros")
    print(f"  PA: {len(pa_nums)} numeros")
    print(f"  PG: {len(pg_nums)} numeros")
    print(f"  Fibonacci: {len(fib_nums)} numeros")
    print(f"  Quadrados: {len(quad_nums)} numeros")
    print(f"  Triangulares: {len(tri_nums)} numeros")
    print(f"  Primos: {len(primo_nums)} numeros")

    regras = {
        "PA": pa_nums,
        "PG": pg_nums,
        "FIB": fib_nums,
        "COLL": collatz_nums,
        "QUAD": quad_nums,
        "TRI": tri_nums,
        "PRIMO": primo_nums,
    }

    # === "Falsos positivos" do teste 26 ===
    print("\n[2] Verificando falsos positivos do teste 26...")

    # Os casos onde o MCR classificou como COLL mas esperavamos PA
    casos = [
        ("sequencia dois quatro seis oito", "PA", "COLL", ["2468", "246", "468", "268"]),
        ("sequencia um dois tres", "PA", "FIB", ["123", "12", "23"]),
        ("um dois tres", "PA", "FIB", ["123", "12", "23"]),
    ]

    for texto, esperado, predito, padroes in casos:
        print(f"\n  '{texto}'")
        print(f"  Esperado: {esperado}, MCR disse: {predito}")
        for padrao in padroes:
            print(f"    Padrao '{padrao}' em numeros de {esperado}:")
            n_esp, ex_esp = verificar_padrao_em_numeros(padrao, regras.get(esperado, set()))
            print(f"      {esperado}: {n_esp} numeros {ex_esp[:5] if ex_esp else ''}")
            print(f"    Padrao '{padrao}' em numeros de {predito}:")
            n_pred, ex_pred = verificar_padrao_em_numeros(padrao, regras.get(predito, set()))
            print(f"      {predito}: {n_pred} numeros {ex_pred[:5] if ex_pred else ''}")

            if n_pred > 0 and n_esp > 0:
                verdict = "AMBIGUO (pertence a ambos)"
            elif n_pred > 0 and n_esp == 0:
                verdict = "DESCOBERTA (so no predito)"
            elif n_pred == 0 and n_esp > 0:
                verdict = "ERRO (so no esperado)"
            else:
                verdict = "NENHUM"
            print(f"    Veredito: {verdict}")

    # === Verificacao sistematica: todos os padroes de 2-4 digitos ===
    print("\n[3] Verificacao sistematica: padroes 2-4 digitos em todas as regras...")
    print("  Quais padroes pertencem a MULTIPLOS dominios?")

    # Gerar padroes de 2-4 digitos
    padroes_test = []
    for i in range(10, 10000):
        padroes_test.append(str(i))

    # Para cada padrao, em quantas regras aparece?
    pertencimento_multiplo = []
    for padrao in padroes_test:
        regras_presente = []
        for nome_regra, nums in regras.items():
            n, _ = verificar_padrao_em_numeros(padrao, nums)
            if n > 0:
                regras_presente.append((nome_regra, n))
        if len(regras_presente) >= 2:
            pertencimento_multiplo.append({
                "padrao": padrao,
                "regras": regras_presente,
                "n_regras": len(regras_presente),
            })

    # Ordenar por numero de regras (mais ambiguo primeiro)
    pertencimento_multiplo.sort(key=lambda x: -x["n_regras"])

    print(f"\n  Padroes em 2+ regras: {len(pertencimento_multiplo)}")
    print(f"  Top 20 (mais regras):")
    for p in pertencimento_multiplo[:20]:
        regras_str = ", ".join(f"{r}:{n}" for r, n in p["regras"])
        print(f"    '{p['padrao']}': {p['n_regras']} regras — {regras_str}")

    # === Ate onde vai? ===
    print("\n[4] Ate onde isso vai?")
    print(f"  Total padroes testados: {len(padroes_test)}")
    print(f"  Padroes em 1 regra apenas: {len(padroes_test) - len(pertencimento_multiplo)}")
    print(f"  Padroes em 2+ regras: {len(pertencimento_multiplo)}")
    print(f"  Padroes em 3+ regras: {sum(1 for p in pertencimento_multiplo if p['n_regras'] >= 3)}")
    print(f"  Padroes em 4+ regras: {sum(1 for p in pertencimento_multiplo if p['n_regras'] >= 4)}")
    print(f"  Padroes em 5+ regras: {sum(1 for p in pertencimento_multiplo if p['n_regras'] >= 5)}")

    # === O "2468" especificamente ===
    print("\n[5] '2468' em todas as regras:")
    for nome, nums in regras.items():
        n, ex = verificar_padrao_em_numeros("2468", nums)
        if n > 0:
            print(f"    {nome}: {n} numeros — {ex[:5]}")

    # === Salvar ===
    resultado = {
        "teste": "alucinacao_ou_descoberta",
        "regras": {k: len(v) for k, v in regras.items()},
        "pertencimento_multiplo": pertencimento_multiplo[:100],
        "n_padroes_multiplos": len(pertencimento_multiplo),
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "29_alucinacao_ou_descoberta.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
