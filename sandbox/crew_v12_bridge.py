"""MCR-DevIA — Crew-V12 Bridge
Cada Crew como um MCR-DevIA completo:
  - Scanner especifico do dominio
  - KG proprio + acesso ao KG compartilhado
  - Auto-fixer do dominio
  - Benchmark de performance"""
import os, json, subprocess, sys, time

KG_PATH = r"E:\Projeto MCR\sandbox\.mcr_devia\knowledge.json"
CREW_KG_DIR = r"E:\Projeto MCR\sandbox\.mcr_devia\crews"

class CrewV12:
    """Cada instancia é uma Crew que sabe V12."""
    
    def __init__(self, nome, escopo, detectores=None):
        self.nome = nome
        self.escopo = escopo  # "narrator", "analyst", "implementer", "validator", "professor"
        self.detectores = detectores or []
        self.kg_pessoal = self._carregar_kg_pessoal()
        self.kg_compartilhado = self._carregar_kg_compartilhado()
        self.metricas = {"acertos": 0, "erros": 0, "benchmarks": []}
    
    def _carregar_kg_pessoal(self):
        path = os.path.join(CREW_KG_DIR, f"{self.nome}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return {"lessons": [], "dominio": self.escopo, "benchmarks": []}
    
    def _salvar_kg_pessoal(self):
        os.makedirs(CREW_KG_DIR, exist_ok=True)
        path = os.path.join(CREW_KG_DIR, f"{self.nome}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.kg_pessoal, f, indent=2, ensure_ascii=False)
    
    def _carregar_kg_compartilhado(self):
        if os.path.exists(KG_PATH):
            with open(KG_PATH, encoding="utf-8") as f:
                return json.load(f)
        return {"lessons": []}
    
    def aprender(self, contexto, antes, depois, score=1.0):
        """Registra aprendizado no KG pessoal + compartilhado."""
        lesson = {
            "context": f"crew_{self.nome}_{contexto}",
            "antes": antes[:200],
            "depois": depois[:200],
            "score": score,
            "benchmark": len(self.metricas["benchmarks"])
        }
        self.kg_pessoal.setdefault("lessons", []).append(lesson)
        
        # Se score alto, compartilha com KG global
        if score >= 0.8:
            self.kg_compartilhado.setdefault("lessons", []).append({
                **lesson,
                "crew_origem": self.nome
            })
            with open(KG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.kg_compartilhado, f, indent=2, ensure_ascii=False)
        
        self._salvar_kg_pessoal()
        self.metricas["acertos"] += 1
    
    def registrar_erro(self, contexto, erro):
        """Aprende com erros tambem."""
        lesson = {
            "context": f"crew_{self.nome}_erro_{contexto}",
            "erro": str(erro)[:200],
            "contra_exemplo": True
        }
        self.kg_pessoal.setdefault("lessons", []).append(lesson)
        self._salvar_kg_pessoal()
        self.metricas["erros"] += 1
    
    def benchmark(self, nome_teste, resultado_antes, resultado_depois, metrica):
        """Registra benchmark de comparacao."""
        entry = {
            "teste": nome_teste,
            "antes": resultado_antes,
            "depois": resultado_depois,
            "melhoria": metrica,
            "timestamp": time.time()
        }
        self.kg_pessoal.setdefault("benchmarks", []).append(entry)
        self.metricas["benchmarks"].append(entry)
        self._salvar_kg_pessoal()
        
        # Se melhoria significativa, propaga para outras crews
        if metrica > 0.2:  # 20% de melhoria
            self._propagar_benchmark(entry)
    
    def _propagar_benchmark(self, entry):
        """Compartilha descoberta com outras crews via KG compartilhado."""
        lesson = {
            "context": "benchmark_cross_crew",
            "crew_origem": self.nome,
            "teste": entry["teste"],
            "melhoria": entry["melhoria"],
            "detalhe": f"{self.nome} melhorou {entry['teste']} em {entry['melhoria']*100:.0f}%"
        }
        self.kg_compartilhado.setdefault("lessons", []).append(lesson)
        with open(KG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.kg_compartilhado, f, indent=2, ensure_ascii=False)
    
    def relatorio(self):
        print(f"\n  === Crew: {self.nome} ({self.escopo}) ===")
        print(f"  KG pessoal: {len(self.kg_pessoal.get('lessons',[]))} lessons")
        print(f"  Benchmarks: {len(self.metricas['benchmarks'])}")
        print(f"  Acertos/Erros: {self.metricas['acertos']}/{self.metricas['erros']}")
        if self.metricas['benchmarks']:
            print(f"  Ultimo benchmark: {self.metricas['benchmarks'][-1]['teste']}")
            print(f"    Melhoria: {self.metricas['benchmarks'][-1]['melhoria']*100:.0f}%")


class MetaSupervisor:
    """Supervisiona as crews, coordena swaps de estrategia, executa benchmarks."""
    
    def __init__(self):
        self.crews = {}
        self._registrar_crews_padrao()
    
    def _registrar_crews_padrao(self):
        # Cada crew com detectores especificos do seu dominio
        self.crews = {
            "narrador": CrewV12("narrador", "narrativa", ["detectar_encoding", "detectar_variavel_global"]),
            "analista": CrewV12("analista", "analise", ["detectar_sql_injection", "detectar_nil"]),
            "implementador": CrewV12("implementador", "geracao", ["detectar_consistencia_tipos"]),
            "validador": CrewV12("validador", "validacao", None),  # Roda scanner completo
            "professor": CrewV12("professor", "ensino", None),  # Meta-conhecimento
        }
    
    def swap_estrategia(self, crew_origem, crew_destino, contexto):
        """Uma crew 'ensina' outra sobre uma abordagem que funcionou."""
        lessons_origem = self.crews[crew_origem].kg_pessoal.get("lessons", [])
        lessons_destino = self.crews[crew_destino].kg_pessoal.get("lessons", [])
        
        # Encontra lessons relevantes da origem que destino nao tem
        contextos_destino = {l.get("context") for l in lessons_destino}
        novas = [l for l in lessons_origem 
                 if contexto in l.get("context", "") 
                 and l.get("context") not in contextos_destino
                 and l.get("score", 0) >= 0.8]
        
        for lesson in novas:
            self.crews[crew_destino].kg_pessoal.setdefault("lessons", []).append({
                **lesson,
                "crew_origem": crew_origem,
                "tipo": "swap"
            })
            print(f"  [SWAP] {crew_origem} -> {crew_destino}: {lesson.get('context','')[:60]}")
        
        self.crews[crew_destino]._salvar_kg_pessoal()
    
    def executar_benchmark_geral(self):
        """Roda benchmarks em todas as crews e compara resultados."""
        print("\n" + "=" * 60)
        print("  META-BENCHMARK: Comparando abordagens entre crews")
        print("=" * 60)
        
        for nome, crew in self.crews.items():
            crew.relatorio()
        
        # Swap automatico: se uma crew tem benchmark melhor que outra
        print("\n  --- Analisando swaps potenciais ---")
        for nome, crew in self.crews.items():
            if crew.metricas["benchmarks"]:
                ultimo = crew.metricas["benchmarks"][-1]
                if ultimo["melhoria"] > 0.3:
                    print(f"  {nome} tem melhoria de {ultimo['melhoria']*100:.0f}% em {ultimo['teste']}")
                    print(f"    -> Pode ensinar outras crews!")
    
    def relatorio_final(self):
        print(f"\n{'='*60}")
        print(f"  META-SUPERVISOR — RELATORIO DAS CREWS V12")
        print(f"{'='*60}")
        
        total_lessons = sum(len(c.kg_pessoal.get("lessons",[])) for c in self.crews.values())
        total_benchmarks = sum(len(c.metricas["benchmarks"]) for c in self.crews.values())
        total_acertos = sum(c.metricas["acertos"] for c in self.crews.values())
        total_erros = sum(c.metricas["erros"] for c in self.crews.values())
        
        print(f"\n  Total de lessons (todas crews): {total_lessons}")
        print(f"  Total de benchmarks: {total_benchmarks}")
        print(f"  Acertos/Erros total: {total_acertos}/{total_erros}")
        print(f"\n  Crews ativas: {len(self.crews)}")
        for nome in self.crews:
            print(f"    - {nome}")
        print(f"\n  Swap de estrategias: automatico via KG compartilhado")
        print(f"  Benchmark cross-crew: ativo")
        print(f"{'='*60}")


# Demo
if __name__ == "__main__":
    print("=" * 70)
    print("  MCR-DevIA — CREW-V12 BRIDGE")
    print("  Cada crew como MCR-DevIA completo")
    print(f"  KG compartilhado: {KG_PATH}")
    print("=" * 70)
    
    meta = MetaSupervisor()
    
    # Simula aprendizado de cada crew
    meta.crews["narrador"].aprender("narrar_evento", 
        "O sistema processou", 
        "MCR-DevIA usou KG hit pra corrigir SQL injection no oraculo.lua", 
        score=0.9)
    
    meta.crews["analista"].aprender("analisar_codigo",
        "Analisando...",
        "codigo morto detectado: 15 arquivos com codigo inacessivel",
        score=0.85)
    
    meta.crews["implementador"].aprender("gerar_npc",
        "Template monster usado para NPC",
        "Erro aprendido: NPC nao usa API monster",
        score=0.95)
    
    meta.crews["validador"].aprender("validar_encoding",
        "22 arquivos Latin-1",
        "22 arquivos convertidos para UTF-8, 0 restantes",
        score=1.0)
    
    meta.crews["professor"].aprender("ensinar_v12",
        "Aluno nao entende V12",
        "Explicado: Python estrutura, IA preenche blanks. Exemplo: scanner detecta, fixer corrige",
        score=0.8)
    
    # Simula benchmarks
    meta.crews["implementador"].benchmark("template_consistencia", 
        12/27,  # antes: 44% consistente
        27/27,  # depois: 100% consistente (com detector)
        0.25)   # 25% de melhoria
    
    meta.crews["narrador"].benchmark("qualidade_narrativa",
        0.5, 0.85, 0.35)  # 35% de melhoria
    
    # Executa swap automatico: implementador ensina os outros sobre consistencia
    print("\n  --- Swaps automaticos ---")
    for crew_nome in meta.crews:
        if crew_nome != "implementador":
            meta.swap_estrategia("implementador", crew_nome, "consistencia")
    
    meta.executar_benchmark_geral()
    meta.relatorio_final()
    
    print("\n  [OK] Sistema Crew-V12 Bridge ativo!")
