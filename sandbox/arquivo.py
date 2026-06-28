import json

def criar_arquivo_json():
    """
    Cria um arquivo .mcr_cmd_update.json no sandbox com o conteúdo especificado.
    """
    # Define o conteúdo a ser escrito no arquivo JSON
    conteudo = {
        'cmd': 'edit',
        'args': [
            'E:\\Projeto MCR\\AGENTS.md',
            '102',
            '> Cloud SUPERVISIONA em loop ate MCR acertar. NUNCA assume sem o HUMANO autorizar.'
        ]
    }

    # Nome do arquivo a ser criado
    nome_arquivo = 'sandbox/mcr_cmd_update.json'

    # Escreve o conteúdo no arquivo JSON
    with open(nome_arquivo, 'w', encoding='utf-8') as file:
        json.dump(conteudo, file, ensure_ascii=False, indent=4)

    print(f"Arquivo {nome_arquivo} criado com sucesso.")

# Chama a função para criar o arquivo
criar_arquivo_json()