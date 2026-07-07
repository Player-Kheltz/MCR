import sys, time
sys.path.insert(0, r'E:\MCR')
from LuaSyntaxValidator import verificar_sintaxe, validar_com_loop
from mcr_devia import _llm

# Codigo com erro de sintaxe (falta end)
codigo_erro = '''
HABILIDADES[ID] = {
    nome = "Teste",
    tipo = "gatilho",
}

function processar(player)
    if player:getLevel() > 10 then
        print("ok")
'''

print("=== VALIDACAO COM AUTO-CORRECAO ===")
t0 = time.time()
codigo_final, valido, tentativas, erros = validar_com_loop(
    codigo=codigo_erro,
    classe='criar_habilidade_spa',
    llm_func=_llm.gerar,
    modelo='qwen2.5-coder:7b',
    max_tentativas=2,
)
t = time.time() - t0

print(f'[VALIDO] {valido}')
print(f'[TENTATIVAS] {tentativas}')
print(f'[ERROS] {erros}')
print(f'[TEMPO] {t:.1f}s')
print(f'\n=== CODIGO CORRIGIDO ===')
print(codigo_final[:800])
print('=== FIM ===')
