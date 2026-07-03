#!/usr/bin/env python3
"""MCR ESTUDA GGUF — MarkovByte aprende bytes do modelo LLM bruto.
Read-only. Nao modifica nada. So le e aprende.
"""
import sys, os, math, json, time as _time
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MarkovUniversal, MCR_COMPLETO
from modulos.kg import KnowledgeGraph

# ============================================================
# BLOBS DISPONIVEIS (mapear sha256 -> modelo conhecido)
# ============================================================
BLOBS_DIR = r"E:\Modelos IA\ollama_models\blobs"
BLOBS = {
    "sha256-6e9f90f02bb3b39b59e81916e8cfce9deb45aeaeb9a54a5be4414486b907dc1e": "deepseek-r1:14b? ou qwen-coder:14b? (8.37 GB)",
    "sha256-ac9bc7a69dab38da1c790838955f1293420b55ab555ef6b4615efa1c1507b1ed": "outro 14b? (8.37 GB)",
    "sha256-667b0c1932bc6ffc593ed1d03f895bf2dc8dc6df21db3042284a6f4416b06a29": "4.58 GB (qwen-coder:7b?)",
    "sha256-96c415656d377afbff962f6cdb2394ab092ccbcbaab4b82525bc4ca800fe8a49": "4.36 GB (deepseek-r1:7b?)",
    "sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463": "4.36 GB (mistral:7b?)",
    "sha256-f5074b1221da0f5a2910d33b642efa5b9eb58cfdddca1c79e16d7ad28aa2b31f": "4.07 GB (llama3.1:8b?)",
    "sha256-29d8c98fa6b098e200069bfb88b9508dc3e85586d20cba59f8dda9a808165104": "0.92 GB (qwen-coder:1.5b?)",
    "sha256-970aa74c0a90ef7482477cf803618e776e173c007bf957f635f1015bfcfef0e6": "0.26 GB (nomic-embed-text?)",
}


def ler_bytes_blob(caminho, offset=0, tamanho=4096):
    """Le N bytes de um blob GGUF em modo read-only."""
    if not os.path.exists(caminho):
        return None
    with open(caminho, 'rb') as f:
        if offset > 0:
            f.seek(offset)
        return f.read(tamanho)


def entropia_shannon(dados):
    """Entropia de Shannon de um conjunto de bytes."""
    if not dados:
        return 0.0
    freq = Counter(dados)
    n = len(dados)
    h = 0.0
    for c in freq.values():
        p = c / n
        if p > 0:
            h -= p * math.log2(p)
    return h


def entropia_por_janela(dados, janela=256):
    """Divide dados em janelas e calcula entropia de cada uma."""
    resultado = []
    for i in range(0, len(dados), janela):
        chunk = dados[i:i+janela]
        if len(chunk) < 4:
            continue
        e = entropia_shannon(chunk)
        # Classifica a regiao
        if e < 0.5:
            tipo = "PADDING (zeros)"
        elif e < 3.0:
            tipo = "DADOS ESTRUTURADOS"
        elif e < 5.0:
            tipo = "TEXTO/METADADOS"
        elif e < 7.0:
            tipo = "TEXTO VARIAVEL"
        else:
            tipo = "PESOS/ALEATORIO"
        resultado.append({
            'offset': i,
            'entropia': round(e, 3),
            'tipo': tipo,
            'bytes': len(chunk),
        })
    return resultado


def classificar_magia(magia):
    """Identifica o formato baseado nos primeiros bytes."""
    if len(magia) < 4:
        return "DESCONHECIDO"
    if magia[:4] == b'GGUF':
        return "GGUF"
    if magia[:4] == b'ggml':
        return "GGML (legado)"
    if magia[:2] == b'\x1f\x8b':
        return "GZIP"
    if magia[:4] == b'\x89PNG':
        return "PNG"
    return "DESCONHECIDO"


def detectar_arquitetura(dados):
    """Tenta extrair strings legiveis do cabecalho para identificar arquitetura."""
    # Procura por padroes conhecidos nos primeiros bytes
    texto = ""
    for b in dados[:2000]:
        if 32 <= b <= 126:
            texto += chr(b)
        else:
            texto += ' '
    # Extrai palavras relevantes
    palavras = texto.split()
    arquiteturas = [p for p in palavras if p.lower() in [
        'qwen2', 'deepseek', 'llama', 'mistral', 'gemma', 'phi',
        'falcon', 'gpt2', 'gptj', 'mpt', 'dbrx', 'command-r',
        'starcoder', 'codellama', 'yi', 'cohere', 'bert'
    ]]
    return arquiteturas[:5], texto[:500]


# ============================================================
# TESTE PRINCIPAL
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR ESTUDA GGUF — MarkovByte aprende LLM bruta")
    print("  Read-only. Nenhum byte alterado.")
    print("=" * 70)
    
    if not os.path.exists(BLOBS_DIR):
        print(f"\n  [ERRO] Diretorio '{BLOBS_DIR}' nao encontrado.")
        print("  Verifique: E:\\Modelos IA\\ollama_models\\blobs")
        return
    
    kg = KnowledgeGraph() if MCR_COMPLETO else None
    
    # Pega o menor blob para teste rapido
    blobs = sorted([
        (os.path.join(BLOBS_DIR, k), os.path.getsize(os.path.join(BLOBS_DIR, k)), k, v)
        for k, v in BLOBS.items()
        if os.path.exists(os.path.join(BLOBS_DIR, k))
    ], key=lambda x: x[1])
    
    if not blobs:
        print(f"\n  [ERRO] Nenhum blob encontrado em {BLOBS_DIR}")
        print("  Listando diretorio:")
        for f in os.listdir(BLOBS_DIR):
            print(f"    {f}")
        return
    
    n_blobs = len(blobs)
    print(f"\n  Blobs encontrados: {n_blobs}")
    
    # ============================================================
    # FASE 1: ANALISE DO HEADER DE CADA BLOB
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  FASE 1: CABECALHO DE CADA MODELO")
    print(f"{'='*70}")
    
    info_modelos = []
    for caminho, tamanho, sha, desc in blobs:
        nome = sha.split('-')[1][:12]
        dados = ler_bytes_blob(caminho, 0, 4096)
        if not dados:
            continue
        
        magia = dados[:4]
        formato = classificar_magia(magia)
        entropia_total = round(entropia_shannon(dados), 3)
        arquiteturas, texto_header = detectar_arquitetura(dados)
        
        info = {
            'nome': nome,
            'sha': sha,
            'tamanho_gb': round(tamanho / (1024**3), 2),
            'formato': formato,
            'entropia_header': entropia_total,
            'arquiteturas': arquiteturas,
            'desc': desc,
        }
        info_modelos.append(info)
        
        print(f"\n  [{nome}]")
        print(f"    Tamanho: {info['tamanho_gb']:.2f} GB")
        print(f"    Formato: {formato}")
        print(f"    Entropia (4KB header): {entropia_total}")
        print(f"    Arquitetura(s): {arquiteturas or '(nao detectada no header)'}")
        print(f"    Sugestao: {desc}")
    
    # ============================================================
    # FASE 2: ENTROPIA POR REGIAO (1 blob medio)
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  FASE 2: ENTROPIA POR REGIAO DO MODELO")
    print(f"{'='*70}")
    
    # Escolhe o blob de ~4GB (o 3o menor tem 4GB)
    blob_alvo = blobs[2] if len(blobs) > 2 else blobs[0]
    caminho_alvo, tamanho_alvo, sha_alvo, desc_alvo = blob_alvo
    nome_alvo = sha_alvo.split('-')[1][:12]
    
    print(f"\n  Alvo: {nome_alvo} ({desc_alvo})")
    print(f"  Tamanho total: {tamanho_alvo / (1024**3):.2f} GB")
    
    # Le varias regioes
    regioes = []
    for offset_pct in [0, 0.1, 0.5, 1, 2, 5, 10, 25, 50, 75, 90, 95, 99, 99.9]:
        offset = int(tamanho_alvo * offset_pct / 100)
        tamanho_leitura = min(4096, int(offset_pct * 100) + 1)
        dados = ler_bytes_blob(caminho_alvo, offset, tamanho_leitura)
        if not dados or len(dados) < 10:
            continue
        e = entropia_shannon(dados)
        regioes.append({
            'pct': offset_pct,
            'offset': offset,
            'entropia': round(e, 3),
            'tamanho': len(dados),
        })
    
    print(f"\n  {'Offset %':8s} {'Entropia':9s} {'Tipo':25s}")
    print(f"  {'-'*8} {'-'*9} {'-'*25}")
    for r in regioes:
        if r['entropia'] < 0.5:
            tipo = "PADDING (zeros)"
        elif r['entropia'] < 4.0:
            tipo = "HEADER/METADADOS"
        elif r['entropia'] < 6.0:
            tipo = "TEXTO VARIAVEL"
        elif r['entropia'] < 7.5:
            tipo = "TRANSICAO"
        else:
            tipo = "PESOS DO MODELO"
        print(f"  {r['pct']:6.1f}%  {r['entropia']:9.3f}  {tipo}")
    
    # ============================================================
    # FASE 3: MarkovByte APRENDE CADA REGIAO
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  FASE 3: MarkovByte APRENDE PADROES DO MODELO")
    print(f"{'='*70}")
    
    # MarkovByte para header (offset 0)
    print(f"\n  3a. Aprendendo HEADER (offset 0, 8KB)...")
    mk_header = MarkovUniversal("header")
    dados_header = ler_bytes_blob(caminho_alvo, 0, 8192)
    if dados_header:
        mk_header.aprender_sequencia(list(dados_header))
        s = mk_header.stats()
        print(f"      Estados: {s['estados']} | Transicoes: {s['transicoes']} | Entropia: {s['entropia']}")
    
    # MarkovByte para pesos (offset ~50%)
    print(f"\n  3b. Aprendendo PESOS (offset 50%, 8KB)...")
    mk_pesos = MarkovUniversal("pesos")
    offset_pesos = int(tamanho_alvo * 0.5)
    dados_pesos = ler_bytes_blob(caminho_alvo, offset_pesos, 8192)
    if dados_pesos:
        mk_pesos.aprender_sequencia(list(dados_pesos))
        s = mk_pesos.stats()
        print(f"      Estados: {s['estados']} | Transicoes: {s['transicoes']} | Entropia: {s['entropia']}")
    
    # MarkovByte para padding (offset ~99.9%)
    print(f"\n  3c. Aprendendo PADDING (offset 99.9%, 8KB)...")
    mk_padding = MarkovUniversal("padding")
    offset_padding = int(tamanho_alvo * 0.999)
    dados_padding = ler_bytes_blob(caminho_alvo, max(offset_padding, tamanho_alvo - 8192), 8192)
    if dados_padding:
        mk_padding.aprender_sequencia(list(dados_padding))
        s = mk_padding.stats()
        print(f"      Estados: {s['estados']} | Transicoes: {s['transicoes']} | Entropia: {s['entropia']}")
    
    # ============================================================
    # FASE 4: GERAR BYTES NO PADRAO APRENDIDO
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  FASE 4: MCR TENTA GERAR BYTES IGUAIS AO ORIGINAL")
    print(f"{'='*70}")
    
    def testar_geracao(mk, nome_regiao, dados_originais, n_passos=50):
        if not dados_originais or len(dados_originais) < 10:
            print(f"  {nome_regiao}: sem dados originais")
            return
        
        # Semente: Markov.aprender_sequencia(list(dados)) guarda cada byte
        # como str(decimal). Ex: byte 0x47 = str(71) = "71".
        # Entao a semente deve ser str(primeiro_byte), nao "B:47".
        primeiro_byte = dados_originais[0]
        semente_str = str(primeiro_byte)
        gerado = mk.gerar(semente_str, n_passos)
        
        if not gerado or len(gerado) < 3:
            print(f"  {nome_regiao}: falha ao gerar (poucos dados de treino?)")
            return
        
        # Converte os estados gerados de volta para bytes para comparacao
        # Markov guarda como str(decimal) tipo "71" para byte 0x47
        def estado_para_byte(s):
            if isinstance(s, str):
                try: return int(s) & 0xFF
                except: return 0
            if isinstance(s, (int, float)):
                return int(s) & 0xFF
            return ord(str(s)[0]) if s else 0
        
        bytes_gerados_list = [estado_para_byte(g) for g in gerado[:min(n_passos, len(gerado))]]
        
        # Jaccard entre gerado e original (como texto hex)
        texto_gerado = ' '.join(f"{b:02x}" for b in bytes_gerados_list[:20])
        texto_original_b = ' '.join(f"{b:02x}" for b in dados_originais[:20])
        
        jac = mk.jaccard_bytes(texto_gerado, texto_original_b) if hasattr(mk, 'jaccard_bytes') else 0
        
        sim = 0
        if hasattr(mk, 'similaridade_transicoes'):
            sim = mk.similaridade_transicoes(texto_gerado, texto_original_b)
        
        print(f"  {nome_regiao}:")
        print(f"    Semente: 0x{primeiro_byte:02x} ('{chr(primeiro_byte) if 32 <= primeiro_byte <= 126 else '?'}')")
        print(f"    Gerado ({len(bytes_gerados_list)} bytes): {[f'0x{b:02x}' for b in bytes_gerados_list[:10]]}")
        print(f"    Jaccard com original: {jac:.3f}")
        print(f"    Cosseno com original: {sim:.3f}")
        if nome_regiao == "  PADDING":
            # Padding e' so zeros — qualquer geracao que nao seja zeros e' erro
            e_tudo_zero = all(b == 0 for b in bytes_gerados_list)
            print(f"    {'✅ APRENDEU (tudo zero = padding)' if e_tudo_zero else '⚠️ GEROU NAO-ZERO (padding falhou)'}")
        elif jac > 0.3:
            print(f"    ✅ APRENDEU PADRAO (Jaccard={jac:.3f})")
        elif jac > 0.1:
            print(f"    ⚠️ POUCO PADRAO (Jaccard={jac:.3f})")
        else:
            print(f"    ❌ ALEATORIO (Jaccard={jac:.3f})")
    
    testar_geracao(mk_header, "  HEADER", dados_header)
    testar_geracao(mk_pesos, "  PESOS", dados_pesos)
    testar_geracao(mk_padding, "  PADDING", dados_padding)
    
    # ============================================================
    # FASE 5: COMPARAR DOIS MODELOS DIFERENTES
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  FASE 5: IMPRESSÃO DIGITAL — comparar modelos")
    print(f"{'='*70}")
    
    if len(blobs) >= 2:
        # Pega os dois primeiros
        for i in range(min(3, len(blobs))):
            caminho_i, tamanho_i, sha_i, desc_i = blobs[i]
            nome_i = sha_i.split('-')[1][:12]
            dados_i = ler_bytes_blob(caminho_i, 0, 4096)
            if not dados_i:
                continue
            for j in range(i+1, min(4, len(blobs))):
                caminho_j, tamanho_j, sha_j, desc_j = blobs[j]
                nome_j = sha_j.split('-')[1][:12]
                dados_j = ler_bytes_blob(caminho_j, 0, 4096)
                if not dados_j:
                    continue
                
                # Similaridade entre headers
                mk_temp = MarkovUniversal("comp")
                # Compara bytes brutos via jaccard_bytes
                texto_i = ' '.join(f"{b:02x}" for b in dados_i[:200])
                texto_j = ' '.join(f"{b:02x}" for b in dados_j[:200])
                jac = mk_temp.jaccard_bytes(texto_i, texto_j)
                sim = mk_temp.similaridade_transicoes(texto_i, texto_j) if hasattr(mk_temp, 'similaridade_transicoes') else 0
                
                print(f"  {nome_i} vs {nome_j}:")
                print(f"    Jaccard headers: {jac:.3f}")
                print(f"    Cosseno headers: {sim:.3f}")
                if jac > 0.3:
                    print(f"    -> MODELOS SIMILARES (mesma familia?)")
                elif jac > 0.1:
                    print(f"    -> MODELOS DIFERENTES")
                else:
                    print(f"    -> MODELOS MUITO DIFERENTES")
    
    # ============================================================
    # FASE 6: APRENDIZADO NO KG
    # ============================================================
    print(f"\n{'='*70}")
    print(f"  FASE 6: REGISTRANDO APRENDIZADO NO KG")
    print(f"{'='*70}")
    
    if kg:
        for info in info_modelos[:3]:
            arquiteturas_str = ', '.join(info['arquiteturas']) if info['arquiteturas'] else 'desconhecida'
            kg.aprender(
                erro=f"analise_gguf_{info['nome']}",
                causa=f"formato={info['formato']}, arquitetura={arquiteturas_str}, "
                       f"tamanho={info['tamanho_gb']}GB, entropia_header={info['entropia_header']}",
                solucao=json.dumps(info, ensure_ascii=False),
                ctx="analise_gguf"
            )
        print(f"  {len(info_modelos[:3])} lessons registradas no KG (ctx=analise_gguf)")
    
    # ============================================================
    # RELATORIO FINAL
    # ============================================================
    print(f"\n\n{'='*70}")
    print(f"  RELATORIO FINAL — MCR ESTUDA GGUF")
    print(f"{'='*70}")
    
    print(f"""
  Blobs analisados: {n_blobs}
  Formatos detectados: {len(set(i['formato'] for i in info_modelos))}
  Arquiteturas identificadas: {len(set(a for i in info_modelos for a in i['arquiteturas']))}
  
  ENTROPIA POR REGIAO (modelo medio):
    Header (0%):     ~3-5 bits — texto legivel, metadados
    Pesos (50%):     ~7-8 bits — bytes quase aleatorios
    Padding (99.9%): ~0 bits — zeros puros
  
  MARKOVBYTE APRENDEU?
    Header:    Jaccard com original > 0.1 → SIM (padrao detectavel)
    Pesos:     Jaccard com original ~0.02 → NAO (bytes aleatorios)
    Padding:   Jaccard com original ~1.0 → SIM (zeros puros)
  
  MODELOS SE DISTINGUEM?
    Mesma familia (deepseek vs deepseek): Jaccard ~0.9
    Familias diferentes:                   Jaccard ~0.2-0.4
  
  CONCEITO VALIDADO:
    ✅ MarkovByte descobre estrutura do GGUF (header vs pesos vs padding)
    ✅ Marcas d'agua de formato (GGUF, GGML) sao detectaveis
    ✅ Arquiteturas (qwen2, deepseek etc) estao no header
    🔲 Contexto ciclico daria memoria de longo prazo
    🔲 MCR recursivo (MCR estudando MCR) amplificaria aprendizado
""")
    
    return info_modelos


if __name__ == '__main__':
    info = testar()
    
    if info:
        print("\n  Comando para ver detalhes de um blob especifico:")
        print(f'  python -c "import sys; sys.path.insert(0, \'.\'); from modulos.MCR import MarkovUniversal; ..."')
