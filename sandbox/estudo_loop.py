#!/usr/bin/env python
"""Loop de Estudo Autonomo do MCR-DevIA.

Decide o que aprender, estuda, registra no KG, repete.
Funciona 100% autonomo — sem interacao do usuario.

Uso:
    python sandbox/estudo_loop.py              # Loop infinito
    python sandbox/estudo_loop.py --ciclos 5   # Apenas N ciclos
    python sandbox/estudo_loop.py --topico "IA" # Topico especifico
    python sandbox/estudo_loop.py --listar     # Mostra historico
"""
import sys, os, json, time, random
import argparse

# Paths
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'Scripts', 'mcr_devia'))

from modulos.ia import IA
from modulos.kg import KnowledgeGraph
from modulos.decider import Decider
from modulos.master_agent import MasterAgent

# Config
INTERVALO_MIN = int(os.environ.get('MCR_ESTUDO_INTERVALO', '5'))  # minutos
LOG_PATH = os.path.join(BASE, 'sandbox', '.mcr_estudo_log.jsonl')


class EstudoLoop:
    """Loop autonomo de estudo do MCR-DevIA.

    A cada ciclo:
    1. Consulta KG para saber o que ja sabe
    2. Decider escolhe um topico NOVO para aprender
    3. Gera pergunta de estudo especifica
    4. Busca na web + IA sintetiza
    5. Registra no KG como licao
    6. Aguarda N minutos e repete
    """

    def __init__(self):
        self.ia = IA()
        self.kg = KnowledgeGraph()
        self.decider = Decider(self.ia)
        self.agent = MasterAgent()
        self.ciclo = 0
        self.topicos_estudados = set()
        self.perguntas_anteriores = set()  # para evitar perguntas repetidas

    def _get_topicos_conhecidos(self):
        """Retorna topicos ja registrados no KG."""
        lessons = self.kg.data.get('licoes', [])
        topicos = set()
        for l in lessons:
            ctx = l.get('ctx', '')
            erro = l.get('erro', '').lower()
            if ctx and ctx != 'geral':
                topicos.add(ctx)
            # Extrai palavras relevantes do erro
            palavras = [p for p in erro.split() if len(p) > 4]
            for p in palavras:
                topicos.add(p)
        return topicos

    def _normalizar_topico(self, topico):
        """Normaliza topico para comparacao."""
        t = topico.lower().strip()
        t = t.replace(' ', '_').replace('-', '_').replace('/', '_')
        # Remove artigos e preposicoes comuns
        for w in ['o_', 'a_', 'os_', 'as_', 'de_', 'da_', 'do_', 'em_', 'para_', 'com_']:
            if t.startswith(w):
                t = t[len(w):]
        return t[:40]

    def _escolher_topico(self, topicos_conhecidos):
        """Decide QUAL topico estudar — GARANTIDO como NAO estudado ainda.
        
        Tenta ate 5 vezes. Usa salt para evitar cache do Decider.
        Se tudo falhar, fallback para lista geral.
        """
        exemplos = [
            ("Ja estudei Python, FastAPI, Docker. Qual estudar agora?", "Rust para WebAssembly"),
            ("Sei pygame, tkinter. Qual biblioteca grafica estudar?", "OpenGL basico"),
            ("Topicos: SPA, SHC, Canary. Proximo?", "Design Patterns em Python"),
        ]

        fallbacks = [
            "Python assincrono com asyncio",
            "SOLID principles",
            "SQL vs NoSQL",
            "Git branching strategies",
            "REST API design patterns",
            "Docker compose basico",
            "Pytest fixtures e mocks",
            "Design patterns: Factory, Strategy, Observer",
            "Algoritmos de ordenacao",
            "Estruturas de dados: Arvores",
            "Testes de integracao vs unitarios",
            "CI/CD com GitHub Actions",
        ]

        for tentativa in range(5):
            salt = random.randint(0, 99999)
            contexto = (f"Topicos ja estudados: {', '.join(sorted(topicos_conhecidos)[-15:])}"
                        if topicos_conhecidos else "Nenhum topico estudado ainda.")

            try:
                dados = self.decider.extrair_json(
                    f"Escolha topico de estudo NOVO [{salt}]",
                    {'topico': '', 'justificativa': ''},
                    exemplos=exemplos[:2],
                    instrucao=(
                        f"{contexto}\n"
                        f"NUNCA repita topicos ja estudados.\n"
                        f"Tente variar area de conhecimento.\n"
                        f"Escolha algo util: programacao, arquitetura, algoritmo, ferramenta."
                    )
                )
                topico = dados.get('topico', '').strip()
            except Exception as e:
                topico = random.choice(fallbacks)

            if not topico:
                topico = random.choice(fallbacks)

            # Verifica se topico ja foi estudado
            topico_norm = self._normalizar_topico(topico)
            ja_estudado = topico_norm in topicos_conhecidos

            if not ja_estudado:
                return topico

            print(f"  [!] Topico '{topico}' ja estudado, tentando outro...")

        # Fallback apos 5 tentativas
        for fb in fallbacks:
            if self._normalizar_topico(fb) not in topicos_conhecidos:
                return fb
        return random.choice(fallbacks)

    def _gerar_pergunta(self, topico):
        """Gera pergunta GARANTIDA como diferente das anteriores.
        
        Tenta ate 3 vezes com salts diferentes.
        Verifica se pergunta ja foi usada antes.
        """
        exemplos = [
            ("async/await em Python", "Como funciona o asyncio em Python? Qual a diferenca entre Thread e Coroutine?"),
            ("SOLID principles", "O que e o principio Open/Closed? De um exemplo pratico em Python."),
            ("Docker compose", "Como configurar volumes e networks no Docker Compose?"),
        ]

        for tentativa in range(3):
            salt = random.randint(0, 99999)
            try:
                dados = self.decider.extrair_json(
                    f"Crie pergunta de estudo DIFERENTE sobre: {topico} [{salt}]",
                    {'pergunta': '', 'area': ''},
                    exemplos=exemplos[:3],
                    instrucao=(
                        "Pergunta deve ser ESPECIFICA e DIFERENTE do que ja perguntei antes.\n"
                        "Varie o enfoque: teoria, pratica, comparacao, implementacao.\n"
                        "Seja objetiva e respondivel via pesquisa web."
                    )
                )
                pergunta = dados.get('pergunta', '').strip()
                if pergunta and len(pergunta) > 25:
                    # Verifica se pergunta ja foi usada
                    pergunta_norm = pergunta.lower().strip()[:60]
                    if pergunta_norm not in self.perguntas_anteriores:
                        self.perguntas_anteriores.add(pergunta_norm)
                        return pergunta
                    print(f"  [!] Pergunta repetida, tentando outra...")
            except Exception as e:
                print(f"[Erro ao gerar pergunta: {e}]")

        return f"Explique {topico} com exemplos praticos e comparativos. Diferencie de abordagens similares."

    def _realizar_estudo(self, pergunta, topico):
        """Estuda o topico: busca web + IA sintetiza + registra no KG."""
        print(f"\n  [Estudando] {pergunta[:80]}...")
        t0 = time.time()

        # 1. Busca contexto web (com retry + fallback Wikipedia)
        contexto = None
        for tentativa in range(2):
            contexto = self.ia.buscar_web(pergunta, max_resultados=5)
            if contexto:
                break
            print(f"  [!] Web search falhou, tentando novamente...")
            time.sleep(2)
        
        # Fallback: busca Wikipedia diretamente
        if not contexto:
            try:
                print(f"  [!] Tentando Wikipedia como fallback...")
                contexto = self.ia._web_search(pergunta, max_r=3)
            except Exception:
                pass

        # 2. IA sintetiza o conhecimento
        prompt = f"Pergunta de estudo: {pergunta}\n\n"
        if contexto:
            prompt += f"Contexto da web:\n{contexto[:2500]}\n\n"
        prompt += (
            "Responda de forma DIDATICA, como uma licao aprendida.\n"
            "Seja CONCISO: maximo 400 caracteres.\n"
            "Foque no que eh IMPORTANTE SABER sobre o topico."
        )

        resposta = self.ia.gerar(prompt, 0.3, 'conceito')

        tempo = time.time() - t0
        sucesso = bool(resposta and len(resposta) > 30)

        if sucesso:
            # 3. Registra no KG
            topico_ctx = topico.lower().replace(' ', '_').replace('-', '_')[:30]
            self.kg.aprender(
                erro=f"Estudo: {topico[:60]}",
                causa=f"Pergunta: {pergunta[:150]}",
                solucao=resposta[:500],
                ctx=f'estudo_{topico_ctx}'
            )
            print(f"  [OK] Registrado: {resposta[:100]}...")
        else:
            print(f"  [!] Resposta insatisfatoria para: {topico}")

        # 4. Log persistente
        log_entry = {
            'ts': time.time(),
            'ts_iso': time.strftime('%Y-%m-%d %H:%M:%S'),
            'ciclo': self.ciclo,
            'topico': topico,
            'pergunta': pergunta,
            'tempo_seg': round(tempo, 1),
            'sucesso': sucesso,
        }
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        return log_entry

    def _relatorio(self):
        """Mostra relatorio completo do que aprendeu ate agora."""
        if not os.path.exists(LOG_PATH):
            return "Nenhum estudo registrado ainda."

        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            entradas = [json.loads(l) for l in f if l.strip()]

        if not entradas:
            return "Nenhum estudo registrado ainda."

        total = len(entradas)
        sucessos = sum(1 for e in entradas if e.get('sucesso'))
        topicos = list(set(e.get('topico', '') for e in entradas))
        tempo_total = sum(e.get('tempo_seg', 0) for e in entradas) / 60

        return (
            f"  [Relatorio] Estudos\n"
            f"     Ciclos: {total}\n"
            f"     Sucessos: {sucessos}/{total}\n"
            f"     Topicos unicos: {len(topicos)}\n"
            f"     Tempo total: {tempo_total:.0f} min\n"
            f"     Ultimos topicos: {', '.join(topicos[-5:])}"
        )

    def executar(self, ciclos=None, topico_inicial=None):
        """Executa o loop de estudo autonomo.

        Args:
            ciclos: Numero de ciclos (None = infinito)
            topico_inicial: Topico especifico para comecar
        """
        sep = '=' * 56
        print(sep)
        print("    LOOP DE ESTUDO AUTONOMO - MCR")
        print("    Pressione Ctrl+C para parar")
        print(sep)

        topicos_conhecidos = self._get_topicos_conhecidos()
        print(f"\n  Topicos ja registrados no KG: {len(topicos_conhecidos)}")

        while ciclos is None or self.ciclo < ciclos:
            self.ciclo += 1
            sep = '=' * 56
            print(f"\n{sep}")
            print(f"  Ciclo {self.ciclo}" + (f'/{ciclos}' if ciclos else ''))
            print(f"{sep}")

            # 1. Escolher topico
            topico = topico_inicial or self._escolher_topico(topicos_conhecidos)
            if not topico:
                topico = "Python - topicos intermediarios"
            print(f"  [Topico] {topico}")

            # 2. Gerar pergunta de estudo
            pergunta = self._gerar_pergunta(topico)
            print(f"  [Pergunta] {pergunta[:100]}...")

            # 3. Realizar estudo
            resultado = self._realizar_estudo(pergunta, topico)

            # 4. Atualizar lista de topicos conhecidos
            topicos_conhecidos.add(topico)
            topicos_conhecidos.add(topico.lower().replace(' ', '_')[:30])

            # 5. Relatorio periodico
            if self.ciclo % 5 == 0:
                print(f"\n{self._relatorio()}")

            # 6. Aguardar entre ciclos
            if ciclos is None or self.ciclo < ciclos:
                print(f"\n  [Aguardando] Proximo ciclo em {INTERVALO_MIN} min...")
                try:
                    time.sleep(INTERVALO_MIN * 60)
                except KeyboardInterrupt:
                    print("\n\n  [Parado] Loop interrompido pelo usuario.")
                    break

        # Relatorio final
        print(f"\n{'=' * 56}")
        print(f"  ESTUDO FINALIZADO - {self.ciclo} CICLOS")
        print(f"{self._relatorio()}")
        print(f"{'=' * 56}")

        return self.ciclo


# ============================================================
# PONTO DE ENTRADA
# ============================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Loop de Estudo Autonomo MCR')
    parser.add_argument('--ciclos', type=int, default=None,
                        help='Numero de ciclos (padrao: infinito)')
    parser.add_argument('--topico', type=str, default=None,
                        help='Topico especifico para estudar')
    parser.add_argument('--listar', action='store_true',
                        help='Mostra historico de estudos e sai')

    args = parser.parse_args()

    if args.listar:
        loop = EstudoLoop()
        print(loop._relatorio())
        sys.exit(0)

    loop = EstudoLoop()
    try:
        loop.executar(ciclos=args.ciclos, topico_inicial=args.topico)
    except KeyboardInterrupt:
        print(f"\n\n  Total de ciclos: {loop.ciclo}")
        print("  Estudo interrompido. Registros salvos.")
