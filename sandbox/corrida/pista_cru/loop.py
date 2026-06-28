# PISTA CRIADA POR: CRU (raw qwen2.5-coder:1.5b)
# Tema: Loop e controle de fluxo
# Problemas: 1 logico + 1 loop infinito + 1 falsa pista

def encontrar_par(lista_num):
    """Encontra o primeiro numero par na lista."""
    # ERRO 1: Se lista_num for None, causa crash
    for num in lista_num:
        if num % 2 == 0:
            return num
    return None

def processar_lista(dados):
    """Processa cada elemento da lista."""
    resultado = []
    i = 0
    # ERRO 2: Loop infinito quando encontra valor negativo
    # Nao incrementa 'i' quando dados[i] < 0
    while i < len(dados):
        if dados[i] < 0:
            continue  # BUG: nao incrementa i, loop infinito!
        if dados[i] > 0:
            resultado.append(dados[i] * 2)
        i += 1
    return resultado

def validar_entrada(valor):
    """Valida se entrada e valida."""
    # FALSA PISTA: A funcao diz que valida, mas so retorna True sempre
    # O comentario sugere que faz validacao complexa
    return True  # TODO: implementar validacao real

def main():
    dados = [5, -3, 10, 0, -1, 8]
    par = encontrar_par(dados)
    print(f"Primeiro par: {par}")
    
    processados = processar_lista(dados)
    print(f"Processados: {processados}")
    
    if validar_entrada(-999):
        print("Entrada valida!")

if __name__ == "__main__":
    main()
