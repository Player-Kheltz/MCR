"""Debug do Decider - ver o que o FAST retorna."""
import sys
sys.path.insert(0, 'E:/Projeto MCR/Scripts/mcr_devia')
from modulos.ia import IA

ia = IA()

# Test 1: 
prompt1 = (
    "Se mencao MCR/Tibia = local. Senao = cloud.\n"
    "Classifique em UMA das categorias abaixo.\n"
    "Categorias: local, cloud\n"
    "Texto: pesquise python 3.13\n"
    "Categoria:"
)
resp1 = ia.fast(prompt1, 0.1, "leve")
print(f"TESTE 1 - com instrucao:")
print(f"  PROMPT: {prompt1}")
print(f"  RESPOSTA: {resp1!r}")

# Test 2: sem instrucao extra
prompt2 = (
    "Classifique em UMA das categorias abaixo.\n"
    "Categorias: local, cloud\n"
    "Texto: pesquise python 3.13\n"
    "Categoria:"
)
resp2 = ia.fast(prompt2, 0.1, "leve")
print(f"\nTESTE 2 - sem instrucao:")
print(f"  PROMPT: {prompt2}")
print(f"  RESPOSTA: {resp2!r}")

# Test 3: ordem invertida
prompt3 = (
    "Classifique em UMA das categorias abaixo.\n"
    "Categorias: cloud, local\n"
    "Texto: pesquise python 3.13\n"
    "Categoria:"
)
resp3 = ia.fast(prompt3, 0.1, "leve")
print(f"\nTESTE 3 - ordem invertida:")
print(f"  PROMPT: {prompt3}")
print(f"  RESPOSTA: {resp3!r}")
