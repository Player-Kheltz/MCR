#!/usr/bin/env pwsh
# oc-dev.ps1 — Abre OpenCode com modelo local (Ollama)
# Faz swap temporario de opencode.json, abre, depois restaura.
# Seguro contra Ctrl+C e fechamento abrupto via trap.

$root = "E:\Projeto MCR"
$default = Join-Path $root "opencode.json"
$local = Join-Path $root "opencode.local.json"
$backup = Join-Path $root "opencode.json.bak"
$restored = $false

# Trap para garantir restauracao mesmo com Ctrl+C ou erro
trap {
    if (-not $restored -and (Test-Path $backup)) {
        Copy-Item $backup $default -Force
        Remove-Item $backup -Force
        $restored = $true
    }
    break
}

# Se o arquivo local nao existe, avisa
if (-not (Test-Path $local)) {
    Write-Host "[ERRO] opencode.local.json nao encontrado em $local" -ForegroundColor Red
    exit 1
}

# Faz backup do atual e usa o local
if (Test-Path $default) {
    Copy-Item $default $backup -Force
}
Copy-Item $local $default -Force

try {
    # Abre opencode com a config local
    opencode
} finally {
    # Restaura o arquivo original
    if (-not $restored -and (Test-Path $backup)) {
        Copy-Item $backup $default -Force
        Remove-Item $backup -Force
        $restored = $true
    }
}
