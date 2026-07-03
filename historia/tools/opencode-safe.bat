@echo off
title OpenCode Safe Mode (Ollama desligado)
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║  OpenCode Safe Mode                      ║
echo  ║  Desliga Ollama antes de abrir           ║
echo  ║  Religado automaticamente ao sair        ║
echo  ╚══════════════════════════════════════════╝
echo.

:: 1. Desliga Ollama (libera GPU para Bun)
echo [1/3] Desligando Ollama...
taskkill /f /im ollama.exe >nul 2>&1
taskkill /f /im ollama-app.exe >nul 2>&1
echo       OK

:: 2. Abre OpenCode
echo [2/3] Abrindo OpenCode...
echo.
start /wait "" opencode.exe

:: 3. Religa Ollama
echo.
echo [3/3] Religando Ollama...
start "" "C:\Users\Kheltz\AppData\Local\Programs\Ollama\ollama.exe"
echo       OK
echo.
echo  ✅ Sessao encerrada. Ollama religado.
