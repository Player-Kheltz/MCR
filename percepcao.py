from hdc_core import HDVector, HDCVocab

class PercepcaoNPC:
    """Converte o estado do mundo percebido por um NPC em HD vectors."""
    
    def __init__(self, nome_npc):
        self.vocab = HDCVocab()
        self.nome_npc = nome_npc
        self.hd_npc = self.vocab.get(nome_npc)
        
        # Cache de vetores semanticos
        self._pos = {}
        self._jogadores = {}
        self._itens = {}
    
    def _pos_vetor(self, x, y, z):
        """Codifica posicao (x,y,z) como HD vector unico"""
        chave = f"pos_{x}_{y}_{z}"
        if chave not in self._pos:
            self._pos[chave] = self.vocab.get(chave)
        return self._pos[chave]
    
    def _jogador_vetor(self, nome):
        """Codifica nome do jogador como HD vector"""
        if nome not in self._jogadores:
            self._jogadores[nome] = self.vocab.get(f"jogador_{nome}")
        return self._jogadores[nome]
    
    def _item_vetor(self, nome_item):
        """Codifica nome de item como HD vector"""
        if nome_item not in self._itens:
            self._itens[nome_item] = self.vocab.get(f"item_{nome_item}")
        return self._itens[nome_item]
    
    def codificar_momento(self, posicao, jogadores_proximos=None,
                          ultima_fala=None, hora=None, itens=None,
                          eventos=None):
        """
        Codifica o momento atual como HD vector 10000-dim.
        
        Args:
            posicao: (x, y, z) tupla
            jogadores_proximos: lista de (nome, distancia, ultima_fala)
            ultima_fala: (quem, frase, assunto) ou None
            hora: inteiro 0-23
            itens: lista de nomes de itens
            eventos: lista de strings de eventos
        
        Returns:
            HDVector de 10000 dim representando o momento
        """
        componentes = []
        
        # NPC + posicao (sempre presente)
        if posicao:
            x, y, z = posicao
            hd_local = self.hd_npc ^ self.vocab.get(f"Z{z}") ^ self._pos_vetor(x, y, z)
            componentes.append(hd_local)
        
        # Jogadores proximos
        if jogadores_proximos:
            for nome_jog, dist, fala in jogadores_proximos:
                if not nome_jog:
                    continue
                hd_jog = self._jogador_vetor(nome_jog) ^ self.vocab.get(f"dist_{int(dist)}")
                if fala:
                    hd_fala = (self._jogador_vetor(nome_jog) ^
                              self.vocab.get("falou") ^
                              self.vocab.get(f"_{fala[:20]}"))
                    componentes.append(hd_fala)
                componentes.append(hd_jog)
        
        # Ultima fala
        if ultima_fala:
            quem, frase, assunto = ultima_fala
            hd_frase = HDVector.bundle(
                self.vocab.get(f"falou_{quem[:10]}"),
                self.vocab.get(f"_{frase[:30]}"),
                self.vocab.get(f"sobre_{assunto[:20]}") if assunto else self.vocab.get("sobre_nada")
            )
            componentes.append(hd_frase)
        
        # Hora
        if hora is not None:
            componentes.append(self.vocab.get(f"hora_{hora}"))
        
        # Itens
        if itens:
            hd_itens = HDVector.bundle(*[self._item_vetor(item) for item in itens])
            componentes.append(hd_itens)
        
        # Eventos
        if eventos:
            for ev in eventos:
                componentes.append(self.vocab.get(f"evento_{ev[:20]}"))
        
        if not componentes:
            return HDVector()
        
        # Bundle tudo num unico HD vector
        return HDVector.bundle(*componentes)
    
    def decoder(self, hd, top_k=10):
        """
        Decodifica um HD vector em conceitos compreensiveis.
        Retorna lista de (nome_conceito, similaridade)
        """
        return self.vocab.decode(hd, top_k=top_k)


if __name__ == "__main__":
    import time
    print("=" * 60)
    print("PERCEPCAO NPC - HDC Encoding (VALIDACAO)")
    print("=" * 60)
    
    perc = PercepcaoNPC("Joao_Ferreiro")
    
    # 1. Codificar momento simples
    print("\n1. Codificando momento (NPC parado sozinho):")
    t0 = time.time()
    hd = perc.codificar_momento(posicao=(971, 995, 7))
    print(f"   Vetor HD gerado em {time.time()-t0:.3f}s")
    print(f"   Decode:", perc.decoder(hd, top_k=5))
    
    # 2. Com jogador falando
    print("\n2. Com jogador proximo falando:")
    t0 = time.time()
    hd2 = perc.codificar_momento(
        posicao=(971, 995, 7),
        jogadores_proximos=[("Kheltz", 3, "preciso de uma espada")],
        ultima_fala=("Kheltz", "preciso de uma espada", "espada"),
        hora=14
    )
    print(f"   Vetor HD gerado em {time.time()-t0:.3f}s")
    dec = perc.decoder(hd2, top_k=10)
    for nome, sim in dec:
        print(f"     {nome}: {sim:.4f}")
    
    # 3. Verificar que momentos DIFERENTES geram HDs diferentes
    hd_similar = perc.codificar_momento(
        posicao=(971, 995, 7),
        jogadores_proximos=[("Kheltz", 2, "comprei uma espada")],
        ultima_fala=("Kheltz", "comprei uma espada", "compra"),
        hora=14
    )
    
    hd_diferente = perc.codificar_momento(
        posicao=(976, 1000, 7),
        jogadores_proximos=[("Maria", 5, "tem livro de magia?")],
        hora=20,
        itens=["pocao", "runas"]
    )
    
    print(f"\n3. Similaridade entre momentos:")
    sim_similar = hd2.similaridade(hd_similar)
    sim_diferente = hd2.similaridade(hd_diferente)
    print(f"   Mesmo local, mesmo jogador, assunto parecido: {sim_similar:.3f}")
    print(f"   Local diferente, jogador diferente, assunto diferente: {sim_diferente:.3f}")
    print(f"   (similar deve ser mais alta que diferente)")
    
    # 4. Simular SDM: armazenar e recuperar
    print("\n4. Teste com SDM:")
    import sys
    sys.path.insert(0, '.')
    from sdm_core import SDM
    
    sdm = SDM()
    hd_momento = perc.codificar_momento(
        posicao=(971, 995, 7),
        jogadores_proximos=[("Kheltz", 3, "preciso de uma espada")],
        hora=14,
        itens=["espada_ferro", "martelo"]
    )
    n_ativos = sdm.store(hd_momento)
    print(f"   Armazenado: {n_ativos} enderecos ativos")
    
    # Recuperar com busca similar
    hd_busca = perc.codificar_momento(
        posicao=(971, 995, 7),
        jogadores_proximos=[("Kheltz", 2, "quero comprar espada")],
        hora=14
    )
    reconstruido, fid, n_ativos = sdm.retrieve(hd_busca)
    print(f"   Buscando momento similar: {n_ativos} enderecos, fid={fid:.3f}")
    if reconstruido:
        hd_r = HDVector(reconstruido)
        sim = hd_r.similaridade(hd_momento)
        print(f"   Similaridade com original: {sim:.3f}")
    
    print("\n" + "=" * 60)
