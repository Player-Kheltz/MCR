"""modulos.episodic_memory — Memória episódica com decaimento."""
import json, time
from pathlib import Path


class EpisodicMemory:
    def __init__(self, max_episodios=500):
        self._episodios = []
        self._max = max_episodios
        self._path = Path(__file__).resolve().parent.parent.parent / 'cache' / 'episodic_memory.json'
        self._carregar()

    def _carregar(self):
        if self._path.exists():
            try:
                with open(self._path, 'r', encoding='utf-8') as f:
                    self._episodios = json.load(f)
            except Exception:
                self._episodios = []

    def salvar(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, 'w', encoding='utf-8') as f:
            json.dump(self._episodios[-self._max:], f, ensure_ascii=False, indent=2)

    def registrar(self, evento, contexto='', tipo='geral'):
        ep = {
            'evento': evento,
            'contexto': contexto,
            'tipo': tipo,
            'timestamp': time.time(),
            'acesso': 0,
        }
        self._episodios.append(ep)
        if len(self._episodios) > self._max:
            self._episodios = self._episodios[-self._max:]
        self.salvar()

    def recuperar(self, consulta, limite=5):
        resultados = []
        consulta_lower = consulta.lower()
        for ep in reversed(self._episodios):
            texto = f"{ep.get('evento', '')} {ep.get('contexto', '')}".lower()
            palavras = set(consulta_lower.split())
            if palavras & set(texto.split()):
                resultados.append(ep)
                if len(resultados) >= limite:
                    break
        return resultados

    def esquecimento(self, meia_vida_seg=86400):
        agora = time.time()
        for ep in self._episodios:
            idade = agora - ep.get('timestamp', agora)
            ep['relevancia'] = max(0.01, 2 ** (-idade / meia_vida_seg))
        self.salvar()
