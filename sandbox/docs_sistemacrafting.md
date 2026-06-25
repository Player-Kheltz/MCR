# SistemaCrafting

# Sistema de Crafting no Projeto MCR (Tibia)

## Introdução

O sistema de crafting é uma feature crucial no projeto MCR, inspirado no famoso jogo Tibia. Este sistema permite aos jogadores criar itens mais valiosos e únicos através da combinação de materiais e ferramentas disponíveis em diversos locais do jogo. Este documento technical descreve o funcionamento interno e as implementações técnicas do sistema.

## Arquitetura e Componentes

O sistema de crafting é composto por vários componentes que trabalham juntos para suportar a criação dos itens:

1. **Materiais**: São os ingredientes básicos necessários para criar itens através do processo de crafting.
2. **Ferramentas**: Algumas receitas de crafting requerem o uso de ferramentas específicas, como fornos ou torno.
3. **Receitas**: Definem quais materiais podem ser combinados e quais itens serão produzidos.
4. **Inventário**: O local onde os jogadores armazenam seus materiais e itens criados.

## Funcionamento

### 1. Seleção de Receita
O jogador acessa o menu de crafting, que exibe todas as receitas disponíveis. Cada receita é listada com sua descrição, os materiais necessários e a ferramenta requerida (se houver).

### 2. Verificação dos Materiais
Antes de iniciar o processo de crafting, o sistema verifica se o jogador possui todos os materiais necessários para a receita selecionada.

### 3. Combinação de Materiais
Os jogadores podem arrastar e soltar materiais no painel de crafting para combinar os itens. O sistema monitora a combinação em tempo real, e se uma receita for atingida, um sinal de sucesso é exibido.

### 4. Produção do Item
Uma vez que todos os materiais necessários forem combinados corretamente, o item será produzido automaticamente e adicionado ao inventário do jogador.

## Implementação Técnica

O sistema foi desenvolvido utilizando uma combinação de tecnologias backend (Node.js, Express) e frontend (React). A integração entre as partes é feita via API RESTful.

### Backend

#### Endpoints
- **GE