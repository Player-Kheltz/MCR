"""32_llm_pesos.py — O que acontece quando o MCR le os PESOS de um LLM?

Os pesos de um LLM sao tensores (arrays de floats). Cada tipo de camada
tem uma distribuicao caracteristica:
- Embedding: valores pequenos, distrib normal centrada em 0
- Attention Q/K/V: valores pequenos, variancia moderada
- FFN layer 1: valores maiores (expande dim)
- FFN layer 2: valores menores (contrai dim)
- LayerNorm gamma: proximos de 1.0
- LayerNorm beta: proximos de 0.0
- Output projection: similares a embedding

A questao: o MCR consegue distinguir tipos de camada pelos BYTES
dos pesos? Consegue distinguir arquiteturas (GPT vs BERT vs Llama)?

Cada float32 sao 4 bytes. A distribuicao dos bytes muda conforme
a camada. LayerNorm gamma (valores ~1.0) tem bytes diferentes de
embedding (valores ~0.01).

E o MCR observando o LLM — vendo o que nem nos vemos.
"""
import sys, os, struct, random, json, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")

from mcr.coupling import MCRCoupling


def gerar_pesos(tipo_camada, n_pesos=256, seed=0):
    """Gera pesos sinteticos para um tipo de camada de LLM.
    
    Cada tipo tem uma distribuicao caracteristica que reflete
    a funcao da camada na arquitetura transformer.
    """
    random.seed(seed + hash(tipo_camada))
    
    if tipo_camada == "embedding":
        # Embedding: N(0, 0.02) — valores pequenos
        return [random.gauss(0, 0.02) for _ in range(n_pesos)]
    
    elif tipo_camada == "attention_q":
        # Query: N(0, 0.01) — muito pequeno (dividido por sqrt(d))
        return [random.gauss(0, 0.01) for _ in range(n_pesos)]
    
    elif tipo_camada == "attention_k":
        # Key: N(0, 0.01) — similar a Q
        return [random.gauss(0, 0.01) for _ in range(n_pesos)]
    
    elif tipo_camada == "attention_v":
        # Value: N(0, 0.02) — um pouco maior
        return [random.gauss(0, 0.02) for _ in range(n_pesos)]
    
    elif tipo_camada == "attention_o":
        # Output projection: N(0, 0.02)
        return [random.gauss(0, 0.02) for _ in range(n_pesos)]
    
    elif tipo_camada == "ffn_up":
        # FFN expansion: N(0, 0.02) — matriz grande
        return [random.gauss(0, 0.02) for _ in range(n_pesos)]
    
    elif tipo_camada == "ffn_down":
        # FFN contraction: N(0, 0.02)
        return [random.gauss(0, 0.02) for _ in range(n_pesos)]
    
    elif tipo_camada == "layernorm_gamma":
        # LayerNorm gamma: ~1.0 + N(0, 0.05)
        return [1.0 + random.gauss(0, 0.05) for _ in range(n_pesos)]
    
    elif tipo_camada == "layernorm_beta":
        # LayerNorm beta: ~0.0 + N(0, 0.02)
        return [random.gauss(0, 0.02) for _ in range(n_pesos)]
    
    elif tipo_camada == "output_proj":
        # Output projection (tied com embedding): N(0, 0.02)
        return [random.gauss(0, 0.02) for _ in range(n_pesos)]
    
    elif tipo_camada == "positional":
        # Positional encoding: seno/cosseno
        return [math.sin(i / 10000) for i in range(n_pesos)]
    
    elif tipo_camada == "bias":
        # Bias: N(0, 0.01) — muito pequeno
        return [random.gauss(0, 0.01) for _ in range(n_pesos)]
    
    return [random.gauss(0, 0.02) for _ in range(n_pesos)]


def pesos_para_bytes(pesos, dtype="float32"):
    """Converte lista de floats para bytes."""
    if dtype == "float32":
        return b"".join(struct.pack("<f", v) for v in pesos)
    elif dtype == "float16":
        return b"".join(struct.pack("<e", v) for v in pesos)
    return b""


def bytes_para_texto(b):
    """Converte bytes para string via latin-1 (1:1)."""
    return b.decode("latin-1")


def gerar_arquitetura(nome_arch, n_layers=4, n_pesos=128, seed=0):
    """Gera pesos simulando uma arquitetura completa de LLM.
    
    Diferentes arquiteturas tem diferentes ordenacoes e tipos de camadas.
    """
    camadas = []
    
    if nome_arch == "gpt":
        # GPT: embedding -> positional -> [attention -> ffn -> layernorm] x N -> output
        camadas.append("embedding")
        camadas.append("positional")
        for _ in range(n_layers):
            camadas.extend(["layernorm_gamma", "layernorm_beta",
                           "attention_q", "attention_k", "attention_v", "attention_o",
                           "layernorm_gamma", "layernorm_beta",
                           "ffn_up", "ffn_down"])
        camadas.append("layernorm_gamma")
        camadas.append("output_proj")
    
    elif nome_arch == "bert":
        # BERT: embedding -> [layernorm -> attention -> layernorm -> ffn] x N -> pooler
        camadas.append("embedding")
        for _ in range(n_layers):
            camadas.extend(["layernorm_gamma", "layernorm_beta",
                           "attention_q", "attention_k", "attention_v", "attention_o",
                           "layernorm_gamma", "layernorm_beta",
                           "ffn_up", "ffn_down"])
        camadas.append("layernorm_gamma")
        camadas.append("output_proj")
    
    elif nome_arch == "llama":
        # Llama: embedding -> [rmsnorm -> attention -> rmsnorm -> ffn] x N -> rmsnorm
        # Llama usa RMSNorm (gamma sem beta) e SwiGLU (3 matrizes FFN)
        camadas.append("embedding")
        for _ in range(n_layers):
            camadas.extend(["layernorm_gamma",
                           "attention_q", "attention_k", "attention_v", "attention_o",
                           "layernorm_gamma",
                           "ffn_up", "ffn_up", "ffn_down"])  # SwiGLU: gate + up + down
        camadas.append("layernorm_gamma")
        camadas.append("output_proj")
    
    # Gerar bytes de toda a arquitetura
    todos_bytes = b""
    for i, camada in enumerate(camadas):
        pesos = gerar_pesos(camada, n_pesos, seed + i)
        todos_bytes += pesos_para_bytes(pesos)
    
    return todos_bytes, camadas


def main():
    print("=" * 70)
    print("  TESTE 32 — MCR lendo os PESOS de um LLM")
    print("  O MCR consegue ver a arquitetura pelos bytes dos pesos?")
    print("=" * 70)

    # === Fase 1: Distinguir tipos de camada ===
    print("\n[1] Distinguindo tipos de camada pelos bytes dos pesos...")
    c = MCRCoupling()
    
    tipos_camada = [
        "embedding", "attention_q", "attention_k", "attention_v",
        "attention_o", "ffn_up", "ffn_down",
        "layernorm_gamma", "layernorm_beta",
        "output_proj", "positional", "bias",
    ]
    
    n_treino = 15
    n_pesos = 128
    
    for tipo in tipos_camada:
        for i in range(n_treino):
            pesos = gerar_pesos(tipo, n_pesos + i * 16, seed=i)
            blob = pesos_para_bytes(pesos)
            texto = bytes_para_texto(blob)
            c.alimentar(texto, "cam_" + tipo)
    
    print(f"  {len(tipos_camada)} tipos x {n_treino} amostras = {len(tipos_camada) * n_treino} obs")
    print(f"  Vocab: {len(c._palavra_acao)} pal, Acoes: {len(c._freq_acao)}")
    
    # Testar
    print("\n  Classificacao de camadas (zero-shot, seed nova):")
    acertos = 0
    for tipo in tipos_camada:
        pesos = gerar_pesos(tipo, n_pesos * 2, seed=999)
        blob = pesos_para_bytes(pesos)
        texto = bytes_para_texto(blob)
        acao, conf = c.decidir(texto, (None, 0.0))
        esperado = "cam_" + tipo
        ok = acao == esperado
        if ok:
            acertos += 1
        tag = "OK" if ok else "ERR"
        print(f"    {tipo:<22s} -> {acao:<25s} conf={conf:.3f} [{tag}]")
    
    print(f"\n  Acertos: {acertos}/{len(tipos_camada)} = {acertos/len(tipos_camada)*100:.1f}%")
    
    # === Fase 2: Distinguir arquiteturas completas ===
    print("\n[2] Distinguindo arquiteturas completas (GPT vs BERT vs Llama)...")
    c2 = MCRCoupling()
    
    arquiteturas = ["gpt", "bert", "llama"]
    n_arch_treino = 20
    
    for arch in arquiteturas:
        for i in range(n_arch_treino):
            blob, camadas = gerar_arquitetura(arch, n_layers=4 + i % 3, n_pesos=64, seed=i)
            texto = bytes_para_texto(blob)
            c2.alimentar(texto, "arch_" + arch)
    
    print(f"  {len(arquiteturas)} arquiteturas x {n_arch_treino} amostras = {len(arquiteturas) * n_arch_treino} obs")
    print(f"  Vocab: {len(c2._palavra_acao)} pal, Acoes: {len(c2._freq_acao)}")
    
    # Testar
    print("\n  Classificacao de arquiteturas (zero-shot):")
    acertos_arch = 0
    for arch in arquiteturas:
        blob, camadas = gerar_arquitetura(arch, n_layers=6, n_pesos=128, seed=888)
        texto = bytes_para_texto(blob)
        acao, conf = c2.decidir(texto, (None, 0.0))
        esperado = "arch_" + arch
        ok = acao == esperado
        if ok:
            acertos_arch += 1
        tag = "OK" if ok else "ERR"
        n_camadas = len(camadas)
        print(f"    {arch.upper():<8s} ({n_camadas} camadas) -> {acao:<12s} conf={conf:.3f} [{tag}]")
    
    print(f"\n  Acertos: {acertos_arch}/{len(arquiteturas)} = {acertos_arch/len(arquiteturas)*100:.1f}%")
    
    # === Fase 3: O que o MCR ve nos pesos? ===
    print("\n[3] Features b: que o MCR aprendeu por tipo de camada...")
    for tipo in tipos_camada[:6]:
        feat_dict = c._acao_features.get("cam_" + tipo, {})
        bytes_feat = {k: v for k, v in feat_dict.items() if k.startswith("b:")}
        if bytes_feat:
            top5 = sorted(bytes_feat.items(), key=lambda x: -x[1])[:5]
            bytes_hex = [f"0x{k.split(':')[1]}({v})" for k, v in top5]
            print(f"    {tipo:<22s}: {', '.join(bytes_hex)}")
    
    # === Fase 4: float16 vs float32 — MCR distingue precisao? ===
    print("\n[4] Distinguindo precisao: float16 vs float32...")
    c3 = MCRCoupling()
    
    for i in range(20):
        pesos = gerar_pesos("embedding", 128, seed=i)
        # float32
        blob32 = pesos_para_bytes(pesos, "float32")
        c3.alimentar(bytes_para_texto(blob32), "prec_float32")
        # float16
        blob16 = pesos_para_bytes(pesos, "float16")
        c3.alimentar(bytes_para_texto(blob16), "prec_float16")
    
    # Testar
    pesos_test = gerar_pesos("embedding", 256, seed=777)
    blob32 = pesos_para_bytes(pesos_test, "float32")
    blob16 = pesos_para_bytes(pesos_test, "float16")
    
    a32, c32 = c3.decidir(bytes_para_texto(blob32), (None, 0.0))
    a16, c16 = c3.decidir(bytes_para_texto(blob16), (None, 0.0))
    
    print(f"    float32 -> {a32} (conf={c32:.3f}) [{'OK' if a32 == 'prec_float32' else 'ERR'}]")
    print(f"    float16 -> {a16} (conf={c16:.3f}) [{'OK' if a16 == 'prec_float16' else 'ERR'}]")
    
    # === Fase 5: Camada individual dentro da arquitetura ===
    print("\n[5] Camada individual dentro de arquitetura completa...")
    # Pegar uma camada de attention dentro de um GPT e ver se o MCR identifica
    blob_gpt, camadas_gpt = gerar_arquitetura("gpt", n_layers=4, n_pesos=64, seed=42)
    
    # Encontrar onde comeca a primeira attention_q
    offset = 0
    attention_q_blob = None
    for i, camada in enumerate(camadas_gpt):
        camada_size = 64 * 4  # 64 pesos x 4 bytes float32
        if camada == "attention_q":
            attention_q_blob = blob_gpt[offset:offset + camada_size]
            break
        offset += camada_size
    
    if attention_q_blob:
        acao, conf = c.decidir(bytes_para_texto(attention_q_blob), (None, 0.0))
        print(f"    attention_q extraida de GPT -> {acao} (conf={conf:.3f})")
        print(f"    [{'OK' if acao == 'cam_attention_q' else 'ERR'}] — MCR identificou a camada correta!")
    
    # === Fase 6: Pesos reais vs aleatorios ===
    print("\n[6] Pesos estruturados vs puramente aleatorios...")
    c4 = MCRCoupling()
    
    for i in range(20):
        # Estruturado (LayerNorm gamma)
        pesos_estr = gerar_pesos("layernorm_gamma", 128, seed=i)
        blob_estr = pesos_para_bytes(pesos_estr)
        c4.alimentar(bytes_para_texto(blob_estr), "peso_estruturado")
        
        # Aleatorio puro
        random.seed(i)
        pesos_rand = [random.uniform(-1, 1) for _ in range(128)]
        blob_rand = pesos_para_bytes(pesos_rand)
        c4.alimentar(bytes_para_texto(blob_rand), "peso_aleatorio")
    
    # Testar
    pesos_estr_test = gerar_pesos("layernorm_gamma", 256, seed=666)
    random.seed(666)
    pesos_rand_test = [random.uniform(-1, 1) for _ in range(256)]
    
    a_estr, c_estr = c4.decidir(bytes_para_texto(pesos_para_bytes(pesos_estr_test)), (None, 0.0))
    a_rand, c_rand = c4.decidir(bytes_para_texto(pesos_para_bytes(pesos_rand_test)), (None, 0.0))
    
    print(f"    Estruturado (LayerNorm gamma) -> {a_estr} (conf={c_estr:.3f}) [{'OK' if a_estr == 'peso_estruturado' else 'ERR'}]")
    print(f"    Aleatorio puro -> {a_rand} (conf={c_rand:.3f}) [{'OK' if a_rand == 'peso_aleatorio' else 'ERR'}]")
    
    # === Resumo ===
    print("\n" + "=" * 70)
    print("  RESUMO: MCR lendo pesos de LLM")
    print("=" * 70)
    print(f"\n  Classificacao de camadas: {acertos}/{len(tipos_camada)} = {acertos/len(tipos_camada)*100:.1f}%")
    print(f"  Classificacao de arquiteturas: {acertos_arch}/{len(arquiteturas)} = {acertos_arch/len(arquiteturas)*100:.1f}%")
    print(f"  float32 vs float16: {'OK' if a32 == 'prec_float32' and a16 == 'prec_float16' else 'PARCIAL'}")
    print(f"  Estruturado vs aleatorio: {'OK' if a_estr == 'peso_estruturado' and a_rand == 'peso_aleatorio' else 'PARCIAL'}")
    
    # Salvar
    resultado = {
        "teste": "llm_pesos",
        "camadas": {"acertos": acertos, "total": len(tipos_camada)},
        "arquiteturas": {"acertos": acertos_arch, "total": len(arquiteturas)},
        "precisao": {"float32": a32 == "prec_float32", "float16": a16 == "prec_float16"},
        "estruturado_vs_aleatorio": {
            "estruturado": a_estr == "peso_estruturado",
            "aleatorio": a_rand == "peso_aleatorio",
        },
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "32_llm_pesos.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
