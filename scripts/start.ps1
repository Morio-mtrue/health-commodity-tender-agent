param([switch]$CheckOnly, [switch]$WithModel)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'Install uv from https://docs.astral.sh/uv/getting-started/installation/ and rerun this command.' }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Install Node.js LTS from https://nodejs.org/ and rerun this command.' }
uv sync --frozen
if ($LASTEXITCODE -ne 0) { throw 'Python dependency setup failed.' }
if (-not (Test-Path -LiteralPath 'node_modules\@modelcontextprotocol\server-filesystem\dist\index.js')) {
    npm ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Borrowed Filesystem MCP setup failed.' }
}
if ($CheckOnly) {
    & '.\.venv\Scripts\python.exe' -m pytest -q
    exit $LASTEXITCODE
}
Write-Output 'Open http://127.0.0.1:8000 in your browser. Press Ctrl+C to stop.'
if ($WithModel) {
    & '.\.venv\Scripts\python.exe' -m scripts.setup_cpu_model
    if ($LASTEXITCODE -ne 0) { throw 'Local model setup failed.' }
    $modelFile = Join-Path $projectRoot 'models\qwen2.5-1.5b-instruct-q4_k_m.gguf'
    $modelExe = Join-Path $projectRoot '.runtime\llama\llama-server.exe'
    $modelProcess = Start-Process -FilePath $modelExe -ArgumentList @('-m', ('"' + $modelFile + '"'), '--host', '127.0.0.1', '--port', '8081', '-c', '16384', '-ngl', '0', '--parallel', '1') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot '.runtime\model-stdout.log') -RedirectStandardError (Join-Path $projectRoot '.runtime\model-stderr.log')
    $modelReady = $false
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        if ($modelProcess.HasExited) { throw "CPU runtime exited with code $($modelProcess.ExitCode). Check Windows Application Control and .runtime/model-stderr.log. Run without -WithModel to review the synthetic case." }
        try { $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8081/health' -TimeoutSec 1; $modelReady = $health.status -eq 'ok' } catch {}
        if ($modelReady) { break }
        Start-Sleep -Seconds 1
    }
    if (-not $modelReady) { Stop-Process -Id $modelProcess.Id; throw 'Local CPU model did not become ready within 30 seconds.' }
    Write-Output 'Local CPU model started on port 8081. Select qwen2.5-1.5b-instruct-q4_k_m.gguf in the workbench.'
}
try {
    & '.\.venv\Scripts\python.exe' -m uvicorn app.server:app --host 127.0.0.1 --port 8000
} finally {
    if ($modelProcess -and -not $modelProcess.HasExited) { Stop-Process -Id $modelProcess.Id }
}
