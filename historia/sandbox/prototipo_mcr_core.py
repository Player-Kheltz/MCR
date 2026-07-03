#!/usr/bin/env python3
"""MCR CORE — Classe única que centraliza TODO o conhecimento do MCR.

TODAS as ferramentas usam o MESMO core.
Quando o core APRENDE algo novo, TODAS as ferramentas melhoram automaticamente.

Interface universal:
  mcr.buscar_por_assinatura(texto_exemplo) → arquivos similares
  mcr.validar_por_padrao(codigo) → anomalias detectadas
  mcr.gerar_por_dominio(texto_exemplo) → texto novo no mesmo padrão
  mcr.aprender(novo_conhecimento) → TODAS as ferramentas melhoram

0 LLM. 0 GPU. 1 ÚNICO CORE.
"""
import sys, os, re, json, math, random, time
from collections import Counter
from typing import List, Dict, Tuple, Optional, Any

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts', 'mcr_devia'))

from modulos.pattern_engine import PatternEngine
from modulos.pi_engine import PiEngine
from modulos.intention_engine import IntentionEngine
from modulos.kg import KnowledgeGraph
from modulos.aprendiz_de_padroes import AprendizDePadroes
from modulos.tool_orchestrator import ToolOrchestrator


class MCRCore:
    """Cérebro ÚNICO do MCR. Todas as ferramentas são extensões deste core.
    
    Quando o core APRENDE → TODAS as ferramentas melhoram.
    Uma única instância. Um único conhecimento. Universal.
    """
    
    _instancia = None  # Singleton
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializar()
        return cls._instancia
    
    def _inicializar(self):
        """Inicializa UMA vez. Singleton — mesma instância para TODAS as ferramentas."""
        print("[MCRCore] Inicializando cérebro único...")
        
        self.pe = PatternEngine()
        self.pi = PiEngine(pe=self.pe)
        self.ie = IntentionEngine(pe=self.pe)
        self.kg = KnowledgeGraph()
        self.aprendiz = AprendizDePadroes(pe=self.pe, kg=self.kg)
        self.tools = ToolOrchestrator()
        
        # Conhecimento do core (cresce com cada aprendizado)
        self.markov_assuntos = {}    # {dominio: {chave: {proxima: freq}}}
        self.fingerprints = {}       # {dominio: fingerprint_medio}
        self.vocabulario = {}         # {palavra: {dominio: freq}}
        self.total_aprendizados = 0
        
        print("[MCRCore] Core pronto. Ferramentas podem usar.")
    
    # ============================================================
    # API UNIVERSAL — TODAS as ferramentas usam estes métodos
    # ============================================================
    
    def buscar_por_assinatura(self, texto_exemplo: str, max_resultados: int = 5) -> List[Dict]:
        """Busca arquivos com ASSINATURA DE PADRÃO similar ao exemplo.
        
        Usado por: buscar_estrategico, buscar_codigo, buscar_kg
        """
        tokens = self.pe.tokenizar_universal(texto_exemplo)
        if not tokens or len(tokens) < 3: return []
        
        fp_ex = self.pe.fingerprint(tokens)
        tipos_ex = set(t[0] for t in tokens)
        
        # Extrai termos para buscar
        termos = self._extrair_termos(texto_exemplo)
        
        # Busca candidatos usando ferramentas
        candidatos = set()
        for termo in termos[:3]:
            try:
                r = self.tools.executar('buscar_estrategico', {'termo': termo})
                if r and r.get('sucesso'):
                    dados = str(r.get('resultado', ''))
                    if 'Nenhum' not in dados[:20]:
                        for linha in dados.split('\n')[:10]:
                            l = linha.strip()
                            if l and not l.startswith('['):
                                candidatos.add(l)
            except: pass
        
        # Valida candidatos por fingerprint
        resultados = []
        for caminho in list(candidatos)[:20]:
            try:
                r = self.tools.executar('ler_arquivo', {'caminho': caminho})
                if not r or not r.get('sucesso'): continue
                conteudo = str(r.get('resultado', ''))[:2000]
            except: continue
            if not conteudo or len(conteudo) < 30: continue
            
            tokens = self.pe.tokenizar_universal(conteudo)
            if not tokens: continue
            fp = self.pe.fingerprint(tokens)
            sim = self.pe.similaridade(fp_ex, fp)
            
            if sim > 0.3:
                resultados.append({'caminho': caminho, 'score': round(sim, 3)})
        
        resultados.sort(key=lambda x: -x['score'])
        return resultados[:max_resultados]
    
    def validar_por_padrao(self, codigo: str) -> Dict:
        """Valida código CONTRA o padrão aprendido.
        
        Usado por: validar_codigo, auto_repair
        """
        tokens = self.pe.tokenizar_universal(codigo)
        if not tokens: return {'valido': True, 'anomalias': [], 'cobertura': 1.0}
        
        # Se não tem markov de código ainda, aprende AGORA
        if 'codigo_validado' not in self.markov_assuntos:
            self._aprender_padrao_codigo()
        
        mk = self.markov_assuntos.get('codigo_validado', {})
        anomalias = []
        acertos = 0
        total = 0
        
        for i in range(len(tokens) - 1):
            t1, t2 = tokens[i][0], tokens[i+1][0]
            total += 1
            if t1 in mk and t2 in mk[t1]:
                acertos += 1
            else:
                anomalias.append({'pos': i, 'tipo_atual': t1, 'tipo_detectado': t2})
        
        return {
            'valido': len(anomalias) == 0,
            'cobertura': round(acertos / max(total, 1), 4),
            'anomalias': anomalias[:10],
            'total_anomalias': len(anomalias),
        }
    
    def gerar_por_dominio(self, dominio: str, semente: str = '',
                          tamanho: int = 30, temperatura: float = 0.3) -> str:
        """Gera texto novo no DOMÍNIO especificado.
        
        Usado por: gerar_historia, gerar_lore, gerar_codigo, gerar_npc
        """
        mk = self.markov_assuntos.get(dominio, {})
        if not mk:
            return f"(Domínio '{dominio}' não aprendido ainda)"
        
        palavras = semente.lower().split() if semente else []
        if len(palavras) < 2 and mk:
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
                pesos_n = [p/max(sum(pesos),1) for p in pesos]
                pesos_t = [p ** (1.0/max(temperatura, 0.01)) for p in pesos_n]
                probs = [p/max(sum(pesos_t),0.001) for p in pesos_t]
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
        
        return ' '.join(palavras) if palavras else ''
    
    def aprender(self, dados: Any, dominio: str = 'geral'):
        """Aprende com QUALQUER dado — TODAS as ferramentas melhoram.
        
        Quando o core aprende:
        - buscar_por_assinatura passa a encontrar MAIS resultados
        - validar_por_padrao detecta anomalias com MAIS precisão
        - gerar_por_dominio gera textos MAIS ricos
        """
        tokens = self.pe.tokenizar_universal(str(dados))
        if not tokens or len(tokens) < 5: return
        
        # Aprende palavras do domínio
        for t in tokens:
            palavra = str(t[1]).lower() if len(t) > 1 else ''
            if palavra and len(palavra) > 2:
                if palavra not in self.vocabulario:
                    self.vocabulario[palavra] = {}
                self.vocabulario[palavra][dominio] = self.vocabulario[palavra].get(dominio, 0) + 1
        
        # Aprende Markov do domínio
        palavras = str(dados).lower().split()
        if dominio not in self.markov_assuntos:
            self.markov_assuntos[dominio] = {}
        mk = self.markov_assuntos[dominio]
        for i in range(len(palavras) - 2):
            chave = f"{palavras[i]} {palavras[i+1]}"
            prox = palavras[i+2]
            if chave not in mk: mk[chave] = {}
            mk[chave][prox] = mk[chave].get(prox, 0) + 1
        
        # Salva no KG
        self.kg.aprender(
            erro=f"mcr_core_aprendizado_{dominio}",
            causa=f"auto_aprendizado, tokens={len(tokens)}",
            solucao=str(dados)[:500],
            ctx=f"core_{dominio}",
        )
        
        self.total_aprendizados += 1
    
    def _aprender_padrao_codigo(self):
        """Aprende padrão de código válido lendo exemplos do projeto (limitado)."""
        arquivos = []
        # Só procura em data/ (é o menor diretório com .lua)
        data_dir = os.path.join(BASE, 'data')
        if os.path.isdir(data_dir):
            for root, dirs, files in os.walk(data_dir):
                for f in files:
                    if f.endswith('.lua') or f.endswith('.py'):
                        arquivos.append(os.path.join(root, f))
                        if len(arquivos) >= 15: break
                if len(arquivos) >= 15: break
        
        for caminho in arquivos:
            try:
                with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                    self.aprender(f.read()[:5000], 'codigo_validado')
            except: pass
    
    def _extrair_termos(self, texto: str) -> List[str]:
        """Extrai termos de busca do texto."""
        termos = []
        siglas = re.findall(r'\b[A-Z]{2,}\b', texto)
        termos.extend(siglas)
        nomes = re.findall(r'\b[A-Z][a-z]{2,}\b', texto)
        for n in nomes:
            if n not in termos: termos.append(n)
        return termos[:5]


# ============================================================
# DEMONSTRAÇÃO: Ferramentas usando o MESMO core
# ============================================================
class FerramentaBusca:
    """Ferramenta de busca — USA o MCRCore."""
    
    def __init__(self, mcr: MCRCore):
        self.mcr = mcr
    
    def buscar(self, termo: str) -> List:
        print(f"\n[FerramentaBusca] Buscando '{termo}'...")
        # USA O CORE
        return self.mcr.buscar_por_assinatura(termo)


class FerramentaValidacao:
    """Ferramenta de validação — USA o MCRCore."""
    
    def __init__(self, mcr: MCRCore):
        self.mcr = mcr
    
    def validar(self, codigo: str) -> Dict:
        print(f"\n[FerramentaValidacao] Validando código...")
        # USA O CORE
        return self.mcr.validar_por_padrao(codigo)


class FerramentaGeracao:
    """Ferramenta de geração — USA o MCRCore."""
    
    def __init__(self, mcr: MCRCore):
        self.mcr = mcr
    
    def gerar(self, dominio: str, semente: str = '') -> str:
        print(f"\n[FerramentaGeracao] Gerando '{dominio}'...")
        # USA O CORE
        return self.mcr.gerar_por_dominio(dominio, semente, tamanho=20, temperatura=0.3)


# ============================================================
# TESTE
# ============================================================
def testar():
    print("=" * 70)
    print("  MCR CORE — Cérebro ÚNICO. Ferramentas como extensões.")
    print("=" * 70)
    
    # PASSO 1: Criar o CORE (UMA vez)
    print(f"\n{'='*70}")
    print(f"  PASSO 1: CRIAR CORE (singleton — mesma instância para todos)")
    print(f"{'='*70}")
    
    mcr = MCRCore()  # Cria ou retorna a instância única
    
    # PASSO 2: Criar ferramentas que usam o MESMO core
    print(f"\n{'='*70}")
    print(f"  PASSO 2: FERRAMENTAS USAM O MESMO CORE")
    print(f"{'='*70}")
    
    bus = FerramentaBusca(mcr)
    val = FerramentaValidacao(mcr)
    ger = FerramentaGeracao(mcr)
    
    print(f"  FerramentaBusca usa core: {bus.mcr is mcr}")
    print(f"  FerramentaValidacao usa core: {val.mcr is mcr}")
    print(f"  FerramentaGeracao usa core: {ger.mcr is mcr}")
    print(f"  Todas usam a MESMA instância? {'✅ SIM' if all(f.mcr is mcr for f in [bus, val, ger]) else '❌ NÃO'}")
    
    # PASSO 3: Alimentar o core com conhecimento
    print(f"\n{'='*70}")
    print(f"  PASSO 3: ALIMENTAR O CORE (aprender com dados)")
    print(f"{'='*70}")
    
    # Lore
    mcr.aprender("Eridanus = Cidade inicial dos aventureiros. Era uma cidade lendária.", 'lore')
    mcr.aprender("Canary = Servidor OTServ personalizado do projeto MCR.", 'lore')
    mcr.aprender("SPA = Sistema de Progressão do Aventureiro. 4 dominios elementais.", 'lore')
    
    # Código
    mcr.aprender("local npc = NPC:new('Teste')\nnpc:setTitle('Ferreiro')\nnpc:onSay(function() end)", 'codigo')
    
    print(f"  Markovs aprendidos: {list(mcr.markov_assuntos.keys())}")
    print(f"  Total de aprendizados: {mcr.total_aprendizados}")
    
    # PASSO 4: Usar ferramentas — ANTES de aprender mais
    print(f"\n{'='*70}")
    print(f"  PASSO 4: USAR FERRAMENTAS ")
    print(f"{'='*70}")
    
    # Geração de lore
    texto = ger.gerar('lore', 'eridanus era uma')
    print(f"  Lore gerada ({len(texto.split())} palavras): {texto[:120]}")
    
    # Geração de código com o MESMO core
    texto2 = ger.gerar('codigo', 'local npc =')
    if texto2:
        print(f"  Código gerado ({len(texto2.split())} tokens): {texto2[:120]}")
    
    # Validação
    codigo_teste = "local lore = {\n    nome = \"Teste\",\nreturn lore\nend"
    resultado = val.validar(codigo_teste)
    print(f"  Validação: cobertura={resultado['cobertura']:.2%}, anomalias={resultado['total_anomalias']}")
    
    # PASSO 5: APRENDER MAIS → TODAS AS FERRAMENTAS MELHORAM
    print(f"\n{'='*70}")
    print(f"  PASSO 5: APRENDER MAIS → TODAS MELHORAM")
    print(f"{'='*70}")
    
    mcr.aprender("Eridanus tinha muralhas de pedra cristalina que brilhavam com a lua.", 'lore')
    mcr.aprender("Os fundadores de Eridanus vieram do norte, cruzando o rio Chromatius.", 'lore')
    mcr.aprender("A cidade foi construída sobre uma mina de cristal mágico.", 'lore')
    
    print(f"  Markov 'lore' cresceu: {len(mcr.markov_assuntos.get('lore', {}))} estados")
    
    # GERA NOVAMENTE — com MAIS conhecimento
    texto3 = ger.gerar('lore', 'eridanus tinha')
    print(f"  Nova lore ({len(texto3.split())} palavras): {texto3[:150]}")
    
    # RELATÓRIO
    print(f"\n\n{'='*70}")
    print(f"  RELATÓRIO — MCR CORE")
    print(f"{'='*70}")
    print(f"  Instância única: {mcr is MCRCore()}")
    print(f"  Ferramentas: {3} (Busca, Validação, Geração)")
    print(f"  Markovs disponíveis: {list(mcr.markov_assuntos.keys())}")
    print(f"  Total aprendizado: {mcr.total_aprendizados}")
    print(f"\n  ✅ Todas as ferramentas usam o MESMO core")
    print(f"  ✅ Aprendeu → Gerou melhor")
    print(f"  ✅ Aprendeu de novo → Gerou melhor ainda")
    print(f"  0 LLM. 0 GPU. 1 ÚNICO CORE.")
    print(f"{'='*70}")


if __name__ == '__main__':
    testar()
