// calcular_dano — Implementacao completa
// Gerado pelo Cloud

#include <cmath>
#include <random>
#include <algorithm>

/**
 * calcular dano critico baseado em nivel, forca e sorte
 * @param nivel Nivel do jogador (1-1000)
 * @param forca Atributo de forca do jogador (1-200)
 * @param sorte Atributo de sorte (0.0 - 1.0)
 * @return Dano critico calculado
 */
int calcularDanoCritico(int nivel, int forca, double sorte) {
    // Dano base
    double danoBase = nivel * 2.5 + forca * 1.2;
    
    // Chance de critico baseada na sorte
    double chanceCritico = 0.05 + (sorte * 0.25);
    if (chanceCritico > 0.5) chanceCritico = 0.5;
    
    // Multiplicador de critico
    double multCritico = 1.0;
    if ((double)rand() / RAND_MAX < chanceCritico) {
        multCritico = 1.5 + (sorte * 1.5);
        if (multCritico > 3.0) multCritico = 3.0;
    }
    
    // Dano final
    int danoFinal = static_cast<int>(danoBase * multCritico);
    return std::max(1, danoFinal);
}