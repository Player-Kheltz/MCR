from collections import defaultdict
from hdc_core import HDVector
from sdm_core import SDM

class RedeNPCs:
    """Rede de comunicacao entre NPCs."""
    
    def __init__(self):
        self.npcs = {}          # nome -> MCRNPCv2
        self.por_regiao = defaultdict(list)  # regiao_id -> [nomes]
        self.sdm_global = SDM()  # memoria compartilhada global
    
    def registrar(self, npc):
        """Adiciona um NPC a rede"""
        self.npcs[npc.nome] = npc
        self.por_regiao[npc.regiao_id].append(npc.nome)
        print(f"  Rede: {npc.nome} registrado na regiao {npc.regiao_id} ({npc.profissao})")
    
    def npcs_proximos(self, nome_npc, raio_tiles=10):
        """Retorna NPCs proximos (mesma regiao e distancia)"""
        npc = self.npcs.get(nome_npc)
        if not npc:
            return []
        
        proximos = []
        for outro_nome in self.por_regiao.get(npc.regiao_id, []):
            if outro_nome == nome_npc:
                continue
            outro = self.npcs[outro_nome]
            dist = abs(npc.x - outro.x) + abs(npc.y - outro.y)
            if dist <= raio_tiles:
                proximos.append((outro_nome, dist))
        
        return proximos
    
    def broadcast_local(self, nome_origem, hd_evento, raio=5):
        """
        Compartilha experiencia apenas com NPCs na mesma vizinhanca.
        Retorna: numero de NPCs que receberam
        """
        npc = self.npcs.get(nome_origem)
        if not npc:
            return 0
        
        n_receberam = 0
        for outro_nome in self.por_regiao.get(npc.regiao_id, []):
            if outro_nome == nome_origem:
                continue
            outro = self.npcs[outro_nome]
            dist = abs(npc.x - outro.x) + abs(npc.y - outro.y)
            if dist <= raio:
                outro.memoria.store(hd_evento)
                n_receberam += 1
        
        return n_receberam
    
    def broadcast_global(self, nome_origem, hd_evento):
        """
        Compartilha experiencia com TODOS os NPCs (eventos importantes).
        """
        npc = self.npcs.get(nome_origem)
        if not npc:
            return 0
        
        # Armazenar na memoria global
        self.sdm_global.store(hd_evento)
        
        # Propagar para todos NPCs
        n_receberam = 0
        for outro_nome, outro in self.npcs.items():
            if outro_nome == nome_origem:
                continue
            outro.memoria.store(hd_evento)
            n_receberam += 1
        
        return n_receberam
    
    def executar_todos(self, jogadores_por_regiao=None, hora=None):
        """
        Executa tick de todos NPCs.
        
        Args:
            jogadores_por_regiao: dict regiao_id -> lista de jogadores
            hora: int 0-23
        
        Returns: dict nome_npc -> resultado do tick
        """
        resultados = {}
        
        for nome, npc in self.npcs.items():
            jogadores = (jogadores_por_regiao or {}).get(npc.regiao_id, [])
            resultado = npc.tick(jogadores_proximos=jogadores, hora=hora)
            resultados[nome] = resultado
        
        return resultados
    
    def resumo(self):
        return {
            "n_npcs": len(self.npcs),
            "n_regioes": len(self.por_regiao),
            "npcs": {n: {"pos": (npc.x, npc.y, npc.z),
                         "regiao": npc.regiao_id,
                         "profissao": npc.profissao,
                         "exploracao": round(npc.exploracao, 3)}
                    for n, npc in self.npcs.items()},
        }


if __name__ == "__main__":
    import time
    print("=" * 60)
    print("REDE DE NPCS - Comunicacao (VALIDACAO)")
    print("=" * 60)
    
    from mundo_tibia import MapaTibia
    from npc_vivo import MCRNPCv2
    from hdc_core import HDCVocab
    
    # Setup
    mapa = MapaTibia()
    rede = RedeNPCs()
    vocab = HDCVocab()
    
    # Criar NPCs em diferentes regioes
    joao = MCRNPCv2("Joao", "ferreiro", 971, 995, 7, 0, mapa)
    maria = MCRNPCv2("Maria", "bibliotecario", 975, 1000, 7, 0, mapa)
    zaran = MCRNPCv2("Zaran", "mercador", 1000, 1005, 7, 0, mapa)
    
    # NPC em outra regiao (Z6_R2 = id 4)
    thor = MCRNPCv2("Thor", "ferreiro", 965, 1015, 6, 4, mapa)
    
    for npc in [joao, maria, zaran, thor]:
        rede.registrar(npc)
    
    # Teste 1: NPCs proximos
    print(f"\n1. NPCs proximos de Joao (raio 10):")
    for nome, dist in rede.npcs_proximos("Joao", raio_tiles=10):
        print(f"   {nome}: {dist} tiles")
    
    # Teste 2: Broadcast local
    print(f"\n2. Broadcast local (Joao, raio=10):")
    hd_evento = vocab.bundle("Kheltz", "pediu", "espada")
    n = rede.broadcast_local("Joao", hd_evento, raio=10)
    print(f"   {n} NPCs receberam")
    
    # Teste 3: Broadcast global
    print(f"\n3. Broadcast global (evento importante):")
    hd_boss = vocab.bundle("Dragon_Lord", "morto", "por_Kheltz")
    n = rede.broadcast_global("Joao", hd_boss)
    print(f"   {n} NPCs receberam (incluindo Thor em outra regiao)")
    
    # Teste 4: Executar todos
    print(f"\n4. Tick de todos NPCs:")
    jogadores_regiao = {
        0: [{"nome": "Kheltz", "dist": 3, "ultima_fala": "preciso de uma espada"}],
        4: [],
    }
    resultados = rede.executar_todos(jogadores_por_regiao=jogadores_regiao, hora=14)
    for nome, resultado in resultados.items():
        print(f"   {nome}: {resultado}")
    
    # Teste 5: Interacao entre NPCs
    print(f"\n5. Maria pergunta sobre Joao (memoria compartilhada):")
    # Se Joao broadcastou "Kheltz pediu espada", Maria pode responder
    # Simular: Maria tem o evento na memoria
    rec, fid, n_ativos = maria.memoria.retrieve(hd_evento)
    print(f"   Maria recupera evento 'Kheltz pediu espada': n_ativos={n_ativos}")
    
    print(f"\nResumo da rede:")
    resumo = rede.resumo()
    print(f"   {resumo['n_npcs']} NPCs em {resumo['n_regioes']} regioes")
    
    print("\n" + "=" * 60)
