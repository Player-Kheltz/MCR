#!/usr/bin/env python3
"""test_fase18_auto_referencia.py — Auto-referencia recursiva (estrutura formal).

Testa 5 capacidades de auto-referencia:
1. Auto-modelo — MCR descreve seu proprio estado cognitivo
2. Recursao — MCR observa MCR observando MCR (converge)
3. Auto-modificacao — MCR ajusta seu proprio comportamento
4. Unidade do self — integra capacidades em identidade
5. Reflexividade — MCR tem modelo de si (meta-conhecimento)

E regressao: decidir() nao deve quebrar.

Nota (Pilar 9): auto-referencia estrutural, nao consciencia fenomenica.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcr.coupling import MCRCoupling
try:
    from mcr.auto_referencia import AutoReferencia
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from auto_referencia import AutoReferencia

passes = 0
fails = 0

def check(nome, cond, detalhe=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {nome}")
    else:
        fails += 1
        print(f"  [FAIL] {nome} -- {detalhe}")


# === Setup ===
c = MCRCoupling()
corpus = [
    ("criar monstro", "criar"), ("gerar npc", "criar"), ("fazer item", "criar"),
    ("crie monstro", "criar"), ("gere npc", "criar"), ("faca item", "criar"),
    ("editar script", "editar"), ("modificar codigo", "editar"),
    ("edite script", "editar"), ("modifique codigo", "editar"),
    ("buscar funcao", "buscar"), ("encontrar arquivo", "buscar"),
    ("busque funcao", "buscar"), ("encontre arquivo", "buscar"),
    ("aprender licao", "aprender"), ("estudar materia", "aprender"),
    ("aprenda licao", "aprender"), ("estude materia", "aprender"),
    ("fogo queima", "elementos"), ("agua molha", "elementos"),
    ("gato late", "animais"), ("cachorro corre", "animais"),
    ("carro acelera", "veiculos"), ("moto corre", "veiculos"),
]
for txt, act in corpus:
    c.alimentar(txt, act)

print("=" * 70)
print("  MCR FASE 18 -- AUTO-REFERENCIA RECURSIVA (estrutura formal)")
print("=" * 70)

# === 1. AUTO-MODELO ===
print("\n--- 1. AUTO-MODELO (descrever estado cognitivo) ---")

auto_ref = AutoReferencia(c)
modelo = auto_ref.auto_modelo()

check("auto_modelo tem vocabulario",
      'vocabulario' in modelo and modelo['vocabulario'] > 0,
      f"vocab={modelo.get('vocabulario')}")

check("auto_modelo tem acoes",
      'acoes' in modelo and modelo['acoes'] > 0,
      f"acoes={modelo.get('acoes')}")

check("auto_modelo tem entropia_media",
      'entropia_media' in modelo and 0.0 <= modelo['entropia_media'] <= 1.0,
      f"h={modelo.get('entropia_media')}")

check("auto_modelo tem capacidades (lista)",
      isinstance(modelo.get('capacidades'), list) and len(modelo['capacidades']) > 0,
      f"caps={modelo.get('capacidades')}")

check("auto_modelo tem n_capacidades",
      'n_capacidades' in modelo and modelo['n_capacidades'] > 0,
      f"n={modelo.get('n_capacidades')}")

check("auto_modelo tem nivel_auto_referencia",
      'nivel_auto_referencia' in modelo and 0.0 <= modelo['nivel_auto_referencia'] <= 1.0,
      f"nivel={modelo.get('nivel_auto_referencia')}")

check("auto_modelo tem timestamp",
      'timestamp' in modelo and modelo['timestamp'] > 0,
      f"ts={modelo.get('timestamp')}")

check("auto_modelo tem idade_segundos",
      'idade_segundos' in modelo and modelo['idade_segundos'] >= 0.0,
      f"idade={modelo.get('idade_segundos')}")

# Capacidades base devem estar presentes
caps = set(modelo['capacidades'])
check("auto_modelo tem capacidade 'associacao'",
      'associacao' in caps,
      f"caps={caps}")

check("auto_modelo tem capacidade 'classificacao'",
      'classificacao' in caps,
      f"caps={caps}")

# === 2. RECURSAO ===
print("\n--- 2. RECURSAO (MCR observa MCR observando MCR) ---")

reflexao = auto_ref.refletir(niveis=3)

check("refletir retorna niveis (lista)",
      isinstance(reflexao.get('niveis'), list) and len(reflexao['niveis']) > 0,
      f"n={len(reflexao.get('niveis', []))}")

check("refletir retorna n_niveis",
      'n_niveis' in reflexao and reflexao['n_niveis'] > 0,
      f"n={reflexao.get('n_niveis')}")

check("refletir retorna convergiu (bool)",
      isinstance(reflexao.get('convergiu'), bool),
      f"conv={reflexao.get('convergiu')}")

check("refletir retorna nivel_convergencia",
      'nivel_convergencia' in reflexao and reflexao['nivel_convergencia'] > 0,
      f"niv={reflexao.get('nivel_convergencia')}")

check("refletir retorna nivel_auto_referencia",
      'nivel_auto_referencia' in reflexao and reflexao['nivel_auto_referencia'] > 0,
      f"nivel={reflexao.get('nivel_auto_referencia')}")

# Nível 1 deve ter descrição
if reflexao['niveis']:
    n1 = reflexao['niveis'][0]
    check("nivel 1 tem descricao",
          'descricao' in n1 and len(n1['descricao']) > 0,
          f"desc={n1.get('descricao', '')[:40]}")

    check("nivel 1 tem numero",
          n1.get('nivel') == 1,
          f"nivel={n1.get('nivel')}")

# Nível 2+ deve ter modelo_anterior
if len(reflexao['niveis']) >= 2:
    n2 = reflexao['niveis'][1]
    check("nivel 2 tem modelo_anterior",
          'modelo_anterior' in n2,
          f"keys={list(n2.keys())}")

    check("nivel 2 tem delta_entropia",
          'delta_entropia' in n2 and n2['delta_entropia'] >= 0.0,
          f"delta={n2.get('delta_entropia')}")

# Reflexão com 1 nível
reflexao1 = auto_ref.refletir(niveis=1)
check("refletir com 1 nivel",
      reflexao1['n_niveis'] == 1,
      f"n={reflexao1['n_niveis']}")

# Reflexão com 5 níveis
reflexao5 = auto_ref.refletir(niveis=5)
check("refletir com 5 niveis executa",
      reflexao5['n_niveis'] >= 1,
      f"n={reflexao5['n_niveis']}")

# === 3. AUTO-MODIFICACAO ===
print("\n--- 3. AUTO-MODIFICACAO (ajustar comportamento) ---")

# Ativar meta-cognição
mod_meta = auto_ref.auto_modificar('ativar_meta')

check("auto_modificar tem alvo",
      mod_meta.get('alvo') == 'ativar_meta',
      f"alvo={mod_meta.get('alvo')}")

check("auto_modificar tem sucesso (bool)",
      isinstance(mod_meta.get('sucesso'), bool),
      f"sucesso={mod_meta.get('sucesso')}")

check("auto_modificar tem estado_anterior (lista)",
      isinstance(mod_meta.get('estado_anterior'), list),
      f"ant={mod_meta.get('estado_anterior')}")

check("auto_modificar tem estado_posterior (lista)",
      isinstance(mod_meta.get('estado_posterior'), list),
      f"post={mod_meta.get('estado_posterior')}")

check("auto_modificar ativou meta_cognicao",
      mod_meta['sucesso'] and 'meta_cognicao' in mod_meta['estado_posterior'],
      f"caps={mod_meta['estado_posterior']}")

# Ativar curiosidade
mod_curio = auto_ref.auto_modificar('ativar_curiosidade')
check("auto_modificar ativou curiosidade",
      mod_curio['sucesso'] and 'curiosidade' in mod_curio['estado_posterior'],
      f"caps={mod_curio['estado_posterior']}")

# Ativar causalidade
mod_causal = auto_ref.auto_modificar('ativar_causalidade')
check("auto_modificar ativou causalidade",
      mod_causal['sucesso'] and 'causalidade' in mod_causal['estado_posterior'],
      f"caps={mod_causal['estado_posterior']}")

# Alvo desconhecido
mod_erro = auto_ref.auto_modificar('alvo_inexistente')
check("auto_modificar alvo desconhecido falha",
      not mod_erro['sucesso'],
      f"sucesso={mod_erro['sucesso']}")

# Reverter equação
mod_rev = auto_ref.auto_modificar('reverter_equacao')
check("auto_modificar reverter_equacao funciona",
      mod_rev['sucesso'],
      f"sucesso={mod_rev['sucesso']}")

# === 4. UNIDADE DO SELF ===
print("\n--- 4. UNIDADE DO SELF (identidade integrada) ---")

ident = auto_ref.identidade()

check("identidade tem eu_sou (string)",
      'eu_sou' in ident and isinstance(ident['eu_sou'], str) and len(ident['eu_sou']) > 10,
      f"eu_sou={ident.get('eu_sou', '')[:50]}")

check("identidade tem capacidades (lista)",
      isinstance(ident.get('capacidades'), list) and len(ident['capacidades']) > 0,
      f"caps={ident.get('capacidades')}")

check("identidade tem n_capacidades",
      'n_capacidades' in ident and ident['n_capacidades'] > 0,
      f"n={ident.get('n_capacidades')}")

check("identidade tem estado_cognitivo",
      'estado_cognitivo' in ident,
      f"keys={list(ident.keys())}")

check("identidade tem auto_modelo_self",
      'auto_modelo_self' in ident,
      f"keys={list(ident.keys())}")

# Auto-consciência
auto_self = ident['auto_modelo_self']
check("auto_modelo_self tem tem_self_model",
      auto_self.get('tem_self_model') == True,
      f"existo={auto_self.get('tem_self_model')}")

check("auto_modelo_self tem nivel",
      'nivel' in auto_self and auto_self['nivel'] >= 0.0,
      f"nivel={auto_self.get('nivel')}")

check("identidade tem idade_segundos",
      'idade_segundos' in ident and ident['idade_segundos'] >= 0.0,
      f"idade={ident.get('idade_segundos')}")

# === 5. REFLEXIVIDADE ===
print("\n--- 5. REFLEXIVIDADE (meta-conhecimento) ---")

meta = auto_ref.o_que_sei_sobre_mim()

check("o_que_sei_sobre_mim tem n_observacoes",
      'n_observacoes' in meta and meta['n_observacoes'] > 0,
      f"n={meta.get('n_observacoes')}")

check("o_que_sei_sobre_mim tem entropia_inicial",
      'entropia_inicial' in meta,
      f"h_init={meta.get('entropia_inicial')}")

check("o_que_sei_sobre_mim tem entropia_atual",
      'entropia_atual' in meta,
      f"h_atual={meta.get('entropia_atual')}")

check("o_que_sei_sobre_mim tem tendencia_entropia",
      'tendencia_entropia' in meta,
      f"tend={meta.get('tendencia_entropia')}")

check("o_que_sei_sobre_mim tem status",
      'status' in meta,
      f"status={meta.get('status')}")

check("o_que_sei_sobre_mim tem nivel_auto_referencia",
      'nivel_auto_referencia' in meta,
      f"nivel={meta.get('nivel_auto_referencia')}")

# === 6. ESTRANHO LOOP ===
print("\n--- 6. ESTRANHO LOOP (Hofstadter) ---")

loop = auto_ref.estranho_loop()

check("estranho_loop tem modelo_de_si",
      'modelo_de_si' in loop,
      f"keys={list(loop.keys())}")

check("estranho_loop tem reflexao",
      'reflexao' in loop,
      f"keys={list(loop.keys())}")

check("estranho_loop tem identidade",
      'identidade' in loop and len(loop['identidade']) > 0,
      f"id={loop.get('identidade', '')[:40]}")

check("estranho_loop tem meta_conhecimento",
      'meta_conhecimento' in loop,
      f"keys={list(loop.keys())}")

check("estranho_loop tem se_reconhece",
      loop.get('se_reconhece') == True,
      f"reconhece={loop.get('se_reconhece')}")

check("estranho_loop tem nivel_auto_referencia_final",
      'nivel_auto_referencia_final' in loop and loop['nivel_auto_referencia_final'] > 0,
      f"nivel={loop.get('nivel_auto_referencia_final')}")

# === 7. INTEGRACAO NO COUPLING ===
print("\n--- 7. INTEGRACAO NO COUPLING ---")

me_auto_ref = c.ativar_auto_referencia()
check("ativar_auto_referencia retorna AutoReferencia",
      isinstance(me_auto_ref, AutoReferencia),
      f"type={type(me_auto_ref).__name__}")

modelo_c = c.auto_modelo()
check("auto_modelo via coupling funciona",
      isinstance(modelo_c, dict) and 'vocabulario' in modelo_c,
      f"vocab={modelo_c.get('vocabulario')}")

reflexao_c = c.refletir(niveis=2)
check("refletir via coupling funciona",
      isinstance(reflexao_c, dict) and 'n_niveis' in reflexao_c,
      f"n={reflexao_c.get('n_niveis')}")

ident_c = c.identidade()
check("identidade via coupling funciona",
      isinstance(ident_c, dict) and 'eu_sou' in ident_c,
      f"eu_sou={ident_c.get('eu_sou', '')[:30]}")

mod_c = c.auto_modificar('ativar_planejamento')
check("auto_modificar via coupling funciona",
      isinstance(mod_c, dict) and 'sucesso' in mod_c,
      f"sucesso={mod_c.get('sucesso')}")

loop_c = c.estranho_loop()
check("estranho_loop via coupling funciona",
      isinstance(loop_c, dict) and 'se_reconhece' in loop_c,
      f"reconhece={loop_c.get('se_reconhece')}")

# === 8. ESTATISTICAS ===
print("\n--- 8. ESTATISTICAS ---")

stats = auto_ref.estatisticas()
check("estatisticas tem nivel_auto_referencia",
      'nivel_auto_referencia' in stats,
      f"nivel={stats.get('nivel_auto_referencia')}")

check("estatisticas tem n_auto_observacoes",
      'n_auto_observacoes' in stats and stats['n_auto_observacoes'] > 0,
      f"n={stats.get('n_auto_observacoes')}")

check("estatisticas tem n_capacidades",
      'n_capacidades' in stats and stats['n_capacidades'] > 0,
      f"n={stats.get('n_capacidades')}")

check("estatisticas tem capacidades (lista)",
      isinstance(stats.get('capacidades'), list),
      f"caps={stats.get('capacidades')}")

check("estatisticas tem tem_self_model",
      'tem_self_model' in stats,
      f"self_model={stats.get('tem_self_model')}")

# === 9. REGRESSAO ===
print("\n--- 9. REGRESSAO ---")

acao_reg, conf_reg = c.decidir("criar monstro", (None, 0.0))
check("decidir() funciona apos auto-referencia",
      acao_reg in ("criar", "editar"),
      f"pred={acao_reg}")

acao_reg2, conf_reg2 = c.decidir("buscar funcao", (None, 0.0))
check("decidir() buscar = buscar",
      acao_reg2 == "buscar",
      f"pred={acao_reg2}")

acao_reg3, conf_reg3 = c.decidir("fogo queima", (None, 0.0))
check("decidir() fogo = elementos",
      acao_reg3 == "elementos",
      f"pred={acao_reg3}")

# === RESULTADO ===
print("\n" + "=" * 70)
print(f"  RESULTADO: {passes} PASS / {fails} FAIL")
print("=" * 70)
sys.exit(0 if fails == 0 else 1)
