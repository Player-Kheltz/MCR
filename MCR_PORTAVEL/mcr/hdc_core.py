import random, math, hashlib, json, os

DIM = 10000

class HDVector:
    __slots__ = ('v',)
    
    def __init__(self, vetor=None):
        if vetor is None:
            self.v = [0] * DIM
        else:
            self.v = vetor[:] if isinstance(vetor, list) else list(vetor)
    
    @staticmethod
    def aleatorio(seed=None):
        rng = random.Random(seed)
        return HDVector([1 if rng.random() < 0.5 else -1 for _ in range(DIM)])
    
    @staticmethod
    def da_string(texto):
        h = hashlib.sha256(texto.encode()).digest()
        rng = random.Random(h)
        return HDVector([1 if rng.random() < 0.5 else -1 for _ in range(DIM)])
    
    @staticmethod
    def binding(a, b):
        return HDVector([a.v[i] * b.v[i] for i in range(DIM)])
    
    def __xor__(self, other):
        return HDVector.binding(self, other)
    
    @staticmethod
    def bundle(*vetores):
        if not vetores:
            return HDVector()
        n = len(vetores)
        soma = [0] * DIM
        for v in vetores:
            for i in range(DIM):
                soma[i] += v.v[i]
        limiar = 0
        return HDVector([1 if s > limiar else -1 for s in soma])
    
    def __add__(self, other):
        if isinstance(other, HDVector):
            return HDVector.bundle(self, other)
        return NotImplemented
    
    @staticmethod
    def permutar(hd, passos=1):
        v = hd.v[:]
        for _ in range(passos):
            v = [v[-1]] + v[:-1]
        return HDVector(v)
    
    @staticmethod
    def cosine(a, b):
        dot = sum(a.v[i] * b.v[i] for i in range(DIM))
        return dot / DIM
    
    def similaridade(self, other):
        return HDVector.cosine(self, other)
    
    def __repr__(self):
        return f"<HDVector cos_medio={sum(self.v)/DIM:.3f}>"

class HDCVocab:
    def __init__(self):
        self._cache = {}
    
    def get(self, nome):
        if nome not in self._cache:
            self._cache[nome] = HDVector.da_string(nome)
        return self._cache[nome]
    
    def binding(self, nome_a, nome_b):
        return HDVector.binding(self.get(nome_a), self.get(nome_b))
    
    def bundle(self, *nomes):
        return HDVector.bundle(*[self.get(n) for n in nomes])
    
    def decode(self, hd, top_k=5):
        """
        Dado um HD vector, encontra os conceitos mais similares no vocabulário.
        Retorna [(nome, similaridade), ...]
        """
        resultados = []
        for nome, vec in self._cache.items():
            sim = hd.similaridade(vec)
            resultados.append((nome, sim))
        resultados.sort(key=lambda x: -x[1])
        return resultados[:top_k]


if __name__ == "__main__":
    import time
    
    print("=" * 60)
    print("HDC - Hyperdimensional Computing (VALIDACAO)")
    print("=" * 60)
    
    t0 = time.time()
    
    # 1. Criar vetores base
    a = HDVector.aleatorio(seed="A")
    b = HDVector.aleatorio(seed="B")
    c = HDVector.aleatorio(seed="C")
    
    print(f"\n1. Vetores base criados: {time.time()-t0:.3f}s")
    print(f"   cosine(a, a) = {a.similaridade(a):.4f} (esperado: 1.0)")
    print(f"   cosine(a, b) = {a.similaridade(b):.4f} (esperado: ~0.0)")
    print(f"   cosine(b, c) = {b.similaridade(c):.4f} (esperado: ~0.0)")
    
    # 2. Binding
    ab = a ^ b
    print(f"\n2. Binding a⊗b:")
    print(f"   cosine(a⊗b, a) = {ab.similaridade(a):.4f} (esperado: ~0.0)")
    print(f"   cosine(a⊗b, b) = {ab.similaridade(b):.4f} (esperado: ~0.0)")
    print(f"   cosine(a⊗b, a⊗b) = {ab.similaridade(ab):.4f} (esperado: 1.0)")
    
    # 3. Unbind (binding com o mesmo vetor desfaz)
    aba = ab ^ a
    print(f"\n3. Unbind (a⊗b)⊗a:")
    print(f"   cosine((a⊗b)⊗a, b) = {aba.similaridade(b):.4f} (esperado: ~1.0)")
    
    # 4. Bundle
    abc = HDVector.bundle(a, b, c)
    print(f"\n4. Bundle a+b+c:")
    print(f"   cosine(a+b+c, a) = {abc.similaridade(a):.4f} (esperado: >0.3)")
    print(f"   cosine(a+b+c, b) = {abc.similaridade(b):.4f} (esperado: >0.3)")
    print(f"   cosine(a+b+c, d) = {abc.similaridade(HDVector.aleatorio(seed='D')):.4f} (esperado: ~0.0)")
    
    # 5. Binding preserva similaridade? (propriedade chave do HDC)
    x = HDCVocab()
    gato = x.get("gato")
    cachorro = x.get("cachorro")
    animal = x.get("animal")
    eh_um = x.get("eh_um")
    
    gato_eh_animal = gato ^ eh_um ^ animal
    cachorro_eh_animal = cachorro ^ eh_um ^ animal
    
    sim_gato_cachorro = gato.similaridade(cachorro)
    sim_gatoanimal_cachorroanimal = gato_eh_animal.similaridade(cachorro_eh_animal)
    
    print(f"\n5. Analogia estrutural (binding preserva relação):")
    print(f"   cosine(gato, cachorro) = {sim_gato_cachorro:.4f}")
    print(f"   cosine(gato⊗eh_um⊗animal, cachorro⊗eh_um⊗animal) = {sim_gatoanimal_cachorroanimal:.4f}")
    print(f"   (similaridade se mantém após mesmo binding)")
    
    # 6. Bundle decode
    print(f"\n6. Vocabulário - decode de bundle:")
    frase = x.bundle("Kheltz", "pediu", "espada_de_ferro")
    print(f"   Bundle(Kheltz, pediu, espada_de_ferro):")
    for nome, sim in x.decode(frase, top_k=5):
        print(f"     {nome}: {sim:.4f}")
    
    print(f"\nTempo total: {time.time()-t0:.3f}s")
    print("=" * 60)
