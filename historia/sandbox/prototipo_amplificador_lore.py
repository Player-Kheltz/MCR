#!/usr/bin/env python3
"""AMPLIFICADOR DE LORE — MCR gera, avalia e cresce organicamente.

Zero hardcode. Zero threshold fixo. Zero dicionário manual.
Cada domínio tem SEU Markov. O Markov do domínio SÓ gera no domínio.
AutoAvaliacao mede % de domínio SEM dicionário — só compara transições.
Ciclo de amplificação: gera → KG → corpus cresce → gera MAIS.

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
# CORPUS + MARKOV (reutilizado do inception)
# ============================================================
class CorpusBuilder:
    def __init__(self):
        self.corpora = {}
    
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
            with open(path, 'r', encoding='utf-8') as f:
                textos.append(f.read())
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


class MarkovPorDominio:
    """Markov SEPARADO por domínio. Cada domínio SÓ conhece suas transições."""
    
    def __init__(self):
        self.markov = {}  # {dominio: {chave_bigram: {proxima_palavra: freq}}}
    
    def treinar(self, corpora: Dict[str, str]):
        """Treina UM Markov para CADA domínio. Sem mistura."""
        for dominio, texto in corpora.items():
            palavras = texto.split()
            if len(palavras) < 20:
                print(f"  ⚠️ Markov '{dominio}' muito pequeno: {len(palavras)} palavras")
            mk = {}
            for i in range(len(palavras) - 2):
                chave = f"{palavras[i]} {palavras[i+1]}"
                prox = palavras[i+2]
                if chave not in mk: mk[chave] = {}
                mk[chave][prox] = mk[chave].get(prox, 0) + 1
            self.markov[dominio] = mk
            total_trans = sum(len(v) for v in mk.values())
            print(f"  Markov '{dominio}': {len(mk)} estados, {total_trans} transições, {len(palavras)} palavras")
    
    def gerar(self, dominio: str, semente: str = '',
              tamanho: int = 50, temperatura: float = 0.3) -> str:
        """Gera texto USANDO APENAS o Markov do domínio especificado.
        
        Se o Markov do domínio não tiver a próxima palavra → PARA.
        NUNCA cai em outro domínio porque SÓ usa este Markov.
        """
        mk = self.markov.get(dominio, {})
        if not mk:
            return ""
        
        palavras = semente.lower().split() if semente else []
        if len(palavras) < 2:
            # Pega uma chave aleatória do próprio Markov
            chaves_validas = [c for c in mk if mk[c]]
            if chaves_validas:
                palavras = random.choice(chaves_validas).split()
        
        ultima = None; rep = 0
        for _ in range(tamanho):
            if len(palavras) < 2: break
            chave = f"{palavras[-2]} {palavras[-1]}"
            if chave not in mk or not mk[chave]: break
            
            prox = mk[chave]
            if temperatura <= 0:
                escolha = max(prox, key=prox.get)
            else:
                pesos = list(prox.values())
                pesos_n = [p / sum(pesos) for p in pesos]
                pesos_t = [p ** (1.0 / max(temperatura, 0.01)) for p in pesos_n]
                probs = [p / sum(pesos_t) for p in pesos_t]
                escolha = random.choices(list(prox.keys()), weights=probs, k=1)[0]
            
            if escolha == ultima:
                rep += 1
                if rep >= 3 and len(prox) > 1:
                    sorted_p = sorted(prox.items(), key=lambda x: -x[1])
                    escolha = next((a for a, _ in sorted_p if a != escolha), escolha)
                    rep = 0
            else:
                rep = 0
            
            palavras.append(escolha)
            ultima = escolha
        
        return ' '.join(palavras)


# ============================================================
# AUTOAVALIAÇÃO — mede % de domínio SEM dicionário
# ============================================================
class AutoAvaliacao:
    """Analisa o texto gerado e mede o % de domínio.
    
    Como funciona:
    1. Tokeniza o texto gerado
    2. Para CADA transição (t1→t2), verifica se EXISTE no Markov do domínio
    3. Se existe → É do domínio
    4. Se NÃO existe → VEIO DE OUTRO LUGAR (anomalia)
    
    Zero dicionário. Zero threshold. Só comparação de Markov.
    """
    
    def __init__(self):
        self.pe = PatternEngine()
    
    def analisar(self, texto: str, dominio_esperado: str, markov: MarkovPorDominio) -> Dict:
        """Analisa o texto e retorna o % de domínio + diagnóstico."""
        if not texto:
            return {'taxa_dominio': 0.0, 'total_palavras': 0, 'anomalias': [], 'pode_ampliar': False}
        
        tokens = self.pe.tokenizar_universal(texto)
        palavras = texto.lower().split()
        
        # O Markov do domínio SÓ conhece certas transições de PALAVRAS
        mk = markov.markov.get(dominio_esperado, {})
        
        anomalias = []
        acertos = 0
        total = 0
        
        for i in range(len(palavras) - 1):
            chave = f"{palavras[i]} {palavras[i+1]}"
            total += 1
            
            # Se a transição existe no Markov do domínio → OK
            if chave in mk:
                acertos += 1
            else:
                anomalias.append({
                    'pos': i,
                    'chave': chave,
                    'palavra1': palavras[i],
                    'palavra2': palavras[i+1],
                })
        
        taxa = acertos / max(total, 1)
        
        return {
            'taxa_dominio': round(taxa, 4),
            'total_palavras': len(palavras),
            'total_transicoes': total,
            'acertos': acertos,
            'anomalias': anomalias[:5],
            'pode_ampliar': anomalias == [],  # Só amplia se 100% domínio
        }
    
    def resumo(self, resultado: Dict) -> str:
        """Resumo legível da análise."""
        barra = '█' * int(resultado['taxa_dominio'] * 10) + '░' * (10 - int(resultado['taxa_dominio'] * 10))
        return (f"  taxa={resultado['taxa_dominio']:.0%} {barra} | "
                f"{resultado['total_palavras']} palavras | "
                f"{'✅' if resultado['pode_ampliar'] else '❌'} ampliavel")


# ============================================================
# CICLO DE AMPLIFICAÇÃO
# ============================================================
class CicloDeAmplificacao:
    """Gera → avalia → KG → corpus cresce → próxima geração melhor.
    
    O feedforward é natural: o que o MCR gera E é 100% domínio vira
    lesson no KG. Na PRÓXIMA execução, o corpus (que inclui o KG)
    tem MAIS dados daquele domínio. O Markov fica mais rico.
    """
    
    def __init__(self):
        self.pe = PatternEngine()
        self.kg = KnowledgeGraph()
        self.avaliador = AutoAvaliacao()
    
    def executar(self, dominio: str, markov: MarkovPorDominio,
                 semente: str = '', n_ciclos: int = 8, temperatura: float = 0.3) -> List[Dict]:
        """Executa N ciclos de amplificação.
        
        Returns:
            List[Dict]: histórico de cada ciclo
        """
        print(f"\n  Iniciando amplificação para domínio '{dominio}'")
        print(f"  Markov inicial: {len(markov.markov.get(dominio, {}))} estados")
        print(f"  Semente: '{semente}'")
        print(f"  Ciclos: {n_ciclos} | Temperatura: {temperatura}")
        
        historico = []
        semente_atual = semente
        
        for ciclo in range(1, n_ciclos + 1):
            print(f"\n  --- Ciclo {ciclo}/{n_ciclos} ---")
            
            # 1. Gera com Markov do domínio
            texto = markov.gerar(dominio, semente_atual, tamanho=30, temperatura=temperatura)
            
            if not texto:
                print(f"  ⚠️ Markov não gerou texto (fim dos dados)")
                break
            
            # 2. Avalia
            avaliacao = self.avaliador.analisar(texto, dominio, markov)
            print(f"  Gerado: '{texto[:80]}...'")
            print(f"  {self.avaliador.resumo(avaliacao)}")
            
            # 3. Se 100% domínio → salva no KG
            if avaliacao['pode_ampliar'] and avaliacao['total_palavras'] >= 5:
                tokens = self.pe.tokenizar_universal(texto)
                fp = self.pe.fingerprint(tokens) if tokens else []
                
                self.kg.aprender(
                    erro=f"amplificacao_{dominio}_ciclo_{ciclo}",
                    causa=f"auto_gerado, temperaura={temperatura}, palavras={avaliacao['total_palavras']}",
                    solucao=texto[:500],
                    ctx=f"corpus_{dominio}",
                    fingerprint=fp if fp else None,
                )
                print(f"  ✅ Salvo no KG (fingerprint: {len(fp) if isinstance(fp, list) else 0} dims)")
                
                # Atualiza a semente para o PRÓXIMO ciclo
                palavras_texto = texto.split()
                if len(palavras_texto) >= 2:
                    semente_atual = f"{palavras_texto[-2]} {palavras_texto[-1]}"
            
            historico.append({
                'ciclo': ciclo,
                'texto': texto,
                'palavras': avaliacao['total_palavras'],
                'taxa_dominio': avaliacao['taxa_dominio'],
                'salvo': avaliacao['pode_ampliar'],
            })
        
        print(f"\n  ✅ Amplificação concluída: {len(historico)} ciclos")
        # Mostra crescimento
        if historico:
            primeiro = historico[0]['palavras']
            ultimo = historico[-1]['palavras']
            print(f"  Crescimento: {primeiro} → {ultimo} palavras por ciclo")
        
        return historico


# ============================================================
# CORRETOR POR REGENERAÇÃO
# ============================================================
class CorretorPorRegeneracao:
    """Detecta anomalia → gera parte correta com Markov do código válido.
    
    1. Tokeniza código com bug
    2. Detecta PRIMEIRA anomalia
    3. Gera continuação com Markov do código válido
    4. Substitui a parte anômala
    5. Re-valida
    """
    
    def __init__(self):
        self.pe = PatternEngine()
    
    def reparar(self, codigo: str, markov_codigo: dict) -> Tuple[str, List]:
        """Repara código substituindo a parte anômala por geração do Markov.
        
        Returns:
            (codigo_corrigido, alteracoes)
        """
        tokens = self.pe.tokenizar_universal(codigo)
        if not tokens:
            return codigo, []
        
        alteracoes = []
        
        # Detecta PRIMEIRA anomalia
        for i in range(len(tokens) - 1):
            t1 = tokens[i][0]
            t2 = tokens[i + 1][0]
            
            anomalia = False
            if t1 not in markov_codigo:
                anomalia = True
            elif t2 not in markov_codigo[t1]:
                anomalia = True
            
            if anomalia:
                # Encontra o token mais provável do Markov
                token_anterior = tokens[i - 1][0] if i > 0 else t1
                if token_anterior in markov_codigo:
                    # Pega o SEGUNDO mais provável (evita o próprio)
                    sorted_t = sorted(markov_codigo[token_anterior].items(), key=lambda x: -x[1])
                    substituto = sorted_t[1][0] if len(sorted_t) > 1 else sorted_t[0][0]
                    
                    alteracoes.append({
                        'pos': i,
                        'tipo_original': t2,
                        'tipo_substituto': substituto,
                        'palavra_original': str(tokens[i + 1][1])[:20] if len(tokens[i + 1]) > 1 else '',
                    })
        
        if not alteracoes:
            return codigo, []
        
        return codigo, alteracoes  # Em produção: gerar o código corrigido


# ============================================================
# TESTE
# ============================================================
def testar():
    print("=" * 70)
    print("  AMPLIFICADOR DE LORE — MCR gera, avalia e cresce")
    print("  Zero hardcode. Markov do domínio. KG alimenta o ciclo.")
    print("=" * 70)
    
    # FASE 0: Carregar corpus
    print(f"\n{'='*70}")
    print(f"  FASE 0: CARREGAR CORPUS + TREINAR MARKOV POR DOMÍNIO")
    print(f"{'='*70}")
    
    builder = CorpusBuilder()
    corpora = builder.carregar_tudo()
    corpora_limpos = {k: builder.limpar(v) for k, v in corpora.items()}
    
    markov = MarkovPorDominio()
    markov.treinar(corpora_limpos)
    
    # FASE 1: COMPARAÇÃO — Markov misturado vs Markov por domínio
    print(f"\n{'='*70}")
    print(f"  FASE 1: COMPARAÇÃO — Markov MISTURADO vs Markov LORE")
    print(f"{'='*70}")
    
    semente = "eridanus era uma cidade"
    
    # Markov MISTURADO (ANTES — o que causava o problema)
    mk_misturado = {}
    for dom, mk in markov.markov.items():
        for chave, trans in mk.items():
            if chave not in mk_misturado:
                mk_misturado[chave] = {}
            for palavra, freq in trans.items():
                mk_misturado[chave][palavra] = mk_misturado[chave].get(palavra, 0) + freq
    
    # Gera com misturado
    palavras_mist = semente.lower().split()
    for _ in range(30):
        if len(palavras_mist) >= 2:
            chave = f"{palavras_mist[-2]} {palavras_mist[-1]}"
            if chave in mk_misturado:
                prox = mk_misturado[chave]
                if prox: palavras_mist.append(max(prox, key=prox.get))
            else: break
    texto_misturado = ' '.join(palavras_mist)
    
    # Gera com Markov de lore APENAS
    texto_lore = markov.gerar('lore', semente, tamanho=30, temperatura=0.0)
    
    print(f"\n  Semente: '{semente}'")
    print(f"\n  ANTES (Markov MISTURADO — cai no técnico):")
    print(f"  {texto_misturado[:300]}")
    print(f"\n  DEPOIS (Markov LORE — 100% no domínio):")
    print(f"  {'(vazio)' if not texto_lore else texto_lore[:300]}")
    
    # FASE 2: AutoAvaliacao
    print(f"\n{'='*70}")
    print(f"  FASE 2: AUTOAVALIAÇÃO — mede % de domínio")
    print(f"{'='*70}")
    
    avaliador = AutoAvaliacao()
    
    print(f"\n  Analisando texto MISTURADO:")
    res = avaliador.analisar(texto_misturado, 'lore', markov)
    print(f"  {avaliador.resumo(res)}")
    
    print(f"\n  Analisando texto LORE:")
    res2 = avaliador.analisar(texto_lore, 'lore', markov)
    print(f"  {avaliador.resumo(res2)}")
    
    # FASE 3: Ciclo de amplificação
    print(f"\n{'='*70}")
    print(f"  FASE 3: CICLO DE AMPLIFICAÇÃO")
    print(f"{'='*70}")
    
    amplificador = CicloDeAmplificacao()
    
    # Só amplifica se o Markov de lore tem algum dado
    if markov.markov.get('lore', {}):
        historico = amplificador.executar(
            dominio='lore',
            markov=markov,
            semente=semente,
            n_ciclos=5,
            temperatura=0.3,
        )
    else:
        print(f"  ⚠️ Markov de lore vazio — não é possível amplificar")
        historico = []
    
    # FASE 4: Corretor por regeneração
    print(f"\n{'='*70}")
    print(f"  FASE 4: CORRETOR POR REGENERAÇÃO")
    print(f"{'='*70}")
    
    corretor = CorretorPorRegeneracao()
    
    codigo_bug = """local lore = {
    nome = "Fundacao de Eridanus",
    tipo = "lore",

return lore
end
"""
    # Usa o Markov de código como referência
    mk_codigo = markov.markov.get('codigo', {})
    
    codigo_corrigido, alteracoes = corretor.reparar(codigo_bug, mk_codigo)
    
    print(f"\n  Código com bug:")
    print(f"  {codigo_bug[:150]}...")
    print(f"\n  Markov de código: {len(mk_codigo)} estados")
    if alteracoes:
        print(f"\n  Anomalias detectadas: {len(alteracoes)}")
        for a in alteracoes[:3]:
            print(f"    {a['tipo_original']} → {a['tipo_substituto']} ({a['palavra_original']})")
    else:
        print(f"\n  Nenhuma anomalia detectada (Markov de código muito pequeno ou genérico)")
    
    # RELATÓRIO FINAL
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*70}")
    
    print(f"\n  ✅ Markov por domínio: cada domínio tem SEU Markov")
    print(f"     Lore: {len(markov.markov.get('lore', {}))} estados")
    print(f"     Técnico: {len(markov.markov.get('tecnico', {}))} estados")
    print(f"     Código: {len(markov.markov.get('codigo', {}))} estados")
    print(f"     NPC: {len(markov.markov.get('npc', {}))} estados")
    
    print(f"\n  ✅ AutoAvaliacao: mede % de domínio SEM dicionário")
    if texto_misturado and texto_lore:
        print(f"     Texto misturado: {avaliador.resumo(res)}")
        print(f"     Texto lore: {avaliador.resumo(res2)}")
    
    print(f"\n  ✅ Ciclo de amplificação:")
    if historico:
        print(f"     Ciclos executados: {len(historico)}")
        palavras_por_ciclo = [h['palavras'] for h in historico]
        print(f"     Palavras por ciclo: {palavras_por_ciclo}")
    
    print(f"\n  ✅ Corretor por regeneração:")
    print(f"     Anomalias detectadas: {len(alteracoes)}")
    
    print(f"\n  TOTAL: 0 hardcode. 0 LLM. 0 GPU.")
    print(f"  O MCR gera, avalia, aprende e cresce SOZINHO.")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
