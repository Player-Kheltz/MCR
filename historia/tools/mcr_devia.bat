@echo off
title MCR-DevIA — Assistente Autonomo do Projeto MCR
cd /d "E:\Projeto MCR"
echo.
echo ============================================
echo   MCR-DevIA — Assistente Autonomo
echo ============================================
echo.
echo Comandos:
echo   1 — Gerar NPC
echo   2 — Gerar Monster
echo   3 — Gerar Item
echo   4 — Gerar Quest
echo   5 — Gerar Spell
echo   6 — Gerar Lore
echo   7 — Perguntar (RAG + Knowledge Graph)
echo   8 — Compilar Projeto
echo   9 — Ensinar novo erro
echo   0 — Status do conhecimento
echo.
set /p opt="Escolha: "

if "%opt%"=="1" (
    set /p nome="Nome do NPC: "
    set /p fala="Saudacao: "
    python sandbox\mcr_devia.py gerar npc "%nome%" "%fala%" 101 50
    goto fim
)
if "%opt%"=="6" (
    set /p tipo="Tipo (npc/item/local): "
    set /p nome="Nome: "
    python sandbox\mcr_devia.py lore %tipo% "%nome%"
    goto fim
)
if "%opt%"=="7" (
    set /p pergunta="Pergunta: "
    python sandbox\mcr_devia.py perguntar "%pergunta%"
    goto fim
)
if "%opt%"=="8" (
    set /p proj="Projeto (canary/otclient): "
    python sandbox\mcr_devia.py compilar %proj%
    goto fim
)
if "%opt%"=="9" (
    set /p erro="Erro: "
    set /p causa="Causa: "
    set /p sol="Solucao: "
    python sandbox\mcr_devia.py ensinar "%erro%" "%causa%" "%sol%"
    goto fim
)
if "%opt%"=="0" (
    python sandbox\mcr_devia.py status
    goto fim
)

echo Opcao invalida. Use 1-9 ou 0.
:fim
echo.
pause
