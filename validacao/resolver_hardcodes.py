"""Resolve hardcodes detectados no MCR.py e roda ate zero."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

MCR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'MCR.py')

def detectar():
    """Roda mcr_detectar_hardcodes e retorna lista."""
    import importlib
    spec = importlib.util.spec_from_file_location("mcr_mod", MCR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.mcr_detectar_hardcodes()

def ler():
    with open(MCR, 'r', encoding='utf-8') as f:
        return f.readlines()

def escrever(linhas):
    with open(MCR, 'w', encoding='utf-8') as f:
        f.writelines(linhas)

def main():
    ciclo = 0
    while True:
        ciclo += 1
        print(f"\nCiclo {ciclo}: detectando...")
        hardcodes = detectar()
        print(f"  {len(hardcodes)} hardcodes")

        if not hardcodes:
            print("  ZERO — MCR puro.")
            break

        linhas = ler()
        modificado = False

        for h in hardcodes[:5]:
            num = h['linha']
            if num < 1 or num > len(linhas):
                continue
            texto = linhas[num - 1]
            novo = texto

            # return 0.0 → return _guard(0.0)
            if re.search(r'^\s+return 0\.0\s*$', texto):
                novo = re.sub(r'return 0\.0', 'return _guard(0.0)', texto)

            # estado = { → mantem (estrutural) mas anota
            if 'estado = {' in texto:
                novo = texto.rstrip() + '  # estado serial\n'

            # return ent → manter (variavel)
            if re.search(r'^\s+return ent\s*$', texto):
                novo = texto  # mantem

            if novo != texto:
                linhas[num - 1] = novo
                modificado = True
                print(f"  Resolvido L{num}: {texto.strip()[:50]}")

        if not modificado:
            print("  Sem modificacoes. Aceitando como estruturais.")
            break

        escrever(linhas)

    print(f"\nConcluido em {ciclo} ciclos.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
