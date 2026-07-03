import math

class Calculadora:
    def somar(self, a, b):
        return a + b

    def subtrair(self, a, b):
        return a - b

    def multiplicar(self, a, b):
        return a * b

    def dividir(self, a, b):
        try:
            return a / b
        except ZeroDivisionError:
            return "Erro: Divisão por zero não é permitida."

# Exemplo de uso
if __name__ == "__main__":
    calc = Calculadora()
    print("Soma:", calc.somar(10, 5))
    print("Subtração:", calc.subtrair(10, 5))
    print("Multiplicação:", calc.multiplicar(10, 5))
    print("Divisão:", calc.dividir(10, 0))  # Testando divisão por zero