"""31_blob.py — O que acontece quando o MCR le um BLOB?

Cada tipo de arquivo tem uma assinatura de bytes (magic numbers):
- PNG: 89 50 4E 47 0D 0A 1A 0A
- JPEG: FF D8 FF
- PDF: 25 50 44 46
- ZIP: 50 4B 03 04
- GIF: 47 49 46 38
- BMP: 42 4D

O MCR ja tem o plano b: (byte). A questao: consegue aprender
essas assinaturas e classificar arquivos pelo conteudo binario?

Como wraith: 'wr' e a assinatura de gerar_monstro.
Os bytes 89 50 4E 47 podem ser a assinatura de PNG.
"""
import sys, os, struct, random, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8")

from mcr.coupling import MCRCoupling


# === Assinaturas de magic numbers ===
ASSINATURAS = {
    "png":  b"\x89PNG\r\n\x1a\n",
    "jpeg": b"\xff\xd8\xff",
    "pdf":  b"%PDF",
    "zip":  b"PK\x03\x04",
    "gif":  b"GIF8",
    "bmp":  b"BM",
    "exe":  b"MZ",
    "rar":  b"Rar!\x1a\x07",
    "gzip": b"\x1f\x8b",
    "tar":  b"ustar",
}

# Descritores de cada tipo (para gerar blobs sinteticos)
DESCRICOES = {
    "png": "imagem png com transparencia",
    "jpeg": "foto jpeg comprimida",
    "pdf": "documento pdf texto",
    "zip": "arquivo zip comprimido",
    "gif": "animacao gif",
    "bmp": "bitmap windows",
    "exe": "executavel windows",
    "rar": "arquivo rar",
    "gzip": "gzip comprimido",
    "tar": "tar archive",
}


def gerar_blob(tipo, tamanho=256, variacao=0):
    """Gera um blob sintetico com a assinatura do tipo + ruido."""
    random.seed(variacao + hash(tipo))
    assinatura = ASSINATURAS[tipo]
    # Assinatura + ruido aleatorio (simula conteudo do arquivo)
    ruido = bytes(random.randint(0, 255) for _ in range(tamanho - len(assinatura)))
    return assinatura + ruido


def blob_para_texto(blob):
    """Converte bytes para string que o MCR pode ingerir.
    
    Usa latin-1 (mapeamento 1:1 byte→char) para preservar todos os bytes.
    O MCR vai extrair features b: (byte) que correspondem aos bytes originais.
    """
    return blob.decode("latin-1")


def main():
    print("=" * 70)
    print("  TESTE 31 — MCR lendo BLOBs binarios")
    print("  O MCR consegue classificar arquivos por magic numbers?")
    print("=" * 70)

    # === Fase 1: Verificar se _extrair_features_nd processa bytes ===
    print("\n[1] Verificando se o MCR processa bytes corretamente...")
    c_test = MCRCoupling()
    blob_png = gerar_blob("png")
    texto_png = blob_para_texto(blob_png)
    c_test.alimentar(texto_png, "png")
    
    # Verificar features extraidas
    feat_png = c_test._acao_features.get("png", {})
    bytes_features = {k: v for k, v in feat_png.items() if k.startswith("b:")}
    print(f"  Blob PNG: {len(blob_png)} bytes")
    print(f"  Features b: extraidas: {len(bytes_features)}")
    # Os primeiros bytes da assinatura PNG
    for i, b in enumerate(blob_png[:8]):
        feat_key = f"b:{b}"
        if feat_key in bytes_features:
            print(f"    byte {i}: 0x{b:02X} -> {feat_key} (encontrado!)")
        else:
            print(f"    byte {i}: 0x{b:02X} -> {feat_key} (NAO encontrado)")
    
    # === Fase 2: Treinar MCR com blobs de cada tipo ===
    print("\n[2] Treinando MCR com blobs de cada tipo...")
    c = MCRCoupling()
    
    tipos = list(ASSINATURAS.keys())
    n_treinamento = 10  # 10 blobs por tipo
    
    for tipo in tipos:
        for i in range(n_treinamento):
            blob = gerar_blob(tipo, tamanho=128 + i * 32, variacao=i)
            texto = blob_para_texto(blob)
            c.alimentar(texto, "arq_" + tipo)
    
    print(f"  {len(tipos)} tipos x {n_treinamento} blobs = {len(tipos) * n_treinamento} observacoes")
    print(f"  Vocabulario: {len(c._palavra_acao)} palavras")
    print(f"  Acoes: {len(c._freq_acao)}")
    
    # === Fase 3: Classificar blobs de teste ===
    print("\n[3] Classificando blobs de teste (vistos no treino)...")
    acertos = 0
    total = 0
    for tipo in tipos:
        blob = gerar_blob(tipo, tamanho=256, variacao=999)  # variacao nova
        texto = blob_para_texto(blob)
        acao, conf = c.decidir(texto, (None, 0.0))
        esperado = "arq_" + tipo
        ok = acao == esperado
        if ok:
            acertos += 1
        total += 1
        tag = "OK" if ok else "ERR"
        print(f"  {tipo.upper():<6s} -> {acao:<12s} conf={conf:.3f} [{tag}]")
    
    print(f"\n  Acertos: {acertos}/{total} = {acertos/total*100:.1f}%")
    
    # === Fase 4: Zero-shot — apenas assinatura (sem ruido) ===
    print("\n[4] Zero-shot: apenas assinatura (magic number sem ruido)...")
    acertos_zs = 0
    total_zs = 0
    for tipo in tipos:
        # So a assinatura, sem ruido
        blob = ASSINATURAS[tipo]
        texto = blob_para_texto(blob)
        acao, conf = c.decidir(texto, (None, 0.0))
        esperado = "arq_" + tipo
        ok = acao == esperado
        if ok:
            acertos_zs += 1
        total_zs += 1
        tag = "OK" if ok else "ERR"
        print(f"  {tipo.upper():<6s} (so assinatura) -> {acao:<12s} conf={conf:.3f} [{tag}]")
    
    print(f"\n  Zero-shot acertos: {acertos_zs}/{total_zs} = {acertos_zs/total_zs*100:.1f}%")
    
    # === Fase 5: Assinatura parcial (primeiros 2-3 bytes) ===
    print("\n[5] Assinatura parcial (2-3 primeiros bytes)...")
    acertos_parc = 0
    total_parc = 0
    for tipo in tipos:
        # So os primeiros 2-3 bytes
        n_bytes = min(3, len(ASSINATURAS[tipo]))
        blob = ASSINATURAS[tipo][:n_bytes]
        texto = blob_para_texto(blob)
        acao, conf = c.decidir(texto, (None, 0.0))
        esperado = "arq_" + tipo
        ok = acao == esperado
        if ok:
            acertos_parc += 1
        total_parc += 1
        tag = "OK" if ok else "ERR"
        print(f"  {tipo.upper():<6s} (primeiros {n_bytes} bytes) -> {acao:<12s} conf={conf:.3f} [{tag}]")
    
    print(f"\n  Parcial acertos: {acertos_parc}/{total_parc} = {acertos_parc/total_parc*100:.1f}%")
    
    # === Fase 6: Que features o MCR aprendeu? ===
    print("\n[6] Features b: aprendidas por tipo (magic numbers)...")
    for tipo in tipos:
        feat_dict = c._acao_features.get("arq_" + tipo, {})
        bytes_feat = {k: v for k, v in feat_dict.items() if k.startswith("b:")}
        if bytes_feat:
            # Top 5 bytes mais frequentes
            top5 = sorted(bytes_feat.items(), key=lambda x: -x[1])[:5]
            bytes_hex = [f"0x{k.split(':')[1]}({v})" for k, v in top5]
            print(f"  {tipo.upper():<6s}: {', '.join(bytes_hex)}")
    
    # === Fase 7: BLOB desconhecido — o que o MCR faz? ===
    print("\n[7] BLOB desconhecido (sem assinatura conhecida)...")
    random.seed(42)
    blob_desconhecido = bytes(random.randint(0, 255) for _ in range(64))
    texto = blob_para_texto(blob_desconhecido)
    acao, conf = c.decidir(texto, (None, 0.0))
    print(f"  Blob aleatorio -> {acao} (conf={conf:.3f})")
    if conf < 0.2:
        print(f"  >>> MCR admite ignorancia (Pilar 9) — conf baixa")
    else:
        print(f"  >>> MCR forca classificacao (conf media/alta)")
    
    # === Resumo ===
    print("\n" + "=" * 70)
    print("  RESUMO: MCR lendo BLOBs")
    print("=" * 70)
    print(f"\n  Classificacao de blobs: {acertos}/{total} = {acertos/total*100:.1f}%")
    print(f"  Zero-shot (so assinatura): {acertos_zs}/{total_zs} = {acertos_zs/total_zs*100:.1f}%")
    print(f"  Assinatura parcial (2-3 bytes): {acertos_parc}/{total_parc} = {acertos_parc/total_parc*100:.1f}%")
    
    # Salvar
    resultado = {
        "teste": "blob_binario",
        "n_tipos": len(tipos),
        "n_treinamento": n_treinamento,
        "classificacao": {"acertos": acertos, "total": total},
        "zero_shot": {"acertos": acertos_zs, "total": total_zs},
        "parcial": {"acertos": acertos_parc, "total": total_parc},
    }
    path_out = os.path.join(os.path.dirname(__file__), "resultados", "31_blob.json")
    with open(path_out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\nResultado salvo: {path_out}")


if __name__ == "__main__":
    main()
