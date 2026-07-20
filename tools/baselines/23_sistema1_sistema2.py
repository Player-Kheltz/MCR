"""23_sistema1_sistema2.py — Sistema 1 (motor) + Sistema 2 (sonho) integrados.

Kahneman invertido no MCR:
- Sistema 1 (motor): rapido, preciso, decidir() em 50ms
- Sistema 2 (sonho): livre, criativo, sem objetivo

O motor consulta o sonho SO quando tem baixa confianca.
O sonho NAO escreve no motor. O motor CONSULTA o sonho.
Como o humano que sonha uma solucao mas verifica com logica ao acordar.

Teste:
1. Motor A (controle): decidir() puro
2. Motor B (S1+S2): decidir() + inspirar() quando conf < 0.5
3. Comparar: B > A sem contaminar?
"""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))

from mcr.coupling import MCRCoupling
from mcr.sonho_markoviano import SonhoMarkoviano
from setup import carregar_mcr, mcr_decidir

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from corpus_matematico import alimentar_corpus_matematico, validar_corpus_matematico


def main():
    print("=" * 70)
    print("  TESTE 23 — Sistema 1 (motor) + Sistema 2 (sonho) integrados")
    print("=" * 70)

    # Carregar motor
    print("\n[1] Carregando motor...")
    c, info = carregar_mcr(leve=True)
    print(f"  {c._total} obs, {len(c._palavra_acao)} pal, {len(c._freq_acao)} acoes")

    # Criar sonhador (Sistema 2) — NAO alimenta o motor
    sonhador = SonhoMarkoviano(c)

    # Alimentar historico de confiancas do sonhador (10 decisoes iniciais)
    # para que o threshold emergente (mediana) tenha dados
    print("\n[1b] Calibrando threshold emergente (10 decisoes iniciais)...")
    for texto_calib in ["criar npc ferreiro", "gerar monstro dragao", "o que e markov",
                         "buscar arquivo config", "validar codigo python",
                         "gerar sprite espada", "analisar estrutura", "conectar modulo",
                         "aprender conceito", "planejar tarefa"]:
        acao, conf = mcr_decidir(c, texto_calib)
        sonhador._confiancas_historico.append(conf)
    confs_ord = sorted(sonhador._confiancas_historico)
    threshold_emergente = confs_ord[len(confs_ord) // 2]
    print(f"  Threshold emergente (mediana): {threshold_emergente:.4f}")
    print(f"  Confiancas: {[round(x,3) for x in sorted(sonhador._confiancas_historico)]}")

    # === Testes ===
    testes = [
        # Regras matematicas
        ("sequencia dois quatro seis oito", "PA"),
        ("padrao tres cinco oito treze", "FIB"),
        ("encadear cinco dezesseis oito quatro", "COLL"),
        ("numeros quatro oito dezesseis", "PG"),
        ("ordem dois tres cinco sete", "PRIMO"),
        ("serie cinco seis dez quize", "TRI"),
        ("numeros nove dezesseis vinteecinco", "QUAD"),
        # Zero-shot
        ("criar alquimista pocoes", "gerar_npc"),
        ("fazer golem pedra", "gerar_monstro"),
        ("qual diferenca markov", "responder"),
        ("criar textura agua", "gerar_sprite"),
        ("criar missao resgate", "gerar_quest"),
        ("encontrar arquivos config", "buscar"),
        ("examinar codigo python", "analisar"),
        ("confirmar sintaxe lua", "validar"),
        ("ligar modulo npc", "conectar"),
        ("absorver nova informacao", "aprender"),
        # Fragmentos
        ("dezesseis oito quatro dois", "COLL"),
        ("oito quatro dois um", "COLL"),
        ("um um dois tres", "FIB"),
    ]

    print(f"\n[2] Testando {len(testes)} casos...")
    print(f"  {'Teste':<40s} {'Esp':<12s} {'S1':<15s} {'S1+S2':<15s} {'Fonte':<15s}")
    print("  " + "-" * 100)

    ac_s1 = 0
    ac_s1s2 = 0
    n_inspirado = 0
    threshold = None  # emergente (mediana do historico)

    for texto, esp in testes:
        # Sistema 1: decidir() puro
        acao_s1, conf_s1 = mcr_decidir(c, texto)

        # Sistema 1 + Sistema 2: sempre consulta o sonhador
        # O sonhador decide se precisa inspirar (threshold emergente)
        acao_s1s2 = acao_s1
        conf_s1s2 = conf_s1
        fonte = "motor"

        inspiracao = sonhador.inspirar(texto, conf_s1, threshold=None)
        if inspiracao is not None and inspiracao.get("acao") is not None:
            acao_s1s2 = inspiracao["acao"]
            conf_s1s2 = inspiracao["confianca"]
            fonte = "sonho"
            n_inspirado += 1

        st_s1 = "OK" if acao_s1 == esp else "ERR"
        st_s1s2 = "OK" if acao_s1s2 == esp else "ERR"
        if acao_s1 == esp:
            ac_s1 += 1
        if acao_s1s2 == esp:
            ac_s1s2 += 1

        print(f"  {texto[:38]:<40s} {esp:<12s} {st_s1} {acao_s1[:10]:<10s} "
              f"{st_s1s2} {acao_s1s2[:10]:<10s} {fonte:<15s}")

    # === Resultados ===
    n = len(testes)
    print(f"\n[3] Resultados:")
    print(f"  Sistema 1 (motor puro):      {ac_s1}/{n} = {ac_s1/n*100:.1f}%")
    print(f"  Sistema 1 + Sistema 2:       {ac_s1s2}/{n} = {ac_s1s2/n*100:.1f}%")
    print(f"  Inspiracoes consultadas:     {n_inspirado}/{n}")
    print(f"  Delta:                       {ac_s1s2 - ac_s1:+d}")

    # Veredito
    if ac_s1s2 > ac_s1:
        veredito = "S2 MELHORA S1 sem contaminar"
    elif ac_s1s2 < ac_s1:
        veredito = "S2 PIORA S1 (contaminacao)"
    else:
        veredito = "S2 NEUTRO"

    print(f"\n  Veredito: {veredito}")

    # === Verificar que o motor NAO foi contaminado ===
    print(f"\n[4] Motor contaminado?")
    print(f"  Obs apos teste: {c._total} (controle: {info['total_obs']})")
    print(f"  Vocab apos teste: {len(c._palavra_acao)} (controle: {info['vocab']})")
    print(f"  freq_sonhar: {c._freq_acao.get('sonhar', 0)}")
    contaminado = c._total > info['total_obs']
    print(f"  Contaminado? {'SIM' if contaminado else 'NAO — motor intacto'}")

    # === Salvar ===
    resultado = {
        "teste": "sistema1_sistema2",
        "n_testes": n,
        "sistema1": {"acertos": ac_s1, "taxa": ac_s1 / n},
        "sistema1_sistema2": {"acertos": ac_s1s2, "taxa": ac_s1s2 / n},
        "n_inspiracoes": n_inspirado,
        "delta": ac_s1s2 - ac_s1,
        "veredito": veredito,
        "motor_contaminado": contaminado,
        "threshold": threshold,
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "23_sistema1_sistema2.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
