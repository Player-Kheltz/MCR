import sys
sys.path.insert(0, r"E:\Projeto MCR\scripts\mcr_devia")
from comandos.cmd_perguntar import execute
print("Import OK")
from comandos.cmd_intencao import execute as int_execute
print("Intencao alias OK")
from comandos.cmd_orquestrar import execute as orq_execute
print("Orquestrar alias OK")
