$targetDirs = @(
    "E:\Projeto MCR\Canary\data-canary\monster",
    "E:\Projeto MCR\Canary\data-canary\npc"
)

foreach ($dir in $targetDirs) {
    Get-ChildItem $dir -Filter *.lua -Recurse | ForEach-Object {
        $raw = [System.IO.File]::ReadAllBytes($_.FullName)
        if ($raw.Length -ge 3 -and $raw[0] -eq 0xEF -and $raw[1] -eq 0xBB -and $raw[2] -eq 0xBF) {
            Write-Host "Convertendo (UTF-8 BOM): $($_.Name)"
            $content = Get-Content $_.FullName -Encoding UTF8 -Raw
            [System.IO.File]::WriteAllText($_.FullName, $content, [System.Text.Encoding]::GetEncoding(28591))
        }
        else {
            try {
                $utf8 = [System.Text.Encoding]::UTF8.GetString($raw)
                $back = [System.Text.Encoding]::UTF8.GetBytes($utf8)
                if ([System.Linq.Enumerable]::SequenceEqual($back, [byte[]]$raw)) {
                    Write-Host "Convertendo (UTF-8 sem BOM): $($_.Name)"
                    [System.IO.File]::WriteAllText($_.FullName, $utf8, [System.Text.Encoding]::GetEncoding(28591))
                } else {
                    Write-Host "Mantendo (já é Latin-1): $($_.Name)"
                }
            }
            catch {
                Write-Host "Erro ao processar: $($_.Name)"
            }
        }
    }
}