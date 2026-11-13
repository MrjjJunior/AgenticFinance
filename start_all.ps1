# start_all.ps1 - one-command launcher for the demo.
#
#   1. Policy Co-Signer service  (independent limits)  -> http://localhost:8001
#   2. Agent backend (FastAPI)                          -> http://localhost:8000
#   3. Opens the frontend console in your browser.
#
# ASCII-only output (no emoji) so it works on any Windows console.
#
# Stop everything afterwards:
#   Get-Content .run_pids.txt | ForEach-Object { Stop-Process -Id $_ -Force }

$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot
$venvPython = Join-Path $repo "procurement_agent\venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: venv python not found at $venvPython"
    Write-Host "Create it first:  cd procurement_agent; python -m venv venv; .\venv\Scripts\pip install -r requirements.txt"
    exit 1
}

# --------------------------------------------------------------- stop previous run
# Frees the demo's own ports (8000/8001/18099) from any previous run of
# this script or of a stale manual uvicorn. These ports belong to THIS demo.
$pidFile = Join-Path $repo ".run_pids.txt"
if (Test-Path $pidFile) {
    foreach ($oldPid in Get-Content $pidFile) {
        $proc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $oldPid -Force
            Write-Host "Stopped previous run (PID $oldPid)"
        }
    }
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}
foreach ($port in 8000, 8001, 18099) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        $ownerPid = $listener[0].OwningProcess
        $proc = Get-Process -Id $ownerPid -ErrorAction SilentlyContinue
        if ($proc -and $proc.ProcessName -match "python") {
            Stop-Process -Id $ownerPid -Force
            Write-Host "Freed port $port (stopped stale python PID $ownerPid)"
            Start-Sleep -Milliseconds 500
        } else {
            Write-Host "WARNING: port $port is held by a non-python process (PID $ownerPid) - not touching it."
        }
    }
}

# --------------------------------------------------------------- optional LLM stub
# If .env points GROQ_BASE_URL at a local OpenAI-compatible stub, start it.
$envFile = Join-Path $repo "procurement_agent\.env"
if (Test-Path $envFile) {
    $stubLine = (Get-Content $envFile | Where-Object { $_ -match "^GROQ_BASE_URL=http://(localhost|127\.0\.0\.1):\d+" } | Select-Object -First 1)
    if ($stubLine) {
        if ($stubLine -match ":(\d+)") { $stubPort = [int]$Matches[1] } else { $stubPort = 18099 }
        $listener = Get-NetTCPConnection -LocalPort $stubPort -State Listen -ErrorAction SilentlyContinue
        if (-not $listener) {
            $stubOut = Join-Path $repo "llm_stub.out.log"
            $stubErr = Join-Path $repo "llm_stub.err.log"
            Remove-Item $stubOut, $stubErr -ErrorAction SilentlyContinue
            $stubProc = Start-Process -FilePath $venvPython `
                -ArgumentList @("llm_stub.py","--port","$stubPort") `
                -WorkingDirectory (Join-Path $repo "procurement_agent") `
                -WindowStyle Hidden -PassThru `
                -RedirectStandardOutput $stubOut -RedirectStandardError $stubErr
            Write-Host "Started OpenAI-compatible LLM stub (PID $($stubProc.Id), port $stubPort)"
            $script:stubPid = $stubProc.Id
        } else {
            Write-Host "LLM stub already running on port $stubPort"
        }
    }
}

function Start-ServiceProc([string]$name, [string[]]$uvicornArgs, [string]$workdir, [int]$port) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        Write-Host "WARNING: port $port is already in use (PID $($listener[0].OwningProcess)) - $name NOT started."
        return $null
    }
    $out = Join-Path $repo "$($name).out.log"
    $err = Join-Path $repo "$($name).err.log"
    Remove-Item $out, $err -ErrorAction SilentlyContinue
    $proc = Start-Process -FilePath $venvPython -ArgumentList $uvicornArgs `
        -WorkingDirectory $workdir -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    Write-Host "Started $name (PID $($proc.Id), port $port, log $err)"
    return $proc
}

# --------------------------------------------------------------- 1. cosigner (8001)
$cosignerProc = Start-ServiceProc -name "cosigner_8001" `
    -uvicornArgs @("-m","uvicorn","cosigner_service.main:create_app","--factory","--port","8001") `
    -workdir $repo -port 8001

# --------------------------------------------------------------- 2. backend (8000)
$backendProc = Start-ServiceProc -name "backend_8000" `
    -uvicornArgs @("-m","uvicorn","app.main:app","--port","8000") `
    -workdir (Join-Path $repo "procurement_agent") -port 8000

# --------------------------------------------------------------- health checks
function Wait-Healthy([string]$url, [string]$name, [int]$attempts = 30) {
    for ($i = 0; $i -lt $attempts; $i++) {
        $resp = curl.exe -s --noproxy "*" --max-time 2 $url 2>$null
        if ($LASTEXITCODE -eq 0 -and $resp -match '"ok"') { Write-Host "  $name is up ($url)"; return $true }
        Start-Sleep -Milliseconds 700
    }
    Write-Host "  WARNING: $name did not answer at $url - check the .err.log"
    return $false
}

Write-Host ""
Write-Host "Waiting for services..."
if ($cosignerProc) { Wait-Healthy "http://localhost:8001/health" "Policy Co-Signer" | Out-Null }
if ($backendProc)  { Wait-Healthy "http://localhost:8000/api/v1/health" "Agent backend" | Out-Null }

# --------------------------------------------------------------- record pids + open UI
$pids = @()
if ($cosignerProc) { $pids += $cosignerProc.Id }
if ($backendProc)  { $pids += $backendProc.Id }
if ($script:stubPid) { $pids += $script:stubPid }
Set-Content -Path $pidFile -Value $pids

Write-Host ""
Write-Host "============================================================"
Write-Host "  Stokvel Procurement Agent demo is running"
Write-Host "============================================================"
Write-Host "  Frontend        : frontend/index.html (opening now)"
Write-Host "  Agent backend   : http://localhost:8000/docs"
Write-Host "  Cosigner service: http://localhost:8001/docs"
Write-Host ""
Write-Host "  Demo flow:"
Write-Host "   1. Load demo data -> Process invoice   -> APPROVED (autonomous tx on Testnet)"
Write-Host "   2. Tick 'Simulate a different invoice', set total over the cap -> ESCALATED (blocked)"
Write-Host "   3. Owner console: set cap to 100, Save -> next invoice is blocked by YOUR limit"
Write-Host ""
Write-Host "  Stop everything:"
Write-Host "    Get-Content .run_pids.txt | ForEach-Object { Stop-Process -Id `$_ -Force }"
Write-Host "============================================================"

Start-Process (Join-Path $repo "frontend\index.html")
