#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCR ANALISAR MODELOS — O MCR le os blobs GGUF e descobre padroes
=================================================================
Le os headers GGUF, amostra os pesos, calcula fingerprint e entropia,
e alimenta TUDO no CerebroAGI. Depois, o proprio MCR responde
o que entendeu dos modelos.

Uso:
    python mcr_analisar_modelos.py               # analisa tudo
    python mcr_analisar_modelos.py --pergunta    # so faz perguntas
    python mcr_analisar_modelos.py --chat        # chat sobre os modelos
"""
import sys, os, struct, json, time, glob, math
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from MCR_AGI import *

BLOBS_DIR = r"E:\Modelos IA\ollama_models\blobs"
CACHE_RESULTADOS = os.path.join(CACHE_DIR, "analise_modelos.json")

# ═══════════════════════════════════════════════════════════════════
# LEITOR DE HEADER GGUF — stdlib puro, zero dependencias
# ═══════════════════════════════════════════════════════════════════

GGUF_MAGIC = b"GGUF"

def ler_header_gguf(caminho: str, max_bytes: int = 1024 * 1024) -> Optional[Dict]:
    """Le o header de um arquivo GGUF e extrai metadados.
    
    Formato GGUF v3:
      - Magic: "GGUF" (4 bytes)
      - Version: int32
      - TensorCount: int64
      - MetadataKVCount: int64
      - KV Pairs: cada um com tipo + chave + valor
      - TensorInfo: cada tensor com nome, dimensoes, tipo
    """
    try:
        with open(caminho, "rb") as f:
            header = f.read(max_bytes)
    except Exception as e:
        return {"erro": str(e)}
    
    if len(header) < 16:
        return {"erro": "arquivo muito pequeno"}
    
    if header[:4] != GGUF_MAGIC:
        return {"erro": "nao e GGUF"}
    
    resultado = {
        "arquivo": os.path.basename(caminho),
        "tamanho": os.path.getsize(caminho),
        "magic": "GGUF",
    }
    
    offset = 4
    resultado["version"] = struct.unpack("<i", header[offset:offset+4])[0]
    offset += 4
    
    # TensorCount + MetadataKVCount
    resultado["tensor_count"] = struct.unpack("<q", header[offset:offset+8])[0]
    offset += 8
    resultado["metadata_kv_count"] = struct.unpack("<q", header[offset:offset+8])[0]
    offset += 8
    
    # Le metadados KV
    metadados = {}
    for _ in range(min(resultado["metadata_kv_count"], 100)):
        if offset + 4 > len(header):
            break
        tipo = struct.unpack("<i", header[offset:offset+4])[0]
        offset += 4
        
        # Chave (string)
        if offset + 8 > len(header):
            break
        str_len = struct.unpack("<q", header[offset:offset+8])[0]
        offset += 8
        if offset + str_len > len(header):
            break
        chave = header[offset:offset+str_len].decode("utf-8", errors="replace")
        offset += str_len
        
        # Valor (depende do tipo)
        valor = None
        if tipo == 0:  # UINT8
            if offset + 1 <= len(header):
                valor = header[offset]
                offset += 1
        elif tipo == 1:  # INT8
            if offset + 1 <= len(header):
                valor = struct.unpack("<b", header[offset:offset+1])[0]
                offset += 1
        elif tipo == 2:  # UINT16
            if offset + 2 <= len(header):
                valor = struct.unpack("<H", header[offset:offset+2])[0]
                offset += 2
        elif tipo == 3:  # INT16
            if offset + 2 <= len(header):
                valor = struct.unpack("<h", header[offset:offset+2])[0]
                offset += 2
        elif tipo == 4:  # UINT32
            if offset + 4 <= len(header):
                valor = struct.unpack("<I", header[offset:offset+4])[0]
                offset += 4
        elif tipo == 5:  # INT32
            if offset + 4 <= len(header):
                valor = struct.unpack("<i", header[offset:offset+4])[0]
                offset += 4
        elif tipo == 6:  # UINT64
            if offset + 8 <= len(header):
                valor = struct.unpack("<Q", header[offset:offset+8])[0]
                offset += 8
        elif tipo == 7:  # INT64
            if offset + 8 <= len(header):
                valor = struct.unpack("<q", header[offset:offset+8])[0]
                offset += 8
        elif tipo == 8:  # FLOAT32
            if offset + 4 <= len(header):
                valor = round(struct.unpack("<f", header[offset:offset+4])[0], 6)
                offset += 4
        elif tipo == 9:  # FLOAT64
            if offset + 8 <= len(header):
                valor = round(struct.unpack("<d", header[offset:offset+8])[0], 6)
                offset += 8
        elif tipo == 10:  # BOOL
            if offset + 1 <= len(header):
                valor = bool(header[offset])
                offset += 1
        elif tipo == 11:  # STRING
            if offset + 8 <= len(header):
                str_len2 = struct.unpack("<q", header[offset:offset+8])[0]
                offset += 8
                if 0 <= str_len2 <= 100000 and offset + str_len2 <= len(header):
                    valor = header[offset:offset+str_len2].decode("utf-8", errors="replace")
                    offset += str_len2
        elif tipo == 12:  # ARRAY (pula — complexo)
            valor = "[array]"
            offset += 16  # estimativa
        
        if chave:
            metadados[chave] = valor
    
    resultado["metadados"] = metadados
    
    # Extrai info estrutural do header
    for chave_info in ["general.architecture", "general.name", "general.quantization_version",
                       "llama.context_length", "llama.embedding_length", "llama.block_count",
                       "llama.vocab_size", "llama.rope.dimension_count",
                       "general.file_type", "tokenizer.ggml.model"]:
        resultado[chave_info] = metadados.get(chave_info)
    
    return resultado


# ═══════════════════════════════════════════════════════════════════
# AMOSTRADOR DE PESOS
# ═══════════════════════════════════════════════════════════════════

def amostrar_pesos(caminho: str, n_amostras: int = 5, bytes_por_amostra: int = 65536) -> Dict:
    """Amostra os pesos de um blob GGUF em N pontos.
    
    Pega amostras ao longo do arquivo (inicio, 25%, 50%, 75%, fim)
    pulando o header (primeiros ~1MB).
    """
    tamanho = os.path.getsize(caminho)
    offset_header = min(1024 * 1024, tamanho // 20)  # pula o header
    
    amostras = {}
    with open(caminho, "rb") as f:
        for i in range(n_amostras):
            # Posicao da amostra ao longo do arquivo (depois do header)
            frac = (i + 1) / (n_amostras + 1)
            pos = int(offset_header + frac * (tamanho - offset_header))
            pos = min(pos, tamanho - bytes_por_amostra)
            pos = max(pos, 0)
            
            f.seek(pos)
            dados = f.read(bytes_por_amostra)
            
            if not dados:
                continue
            
            # Fingerprint
            fp = MCRByteUtils.fingerprint(dados, 16)
            
            # Entropia
            ent = MCRByteUtils.entropia_bytes(dados)
            
            # Distribuicao de bytes
            dist = {}
            for b in dados[:1000]:
                dist[b] = dist.get(b, 0) + 1
            
            amostras[f"amostra_{i}"] = {
                "posicao": pos,
                "offset_pct": round(pos / tamanho * 100, 1),
                "fingerprint": [round(v, 3) for v in fp],
                "entropia": round(ent, 3),
                "bytes_unicos": len(dist),
                "byte_mais_frequente": max(dist, key=dist.get) if dist else 0,
            }
    
    return {
        "tamanho": tamanho,
        "amostras": amostras,
        "entropia_media": round(sum(a["entropia"] for a in amostras.values()) / max(len(amostras), 1), 3),
    }


# ═══════════════════════════════════════════════════════════════════
# COMPARACAO ENTRE MODELOS
# ═══════════════════════════════════════════════════════════════════

def comparar_modelos(resultados: Dict) -> List[Dict]:
    """Compara todos os pares de modelos por fingerprint e entropia."""
    nomes = sorted(resultados.keys())
    comparacoes = []
    
    for i in range(len(nomes)):
        for j in range(i + 1, len(nomes)):
            a, b = nomes[i], nomes[j]
            ra, rb = resultados[a], resultados[b]
            
            # Similaridade de fingerprint (media entre amostras)
            sims = []
            for ka in ra.get("pesos", {}).get("amostras", {}):
                for kb in rb.get("pesos", {}).get("amostras", {}):
                    fa = ra["pesos"]["amostras"][ka]["fingerprint"]
                    fb = rb["pesos"]["amostras"][kb]["fingerprint"]
                    sim = MCRByteUtils.similaridade_cosseno(fa, fb)
                    sims.append(sim)
            sim_media = sum(sims) / max(len(sims), 1) if sims else 0
            
            # Diferenca de entropia
            diff_ent = abs(ra.get("pesos", {}).get("entropia_media", 0) - rb.get("pesos", {}).get("entropia_media", 0))
            
            comparacoes.append({
                "a": a[:20],
                "b": b[:20],
                "sim_fingerprint": round(sim_media, 3),
                "diff_entropia": round(diff_ent, 3),
                "tamanho_a": ra.get("tamanho", 0),
                "tamanho_b": rb.get("tamanho", 0),
                "arquitetura_a": ra.get("header", {}).get("general.architecture", "?"),
                "arquitetura_b": rb.get("header", {}).get("general.architecture", "?"),
            })
    
    comparacoes.sort(key=lambda x: -x["sim_fingerprint"])
    return comparacoes


# ═══════════════════════════════════════════════════════════════════
# ALIMENTACAO NO MCR
# ═══════════════════════════════════════════════════════════════════

def alimentar_no_mcr(cerebro: CerebroAGI, resultados: Dict, comparacoes: List[Dict]):
    """Alimenta TUDO que foi descoberto no CerebroAGI."""
    
    # Alimenta cada modelo como topico
    for nome_blob, info in resultados.items():
        texto = (
            f"Modelo {nome_blob[:20]}: "
            f"tamanho {info.get('tamanho',0)/1024/1024:.0f}MB, "
            f"arquitetura {info.get('header',{}).get('general.architecture','?')}, "
            f"nome {info.get('header',{}).get('general.name','?')}, "
            f"contexto {info.get('header',{}).get('llama.context_length','?')}, "
            f"embeddings {info.get('header',{}).get('llama.embedding_length','?')}, "
            f"camadas {info.get('header',{}).get('llama.block_count','?')}, "
            f"vocabulario {info.get('header',{}).get('llama.vocab_size','?')}, "
            f"quantizacao v{info.get('header',{}).get('general.quantization_version','?')}, "
            f"entropia media {info.get('pesos',{}).get('entropia_media','?')}, "
            f"versao GGUF {info.get('header',{}).get('version','?')}"
        )
        cerebro.alimentar(texto, f"modelo_{nome_blob[:20]}")
        
        # Alimenta fingerprints das amostras como descricoes naturais
        for k_am, v_am in info.get("pesos", {}).get("amostras", {}).items():
            ent = v_am['entropia']
            tipo = "grande e complexo" if ent > 7 else "pequeno e compacto" if ent > 6 else "muito pequeno"
            cerebro.alimentar(
                f"Uma amostra extraida do modelo {nome_blob[:20]} na posicao {v_am['offset_pct']}% do arquivo "
                f"tem entropia {ent}, o que significa que este e um modelo {tipo}. "
                f"O fingerprint desta amostra e {str(v_am['fingerprint'][:4])}. "
                f"Existem {v_am['bytes_unicos']} valores de byte diferentes nesta regiao.",
                f"desc_{nome_blob[:10]}_{k_am}"
            )
    
    # Alimenta comparacoes como linguagem natural
    for c in comparacoes:
        similar = "muito similares" if c['sim_fingerprint'] > 0.8 else "diferentes" if c['sim_fingerprint'] < 0.3 else "moderadamente similares"
        relacao = "mesma arquitetura" if c['arquitetura_a'] == c['arquitetura_b'] else "arquiteturas diferentes"
        cerebro.alimentar(
            f"Os modelos {c['a']} e {c['b']} sao {similar} entre si, com similaridade de fingerprint de {c['sim_fingerprint']}. "
            f"Eles tem {relacao}. O primeiro tem {c['tamanho_a']/1024/1024:.0f}MB e o segundo tem {c['tamanho_b']/1024/1024:.0f}MB. "
            f"A diferenca de entropia entre eles e de {c['diff_entropia']}.",
            f"comp_{c['a'][:10]}_vs_{c['b'][:10]}"
        )


# ═══════════════════════════════════════════════════════════════════
# PERGUNTAS AO MCR
# ═══════════════════════════════════════════════════════════════════

def perguntar(cerebro: CerebroAGI):
    """O MCR responde o que entendeu dos modelos."""
    print("\n" + "=" * 55)
    print("  O MCR ANALISOU OS MODELOS. ELE DIZ:")
    print("=" * 55)
    print()
    
    perguntas = [
        "quantos modelos existem e quais sao suas arquiteturas",
        "qual modelo tem a maior entropia",
        "existem modelos que sao similares entre si",
        "qual modelo e maior e qual e menor",
        "tem alguma anomalia nos modelos",
        "resumo completo do que foi analisado",
    ]
    
    for p in perguntas:
        r = cerebro.gerar(p, 8, p)
        if MCRExpansor._ext:
            expandido = MCRExpansor.responder(p)
            if expandido and expandido != p and len(expandido) > len(p) + 10:
                r = expandido
        safe = r.encode("ascii", errors="replace").decode("ascii")[:300]
        print(f"  [MCR] {p}:")
        for linha in safe.split("\n"):
            print(f"    {linha.strip()}")
        print()


# ═══════════════════════════════════════════════════════════════════
# RELATORIO ESTRUTURADO
# ═══════════════════════════════════════════════════════════════════

def relatorio(resultados: Dict, comparacoes: List[Dict]):
    """Relatorio completo do que foi analisado."""
    print("\n" + "=" * 55)
    print("  RELATORIO DA ANALISE")
    print("=" * 55)
    print()
    
    print(f"  Total de blobs: {len(resultados)}")
    total_gb = sum(r.get("tamanho", 0) for r in resultados.values()) / 1024**3
    print(f"  Tamanho total: {total_gb:.1f}GB")
    print()
    
    for nome, info in sorted(resultados.items()):
        h = info.get("header", {})
        p = info.get("pesos", {})
        tam = info.get("tamanho", 0)
        
        print(f"  [{nome[:30]}]")
        print(f"    Tamanho: {tam/1024/1024:.0f}MB")
        print(f"    Arquitetura: {h.get('general.architecture', '?')}")
        print(f"    Nome: {h.get('general.name', '?')}")
        print(f"    Contexto: {h.get('llama.context_length', '?')} tokens")
        print(f"    Embeddings: {h.get('llama.embedding_length', '?')} dims")
        print(f"    Camadas: {h.get('llama.block_count', '?')}")
        print(f"    Vocabulario: {h.get('llama.vocab_size', '?')} tokens")
        print(f"    Quantizacao: v{h.get('general.quantization_version', '?')}")
        print(f"    GGUF version: {h.get('version', '?')}")
        print(f"    Entropia media: {p.get('entropia_media', '?')}")
        
        if h.get("erro"):
            print(f"    ERRO: {h['erro']}")
        print()
    
    print("  COMPARACOES:")
    print(f"    Total de pares: {len(comparacoes)}")
    print()
    
    for c in comparacoes[:5]:
        relacao = "MESMA ARQUITETURA" if c["arquitetura_a"] == c["arquitetura_b"] else "ARQUIT. DIFERENTE"
        print(f"    {c['a']:20s} vs {c['b']:20s}")
        print(f"      Sim fingerprint: {c['sim_fingerprint']:.3f} | {relacao}")
        print(f"      Tamanhos: {c['tamanho_a']/1024/1024:.0f}MB vs {c['tamanho_b']/1024/1024:.0f}MB")
        print()
    
    # Salva
    with open(CACHE_RESULTADOS, "w", encoding="utf-8") as f:
        json.dump({"resultados": {k[:30]: v for k, v in resultados.items()},
                    "comparacoes": comparacoes,
                    "timestamp": time.time()}, f, indent=2, ensure_ascii=False)
    print(f"  Resultados salvos em: {CACHE_RESULTADOS}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    
    print("=" * 55)
    print("  MCR ANALISADOR DE MODELOS")
    print("  Lendo blobs GGUF, extraindo padroes...")
    print("=" * 55)
    print()
    
    if not os.path.exists(BLOBS_DIR):
        print(f"  Diretorio de blobs nao encontrado: {BLOBS_DIR}")
        return
    
    # Coleta blobs
    blobs = sorted(glob.glob(os.path.join(BLOBS_DIR, "sha256-*")))
    print(f"  Encontrados {len(blobs)} blobs")
    print()
    
    resultados = {}
    t0 = time.time()
    
    for caminho in blobs:
        nome = os.path.basename(caminho)
        tam = os.path.getsize(caminho)
        print(f"  Lendo {nome}: {tam/1024/1024:.0f}MB...", end="", flush=True)
        
        # Header GGUF
        header = ler_header_gguf(caminho)
        
        # Pesos (amostras)
        pesos = amostrar_pesos(caminho)
        
        resultados[nome] = {
            "tamanho": tam,
            "header": header or {"erro": "falha ao ler header"},
            "pesos": pesos,
        }
        
        print(f" {header.get('general.architecture','?') if header and not header.get('erro') else 'ERRO'}")
    
    tempo_leitura = time.time() - t0
    
    print(f"\n  Leitura concluida em {tempo_leitura:.2f}s")
    print()
    
    # Comparacoes
    comparacoes = comparar_modelos(resultados)
    
    # Relatorio
    relatorio(resultados, comparacoes)
    
    # Alimenta no MCR
    cerebro = CerebroAGI()
    alimentar_no_mcr(cerebro, resultados, comparacoes)
    
    # Registra extrator
    MCRExpansor.registrar("modelos", lambda p: [
        {"assinatura": d.get("texto",""), "meta": {"topico": n}}
        for n, d in list(cerebro.topicos.items())[:20]
    ])
    MCRExpansor.registrar_construtor("modelos", lambda ctx, r: r.get("assinatura",""))
    
    print(f"  Alimentado no MCR: {len(cerebro.topicos)} topicos, {cerebro.mk_byte.total} bytes")
    print()
    
    # Pergunta ao MCR
    if "--pergunta" in args or len(args) == 0:
        perguntar(cerebro)
    
    # Chat
    if "--chat" in args:
        # Inicia SuperLoop
        sl = MCRSuperLoop(cerebro)
        t = threading.Thread(target=sl.iniciar_loop, daemon=True)
        t.start()
        chat_loop(cerebro, None)


if __name__ == "__main__":
    main()
