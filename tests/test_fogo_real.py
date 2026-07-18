"""TESTE DE FOGO REAL — MCR pipeline completo + LLMs.

Não testa LLM cru. Testa o MCR com LLM plugado:
  MarkovDecider → Cache → Contexto → Golden Examples → LLM → 
  SanityValidator → ShadowCanary → LuaValidator → Canonização
"""
import sys, json, time
sys.path.insert(0, 'E:/MCR')
sys.path.insert(0, 'E:/MCR/devia/kernel')

from mcr.config_llm import MODELO_CODIGO, MODELO_LORE
print('=' * 65)
print('  TESTE DE FOGO — MCR Pipeline Completo')
print(f'  Qwen3.5:9b (codigo) + Gemma4:12b (lore)')
print('=' * 65)
t_global = time.time()

# ─── TESTE 1: NPC via PipelineCompleto ──────────────────────
print('\n[1] MCR PipelineCompleto — NPC com Golden Examples')
print('-' * 55)
t0 = time.time()

from mcr.pipeline_completo import PipelineCompleto
pipe = PipelineCompleto()

# Usa o pipeline COMPLETO: classificação + contexto + golden + LLM + validação
resultado = pipe.processar("Crie um NPC ferreiro anão chamado Brunin Forjador")

tempo = time.time() - t0
resposta = resultado.get('resposta', '')
classe = resultado.get('classe', '?')
rota = resultado.get('rota', '?')
validacao = resultado.get('validacao_codigo', {})
valido = validacao.get('valido', False) if validacao else None
modelo = resultado.get('modelo', '?')

print(f'  Classe: {classe} | Rota: {rota} | Modelo: {modelo} | {tempo:.1f}s')
print(f'  Validação código: {"OK" if valido else "FALHA" if valido is not None else "N/A"}')
print(f'  Tamanho resposta: {len(resposta)} chars')
if resposta:
    linhas = resposta.count('\n') + 1
    tem_internal = 'internalNpcName' in resposta
    tem_create = 'Game.createNpcType' in resposta  
    tem_register = 'register' in resposta.lower() and 'npcType' in resposta.lower()
    print(f'  Linhas: {linhas} | internalNpcName={tem_internal} | createNpcType={tem_create} | register={tem_register}')
    print(f'  Preview:')
    for l in resposta.split('\n')[:8]:
        print(f'    {l[:100]}')

# ─── TESTE 2: Monstro via PipelineCompleto ─────────────────
print('\n[2] MCR PipelineCompleto — Monstro com Golden Examples')
print('-' * 55)
t0 = time.time()

resultado2 = pipe.processar("Crie um monstro dragao de lava ancião das profundezas")

tempo2 = time.time() - t0
resposta2 = resultado2.get('resposta', '')
classe2 = resultado2.get('classe', '?')
rota2 = resultado2.get('rota', '?')
validacao2 = resultado2.get('validacao_codigo', {})
valido2 = validacao2.get('valido', False) if validacao2 else None

print(f'  Classe: {classe2} | Rota: {rota2} | {tempo2:.1f}s')
print(f'  Validação: {"OK" if valido2 else "FALHA" if valido2 is not None else "N/A"}')
print(f'  Tamanho: {len(resposta2)} chars')
if resposta2:
    tem_create_m = 'Game.createMonsterType' in resposta2 or 'MonsterType' in resposta2
    tem_register_m = 'register' in resposta2.lower()
    print(f'  createMonsterType={tem_create_m} | register={tem_register_m}')
    print(f'  Preview:')
    for l in resposta2.split('\n')[:5]:
        print(f'    {l[:100]}')

# ─── TESTE 3: Lore via Gemma4 (usando inner_voice) ─────────
print('\n[3] MCR — Geração de Lore com contexto')
print('-' * 55)
t0 = time.time()

try:
    from mcr.mcr_inner_voice import InnerVoice
    voice = InnerVoice()
    # Injeta o modelo de lore
    voice._MODELO_CHAT = MODELO_LORE
    pensamento = voice.pensar()
    if pensamento:
        texto = pensamento.get('pensamento', '')
        print(f'  Pensamento gerado: {len(texto)} chars')
        print(f'  Preview: {texto[:200]}...' if texto else '  VAZIO')
        print(f'  Memoria origem: {pensamento.get("memoria_origem", "?")[:80]}')
        print(f'  Conceito origem: {pensamento.get("conceito_origem", "?")[:80]}')
    else:
        print('  Sem memorias para gerar pensamento')
except Exception as e:
    print(f'  InnerVoice indisponivel: {e}')

# ─── RESULTADO ─────────────────────────────────────────────
print(f'\n{"="*65}')
print(f'  RESULTADO FINAL — {time.time()-t_global:.0f}s')
print(f'{"="*65}')
print(f'  MCR Pipeline: {"OK" if valido else "FALHA estrutural" if valido is not None else "N/A"}')
print(f'  NPC gerado: {len(resposta)} chars, {rota}')
print(f'  Monstro gerado: {len(resposta2)} chars, {rota2}')
print(f'  Lore gerado via InnerVoice')
print(f'  Modelos: Qwen3.5:9b + Gemma4:12b')
print(f'{"="*65}')
