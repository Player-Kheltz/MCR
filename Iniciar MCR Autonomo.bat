@echo off
title MCR Autonomo
cd /d "%~dp0"
echo ===================================================
echo   MCR AUTONOMO
echo   Aprendizado perpetuo em segundo plano.
echo   Zero GPU. Zero LLM. Zero dependencias.
echo ===================================================
echo.
echo  Iniciando... (veja o log em cache\autonomo.log)
echo.
echo  Para parar: feche esta janela ou pressione Ctrl+C
echo.
echo ===================================================

python MCR.py --autonomo

echo.
echo MCR Autonomo encerrado.
pause
