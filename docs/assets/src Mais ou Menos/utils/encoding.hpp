/**
 * Projeto MCR – Utilitários de Codificação
 * Arquivo: src/utils/encoding_utils.hpp
 *
 * Descrição: Fornece funções para detecção e conversão segura entre
 *            UTF‑8 e Latin‑1 (ISO‑8859‑1), respeitando a natureza híbrida
 *            dos ficheiros de dados do Projeto MCR (scripts em Latin‑1,
 *            dados em UTF‑8 ou Latin‑1).
 */

#pragma once

#include <string>
#include <cstdint>

/**
 * @brief Detecta se uma string é UTF‑8 válida.
 *
 * Verifica cada byte da string de acordo com as regras de codificação UTF‑8
 * (RFC 3629). Sequências de 2, 3 e 4 bytes são validadas.
 *
 * @param str A string a ser verificada.
 * @return true se for UTF‑8 válido, false caso contrário.
 */
inline bool isUtf8(const std::string &str) {
    size_t i = 0;
    while (i < str.size()) {
        unsigned char c = str[i];

        if (c <= 0x7F) {
            // ASCII
            ++i;
            continue;
        } else if (c >= 0xC2 && c <= 0xDF) {
            // Sequência de 2 bytes
            if (i + 1 >= str.size()) return false;
            unsigned char c2 = str[i + 1];
            if ((c2 & 0xC0) != 0x80) return false;
            i += 2;
        } else if (c >= 0xE0 && c <= 0xEF) {
            // Sequência de 3 bytes
            if (i + 2 >= str.size()) return false;
            unsigned char c2 = str[i + 1], c3 = str[i + 2];
            if ((c2 & 0xC0) != 0x80 || (c3 & 0xC0) != 0x80) return false;
            i += 3;
        } else if (c >= 0xF0 && c <= 0xF4) {
            // Sequência de 4 bytes
            if (i + 3 >= str.size()) return false;
            unsigned char c2 = str[i + 1], c3 = str[i + 2], c4 = str[i + 3];
            if ((c2 & 0xC0) != 0x80 || (c3 & 0xC0) != 0x80 || (c4 & 0xC0) != 0x80) return false;
            i += 4;
        } else {
            // Byte inválido em qualquer contexto UTF‑8
            return false;
        }
    }
    return true;
}

/**
 * @brief Converte uma string de Latin‑1 (ISO‑8859‑1) para UTF‑8.
 *
 * Caracteres no intervalo 0x00‑0x7F são mantidos como ASCII.
 * Caracteres no intervalo 0x80‑0xFF são expandidos para a sequência
 * UTF‑8 de 2 bytes correspondente.
 *
 * @param latin1 A string em Latin‑1.
 * @return A string convertida para UTF‑8.
 */
inline std::string latin1ToUtf8(const std::string &latin1) {
    std::string utf8;
    utf8.reserve(latin1.size() * 2); // reserva espaço para o pior caso
    for (unsigned char c : latin1) {
        if (c < 0x80) {
            utf8 += c;
        } else {
            utf8 += static_cast<char>(0xC0 | (c >> 6));
            utf8 += static_cast<char>(0x80 | (c & 0x3F));
        }
    }
    return utf8;
}

/**
 * @brief Converte uma string de UTF‑8 para Latin‑1, com preservação de bytes
 *        que já estão em Latin‑1.
 *
 * Estratégia híbrida (tolerante a falhas):
 *   - Caracteres ASCII (< 0x80) são copiados directamente.
 *   - Sequências UTF‑8 válidas de 2 bytes são convertidas para o caractere
 *     Latin‑1 correspondente, se este couber em 1 byte (0x00‑0xFF).
 *   - Qualquer outro byte (incluindo caracteres Latin‑1 puros como 0xF4 = 'ô')
 *     é mantido intacto, pois assumimos que o ficheiro de origem já estava
 *     em Latin‑1.
 *
 * Isto elimina o bug "n?made": o byte 0xF4 deixa de ser substituído por '?'
 * e passa a ser preservado como 'ô'.
 *
 * @param input A string de entrada (pode estar em UTF‑8, Latin‑1, ou misto).
 * @return A string convertida para Latin‑1.
 */
inline std::string toLatin1(const std::string &input) {
    std::string result;
    result.reserve(input.size());

    for (size_t i = 0; i < input.size(); ++i) {
        unsigned char c = input[i];

        if (c <= 0x7F) {
            // ASCII
            result += static_cast<char>(c);
        } else if ((c & 0xE0) == 0xC0 && i + 1 < input.size()) {
            // Possível sequência UTF‑8 de 2 bytes
            unsigned char c2 = input[i + 1];
            if ((c2 & 0xC0) == 0x80) {
                // Segundo byte válido
                uint16_t codepoint = ((c & 0x1F) << 6) | (c2 & 0x3F);
                if (codepoint <= 0xFF) {
                    // O caractere cabe em Latin‑1
                    result += static_cast<char>(codepoint);
                    ++i; // consome o segundo byte
                } else {
                    // Não cabe em Latin‑1 → preserva o byte original
                    result += static_cast<char>(c);
                }
            } else {
                // Não é um seguidor UTF‑8 → preserva o byte original
                result += static_cast<char>(c);
            }
        } else {
            // Não é ASCII nem início de UTF‑8 de 2 bytes.
            // Presume‑se que o byte já pertence a Latin‑1 (ex.: 0xF4 = 'ô').
            // Mantém o byte original – esta é a chave da preservação.
            result += static_cast<char>(c);
        }
    }

    return result;
}