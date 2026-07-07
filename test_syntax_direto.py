"""Teste direto do LuaSyntaxValidator sem cache."""
import sys, time
sys.path.insert(0, r'E:\MCR')

from PipelineExecutor import _dedup_resposta
from LuaSyntaxValidator import validar_com_loop
from mcr_devia import _llm

# Codigo Lua que vai ser gerado pelo LLM
prompt = (
    "Crie UMA habilidade SPA para o dominio Energia (26). "
    "Nome: Trovoada Arcana. Tipo: gatilho. "
    "Use a estrutura HABILIDADES[ID] = { ... } com efeitoConfig "
    "incluindo tipo=dano_extra, elemento=COMBAT_ENERGYDAMAGE. "
    "Nao use function manual. Responda APENAS com o codigo Lua."
)

print('Gerando habilidade via LLM...')
t0 = time.time()
resp = _llm.gerar(prompt, modelo='qwen2.5-coder:7b', temp=0.3)
print(f'LLM: {time.time()-t0:.1f}s, {len(resp)} chars')

# Valida sintaxe (simulando o pipeline)
print('\nValidando sintaxe...')
t0 = time.time()
codigo_final, sintaxe_ok, tentativas, erros = validar_com_loop(
    codigo=resp,
    classe='criar_habilidade_spa',
    llm_func=_llm.gerar,
    modelo='qwen2.5-coder:7b',
    max_tentativas=3,
)
print(f'Validator: {time.time()-t0:.1f}s')
print(f'Sintaxe OK: {sintaxe_ok}')
print(f'Tentativas: {tentativas}')
if erros:
    print(f'Erros: {erros}')

# Dedup
codigo_final = _dedup_resposta(codigo_final)
print(f'\n=== CODIGO FINAL ({len(codigo_final)} chars) ===')
print(codigo_final[:800])
print('=== FIM ===')
