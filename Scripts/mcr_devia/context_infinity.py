"""
CONTEXT INFINITY - Orquestrador de Contexto com IA-Crew
Gerencia o que entra e sai do contexto ativo do MCR-DevIA.

Arquitetura:
  Fragmento Entrando
       ↓
  ┌── ORQUESTRADOR ───────────────────────────────┐
  │                                                │
  │  1. ADICIONADOR:                               │
  │     - Recebe novo fragmento                    │
  │     - Calcula prioridade (relevancia + urgencia)│
  │     - Se contexto lotado, chama REMOVEDOR      │
  │                                                │
  │  2. REMOVEDOR:                                 │
  │     - Identifica fragmento de menor prioridade │
  │     - Salva resumo no KG (nunca perde dados)   │
  │     - Remove do contexto ativo                 │
  │                                                │
  │  3. INDEXADOR:                                 │
  │     - Mantem indice do que esta no contexto    │
  │     - Permite busca rapida sem carregar tudo   │
  │                                                │
  │  4. SUPERVISOR:                                │
  │     - Verifica se algo importante foi removido │
  │     - Se sim, re-adiciona com prioridade maior │
  │     - Log de todas as operacoes                │
  └────────────────────────────────────────────────┘
       ↓
  Contexto Ativo (otimizado para o modelo atual)

Todas as decisoes sao V12: Python estrutura, IA preenche blanks.
Mas a MAIORIA das decisoes sao regras Python (prioridade, relevancia).
IA so e chamada para: "este fragmento e relevante para a pergunta?"
"""
import json, time, os, sys
from typing import List, Dict, Any, Optional

# Contexto maximo por modelo (via Model Router)
CTX_POR_MODELO = {
    "qwen2.5-coder:1.5b": 2048,
    "qwen2.5-coder:7b": 8192,
    "deepseek-r1:7b": 8192,
    "llama3.1:8b": 8192,
}

class FragmentoContexto:
    """Um fragmento de informacao no contexto ativo."""
    def __init__(self, id: str, conteudo: str, origem: str = "",
                 prioridade: int = 0, tipo: str = "texto",
                 tokens_estimados: int = 0, tags: list = None):
        self.id = id
        self.conteudo = conteudo
        self.origem = origem
        self.prioridade = prioridade  # 0-100 (mais alto = mais importante)
        self.tipo = tipo  # texto, codigo, json, kg_lesson, resultado
        self.tokens = tokens_estimados or len(conteudo) // 2
        self.acessos = 0
        self.criado_em = time.time()
        self.ultimo_acesso = time.time()
        self.resumo = ""  # Resumo salvo no KG se removido
        self._tags = tags or []  # Tags para busca (nova)
     
    def registrar_acesso(self):
        """Registra que este fragmento foi acessado."""
        self.acessos += 1
        self.ultimo_acesso = time.time()
        self.prioridade = min(100, self.prioridade + 2)


class OrquestradorContexto:
    """
    Gerencia o contexto ativo: adiciona, remove, supervisiona.
    
    Uso:
        ctx = OrquestradorContexto()  # usa modelo do router padronizado
        ctx.adicionar(fragmento)
        ctx.adicionar(outro_fragmento)
        contexto_otimizado = ctx.otimizar(pergunta_atual)
        resposta = modelo(contexto_otimizado)
    """
    
    def __init__(self, modelo: str = None,
                 kg_path: str = None):
        if modelo is None:
            try:
                from modulos.util import _get_modelo
                cfg = _get_modelo("leve")
                modelo = cfg["modelo"]
            except:
                modelo = "qwen2.5-coder:7b"  # fallback seguro
        self.modelo = modelo
        self.ctx_max = CTX_POR_MODELO.get(modelo, 2048)
        self.fragmentos: Dict[str, FragmentoContexto] = {}
        self.indice: Dict[str, List[str]] = {}  # termo -> [ids_fragmentos]
        self.historico_remocoes: List[Dict] = []
        
        # Carrega KG se disponivel
        self.kg = None
        if kg_path and os.path.exists(kg_path):
            try:
                with open(kg_path, encoding='utf-8') as f:
                    self.kg = json.load(f)
            except: pass
    
    # ----------------------------------------------------------
    # ADICIONADOR
    # ----------------------------------------------------------
    def adicionar(self, fragmento: FragmentoContexto) -> bool:
        """Adiciona fragmento ao contexto ativo.
        Se nao couber, chama REMOVEDOR para abrir espaco."""
        if fragmento.id in self.fragmentos:
            return True  # Ja existe, nao duplica
        
        tokens_livres = self._tokens_livres()
        
        if fragmento.tokens <= tokens_livres:
            # Cabe direto
            self._inserir(fragmento)
            return True
        
        # Nao cabe: precisa remover algo
        removidos = self._liberar_espaco(fragmento.tokens)
        
        if self._tokens_livres() >= fragmento.tokens:
            self._inserir(fragmento)
            return True
        
        # Mesmo removendo, nao cabe: fragmento muito grande
        # Solucao: fragmentar de novo
        print(f"  [Contexto] Fragmento {fragmento.id} muito grande ({fragmento.tokens} tokens)")
        return False
    
    def _tokens_livres(self) -> int:
        """Calcula tokens disponiveis no contexto."""
        usados = sum(f.tokens for f in self.fragmentos.values())
        return max(0, self.ctx_max - usados)
    
    def _inserir(self, fragmento: FragmentoContexto):
        """Insere fragmento e atualiza indice."""
        self.fragmentos[fragmento.id] = fragmento
        # Indexar termos
        termos = set(fragmento.conteudo.lower().split()[:50])
        for termo in termos:
            if len(termo) > 3:
                if termo not in self.indice:
                    self.indice[termo] = []
                self.indice[termo].append(fragmento.id)
    
    # ----------------------------------------------------------
    # REMOVEDOR
    # ----------------------------------------------------------
    def _liberar_espaco(self, tokens_necessarios: int) -> List[FragmentoContexto]:
        """Remove fragmentos de menor prioridade ate ter espaco."""
        removidos = []
        
        # Ordenar por prioridade (menor primeiro), depois por ultimo acesso
        candidatos = sorted(
            self.fragmentos.values(),
            key=lambda f: (f.prioridade, f.ultimo_acesso)
        )
        
        while candidatos and self._tokens_livres() < tokens_necessarios:
            frag = candidatos.pop(0)
            if frag.prioridade >= 50:  # Nao remover se prioridade media-alta
                break
            
            # Salva resumo no KG antes de remover
            self._salvar_resumo(frag)
            
            # Remove do contexto ativo
            del self.fragmentos[frag.id]
            self.historico_remocoes.append({
                "id": frag.id,
                "origem": frag.origem,
                "prioridade": frag.prioridade,
                "tokens": frag.tokens,
                "acessos": frag.acessos,
                "removido_em": time.time()
            })
            removidos.append(frag)
        
        return removidos
    
    def _salvar_resumo(self, fragmento: FragmentoContexto):
        """Salva resumo do fragmento removido no KG (nunca perde dados)."""
        if self.kg is not None and fragmento.conteudo:
            # Cria resumo: primeiras e ultimas linhas
            linhas = fragmento.conteudo.split('\n')
            if len(linhas) > 6:
                resumo = '\n'.join(linhas[:3] + ['...'] + linhas[-3:])
            else:
                resumo = fragmento.conteudo[:200]
            fragmento.resumo = resumo
            # Registra no KG (se tiver acesso)
            try:
                self.kg["licoes"].append({
                    "id": f"CTX_{fragmento.id[:8]}",
                    "erro": f"Contexto removido: {fragmento.origem}",
                    "causa": f"Prioridade {fragmento.prioridade}, {fragmento.acessos} acessos",
                    "solucao": resumo,
                    "ctx": "contexto_removido"
                })
            except: pass
    
    # ----------------------------------------------------------
    # INDEXADOR
    # ----------------------------------------------------------
    def buscar(self, termo: str) -> List[str]:
        """Busca fragmentos por termo no indice."""
        return self.indice.get(termo.lower(), [])
    
    def buscar_fragmentos(self, pergunta: str, max_result: int = 3) -> List[FragmentoContexto]:
        """Busca fragmentos relevantes para uma pergunta.
        Usa o indice + prioridade para encontrar os melhores."""
        termos = set(pergunta.lower().split())
        scores = {}
        
        for termo in termos:
            if len(termo) < 3: continue
            for frag_id in self.indice.get(termo, []):
                if frag_id not in scores:
                    scores[frag_id] = 0
                scores[frag_id] += 1
        
        # Ordenar por score + prioridade
        resultados = []
        for frag_id, score in sorted(scores.items(), key=lambda x: -x[1]):
            frag = self.fragmentos.get(frag_id)
            if frag:
                frag.registrar_acesso()
                resultados.append((score + frag.prioridade/10, frag))
        
        resultados.sort(key=lambda x: -x[0])
        return [r[1] for r in resultados[:max_result]]
    
    # ----------------------------------------------------------
    # SUPERVISOR
    # ----------------------------------------------------------
    def supervisionar(self) -> List[str]:
        """Verifica se algo importante foi removido sem necessidade.
        Retorna lista de inconsistencias encontradas."""
        inconsistencias = []
        
        # Verifica se algum fragmento removido tinha alta prioridade
        for remocao in self.historico_remocoes[-20:]:  # Ultimas 20
            if remocao["prioridade"] > 60:
                inconsistencias.append(
                    f"Fragmento {remocao['id']} (prioridade {remocao['prioridade']}) "
                    f"foi removido mas tinha alta prioridade"
                )
                # Re-adiciona com prioridade maior
                # (precisaria do conteudo original - salvo no KG)
        
        # Verifica fragmentos com baixo acesso mas alta prioridade
        for frag in self.fragmentos.values():
            if frag.prioridade > 70 and frag.acessos < 2:
                inconsistencias.append(
                    f"Fragmento {frag.id} tem alta prioridade ({frag.prioridade}) "
                    f"mas so {frag.acessos} acessos"
                )
        
        return inconsistencias
    
    # ----------------------------------------------------------
    # OTIMIZACAO PARA RESPOSTA
    # ----------------------------------------------------------
    def montar_contexto_para_resposta(self, pergunta: str) -> str:
        """Monta o contexto otimizado para gerar uma resposta.
        1. Busca fragmentos relevantes para a pergunta
        2. Adiciona contexto do KG (se houver)
        3. Junta tudo respeitando o limite de tokens"""
        
        # Fragmentos relevantes
        relevantes = self.buscar_fragmentos(pergunta, max_result=5)
        
        # Monta contexto
        partes = []
        tokens_usados = 0
        
        # Primeiro: lessons do KG (mais importantes - usando scoring)
        if self.kg:
            stop_words = {'que','para','com','como','mais','mas','por','dos','das','era','sao',
                          'isso','entre','sobre','antes','depois','tem','ser','seu','sua','todo',
                          'pode','muito','pouco','quando','onde','assim','apos','ate','sem','sob',
                          'fazer','ter','estar','ficar','ainda','bem','ja','nao','sim','vai','foi',
                          'em','e','o','a','de','da','do','no','na','um','uma','leia','arquivo'}
            termos_pergunta = [t.lower() for t in pergunta.split() if len(t) > 3 and t.lower() not in stop_words]
            lessons_relevantes = []
            for l in self.kg.get("licoes", []):
                sol = l.get("solucao","").lower()
                # Score = quantos termos da pergunta aparecem na solucao
                score = sum(1 for t in termos_pergunta if t in sol)
                if score >= 2:  # Precisa de pelo menos 2 matches
                    lessons_relevantes.append((score, sol))
            # Ordenar por score decrescente, pegar as melhores
            lessons_relevantes.sort(key=lambda x: -x[0])
            for score, sol in lessons_relevantes[:3]:
                tk = len(sol) // 2
                if tokens_usados + tk < self.ctx_max and score >= 2:
                    partes.append(f"[KG] {sol}")
                    tokens_usados += tk
        
        # Depois: fragmentos do contexto ativo
        for frag in relevantes:
            if tokens_usados + frag.tokens < self.ctx_max:
                partes.append(frag.conteudo)
                tokens_usados += frag.tokens
        
        return '\n\n'.join(partes)
    
    # ----------------------------------------------------------
    # ESTATISTICAS
    # ----------------------------------------------------------
    def stats(self) -> dict:
        """Retorna metricas do orquestrador."""
        return {
            "modelo": self.modelo,
            "ctx_max": self.ctx_max,
            "fragmentos_ativos": len(self.fragmentos),
            "tokens_ativos": sum(f.tokens for f in self.fragmentos.values()),
            "tokens_livres": self._tokens_livres(),
            "indice_termos": len(self.indice),
            "remocoes_total": len(self.historico_remocoes),
            "fragmentos": [
                {"id": f.id, "prio": f.prioridade, "tokens": f.tokens,
                 "acessos": f.acessos, "origem": f.origem}
                for f in sorted(self.fragmentos.values(),
                               key=lambda x: -x.prioridade)[:10]
            ]
        }


# ============================================================
# SESSION CACHE — Novo: sem limite, absorve tudo, pesca sob demanda
# ============================================================

class SessionCache:
    """Cache de sessao que ABSORVE tudo sem limite.
    
    Diferenca do OrquestradorContexto:
    - Nao tem ctx_max (guarda em RAM ate o fim da execucao)
    - Nunca remove fragmentos — acumula infinitamente
    - pescar() retorna SO o relevante para o prompt do LLM
    - Suporta tags, tipos, busca textual e reconstrucao de estado
    - Cada passo do MasterAgent escreve automaticamente
    
    Uso:
        cache = SessionCache()
        cache.absorver('request', 'Cria um jogo', 'request', tags=['projeto'])
        cache.absorver('codigo_1', 'print("hello")', 'codigo', tags=['python'])
        relevantes = cache.pescar(pergunta='cria jogo', tipos=['request'], max_tokens=500)
        estado = cache.reconstruir()  # volta no tempo
    """
    
    def __init__(self):
        self.fragmentos: Dict[str, FragmentoContexto] = {}
        self.indice: Dict[str, List[str]] = {}
        self.historico: List[dict] = []
    
    def _calcular_prioridade(self, tipo, tags):
        """Calcula prioridade baseado no tipo e tags."""
        prioridades = {
            'request': 100, 'plano': 90, 'codigo': 80,
            'resultado': 70, 'explicacao': 60, 'contexto': 50,
            'melhoria': 75, 'log': 30, 'debug': 20,
        }
        return prioridades.get(tipo, 50)
    
    def _indexar(self, frag):
        """Indexa termos do fragmento para busca rapida."""
        termos = set(frag.conteudo.lower().split()[:50])
        for termo in termos:
            if len(termo) > 3:
                if termo not in self.indice:
                    self.indice[termo] = []
                self.indice[termo].append(frag.id)
    
    def absorver(self, id, conteudo, tipo="texto", tags=None, origem=""):
        """Absorve um fragmento. NUNCA remove, nunca perde.
        
        Se o id ja existe, atualiza o conteudo e aumenta prioridade
        (significa que o conhecimento foi refinado).
        """
        if id in self.fragmentos:
            frag = self.fragmentos[id]
            frag.conteudo = conteudo
            frag.prioridade = min(100, frag.prioridade + 5)
            frag.ultimo_acesso = time.time()
            if tags:
                frag._tags = list(set(frag._tags + tags))
            self.historico.append({'ts': time.time(), 'acao': 'atualizar', 'id': id})
            return
        
        prioridade = self._calcular_prioridade(tipo, tags)
        frag = FragmentoContexto(id, conteudo, origem, prioridade, tipo,
                                 tags=tags or [])
        self.fragmentos[id] = frag
        self._indexar(frag)
        self.historico.append({'ts': time.time(), 'acao': 'absorver', 'id': id, 'tipo': tipo})
    
    def pescar(self, pergunta="", tipos=None, tags=None, n=3, max_tokens=800):
        """Pesca fragmentos relevantes. Retorna SO o necessario para o prompt.
        
        Args:
            pergunta: Texto da consulta (para match textual)
            tipos: Filtrar por tipo ('codigo', 'explicacao', 'resultado')
            tags: Filtrar por tags (['python', 'pygame', 'entities'])
            n: Maximo de fragmentos
            max_tokens: Limite de tokens para o prompt (opcional)
        Returns:
            Lista de FragmentoContexto mais relevantes
        """
        candidatos = list(self.fragmentos.values())
        
        # Filtro por tipo
        if tipos:
            candidatos = [f for f in candidatos if f.tipo in tipos]
        
        # Filtro por tags
        if tags:
            candidatos = [f for f in candidatos 
                         if f._tags and any(t in f._tags for t in tags)]
        
        # Score por pergunta (match textual)
        if pergunta and candidatos:
            termos = set(pergunta.lower().split())
            scores = []
            for frag in candidatos:
                score = sum(1 for t in termos 
                          if len(t) > 3 and t in frag.conteudo.lower())
                if score > 0:
                    score += frag.prioridade / 10
                    score += frag.acessos / 100
                    scores.append((score, frag))
                    frag.registrar_acesso()
            scores.sort(key=lambda x: -x[0])
            candidatos = [s[1] for s in scores]
        
        # Se tem pergunta mas ninguem matched, retorna os mais recentes
        if pergunta and not candidatos:
            candidatos = sorted(self.fragmentos.values(), 
                               key=lambda f: f.ultimo_acesso, reverse=True)[:n]
        
        # Limite por tokens (opcional)
        if max_tokens and candidatos:
            resultado = []
            tokens = 0
            for frag in candidatos:
                if tokens + frag.tokens <= max_tokens:
                    resultado.append(frag)
                    tokens += frag.tokens
            return resultado
        
        return candidatos[:n]
    
    def precarregar(self, kg=None, request="", memorias=None):
        """Preenche o cache com conhecimento relevante ANTES da execucao.
        
        1. Lessons do KG (keyword match) — ate 5
        2. Lessons do KG (embedding semantico) — ate 5
        3. Episodios similares da memoria — ate 3
        4. ContextCrew (docs, codigo fonte) — ate 3
        
        Chame ANTES de executar qualquer tarefa para que o cache
        ja tenha contexto sobre o dominio do problema.
        """
        if not request:
            return 0
        
        count = 0
        
        # 1. KG keyword
        if kg:
            try:
                for l in kg.buscar(request, max_r=10)[:5]:
                    lid = l.get('id', '')
                    if f'kg_{lid}' not in self.fragmentos:
                        self.absorver(f'kg_{lid}', 
                            f"{l.get('erro','')}: {l.get('solucao','')}",
                            'contexto', tags=['kg', l.get('ctx','')], origem='kg_preload')
                        count += 1
            except Exception:
                pass
            
            # 2. KG embedding
            try:
                if hasattr(kg, 'buscar_por_embedding'):
                    for l in kg.buscar_por_embedding(request, n=5):
                        lid = l.get('id', '')
                        if f'kg_{lid}' not in self.fragmentos:
                            self.absorver(f'kg_{lid}',
                                f"{l.get('erro','')}: {l.get('solucao','')}",
                                'contexto', tags=['kg', 'embedding'], origem='kg_embedding')
                            count += 1
            except Exception:
                pass
        
        # 3. Memorias
        if memorias:
            try:
                for i, m in enumerate(memorias[:3]):
                    licao = str(m.get('licao', '')) if isinstance(m, dict) else str(m)
                    if licao:
                        self.absorver(f'memoria_{i}', licao, 'contexto',
                                      tags=['memoria'], origem='memoria_preload')
                        count += 1
            except Exception:
                pass
        
        # 4. ContextCrew
        try:
            from context_crew import ContextCrew
            crew = ContextCrew()
            ctx = crew.buscar(request, max_r=3)
            if ctx:
                textos = [t[0] if isinstance(t, tuple) else str(t) for t in ctx]
                self.absorver('context_crew', '\n'.join(textos), 'contexto',
                              tags=['contextcrew'], origem='crew_preload')
                count += 1
        except Exception:
            pass
        
        return count

    def reconstruir(self, tags=None, tipos=None, max_chars=3000):
        """Reconstroi o estado completo da sessao.
        
        Permite 'voltar no tempo' e reconstruir qualquer parte
        do que foi feito, porque TUDO foi absorvido.
        """
        filtrados = self.pescar(tags=tags, tipos=tipos, n=50, max_tokens=None)
        partes = []
        chars = 0
        for f in filtrados:
            trecho = f"{f.tipo.upper()}: {f.conteudo[:500]}"
            if chars + len(trecho) <= max_chars:
                partes.append(trecho)
                chars += len(trecho)
        return '\n\n'.join(partes) if partes else "(vazio)"
    
    def metricas(self):
        """Retorna metricas do cache."""
        return {
            'fragmentos': len(self.fragmentos),
            'termos_indexados': len(self.indice),
            'eventos_historico': len(self.historico),
            'tokens_total': sum(f.tokens for f in self.fragmentos.values()),
        }


# ============================================================
# TESTE
# ============================================================
if __name__ == "__main__":
    print("=== CONTEXT INFINITY - TESTE ===\n")
    
    ctx = OrquestradorContexto(modelo="qwen2.5-coder:7b")
    
    # Adicionar varios fragmentos
    ctx.adicionar(FragmentoContexto("f1", "Sistema de Habilidades Contextuais (SHC): 5 camadas", "kg", 90, "kg"))
    ctx.adicionar(FragmentoContexto("f2", "def validar_item(item): return item.get('article') == 'um'", "codigo", 70, "codigo"))
    ctx.adicionar(FragmentoContexto("f3", "SPA = Sistema de Progressao do Aventureiro", "kg", 80, "kg"))
    ctx.adicionar(FragmentoContexto("f4", "Eridanus e a cidade inicial do MCR", "kg", 60, "kg"))
    ctx.adicionar(FragmentoContexto("f5", "items.xml: 17019 itens extraidos", "dados", 50, "dados"))
    
    # Simular acesso
    ctx.fragmentos["f1"].registrar_acesso()
    ctx.fragmentos["f1"].registrar_acesso()
    ctx.fragmentos["f3"].registrar_acesso()
    
    print(f"Fragmentos ativos: {len(ctx.fragmentos)}")
    print(f"Tokens usados: {sum(f.tokens for f in ctx.fragmentos.values())}/{ctx.ctx_max}")
    
    # Buscar por SHC
    print(f"\nBuscando 'SHC': {ctx.buscar('shc')}")
    print(f"Buscando 'eridanus': {ctx.buscar('eridanus')}")
    
    # Contexto para uma pergunta
    print(f"\nContexto para 'O que e SHC?':")
    print(ctx.montar_contexto_para_resposta("O que e SHC?")[:300])
    
    # Supervisionar
    inc = ctx.supervisionar()
    print(f"\nSupervisor: {len(inc)} inconsistencias")
    
    # Stats
    stats = ctx.stats()
    print(f"\nStats: {json.dumps(stats, indent=2)[:500]}")
