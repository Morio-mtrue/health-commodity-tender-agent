$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$clientFile = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_HOST = '127.0.0.1:11435'
$env:OLLAMA_MODELS = Join-Path $projectRoot '.runtime\ollama-models'
$env:OLLAMA_NUM_PARALLEL = '1'
if (-not (Test-Path -LiteralPath $clientFile)) {
    & '.\.venv\Scripts\python.exe' -m scripts.fetch_ollama_installer
    if ($LASTEXITCODE -ne 0) { throw 'Official installer download failed.' }
    $installerFile = Join-Path $projectRoot '.runtime\OllamaSetup.exe'
    $signature = Get-AuthenticodeSignature -FilePath $installerFile
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(^|, )O=Ollama Inc\.(,|$)') {
        throw 'Ollama installer must have a valid Authenticode signature from Ollama Inc.'
    }
    @{status=[string]$signature.Status;publisher=$signature.SignerCertificate.Subject;certificate=$signature.SignerCertificate.Thumbprint} | ConvertTo-Json | Set-Content -LiteralPath '.runtime\ollama-signature.json'
    $markerDir = Join-Path $env:LOCALAPPDATA 'Ollama'
    New-Item -ItemType Directory -Path $markerDir -Force | Out-Null
    New-Item -ItemType File -Path (Join-Path $markerDir 'upgraded') -Force | Out-Null
    $installer = Start-Process -FilePath $installerFile -ArgumentList '/VERYSILENT /NORESTART /SUPPRESSMSGBOXES' -WindowStyle Hidden -PassThru
    $installDeadline = [DateTime]::UtcNow.AddMinutes(10)
    while (-not $installer.WaitForExit(1000)) {
        if ([DateTime]::UtcNow -gt $installDeadline) { throw 'Ollama installation exceeded ten minutes; inspect the installer process before retrying.' }
    }
    if ($installer.ExitCode -ne 0) { throw "Official Ollama installation failed with exit code $($installer.ExitCode)." }
}
$clientSignature = Get-AuthenticodeSignature -FilePath $clientFile
if ($clientSignature.Status -ne 'Valid' -or $clientSignature.SignerCertificate.Subject -notmatch '(^|, )O=Ollama Inc\.(,|$)') {
    throw 'Installed Ollama executable does not have the expected valid publisher signature.'
}
$ready = $false
try { $runtime = Invoke-RestMethod 'http://127.0.0.1:11435/api/version' -TimeoutSec 2; $ready = [bool]$runtime.version } catch {}
if (-not $ready) {
    Start-Process -FilePath $clientFile -ArgumentList 'serve' -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.runtime\ollama-stdout.log') -RedirectStandardError (Join-Path $projectRoot '.runtime\ollama-stderr.log') | Out-Null
    # First startup may spend over a minute discovering Windows GPU drivers.
    for ($attempt=0; $attempt -lt 180; $attempt++) {
        try { $runtime = Invoke-RestMethod 'http://127.0.0.1:11435/api/version' -TimeoutSec 1; $ready = [bool]$runtime.version } catch {}
        if ($ready) { break }
        Start-Sleep -Seconds 1
    }
}
if (-not $ready) { throw 'Approved Ollama runtime did not become ready on project port 11435.' }
$modelFile = Join-Path $projectRoot 'models\qwen2.5-1.5b-instruct-q4_k_m.gguf'
if (-not (Test-Path -LiteralPath $modelFile)) {
    & '.\.venv\Scripts\python.exe' -m scripts.setup_cpu_model
    if ($LASTEXITCODE -ne 0) { throw 'Pinned model download failed.' }
}
('FROM "' + $modelFile.Replace('\','/') + '"') | Set-Content -LiteralPath '.runtime\Qwen.Modelfile' -Encoding utf8
$tags = Invoke-RestMethod 'http://127.0.0.1:11435/api/tags' -TimeoutSec 5
if (-not ($tags.models | Where-Object name -eq 'tender-qwen:1.5b-q4')) {
    & $clientFile create 'tender-qwen:1.5b-q4' -f '.runtime\Qwen.Modelfile' *> '.runtime\ollama-import.log'
    if ($LASTEXITCODE -ne 0) { throw 'Pinned GGUF import failed.' }
}
@{runtime='ollama';version=$runtime.version;url='http://127.0.0.1:11435';model='tender-qwen:1.5b-q4';cloud_disabled=$true} | ConvertTo-Json | Set-Content -LiteralPath '.runtime\ollama-runtime.json'
Write-Output 'Ollama ready on project port 11435. Model: tender-qwen:1.5b-q4. Cloud features disabled for this process.'
