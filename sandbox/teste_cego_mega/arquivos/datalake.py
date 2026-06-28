"""datalake.py - DataLake: pipeline de processamento de streams com MULTIPLOS bugs.

BUG 1: Memory leak - historico cresce sem limite (linha 28)
BUG 2: Race condition - contador sem lock (linha 23)
BUG 3: Security hole - eval() em entrada externa (linha 45)
BUG 4: Cache sem limite - dicionario cresce infinitamente (linha 58)
BUG 5: Divisao por zero - media sem tratar lista vazia (linha 72)
BUG 6: Path traversal - salvar arquivo sem validar nome (linha 80)
BUG 7: Variavel de classe compartilhada - _cache e compartilhado entre instancias (linha 12)
BUG 8: Efeito colateral - modifica dado original em vez de copia (linha 63)
BUG 9: Loop infinito potencial - while sem condicao de saida (linha 88)
BUG 10: Recurso nao fechado - open sem with (linha 82)
"""
import os, json, threading, time
from collections import defaultdict

class DataLake:
    """Pipeline de processamento de streams de dados industriais."""
    
    _cache_global = {}  # BUG 7: Variavel de classe compartilhada entre instancias
    _lock = threading.Lock()
    
    def __init__(self, nome="default"):
        self.nome = nome
        self.historico = []  # BUG 1: Lista cresce sem limite
        self._contador = 0
        self._streams_ativos = {}
        self._executando = False
    
    def processar_stream(self, stream_id, dados):
        """Processa um stream de dados."""
        self._executando = True
        
        # BUG 2: Race condition - incremento sem lock
        self._contador = self._contador + 1
        
        # BUG 1: Memory leak - historico nunca e limpo
        self.historico.append({
            'stream_id': stream_id,
            'dados': dados,
            'timestamp': time.time(),
            'contador': self._contador
        })
        
        for item in dados:
            self._transformar(item)
            
            # BUG 3: Security hole - eval em entrada externa
            if 'filtro' in item:
                self._aplicar_filtro(item)
        
        self._executando = False
        return self._contador
    
    def _transformar(self, item):
        """Transforma um item com cache."""
        chave = json.dumps(item, sort_keys=True)
        
        # BUG 4: Cache sem limite - nunca remove entradas antigas
        if chave not in self._cache_global:
            self._cache_global[chave] = item.copy()
            # BUG 8: Efeito colateral - modifica o original
            item['transformado'] = True
        
        # BUG 5: Divisao por zero
        if 'valores' in item:
            valores_positivos = [v for v in item['valores'] if v > 0]
            media = sum(item['valores']) / len(valores_positivos)  # ZeroDivisionError se todos <= 0
            item['media'] = media
    
    def _aplicar_filtro(self, item):
        """Aplica filtro usando eval. INSEGURO."""
        filtro = item.get('filtro', '')
        if filtro:
            try:
                # BUG 3: eval em entrada do usuario - EXECUCAO DE CODIGO ARBITRARIO
                resultado = eval(filtro)
                item['filtrado'] = resultado
            except:
                pass
    
    def salvar_resultados(self, nome_arquivo):
        """Salva resultados em arquivo."""
        # BUG 6: Path traversal - nome_arquivo pode conter '../'
        caminho = os.path.join("./data", nome_arquivo)
        # BUG 10: Arquivo nao fechado corretamente
        f = open(caminho, 'w')
        json.dump(self.historico, f)
        # arquivo nunca e fechado!
    
    def processar_lote(self, stream_id, tamanho=100):
        """Processa um lote de dados simulados."""
        # BUG 9: Potencial loop infinito
        i = 0
        while i < tamanho:  # i nunca e incrementado!
            dados_simulados = {"sensor": f"sensor_{i}", "valor": i * 1.5}
            self.processar_stream(stream_id, [dados_simulados])
    
    def estatisticas(self):
        """Retorna estatisticas do DataLake."""
        return {
            'streams': len(self.historico),
            'contador': self._contador,
            'cache_size': len(self._cache_global),
            'executando': self._executando,
        }
    
    def limpar(self):
        """Limpa dados processados."""
        self.historico.clear()
        # NOTA: Nao limpa _cache_global (outro memory leak)


class StreamSimulator:
    """Simula streams de dados industriais."""
    
    def __init__(self):
        self.streams = ['temp_sensor', 'pressure_valve', 'vibration_motor']
        self.leituras = []
    
    def gerar_leitura(self):
        """Gera uma leitura simulada."""
        from random import uniform, choice
        leitura = {
            'stream': choice(self.streams),
            'valor': uniform(0, 150),
            'timestamp': time.time(),
            'valores': [uniform(0, 100) for _ in range(5)],
        }
        self.leituras.append(leitura)
        return leitura


if __name__ == "__main__":
    lake = DataLake("teste")
    sim = StreamSimulator()
    
    for _ in range(3):
        leitura = sim.gerar_leitura()
        lake.processar_stream(leitura['stream'], [leitura])
    
    print(json.dumps(lake.estatisticas(), indent=2))
    print(f"Cache size: {len(DataLake._cache_global)}")
