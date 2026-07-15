import sys, json, os, time
sys.path.insert(0, "E:/MCR")
print("=" * 70)
print("  MCR CAPABILITY AUDIT — SMOKE TEST")
print("=" * 70)

# TEST 1: Init
print("\n[TEST 1] MCR Initialization...")
t0 = time.time()
from mcr.mcr import MCR
mcr = MCR()
t1 = time.time()
print(f"  Init time: {t1-t0:.2f}s")
print(f"  Tools registered: {len(mcr._registry.listar())}")
print(f"  MK states: {len(mcr.mk.transicoes)}")
print(f"  Observer active: {mcr._obs_ativado}")

print("\n[TEST 2] Registered wrapper tools:")
for name in sorted(mcr._registry.listar()):
    entry = mcr._registry.selecionar(name)
    if entry and entry.dominio == "manual":
        print(f"  * {name}")

print("\n[TEST 3] processar('Crie um NPC ferreiro')...")
r1 = mcr.processar("Crie um NPC ferreiro")
print(f"  sucesso: {r1.get('sucesso')}, acao: {r1.get('acao')}, confianca: {r1.get('confianca')}")
res = r1.get("resultado", {})
print(f"  resultado.sucesso: {res.get('sucesso')}, tipo: {res.get('tipo')}, entidade: {res.get('entidade')}")
print(f"  _tool: {res.get('_tool')}")
codigo = res.get("codigo", "")
if codigo:
    print(f"  codigo ({len(codigo)} chars):")
    for line in codigo.strip().split("\n")[:5]:
        print(f"    {line.rstrip()}")
else:
    print(f"  codigo: EMPTY, erro: {res.get('erro', 'N/A')}")
v = res.get("_validacao", {})
if v:
    print(f"  validacao: valido={v.get('valido')}, checks={v.get('checks')}")

print("\n[TEST 4] processar('Gere um monstro dragao')...")
r2 = mcr.processar("Gere um monstro dragao")
print(f"  sucesso: {r2.get('sucesso')}, acao: {r2.get('acao')}, confianca: {r2.get('confianca')}")
res2 = r2.get("resultado", {})
print(f"  resultado.sucesso: {res2.get('sucesso')}, tipo: {res2.get('tipo')}, entidade: {res2.get('entidade')}")
print(f"  perigo: {res2.get('perigo')}, race: {res2.get('race')}")
codigo2 = res2.get("codigo", "")
if codigo2:
    print(f"  codigo ({len(codigo2)} chars):")
    for line in codigo2.strip().split("\n")[:5]:
        print(f"    {line.rstrip()}")
else:
    print(f"  codigo: EMPTY")

print("\n[TEST 5] processar('O que e Markov?')...")
r3 = mcr.processar("O que e Markov?")
print(f"  sucesso: {r3.get('sucesso')}, acao: {r3.get('acao')}")
res3 = r3.get("resultado", {})
print(f"  resposta: {str(res3.get('resposta', res3.get('saida', '')))[:200]}")

print("\n[TEST 6] Observer...")
if mcr._obs_ativado:
    try:
        obs_stats = mcr.treinar_observador()
        print(f"  delta_H: {obs_stats.get('delta_H')}, cobertura: {obs_stats.get('cobertura')}, pares: {obs_stats.get('pares')}")
    except Exception as ex:
        print(f"  Error: {ex}")
else:
    print("  NOT active")

print("\n[TEST 7] Markov persistence...")
mcr.mk.save()
import glob as _g
for pat in ["E:/MCR/mcr/kernel/markov_*.json", "E:/MCR/cache/markov_*.json"]:
    files = _g.glob(pat)
    print(f"  {pat}: {len(files)} files")
    for f in files:
        print(f"    {os.path.basename(f)}: {os.path.getsize(f)} bytes")

print("\n[TEST 8] Entity Factory...")
from mcr.golden_templates import gerar_npc_canary, gerar_monstro_parametrizado
npc = gerar_npc_canary({"name": "FerreiroTeste", "health": 100, "looktype": 128, "greeting": "Ola!", "job_desc": "Sou ferreiro."})
print(f"  NPC template: {len(npc)} chars, has npcType:register: {'npcType:register' in npc}")
mon = gerar_monstro_parametrizado({"name": "DragaoTeste", "health": 3000, "experience": 8000, "speed": 160, "looktype": 100, "description": "Um dragao feroz.", "race": "blood"})
print(f"  Monster template: {len(mon)} chars, has mType:register: {'mType:register' in mon}")

print("\n[TEST 9] Sprite Motor...")
try:
    from mcr.sprite_corpus import carregar_categoria, listar_categorias
    cats = listar_categorias()
    print(f"  Categories: {len(cats)}")
    if cats:
        fc = list(cats.keys())[0]
        sprites = carregar_categoria(fc, max_sprites=5)
        print(f"  Loaded {len(sprites)} from '{fc}'")
        if len(sprites) >= 3:
            from mcr.mcr_sprite_motor import MCRSpriteMotor
            motor = MCRSpriteMotor()
            motor.treinar(sprites, fc)
            gerados = motor.gerar(n=1)
            print(f"  Generated: {len(gerados)}")
            if gerados:
                print(f"    regions: {len(gerados[0]['regioes'])}, colors: {len(gerados[0]['cores'])}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n[TEST 10] Raciocinador...")
from mcr.raciocinador import Raciocinador
rac = Raciocinador()
rr = rac.raciocinar("Quanto e 15 + 27?")
print(f"  Math: {rr.get('resultado')}, tipo: {rr.get('tipo')}")

print("\n[TEST 11] Metacognicao KG...")
from mcr.metacognicao import Metacognicao
meta = Metacognicao()
s = meta.estatisticas()
print(f"  KG loaded: {s.get('carregado')}, patterns: {s.get('total_padroes')}")
sc, j = meta.calcular_confianca("Crie um NPC ferreiro")
print(f"  NPC confidence: {sc:.2f} - {j}")

print("\n" + "=" * 70)
print("  MCR STATS")
s2 = mcr.estatisticas()
print(f"  Processamentos: {s2['processamentos']}, Ferramentas: {s2['ferramentas']}, Erros: {s2['erros_registrados']}")
print(f"  MK: {s2['markov']['estados']} estados, {s2['markov']['transicoes']} transicoes, H={s2['markov']['entropia_media']}")
print("=" * 70)
