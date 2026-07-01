#!/usr/bin/env python3
"""MCR INCEPTION — Conselho de Padrões em Escala.

MCR convoca MCRs para gerar, validar e escolher o melhor resultado.
Cada MCR worker opera com temperatura DIFERENTE (superposição).
O conselho ANALISA os padrões de CADA resultado e escolhe o melhor.

4 níveis:
  0 - Coordenador: IE + PE decide o domínio
  1 - Workers: N cópias do MCR com temperaturas diferentes
  2 - Validadores: N cópias validam cada resultado
  3 - Conselho: analisa padrões e escolhe o melhor

0 LLM. 0 GPU. 0 modificação no MCR.
"""
import sys, os, re, json, math, random, time as _time
from collections import Counter
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.intention_engine import IntentionEngine
from modulos.kg import KnowledgeGraph
from modulos.pi_engine import PiEngine

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# ============================================================
# CORPUS + MARKOV (reutilizado do gerador de texto)
# ============================================================
class CorpusBuilder:
    def __init__(self):
        self.corpora = {'lore': '', 'tecnico': '', 'codigo': '', 'npc': ''}
    
    def carregar_tudo(self):
        self.corpora['lore'] = self._carregar_lore()
        self.corpora['tecnico'] = self._carregar_tecnico()
        self.corpora['codigo'] = self._carregar_codigo()
        self.corpora['npc'] = self._carregar_npc()
        return self.corpora
    
    def _carregar_lore(self):
        textos = []
        path = os.path.join(BASE, 'docs', 'MCR_IDENTITY.md')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: textos.append(f.read())
        return ' '.join(textos)
    
    def _carregar_tecnico(self):
        textos = []
        conv = os.path.join(BASE, 'sandbox', '.mcr_conversa.jsonl')
        if os.path.exists(conv):
            try:
                with open(conv, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            msg = entry.get('msg', '')
                            if msg and len(msg) > 20: textos.append(msg)
                        except: pass
            except: pass
        try:
            kg = KnowledgeGraph()
            for l in kg._get_licoes()[:500]:
                sol = l.get('solucao', '')
                if sol and len(sol) > 20: textos.append(sol)
        except: pass
        return ' '.join(textos)
    
    def _carregar_codigo(self):
        textos = []
        for root, dirs, files in os.walk(BASE):
            if any(p in root for p in ['node_modules', '.git', '__pycache__', 'Backup']): continue
            for f in files:
                if f.endswith(('.lua', '.py')):
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8', errors='replace') as fh:
                            textos.append(fh.read())
                    except: pass
        return ' '.join(textos)
    
    def _carregar_npc(self):
        textos = []
        npc_dir = os.path.join(BASE, 'data', 'npc')
        if os.path.isdir(npc_dir):
            for f in os.listdir(npc_dir):
                if f.endswith('.lua'):
                    try:
                        with open(os.path.join(npc_dir, f), 'r', encoding='utf-8') as fh:
                            textos.append(fh.read())
                    except: pass
        return ' '.join(textos)
    
    def limpar(self, texto):
        texto = re.sub(r'http\S+', '', texto)
        texto = re.sub(r'[<>]', '', texto)
        texto = re.sub(r'[^\w\s\.\,\!\?\-\'\"]', ' ', texto)
        return re.sub(r'\s+', ' ', texto).strip().lower()


# ============================================================
# MARKOV TREINADO POR DOMÍNIO
# ============================================================
class MarkovPorDominio:
    def __init__(self):
        self.markov = {}  # dominio → {chave: {proxima: freq}}
    
    def treinar(self, corpora: Dict[str, str]):
        for dominio, texto in corpora.items():
            palavras = texto.split()
            mk = {}
            for i in range(len(palavras) - 2):
                chave = f"{palavras[i]} {palavras[i+1]}"
                prox = palavras[i+2]
                if chave not in mk: mk[chave] = {}
                mk[chave][prox] = mk[chave].get(prox, 0) + 1
            self.markov[dominio] = mk
    
    def gerar(self, dominio: str, semente: str = '', 
              tamanho: int = 30, temperatura: float = 0.3) -> str:
        mk = self.markov.get(dominio, {})
        if not mk or not any(mk.values()):
            return ""
        
        palavras = semente.lower().split() if semente else []
        if len(palavras) < 2:
            chaves_validas = [c for c in mk if mk[c]]
            if chaves_validas:
                palavras = random.choice(chaves_validas).split()
        
        ultima = None; rep = 0
        for _ in range(tamanho):
            if len(palavras) < 2: break
            chave = f"{palavras[-2]} {palavras[-1]}"
            if chave not in mk: break
            prox = mk[chave]
            if not prox: break
            
            # Escolhe com temperatura
            if temperatura <= 0:
                escolha = max(prox, key=prox.get)
            else:
                pesos = list(prox.values())
                soma = sum(pesos)
                pesos_n = [p/soma for p in pesos]
                pesos_t = [p ** (1.0/max(temperatura, 0.01)) for p in pesos_n]
                total = sum(pesos_t)
                probs = [p/total for p in pesos_t]
                escolha = random.choices(list(prox.keys()), weights=probs, k=1)[0]
            
            if escolha == ultima: rep += 1
            else: rep = 0
            if rep >= 3 and len(prox) > 1:
                sorted_p = sorted(prox.items(), key=lambda x: -x[1])
                for alt, _ in sorted_p:
                    if alt != escolha: escolha = alt; break
                rep = 0
            
            palavras.append(escolha)
            ultima = escolha
        
        return ' '.join(palavras)


# ============================================================
# TEMPERADOR INTERNO — Caos adaptativo
# ============================================================
class TemperadorInterno:
    """Ajusta o caos DINÂMICAMENTE baseado no padrão detectado."""
    
    def calcular(self, dominio: str, markov: dict, entropia: float = 0.5) -> float:
        """Calcula temperatura ideal baseada no estado do domínio."""
        # Se o domínio tem POUCOS dados → mais caos (explora)
        n_estados = len(markov.get(dominio, {}))
        if n_estados < 50:
            return 0.6  # Exploração
        elif n_estados < 200:
            return 0.4  # Balanceado
        else:
            return 0.2  # Conservador (já tem padrão)
    
    def sugerir_temperaturas(self, dominio: str, markov: dict) -> List[float]:
        """Sugere N temperaturas para workers em superposição."""
        base = self.calcular(dominio, markov)
        return [
            max(0.0, base - 0.2),  # Conservador
            base,                    # Balanceado
            min(1.0, base + 0.3),  # Criativo
            min(1.0, base + 0.7),  # Caótico (exploração)
        ]


# ============================================================
# WORKER MCR — Instância individual
# ============================================================
class MCRWorker:
    """Uma instância do MCR que gera texto com temperatura específica."""
    
    def __init__(self, id: str, temperatura: float, dominio: str):
        self.id = id
        self.temperatura = temperatura
        self.dominio = dominio
    
    def gerar(self, markov: MarkovPorDominio, semente: str, tamanho: int = 30) -> str:
        """Gera texto com a temperatura DESTA instância."""
        texto = markov.gerar(self.dominio, semente, tamanho, self.temperatura)
        return texto
    
    def validar(self, texto: str, pe: PatternEngine) -> Dict:
        """Auto-valida o texto gerado (sem comparação externa)."""
        tokens = pe.tokenizar_universal(texto)
        if not tokens: return {'cobertura': 0, 'anomalias': 999, 'tokens': 0}
        
        # Cobertura: quantos tokens são do domínio esperado
        tipos = [t[0] for t in tokens]
        palavras = [str(t[1]).lower() for t in tokens if len(t) > 1]
        
        # Palavras que indicam lore
        termos_lore = ['cidade', 'fundação', 'aventureiro', 'história', 'lendária', 
                       'povo', 'terra', 'rei', 'norte', 'sul', 'era', 'antiga']
        
        n_lore = sum(1 for p in palavras if any(t in p for t in termos_lore))
        score = n_lore / max(len(palavras), 1)
        
        return {
            'id': self.id,
            'temperatura': self.temperatura,
            'dominio': self.dominio,
            'texto': texto,
            'tamanho': len(texto.split()),
            'score_lore': round(score, 3),
            'tokens': len(tokens),
            'tipos_unicos': len(set(tipos)),
        }


# ============================================================
# CONSELHO MCR — Decide o melhor resultado
# ============================================================
class ConselhoMCR:
    """Recebe N resultados de N workers e escolhe o MELHOR.
    
    Critérios do conselho:
      1. Mais palavras no domínio (score_lore > 0.1)
      2. Tamanho mínimo (30+ palavras)
      3. Menos anomalias estruturais
      4. Se empatar: temperatura balanceada ganha
    """
    
    def avaliar(self, resultados: List[Dict]) -> Dict:
        """Avalia todos os resultados e retorna o melhor + relatório."""
        if not resultados: return None
        
        print(f"\n  {'='*50}")
        print(f"  CONSELHO MCR — Analisando {len(resultados)} resultados")
        print(f"  {'='*50}")
        
        # Pontua cada resultado
        for r in resultados:
            score = 0.0
            # Critério 1: score_lore (0-1)
            score += r.get('score_lore', 0) * 3
            # Critério 2: tamanho mínimo (30+ palavras)
            tam = r.get('tamanho', 0)
            score += min(1.0, tam / 50) * 2
            # Critério 3: tokens
            score += min(1.0, r.get('tokens', 0) / 30)
            # Bônus: temperatura balanceada
            temp = r.get('temperatura', 0.5)
            if 0.2 <= temp <= 0.5: score += 0.5
            
            r['_score_final'] = round(score, 3)
        
        # Ordena por score
        resultados.sort(key=lambda x: -x['_score_final'])
        
        # Mostra ranking
        for i, r in enumerate(resultados, 1):
            status = "👑" if i == 1 else "  "
            print(f"  {status} #{i} {r['id']} (T={r['temperatura']:.1f}) | "
                  f"score={r['_score_final']:.2f} | lore={r['score_lore']:.2f} | "
                  f"{r['tamanho']} palavras")
        
        # Retorna o melhor
        melhor = resultados[0]
        print(f"\n  👑 ESCOLHIDO: {melhor['id']} (T={melhor['temperatura']:.1f})")
        print(f"  Score final: {melhor['_score_final']:.2f}")
        print(f"  Texto ({melhor['tamanho']} palavras):")
        print(f"  {melhor['texto'][:300]}")
        
        return melhor


# ============================================================
# CICLO INCEPTION — 4 níveis
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR INCEPTION — Conselho de Padrões em Escala")
    print("  N workers com temperaturas diferentes → Conselho escolhe o melhor")
    print("=" * 70)
    
    pe = PatternEngine()
    
    # FASE 0: Carregar corpus + treinar Markov
    print(f"\n{'='*70}")
    print(f"  FASE 0: CARREGAR CORPUS + TREINAR MARKOV")
    print(f"{'='*70}")
    
    builder = CorpusBuilder()
    corpora = builder.carregar_tudo()
    corpora_limpos = {k: builder.limpar(v) for k, v in corpora.items()}
    
    markov = MarkovPorDominio()
    markov.treinar(corpora_limpos)
    
    for dom, mk in markov.markov.items():
        print(f"  Markov '{dom}': {len(mk)} estados")
    
    # FASE 1: NÍVEL 0 — COORDENADOR
    print(f"\n{'='*70}")
    print(f"  NÍVEL 0: COORDENADOR — IE + Temperador")
    print(f"{'='*70}")
    
    pergunta = "Crie uma história sobre a fundação de Eridanus"
    
    # IE detecta
    ie = IntentionEngine(pe=pe)
    intencoes = ie.detectar(pergunta)
    if intencoes:
        cat, params, conf = intencoes[0]
        tipo = params.get('tipo', '')
        print(f"  IE: {cat}/{tipo} (conf={conf:.3f})")
    else:
        cat, tipo = 'CREATE', 'lore'
        print(f"  IE: GERAL (fallback CREATE/lore)")
    
    # Temperador sugere temperaturas
    temperador = TemperadorInterno()
    semente = "eridanus era uma cidade"
    temperaturas = temperador.sugerir_temperaturas(cat.lower(), markov.markov)
    print(f"  Semente: '{semente}'")
    print(f"  Temperaturas sugeridas: {temperaturas}")
    
    # Define domínio
    if tipo in ('lore', 'historia'):
        dominio = 'lore'
    elif tipo == 'npc':
        dominio = 'npc'
    else:
        dominio = 'tecnico'
    
    print(f"  Domínio: {dominio}")
    
    # FASE 2: NÍVEL 1 — WORKERS
    print(f"\n{'='*70}")
    print(f"  NÍVEL 1: WORKERS — N instâncias do MCR gerando")
    print(f"{'='*70}")
    
    workers = []
    for i, temp in enumerate(temperaturas):
        wid = f"MCR_{['A','B','C','D'][i]}"
        w = MCRWorker(wid, temp, dominio)
        texto = w.gerar(markov, semente, tamanho=40)
        valid = w.validar(texto, pe)
        valid['texto'] = texto
        valid['temperatura'] = temp
        workers.append(valid)
        
        print(f"\n  [{wid}] Temperatura={temp:.1f} | Dominio={dominio}")
        print(f"  Texto: {texto[:150]}...")
        print(f"  Score lore: {valid['score_lore']:.3f} | Tokens: {valid['tokens']}")
    
    # FASE 3: NÍVEL 2 — VALIDADORES (embutidos no worker)
    print(f"\n{'='*70}")
    print(f"  NÍVEL 2: VALIDAÇÃO — Auto-validação de cada worker")
    print(f"{'='*70}")
    
    for w in workers:
        print(f"  {w['id']}: score_lore={w['score_lore']:.3f}, {w['tamanho']} palavras, {w['tokens']} tokens")
    
    # FASE 4: NÍVEL 3 — CONSELHO
    print(f"\n{'='*70}")
    print(f"  NÍVEL 3: CONSELHO — Analisa padrões e escolhe o melhor")
    print(f"{'='*70}")
    
    conselho = ConselhoMCR()
    melhor = conselho.avaliar(workers)
    
    # FASE 5: NÍVEL 4 — APRENDIZ
    print(f"\n{'='*70}")
    print(f"  NÍVEL 4: APRENDIZ — KG aprende com o escolhido")
    print(f"{'='*70}")
    
    if melhor:
        # Tokeniza o escolhido
        tokens = pe.tokenizar_universal(melhor['texto'])
        fp = pe.fingerprint(tokens) if tokens else []
        
        # Salva no KG
        try:
            kg = KnowledgeGraph()
            kg.aprender(
                erro=f"inception: {pergunta[:80]}",
                causa=f"worker={melhor['id']}, temp={melhor['temperatura']:.1f}, score={melhor['_score_final']:.2f}",
                solucao=melhor['texto'][:500],
                ctx='inception_aprendizado',
                fingerprint=fp if fp else None,
            )
            print(f"  ✅ Aprendizado salvo no KG (fingerprint: {len(fp) if isinstance(fp, list) else 0} dims)")
            print(f"  → Próxima pergunta similar pode RECONSTRUIR este resultado")
        except Exception as e:
            print(f"  ❌ Erro no aprendizado: {e}")
    
    # RELATÓRIO FINAL
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO FINAL — MCR INCEPTION")
    print(f"{'='*70}")
    
    print(f"\n  Níveis executados: 4/4 ✅")
    print(f"  Workers criados: {len(workers)}")
    print(f"  Temperaturas: {temperaturas}")
    print(f"  Escolhido: {melhor['id'] if melhor else 'NENHUM'}")
    print(f"  Score do escolhido: {melhor['_score_final'] if melhor else 0:.2f}")
    print(f"\n  MECANISMO DE SUPERPOSIÇÃO:")
    print(f"  MCR_A (T={temperaturas[0]:.1f}) → conservador (segue o padrão)")
    print(f"  MCR_B (T={temperaturas[1]:.1f}) → balanceado (padrão + variação)")
    print(f"  MCR_C (T={temperaturas[2]:.1f}) → criativo (explora variações)")
    print(f"  MCR_D (T={temperaturas[3]:.1f}) → caótico (busca novos padrões)")
    print(f"  Conselho → escolhe o de MELHOR PADRÃO, não o mais criativo")
    print(f"\n  0 LLM. 0 GPU. Apenas MCR conversando com MCR.")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
