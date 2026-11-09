param([string]$EngineRoot = '', [int]$Port = 9880)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
if (-not $EngineRoot) { $EngineRoot = $env:GPT_SOVITS_ROOT }
if (-not $EngineRoot -and (Test-Path -LiteralPath "$projectRoot\runtime.local.json")) {
    $EngineRoot = (Get-Content -LiteralPath "$projectRoot\runtime.local.json" -Raw | ConvertFrom-Json).engine_root
}
if (-not $EngineRoot) { $EngineRoot = 'D:\GPT-SoVITS' }
$python = @('.venv312\Scripts\python.exe', '.venv\Scripts\python.exe', 'runtime\python.exe') | ForEach-Object { Join-Path $EngineRoot $_ } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) { throw 'GPT-SoVITS Python runtime was not found. See docs/INSTALL.md.' }
$url = "http://127.0.0.1:$Port"
$ready = $false
try { $ready = (Invoke-WebRequest -Uri "$url/config" -TimeoutSec 2 -UseBasicParsing).StatusCode -eq 200 } catch {}
if (-not $ready) {
    New-Item -ItemType Directory -Path "$projectRoot\logs" -Force | Out-Null
    $arguments = @('-X', 'utf8', '-u', ('"' + "$projectRoot\webui.py" + '"'), '--engine-root', ('"' + $EngineRoot + '"'), '--port', $Port)
    Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput "$projectRoot\logs\web.log" -RedirectStandardError "$projectRoot\logs\web-error.log"
    for ($attempt=0; $attempt -lt 45; $attempt++) {
        Start-Sleep -Seconds 1
        try { $ready = (Invoke-WebRequest -Uri "$url/config" -TimeoutSec 2 -UseBasicParsing).StatusCode -eq 200 } catch {}
        if ($ready) { break }
    }
}
if (-not $ready) { throw "Web page did not start. See $projectRoot\logs\web-error.log" }
Start-Process $url
