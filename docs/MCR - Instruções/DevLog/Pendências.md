# Pendências MCR-DevIA (25/06 03:30)

## ⚠️ PRIORIDADE MÁXIMA PARA AMANHÃ

### 1. Usar ferramentas DELE (NAO write/grep)
Toda tarefa passa por:
  - mcr_devia.py (ensinar, perguntar, status)
  - mcr_scriptbuilder.py (gerar codigo)
  - mcr_ultimate.py (orquestrar)
  - mcr_knowledge.py (aprender dominios)
  Proibido usar write/grep para criar ou modificar scripts.
  Se precisar de algo novo, pedir pra ELE fazer.

### 2. Subir deteccao de 5/12 para 12/12
  - Gerar detectores para cada problema perdido
  - Integrar automaticamente no scan()
  - Validar com novo teste cego

### 3. Implementar aprendizado por observacao
  - Cada acao minha vira licao no KG (via mcr_devia.py ensinar)
  - Nada de aprendizado desperdicado
  - Tudo registrado nas ferramentas dele

## Status atual
- V66, 70 licoes, 17 contextos
- 25 scripts em scripts/mcr_devia/
- Deteccao: 5/12 no teste cego ultra
- 2 detectores auto-gerados integrados ao scan()
- Toque correlacionado funcionando (KG vs deteccao)
- Performance: scan ~13s/12 arquivos
