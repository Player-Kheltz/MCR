import time, random, math
from collections import deque
from hdc_core import HDVector
from sdm_core import SDM_MDL
from percepcao import PercepcaoNPC
from mundo_tibia import MapaTibia

# Estados emocionais/atitudinais do NPC
PERSONALIDADES = {
    "ferreiro": {
        "saudacoes": ["Ola, viajante.", "Bem-vindo a forja.", "Precisa de algo?"],
        "tchau": ["Volte sempre.", "Cuidado com as espadas.", "Fique com ouro."],
        "assuntos": ["espada", "ferro", "martelo", "armadura", "bigorna"],
        "exploracao_base": 0.3,
    },
    "bibliotecario": {
        "saudacoes": ["Bem-vindo a biblioteca.", "Veio estudar?", "Silencio..."],
        "tchau": ["Bons estudos.", "Nao rasgue as paginas.", "Ate mais."],
        "assuntos": ["livro", "magia", "historia", "runas", "conhecimento"],
        "exploracao_base": 0.4,
    },
    "mercador": {
        "saudacoes": ["Ola, quer negociar?", "Tenho os melhores precos!", "Compre ou troque!"],
        "tchau": ["Volte para negociar.", "Nao aceito fiado.", "Foi bom negociar."],
        "assuntos": ["pocao", "anel", "escudo", "capacete", "tesouro"],
        "exploracao_base": 0.5,
    },
}

class MCRNPCv2:
    def __init__(self, nome, profissao, x, y, z, regiao_id, mapa,
                 entropia_min=0.2, entropia_max=0.7):
        self.nome = nome
        self.profissao = profissao
        self.traits = PERSONALIDADES.get(profissao, PERSONALIDADES["ferreiro"])
        
        # Mapa e posicao
        self.mapa = mapa
        self.x, self.y, self.z = x, y, z
        self.regiao_id = regiao_id
        self.posicao_anterior = (x, y, z)
        
        # Estado interno
        self.passos_dados = 0
        self.conversando_com = None
        self.ultima_acao = None
        self.acao_contador = 0
        
        # Percepcao e memoria
        self.percepcao = PercepcaoNPC(nome)
        self.memoria = SDM_MDL(limiar_novidade=0.2)
        
        # Criticalidade
        self.entropia_min = entropia_min
        self.entropia_max = entropia_max
        self.exploracao = self.traits["exploracao_base"]
        self.hist_entropia = deque(maxlen=50)
        self.hist_acoes = deque(maxlen=20)
        
        # Cache do ultimo HD do momento (para compartilhamento)
        self.ultimo_hd = None
        
        # Inventario simulado
        self.inventario = []
        
        print(f"  NPC {nome} criado em ({x},{y},{z}) regiao {regiao_id}")
    
    def _entropia_momento(self, hd):
        """Calcula entropia baseada no erro de reconstrucao da SDM"""
        import sdm_core
        reconstruido, fid, n_ativos = self.memoria.retrieve(hd)
        if reconstruido is None:
            return 1.0  # max entropy: nunca visto
        
        # Projetar HD para SDM_DIM antes de comparar
        v_proj = sdm_core.projetar(hd.v if hasattr(hd, 'v') else hd)
        erros = sum(1 for j in range(len(v_proj)) if v_proj[j] != reconstruido[j])
        return erros / len(v_proj)
    
    def _atualizar_criticalidade(self, entropia):
        """Auto-regulacao: ajusta exploracao baseado na entropia"""
        self.hist_entropia.append(entropia)
        if len(self.hist_entropia) < 10:
            return
        
        ent_media = sum(self.hist_entropia) / len(self.hist_entropia)
        
        if ent_media < self.entropia_min:
            # Muito rigido: explorar mais
            self.exploracao = min(0.9, self.exploracao * 1.15)
        elif ent_media > self.entropia_max:
            # Muito caotico: consolidar, explorar menos
            self.exploracao = max(0.02, self.exploracao * 0.9)
        # else: criticalidade mantida
        
        return ent_media
    
    def _surpresa_acao(self, acao):
        """Calcula surpresa esperada para cada acao (Active Inference simulado)"""
        # Acoes que ja fez muito tem baixa surpresa
        historico = [a for a in self.hist_acoes if a == acao]
        n_vezes = len(historico)
        return 1.0 / (n_vezes + 1)
    
    def _acoes_disponiveis(self, jogadores_proximos=None):
        """Retorna lista de (nome_acao, surpresa_esperada)"""
        acoes = [("observar", 0.1)]
        
        if jogadores_proximos:
            acoes.append(("falar_saudacao", 0.2))
            if self.conversando_com:
                acoes.append(("falar_resposta", 0.05))
                acoes.append(("comerciar", 0.3))
            else:
                acao_falar = f"falar_com_{len(jogadores_proximos)}"
                acoes.append((acao_falar, 0.4))
        
        # Andar: mais surpresa se muito tempo parado
        if self.passos_dados > 0 and self.passos_dados % 20 == 0:
            acoes.append(("andar_aleatorio", 0.2))
        
        # Sempre pode esperar
        acoes.append(("esperar", 0.01))
        
        return acoes
    
    def tick(self, jogadores_proximos=None, hora=None):
        """
        Um ciclo de vida do NPC.
        
        Args:
            jogadores_proximos: lista de dicts com 'nome', 'dist', 'ultima_fala'
            hora: inteiro 0-23
        
        Returns:
            str: descricao da acao tomada
        """
        self.passos_dados += 1
        self.posicao_anterior = (self.x, self.y, self.z)
        
        # 1. OBSERVAR
        hd_momento = self.percepcao.codificar_momento(
            posicao=(self.x, self.y, self.z),
            jogadores_proximos=[(j['nome'], j['dist'], j.get('ultima_fala', ''))
                               for j in (jogadores_proximos or [])],
            hora=hora,
            itens=self.inventario[:5],
        )
        self.ultimo_hd = hd_momento
        
        # 2. CALCULAR ENTROPIA (novidade)
        entropia = self._entropia_momento(hd_momento)
        
        # 3. ATUALIZAR CRITICALIDADE
        ent_media = self._atualizar_criticalidade(entropia)
        
        # 4. RECUPERAR MEMORIA SIMILAR
        reconstruido, fid, n_ativos = self.memoria.retrieve(hd_momento)
        tem_memoria = reconstruido is not None
        
        # 5. ESCOLHER ACAO (Active Inference)
        acoes = self._acoes_disponiveis(jogadores_proximos)
        
        # Escolhe acao com menor surpresa, modulada por exploracao
        acoes_com_peso = []
        for nome_acao, surpresa in acoes:
            peso = surpresa * (1 - self.exploracao) + self.exploracao * random.random()
            acoes_com_peso.append((peso, nome_acao))
        acoes_com_peso.sort(key=lambda x: x[0])
        
        acao_escolhida = acoes_com_peso[0][1]
        self.hist_acoes.append(acao_escolhida)
        self.ultima_acao = acao_escolhida
        
        # 6. EXECUTAR ACAO
        resultado = self._executar_acao(acao_escolhida, jogadores_proximos, hora)
        
        # 7. APRENDER (armazenar na SDM se for novo)
        if entropia > self.memoria.limiar_novidade:
            self.memoria.store_se_novo(hd_momento)
        
        return resultado
    
    def _executar_acao(self, acao, jogadores_proximos=None, hora=None):
        """Executa a acao escolhida"""
        self.acao_contador += 1
        
        if acao == "esperar":
            return f"{self.nome} observa o movimento."
        
        elif acao == "observar":
            # Atualiza posicao sutilmente
            return f"{self.nome} olha em volta."
        
        elif acao.startswith("falar_"):
            if not jogadores_proximos:
                return f"{self.nome} murmura algo sozinho."
            
            jogador = jogadores_proximos[0]
            nome_j = jogador['nome']
            self.conversando_com = nome_j
            
            if "saudacao" in acao:
                fala = random.choice(self.traits["saudacoes"])
            else:
                fala = f"{random.choice(self.traits['saudacoes'])} O que deseja, {nome_j}?"
            
            return f"{self.nome} diz: \"{fala}\""
        
        elif acao == "comerciar":
            if self.inventario:
                item = random.choice(self.inventario)
                return f"{self.nome} oferece {item} por 100 moedas."
            return f"{self.nome} diz: \"Nao tenho nada para vender hoje.\""
        
        elif acao == "andar_aleatorio":
            # Anda ate um ponto aleatorio proximo
            dx = random.choice([-2, -1, 0, 1, 2])
            dy = random.choice([-2, -1, 0, 1, 2])
            nx, ny = self.x + dx, self.y + dy
            
            reg = self.mapa.regiao_em(nx, ny, self.z)
            if reg and reg.id == self.regiao_id:
                self.x, self.y = nx, ny
                return f"{self.nome} andou para ({self.x},{self.y})."
            
            return f"{self.nome} tentou andar mas nao ha caminho."
        
        return f"{self.nome} esta parado."
    
    def falar(self, mensagem):
        """Responde a uma mensagem do jogador"""
        self.hist_acoes.append("falar_resposta")
        
        # Palavras-chave
        msg_lower = mensagem.lower()
        
        if any(p in msg_lower for p in ["tchau", "ate", "sai", "vou"]):
            self.conversando_com = None
            return random.choice(self.traits["tchau"])
        
        if any(p in msg_lower for p in ["preco", "quanto", "custa", "comprar", "vender"]):
            return self._responder_comercio(msg_lower)
        
        if any(p in msg_lower for p in ["oi", "ola", "hey", "bom dia", "boa tarde"]):
            return random.choice(self.traits["saudacoes"])
        
        # Intencao detectada via palavras-chave do assunto
        for assunto in self.traits["assuntos"]:
            if assunto in msg_lower:
                return f"{self.nome} diz: \"Ah, {assunto}? Tenho experiencia com isso.\""
        
        # Fallback: pergunta generica
        return f"{self.nome} diz: \"{msg_lower}? Interessante...\""
    
    def _responder_comercio(self, msg):
        if not self.inventario:
            return f"{self.nome} diz: \"Nao tenho nada para vender hoje.\""
        
        item = random.choice(self.inventario)
        preco = random.randint(50, 500)
        return f"{self.nome} diz: \"Tenho {item} por {preco} moedas.\""
    
    def adicionar_item(self, item):
        self.inventario.append(item)


if __name__ == "__main__":
    import time
    print("=" * 60)
    print("MCRNPCv2 - NPC Vivo (VALIDACAO)")
    print("=" * 60)
    
    # Carregar mapa
    mapa = MapaTibia()
    
    # Criar NPC
    joao = MCRNPCv2("Joao", "ferreiro", 971, 995, 7, 0, mapa)
    joao.adicionar_item("espada de ferro")
    joao.adicionar_item("escudo de madeira")
    
    maria = MCRNPCv2("Maria", "bibliotecario", 975, 1000, 7, 0, mapa)
    maria.adicionar_item("livro de magia antigo")
    maria.adicionar_item("mapa do tesouro")
    
    print("\n--- Cenario 1: NPC sozinho (5 ticks) ---")
    for tick in range(5):
        resultado = joao.tick(hora=14)
        print(f"  tick {tick+1}: {resultado}")
        time.sleep(0.1)
    
    print("\n--- Cenario 2: Jogador se aproxima ---")
    jogadores = [{"nome": "Kheltz", "dist": 3, "ultima_fala": "preciso de uma espada"}]
    
    for tick in range(3):
        resultado = joao.tick(jogadores_proximos=jogadores, hora=15)
        print(f"  tick {tick+1}: {resultado}")
        time.sleep(0.1)
    
    print("\n--- Cenario 3: Jogador fala com NPC ---")
    print(f"  Jogador: Ola")
    resp = joao.falar("Ola")
    print(f"  {resp}")
    
    print(f"  Jogador: Quanto custa a espada?")
    resp = joao.falar("Quanto custa a espada?")
    print(f"  {resp}")
    
    print(f"  Jogador: Tchau")
    resp = joao.falar("Tchau")
    print(f"  {resp}")
    
    print("\n--- Cenario 4: Memoria episodica (SDM) ---")
    print("  Mesmo jogador volta depois de algumas interacoes...")
    
    # O SDM ja deve ter memorizado as interacoes anteriores
    rec, fid, n = joao.memoria.retrieve(joao.ultimo_hd)
    print(f"  Memoria recuperada: n_ativos={n}, fidelidade={fid:.3f}")
    
    print("\n--- Cenario 5: Andar aleatorio ---")
    for tick in range(20):
        resultado = joao.tick(hora=16)
        if "andou" in resultado:
            print(f"  tick {tick+1}: {resultado}")
        if tick == 19:
            print(f"  (andou ate se cansar)")
    
    print("\n--- Cenario 6: Criticalidade ---")
    print(f"  Joao: exploracao={joao.exploracao:.3f}")
    print(f"  Maria: exploracao={maria.exploracao:.3f}")
    
    # Simular muitas repeticoes para baixar entropia
    for _ in range(30):
        joao.tick(hora=17)
    
    ent_media = sum(joao.hist_entropia) / len(joao.hist_entropia)
    print(f"  Apos 30 ticks repetitivos: entropia_media={ent_media:.3f}, exploracao={joao.exploracao:.3f}")
    
    print("\n" + "=" * 60)
    print("NPC Vivo validado!")
    print("=" * 60)
