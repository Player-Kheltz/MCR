#!/usr/bin/env python
"""CommandLoader Prototype v2 - Carregamento dinamico de comandos."""
import os, sys, importlib

class CommandLoader:
    """Carrega comandos de um diretorio. Hot-reload via .refresh()."""
    
    def __init__(self, cmd_dir=None):
        self.cmd_dir = cmd_dir or os.path.dirname(os.path.abspath(__file__))
        self._comandos = {}
        self.refresh()
    
    def _carregar_modulo(self, fpath):
        """Carrega um modulo .py de arquivo."""
        import importlib.util as _util
        nome_mod = os.path.splitext(os.path.basename(fpath))[0]
        spec = _util.spec_from_file_location(nome_mod, fpath)
        if not spec or not spec.loader:
            return None
        mod = _util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    
    def refresh(self):
        self._comandos = {}
        if not os.path.isdir(self.cmd_dir):
            return
        
        for f in sorted(os.listdir(self.cmd_dir)):
            if not f.startswith('cmd_') or not f.endswith('.py'):
                continue
            fpath = os.path.join(self.cmd_dir, f)
            try:
                mod = self._carregar_modulo(fpath)
                if mod and hasattr(mod, 'register'):
                    meta = mod.register()
                    nome = meta.get('name', f[4:-3])
                    self._comandos[nome] = {
                        'meta': meta,
                        'handler': meta.get('handler'),
                        'module': mod,
                    }
            except Exception as e:
                print(f'[Loader] ERRO {f}: {e}')
    
    def listar(self):
        if not self._comandos:
            print('[Loader] Nenhum comando')
            return
        for nome, info in sorted(self._comandos.items()):
            print(f'  {nome:20s} | {info["meta"].get("desc","")}')
    
    def executar(self, nome, kg, ia, args, ctx_crew=None):
        if nome not in self._comandos:
            return False
        cmd = self._comandos[nome]
        handler = cmd.get('handler')
        if not handler:
            return False
        try:
            return handler(kg, ia, args, ctx_crew=ctx_crew)
        except Exception as e:
            print(f'[Loader] ERRO: {nome}: {e}')
            import traceback; traceback.print_exc()
            return False


def testar():
    print('='*60)
    print('TESTE V2: CommandLoader Prototype')
    print('='*60)
    
    loader = CommandLoader()
    
    print('\n1. Comandos carregados:')
    loader.listar()
    total = len(loader._comandos)
    print(f'   Total: {total}')
    
    class FakeKG:
        data = {'versoes': 1, 'metricas': {'licoes': 100, 'geracoes': 50, 'compilacoes': 5}}
    class FakeIA: pass
    
    kg = FakeKG()
    ia = FakeIA()
    
    if 'status' in loader._comandos:
        print('\n2. Executando cmd_status:')
        r = loader.executar('status', kg, ia, [])
        print(f'   Resultado: {r}')
    
    if 'grep' in loader._comandos:
        print('\n3. Executando cmd_grep:')
        r = loader.executar('grep', kg, ia, ['busca', '--literal'])
        print(f'   Resultado: {r}')
    
    print('\n4. Refresh (hot-reload):')
    loader.refresh()
    loader.listar()
    
    print('\n5. Performance:')
    import time
    t0 = time.perf_counter()
    for _ in range(1000):
        _ = loader._comandos.get('status')
    t = time.perf_counter() - t0
    print(f'   1000 lookups em {t*1000:.2f}ms = {t/1000*1e6:.1f}us/lookup')
    
    print('\n' + '='*60)
    print('TESTE CONCLUIDO')
    print('='*60)

if __name__ == '__main__':
    testar()
