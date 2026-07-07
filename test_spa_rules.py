import sys, re, time
sys.path.insert(0, r'E:\MCR')
from mcr_devia import _llm

# Exemplo real de habilidade
codigo_ex = open(r'E:\Projeto MCR\Canary\data-canary\scripts\MCR\SPA\habilidades\espadas_leves.lua', 'r', encoding='iso-8859-1').read()
match = re.search(r'HABILIDADES\[\d+\]\s*=\s*\{[\s\S]*?\n\}', codigo_ex)
codigo_ex = match.group(0)[:1500] if match else codigo_ex[:1500]

regras = (
    'DIRETRIZES OBRIGATORIAS PARA HABILIDADES SPA v2.0:\n'
    '1. E PROIBIDO usar o campo `efeito = function(...)`. NUNCA escreva funcoes Lua.\n'
    '2. Toda a logica DEVE ser declarativa dentro de `efeitoConfig`.\n'
    '3. life_leech = 15 dentro de efeitoConfig, nao em funcao manual.\n'
    '4. NUNCA escreva funcoes manuais para calcular dano ou curar. Apenas parametros.\n'
)

prompt = (
    regras
    + 'Aqui esta um exemplo real de habilidade SPA do Canary:\n\n'
    + '=== EXEMPLO ===\n' + codigo_ex + '\n=== FIM EXEMPLO ===\n\n'
    + 'Agora crie a habilidade:\n'
    + '- Nome: Lanca das Sombras\n'
    + '- Dominio: Morte (id 6)\n'
    + '- Nivel minimo: 10, Tipo: gatilho, Categoria: single\n'
    + '- Tipo de efeito: dano_extra, life_leech: 15\n'
    + '- Foco minimo: 50\n'
    + '- Use efeitoConfig com tipo=dano_extra, life_leech, elemento.\n'
    + '- NAO use efeito = function(). Use APENAS efeitoConfig.\n'
    + '- Responda APENAS com o codigo HABILIDADES[ID] = { ... }\n'
)

t0 = time.time()
resp = _llm.gerar(prompt, modelo='qwen2.5-coder:7b', temp=0.3)
t = time.time() - t0

print(f'Tempo: {t:.1f}s')
print(resp[:1500])
print()

has_function = 'function' in resp and ('efeito' in resp.split('function')[0][-20:] if 'function' in resp else False)
checks = [
    ('efeitoConfig com tipo', 'efeitoConfig' in resp and 'tipo' in resp),
    ('dano_extra', 'dano_extra' in resp),
    ('life_leech', 'life_leech' in resp),
    ('SEM function manual', not ('efeito = function' in resp or 'efeito=function' in resp.replace(' ', ''))),
    ('SEM function em geral', 'function' not in resp),
    ('Categoria single', 'single' in resp),
    ('Dominio 6', '6' in resp),
]
ok = sum(1 for _, v in checks if v)
for nome, v in checks:
    marc = 'OK' if v else 'X'
    print(f'  {marc} {nome}')
print(f'  Total: {ok}/{len(checks)}')
if ok >= 6:
    print('VEREDITO: SPA rules fix funcionou!')
elif 'function' not in resp:
    print('VEREDITO: Quase la, mas faltou life_leech no efeitoConfig')
else:
    print('VEREDITO: Ainda tem funcao manual. Prompt precisa ser mais forte.')
