# Build entire Spectrum Launcher project (Windows-friendly)
# 1. Rust PyO3 extension via Cargo
# 2. Bazel filegroups for Python sources and assets

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Resolve-PythonExe {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $cmd) { throw "python not found; install Python 3.12+" }
    $exe = $cmd.Source
    if ($exe -match "WindowsApps\\python(\.exe)?$") {
        $candidates = @(
            "$env:LOCALAPPDATA\Python\bin\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
            "C:\Python314\python.exe",
            "C:\Python312\python.exe"
        )
        foreach ($c in $candidates) {
            if (Test-Path $c) { return $c }
        }
        throw "PYO3 needs a full Python install (not Windows Store stub): $exe"
    }
    return $exe
}

$py = Resolve-PythonExe
$env:PYO3_PYTHON = $py
Write-Host "PYO3_PYTHON=$py"

Write-Host "[1/2] Cargo: spectrum-core (PyO3) ..."
& "$PSScriptRoot\cargo_build.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/2] Bazel: //:build_all ..."
bazel build //:build_all
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Build complete."
Write-Host "  Rust extension: python\spectrum_core\_spectrum_core.pyd"
Write-Host "  Run: python main.py"
