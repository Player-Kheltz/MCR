@echo off
title MCR Evolucao Autonoma 24/7
echo ========================================
echo  MCR EVOLUCAO AUTONOMA 24/7
echo  Rodando em loop infinito...
echo  Data: %date% %time%
echo ========================================
echo.
echo  Pressione Ctrl+C para parar
echo.
cd /d "%~dp0"

:loop
echo [%date% %time%] Iniciando ciclo de evolucao...
python evoluir_autonomo.py
echo [%date% %time%] Ciclo concluido. Aguardando 60 segundos...
timeout /t 60 /nobreak >nul
goto loop
