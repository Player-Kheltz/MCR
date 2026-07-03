#!/usr/bin/env python3
"""MCR estuda lore sobre Eridanus e gera narrativa."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'mcr_devia'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from modulos.MCR import MCRDocIndex, MCRSignature, MCRConector, MCRCadeia, MCRPergunta, MCRAssinatura

print('=' * 60)
print('FASE 1: MCR ESTUDA DOCS SOBRE ERIDANUS')
print('=' * 60)

idx = MCRDocIndex()
idx.indexar()

# Busca todos os docs sobre Eridanus
docs_eridanus = []
for termo in ['Eridanus', 'cidade', 'lendaria', 'simplicidade', 'aventureiro', 'fundada', 'cristal', 'tutorial']:
    docs = idx.buscar(termo)
    for d in docs:
        if d not in docs_eridanus:
            docs_eridanus.append(d)

print(f'Docs sobre Eridanus encontrados: {len(docs_eridanus)}')
for d in docs_eridanus:
    print(f'  {d["caminho"]} ({d["tamanho"]} bytes)')

# Le o conteudo de CADA doc e alimenta o MCRConector + KG
print()
print('=' * 60)
print('FASE 2: MCR APRENDE COM OS DOCS (conector + KG)')
print('=' * 60)

conector = MCRConector()
total_bytes = 0

for doc in docs_eridanus[:10]:
    conteudo = idx.ler(doc['caminho'], 2000)
    if conteudo and len(conteudo) > 50:
        nome = f"doc_{os.path.basename(doc['caminho']).replace('.','_').replace(' ','')}"
        conector.alimentar(conteudo[:1500], nome)
        total_bytes += len(conteudo)
        print(f'  Alimentado: {nome} ({len(conteudo)} chars)')

# Tambem le o MCR_IDENTITY.md
identity = idx.ler('docs/MCR_IDENTITY.md', 2000)
if identity:
    conector.alimentar(identity[:1500], 'mcr_identity')
    total_bytes += len(identity)
    print(f'  Alimentado: MCR_IDENTITY.md ({len(identity)} chars)')

print(f'  Total: {len(conector.topicos)} topicos, {total_bytes} chars')

# Assinatura do que foi aprendido
print()
print('=' * 60)
print('FASE 3: ASSINATURA DO CONHECIMENTO')
print('=' * 60)

texto_total = ' '.join([d.get('texto', '') for d in conector.topicos.values()])
sig = MCRSignature.extrair(texto_total.encode('utf-8') if texto_total else b'eridanus')
print(f'Assinatura: entropia={sig["entropia"]}, estados={sig["estados"]}, transicoes={sig["transicoes"]}')
print(f'Fingerprint: {[round(x,2) for x in sig.get("fingerprint", [])[:5]]}')

# Analisa os niveis que emergem
print()
print('=' * 60)
print('FASE 4: MCR MetaNiveis sobre Eridanus')
print('=' * 60)

from modulos.MCR import MCRMetaNivel
meta = MCRMetaNivel()
meta.alimentar(texto_total.encode('utf-8')[:2000] if texto_total else b'eridanus')
diag = meta.diagnosticar()
print(f'Niveis: {diag["n_niveis"]} {diag.get("ordem", [])}')
print(f'Energia: {diag.get("energia_total", 0):.2f}')

# Gera lore!
print()
print('=' * 60)
print('FASE 5: MCR GERA LORE SOBRE ERIDANUS')
print('=' * 60)

# Usa o conector alimentado + cadeia
cadeia = MCRCadeia(conector)
resultado = cadeia.gerar('Eridanus', n_tokens=100)
texto = resultado.get('texto', '')
print(f'Lore gerada ({len(texto)} chars):')
print()
print(texto[:500])
print()
print(f'Nota: {resultado.get("nota", 0)}/10')
print(f'Loops: {resultado.get("loops_detectados", 0)}')

print()
print('=' * 60)
print('DIAGNOSTICO')
print('=' * 60)
av_sem = __import__('modulos.MCR', fromlist=['AutoavaliadorSemantico']).AutoavaliadorSemantico()
av = av_sem.avaliar(texto, 'lore') if hasattr(av_sem, 'avaliar') else {'nota':0}
print(f'Nota semantica: {av.get("nota", 0)}/10')
print(f'Diagnostico: {av.get("diagnostico", "?")}')
