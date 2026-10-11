$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$modelFile = Join-Path $projectRoot 'models\qwen2.5-1.5b-instruct-q4_k_m.gguf'
$runtimeFile = Join-Path $projectRoot '.runtime\llama\llama-server.exe'
if (-not (Test-Path -LiteralPath $modelFile) -or -not (Test-Path -LiteralPath $runtimeFile)) {
    throw 'Run uv run python -m scripts.setup_cpu_model first, or use an existing Ollama runtime.'
}
Write-Output 'Starting the pinned CPU model on http://127.0.0.1:8081. Press Ctrl+C to stop.'
& $runtimeFile -m $modelFile --host 127.0.0.1 --port 8081 -c 16384 -ngl 0 --parallel 1
