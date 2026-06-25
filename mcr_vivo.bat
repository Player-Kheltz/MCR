@echo off
title MCR-DevIA — Batimento Cardiaco + Observatorio
cd /d "E:\Projeto MCR"
cls
echo.
echo ============================================
echo   MCR-DevIA — MODO VIVO
echo   Batimento cardiaco + Observatorio
echo ============================================
echo.
echo  Iniciando batimento cardiaco (a cada 2min)...
echo  O MCR-DevIA vai escanear, aprender e se reparar
echo  sozinho. O observatorio mostra o que esta acontecendo.
echo.
echo  Para parar: feche a janela (Ctrl+C)
echo.
start /B python sandbox\mcr_loop.py
timeout /t 3 /nobreak >nul
python sandbox\mcr_observatory_v2.py
pause
