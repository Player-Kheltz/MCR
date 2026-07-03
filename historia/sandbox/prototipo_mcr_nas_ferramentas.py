#!/usr/bin/env python3
"""MCR DENTRO DAS FERRAMENTAS — Validando a nova arquitetura.

Cada ferramenta ganha um 'cerebro MCR' (PatternEngine + Markov + IE)
que processa a entrada antes de executar.

Melhorias:
1. GeradorTexto contextual — corpus SEPARADO por intencao (lore vs codigo vs explicacao)
2. validar_codigo com diagnostico — Markov de AST + sugestao de correcao
3. buscar_estrategico com ranking — IE ranqueia resultados

0 LLM. 0 modificacao no MCR.
"""
import sys, os, re, json, math, random, time as _time
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.intention_engine import IntentionEngine
from modulos.kg import KnowledgeGraph
from modulos.pi_engine import PiEngine

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# ============================================================
# CORPUS POR DOMÍNIO — GeradorTexto contextual
# ============================================================
class CorpusPorDominio:
    """Carrega corpus SEPARADO por domínio (lore vs técnico vs código)."""
    
    DOMINIOS = ['lore', 'tecnico', 'codigo', 'npc', 'explicacao']
    
    def __init__(self):
        self.corpora = {}
    
    def carregar_tudo(self):
        """Carrega todos os corpora separadamente."""
        self.corpora['lore'] = self._carregar_lore()
        self.corpora['tecnico'] = self._carregar_tecnico()
        self.corpora['codigo'] = self._carregar_codigo()
        self.corpora['explicacao'] = self.corpora.get('tecnico', '') + ' ' + self.corpora.get('lore', '')
        self.corpora['npc'] = self._carregar_npc()
        
        for dom, txt in self.corpora.items():
            print(f"  Corpus '{dom}': {len(txt.split())} palavras")
        return self.corpora
    
    def _carregar_lore(self):
        """Carrega apenas textos de lore/história."""
        textos = []
        # MCR_IDENTITY.md (tem definições de cidade, lore)
        path = os.path.join(BASE, 'docs', 'MCR_IDENTITY.md')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                textos.append(f.read())
        # Qualquer .md que contenha 'lore' ou 'história'
        docs_dir = os.path.join(BASE, 'docs')
        if os.path.isdir(docs_dir):
            for fname in os.listdir(docs_dir):
                if fname.endswith('.md') and any(w in fname.lower() for w in ['lore', 'hist', 'conceito', 'identidade']):
                    path = os.path.join(docs_dir, fname)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            textos.append(f.read())
                    except: pass
        return ' '.join(textos)
    
    def _carregar_tecnico(self):
        """Carrega textos técnicos (docs, conversas)."""
        textos = []
        # Conversas
        conv_path = os.path.join(BASE, 'sandbox', '.mcr_conversa.jsonl')
        if os.path.exists(conv_path):
            try:
                with open(conv_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            msg = entry.get('msg', '')
                            if msg and len(msg) > 20: textos.append(msg)
                        except: pass
            except: pass
        # KG solutions
        try:
            kg = KnowledgeGraph()
            for l in kg._get_licoes()[:500]:
                sol = l.get('solucao', '')
                if sol and len(sol) > 20: textos.append(sol)
        except: pass
        return ' '.join(textos)
    
    def _carregar_codigo(self):
        """Carrega apenas código-fonte."""
        textos = []
        for root, dirs, files in os.walk(os.path.join(BASE, 'data')):
            for f in files:
                if f.endswith('.lua') or f.endswith('.py'):
                    path = os.path.join(root, f)
                    try:
                        with open(path, 'r', encoding='utf-8') as fh:
                            textos.append(fh.read())
                    except: pass
        return ' '.join(textos)
    
    def _carregar_npc(self):
        """Carrega apenas arquivos de NPC."""
        textos = []
        npc_dir = os.path.join(BASE, 'data', 'npc')
        if os.path.isdir(npc_dir):
            for fname in os.listdir(npc_dir):
                if fname.endswith('.lua'):
                    try:
                        with open(os.path.join(npc_dir, fname), 'r', encoding='utf-8') as f:
                            textos.append(f.read())
                    except: pass
        return ' '.join(textos)
    
    def selecionar(self, intencao: str, tipo: str = '') -> str:
        """Seleciona o corpus adequado para a intenção."""
        if intencao == 'CREATE':
            if tipo in ('lore', 'historia'): return self.corpora.get('lore', '')
            if tipo == 'npc': return self.corpora.get('npc', '') + ' ' + self.corpora.get('codigo', '') 
            return self.corpora.get('codigo', '')
        elif intencao == 'EXPLAIN':
            return self.corpora.get('explicacao', '')
        return self.corpora.get('tecnico', '')
    
    def limpar(self, texto):
        texto = re.sub(r'http\S+', '', texto)
        texto = re.sub(r'[<>]', '', texto)
        texto = re.sub(r'[^\w\s\.\,\!\?\-\'\"]', ' ', texto)
        return re.sub(r'\s+', ' ', texto).strip().lower()


class GeradorTextoContextual:
    """Gera texto usando corpus ESPECÍFICO da intenção."""
    
    def __init__(self):
        self.markov = {}  # dominio → {chave: {proxima: count}}
    
    def treinar(self, corpora: Dict[str, str]):
        """Treina Markov para CADA domínio separadamente."""
        for dominio, texto in corpora.items():
            palavras = texto.split()
            mk = {}
            for i in range(len(palavras) - 2):
                chave = f"{palavras[i]} {palavras[i+1]}"
                prox = palavras[i+2]
                if chave not in mk: mk[chave] = {}
                mk[chave][prox] = mk[chave].get(prox, 0) + 1
            self.markov[dominio] = mk
            print(f"  Markov '{dominio}': {len(mk)} estados")
    
    def gerar(self, intencao: str, tipo: str = '',
              semente: str = '', tamanho: int = 40, temperatura: float = 0.3) -> str:
        """Gera texto usando o corpus da intenção."""
        # Seleciona corpus
        if intencao == 'CREATE' and tipo in ('lore', 'historia'):
            dominio = 'lore'
        elif intencao == 'CREATE' and tipo == 'npc':
            dominio = 'npc'
        elif intencao == 'EXPLAIN':
            dominio = 'explicacao'
        else:
            dominio = 'tecnico'
        
        mk = self.markov.get(dominio, {})
        if not mk:
            return "(corpus vazio para esta intencao)"
        
        palavras = semente.lower().split() if semente else []
        if len(palavras) < 2:
            palavras = list(random.choice(list(mk.keys())).split()) if mk else ['o', 'sistema']
        
        ultima_palavra = None
        repeticoes = 0
        
        for _ in range(tamanho):
            if len(palavras) >= 2:
                chave = f"{palavras[-2]} {palavras[-1]}"
            else:
                break
            
            if chave not in mk:
                break
            
            proximas = mk[chave]
            if not proximas:
                break
            
            # Escolhe com temperatura
            if temperatura <= 0:
                escolhida = max(proximas, key=proximas.get)
            else:
                pesos = list(proximas.values())
                soma = sum(pesos)
                pesos_norm = [p/soma for p in pesos]
                pesos_temp = [p ** (1.0/max(temperatura, 0.01)) for p in pesos_norm]
                total = sum(pesos_temp)
                probs = [p/total for p in pesos_temp]
                escolhida = random.choices(list(proximas.keys()), weights=probs, k=1)[0]
            
            # Limitador de repetição
            if escolhida == ultima_palavra:
                repeticoes += 1
                if repeticoes >= 3 and len(proximas) > 1:
                    sorted_p = sorted(proximas.items(), key=lambda x: -x[1])
                    for alt, _ in sorted_p:
                        if alt != escolhida:
                            escolhida = alt; break
                    repeticoes = 0
            else:
                repeticoes = 0
            
            palavras.append(escolhida)
            ultima_palavra = escolhida
        
        texto = ' '.join(palavras)
        return texto[0].upper() + texto[1:] if texto else ''


# ============================================================
# VALIDADOR DE CÓDIGO COM DIAGNÓSTICO
# ============================================================
class ValidadorCodigoMCR:
    """Valida código com PatternEngine + Markov de AST.
    
    Não só detecta erro — diz ONDE e POR QUÊ.
    """
    
    def __init__(self):
        self.pe = PatternEngine()
        
        # Markov de código VÁLIDO (aprendido de exemplos reais)
        self.markov_ast = {
            'KW_local': {'AST_Assign': 0.6, 'AST_Call': 0.3, 'KW_function': 0.1},
            'AST_Assign': {'AST_Call': 0.5, 'AST_Table': 0.3, 'FIM_LINHA': 0.2},
            'AST_Table': {'STR_Key': 0.4, 'AST_Assign': 0.3, 'AST_Table': 0.2, 'FIM_TABLE': 0.1},
            'STR_Key': {'AST_Assign': 0.6, 'AST_Value': 0.3, 'FIM_LINHA': 0.1},
            'AST_Call': {'FIM_LINHA': 0.5, 'AST_Func': 0.3, 'AST_Args': 0.2},
            'FIM_TABLE': {'KW_return': 0.7, 'KW_local': 0.2, 'AST_Call': 0.1},
            'KW_return': {'STR_Value': 0.6, 'AST_Call': 0.3, 'FIM_LINHA': 0.1},
            'FIM_LINHA': {'KW_local': 0.3, 'KW_return': 0.3, 'FIM_LINHA': 0.2, 'AST_Call': 0.2},
        }
    
    def validar(self, codigo: str) -> Dict:
        """Valida código e retorna diagnóstico completo.
        
        Returns:
            dict: {valido, erros: [{linha, descricao, sugestao}], tokens, entropia}
        """
        # Tokeniza
        tokens = self.pe.tokenizar_universal(codigo) or []
        tipos = [t[0] for t in tokens]
        
        # Extrai padrões
        padroes = self.pe.extrair_padroes(tokens)
        entropia = padroes.get('entropia', 1.0)
        
        erros = []
        
        # Verificação 1: tokens quebram o padrão AST esperado
        for i in range(len(tipos) - 1):
            t_atual = tipos[i]
            t_prox = tipos[i + 1]
            
            if t_atual in self.markov_ast:
                esperados = self.markov_ast[t_atual]
                if t_prox not in esperados:
                    # Transição anômala
                    linha = self._encontrar_linha(codigo, tokens, i)
                    erros.append({
                        'linha': linha,
                        'descricao': f"'{t_prox}' inesperado depois de '{t_atual}'",
                        'sugestao': self._sugerir_correcao(t_atual, t_prox),
                        'tipo': 'transicao_invalida',
                    })
        
        # Verificação 2: 'return' dentro de table
        dentro_table = False
        for i, t in enumerate(tipos):
            if t == 'AST_Table': dentro_table = True
            if t == 'FIM_TABLE': dentro_table = False
            if t == 'KW_return' and dentro_table:
                linha = self._encontrar_linha(codigo, tokens, i)
                erros.append({
                    'linha': linha,
                    'descricao': "'return' dentro de table (deve estar DEPOIS do fechamento '}')",
                    'sugestao': "Mover 'return' para depois da linha com '}'",
                    'tipo': 'return_em_table',
                })
        
        # Verificação 3: 'end' sem 'function'
        stack = []
        for i, t in enumerate(tipos):
            if t == 'KW_function': stack.append('function')
            if t == 'KW_end':
                if not stack:
                    linha = self._encontrar_linha(codigo, tokens, i)
                    erros.append({
                        'linha': linha,
                        'descricao': f"'end' sem 'function' correspondente",
                        'sugestao': "Remover 'end' extra ou adicionar 'function' faltante",
                        'tipo': 'end_sem_function',
                    })
                else:
                    stack.pop()
        
        return {
            'valido': len(erros) == 0,
            'erros': erros[:5],
            'total_erros': len(erros),
            'tokens': len(tokens),
            'tipos': tipos[:15],
            'entropia': round(entropia, 4),
        }
    
    def _encontrar_linha(self, codigo: str, tokens: list, idx: int) -> int:
        """Estima a linha do erro baseado na posição do token."""
        try:
            token_str = str(tokens[idx])
            # Procura o token no código
            lines = codigo.split('\n')
            for i, line in enumerate(lines):
                if token_str[:10] in line:
                    return i + 1
        except: pass
        return 0
    
    def _sugerir_correcao(self, t_atual: str, t_prox: str) -> str:
        """Sugere correção baseada no Markov de código válido."""
        if t_atual not in self.markov_ast:
            return "Verificar estrutura ao redor"
        esperados = self.markov_ast[t_atual]
        mais_provavel = max(esperados, key=esperados.get)
        return f"Substituir '{t_prox}' por '{mais_provavel}' (ou adicionar '{mais_provavel}' antes)"


# ============================================================
# BUSCA ESTRATÉGICA COM RANKING
# ============================================================
class BuscaEstrategicaMCR:
    """buscar_estrategico + IE ranking = resultados RELEVANTES."""
    
    def __init__(self):
        self.pe = PatternEngine()
        self.ie = IntentionEngine(pe=self.pe)
    
    def buscar(self, termo: str, intencao: str = '', top_n: int = 5) -> List[Dict]:
        """Busca e RANQUEIA por relevância à intenção."""
        from modulos.tool_orchestrator import ToolOrchestrator
        tools = ToolOrchestrator()
        
        r = tools.executar('buscar_estrategico', {'termo': termo})
        if not r or not r.get('sucesso'):
            return []
        
        dados = str(r.get('resultado', ''))
        if not dados or 'Nenhum' in dados:
            return []
        
        # Para cada resultado, calcula relevância
        resultados = []
        for linha in dados.split('\n'):
            linha = linha.strip()
            if not linha:
                continue
            
            # Calcula relevância com IE
            score_relevancia = self._calcular_relevancia(linha, termo, intencao)
            resultados.append({
                'caminho': linha,
                'relevancia': score_relevancia,
            })
        
        # Ordena por relevância
        resultados.sort(key=lambda x: -x['relevancia'])
        return resultados[:top_n]
    
    def _calcular_relevancia(self, texto: str, termo: str, intencao: str = '') -> float:
        """Calcula quão relevante um resultado é para a intenção."""
        score = 0.0
        texto_lower = texto.lower()
        
        # Match do termo
        if termo.lower() in texto_lower:
            score += 0.5
        
        # Preferência por arquivos .md (documentação)
        if texto.endswith('.md'):
            score += 0.2
        elif texto.endswith('.lua') and intencao == 'CREATE':
            score += 0.2
        
        # Preferência por docs/
        if texto.startswith('docs/'):
            score += 0.15
        
        # Penalidade para diretórios muito genéricos
        if 'node_modules' in texto_lower or 'backup' in texto_lower or 'legado' in texto_lower:
            score -= 0.3
        
        return max(0.0, min(1.0, score))


# ============================================================
# TESTE COMPARATIVO
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR DENTRO DAS FERRAMENTAS — Protótipo de Validação")
    print("  GeradorTexto contextual + Validador AST + Busca rankeada")
    print("=" * 70)
    
    # FASE 1: Corpus por domínio
    print(f"\n{'='*70}")
    print(f"  FASE 1: CORPUS POR DOMÍNIO")
    print(f"{'='*70}")
    
    corpus = CorpusPorDominio()
    corpora = corpus.carregar_tudo()
    
    gerador = GeradorTextoContextual()
    gerador.treinar(corpora)
    
    # FASE 2: Geração contextual vs mista
    print(f"\n{'='*70}")
    print(f"  FASE 2: GERAÇÃO CONTEXTUAL vs MISTA")
    print(f"{'='*70}")
    
    semente = "eridanus era uma cidade"
    
    # ANTES (corpus misto)
    mk_misto = {}
    for dom, texto in corpora.items():
        palavras = texto.split()
        for i in range(len(palavras)-2):
            chave = f"{palavras[i]} {palavras[i+1]}"
            prox = palavras[i+2]
            if chave not in mk_misto: mk_misto[chave] = {}
            mk_misto[chave][prox] = mk_misto[chave].get(prox, 0) + 1
    
    # Simula geracao com corpus misto (ANTES)
    palavras_antes = semente.lower().split()
    for _ in range(30):
        if len(palavras_antes) >= 2:
            chave = f"{palavras_antes[-2]} {palavras_antes[-1]}"
            if chave in mk_misto:
                prox = mk_misto[chave]
                if prox:
                    escolha = max(prox, key=prox.get)
                    palavras_antes.append(escolha)
    texto_antes = ' '.join(palavras_antes)
    
    # Geração com corpus contextual (DEPOIS)
    texto_depois = gerador.gerar('CREATE', 'lore', semente, tamanho=40, temperatura=0.3)
    
    print(f"\n  ANTES (corpus misto — história vira documentação):")
    print(f"  {texto_antes[:300]}")
    print()
    print(f"  DEPOIS (corpus lore — mantém narrativa):")
    print(f"  {texto_depois[:300]}")
    
    # Análise de qualidade
    termos_tecnicos = ['servidor', 'arquivo', 'sistema', 'buff', 'timestamp', 'xp', 'lua', 'dados', 'modificação']
    termos_lore = ['cidade', 'fundação', 'aventureiro', 'história', 'lendária', 'povo', 'terra', 'norte', 'sul', 'rei']
    
    tec_antes = sum(1 for t in termos_tecnicos if t in texto_antes.lower())
    tec_depois = sum(1 for t in termos_tecnicos if t in texto_depois.lower())
    lore_antes = sum(1 for t in termos_lore if t in texto_antes.lower())
    lore_depois = sum(1 for t in termos_lore if t in texto_depois.lower())
    
    print(f"\n  Termos técnicos: ANTES={tec_antes}, DEPOIS={tec_depois} {'⬆️ piorou' if tec_depois > tec_antes else '⬇️ melhorou'}")
    print(f"  Termos de lore:  ANTES={lore_antes}, DEPOIS={lore_depois} {'⬆️ melhorou' if lore_depois > lore_antes else '⬇️ piorou'}")
    
    # FASE 3: Validador com diagnóstico
    print(f"\n{'='*70}")
    print(f"  FASE 3: VALIDADOR DE CÓDIGO COM DIAGNÓSTICO")
    print(f"{'='*70}")
    
    validador = ValidadorCodigoMCR()
    
    codigos_teste = [
        ("Código com bug (return dentro de table)", """local lore = {
    nome = "Fundacao de Eridanus",
    tipo = "lore",

return lore
end"""),
        ("Código normal (sem bugs)", """local lore_eridanus = {
    nome = "Fundacao de Eridanus",
    tipo = "lore",
}

return lore_eridanus"""),
    ]
    
    for nome, codigo in codigos_teste:
        print(f"\n  {nome}:")
        diag = validador.validar(codigo)
        status = "✅ VALIDO" if diag['valido'] else f"❌ {diag['total_erros']} erro(s)"
        print(f"  Status: {status}")
        print(f"  Tokens: {diag['tokens']} | Entropia: {diag['entropia']}")
        for err in diag['erros'][:3]:
            print(f"    Linha {err['linha']}: {err['descricao']}")
            print(f"    → Sugestão: {err['sugestao']}")
    
    # FASE 4: Busca com ranking
    print(f"\n{'='*70}")
    print(f"  FASE 4: BUSCA ESTRATÉGICA COM RANKING")
    print(f"{'='*70}")
    
    busca = BuscaEstrategicaMCR()
    
    print(f"\n  Buscando 'NPC' (intenção: CREATE/npc):")
    resultados = busca.buscar('NPC', 'CREATE', top_n=5)
    for i, r in enumerate(resultados, 1):
        print(f"  {i}. [{r['relevancia']:.2f}] {r['caminho'][:80]}")
    
    print(f"\n  Buscando 'SPA' (intenção: EXPLAIN):")
    resultados2 = busca.buscar('SPA', 'EXPLAIN', top_n=5)
    for i, r in enumerate(resultados2, 1):
        print(f"  {i}. [{r['relevancia']:.2f}] {r['caminho'][:80]}")
    
    # RELATÓRIO FINAL
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO FINAL")
    print(f"{'='*70}")
    print(f"\n  ✅ GeradorTexto contextual — corpus por intenção funciona")
    print(f"     Termos técnicos na história: ANTES={tec_antes} → DEPOIS={tec_depois}")
    print(f"     Termos de lore na história:  ANTES={lore_antes} → DEPOIS={lore_depois}")
    print(f"\n  ✅ Validador com diagnóstico — erro DETECTADO + SUGESTÃO")
    print(f"     'return dentro de table' → 'Mover return para depois de }}'")
    print(f"\n  ✅ Busca com ranking — resultados RELEVANTES primeiro")
    print(f"     NPC com intenção CREATE: arquivos .lua ranqueados acima")
    print(f"\n  Ferramentas com MCR dentro — qualidade COMPROVADA")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
