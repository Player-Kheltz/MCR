import re

with open('mcr/coupling.py', encoding='utf-8') as fh:
    content = fh.read()

# Cut from 'def save' to end of return False in def load
# Pattern: def save...\n    return False\n
new_save_load = '''
    def save(self, caminho: str = None):
        import json, os
        if caminho is None:
            caminho = os.path.join(os.path.dirname(__file__),
                                   f'coupling_{self.__class__.__name__}.json')
        dados = {}
        dados['total'] = self._total
        dados['palavra_acao'] = {k: dict(v) for k, v in self._palavra_acao.items()}
        dados['cluster_acao'] = {k: dict(v) for k, v in self._cluster_acao.items()}
        dados['posicao_acao'] = {k: dict(v) for k, v in self._posicao_acao.items()}
        dados['contexto_acao'] = {k: dict(v) for k, v in self._contexto_acao.items()}
        dados['freq_acao'] = dict(self._freq_acao)
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def load(self, caminho: str = None) -> bool:
        import json, os
        if caminho is None:
            caminho = os.path.join(os.path.dirname(__file__),
                                   f'coupling_{self.__class__.__name__}.json')
        if not os.path.exists(caminho):
            return False
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            self._total = dados.get('total', 0)
            self._freq_acao = defaultdict(int, dados.get('freq_acao', {}))
            self._palavra_acao = defaultdict(lambda: defaultdict(int))
            for p, ac in dados.get('palavra_acao', {}).items():
                self._palavra_acao[p].update(ac)
            self._cluster_acao = defaultdict(lambda: defaultdict(int))
            for c, ac in dados.get('cluster_acao', {}).items():
                self._cluster_acao[c].update(ac)
            self._posicao_acao = defaultdict(lambda: defaultdict(int))
            for ps, ac in dados.get('posicao_acao', {}).items():
                self._posicao_acao[ps].update(ac)
            self._contexto_acao = defaultdict(lambda: defaultdict(int))
            for ctx, ac in dados.get('contexto_acao', {}).items():
                self._contexto_acao[ctx].update(ac)
            return True
        except Exception:
            return False
'''

# Replace everything from the first occurrence of 'def save' to the file end
idx = content.find('def save')
if idx >= 0:
    # find the start of that line
    start = content.rfind('\n', 0, idx) + 1
    # remove everything from start to EOF
    content = content[:start] + new_save_load
else:
    print('Warning: def save not found in content')

with open('mcr/coupling.py', 'w', encoding='utf-8') as fh:
    fh.write(content)

print('coupling.py rewrite complete')
