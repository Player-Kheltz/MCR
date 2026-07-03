@echo off
title MCR-DevIA
cd /d "E:\Projeto MCR"
set DEVIA=scripts\mcr_devia

if "%1"=="" (
    echo.
    echo ============================================
    echo   MCR-DevIA - Comando Unificado
    echo ============================================
    echo.
    echo   Comandos:
    echo     mcr chat              Terminal interativo
    echo     mcr vivo              Modo autonomo + observatorio
    echo     mcr status            Estado do MCR-DevIA
    echo     mcr lore "[tipo]"     Gera lore
    echo     mcr ensinar [erro] [causa] [sol]  Aprende algo
    echo     mcr scan              Escaneia projeto
    echo     mcr treinar           Campo de treinamento
    echo     mcr compilar [proj]   Compila servidor
    echo     mcr gerar [tipo] [args...]  Gera codigo via scriptbuilder
    echo.
    echo   Exemplos:
    echo     mcr gerar npc Ferreiro "Bem-vindo" 101 50
    echo     mcr lore npc Sabio
    echo     mcr status
    echo.
    goto :fim
)

if "%1"=="chat" python %DEVIA%\mcr_chat.py & goto :fim
if "%1"=="vivo" start mcr_vivo.bat & goto :fim
if "%1"=="dashboard" python %DEVIA%\kernel.py --dashboard & goto :fim
if "%1"=="self-study" python %DEVIA%\kernel.py --self-study & goto :fim
if "%1"=="auto-melhorar" python %DEVIA%\kernel.py --auto-melhorar & goto :fim
if "%1"=="diagnosticar" python %DEVIA%\kernel.py --diagnosticar & goto :fim
if "%1"=="pattern" python %DEVIA%\kernel.py --pattern %2 %3 %4 %5 & goto :fim
if "%1"=="status" python %DEVIA%\mcr_devia.py status & goto :fim
if "%1"=="lore" python %DEVIA%\mcr_devia.py lore %2 %3 & goto :fim
if "%1"=="ensinar" python %DEVIA%\mcr_devia.py ensinar %2 %3 %4 %5 & goto :fim
if "%1"=="scan" python %DEVIA%\mcr_learning_scan.py & goto :fim
if "%1"=="treinar" python %DEVIA%\criar_training.py & goto :fim
if "%1"=="compilar" python %DEVIA%\mcr_autobuild.py %2 & goto :fim
if "%1"=="gerar" python %DEVIA%\mcr_scriptbuilder.py "gerar %2 %3 %4 %5 %6" & goto :fim

echo Comando invalido: %1
echo Use mcr sem parametros para ajuda.

:fim
