#!/usr/bin/env python3
"""Adiciona --serve e --dashboard ao kernel.py."""
kpath = r'E:\Projeto MCR\scripts\mcr_devia\kernel.py'
with open(kpath, 'r', encoding='utf-8') as f:
    content = f.read()

old_marker = "    else:\n        resultado = k.executar(cmd, args)\n        if not resultado:\n            print(f'[Kernel] Comando nao encontrado: {cmd}')\n\nif __name__"

new_block = """    elif cmd == '--serve':
        # Modo servidor: aguarda comandos em .mcr_cmd.json"""
        import time as _ts
        _js_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sandbox', '.mcr_cmd.json')
        print('[Serve] Aguardando .mcr_cmd.json... (Ctrl+C para sair)')
        try:
            while True:
                if os.path.exists(_js_path):
                    try:
                        import json as _js
                        with open(_js_path, encoding='utf-8') as _f:
                            _d = _js.load(_f)
                        if not _d.get('_executado'):
                            _cmd = _d.get('cmd', '')
                            _args = _d.get('args', [])
                            if _cmd:
                                k.executar(_cmd, _args)
                            _d['_executado'] = True
                            with open(_js_path, 'w', encoding='utf-8') as _fw:
                                _js.dump(_d, _fw, ensure_ascii=False)
                    except: pass
                _ts.sleep(1)
        except KeyboardInterrupt:
            print('[Serve] Finalizado')
    elif cmd == '--dashboard':
        # Dashboard web simples
        from http.server import HTTPServer, BaseHTTPRequestHandler
        class _DashHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                html = '<html><head><title>MCR-DevIA</title>'
                html += '<style>body{font-family:sans-serif;margin:20px;background:#1a1a2e;color:#eee;}'
                html += '.card{background:#16213e;border-radius:8px;padding:15px;margin:10px 0;}</style>'
                html += '</head><body><h1>MCR-DevIA Dashboard</h1>'
                html += f'<div class=card><h2>KG</h2><p>Comandos: {len(k.loader._cache)}</p></div>'
                html += '<div class=card><h2>Memoria</h2><p>Ativa</p></div>'
                html += '</body></html>'
                self.wfile.write(html.encode('utf-8'))
        print('[Dashboard] http://localhost:8765')
        HTTPServer(('', 8765), _DashHandler).serve_forever()
    else:
        resultado = k.executar(cmd, args)
        if not resultado:
            print(f'[Kernel] Comando nao encontrado: {cmd}')

if __name__'''

if old_marker in content:
    content = content.replace(old_marker, new_block)
    with open(kpath, 'w', encoding='utf-8') as f:
        f.write(content)
    try:
        compile(content, kpath, 'exec')
        print('OK')
    except SyntaxError as e:
        print(f'ERRO: {e}')
else:
    print('Marcador nao encontrado')
    for i, line in enumerate(open(kpath, encoding='utf-8')):
        if 'else:' in line and 330 < i < 350:
            print(f'L{i+1}: {line.rstrip()}')
