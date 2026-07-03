"""
CREW PATTERN v1.0 — Pipeline Universal
========================================
Padrao extraido da Context Crew, aplicavel a QUALQUER metodo:

   Analisar (Python/IA) → Pesquisar (Python) → Filtrar (Python) → Compactar (IA so se precisar)

Regras:
  1. Python faz o trabalho pesado (busca, filtro, score) — 0 IA
  2. KG (V12) responde se ja sabe — 0 IA
  3. IA so para sintese criativa — 1 chamada

Uso:
    from crew_pattern import CrewPipeline
    crew = CrewPipeline(kg, ia)
    resposta = crew.processar(
        pergunta="qualquer texto",
        fn_compactar=lambda ctx, pergunta: ia.gerar(f"...{ctx}...{pergunta}...")
    )
"""

import os, re, sys, json, urllib.request
from typing import Callable, Optional, Dict, Any, List

# Stop words centralizadas (evita duplicacao entre arquivos)
from stop_words import STOP_V12, STOP_BUSCA

OLLAMA_URL = 'http://localhost:11434/api/generate'

# ============================================================
# HELPERS
# ============================================================


def _termos_v12(texto: str) -> set:
    """Extrai keywords para V12 check (mais restritivo, tira artigos/preposicoes)."""
    return set(re.findall(r'\b[a-zA-Z]{3,}\b', texto.lower())) - STOP_V12


def _termos_busca(texto: str) -> set:
    """Extrai keywords para busca (mais abrangente)."""
    return set(re.findall(r'\b[a-zA-Z_]{3,}\b', texto.lower())) - STOP_BUSCA


def _ollama_fast(prompt: str, temp: float = 0.1,
                 modelo: str = None,
                 ctx: int = 2048) -> Optional[str]:
    """Chamada ao modelo via router padronizado."""
    try:
        from modulos.util import fast as _util_fast
        return _util_fast(prompt, temp, "fast") or None
    except:
        return None


# ============================================================
# CLASSE PRINCIPAL
# ============================================================

class CrewPipeline:
    """
    Pipeline universal: analisar → pesquisar → filtrar → compactar.
    
    Funciona como um "decorator" de metodos:
        resposta = crew.processar(pergunta, fn_compactar=...)
    
    Se V12 encontrar resposta direta no KG, retorna SEM chamar fn_compactar.
    Se ContextCrew disponivel, injeta contexto.
    """

    def __init__(self, kg=None, ia=None, ctx_crew=None, verbose=True):
        self.kg = kg
        self.ia = ia
        self.ctx_crew = ctx_crew
        self.verbose = verbose
        self.stats = {"v12_hits": 0, "crew_hits": 0, "fallbacks": 0, "total": 0}
    
    def processar(self,
                  pergunta: str,
                  fn_compactar: Callable = None,
                  fn_extrair: Callable = None,
                  fn_buscar: Callable = None,
                  fontes: list = None,
                  usar_v12: bool = True,
                  usar_crew: bool = True) -> Optional[str]:
        """
        Pipeline universal.
        
        Args:
            pergunta: str — descricao do que precisa ser feito
            fn_compactar: callable(contexto, pergunta) -> str or None
                SINTETIZA a resposta final. UNICA chamada IA se necessario.
                Se None, retorna o contexto encontrado.
            fn_extrair: callable(pergunta) -> set of keywords
                Se None, usa _termos_busca() padrao.
            fn_buscar: callable(keywords, contexto_crew) -> list of resultados
                Se None, usa KG.buscar() padrao.
            fontes: list — fontes para ContextCrew (ex: ['kg', 'docs'])
            usar_v12: bool — se deve verificar KG antes de chamar IA
            usar_crew: bool — se deve usar ContextCrew
        
        Returns:
            str or None
        """
        self.stats["total"] += 1
        
        # --- FASE 0: V12 — Se KG ja sabe, responde direto (0 IA) ---
        if usar_v12 and self.kg:
            r_v12 = self._v12_check(pergunta)
            if r_v12:
                if self.verbose:
                    print(f'  [CrewPipeline] V12: resposta direta do KG')
                self.stats["v12_hits"] += 1
                return r_v12
        
        # --- FASE 1: ContextCrew — pesquisa contexto em tempo real ---
        contexto_crew = ""
        if usar_crew and self.ctx_crew:
            try:
                ctx = self.ctx_crew.executar(pergunta)
                if ctx:
                    contexto_crew = ctx
                    if self.verbose:
                        print(f'  [CrewPipeline] ContextCrew: {len(ctx)//2} tokens')
            except Exception as e:
                if self.verbose:
                    print(f'  [CrewPipeline] ContextCrew erro: {e}')
        
        # --- FASE 2: Extrair termos (Python, 0 IA) ---
        termos = fn_extrair(pergunta) if fn_extrair else _termos_busca(pergunta)
        
        # --- FASE 3: Buscar contexto ---
        contexto_busca = None
        if fn_buscar:
            contexto_busca = fn_buscar(termos, contexto_crew)
        elif self.kg:
            r_kg = self.kg.buscar(pergunta)
            if r_kg:
                contexto_busca = '\n'.join(
                    f'- {l["solucao"]}' for l in r_kg
                )
        
        # --- FASE 4: Compactar — SO IA AQUI ---
        contexto_final = ""
        if contexto_crew:
            contexto_final += contexto_crew + "\n\n"
        if contexto_busca:
            contexto_final += str(contexto_busca)
        
        if fn_compactar and contexto_final.strip():
            resposta = fn_compactar(contexto_final, pergunta)
            if resposta:
                self.stats["crew_hits"] += 1
                return resposta
        
        # Se nao tem compactar, retorna o contexto encontrado
        if contexto_final.strip():
            self.stats["crew_hits"] += 1
            return contexto_final
        
        self.stats["fallbacks"] += 1
        return None
    
    def _v12_check(self, pergunta: str) -> Optional[str]:
        """V12: se KG tem resposta direta, retorna sem chamar IA."""
        if not self.kg:
            return None
        r_kg = self.kg.buscar(pergunta)
        if not r_kg:
            return None
        kwargs = _termos_v12(pergunta)
        if not kwargs:
            return None
        for l in r_kg:
            sol = l.get("solucao", "").lower()
            matches = sum(1 for t in kwargs if t in sol)
            if matches >= 2 or (len(kwargs) == 1 and list(kwargs)[0] in sol):
                return l["solucao"]
        return None
    
    def get_stats(self) -> Dict:
        s = dict(self.stats)
        if s["total"] > 0:
            s["v12_pct"] = round(s["v12_hits"] / s["total"] * 100)
            s["crew_pct"] = round(s["crew_hits"] / s["total"] * 100)
            s["fallback_pct"] = round(s["fallbacks"] / s["total"] * 100)
        return s
    
    def reset_stats(self):
        self.stats = {"v12_hits": 0, "crew_hits": 0, "fallbacks": 0, "total": 0}


# ============================================================
# GREP PIPELINE — Busca em arquivos com score matematico
# ============================================================

def grep_pipeline(pergunta: str, sandbox_dir: str,
                  extensoes: list = None,
                  max_resultados: int = 10) -> list:
    """
    Busca arquivos por termos extraidos da pergunta.
    Score matematico (0 IA): nome do arquivo + conteudo.
    
    Retorna: lista de dicts {'arquivo', 'trecho', 'termo', 'score'}
    """
    if extensoes is None:
        extensoes = ['.py', '.lua', '.ts', '.js', '.md', '.xml', '.json', '.txt']
    
    termos = _termos_busca(pergunta)
    if not termos:
        return []
    
    encontrados = []
    
    for ext in extensoes:
        for root, dirs, files in os.walk(sandbox_dir):
            # Pular diretorios de sistema
            if any(p in root for p in ['node_modules', '.git', '__pycache__',
                                        '.venv', 'venv', 'env']):
                continue
            for f in files:
                if not f.endswith(ext):
                    continue
                
                path = os.path.join(root, f)
                try:
                    with open(path, encoding='utf-8', errors='replace') as fh:
                        conteudo = fh.read(2000)  # Le so o inicio
                except Exception as e:
                    print(f"[Fix] ERRO: {e}")
                
                conteudo_lower = conteudo.lower()
                nome_lower = f.lower()
                
                # Score: match no nome (peso 3) + match no conteudo (peso 1)
                for termo in termos:
                    score = 0
                    if termo.lower() in nome_lower:
                        score += 3
                    if termo.lower() in conteudo_lower:
                        score += 1
                    if score > 0:
                        trecho = conteudo.replace('\n', ' ').strip()
                        encontrados.append({
                            'arquivo': f,
                            'caminho': path,
                            'trecho': trecho,
                            'termo': termo,
                            'score': score
                        })
                        break
                
                if len(encontrados) >= max_resultados:
                    break
            if len(encontrados) >= max_resultados:
                break
        if len(encontrados) >= max_resultados:
            break
    
    # Ordena por score decrescente
    encontrados.sort(key=lambda e: -e['score'])
    return encontrados


# ============================================================
# TESTE RAPIDO
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  CREW PIPELINE — Teste")
    print("=" * 50)
    
    # Teste do grep_pipeline
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    # Criar arquivos de teste
    arquivos_teste = {
        "teste_npc.lua": "-- NPC: Zoltan\nlocal npc = NPC('Zoltan')\nnpc:setSaudacao('Ola!')\n",
        "teste_monster.lua": "-- Monster: Dragon\nlocal mon = Monster('Dragon')\nmon:setHealth(5000)\n",
        "utils.py": "def helper():\n    return 42\n",
    }
    
    for nome, conteudo in arquivos_teste.items():
        with open(os.path.join(tmpdir, nome), 'w', encoding='utf-8') as f:
            f.write(conteudo)
    
    # Testar busca
    resultados = grep_pipeline("criar NPC Zoltan", tmpdir)
    print("Busca por 'criar NPC Zoltan':")
    for r in resultados:
        print(f"  score={r['score']} {r['arquivo']}: {r['trecho']}")
    
    print("\nBusca por 'helper function':")
    resultados = grep_pipeline("helper function", tmpdir)
    for r in resultados:
        print(f"  score={r['score']} {r['arquivo']}: {r['trecho']}")
    
    print("\n[OK] Testes basicos do grep pipeline")
