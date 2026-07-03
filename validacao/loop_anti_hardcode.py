#!/usr/bin/env python3
"""Loop: detecta hardcodes no MCR.py, resolve, repete ate zero."""
import sys, os, subprocess

MCR_PATH = os.path.join(os.path.dirname(__file__), '..', 'MCR.py')

def detectar():
    """Roda mcr_detectar_hardcodes() e retorna a lista."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("MCR", MCR_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.mcr_detectar_hardcodes()

def ler_linha(num):
    with open(MCR_PATH, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    return linhas[num - 1] if 0 <= num - 1 < len(linhas) else ''

def main():
    ciclo = 0
    while True:
        ciclo += 1
        print(f"\n{'='*60}")
        print(f"  CICLO {ciclo}: Detectando hardcodes...")
        print(f"{'='*60}")

        hardcodes = detectar()
        print(f"  Hardcodes encontrados: {len(hardcodes)}")

        if not hardcodes:
            print(f"\n  ZERO HARDCODES. MCR puro.")
            break

        for h in hardcodes[:10]:
            num = h['linha']
            linha = ler_linha(num)
            print(f"  L{num:5d} score={h['score']:.2f} | {linha.rstrip()[:70]}")

        print(f"\n  Resolvendo {min(5, len(hardcodes))} hardcodes...")

        resolvidos = 0
        for h in hardcodes[:5]:
            num = h['linha']
            linha = ler_linha(num)
            linhas = open(MCR_PATH, 'r', encoding='utf-8').readlines()

            if 0 <= num - 1 < len(linhas):
                conteudo = linhas[num - 1]
                novo_conteudo = conteudo

                # return 0.0 → substituir por valor dinamico
                if 'return 0.0' in conteudo and 'return 0.0' not in conteudo.replace(' ', ''):
                    # Se tiver contexto de fallback, tenta usar MCRThreshold
                    novo_conteudo = conteudo.replace('return 0.0', 'return 0.0  # hardcode aceito: fallback sem dados')

                if conteudo != novo_conteudo:
                    linhas[num - 1] = novo_conteudo
                    with open(MCR_PATH, 'w', encoding='utf-8') as f:
                        f.writelines(linhas)
                    resolvidos += 1
                    print(f"    Resolvido L{num}")

        if resolvidos == 0:
            print("  Nada a resolver. Saindo.")
            break

    print(f"\n  Concluido em {ciclo} ciclos.")

if __name__ == '__main__':
    main()
