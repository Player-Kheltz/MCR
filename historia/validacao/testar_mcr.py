"""Testa o MCR contra 11 amostras de formatos diferentes.
Gera relatorio markdown automatico."""
import os, sys, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from MCR import MCR, MCRByteUtils, MCRMotor, MCRPiEngine

BASE = os.path.dirname(__file__)
SAMPLES_DIR = os.path.join(BASE, 'amostras')
RESULTADOS = os.path.join(BASE, 'resultados.md')

def analisar_arquivo(caminho):
    """Aplica MCR num arquivo e retorna metricas."""
    with open(caminho, 'rb') as f:
        dados = f.read()

    nome = os.path.basename(caminho)
    ext = nome.split('.')[-1] if '.' in nome else 'bin'

    # MCRByteUtils — usa bytes BRUTOS, sem decodificar como texto
    entropia_bytes = MCRByteUtils.entropia_bytes(dados)
    fingerprint = MCRByteUtils.fingerprint(str(dados[:500]), 8)

    # MCR puro (nivel byte)
    mk = MCR(nome)
    mk.aprender_sequencia([f"B:{b:02x}" for b in dados[:2000]])
    stats = mk.stats()

    # Transicoes top 5
    top_estados = sorted(mk.freq.items(), key=lambda x: -x[1])[:5]

    return {
        'arquivo': nome,
        'tipo': ext,
        'tamanho': len(dados),
        'entropia_bytes': round(entropia_bytes, 3),
        'fingerprint': [round(v, 3) for v in fingerprint],
        'markov_estados': stats['estados'],
        'markov_transicoes': stats['transicoes'],
        'entropia_markov': stats['entropia_media'],
        'top_5_estados': [(k, v) for k, v in top_estados],
    }

def comparar_pares(analises):
    """Calcula Jaccard entre todos os pares usando bytes brutos."""
    pares = {}
    nomes = [a['arquivo'] for a in analises]
    dados_raw = {}
    for a in analises:
        caminho = os.path.join(SAMPLES_DIR, a['arquivo'])
        with open(caminho, 'rb') as f:
            dados_raw[a['arquivo']] = f.read(500)

    def _bytes_to_str(b):
        """Converte bytes para str preservando todos os valores."""
        return ' '.join(f"{x:02x}" for x in b)

    for i in range(len(nomes)):
        for j in range(i + 1, len(nomes)):
            a, b = nomes[i], nomes[j]
            # Converte para hex string para jaccard_bytes
            sa = _bytes_to_str(dados_raw[a])
            sb = _bytes_to_str(dados_raw[b])
            ja = MCRByteUtils.jaccard_bytes(sa, sb)
            cos = MCRByteUtils.similaridade_cosseno(sa, sb)
            pares[f"{a} vs {b}"] = {
                'jaccard': round(ja, 4),
                'cosseno': round(cos, 4),
            }
    return pares

def gerar_relatorio(analises, pares):
    """Gera relatorio markdown."""
    linhas = []
    linhas.append("# Validacao MCR — Relatorio Automatico")
    linhas.append("")
    linhas.append(f"Gerado em: {__import__('datetime').datetime.now().isoformat()}")
    linhas.append(f"Amostras: {len(analises)}")
    linhas.append("")

    # Tabela de metricas
    linhas.append("## 1. Metricas por Amostra")
    linhas.append("")
    linhas.append("| Amostra | Tipo | Bytes | Entropia (bytes) | Estados MK | Transicoes MK | Entropia MK |")
    linhas.append("|---------|------|------:|-----------------:|-----------:|--------------:|------------:|")
    for a in sorted(analises, key=lambda x: -x['entropia_bytes']):
        linhas.append(
            f"| {a['arquivo']:30s} | {a['tipo']:5s} | {a['tamanho']:6d} | "
            f"{a['entropia_bytes']:15.3f} | {a['markov_estados']:9d} | "
            f"{a['markov_transicoes']:12d} | {a['entropia_markov']:10.3f} |"
        )
    linhas.append("")

    # Fingerprints
    linhas.append("## 2. Fingerprint (8 dimensoes)")
    linhas.append("")
    linhas.append("| Amostra | D0 | D1 | D2 | D3 | D4 | D5 | D6 | D7 |")
    linhas.append("|---------|----|----|----|----|----|----|----|----|")
    for a in sorted(analises, key=lambda x: x['arquivo']):
        fp = a['fingerprint']
        linhas.append(
            f"| {a['arquivo']:30s} | {fp[0]:.3f} | {fp[1]:.3f} | {fp[2]:.3f} | "
            f"{fp[3]:.3f} | {fp[4]:.3f} | {fp[5]:.3f} | {fp[6]:.3f} | {fp[7]:.3f} |"
        )
    linhas.append("")

    # Top 5 estados
    linhas.append("## 3. Top 5 Estados (bytes mais frequentes)")
    linhas.append("")
    for a in sorted(analises, key=lambda x: x['arquivo']):
        linhas.append(f"**{a['arquivo']}:**")
        for estado, freq in a['top_5_estados'][:5]:
            try:
                char = chr(int(estado[2:], 16)) if estado.startswith('B:') else estado
                char_repr = f"'{char}'" if char.isprintable() else f"0x{int(estado[2:], 16):02X}"
            except:
                char_repr = estado
            linhas.append(f"  - `{estado}` ({char_repr}) x {freq}")
        linhas.append("")

    # Pares
    linhas.append("## 4. Matriz de Similaridade (Jaccard)")
    linhas.append("")
    maiores = sorted(pares.items(), key=lambda x: -x[1]['jaccard'])
    for nome_par, vals in maiores:
        linhas.append(f"| {nome_par:60s} | J={vals['jaccard']:.4f} | C={vals['cosseno']:.4f} |")
    linhas.append("")

    # Validacao
    linhas.append("## 5. Validacao das Hipoteses")
    linhas.append("")

    hipoteses = []

    # H1: silencio ≈ 0
    for a in analises:
        if 'silencio' in a['arquivo']:
            h1 = a['entropia_bytes'] < 0.5
            hipoteses.append((
                "H1: entropia(silencio) ≈ 0 (estrutura maxima)",
                h1,
                f"entropia = {a['entropia_bytes']:.3f}"
            ))
            break

    # H2: barulho ≈ 8
    for a in analises:
        if 'barulho' in a['arquivo']:
            h2 = a['entropia_bytes'] > 7.0
            hipoteses.append((
                "H2: entropia(ruido) ≈ 8 (aleatoriedade maxima)",
                h2,
                f"entropia = {a['entropia_bytes']:.3f}"
            ))
            break

    # H3: zeros ≈ 0
    for a in analises:
        if 'zeros' in a['arquivo']:
            h3 = a['entropia_bytes'] < 0.5
            hipoteses.append((
                "H3: entropia(zeros) ≈ 0 (bytes repetidos)",
                h3,
                f"entropia = {a['entropia_bytes']:.3f}"
            ))
            break

    # H4: aleatorio ≈ 8
    for a in analises:
        if 'aleatorio' in a['arquivo'] and 'binario' in a['arquivo']:
            h4 = a['entropia_bytes'] > 7.0
            hipoteses.append((
                "H4: entropia(aleatorio) ≈ 8 (bytes aleatorios)",
                h4,
                f"entropia = {a['entropia_bytes']:.3f}"
            ))
            break

    # H5: identicos = 1.0
    for nome_par in pares:
        if 'silencio' in nome_par and nome_par.count('silencio') > 1:
            h5 = pares[nome_par]['jaccard'] == 1.0
            hipoteses.append((
                "H5: jaccard(identicos) = 1.0 (mesmo arquivo)",
                h5,
                f"jaccard = {pares[nome_par]['jaccard']:.4f}"
            ))
            break

    # H6: silencio vs barulho ≈ 0
    for nome_par in pares:
        if 'silencio' in nome_par and 'barulho' in nome_par:
            h6 = pares[nome_par]['jaccard'] < 0.1
            hipoteses.append((
                "H6: jaccard(silencio, barulho) ≈ 0 (diferentes)",
                h6,
                f"jaccard = {pares[nome_par]['jaccard']:.4f}"
            ))
            break

    # H7: texto distingue estrutura
    for nome_par in pares:
        if 'lorem' in nome_par and 'repetitivo' in nome_par:
            h7 = pares[nome_par]['jaccard'] < 0.3
            hipoteses.append((
                "H7: jaccard(texto, repetitivo) < 0.3 (estruturas diferentes)",
                h7,
                f"jaccard = {pares[nome_par]['jaccard']:.4f}"
            ))
            break

    for desc, resultado, detalhe in hipoteses:
        status = "PASSOU" if resultado else "FALHOU"
        linhas.append(f"| {desc:60s} | {status:6s} | {detalhe} |")

    # Resumo
    linhas.append("")
    linhas.append("## 6. Resumo Final")
    linhas.append("")
    passaram = sum(1 for _, r, _ in hipoteses if r)
    total = len(hipoteses)
    pct = passaram / total * 100 if total > 0 else 0
    linhas.append(f"**Hipoteses validadas: {passaram}/{total} ({pct:.0f}%)**")
    linhas.append("")
    if pct >= 80:
        linhas.append("**Conclusao: O MCR distingue corretamente estrutura de ruido em multiplos formatos.**")
    else:
        linhas.append("**Conclusao: O MCR precisa de ajustes para os formatos testados.**")

    return '\n'.join(linhas)

def main():
    print("=" * 60)
    print("VALIDACAO MCR — Testando contra 11 amostras")
    print("=" * 60)
    print()

    if not os.path.exists(SAMPLES_DIR):
        print("ERRO: gere as amostras primeiro: python gerar_amostras.py")
        return 1

    amostras = sorted([
        os.path.join(SAMPLES_DIR, f) for f in os.listdir(SAMPLES_DIR)
    ])

    print(f"Analisando {len(amostras)} amostras...")

    # Fase 1: analisar cada uma
    analises = []
    for i, caminho in enumerate(amostras, 1):
        nome = os.path.basename(caminho)
        print(f"  [{i}/{len(amostras)}] {nome}...", end=' ')
        try:
            analise = analisar_arquivo(caminho)
            analises.append(analise)
            print(f"OK (H={analise['entropia_bytes']:.3f})")
        except Exception as e:
            print(f"ERRO: {e}")

    # Fase 2: comparar pares
    print()
    print("Comparando pares...")
    pares = comparar_pares(analises)
    print(f"  {len(pares)} pares calculados")

    # Fase 3: gerar relatorio
    print()
    print("Gerando relatorio...")
    relatorio = gerar_relatorio(analises, pares)

    with open(RESULTADOS, 'w', encoding='utf-8') as f:
        f.write(relatorio)
    print(f"  Relatorio salvo em: {RESULTADOS}")

    # Resumo rapido
    print()
    print("=" * 60)
    print("RESUMO RAPIDO")
    print("=" * 60)
    for a in sorted(analises, key=lambda x: -x['entropia_bytes']):
        barra = '#' * max(0, min(20, int(a['entropia_bytes'] * 2.5)))
        print(f"  H={a['entropia_bytes']:.3f} {barra:20s} {a['arquivo']:30s}")
    print()

    # Valida entropia escala corretamente
    max_h = max(a['entropia_bytes'] for a in analises)
    min_h = min(a['entropia_bytes'] for a in analises)
    print(f"  Entropia maxima: {max_h:.3f} (esperado ~8)")
    print(f"  Entropia minima: {min_h:.3f} (esperado ~0)")
    print(f"  Diferenca: {max_h - min_h:.3f} (esperado ~8)")
    print()
    if max_h - min_h > 5:
        print("  ESCALA OK — MCR distingue estrutura vs ruido")
    else:
        print("  ESCALA FRACA — diferenca pequena entre extremos")

    # Limpa arquivos temporarios do MCR (session)
    try:
        import shutil
        shutil.rmtree(os.path.join(BASE, 'cache'), ignore_errors=True)
    except:
        pass

    return 0

if __name__ == '__main__':
    sys.exit(main())
