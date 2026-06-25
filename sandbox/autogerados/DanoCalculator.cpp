// uma funcao que calcula dano baseado em nivel e forca
// Gerado pelo MCR-DevIA
#include "DanoCalculator.hpp"

```cpp
#include <iostream>

class DanoCalculator {
public:
    static int calcularDano(int nivel, int forca) {
        // Fórmula simples para calcular dano: (Nível * Força) / 10
        return (nivel * forca) / 10;
    }
};

int main() {
    int nivel = 5; // Exemplo de nível do personagem
    int forca = 8; // Exemplo de força do personagem

    int dano = DanoCalculator::calcularDano(nivel, forca);
    std::cout << "O dano calculado é: " << dano << std::endl;

    return 0;
}
```
