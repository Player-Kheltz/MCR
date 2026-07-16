# Script para alternar o modelo no .opencode.json
param(
    [Parameter(Mandatory)]
    [string]$Modelo
)

$configPath = "E:\MCR\.opencode.json"
$config = Get-Content -Path $configPath -Raw | ConvertFrom-Json
$config.model = "ollama/$Modelo"
$config | ConvertTo-Json -Depth 10 | Set-Content -Path $configPath
Write-Host "Modelo alterado para: ollama/$Modelo"
Write-Host "Reinicie o OpenCode para aplicar."
