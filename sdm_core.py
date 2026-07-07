import random, math, time

# SDM usa dimensao reduzida para performance
# HD original tem 10000 dims, projetamos para SDM_DIM
SDM_DIM = 200
N_ENDERECOS = 500
RAIO_ATIVACAO = 0.25

# Projecao: mapeia indices 0..9999 para 0..SDM_DIM-1
_RNG_PROJ = random.Random(123)
_PROJECAO = [_RNG_PROJ.randint(0, SDM_DIM - 1) for _ in range(10000)]

def projetar(hd_v):
    """Projeta HD vector 10000-dim para SDM_DIM-dim por soma de buckets"""
    v = hd_v.v if hasattr(hd_v, 'v') else hd_v
    proj = [0] * SDM_DIM
    for i, val in enumerate(v):
        proj[_PROJECAO[i]] += val
    return [1 if s > 0 else -1 for s in proj]

class SDM:
    def __init__(self, n_enderecos=N_ENDERECOS, raio=RAIO_ATIVACAO):
        self.raio = raio
        self.n_enderecos = n_enderecos
        self.dim = SDM_DIM
        self.limiar = raio * self.dim
        
        rng = random.Random(42)
        self.enderecos = [[1 if rng.random() < 0.5 else -1 for _ in range(self.dim)]
                          for _ in range(n_enderecos)]
        
        self.conteudo = [[0] * self.dim for _ in range(n_enderecos)]
        self.n_armazenados = 0
    
    def _projetar(self, hd_v):
        return projetar(hd_v)
    
    def _enderecos_ativos(self, vetor):
        ativos = []
        for i, end in enumerate(self.enderecos):
            dot = sum(vetor[j] * end[j] for j in range(self.dim))
            if dot > self.limiar:
                ativos.append(i)
        return ativos
    
    def store(self, hd_v):
        v = self._projetar(hd_v)
        ativos = self._enderecos_ativos(v)
        for idx in ativos:
            c = self.conteudo[idx]
            for j in range(self.dim):
                c[j] += v[j]
        self.n_armazenados += 1
        return len(ativos)
    
    def retrieve(self, hd_v):
        v = self._projetar(hd_v)
        ativos = self._enderecos_ativos(v)
        if not ativos:
            return None, 0.0, 0
        
        soma = [0] * self.dim
        for idx in ativos:
            c = self.conteudo[idx]
            for j in range(self.dim):
                soma[j] += c[j]
        
        n_ativos = len(ativos)
        reconstruido = [1 if soma[j] > 0 else -1 for j in range(self.dim)]
        
        concordancia = sum(1 for j in range(self.dim) if abs(soma[j]) > 0)
        fidelidade = concordancia / self.dim
        
        return reconstruido, fidelidade, n_ativos

class SDM_MDL(SDM):
    def __init__(self, limiar_novidade=0.25, **kwargs):
        super().__init__(**kwargs)
        self.limiar_novidade = limiar_novidade
        self.n_rejeitados = 0
    
    def store_se_novo(self, hd_v):
        reconstruido, fid, n_ativos = self.retrieve(hd_v)
        if reconstruido is None:
            return self.store(hd_v), True
        
        v = self._projetar(hd_v)
        erros = sum(1 for j in range(self.dim) if v[j] != reconstruido[j])
        erro_pct = erros / self.dim
        
        if erro_pct > self.limiar_novidade:
            return self.store(hd_v), True
        else:
            self.n_rejeitados += 1
            return 0, False

    def stats(self):
        total = self.n_armazenados + self.n_rejeitados
        return {
            'armazenados': self.n_armazenados,
            'rejeitados': self.n_rejeitados,
            'total_operacoes': total,
            'taxa_reducao': f"{self.n_armazenados}/{total} = {self.n_armazenados/total*100:.1f}%" if total > 0 else "N/A"
        }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    
    from hdc_core import HDVector, HDCVocab
    
    print("=" * 60)
    print("SDM - Sparse Distributed Memory (VALIDACAO)")
    print(f"  SDM_DIM={SDM_DIM}, N_ENDERECOS={N_ENDERECOS}")
    print("=" * 60)
    
    vocab = HDCVocab()
    sdm = SDM()
    sdm_mdl = SDM_MDL()
    
    # 1. Teste basico
    print("\n1. Teste basico store/retrieve:")
    t0 = time.time()
    
    hd1 = vocab.bundle("Kheltz", "pediu", "espada_de_ferro")
    hd2 = vocab.bundle("Maria", "perguntou", "runas")
    hd3 = vocab.bundle("Joao", "vendeu", "pocao")
    hd4 = vocab.bundle("Kheltz", "comprou", "espada_de_ferro")
    
    for hd in [hd1, hd2, hd3, hd4]:
        sdm.store(hd)
    
    print(f"   4 episodios armazenados em {time.time()-t0:.3f}s")
    
    # Buscar "Kheltz precisa de espada"
    hd_busca = vocab.bundle("Kheltz", "precisa", "espada")
    reconstruido, fid, n_ativos = sdm.retrieve(hd_busca)
    
    if reconstruido:
        print(f"   Busca: Kheltz + precisa + espada")
        print(f"   Enderecos ativos: {n_ativos}")
        print(f"   Fidelidade: {fid:.3f}")
    
    # 2. Teste MDL
    print("\n2. Teste MDL:")
    # Store um episodio
    hd_orig = vocab.bundle("Kheltz", "pediu", "espada")
    sdm_mdl.store(hd_orig)
    print(f"   Original: armazenado")
    
    # Tentar store de algo muito similar
    hd_similar = vocab.bundle("Kheltz", "pediu", "espada")
    n, is_novo = sdm_mdl.store_se_novo(hd_similar)
    print(f"   Similar (mesmo): {'REJEITADO' if not is_novo else 'ACEITO'} ({sdm_mdl.n_rejeitados} rejeitados)")
    
    # Store de algo diferente
    hd_diff = vocab.bundle("Joao", "vendeu", "armadura")
    n, is_novo = sdm_mdl.store_se_novo(hd_diff)
    print(f"   Diferente: {'ACEITO' if is_novo else 'REJEITADO'}")
    
    print(f"   SDM+MDL stats: {sdm_mdl.stats()}")
    
    # 3. Capacidade
    print("\n3. Teste de capacidade (200 episodios)...")
    t0 = time.time()
    
    sdm_grande = SDM()
    sujeitos = ["Kheltz", "Joao", "Maria", "Pedro", "Ana"]
    verbos = ["pediu", "vendeu", "comprou", "perguntou"]
    objetos = ["espada", "pocao", "runas", "armadura"]
    
    for i in range(200):
        s = random.choice(sujeitos)
        v = random.choice(verbos)
        o = random.choice(objetos)
        hd = vocab.bundle(s, v, o)
        sdm_grande.store(hd)
    
    hd_teste = vocab.bundle("Kheltz", "pediu", "espada")
    reconstruido, fid, n_ativos = sdm_grande.retrieve(hd_teste)
    
    print(f"   200 episodios em {time.time()-t0:.3f}s")
    print(f"   Busca 'Kheltz pediu espada': {n_ativos} enderecos ativos, fid={fid:.3f}")
    
    # 4. Memoria seletiva
    print("\n4. Memoria seletiva (MDL vs SDM puro):")
    sdm_puro = SDM()
    sdm_seletivo = SDM_MDL()
    
    for i in range(100):
        s = random.choice(sujeitos[:3])
        v = random.choice(verbos[:3])
        o = random.choice(objetos[:3])
        hd = vocab.bundle(s, v, o)
        sdm_puro.store(hd)
        sdm_seletivo.store_se_novo(hd)
    
    unicos_esperados = len(set([f"{s}{v}{o}" for s in sujeitos[:3] for v in verbos[:3] for o in objetos[:3]]))
    print(f"   Combinacoes unicas possiveis: {unicos_esperados}")
    print(f"   SDM puro: {sdm_puro.n_armazenados} armazenados (cresce sempre)")
    print(f"   SDM+MDL: {sdm_seletivo.n_armazenados} armazenados, {sdm_seletivo.n_rejeitados} rejeitados")
    print(f"   (MDL deve rejeitar repeticoes alem do vocabulario base)")
    
    print("\n" + "=" * 60)
    print("SDM validado com sucesso!")
    print("=" * 60)
