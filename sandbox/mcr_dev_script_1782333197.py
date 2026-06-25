[find_example] Tipo: python_script | Projeto: Fibonacci Calculator
[find_example] Encontrados 1 exemplo
=== EXEMPLO: scripts\fibonacci.py (score:3) ===
#!/usr/bin/env python3
"""
fibonacci.py â€” Script para calcular a sequência de Fibonacci.

Uso:
    python "scripts/fibonacci.py" 10
"""
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib_sequence = [0, 1]
    for i in range(2, n):
        next_value = fib_sequence[-1] + fib_sequence[-2]
        fib_sequence.append(next_value)

    return fib_sequence

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Uso: python fibonacci.py <numero>")
        sys.exit(1)

    n = int(sys.argv[1])
    result = fibonacci(n)
    print(f"A sequência de Fibonacci para {n} é: {result}")