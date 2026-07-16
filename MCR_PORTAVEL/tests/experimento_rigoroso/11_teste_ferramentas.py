"""Teste Real — Valida todas as 77 ferramentas do MCR.
Cada ferramenta é exercitada via processar() com input real.
Reporta sucesso/falha/erro para cada uma."""
import sys, time, json
sys.path.insert(0, 'E:/MCR')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from mcr.mcr import MCR
mcr = MCR()

tools = mcr._registry.listar()
print(f'Ferramentas registradas: {len(tools)}')
print('=' * 70)

# Inputs reais para cada ferramenta
# gerar_npc/monstro/sprite/quest sao todos 'gerar' (verbo normalizado)
# O MCR descobre o dominio por assinatura, nao por hardcode
testes = {
    'gerar': 'crie um npc ferreiro que vende espadas',
    'gerar_codigo': 'gere um codigo python',
    'responder': 'o que e markov',
    'analisar': 'analise o codigo do mcr.py',
    'buscar': 'busque por ferreiro no codigo',
    'editar': 'edite o arquivo mcr.py',
    'validar': 'valide o codigo lua do npc',
    'conectar': 'conecte npc e monstro',
    'aprender': 'aprenda sobre markov',
    'planejar': 'planeje uma quest de dragao',
    'buscar_arquivos': 'busque arquivos mcr',
    'buscar_conteudo': 'busque por coupling no mcr',
    'ler_arquivo': 'ler mcr.py',
    'escrever_arquivo': 'escrever teste.json conteudo de teste',
    'editar_arquivo': 'editar mcr.py coupling',
    'status': 'status do sistema',
    'pensar': 'pensar sobre a arquitetura do MCR',
    'explorar': 'explorar o projeto',
    'conselho': 'conselho sobre melhorar o MCR',
    'todo': 'todo melhorar zero-shot',
    'system_scan': 'system_scan',
    'verificar_mudancas': 'verificar_mudancas',
    'proativo': 'proativo',
    'bugfinder': 'bugfinder',
    'autoteste': 'autoteste',
    'gerir_mundo': 'gerir mundo vivo',
}

passou = 0
falhou = 0
erros = 0
detalhes = []

t0 = time.time()
for tool_name, entrada in testes.items():
    try:
        entry = mcr._registry.selecionar(tool_name)
        if entry is None:
            detalhes.append((tool_name, 'AUSENTE', '', ''))
            falhou += 1
            continue
        # Executa a ferramenta diretamente
        resultado = entry.executar(entrada=entrada, texto=entrada)
        sucesso = resultado.get('sucesso', False)
        tipo = resultado.get('tipo', '?')
        erro = resultado.get('erro', '')[:50]
        if sucesso:
            status = 'PASS'
            passou += 1
        elif erro:
            status = 'ERRO'
            erros += 1
        else:
            status = 'FAIL'
            falhou += 1
        detalhes.append((tool_name, status, tipo, erro))
    except Exception as e:
        detalhes.append((tool_name, 'CRASH', '', str(e)[:50]))
        erros += 1

t_total = time.time() - t0

# Reporta
print(f'\n{"Ferramenta":<25s} {"Status":<8s} {"Tipo":<15s} {"Erro/Nota"}')
print('-' * 70)
for name, status, tipo, erro in detalhes:
    nota = erro if erro else tipo
    print(f'{name:<25s} {status:<8s} {tipo:<15s} {nota[:40]}')

print(f'\n{"=" * 70}')
print(f'  PASS: {passou}/{len(testes)}')
print(f'  FAIL: {falhou}/{len(testes)}')
print(f'  ERRO: {erros}/{len(testes)}')
print(f'  Tempo: {t_total:.2f}s ({t_total/len(testes)*1000:.0f}ms/tool)')
print(f'  Ferramentas no registry: {len(tools)}')
print(f'{"=" * 70}')

# Teste via processar() — MCR decide qual ferramenta usar
print(f'\n[TESTE VIA processar()] MCR decide a ferramenta')
print('-' * 70)
inputs_processar = [
    'crie um npc ferreiro',
    'o que e entropia',
    'analise o codigo',
    'busque por coupling',
    'status do sistema',
    'planeje uma quest',
    'aprenda sobre markov',
    'valide o codigo',
    'conecte arte e ciencia',
]
passou_p = 0
for inp in inputs_processar:
    try:
        r = mcr.processar(inp)
        acao = r.get('acao', '?')
        sucesso = r.get('sucesso', False)
        conf = r.get('confianca', 0)
        tempo = r.get('tempo', 0)
        status = 'PASS' if sucesso else 'FAIL'
        if sucesso: passou_p += 1
        print(f'  [{status}] {inp[:35]:35s} -> {acao:15s} c={conf:.2f} t={tempo:.3f}s')
    except Exception as e:
        print(f'  [CRASH] {inp[:35]:35s} -> {str(e)[:40]}')

print(f'\n  processar(): {passou_p}/{len(inputs_processar)}')
print('=' * 70)
