#!/usr/bin/env pwsh
# ============================================================
# Script de Configuracao do Ollama - MCR Project
# Previne crashes do Bun (OpenCode) causados por
# disputa de recursos entre Ollama, navegadores e editores.
# ============================================================

Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      Configuracao do Ollama - MCR            ║" -ForegroundColor Cyan
Write-Host "║      Previne crash do Bun/OpenCode           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# PASSO 1: Gravar variaveis de ambiente (permanentes)
# ============================================================
Write-Host "[1/3] Gravando variaveis de ambiente..." -ForegroundColor Yellow
setx OLLAMA_MAX_LOADED_MODELS 1 > $null
setx OLLAMA_NUM_PARALLEL 1 > $null
setx OLLAMA_KEEP_ALIVE 5m > $null
Write-Host "       OK!" -ForegroundColor Green

# ============================================================
# PASSO 2: Aplicar no processo atual
# ============================================================
$env:OLLAMA_MAX_LOADED_MODELS = "1"
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_KEEP_ALIVE = "5m"

# ============================================================
# PASSO 3: Reiniciar servico Ollama
# ============================================================
Write-Host "[2/3] Reiniciando servico Ollama..." -ForegroundColor Yellow
$old = Get-Process ollama* -ErrorAction SilentlyContinue
if ($old) {
    Write-Host "       Encerrando processos antigos..."
    $old | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host "       Iniciando Ollama serve..."
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 3

$check = Get-Process ollama -ErrorAction SilentlyContinue
if ($check) {
    Write-Host "       Ollama rodando (PID: $($check.Id))" -ForegroundColor Green
} else {
    Write-Host "       ERRO: Ollama nao iniciou" -ForegroundColor Red
}

# ============================================================
# PASSO 4: Testar
# ============================================================
Write-Host "[3/3] Testando conexao..." -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    $data = $r.Content | ConvertFrom-Json
    $count = $data.models.Count
    Write-Host "       Ollama ONLINE - $count modelos disponiveis" -ForegroundColor Green
} catch {
    Write-Host "       AVISO: Ollama nao respondeu na porta 11434" -ForegroundColor Red
    Write-Host "       Execute 'ollama serve' manualmente"
}

# ============================================================
Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Configuracao concluida!                      ║" -ForegroundColor Cyan
Write-Host "║                                              ║" -ForegroundColor Cyan
Write-Host "║  Agora abra o OpenCode em OUTRO terminal:     ║" -ForegroundColor Cyan
Write-Host "║    opencode -m ollama/hermes3:8b              ║" -ForegroundColor Cyan
Write-Host "║                                              ║" -ForegroundColor Cyan
Write-Host "║  Ou use o atalho:                             ║" -ForegroundColor Cyan
Write-Host "║    .\mcr-dev.bat                              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
