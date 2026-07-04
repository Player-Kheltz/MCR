#!/usr/bin/env python3
"""
NPC MCR — Assistente com "alma" para servidor Tibia.

Simula um NPC do Tibia que:
  - Lembra de cada jogador (SessionCache)
  - Entende intencoes por parsing semantico (sujeito -> relacao -> objeto)
  - Gera respostas contextualizadas (MCRConexao + cadeia pensamento)
  - Evolui a personalidade (auto-evolution)
  - Aprende com cada interacao (Markov-2 + coupling)
  - Decide se da quest, item, ou conversa (orquestrador)
  - Tudo stdlib, 0 LLM, 0 dependencias

Uso:
    python npc_mcr.py                          # NPC interativo
    python npc_mcr.py --auto                   # NPC autonomo (aprende sozinho)
    python npc_mcr.py --load path/cerebro.json # carrega estado anterior
"""

import sys, os, json, time, random as _rand

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MCR_DIR = os.path.join(BASE_DIR, '..', '..')
os.chdir(MCR_DIR)
sys.path.insert(0, MCR_DIR)

__file__ = os.path.join(MCR_DIR, "MCR.py")
with open(__file__, encoding="utf-8") as f:
    _code = f.read().split("def main():")[0]
exec(compile(_code, "MCR.py", "exec"))

NPC_PATH = os.path.join(MCR_DIR, "cache", "npc_estado.json")
NPC_LOG = os.path.join(MCR_DIR, "cache", "npc.log")

# Personalidades que o NPC pode aprender (iniciais, evolve com o tempo)
_PERSONALIDADES = [
    "amigavel", "sabio", "misterioso", "negociante", "guerreiro",
    "ferreiro", "curandeiro", "bibliotecario",
]

def _log(msg):
    with open(NPC_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    print(f"  {msg}")


class MCRNPC:
    """NPC com alma — usa MCR para conversar, aprender e evoluir."""

    def __init__(self, nome="Ferronius", personalidade="ferreiro"):
        self.nome = nome
        self.personalidade = personalidade
        
        # Nucleo MCR
        self.cerebro = CerebroAGI()
        self.cerebro_path = os.path.join(MCR_DIR, "cache", "cerebro.json")
        self.cerebro.carregar(self.cerebro_path)
        
        # Seed de conhecimento inicial (personalidade)
        self._seed_conhecimento()
        
        # Estado do NPC
        self.n_conversas = 0
        self.ultimo_assunto = ""
        self.jogadores_conhecidos = {}
        
        _log(f"NPC {self.nome} iniciado (personalidade: {self.personalidade})")
        _log(f"Conhecimento: {len(self.cerebro.topicos)} topicos")
    
    def _seed_conhecimento(self):
        """Alimenta conhecimento basico da personalidade."""
        seeds = {
            "ferreiro": [
                "Eu forjo espadas e armaduras de qualidade",
                "O aco precisa ser aquecido ate ficar rubro",
                "Uma boa lamina leva horas de martelada",
                "O fogo da forja nunca se apaga",
                "Preciso de minerio para continuar trabalhando",
            ],
            "sabio": [
                "O conhecimento e' a luz que ilumina a escuridao",
                "Os antigos deixaram pergaminhos valiosos",
                "Cada resposta leva a uma nova pergunta",
                "A sabedoria vem com o tempo e a experiencia",
                "Nem tudo que brilha e ouro, nem tudo que e' misterio e magia",
            ],
            "negociante": [
                "O ouro move o mundo, meu caro",
                "Tenho mercadorias raras de terras distantes",
                "O segredo do comercio e' saber o valor das coisas",
                "Nao levo calote, mas faco bom prec'o para clientes fiéis",
                "Moedas de ouro falam mais alto que palavras",
            ],
        }
        base = seeds.get(self.personalidade, seeds["ferreiro"])
        for i, texto in enumerate(base):
            self.cerebro.alimentar(texto, f"{self.nome}_seed_{i}")
        
        # Itens que o NPC conhece (para gerar por superposicao)
        itens = ["espada", "armadura", "escudo", "elmo", "bota", "luvas"]
        materiais = ["ferro", "aco", "prata", "ouro", "mitril"]
        qualidades = ["comum", "raro", "epico", "lendario"]
        for item in itens:
            for mat in materiais:
                for qual in qualidades:
                    self.cerebro.alimentar(
                        f"{qual} {item} de {mat}", 
                        f"item_{item}_{mat}_{qual}"
                    )
    
    def _estado_orquestrador(self, jogador, mensagem):
        """Estado do orquestrador para decidir acao."""
        n_vezes = self.jogadores_conhecidos.get(jogador, {}).get("n_visitas", 0)
        return f"jogador:{jogador[:10]}_n:{min(n_vezes,5)}_ult:{self.ultimo_assunto[:10]}"
    
    def _detectar_intencao(self, mensagem):
        """Extrai (sujeito, relacao, objeto) da mensagem do jogador."""
        triplas = self.cerebro.parser.extrair(mensagem)
        if triplas:
            s, r, o = triplas[0]
            return (s.strip('.,!?;:()[]{}"\''), r.strip('.,!?;:()[]{}"\''), o.strip('.,!?;:()[]{}"\''))
        
        # Fallback por palavra-chave
        msg = mensagem.lower()
        if any(p in msg for p in ["quero", "preciso", "gostaria"]):
            return ("jogador", "quer", mensagem.split()[-1] if len(mensagem.split()) > 1 else "ajuda")
        if any(p in msg for p in ["quanto", "preco", "custa"]):
            return ("jogador", "pergunta_preco", mensagem.split()[-1] if len(mensagem.split()) > 1 else "item")
        if any(p in msg for p in ["quem", "o que", "onde"]):
            return ("jogador", "pergunta", mensagem)
        if any(p in msg for p in ["oi", "ola", "bom dia", "boa tarde"]):
            return ("jogador", "saudacao", self.nome)
        return ("jogador", "conversar", mensagem)
    
    def _decidir_acao(self, jogador, intencao):
        """Decide a acao do NPC via orquestrador Markov."""
        sujeito, relacao, objeto = intencao
        estado = f"{self._estado_orquestrador(jogador, objeto)}_rel:{relacao[:10]}"
        
        acao, conf = self.cerebro.mk_orq.predizer(estado)
        if acao and conf > 0.3:
            return acao
        
        # Fallback por tipo de relacao
        if relacao == "saudacao": return "saudar"
        if relacao == "pergunta_preco": return "informar_preco"
        if relacao == "quer": return "negociar"
        if relacao == "pergunta": return "responder"
        return "conversar"
    
    def _gerar_item(self, qualidade="raro", tipo="espada", material="aco"):
        """Gera o nome de um item (template simples, sem Markov)."""
        return f"{qualidade} {tipo} de {material}"
    
    def _responder(self, jogador, mensagem):
        """Gera resposta contextualizada para o jogador."""
        # Absorve no cache de sessao
        self.cerebro.session_cache.absorver(
            f"jogador_{jogador}_{self.n_conversas}",
            mensagem, "request", tags=[jogador, "jogador"])
        
        # Detecta intencao
        intencao = self._detectar_intencao(mensagem)
        self.cerebro.alimentar(f"[{jogador}] {mensagem}", f"conv_{self.n_conversas}")
        
        # Decide acao
        acao = self._decidir_acao(jogador, intencao)
        sujeito, relacao, objeto = intencao
        
        # Usa o objeto da intencao como tipo de item (se existir)
        tipo_item = objeto if objeto and len(objeto) > 2 else _rand.choice(["espada", "armadura", "escudo", "elmo"])
        tipo_item = tipo_item.strip('.,!?;:()[]{}"\'')  # remove pontuacao
        
        if acao == "saudar":
            respostas = [
                f"Saudacoes, {jogador}! Em que posso ajudar?",
                f"Bem-vindo, {jogador}! Precisa de algo?",
                f"Ola, {jogador}! A forja esta quente e as ferramentas estao prontas.",
            ]
            resposta = _rand.choice(respostas)
        
        elif acao == "informar_preco":
            item = self._gerar_item(tipo=tipo_item)
            respostas = [
                f"Este {item} custa {_rand.randint(50,500)} moedas de ouro.",
                f"Tenho um {item} especial por {_rand.randint(100,800)} moedas.",
                f"Por {_rand.randint(200,1000)} moedas, e' seu.",
            ]
            resposta = _rand.choice(respostas)
        
        elif acao == "negociar":
            item = self._gerar_item(tipo=tipo_item)
            respostas = [
                f"Entendo. Posso fazer um {item} para voce.",
                f"Preciso de materiais, mas posso conseguir um {item}.",
                f"Interessante. Tenho um {item} que pode lhe servir.",
            ]
            resposta = _rand.choice(respostas)
        
        elif acao == "responder":
            # Tenta cadeia de pensamento com contexto da sessao
            cadeia = self.cerebro._cadeia_pensamento(mensagem, intencao=self.personalidade, passos=3)
            # Guardrail: rejeita se resultado tem lixo byte (B:XX)
            if len(cadeia.split()) > 2 and not any(t.startswith('B:') for t in cadeia.split()):
                resposta = f"{self.nome} reflete: {cadeia}"
            else:
                resposta = self.cerebro.conexao.analisar(
                    f"conv_{self.n_conversas}",
                    f"{self.nome}_seed_0"
                ).get("melhor", {}).get("palavra")
                if isinstance(resposta, str) and len(resposta) > 3:
                    resposta = f"{self.nome}: {resposta}"
                else:
                    resposta = f"{self.nome}: Uma pergunta interessante, {jogador}. Deixe-me pensar..."
        
        else:
            resposta = self.cerebro.gerar(mensagem, passos=4)
            if not resposta or resposta == mensagem:
                resposta = f"{self.nome} ouve atentamente e pensa sobre o que dizer."
        
        # Aprende a transicao
        self.cerebro.mk_orq.aprender(
            f"{self._estado_orquestrador(jogador, mensagem)}_acao:{acao}",
            "ok")
        
        # Atualiza estado
        self.ultimo_assunto = objeto if objeto else mensagem.split()[-1] if mensagem.split() else ""
        self.n_conversas += 1
        
        # Atualiza jogador
        if jogador not in self.jogadores_conhecidos:
            self.jogadores_conhecidos[jogador] = {"n_visitas": 0, "ultima_interacao": time.time()}
        self.jogadores_conhecidos[jogador]["n_visitas"] += 1
        self.jogadores_conhecidos[jogador]["ultima_interacao"] = time.time()
        
        return resposta

    def conversar(self, jogador="Aventureiro", mensagem=""):
        """Ponto de entrada: jogador fala com NPC."""
        if not mensagem.strip():
            return f"{self.nome} espera que voce diga algo."
        
        resposta = self._responder(jogador, mensagem)
        return resposta
    
    def falar(self, jogador="Aventureiro"):
        """Loop interativo de conversa com o NPC."""
        print(f"\n=== {self.nome} (personalidade: {self.personalidade}) ===")
        print(f"(digite 'sair' para encerrar, '!status' para ver estado)")
        print()
        
        if not self.cerebro.session_cache.fragmentos:
            self.cerebro.session_cache.absorver("inicio", f"Conversa com {self.nome}", "contexto", tags=["npc"])
        
        while True:
            try:
                msg = input(f"[{jogador}] ").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n{self.nome} se despede.")
                break
            
            if not msg: continue
            if msg.lower() == "sair":
                print(f"{self.nome} se despede de {jogador}.")
                break
            if msg.lower() == "!status":
                print(f"  Jogador: {jogador}")
                print(f"  Conversas: {self.n_conversas}")
                print(f"  Conhecimento: {len(self.cerebro.topicos)} topicos")
                print(f"  Cache: {len(self.cerebro.session_cache.fragmentos)} fragmentos")
                continue
            
            resposta = self.conversar(jogador, msg)
            print(f"[{self.nome}] {resposta}")


def modo_autonomo(npc):
    """NPC autonomo: aprende sozinho enquanto 'vive'."""
    _log(f"Modo autonomo ativado. Pressione Ctrl+C para parar.")
    ciclo = 0
    try:
        while True:
            ciclo += 1
            # Simula um jogador generico
            jogador = _rand.choice(["Kheltz", "Aria", "Thorn", "Lyra", "Ragnar"])
            
            if ciclo % 3 == 0:
                # Ocasionalmente, revisita aprendizado
                if npc.cerebro.topicos:
                    topico = _rand.choice(list(npc.cerebro.topicos.keys()))
                    texto = npc.cerebro.topicos[topico].get('texto', '')
                    if texto:
                        npc.cerebro.alimentar(f"[revisao] {texto}", f"rev_{ciclo}")
                        _log(f"Revisando conhecimento: {topico}")
            
            # Aprende nova transicao
            if ciclo % 2 == 0:
                r = npc.cerebro.auto_evolution.ciclo()
                if r.get('mutado'):
                    _log(f"Personalidade evoluindo...")
            
            # Salva periodicamente
            if ciclo % 5 == 0:
                npc.cerebro.salvar(npc.cerebro_path)
                _log(f"Ciclo {ciclo}: {len(npc.cerebro.topicos)} topicos, {npc.n_conversas} conversas")
            
            time.sleep(1)
    except KeyboardInterrupt:
        _log("NPC autonomo parado.")
        npc.cerebro.salvar(npc.cerebro_path)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="NPC MCR para Tibia")
    parser.add_argument("--nome", default="Ferronius", help="Nome do NPC")
    parser.add_argument("--personalidade", default="ferreiro", 
                       choices=_PERSONALIDADES, help="Personalidade inicial")
    parser.add_argument("--jogador", default="Aventureiro", help="Nome do jogador")
    parser.add_argument("--auto", action="store_true", help="Modo autonomo")
    parser.add_argument("--load", help="Carregar estado de um arquivo")
    args = parser.parse_args()
    
    npc = MCRNPC(nome=args.nome, personalidade=args.personalidade)
    
    if args.auto:
        modo_autonomo(npc)
    else:
        # Testa automatizado antes do interativo
        print("=" * 55)
        print(f"  NPC MCR: {npc.nome}")
        print(f"  Personalidade: {npc.personalidade}")
        print("=" * 55)
        
        # Teste rapido
        testes = [
            "Ola!",
            "Quanto custa uma espada?",
            "Preciso de uma armadura",
            "O que voce sabe sobre mitril?",
        ]
        for msg in testes:
            print(f"\n[Jogador] {msg}")
            resp = npc.conversar(args.jogador, msg)
            print(f"[{npc.nome}] {resp}")
        
        print("\n" + "=" * 55)
        print("  Modo interativo:")
        print("=" * 55)
        npc.falar(args.jogador)
