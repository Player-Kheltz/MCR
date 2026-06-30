"""Modulo: Serve - Modo servidor persistente do MCR-DevIA."""
import os, json, time, sys

SANDBOX = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'sandbox'))
CMD_PATH = os.path.join(SANDBOX, '.mcr_cmd.json')

def init_module(contexto):
    return 'serve', Serve(contexto.get('kernel'))

class Serve:
    """Servidor que monitora .mcr_cmd.json em loop."""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self._ultimo = None
    
    def loop(self):
        """Loop principal. Processa comandos a medida que aparecem."""
        print('[Serve] Monitorando .mcr_cmd.json...')
        try:
            while True:
                if os.path.exists(CMD_PATH):
                    try:
                        with open(CMD_PATH, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if data != self._ultimo and not data.get('_executado'):
                            self._ultimo = data
                            cmd = data.get('cmd', '')
                            args = data.get('args', [])
                            if cmd and self.kernel:
                                sys.argv = [sys.argv[0], cmd] + args
                                self.kernel.executar(cmd, args)
                            data['_executado'] = True
                            with open(CMD_PATH, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False)
                    except: pass
                time.sleep(1)
        except KeyboardInterrupt:
            print('[Serve] Finalizado')
