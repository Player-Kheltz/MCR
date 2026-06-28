#!/usr/bin/env python3
"""Adiciona modo servidor (--serve) e dashboard web ao kernel."""
import sys, os

kpath = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(kpath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Modo --serve: apos o ultimo else, adicionar no main_kernel
for i, line in enumerate(lines):
    if 'if cmd == ' in line:
        pass
    
# Encontra final do main_kernel
end_main = None
for i, line in enumerate(lines):
    if line.startswith("if __name__ == '__main__':"):
        end_main = i
        break

if end_main is None:
    print('ERRO: final do main_kernel nao encontrado')
    sys.exit(1)

# Adiciona modo --serve e --dashboard no main_kernel ANTES do if __name__
serve_code = [
    "    elif cmd == '--serve':\n",
    "        '''Modo servidor: fica escutando .mcr_cmd.json em loop.'''\n",
    "        import time\n",
    "        _last_cmd = None\n",
    "        print('[Serve] Aguardando comandos em .mcr_cmd.json... (Ctrl+C para sair)')\n",
    "        try:\n",
    "            while True:\n",
    "                _json_path = os.path.join(os.path.dirname(__file__), '..', 'sandbox', '.mcr_cmd.json')\n",
    "                if os.path.exists(_json_path):\n",
    "                    try:\n",
    "                        with open(_json_path, 'r', encoding='utf-8') as _f:\n",
    "                            import json as _js\n",
    "                            _data = _js.load(_f)\n",
    "                        if _data.get('_executado') != True and _data != _last_cmd:\n",
    "                            _last_cmd = _data\n",
    "                            sys.argv = [sys.argv[0], _data.get('cmd',''), *_data.get('args',[])]\n",
    "                            cmd = _data.get('cmd','')\n",
    "                            args = _data.get('args',[])\n",
    "                            if cmd:\n",
    "                                resultado = k.executar(cmd, args)\n",
    "                                _data['_executado'] = True\n",
    "                                _data['_resultado'] = bool(resultado)\n",
    "                                with open(_json_path, 'w', encoding='utf-8') as _fw:\n",
    "                                    _js.dump(_data, _fw, ensure_ascii=False)\n",
    "                    except: pass\n",
    "                time.sleep(1)\n",
    "        except KeyboardInterrupt:\n",
    "            print('[Serve] Finalizado')\n",
    "    elif cmd == '--dashboard':\n",
    "        '''Dashboard web simples.'''\n",
    "        from http.server import HTTPServer, BaseHTTPRequestHandler\n",
    "        import json as _js_dash\n",
    "        class _DashHandler(BaseHTTPRequestHandler):\n",
    "            def do_GET(self):\n",
    "                self.send_response(200)\n",
    "                self.send_header('Content-type', 'text/html; charset=utf-8')\n",
    "                self.end_headers()\n",
    "                # Carrega dados\n",
    "                kg_info = {'licoes':0,'versoes':0}\n",
    "                mem_info = {'total':0}\n",
    "                try:\n",
    "                    ka = MCRKernel()\n",
    "                    ka.inicializar()\n",
    "                    if ka.contexto.get('kg'):\n",
    "                        kg_info = ka.contexto['kg'].data['metricas']\n",
    "                    if ka.contexto.get('memoria'):\n",
    "                        mem_info = ka.contexto['memoria'].estatisticas()\n",
    "                except: pass\n",
    "                html = f'''<html><head><title>MCR-DevIA Dashboard</title>\n",
    "                <style>body{{font-family:sans-serif;margin:20px;background:#1a1a2e;color:#eee;}}\n",
    "                .card{{background:#16213e;border-radius:8px;padding:15px;margin:10px 0;}}\n",
    "                h1{{color:#0f3460;}} .val{{font-size:24px;font-weight:bold;color:#e94560;}}</style>\n",
    "                </head><body>\n",
    "                <h1>MCR-DevIA Dashboard</h1>\n",
    "                <div class=card><h2>Knowledge Graph</h2>\n",
    "                <p>Licoes: <span class=val>{kg_info.get('licoes',0)}</span></p>\n",
    "                <p>Geracoes: <span class=val>{kg_info.get('geracoes',0)}</span></p>\n",
    "                <p>Versoes: <span class=val>{kg_info.get('versoes',0)}</span></p>\n",
    "                </div>\n",
    "                <div class=card><h2>Memoria</h2>\n",
    "                <p>Registros: <span class=val>{mem_info.get('total',0)}</span></p>\n",
    "                <p>Comandos: <span class=val>{mem_info.get('comandos_distintos',0)}</span></p>\n",
    "                </div>\n",
    "                <div class=card><h2>Comandos</h2>\n",
    "                <p>Disponiveis: <span class=val>{k.listar_comandos() if len(str('')) else 0}</span></p>\n",
    "                </div>\n",
    "                </body></html>'''\n",
    "                self.wfile.write(html.encode('utf-8'))\n",
    "        print('[Dashboard] http://localhost:8765')\n",
    "        HTTPServer(('', 8765), _DashHandler).serve_forever()\n",
]

# Insere antes do if __name__
lines.insert(end_main, ''.join(serve_code))

with open(kpath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

try:
    compile(''.join(lines), kpath, 'exec')
    print('OK - Modo --serve e --dashboard adicionados')
except SyntaxError as e:
    print(f'ERRO: {e}')
    sys.exit(1)

# 2. Script de bateria para kernel
test_path = r'E:\Projeto MCR\sandbox\testes_extensivos\bateria_kernel.py'
with open(test_path, 'w', encoding='utf-8') as f:
    f.write('''#!/usr/bin/env python3
"""Bateria de testes para o KERNEL (MCR_DevIA-Kernel.py)."""
import sys, os, time
sys.path.insert(0, r'E:\\Projeto MCR\\scripts\\mcr_devia')
from kernel import MCRKernel

k = MCRKernel()
k.inicializar()

testes = [
    ("status", [], "Status basico"),
    ("glob", ["*.md", "--max", "2"], "Glob arquivos"),
    ("fast", ["teste rapido"], "Fast classification"),
    ("memoria", ["--stats"], "Memoria stats"),
]

print(f'Executando {len(testes)} testes no kernel...')
passou = 0
falhou = 0
for cmd, args, nome in testes:
    try:
        t0 = time.time()
        r = k.executar(cmd, args)
        t = time.time() - t0
        if r:
            print(f'  [PASS] {cmd:15s} {nome:30s} ({t:.1f}s)')
            passou += 1
        else:
            print(f'  [FAIL] {cmd:15s} {nome:30s}')
            falhou += 1
    except Exception as e:
        print(f'  [ERRO] {cmd:15s} {nome:30s}: {e}')
        falhou += 1

print(f'\\nResultado: {passou}/{len(testes)} passaram, {falhou} falharam')
''')

print('OK - Script de bateria criado em testes_extensivos/bateria_kernel.py')

# 3. Le os testes existentes para adaptar
print('\\nProximo passo: adaptar bateria_completa.py para o kernel.')
print('Por hora, a bateria basica com 4 testes esta pronta.')
