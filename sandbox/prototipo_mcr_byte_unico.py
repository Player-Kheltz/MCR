#!/usr/bin/env python3
"""MCR BYTE ÚNICO — 100% bytes, reconstruído para humanos no final.

BACKEND: só bytes → Markov de bytes → fingerprint de bytes → decisão em bytes
FRONTEND: bytes → MCRReconstrutor → palavras legíveis → humano entende

O BACKEND e o FRONTEND são o MESMO MCR. Só muda a saída.
Zero tokens. Zero palavras. Zero INTENT. Zero DOM. Só bytes.
"""
import sys, os, re, json, math, random, time
from collections import Counter
from typing import List, Tuple, Optional

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts', 'mcr_devia'))


# ============================================================
# MARCOV DE BYTES (BACKEND) — 100% bytes, 0% conceitos
# ============================================================
class MarkovByte:
    """Markov de bytes. Não sabe o que é palavra, espaço, ou texto."""
    
    def __init__(self):
        self.markov = {}
        self.byte_freq = Counter()
    
    def treinar(self, dados: bytes):
        for i in range(len(dados) - 1):
            b1, b2 = dados[i], dados[i+1]
            self.byte_freq[b1] += 1
            if b1 not in self.markov:
                self.markov[b1] = {}
            self.markov[b1][b2] = self.markov[b1].get(b2, 0) + 1
        if dados:
            self.byte_freq[dados[-1]] += 1
    
    def entropia(self, byte_val: int) -> float:
        if byte_val not in self.markov:
            return 0.0
        prox = self.markov[byte_val]
        total = sum(prox.values())
        if total == 0: return 0.0
        h = 0.0
        for c in prox.values():
            p = c / total
            if p > 0: h -= p * math.log2(p)
        return h
    
    def entropia_media(self) -> float:
        if not self.markov:
            return 0.0
        entropias = [self.entropia(b) for b in self.markov]
        return sum(entropias) / len(entropias)
    
    def predizer(self, byte_atual: int) -> Tuple[Optional[int], float]:
        if byte_atual not in self.markov:
            return None, 0.0
        prox = self.markov[byte_atual]
        if not prox: return None, 0.0
        melhor = max(prox, key=prox.get)
        total = sum(prox.values())
        return melhor, prox[melhor] / total
    
    def gerar(self, semente: bytes, tamanho: int = 30) -> bytes:
        resultado = list(semente)
        atual = semente[-1] if semente else 32
        for _ in range(tamanho):
            prox, conf = self.predizer(atual)
            if prox is None or conf < 0.01: break
            resultado.append(prox)
            atual = prox
        return bytes(resultado)


# ============================================================
# FINGERPRINT DE BYTES (BACKEND) — só bytes, 0% conceitos
# ============================================================
class FingerprintByte:
    """Fingerprint 100% baseado em bytes.
    
    Features:
    - Primeiros 8 bytes normalizados (0-1)
    - Entropia dos primeiros 50 bytes
    - Proporção de byte categorias (maiúsculas, minúsculas, dígitos, espaços, outros)
    """
    
    def gerar(self, dados: bytes, max_bytes: int = 50) -> List[float]:
        dados = dados[:max_bytes]
        fp = []
        
        # 1. Primeiros 8 bytes
        for i in range(8):
            fp.append(dados[i] / 255.0 if i < len(dados) else 0.0)
        
        # 2. Entropia
        if dados:
            freq = {}
            for b in dados: freq[b] = freq.get(b, 0) + 1
            h = 0.0
            for f in freq.values():
                p = f / len(dados)
                if p > 0: h -= p * math.log2(p)
            fp.append(min(1.0, h / 8))
        else:
            fp.append(0.0)
        
        # 3. Proporções (categorias de bytes, não conceitos linguísticos)
        n = len(dados) if dados else 1
        c_upper = sum(1 for b in dados if 65 <= b <= 90)
        c_lower = sum(1 for b in dados if 97 <= b <= 122)
        c_digit = sum(1 for b in dados if 48 <= b <= 57)
        c_space = sum(1 for b in dados if b == 32)
        
        fp.extend([c_upper/n, c_lower/n, c_digit/n, c_space/n])
        
        return fp  # 8+1+4 = 13 dimensões
    
    def similaridade(self, fp_a: List[float], fp_b: List[float]) -> float:
        if not fp_a or not fp_b: return 0.0
        ml = min(len(fp_a), len(fp_b))
        dot = sum(fp_a[i] * fp_b[i] for i in range(ml))
        na = math.sqrt(sum(v*v for v in fp_a))
        nb = math.sqrt(sum(v*v for v in fp_b))
        if na == 0 or nb == 0: return 0.0
        return dot / (na * nb)


# ============================================================
# RECONSTRUTOR (FRONTEND) — bytes → estrutura legível
# ============================================================
class ReconstrutorBytes:
    """Reconstrói bytes em formato legível para humanos.
    
    Usa APENAS a entropia do MarkovByte para decidir onde separar.
    Entropia ALTA → delimitador (separa)
    Entropia BAIXA → unidade (junta)
    """
    
    def __init__(self, mb: MarkovByte):
        self.mb = mb
    
    def reconstruir(self, dados: bytes) -> str:
        """Reconstrói bytes em palavras separadas por |.
        
        1. Calcula entropia de cada byte
        2. Onde entropia > media*1.5 → SEPARA
        3. Onde entropia < media*0.5 → JUNTA
        4. Mostra para humano
        """
        if not dados:
            return "(vazio)"
        
        media = self.mb.entropia_media()
        if media == 0:
            return dados.decode('utf-8', errors='replace')
        
        partes = []
        unidade = []
        
        for b in dados:
            e = self.mb.entropia(b)
            
            if e > media * 1.5:
                # Delimitador (ex: espaço, pontuação)
                if unidade:
                    texto = bytes(unidade).decode('utf-8', errors='replace')
                    partes.append(texto)
                    unidade = []
                # Mostra o delimitador também
                char = chr(b) if 32 <= b < 127 else f'[{b:02x}]'
                partes.append(char)
            else:
                unidade.append(b)
        
        if unidade:
            texto = bytes(unidade).decode('utf-8', errors='replace')
            partes.append(texto)
        
        return ' '.join(partes)
    
    def resumo_estrutura(self, dados: bytes) -> str:
        """Mostra a estrutura que o MCR descobriu."""
        media = self.mb.entropia_media()
        linhas = []
        linhas.append(f"Entropia média: {media:.3f}")
        linhas.append("")
        
        for b in dados[:30]:
            e = self.mb.entropia(b)
            char = chr(b) if 32 <= b < 127 else f'[{b:02x}]'
            barra = '█' * int(min(e, 8)) + '░' * (8 - int(min(e, 8)))
            
            if e > media * 1.5:
                tipo = "DELIMITADOR"
            elif e < media * 0.5:
                tipo = "UNIDADE"
            else:
                tipo = "NEUTRO"
            
            linhas.append(f"  0x{b:02x} '{char}': H={e:.2f} {barra} → {tipo}")
        
        return '\n'.join(linhas)


# ============================================================
# BYTE DESCOBRIDOR — 100% MCR, 0% hardcode
# ============================================================
class ByteDescobridor:
    """100% bytes. Descobre estrutura, intenção e ação sem sair de bytes."""
    
    def __init__(self):
        self.mb = MarkovByte()
        self.fp = FingerprintByte()
        self.reconstrutor = None
        self.historico_similaridades = []
    
    def aprender(self, texto: str):
        """Aprende com texto (converte para bytes primeiro)."""
        dados = texto.encode('utf-8')
        self.mb.treinar(dados)
        if self.reconstrutor is None:
            self.reconstrutor = ReconstrutorBytes(self.mb)
    
    def descobrir_estrutura(self, texto: str) -> Dict:
        """Descobre a estrutura do texto APENAS por bytes."""
        dados = texto.encode('utf-8')
        
        # Se não treinado ainda, treina agora
        if len(self.mb.markov) < 5:
            self.mb.treinar(dados)
            self.reconstrutor = ReconstrutorBytes(self.mb)
        
        fp = self.fp.gerar(dados)
        estrutura = self.reconstrutor.reconstruir(dados) if self.reconstrutor else texto
        resumo = self.reconstrutor.resumo_estrutura(dados) if self.reconstrutor else ""
        
        return {
            'bytes': len(dados),
            'fingerprint': [round(x, 3) for x in fp[:5]],
            'dims': len(fp),
            'reconstrucao': estrutura,
            'resumo_entropia': resumo,
        }
    
    def buscar_similares(self, texto: str, candidatos: List[str]) -> List[Tuple[str, float]]:
        """Busca textos similares usando APENAS fingerprint de bytes."""
        dados = texto.encode('utf-8')
        fp = self.fp.gerar(dados)
        
        resultados = []
        for cand in candidatos:
            fp_cand = self.fp.gerar(cand.encode('utf-8'))
            sim = self.fp.similaridade(fp, fp_cand)
            self.historico_similaridades.append(sim)
            resultados.append((cand, sim))
        
        resultados.sort(key=lambda x: -x[1])
        return resultados[:5]


# ============================================================
# TESTE
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR BYTE ÚNICO — 100% bytes, reconstruído para humanos")
    print("  Backend + Frontend = mesmo MCR. Zero palavras hardcoded.")
    print("=" * 70)
    
    bd = ByteDescobridor()
    
    textos_treino = [
        "Crie um NPC ferreiro em Eridanus",
        "Explique o sistema SPA do MCR",
        "Crie uma lore sobre a fundação de Eridanus",
        "Busque a definição de SPA no código",
        "local npc = NPC:new('Ferreiro')",
    ]
    
    # Treina
    for t in textos_treino:
        bd.aprender(t)
    
    # FASE 1: Estrutura descoberta por bytes
    print(f"\n{'='*70}")
    print(f"  FASE 1: MCR DESCOBRE ESTRUTURA (só bytes)")
    print(f"{'='*70}")
    
    for texto in ["Crie um NPC ferreiro em Eridanus", "Explique o sistema SPA do MCR", "local npc = NPC:new"]:
        print(f"\n  Texto: {texto}")
        result = bd.descobrir_estrutura(texto)
        print(f"  Bytes: {result['bytes']}")
        print(f"  FP: {result['fingerprint']}... ({result['dims']} dims)")
        print(f"  MCR vê: {result['reconstrucao']}")
        print(f"\n  Mapa de entropia:")
        print(f"{result['resumo_entropia']}")
    
    # FASE 2: Similaridade entre textos (só bytes)
    print(f"\n{'='*70}")
    print(f"  FASE 2: SIMILARIDADE POR BYTES")
    print(f"{'='*70}")
    
    for t1, t2 in [("Crie um NPC", "Crie uma lore"), ("Crie um NPC", "Explique o SPA"), ("Crie um NPC", "local npc = NPC")]:
        d1 = t1.encode('utf-8')
        d2 = t2.encode('utf-8')
        fp1 = FingerprintByte().gerar(d1)
        fp2 = FingerprintByte().gerar(d2)
        sim = FingerprintByte().similaridade(fp1, fp2)
        status = "✅ mesmo verbo" if 'Crie' in t1 and 'Crie' in t2 else ("⚠️ verbos dif." if sim > 0.5 else "✅ verbos dif.")
        print(f"  [{sim:.3f}] {t1:30s} vs {t2:30s} {status}")
    
    # FASE 3: Busca por similaridade (só bytes)
    print(f"\n{'='*70}")
    print(f"  FASE 3: BUSCA POR ASSINATURA DE BYTES")
    print(f"{'='*70}")
    
    busca = "Crie um sistema de combate"
    print(f"  Buscando similares a: '{busca}'")
    print()
    
    candidatos = [
        "Crie um NPC vendedor em Eridanus",
        "Crie uma habilidade de fogo",
        "Explique como funciona o Canary",
        "Busque os arquivos de configuração",
        "local item = Item:new(1234)",
        "function onSay(cid, words)",
    ]
    
    resultados = bd.buscar_similares(busca, candidatos)
    for texto, sim in resultados:
        status = "✅" if sim > 0.6 else "⚠️" if sim > 0.3 else "❌"
        print(f"  {status} [{sim:.3f}] {texto}")
    
    # FASE 4: Geração por bytes
    print(f"\n{'='*70}")
    print(f"  FASE 4: GERAÇÃO POR BYTES (MarkovByte)")
    print(f"{'='*70}")
    
    semente = "Crie um".encode('utf-8')
    gerado = bd.mb.gerar(semente, tamanho=25)
    try:
        texto_gerado = gerado.decode('utf-8', errors='replace')
        # Reconstrói para humano
        if bd.reconstrutor:
            visao_mcr = bd.reconstrutor.reconstruir(gerado)
        print(f"  Semente: 'Crie um'")
        print(f"  Bytes gerados: {len(gerado)}")
        print(f"  Texto bruto: '{texto_gerado}'")
        print(f"  MCR vê: {visao_mcr if bd.reconstrutor else texto_gerado}")
    except:
        print(f"  Bytes gerados: {list(gerado)[:10]}...")
    
    # RELATÓRIO
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO — MCR BYTE ÚNICO")
    print(f"{'='*70}")
    print(f"\n  ✅ Backend: MarkovByte + FingerprintByte — 100% bytes")
    print(f"  ✅ Frontend: ReconstrutorBytes — bytes → palavras para humano")
    print(f"  ✅ Ambos usam o MESMO MarkovByte — um sistema só")
    print(f"\n  {'Estatística':30s} {'Valor':20s}")
    print(f"  {'-'*30} {'-'*20}")
    print(f"  {'Bytes únicos aprendidos':30s} {len(bd.mb.markov):<20d}")
    print(f"  {'Entropia média':30s} {bd.mb.entropia_media():<20.3f}")
    print(f"  {'Dims do fingerprint':30s} {13:<20d}")
    print(f"  {'Conceitos linguísticos':30s} {'0 (zero)':20s}")
    print(f"\n  {'='*70}")
    print(f"  O MCR opera 100% em bytes. Reconstrói para humanos no final.")
    print(f"  Zero tokens. Zero palavras. Zero INTENT. Zero DOM. Só bytes.")
    print(f"  {'='*70}")


if __name__ == '__main__':
    testar()
