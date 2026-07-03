"""Teste de persistencia do MCR."""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from MCR import *

# --- SALVAR ---
motor = MCRMotor()
motor.alimentar('SPA e o sistema de progressao do aventureiro com dominios elementais Fogo Gelo Terra', 'spa')
motor.alimentar('SHC e o sistema de habilidades contextuais com 5 camadas postura nivel sinergia estado', 'shc')
motor.alimentar('O NPC ferreiro em Eridanus se chama Bruno Ferro Forte e vende armaduras na praca central', 'npc')

# Conecta para gerar experiencia
c = motor.conectar('spa', 'shc')
print(f'Conexao spa+shc: nota={c["nota"]}')

tmp = tempfile.mktemp(suffix='.json')
ok = motor.salvar(tmp)
print(f'Salvou: {ok}')
print(f'Topicos salvos: {len(motor.topicos)}')
print(f'Conexoes salvas: {motor.total_conexoes}')
print()

# --- CARREGAR (motor novo) ---
motor2 = MCRMotor()
ok2 = motor2.carregar(tmp)
print(f'Carregou: {ok2}')
print(f'Topicos carregados: {len(motor2.topicos)}')
print(f'Nomes: {list(motor2.topicos.keys())}')
print(f'Conexoes: {motor2.total_conexoes}')
print(f'Byte estados: {motor2.mk_byte.stats()["estados"]}')
print(f'Palavra estados: {motor2.mk_palavra.stats()["estados"]}')

# Verifica se conexao ainda funciona
c2 = motor2.conectar('spa', 'shc')
print(f'Reconexao spa+shc: {c2["nota"] if c2 else "None"}')
print()

# --- FERRAMENTAS COM CARREGAMENTO ---
motor3 = MCRMotor()
motor3.carregar(tmp)
ferr = MCRFerramentas(motor3)
r = ferr.executar('Crie um NPC ferreiro em Eridanus', r'E:\Projeto MCR')
print(f'Ferramentas apos carregar:')
print(f'  Resposta: {r["resposta"][:100]}')
print(f'  Nota: {r["nota"]}')
print(f'  Salvo em: {r.get("salvo_em", "?")}')
print()

# --- LIMPEZA ---
os.remove(tmp)
print('Persistencia OK!')
