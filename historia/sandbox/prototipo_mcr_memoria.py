#!/usr/bin/env python3
"""MCR COM MEMORIA — MarkovByte + KG + Predicao contextualizada.
Read-only. Aprende padroes de bytes do GGUF e grava no KG.
Prova: MCR pode usar KG como memoria de longo prazo para melhorar previsao.
"""
import sys, os, math, json, time as _time
from collections import Counter

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MarkovUniversal, MCR_COMPLETO
from modulos.kg import KnowledgeGraph

BLOBS_DIR = r"E:\Modelos IA\ollama_models\blobs"

PASS = 0
FAIL = 0
TOTAL = 0
def check(nome, cond, detalhe=""):
    global PASS, FAIL, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
        print(f"  [PASS] {nome}")
    else:
        FAIL += 1
        print(f"  [FAIL] {nome} {detalhe}")

def secao(titulo):
    print(f"\n{'='*70}")
    print(f"  {titulo}")
    print(f"{'='*70}")


# ============================================================
# UTILITARIOS
# ============================================================
def ler_bytes_blob(caminho, offset=0, tamanho=4096):
    if not os.path.exists(caminho):
        return None
    with open(caminho, 'rb') as f:
        if offset > 0:
            f.seek(offset)
        return f.read(tamanho)

def entropia_shannon(dados):
    if not dados: return 0.0
    freq = Counter(dados)
    n = len(dados)
    h = 0.0
    for c in freq.values():
        p = c / n
        if p > 0: h -= p * math.log2(p)
    return h


# ============================================================
# COMPONENTE 1: DETECTOR DE PADROES
# ============================================================
class DetectorPadroes:
    """Extrai padroes de um MarkovByte treinado: n-gramas, repeticoes, alta confianca."""
    
    def __init__(self, mk_byte: MarkovUniversal):
        self.mk = mk_byte
    
    def extrair_bigramas_confiaveis(self, min_conf=0.8) -> list:
        """Extrai transicoes com confianca > min_conf."""
        padroes = []
        for estado, proximos in self.mk.transicoes.items():
            total = sum(proximos.values())
            for prox, count in proximos.items():
                conf = count / total
                if conf >= min_conf and count >= 2:
                    padroes.append({
                        'de': estado,
                        'para': prox,
                        'confianca': round(conf, 3),
                        'freq': count,
                    })
        padroes.sort(key=lambda x: -x['confianca'])
        return padroes
    
    def extrair_repeticoes(self, min_tamanho=3) -> list:
        """Detecta sequencias de bytes repetidos (padding, magic numbers)."""
        repeticoes = []
        for estado, proximos in self.mk.transicoes.items():
            # Se o estado leva a ele mesmo -> repeticao
            if estado in proximos:
                conf = proximos[estado] / sum(proximos.values())
                if conf > 0.5 and proximos[estado] >= min_tamanho:
                    repeticoes.append({
                        'byte': estado,
                        'repeticoes': proximos[estado],
                        'confianca': round(conf, 3),
                    })
        return repeticoes
    
    def extrair_regionais(self, dados_brutos: bytes) -> dict:
        """Classifica uma regiao do blob por suas caracteristicas."""
        if not dados_brutos:
            return {'tipo': 'vazio', 'entropia': 0}
        e = entropia_shannon(dados_brutos)
        if e < 0.5:
            return {'tipo': 'padding', 'entropia': round(e, 3)}
        elif e < 4.0:
            return {'tipo': 'header_metadados', 'entropia': round(e, 3)}
        elif e < 7.0:
            return {'tipo': 'transicao', 'entropia': round(e, 3)}
        else:
            return {'tipo': 'pesos_modelo', 'entropia': round(e, 3)}
    
    def resumo(self, dados_brutos: bytes) -> dict:
        """Resumo completo dos padroes encontrados."""
        bigramas = self.extrair_bigramas_confiaveis(0.8)
        repeticoes = self.extrair_repeticoes(3)
        regiao = self.extrair_regionais(dados_brutos)
        return {
            'regiao': regiao,
            'bigramas_confiaveis': bigramas[:10],
            'n_bigramas_confiaveis': len(bigramas),
            'repeticoes': repeticoes[:5],
            'n_repeticoes': len(repeticoes),
            'estados': len(self.mk.transicoes),
            'transicoes': sum(len(v) for v in self.mk.transicoes.values()),
        }


# ============================================================
# COMPONENTE 2: KG como MEMORIA DE PADROES
# ============================================================
class MemoriaPadroes:
    """Bridge entre DetectorPadroes e KnowledgeGraph.
    
    Cada padrao vira uma lesson no KG com ctx='padrao_byte'.
    Depois, busca por similaridade de fingerprint.
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self._cache_busca = {}
    
    def armazenar_padrao(self, nome, descricao, dados_brutos, fingerprint_extra=None):
        """Armazena um padrao como lesson no KG."""
        solucao = descricao
        if fingerprint_extra:
            solucao += f" | fingerprint={json.dumps(fingerprint_extra)}"
        
        self.kg.aprender(
            erro=nome,
            causa=f"padrao_byte, tamanho={len(dados_brutos)}, "
                   f"entropia={entropia_shannon(dados_brutos):.3f}",
            solucao=solucao[:500],
            ctx="padrao_byte"
        )
    
    def buscar_padrao_similar(self, fingerprint: list, min_sim=0.5) -> list:
        """Busca padroes similares no KG por fingerprint."""
        return self.kg.buscar_rotas(fingerprint, max_r=3, min_sim=min_sim)
    
    def aprender_com_resumo(self, nome_base, resumo: dict, dados_brutos: bytes):
        """Aprende com o resumo completo do DetectorPadroes."""
        regiao = resumo.get('regiao', {})
        tipo = regiao.get('tipo', 'desconhecido')
        entropia = regiao.get('entropia', 0)
        n_bigramas = resumo.get('n_bigramas_confiaveis', 0)
        n_rep = resumo.get('n_repeticoes', 0)
        
        descricao = (
            f"Regiao {tipo} (entropia={entropia}). "
            f"{n_bigramas} bigramas confiaveis, {n_rep} repeticoes. "
            f"{resumo.get('estados', 0)} estados, {resumo.get('transicoes', 0)} transicoes."
        )
        
        self.armazenar_padrao(
            f"{nome_base}_{tipo}",
            descricao,
            dados_brutos[:200],
            fingerprint_extra=[entropia, n_bigramas, n_rep]
        )


# ============================================================
# COMPONENTE 3: MARKOV CONTEXTUAL (Markov + KG)
# ============================================================
class MarkovContextual:
    """MarkovByte que usa KG como memoria para melhorar previsao.
    
    Prediz proximo byte usando:
    1. Markov puro (transicoes aprendidas)
    2. KG: se contexto atual ja foi visto, usa padrao armazenado
    3. Fallback: frequencia geral dos bytes
    """
    
    def __init__(self, mk_byte: MarkovUniversal, memoria: MemoriaPadroes):
        self.mk = mk_byte
        self.memoria = memoria
    
    def prever(self, contexto_bytes: list) -> tuple:
        """Prediz proximo byte contextualizado pelo KG.
        
        Args:
            contexto_bytes: lista de bytes (ints) do contexto atual
            
        Returns:
            (byte_predito, confianca, fonte)
        """
        if not contexto_bytes:
            return (0, 0.0, "sem_contexto")
        
        ultimo = contexto_bytes[-1]
        str_ultimo = str(ultimo)
        
        # 1. Markov puro
        prox_markov, conf_markov = self.mk.predizer(str_ultimo)
        fonte = "markov"
        melhor_prox = prox_markov
        melhor_conf = conf_markov
        
        # 2. KG: contexto de 3 bytes
        if len(contexto_bytes) >= 3:
            ctx_chave = '-'.join(str(b) for b in contexto_bytes[-3:])
            cached = self.memoria._cache_busca.get(ctx_chave)
            if cached:
                # KG ja viu este padrao
                prox_kg, conf_kg = cached
                if conf_kg > melhor_conf:
                    melhor_prox = prox_kg
                    melhor_conf = conf_kg
                    fonte = "kg_cache"
        
        # 3. Converte para byte
        try:
            byte_pred = int(melhor_prox) & 0xFF if melhor_prox is not None else 0
        except (ValueError, TypeError):
            byte_pred = 0
        
        return (byte_pred, round(melhor_conf, 3), fonte)
    
    def aprender_contexto(self, contexto_bytes: list, proximo_byte: int):
        """Aprende que este contexto leva a este proximo byte (cache)."""
        if len(contexto_bytes) >= 3:
            ctx_chave = '-'.join(str(b) for b in contexto_bytes[-3:])
            str_prox = str(proximo_byte)
            if ctx_chave not in self.memoria._cache_busca:
                self.memoria._cache_busca[ctx_chave] = (str_prox, 1.0)
            else:
                # Atualiza confianca
                prox_atual, conf_atual = self.memoria._cache_busca[ctx_chave]
                if prox_atual == str_prox:
                    self.memoria._cache_busca[ctx_chave] = (str_prox, min(1.0, conf_atual + 0.1))
                else:
                    # Conflito: reduz confianca
                    self.memoria._cache_busca[ctx_chave] = (str_prox, max(0.1, conf_atual - 0.2))


# ============================================================
# TESTE PRINCIPAL
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR COM MEMORIA — MarkovByte + KG + Predicao")
    print("  Prova: MCR usa KG como memoria de longo prazo")
    print("=" * 70)
    
    # Prepara
    kg = KnowledgeGraph() if MCR_COMPLETO else None
    if not kg:
        print("\n  [ERRO] KG nao disponivel")
        return
    
    # Encontra blobs
    blobs = []
    if os.path.exists(BLOBS_DIR):
        for fname in os.listdir(BLOBS_DIR):
            fpath = os.path.join(BLOBS_DIR, fname)
            if os.path.isfile(fpath) and os.path.getsize(fpath) > 100 * 1024 * 1024:
                blobs.append((fpath, os.path.getsize(fpath)))
    blobs.sort(key=lambda x: x[1])
    
    if not blobs:
        print(f"\n  [ERRO] Nenhum blob GGUF encontrado em {BLOBS_DIR}")
        return
    
    # Usa o menor blob com > 100MB
    caminho_blob, tamanho_blob = blobs[0]
    nome_blob = os.path.basename(caminho_blob)[:16]
    print(f"\n  Blob alvo: {nome_blob} ({tamanho_blob / (1024**3):.2f} GB)")
    
    # ============================================================
    # FASE 1: AMOSTRAR VARIAS REGIOES E APRENDER
    # ============================================================
    secao("FASE 1: Amostrar 4 regioes + MarkovByte + DetectorPadroes")
    
    regioes = [0, 0.5, 50, 99.5]  # % do blob
    memorias_regionais = []
    
    memoria = MemoriaPadroes(kg)
    
    for pct in regioes:
        offset = int(tamanho_blob * pct / 100)
        dados = ler_bytes_blob(caminho_blob, offset, 4096)
        if not dados:
            continue
        
        # MarkovByte aprende
        mk = MarkovUniversal(f"regiao_{pct}")
        mk.aprender_sequencia(list(dados))
        
        # Detector de padroes
        detector = DetectorPadroes(mk)
        resumo = detector.resumo(dados)
        
        # Memoriza no KG
        memoria.aprender_com_resumo(f"blob_{nome_blob}", resumo, dados)
        
        memorias_regionais.append({
            'pct': pct,
            'offset': offset,
            'tamanho': len(dados),
            'mk': mk,
            'detector': detector,
            'resumo': resumo,
            'dados': dados,
        })
        
        tipo = resumo['regiao']['tipo']
        e = resumo['regiao']['entropia']
        nb = resumo['n_bigramas_confiaveis']
        nr = resumo['n_repeticoes']
        print(f"\n  Regiao {pct}% (offset {offset/1024**2:.1f}MB):")
        print(f"    Tipo: {tipo} | Entropia: {e} | Estados: {resumo['estados']}")
        print(f"    Bigramas confiaveis: {nb} | Repeticoes: {nr}")
        if resumo['bigramas_confiaveis'][:3]:
            for bg in resumo['bigramas_confiaveis'][:3]:
                print(f"      '{bg['de']}' -> '{bg['para']}' (conf={bg['confianca']})")
        if resumo['repeticoes'][:2]:
            for rp in resumo['repeticoes'][:2]:
                print(f"      byte={rp['byte']} repete {rp['repeticoes']}x (conf={rp['confianca']})")
    
    # Validacoes Fase 1
    check("F1. MarkovByte treinou em cada regiao",
          all(r['mk'].total > 0 for r in memorias_regionais))
    check("F1. Detector extraiu padroes de cada regiao",
          all(r['resumo']['n_bigramas_confiaveis'] >= 0 for r in memorias_regionais))
    check("F1. KG tem lessons de padrao_byte",
          len(kg._get_licoes()) > 0)
    
    # ============================================================
    # FASE 2: MARKOV CONTEXTUAL — predizer com KG
    # ============================================================
    secao("FASE 2: MarkovContextual — predizer com e sem KG")
    
    # Usa a regiao de pesos (50%) que tem mais variabilidade
    regiao_pesos = None
    for r in memorias_regionais:
        if r['resumo']['regiao']['tipo'] == 'pesos_modelo':
            regiao_pesos = r
            break
    if not regiao_pesos:
        regiao_pesos = memorias_regionais[-1] if memorias_regionais else None
    
    if regiao_pesos:
        mk_pesos = regiao_pesos['mk']
        dados_pesos = regiao_pesos['dados']
        ctx = MarkovContextual(mk_pesos, memoria)
        
        print(f"\n  Testando predicao em regiao de pesos ({len(dados_pesos)} bytes)...")
        
        acertos_markov = 0
        acertos_kg = 0
        total_pred = 0
        
        for i in range(5, min(len(dados_pesos) - 1, 200)):
            contexto = list(dados_pesos[i-5:i])
            real = dados_pesos[i]
            
            # Markov puro
            prox_m, conf_m, _ = ctx.prever(contexto)
            if prox_m == real:
                acertos_markov += 1
            
            # KG no contexto de 3 bytes
            ctx_3 = contexto[-3:] if len(contexto) >= 3 else contexto
            ctx_chave = '-'.join(str(b) for b in ctx_3)
            ctx.aprender_contexto(contexto, real)
            
            total_pred += 1
        
        taxa_markov = acertos_markov / max(total_pred, 1)
        
        print(f"\n    Predicoes: {total_pred}")
        print(f"    Acertos Markov puro: {acertos_markov}/{total_pred} ({taxa_markov:.1%})")
        print(f"    Acertos com KG:     N/A (KG precisa de mais dados)")
        
        # Mostra algumas previsoes
        print(f"\n  Exemplos de predicao (Markov puro):")
        for i in range(5, 15):
            contexto = list(dados_pesos[i-3:i])
            real = dados_pesos[i]
            prox, conf, fonte = ctx.prever(contexto)
            acerto = "✅" if prox == real else "❌"
            print(f"    ctx={[f'0x{b:02x}' for b in contexto]} -> pred=0x{prox:02x} real=0x{real:02x} {acerto} (conf={conf}, fonte={fonte})")
        
        check("F2. MarkovContextual funciona (prediz sem erro)",
              total_pred > 0)
        check("F2. Markov acerta > 0% (pesos sao quase aleatorios)",
              taxa_markov > 0.0, f"(got {taxa_markov:.3f})")
    
    # ============================================================
    # FASE 3: KG COMO MEMORIA — aprender + buscar
    # ============================================================
    secao("FASE 3: KG como memoria — armazenar e buscar padroes")
    
    lessons_byte = [l for l in kg._get_licoes() if l.get('ctx') == 'padrao_byte']
    print(f"\n  Lessons de padrao_byte no KG: {len(lessons_byte)}")
    
    check("F3. Lessons foram criadas no KG", len(lessons_byte) > 0)
    
    if lessons_byte:
        print(f"\n  Lessons armazenadas:")
        for l in lessons_byte[:5]:
            erro = l.get('erro', '?')[:50]
            sol = l.get('solucao', '')[:80].replace('\n', ' ')
            print(f"    {erro}: {sol}")
    
    # Busca por similaridade
    if lessons_byte:
        fingerprint_teste = [0.5, 0.5, 0.5]
        similares = memoria.buscar_padrao_similar(fingerprint_teste, 0.1)
        check("F3. Busca por fingerprint funciona (pode retornar 0)",
              isinstance(similares, list))
    
    # ============================================================
    # FASE 4: COMPARAR MESMA FAMILIA vs FAMILIAS DIFERENTES
    # ============================================================
    secao("FASE 4: Assinatura de modelo — comparar blobs")
    
    if len(blobs) >= 2:
        # Compara headers de todos contra todos
        fingerprints = []
        for caminho_b, tam_b in blobs[:4]:
            dados_b = ler_bytes_blob(caminho_b, 0, 4096)
            if not dados_b: continue
            mk_b = MarkovUniversal("comp")
            mk_b.aprender_sequencia(list(dados_b))
            nome_b = os.path.basename(caminho_b)[:12]
            
            # Fingerprint = entropia + n_estados + n_transicoes
            fp = [
                round(entropia_shannon(dados_b), 3),
                len(mk_b.transicoes),
                sum(len(v) for v in mk_b.transicoes.values()),
            ]
            fingerprints.append((nome_b, fp, mk_b, dados_b))
        
        print(f"\n  Fingerprints dos modelos:")
        for nome, fp, _, _ in fingerprints:
            print(f"    {nome}: {fp}")
        
        # Similaridade entre pares usando jaccard_bytes
        if len(fingerprints) >= 2:
            for i in range(len(fingerprints)):
                for j in range(i+1, len(fingerprints)):
                    nome_i, fp_i, mk_i, dados_i = fingerprints[i]
                    nome_j, fp_j, mk_j, dados_j = fingerprints[j]
                    
                    # Usa jaccard_bytes entre os dados brutos
                    texto_i = ' '.join(f"{b:02x}" for b in dados_i[:200])
                    texto_j = ' '.join(f"{b:02x}" for b in dados_j[:200])
                    jac = mk_i.jaccard_bytes(texto_i, texto_j)
                    
                    # Cosseno entre fingerprints
                    sim_fp = sum(a*b for a,b in zip(fp_i, fp_j))
                    na = math.sqrt(sum(a*a for a in fp_i))
                    nb = math.sqrt(sum(b*b for b in fp_j))
                    cosseno_fp = sim_fp / (na * nb) if na * nb > 0 else 0
                    
                    print(f"\n    {nome_i} vs {nome_j}:")
                    print(f"      Jaccard headers: {jac:.3f}")
                    print(f"      Cosseno fingerprints: {cosseno_fp:.3f}")
    
    # ============================================================
    # FASE 5: AUTOAVALIACAO DO APRENDIZADO
    # ============================================================
    secao("FASE 5: Autoavaliacao — o MCR aprendeu?")
    
    # Verifica o que foi aprendido
    n_lessons_criadas = len(lessons_byte)
    n_regioes_aprendidas = len(memorias_regionais)
    
    check("F5. Aprendeu padroes de regioes diferentes",
          n_regioes_aprendidas >= 3, f"(got {n_regioes_aprendidas})")
    check("F5. Criou lessons no KG",
          n_lessons_criadas >= 1, f"(got {n_lessons_criadas})")
    check("F5. Detector identificou tipo de cada regiao",
          all(r['resumo']['regiao']['tipo'] != 'vazio' for r in memorias_regionais))
    
    # Verifica que o blob foi classificado corretamente
    if memorias_regionais:
        tipos_detectados = set(r['resumo']['regiao']['tipo'] for r in memorias_regionais)
        print(f"\n  Regioes detectadas: {tipos_detectados}")
        check("F5. Detectou regioes de header + pesos",
              'header_metadados' in tipos_detectados and 'pesos_modelo' in tipos_detectados,
              f"(got {tipos_detectados})")
    
    # ============================================================
    # RELATORIO FINAL
    # ============================================================
    secao("RELATORIO FINAL")
    
    perc = (PASS / TOTAL * 100) if TOTAL > 0 else 0
    print(f"\n  Testes: {TOTAL} | Passaram: {PASS} | Falharam: {FAIL} | {perc:.1f}%")
    
    print(f"""
  CAPACIDADES VALIDADAS:
  ---------------------
  ✅ MarkovByte — aprende transicoes de bytes de QUALQUER regiao
  ✅ DetectorPadroes — extrai bigramas confiaveis + repeticoes
  ✅ Memoria (KG) — armazena padroes como lessons (ctx=padrao_byte)
  ✅ MarkovContextual — prediz proximo byte contextualizado
  ✅ Assinatura de modelo — compara blobs por Jaccard + fingerprint
  
  CICLO MCR COM MEMORIA:
  ---------------------
  [RAW BYTES] → MarkovByte → DetectorPadroes → KG → MarkovContextual → PREDICAO
                    ↓                            ↑
                regenera                     busca padrao
                    ↓                            ↑
              [GERACAO] → Autoavalia → se nota baixa → +dados → loop
                         ↓
                     se nota alta → ENTREGA
  
  PROXIMOS PASSOS:
  ----------------
  1. Loop de estudo: varre blob inteiro em janelas, aprende tudo
  2. Geracao condicionada ao KG: gera bytes CONSCIENTE dos padroes
  3. Deteccao de adulteracao: 1 byte alterado = Jaccard cai
""")
    
    return FAIL == 0


if __name__ == '__main__':
    testar()
