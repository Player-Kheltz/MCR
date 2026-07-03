@echo off
title MCR-DevIA OBSERVATORY — Narrador ao Vivo
cd /d "E:\Projeto MCR"
cls
echo.
echo ============================================
echo   MCR-DevIA OBSERVATORY
echo   Observando e narrando em tempo real
echo ============================================
echo.
echo  O narrador vai mostrar o que o MCR-DevIA
echo  esta pensando, aprendendo e descobrindo.
echo.
echo  Digite perguntas para interagir com ele!
echo.
timeout /t 3 /nobreak >nul
python sandbox\mcr_observatory.py
pause
