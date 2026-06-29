@echo off
title MCR-DevIA — Dashboard de Pensamento em Tempo Real
cd /d "E:\Projeto MCR"
cls
echo ============================================
echo   MCR-DevIA — Dashboard Unificado
echo ============================================
echo.
echo  Iniciando servidor SSE na porta 8765...
echo  Abrindo navegador...
echo.
echo  Para parar: feche esta janela (Ctrl+C)
echo.
REM Inicia o SSE server com kernel
start /B python scripts\mcr_devia\kernel.py --dashboard
timeout /t 3 /nobreak >nul
REM Abre o navegador no dashboard
start http://localhost:8765/thought_dashboard.html
echo  Dashboard aberto no navegador.
echo  http://localhost:8765/thought_dashboard.html
echo.
pause
