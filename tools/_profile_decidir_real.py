"""Profile DECIDIR com cProfile — achar a fonte O(n²) empiricamente.

Roda decidir() numa pergunta tipica com o motor carregado (160K obs).
Timeout: 30s. Se passar, printa os 30 callers mais lentos.
"""
import cProfile
import pstats
import sys
import time

sys.path.insert(0, r"E:\MCR")
sys.stdout.reconfigure(encoding='utf-8')

from mcr.coupling import MCRCoupling

MOTOR_PATH = r"E:\MCR\cache\coupling_MCRCoupling_backup_preB2c.json"


def main():
    print("[1] Carregando motor (160K obs)...")
    t0 = time.time()
    m = MCRCoupling()
    m.load(MOTOR_PATH)
    print(f"    load em {time.time()-t0:.1f}s | obs={m._total} | pal={len(m._transicao_palavra)}")

    perguntas = [
        "voce sabe quem voce e?",
        "o que e o mcr?",
        "voce tem consciencia?",
        "criar monstro dragao",
    ]

    for pergunta in perguntas:
        print(f"\n[2] Profile: '{pergunta}' (timeout 30s)")
        pr = cProfile.Profile()
        t0 = time.time()
        try:
            pr.enable()
            acao, conf = m.decidir(pergunta, (None, 0.0))
            pr.disable()
            print(f"    decidir retornou em {time.time()-t0:.2f}s: acao={acao} conf={conf:.3f}")
        except Exception as e:
            pr.disable()
            print(f"    ERRO em {time.time()-t0:.2f}s: {e}")
            break

        st = pstats.Stats(pr)
        st.sort_stats('cumulative')
        print("    Top 25 por cumulativo:")
        st.print_stats(25)

        print("    Top 25 por tempo interno (tottime):")
        st.sort_stats('tottime')
        st.print_stats(25)


if __name__ == "__main__":
    main()
