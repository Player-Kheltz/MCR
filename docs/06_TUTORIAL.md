> **Documenta��o hist�rica.** Este documento descreve vers�es anteriores do MCR.
> Para o estado atual, veja [README.md](../README.md) e [MANIFESTO_MCR.md](../MANIFESTO_MCR.md).
# Tutoriais MCR

## Tutorial 1: Análise de Arquivo

```python
from MCR import MCR, MCRByteUtils

# Carrega qualquer arquivo como bytes
with open("meu_arquivo.wav", "rb") as f:
    dados = f.read()

# Entropia dos bytes — quão estruturado é?
h = MCRByteUtils.entropia_bytes(dados)
print(f"Entropia: {h:.3f}")

if h < 1.0:
    print("Tipo: dados muito estruturados (repetitivos)")
elif h < 4.0:
    print("Tipo: dados estruturados (texto, imagem simples)")
elif h < 6.0:
    print("Tipo: dados semi-estruturados")
else:
    print("Tipo: dados aleatórios ou criptografados")

# Fingerprint — assinatura do arquivo
fp = MCRByteUtils.fingerprint(str(dados[:500]), 8)
print(f"Fingerprint: {[round(v, 2) for v in fp]}")
```

## Tutorial 2: Conexão entre Tópicos

```python
from MCR import MCRMotor

motor = MCRMotor()

# Alimenta conhecimento
motor.alimentar("""
SPA significa Sistema de Progressao do Aventureiro.
Gerencia habilidades em dominios elementais como Fogo e Gelo.
Cada dominio tem 25 niveis de habilidade.
""", "spa")

motor.alimentar("""
A arvore de Natal fica na praca central de Eridanus.
As luzes magicas sao acesas resolvendo desafios.
Cada luz acesa da recompensas especiais.
""", "arvore_natal")

# Conecta os dois tópicos
resultado = motor.conectar("spa", "arvore_natal")

if resultado:
    print(f"Nota: {resultado['nota']}/10")
    print(f"Equacao: {resultado['detalhes']['equacao']}")
    print(f"Tipo de ponte: {resultado['tipo_ponte']}")
    print(f"Sequencia gerada: {resultado['sequencia'][:100]}")
else:
    print("Sem conexao viavel entre os topicos")
```

## Tutorial 3: Geração por Assinatura

```python
from MCR import MCRMotor, MCRPiEngine

motor = MCRMotor()
motor.alimentar("""
SPA e o sistema de progressao do aventureiro com dominios
elementais como Fogo, Gelo, Terra, Energia e Sagrado.
Cada dominio tem 25 niveis que o jogador pode evoluir
completando quests e derrotando monstros.
O SPA integra com o SHC para criar experiencias unicas.
""", "spa")

motor.alimentar("""
SHC significa Sistema de Habilidades Contextuais.
Possui 5 camadas: postura, nivel, sinergia, estado e condicao.
As posturas definem o estilo de combate do jogador.
As sinergias combinam dominios elementais para efeitos unicos.
""", "shc")

# Geração que maximiza assinatura (byte + palavra + token)
texto = motor.gerar_por_assinatura("SPA e o sistema de", passos=8)
print(texto)
# "SPA e o sistema de progressao do aventureiro com dominios elementais..."

# Ou usando PiEngine (decide metodo por entropia)
texto2 = MCRPiEngine.continuar_padrao("Crie um NPC ferreiro", motor, 6)
print(texto2)
```

## Tutorial 4: AutoLoop com Checkpoint

```python
import os
from MCR import MCRAutoLoop, MCRMotor

# Cria motor com dados
motor = MCRMotor()
motor.alimentar_json("meus_dados.json")

# AutoLoop com checkpoint automatico
auto = MCRAutoLoop(motor)
resultado = auto.loop("spa", "arvore_natal", max_iter=5)

print(f"Melhor nota: {resultado['melhor_nota']}/10")
print(f"Ciclos executados: {resultado['ciclos']}")

# Na proxima execucao, o AutoLoop retoma automaticamente
# do checkpoint salvo
```

## Tutorial 5: Validacao de Formatos

```python
from MCR import MCRByteUtils

# Compara dois arquivos de tipos diferentes
with open("audio.wav", "rb") as f:
    audio = f.read(500).hex()  # converte para hex string
with open("imagem.ppm", "rb") as f:
    imagem = f.read(500).hex()

j = MCRByteUtils.jaccard_bytes(audio, imagem)
c = MCRByteUtils.similaridade_cosseno(audio, imagem)
print(f"Jaccard: {j:.4f}")
print(f"Cosseno: {c:.4f}")
if j < 0.1:
    print("Arquivos de tipos diferentes")
else:
    print("Arquivos podem ser do mesmo tipo")
```
