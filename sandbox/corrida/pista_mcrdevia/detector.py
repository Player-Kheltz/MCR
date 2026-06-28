# PISTA CRIADA POR: MCR-DevIA ATUAL
# Tema: Deteccao e correcao de erros em script Python
# Problemas: 2 logicos + 1 falsa pista

import json

# ============================================================
# SISTEMA DE DETECCAO DE ERROS EM CONFIG
# ============================================================

def carregar_config(caminho):
    """Carrega config de um arquivo JSON."""
    with open(caminho, 'r') as f:
        return json.load(f)

def validar_config(config):
    """Valida se config tem todos os campos obrigatorios."""
    obrigatorios = ['nome', 'versao', 'limite']
    for campo in obrigatorios:
        if campo not in config:
            return False, f"Campo {campo} faltando"
    
    # ERRO 1: Nao valida tipo dos campos
    # 'limite' deveria ser int, mas aceita qualquer tipo
    # FALSA PISTA: comentario abaixo diz que valida, mas nao valida
    
    return True, "Config valida"

def processar_itens(itens, limite):
    """Processa lista de itens ate o limite."""
    # ERRO 2: 'itens' pode ser None e causa crash
    # A funcao assume que itens sempre e uma lista
    
    resultado = []
    for i in range(min(limite, len(itens))):
        item = itens[i]
        if item.get('ativo', True):
            resultado.append(item['nome'])
    return resultado

def salvar_resultado(resultado, caminho):
    """Salva resultado em arquivo."""
    # FALSA PISTA: A funcao parece salvar mas nao tem permissao de escrita
    # O comentario diz que sim, mas o codigo so abre pra leitura
    with open(caminho, 'r') as f:  # 'r' em vez de 'w'
        json.dump(resultado, f)

def main():
    config = carregar_config('config.json')
    valido, msg = validar_config(config)
    if not valido:
        print(f"Erro: {msg}")
        return
    
    itens = config.get('itens')
    limite = config['limite']
    resultado = processar_itens(itens, limite)
    print(f"Processados {len(resultado)} itens")
    
    salvar_resultado(resultado, 'resultado.json')

if __name__ == '__main__':
    main()
