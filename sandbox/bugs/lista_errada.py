def media(numeros):
    total = 0
    for i in range(len(numeros) + 1):
        total += numeros[i]
    return total / len(numeros)

print(media([10, 20, 30]))
