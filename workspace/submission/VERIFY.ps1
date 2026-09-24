[CmdletBinding()]
param(
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = "Stop"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$aiRoot = Join-Path $packageRoot "ai-engine"
$frontendRoot = Join-Path $packageRoot "frontend"

$required = @(
    "README.md",
    "MANIFEST.md",
    "FINAL_REPORT.md",
    "LICENSES.md",
    "ai-engine\requirements.txt",
    "ai-engine\src\visual_event_ai\app.py",
    "ai-engine\tests\test_api.py",
    "frontend\package.json",
    "frontend\src\App.tsx",
    "docs\COMPETITION_MATERIAL_PACK.md",
    "docs\latex\main.tex"
)

$missing = @($required | Where-Object { -not (Test-Path (Join-Path $packageRoot $_)) })
if ($missing.Count -gt 0) {
    throw "Missing required files: $($missing -join ', ')"
}

$forbidden = @(Get-ChildItem -LiteralPath $packageRoot -Recurse -Force -File | Where-Object {
    $_.FullName -match "\\__pycache__\\|\.pyc$|\\node_modules(\\|$)|\\dist(\\|$)|\.pytest_cache(\\|$)|\\runtime(\\|$)|\.db$|\.env$"
})
if ($forbidden.Count -gt 0) {
    throw "Forbidden generated artifacts found: $($forbidden.FullName -join '; ')"
}

$textFiles = @(Get-ChildItem -LiteralPath $packageRoot -Recurse -File | Where-Object { $_.Extension -in @('.md', '.ps1', '.py', '.ts', '.tsx', '.json', '.tex', '.bib', '.toml') -and $_.Name -ne 'VERIFY.ps1' })
$sensitivePatterns = @('C:\Users\', 'C:/Users/', 'BEGIN PRIVATE KEY', 'api_key=', 'api-key=')
$sensitive = @($textFiles | Select-String -Pattern $sensitivePatterns -SimpleMatch -ErrorAction SilentlyContinue)
if ($sensitive.Count -gt 0) {
    throw "Sensitive or personal absolute path literal found."
}

$oldPythonPath = $env:PYTHONPATH
$oldNoBytecode = $env:PYTHONDONTWRITEBYTECODE
$oldPytestAddopts = $env:PYTEST_ADDOPTS
$aiLocationPushed = $false
$pytestTemp = Join-Path $aiRoot ".codex-pytest-temp-verify"
try {
    $env:PYTHONPATH = "src"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    $env:PYTEST_ADDOPTS = "--basetemp=`"$pytestTemp`""
    Push-Location $aiRoot
    $aiLocationPushed = $true
    python -B -m pytest -p no:cacheprovider -q
    if ($LASTEXITCODE -ne 0) { throw "AI tests failed with exit code $LASTEXITCODE" }
    Pop-Location
    $aiLocationPushed = $false
}
finally {
    if ($aiLocationPushed) { Pop-Location }
    if ($null -eq $oldPythonPath) { Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue } else { $env:PYTHONPATH = $oldPythonPath }
    if ($null -eq $oldNoBytecode) { Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue } else { $env:PYTHONDONTWRITEBYTECODE = $oldNoBytecode }
    if ($null -eq $oldPytestAddopts) { Remove-Item Env:PYTEST_ADDOPTS -ErrorAction SilentlyContinue } else { $env:PYTEST_ADDOPTS = $oldPytestAddopts }
    $pytestTempResolved = [IO.Path]::GetFullPath($pytestTemp)
    $aiRootResolved = [IO.Path]::GetFullPath($aiRoot)
    if (([IO.Path]::GetDirectoryName($pytestTempResolved) -ne $aiRootResolved) -or ([IO.Path]::GetFileName($pytestTempResolved) -ne ".codex-pytest-temp-verify")) {
        throw "Refusing pytest temp cleanup outside the AI project root."
    }
    if (Test-Path -LiteralPath $pytestTempResolved) { Remove-Item -LiteralPath $pytestTempResolved -Recurse -Force }
    $runtime = Join-Path $aiRoot "runtime"
    if (Test-Path $runtime) { python -c "import shutil; shutil.rmtree(r'$runtime', ignore_errors=True)" | Out-Null }
}

if (-not $SkipFrontendBuild) {
    if (Test-Path (Join-Path $frontendRoot "node_modules")) {
        Push-Location $frontendRoot
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed with exit code $LASTEXITCODE" }
        Pop-Location
        $dist = Join-Path $frontendRoot "dist"
        if (Test-Path $dist) { Remove-Item -LiteralPath $dist -Recurse -Force }
    }
    else {
        Write-Warning "frontend/node_modules is absent; frontend build was skipped. Run npm install first."
    }
}

Write-Output "VERIFY_OK: required files, contamination scan and AI tests passed."
