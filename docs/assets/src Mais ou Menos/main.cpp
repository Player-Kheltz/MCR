/**
 * Canary - A free and open-source MMORPG server emulator
 * Copyright (©) 2019–present OpenTibiaBR <opentibiabr@outlook.com>
 * Repository: https://github.com/opentibiabr/canary
 * License: https://github.com/opentibiabr/canary/blob/main/LICENSE
 * Contributors: https://github.com/opentibiabr/canary/graphs/contributors
 * Website: https://docs.opentibiabr.com/
 */

#ifdef _WIN32
#include <windows.h>
#endif
#include <clocale>
#include <locale>
#include <iostream>
#include "canary_server.hpp"
#include "lib/di/container.hpp"

int main() {
    // [MCR] 1. Configuração do C-Runtime
    // Permite leitura de acentos (Latin-1) em funções antigas de C (como tolower)
    std::setlocale(LC_CTYPE, ".1252");
    // Força o padrão numérico a ignorar pontos de milhar, protegendo o SQL do MariaDB
    std::setlocale(LC_NUMERIC, "C");

    // [MCR] 2. Configuração do C++ Runtime (Localidade Híbrida)
    // Cria uma base "C" (segura para números) e injeta a classificação de caracteres ".1252"
    try {
        std::locale baseLocale("C");
        std::locale hybridLocale(baseLocale, ".1252", std::locale::ctype);
        std::locale::global(hybridLocale);
    } catch (...) {
        // Fallback de segurança
        std::locale::global(std::locale("C"));
    }

    // [MCR] 3. Sincronização do Console
    // Restaura o console para UTF-8 (65001) pois os arquivos C++ que imprimem os logs estão em UTF-8
    #ifdef _WIN32
        SetConsoleOutputCP(CP_UTF8);
        SetConsoleCP(CP_UTF8);
    #endif

    return inject<CanaryServer>().run();
}