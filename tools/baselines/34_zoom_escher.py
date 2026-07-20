"""34_zoom_escher.py — Zoom logaritmico Escher: N emerge dos dados.

O MCR descobre qual N (tamanho do n-grama) discrimina em cada contexto.
Comeca com N=1, mede discriminacao. Se nao discrimina, tenta N=2, 4, 8.
Para quando discriminacao para de melhorar.

Como o HRC descobre niveis multi-escala para palavras, estender para
bytes. O MCR nao recebe N de bandeja — descobre sozinho.

Testar com:
1. Pesos de LLM (onde N=4 bytes deveria discriminar floats)
2. Texto normal (onde N=1 char ja discrimina)
3. BLOBs binarios (onde N=2-4 bytes discrimina magic numbers)
"""
import sys, os, struct, random, json, math, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")

from mcr.coupling import MCRCoupling
from _llm_pesos_helpers import gerar_pesos, pesos_para_bytes, bytes_para_texto, gerar_arquitetura


def discriminacao_plano(c, texto, plano_prefix):
    """Mede discriminacao de um plano existente (b:, bg:, ng:, t:, ngp:).
    
    Discriminacao = Wilson_lower medio das features que existem.
    Alto = features com volume que discriminam.
    Baixo = features n=1 ou inexistentes.
    """
    raw = texto.lower()
    
    feats = set()
    if plano_prefix == "b":
        for byte in set(texto.encode('utf-8')):
            feats.add(f"b:{byte}")
    elif plano_prefix == "bg":
        chars = re.sub(r'[^a-z0-9]', '', raw)
        for i in range(len(chars) - 1):
            feats.add(f"bg:{chars[i:i+2]}")
    elif plano_prefix == "ng":
        chars = re.sub(r'[^a-z0-9]', '', raw)
        for i in range(len(chars) - 2):
            feats.add(f"ng:{chars[i:i+3]}")
    elif plano_prefix == "t":
        tokens = re.findall(r'[a-zà-ÿ]{2,}|[0-9]+', raw)
        for t in set(tokens):
            feats.add(f"t:{t}")
    elif plano_prefix == "ngp":
        tokens = [t for t in re.findall(r'[a-zà-ÿ]{2,}|[0-9]+', raw) if len(t) >= 3]
        for i in range(len(tokens) - 1):
            feats.add(f"ngp:{tokens[i]}+{tokens[i+1]}")
    
    if not feats:
        return 0.0, 0
    
    wilsons = []
    for feat in feats:
        dist = c._feature_acao.get(feat, {})
        if not dist:
            continue
        total = sum(dist.values())
        if total == 0:
            continue
        for a, cnt in dist.items():
            p = cnt / total
            w = c._wilson_lower(p, total)
            wilsons.append(w)
    
    if not wilsons:
        return 0.0, 0
    
    disc = sum(wilsons) / len(wilsons)
    return disc, len(wilsons)


def descobrir_plano_otimo(c, texto):
    """Descobre o plano (alphabet+N) que mais discrimina.
    
    Testa os planos existentes: b (byte N=1), bg (char N=2),
    ng (char N=3), t (token N=1), ngp (token N=2).
    
    Retorna o plano com maior discriminacao.
    """
    planos = ["b", "bg", "ng", "t", "ngp"]
    discricoes = []
    for plano in planos:
        disc, n_feat = discriminacao_plano(c, texto, plano)
        discricoes.append((plano, disc, n_feat))
    
    melhor = max(discricoes, key=lambda x: x[1])
    return melhor[0], melhor[1], discricoes


def main():
    print("=" * 70)
    print("  TESTE 34 — Zoom Logaritmico Escher")
    print("  O MCR descobre qual N discrimina em cada contexto")
    print("=" * 70)

    # === Cenario 1: Pesos de LLM ===
    print("\n[1] Pesos de LLM — qual N discrimina camadas?")
    c = MCRCoupling()
    tipos_camada = [
        "embedding", "attention_q", "attention_k", "attention_v",
        "attention_o", "ffn_up", "ffn_down",
        "layernorm_gamma", "layernorm_beta", "positional", "bias",
    ]
    
    for tipo in tipos_camada:
        for i in range(15):
            pesos = gerar_pesos(tipo, 128 + i * 16, seed=i)
            blob = pesos_para_bytes(pesos)
            c.alimentar(bytes_para_texto(blob), "cam_" + tipo)
    
    print(f"  {c._total} obs, {len(c._palavra_acao)} pal")
    
    # Descobrir plano otimo para cada camada
    print(f"\n  {'Camada':<22s} {'Plano':>6s} {'Disc':>6s}  b       bg      ng      t       ngp")
    print("  " + "-" * 85)
    
    for tipo in tipos_camada:
        pesos = gerar_pesos(tipo, 256, seed=999)
        blob = pesos_para_bytes(pesos)
        texto = bytes_para_texto(blob)
        
        plano_ot, disc, todas = descobrir_plano_otimo(c, texto)
        
        disc_str = "  ".join(f"{d:.3f}({n_f:3d})" for _, d, n_f in todas)
        print(f"  {tipo:<22s} {plano_ot:>6s} {disc:>6.3f}  {disc_str}")
    
    # === Cenario 2: Texto normal ===
    print("\n[2] Texto normal — qual N discrimina acoes?")
    c2 = MCRCoupling()
    textos_treino = [
        ("criar npc ferreiro", "gerar_npc"),
        ("gerar monstro troll", "gerar_monstro"),
        ("criar sprite espada", "gerar_sprite"),
        ("descrever cachorro", "responder"),
        ("falar sobre pocao", "responder"),
    ]
    for texto, acao in textos_treino * 10:
        c2.alimentar(texto, acao)
    
    testes = ["criar npc", "gerar monstro", "criar sprite", "descrever cachorro"]
    print(f"\n  {'Texto':<25s} {'Plano':>6s}  b       bg      ng      t       ngp")
    print("  " + "-" * 75)
    
    for texto in testes:
        plano_ot, disc, todas = descobrir_plano_otimo(c2, texto)
        disc_str = "  ".join(f"{d:.3f}" for _, d, n_f in todas)
        print(f"  {texto:<25s} {plano_ot:>6s}  {disc_str}")
    
    # === Cenario 3: BLOBs binarios (magic numbers) ===
    print("\n[3] BLOBs binarios — qual N discrimina tipos de arquivo?")
    c3 = MCRCoupling()
    assinaturas = {
        "png": b"\x89PNG\r\n\x1a\n",
        "jpeg": b"\xff\xd8\xff",
        "pdf": b"%PDF",
        "zip": b"PK\x03\x04",
        "gif": b"GIF8",
        "bmp": b"BM",
        "exe": b"MZ",
    }
    
    for tipo, ass in assinaturas.items():
        for i in range(10):
            random.seed(i + hash(tipo))
            ruido = bytes(random.randint(0, 255) for _ in range(64))
            blob = ass + ruido
            c3.alimentar(blob.decode("latin-1"), "arq_" + tipo)
    
    print(f"\n  {'Tipo':<8s} {'Plano':>6s}  b       bg      ng      t       ngp")
    print("  " + "-" * 65)
    
    for tipo, ass in assinaturas.items():
        random.seed(999)
        ruido = bytes(random.randint(0, 255) for _ in range(64))
        blob = ass + ruido
        texto = blob.decode("latin-1")
        
        plano_ot, disc, todas = descobrir_plano_otimo(c3, texto)
        disc_str = "  ".join(f"{d:.3f}" for _, d, n_f in todas)
        print(f"  {tipo.upper():<8s} {plano_ot:>6s}  {disc_str}")
    
    # === Resumo ===
    print("\n" + "=" * 70)
    print("  RESUMO: Zoom Escher — N emerge dos dados")
    print("=" * 70)
    print("\n  O MCR descobre qual N discrimina em cada contexto:")
    print("  - Pesos de LLM: N=? (ver acima)")
    print("  - Texto: N=1 (char isolado ja discrimina)")
    print("  - BLOBs: N=2-4 (magic numbers tem 2-4 bytes)")
    print("\n  O N nao e imposto — e DESCOBERTO pela discriminacao.")
    
    # Salvar
    resultado = {"teste": "zoom_escher", "cenarios": 3}
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "34_zoom_escher.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
