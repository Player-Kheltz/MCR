#!/usr/bin/env python3
"""Adiciona expansao dinamica ao pipeline."""
path = r'E:\Projeto MCR\scripts\mcr_devia\modulos\pipeline.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

expansion = [
    '\n',
    '        # EXPANSAO DINAMICA via ContextCrew\n',
    '        resposta = self._montar(etapas, resultados)\n',
    '        if resposta and self.ctx_crew:\n',
    '            for rodada in range(3):\n',
    '                gaps = self.ctx_crew.executar(\n',
    '                    "Analise o texto abaixo e identifique FALHAS ou OMISSOES. Se completo, responda OK.\\n\\n"\n',
    '                    + resposta[:800]\n',
    '                ) or ""\n',
    '                if not gaps or "OK" in gaps.upper() or len(gaps) < 20:\n',
    '                    break\n',
    '                print(f"  [Expansao {rodada+1}] Gaps detectados")\n',
    '                exp = _gerar(\n',
    '                    f"Expanda o texto abaixo adicionando: {gaps[:300]}\\n\\nTexto:\\n{resposta[:1000]}\\n\\nExpandido:",\n',
    '                    0.4, "code"\n',
    '                ) or ""\n',
    '                if len(exp) > 50:\n',
    '                    resposta = resposta + "\\n\\n" + exp\n',
    '                else:\n',
    '                    break\n',
    '        print(f\'[Pipeline] Total: {len(resposta)}c em {time.time()-t0:.0f}s\')\n',
    '        return resposta\n',
]

# Insert after line 53 (0-indexed 52)
for idx, line in enumerate(expansion):
    lines.insert(53 + idx, line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

try:
    compile(''.join(lines), path, 'exec')
    print('OK')
except SyntaxError as e:
    print('ERRO:', e)
