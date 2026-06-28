"""processor.py - Processador de dados com MULTIPLOS problemas.
Bug 1: Race condition (linha 18)
Bug 2: Memory leak (linha 29)
Bug 3: Logica incorreta (linha 42)
Bug 4: Security hole (linha 55)
Bug 5: Performance (linha 67)
"""
import os, json, threading, time

class DataProcessor:
    """Processa dados de sensores industriais."""
    
    _cache = {}
    _lock = threading.Lock()
    _contador = 0
    
    def __init__(self, caminho="./data"):
        self.caminho = caminho
        self.resultados = []
        self._executando = False
        os.makedirs(caminho, exist_ok=True)
    
    def processar(self, dados):
        """Processa uma lista de dados."""
        self._executando = True
        for item in dados:
            # BUG 1: Race condition ao incrementar contador
            self._contador = self._contador + 1
            
            # BUG 2: Memory leak - resultados nunca sao limpos
            self.resultados.append(self._transformar(item))
            
            # BUG 3: Logica incorreta - media com divisao por zero
            if 'valores' in item:
                media = sum(item['valores']) / len([v for v in item['valores'] if v > 0])
                item['media'] = media
        
        # BUG 4: Security hole - eval em input do usuario
        for item in dados:
            if 'filtro' in item:
                try:
                    resultado = eval(item['filtro'])
                    item['filtrado'] = resultado
                except:
                    pass
        
        self._executando = False
        return self.resultados
    
    def _transformar(self, item):
        """Transforma um item (com cache)."""
        chave = json.dumps(item, sort_keys=True)
        # BUG 5: Cache sem limite de tamanho
        if chave not in self._cache:
            self._cache[chave] = item.copy()
            time.sleep(0.1)  # Simula processamento pesado
            # BUG 6: Modifica o item original em vez da copia
            item['processado'] = True
        return self._cache[chave]
    
    def salvar(self, nome):
        """Salva resultados em arquivo. SEM validacao de path (path traversal)."""
        path = os.path.join(self.caminho, nome)
        with open(path, 'w') as f:
            json.dump(self.resultados, f)
    
    def estatisticas(self):
        """Retorna estatisticas (com bug de arredondamento)."""
        total = len(self.resultados)
        if total == 0:
            return {}
        # BUG 7: Soma em ponto flutuante com acumulo de erro
        soma = sum(sum(v.values()) if isinstance(v, dict) else v for v in self.resultados if isinstance(v, (dict, int, float)))
        return {
            'total': total,
            'soma': soma,
            'media': soma / total,
            'cache_size': len(self._cache),
        }


class SensorSimulator:
    """Simula sensores industriais."""
    
    def __init__(self):
        self.sensores = ['temp1', 'temp2', 'pressao', 'vibracao']
        self.historico = []
    
    def ler(self):
        """Le dados dos sensores (com ruido simulado)."""
        from random import uniform
        dados = {}
        for s in self.sensores:
            dados[s] = uniform(20.0, 100.0)
        self.historico.append(dados)
        return dados
    
    def alarme(self, limite=80.0):
        """Verifica se algum sensor passou do limite."""
        for sensor, valor in self.ler().items():
            if valor > limite:
                return f"ALARME: {sensor} em {valor:.1f}"
        return "OK"


if __name__ == "__main__":
    p = DataProcessor()
    sim = SensorSimulator()
    
    for _ in range(5):
        dados = sim.ler()
        p.processar([dados])
    
    print(p.estatisticas())
