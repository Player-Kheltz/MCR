#!/usr/bin/env python3
"""Adiciona metodo _gerar_componentes_auto ao conselho.py."""
path = r'E:\Projeto MCR\scripts\mcr_devia\modulos\conselho.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new = [
    '    def _gerar_componentes_auto(self, tema):\n',
    '        """Gera componentes se nao existirem no KG."""\n',
    '        if not self.auto_componentes or not self.kg: return ""\n',
    '        print("  [Componentes] Gerando automaticamente...")\n',
    '        from modulos.util import fast as _fast\n',
    '        for tipo, prompt in [\n',
    '            ("Personagens", "Crie 3 personagens para " + tema + " em Tibia. Formato: Nome | Funcao"),\n',
    '            ("Locais", "Crie 2 locais para " + tema + " em Tibia. Formato: Local | Descricao"),\n',
    '            ("Artefatos", "Crie 2 artefatos para " + tema + " em Tibia. Formato: Artefato | Descricao"),\n',
    '        ]:\n',
    '            r = _fast(prompt, 0.3, "leve") or ""\n',
    '            if r:\n',
    '                self.kg.aprender(tipo + ": " + tema, "Gerado", r[:500], "componente_historia")\n',
    '        return self._buscar_componentes(tema)\n',
    '\n',
]

for i, line in enumerate(lines):
    if 'def _ctx' in line:
        for j, l in enumerate(new):
            lines.insert(i + j, l)
        break

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

try:
    compile(''.join(lines), path, 'exec')
    print('OK')
except SyntaxError as e:
    print('ERRO:', e)
