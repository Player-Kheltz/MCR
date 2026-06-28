@echo off
title MCR-DevIA
cd /d "%~dp0..\scripts\mcr_devia"
echo Iniciando MCR-DevIA...
start http://localhost:8765
python MCR_DevIA-Kernel.py --dashboard
pause
