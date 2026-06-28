#!/usr/bin/env python3
"""Substitui a montagem final do pipeline por versao com expansao."""
import sys

path = r'E:\Projeto MCR\scripts\mcr_devia\modulos\pipeline.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = """        resposta = self._montar(etapas, resultados)
        print(f'[Pipeline] Total: {len(resposta)}c em {time.time()-t0:.0f}s')
        return resposta"""

new = """        resposta = self._montar(etapas, resultados)
        
        # EXPANSAO DINAMICA via ContextCrew
        if resposta and self.ctx_crew:
            for rodada in range(3):
                gaps = self.ctx_crew.executar(
                    "Analise o texto abaixo. Se estiver COMPLETO e DETALHADO, responda OK. "
                    "Se faltar algo, aponte o que falta especificamente.\\n\\n"
                    + resposta[:800]
                ) or ""
                if not gaps or "OK" in gaps.upper() or len(gaps) < 20:
                    break
                print(f"  [Expansao {rodada+1}] gaps encontrados")
                exp = _gerar(
                    f"Expanda o texto abaixo adicionando especificamente: {gaps[:300]}\\n\\nTexto:\\n{resposta[:1000]}\\n\\nExpandido:",
                    0.4, "code"
                ) or ""
                if len(exp) > 50:
                    resposta = resposta + "\\n\\n" + exp
                else:
                    break
        
        print(f'[Pipeline] Total: {len(resposta)}c em {time.time()-t0:.0f}s')
        return resposta"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    try:
        compile(content, path, 'exec')
        print('OK - expansao dinamica adicionada')
    except SyntaxError as e:
        print('ERRO:', e)
else:
    print('old nao encontrado')
    print('Buscando...')
    if '_montar' in content:
        print('  _montar encontrado')
    if 'self.ctx_crew' in content:
        print('  self.ctx_crew encontrado')
