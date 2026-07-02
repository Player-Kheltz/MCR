# MCR Evolucao Autonoma 24/7 - PowerShell Script
# Roda em loop infinito, com log e salvamento automatico
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$logFile = Join-Path $scriptPath "evolucao_log.txt"
$cacheFile = Join-Path $scriptPath "cache\evolucao.json"

Write-Host "========================================"
Write-Host " MCR EVOLUCAO AUTONOMA 24/7"
Write-Host " Log: $logFile"
Write-Host " Cache: $cacheFile"
Write-Host "========================================"
Write-Host ""
Write-Host " Pressione Ctrl+C para parar"
Write-Host ""

$ciclo = 0

while ($true) {
    $ciclo++
    $data = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "[$data] Ciclo $ciclo - Iniciando evolucao..."
    "$data - Ciclo $ciclo - Iniciando" | Out-File -FilePath $logFile -Append -Encoding utf8
    
    # Executa a evolucao
    $output = & python "$scriptPath\evoluir_autonomo.py" 2>&1
    $exitCode = $LASTEXITCODE
    
    $data = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # Salva resultado no log
    "$data - Ciclo $ciclo - Exit: $exitCode" | Out-File -FilePath $logFile -Append -Encoding utf8
    
    # Mostra na tela
    Write-Host "[$data] Ciclo $ciclo concluido (exit=$exitCode)"
    Write-Host "Aguardando 30 segundos..."
    
    Start-Sleep -Seconds 30
}
