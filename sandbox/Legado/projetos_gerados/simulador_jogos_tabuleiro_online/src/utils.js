// utils.js
/**
 * Função para gerar um ID único.
 * @returns {string} - Um ID único.
 */
export function generateUniqueId() {
    return 'id_' + Math.random().toString(36).substr(2, 9);
}
/**
 * Função para verificar se duas posições são iguais.
 * @param {object} pos1 - Primeira posição com propriedades x e y.
 * @param {object} pos2 - Segunda posição com propriedades x e y.
 * @returns {boolean} - Verdadeiro se as posições forem iguais, falso caso contrário.
 */
export function arePositionsEqual(pos1, pos2) {
    return pos1.x === pos2.x && pos1.y === pos2.y;
}
/**
 * Função para verificar se uma posição está dentro dos limites do tabuleiro.
 * @param {object} position - Posição com propriedades x e y.
 * @param {number} boardSize - Tamanho do tabuleiro (assume que o tabuleiro é quadrado).
 * @returns {boolean} - Verdadeiro se a posição estiver dentro dos limites, falso caso contrário.
 */
export function isPositionWithinBounds(position, boardSize) {
    return (
        position.x >= 0 && position.x < boardSize &&
        position.y >= 0 && position.y < boardSize
    );
}
/**
 * Função para calcular a distância entre duas posições.
 * @param {object} pos1 - Primeira posição com propriedades x e y.
 * @param {object} pos2 - Segunda posição com propriedades x e y.
 * @returns {number} - Distância euclidiana entre as duas posições.
 */
export function calculateDistance(pos1, pos2) {
    const dx = pos1.x - pos2.x;
    const dy = pos1.y - pos2.y;
    return Math.sqrt(dx * dx + dy * dy);
}
/**
 * Função para clonar um objeto.
 * @param {object} obj - O objeto a ser clonado.
 * @returns {object} - Um clone do objeto original.
 */
export function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }
    if (Array.isArray(obj)) {
        const copy = [];
        for (let i = 0, len = obj.length; i < len; i++) {
            copy[i] = deepClone(obj[i]);
        }
        return copy;
    }
    const copy = {};
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            copy[key] = deepClone(obj[key]);
        }
    }
    return copy;
}
/**
 * Função para gerar um número aleatório dentro de um intervalo.
 * @param {number} min - O valor mínimo do intervalo.
 * @param {number} max - O valor máximo do intervalo.
 * @returns {number} - Um número aleatório entre min e max (inclusive).
 */
export function getRandomNumber(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}
/**
 * Função para verificar se um objeto está vazio.
 * @param {object} obj - O objeto a ser verificado.
 * @returns {boolean} - Verdadeiro se o objeto estiver vazio, falso caso contrário.
 */
export function isEmptyObject(obj) {
    return Object.keys(obj).length === 0;
}
Este módulo `utils.js` fornece várias funções utilitárias que podem ser úteis em um simulador de jogos de tabuleiro online, incluindo geração de IDs únicos, comparação de posições, verificação de limites do tabuleiro, cálculo de distância entre posições, clonagem profunda de objetos, geração de números aleatórios e verificação se um objeto está vazio. Você pode importar essas funções em seus componentes React ou arquivos JavaScript para usar em seu projeto.