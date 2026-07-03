@echo off
title MCR-Dev (OpenClaw + Ollama)
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║    MCR-Dev via OpenClaw + Ollama         ║
echo  ║    (Node.js, sem Bun - sem crash GPU)    ║
echo  ╚══════════════════════════════════════════╝
echo.
npx openclaw --model ollama:qwen2.5-coder:7b
