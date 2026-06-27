# 全链路 Bazel 编译：Rust (Cargo) + Python 资源打包
# 发布包: .\build_release.ps1  或  bazel build //:build_release
param(
    [switch]$Release,
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. "$PSScriptRoot\tools\resolve_python.ps1"

if ($Release) {
    & "$PSScriptRoot\build_release.ps1" -Version $Version
    exit $LASTEXITCODE
}

$py = Resolve-PythonExe
$env:PYO3_PYTHON = $py
Write-Host "PYO3_PYTHON=$py"
Write-Host "[build] Bazel //:build_all (Rust + Python + assets) ..."
bazel build //:build_all
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$bazelPyd = Join-Path $PSScriptRoot "bazel-bin\spectrum-core\_spectrum_core.pyd"
$devPyd = Join-Path $PSScriptRoot "python\spectrum_core\_spectrum_core.pyd"
if (Test-Path $bazelPyd) {
    $devDir = Split-Path $devPyd -Parent
    if (-not (Test-Path $devDir)) {
        New-Item -ItemType Directory -Force -Path $devDir | Out-Null
    }
    Copy-Item $bazelPyd $devPyd -Force
    Write-Host "Synced -> python\spectrum_core\_spectrum_core.pyd"
}

$launcherDir = Join-Path $PSScriptRoot "bazel-bin\launcher"
Write-Host ""
Write-Host "Build complete."
Write-Host "  Bazel targets: //:build_all"
Write-Host "  Rust extension: bazel-bin\spectrum-core\_spectrum_core.pyd"
Write-Host "  Python sources: //python:spectrum_core + //app:app_src"
Write-Host "  Launcher tree:  bazel-bin\launcher\"
Write-Host "  Dev copy:       python\spectrum_core\_spectrum_core.pyd"
Write-Host "  Run (Bazel):    cd bazel-bin\launcher && python main.py"
Write-Host "  Run (dev):      python main.py"
