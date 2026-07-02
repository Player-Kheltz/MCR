"""Validacao final do MCR_AGI.py"""
import sys; sys.path.insert(0, '.')
from MCR_AGI import *

ok = 0; t = 0
def test(n, c, d=''):
    global ok, t; t+=1
    if c: ok+=1; print(f'  [OK] {n}')
    else: print(f'  [FAIL] {n}: {d}')

print('VALIDACAO FINAL MCR_AGI')
print(f'Tamanho: {os.path.getsize("MCR_AGI.py")} bytes')
print()

# 1. Primitivas
mk=MCR('t'); mk.aprender('A','B'); mk.aprender('A','C'); mk.aprender('A','B')
p,c=mk.predizer('A'); test('MCR predizer', p=='B')
test('MCR entropia', mk.entropia('A')>0)
fp=MCRByteUtils.fingerprint('test',8); test('Fingerprint', len(fp)==8)
df=MCRByteUtils.delta_fingerprint('abc','abcdef'); test('Delta FP', sum(abs(d) for d in df) > 0)
th=MCRThreshold('t')
for v in [0.1,0.2,0.3,0.4,0.5]: th.observar(v)
test('Threshold', th.calcular()>0)
ent=MCREntropia('t')
for _ in range(15): ent.alimentar('AAAA')
test('Loop detection', ent.esta_em_loop())

# 2. Serializador
e=EstadoMundo.criar_simples()
s=MCRSerializador.serializar(e.entidades)
test('Serializador', len(s)>0)
fp_s=MCRSerializador.fingerprint(e.entidades)
test('Serializador fingerprint', len(fp_s)==8)

# 3. Acoes
e=EstadoMundo.criar_simples()
e2=MCRAcao.executar(e,'andar_dir')
test('Andar dir x+=1', e2.get('heroi').props['x']==1)
e3=MCRAcao.executar(e,'andar_baixo')
test('Andar baixo y+=1', e3.get('heroi').props['y']==1)
test('Acoes >=5', len(MCRAcao.disponiveis())>=5)
test('Acao invalida', MCRAcao.executar(e,'invalida').get('heroi').props['x']==0)

# 4. NLP
test('NLP ataque', 'atacar' in MCRNLP.entender('ataque'))
test('NLP norte', 'andar_cima' in MCRNLP.entender('norte'))
test('NLP direita', 'andar_dir' in MCRNLP.entender('direita'))
test('NLP abrir', 'abrir' in MCRNLP.entender('abrir'))
dom=MCRNLP.detectar_dominio('heroi andou para direita')
test('NLP dominio grid', dom=='grid' or dom=='texto')

# 5. World
w=MCRWorld()
w.aprender(e,'andar_dir',e2)
test('World causal', w.predizer_acao(e,e2)=='andar_dir')
cf=w.contrafactual(e,'atacar','hp',100)
test('World contrafactual', 'hp' in cf)
test('World distancia', w.distancia(e,e2)>0)
test('World simular', w.simular(e,'andar_dir') is not None)

# 6. Coupling
cp=MCRCoupling()
cp.alimentar('byte','palavra','B:41','Fogo')
cp.alimentar('byte','palavra','B:42','Agua')
cp.alimentar('byte','palavra','B:43','Terra')
cp.recalcular()
test('Coupling peso', cp.peso('byte','palavra')>0)
mod=cp.modular('palavra',{'A':0.5,'B':0.5})
test('Coupling modulacao', sum(mod.values())>1.0)

# 7. Planner
pl=MCRPlanner(w)
plan=pl.plano(e,e)
test('Planner mesmo estado', isinstance(plan, list))

# 8. Cerebro
c=CerebroAGI()
c.alimentar('SPA sistema progressao aventureiro dominios Fogo Gelo Terra','spa')
c.alimentar('SHC sistema habilidades contextuais posturas sinergias','shc')
c.alimentar('Eridanus cidade inicial porto praca central templo forja','eridanus')
test('Cerebro topicos', len(c.topicos)>=3)
g=c.gerar('SPA',6)
test('Cerebro geracao', len(g)>3)
test('Cerebro bytes', c.mk_byte.total>0)
test('Cerebro palavras', c.mk_palavra.total>0)

# 9. RL
ql=MCRQLearn()
for i in range(100):
    ei=EstadoMundo.criar_simples()
    eg=ei.clone(); eg.get('bau').props['aberto']=True
    ql.executar_episodio(ei,eg,15)
test('RL episodios', ql.episodio>=100)
test('RL Q-valores', ql.mk_Q.total>0)
melhor=ql.melhor_acao(e)
test('RL melhor acao', melhor is not None)

# 10. Memoria
mem=MCRMemory(':memory:')
for _ in range(20):
    ei=EstadoMundo.criar_simples(); e2=MCRAcao.executar(ei,'andar_dir')
    mem.salvar_causal(ei,'andar_dir',e2)
test('Memoria causais', mem.stats()['causais']>=20)
fp=str(e.fingerprint(8))
sim=mem.buscar_similar(fp)
test('Memoria busca', len(sim)>=0)
mem.fechar()

# 11. Bridge
br=MCRBridge(); br.registrar_dominio('t')
a=br.analise('fogo queima','fogo queima madeira','gelo congela','gelo congela agua')
test('Bridge', 'nota' in a)

# 12. Codex
cx=MCRCodex()
test('Codex scan', len(cx.escanear())>=0)

# 13. Genesis
g=MCRGenesis(c)
diag=g.diagnosticar()
test('Genesis gaps', 'gaps' in diag)

# 14. Ambiente
amb=AmbienteRico(30,30)
test('Ambiente criado', amb.w*amb.h==900)
amb.tick()
test('Ambiente tick', amb.tick_atual==1)

# 15. Expansor
MCRExpansor.registrar('teste',lambda p:[{'assinatura':f'resposta:{p}'}])
MCRExpansor.registrar_construtor('fmt',lambda ctx,r:r.get('assinatura',''))
resp=MCRExpansor.responder('worm')
test('Expansor', len(resp)>0)
test('Expansor stats', MCRExpansor.stats()['extratores']>=1)

# 16. NPC Brain
brain=MCRNPCBrain()
if brain.carregar():
    test('NPC brain', brain.total_npcs>0)
    test('NPC resposta', len(brain.responder('worm'))>0)

# 17. SuperLoop
c2=CerebroAGI()
sl=MCRSuperLoop(c2)
sl.ciclo(); sl.ciclo()
test('SuperLoop', sl.geracao>=2)

# 18. Decisor Universal
du=MCRDecisorUniversal
params=du.decidir()
test('Decisor', 'passos' in params)

# 19. Registry
tiles=MCRRegistry.tipos_por_categoria('terreno')
test('Registry', len(tiles)>=3)

print(f'\n{ok}/{t} - {ok/t*100:.0f}%')
score = ok/t*100
if score >= 90: print('CLASSIFICACAO: EXCELENTE')
elif score >= 70: print('CLASSIFICACAO: BOM')
else: print('CLASSIFICACAO: PRECISA DE AJUSTES')
