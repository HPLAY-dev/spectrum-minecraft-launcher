# 全链路 Bazel 发布：Rust + Python + Nuitka standalone
param(
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. "$PSScriptRoot\tools\resolve_python.ps1"

$py = Resolve-PythonExe
$env:PYO3_PYTHON = $py
$env:LAUNCHER_VERSION = $Version

Write-Host "PYO3_PYTHON=$py"
Write-Host "LAUNCHER_VERSION=$Version"
Write-Host "[release] Bazel //:build_release (Rust + Python + Nuitka) ..."
Write-Host "Requires: pip install nuitka PySide6 modrinth_api_wrapper requests"
Write-Host "Toolchain: Python <3.13 -> MinGW64 | 3.13+ -> MSVC or Zig (auto)"
Write-Host "Optional: `$env:NUITKA_TOOLCHAIN = 'msvc' | 'zig'"
bazel build //:build_release
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$nuitkaDist = Join-Path $PSScriptRoot "bazel-bin\nuitka\main.dist"
& "$PSScriptRoot\tools\nuitka_release.ps1" -SourceDist $nuitkaDist -RepoRoot $PSScriptRoot -Version $Version

$bazelPyd = Join-Path $PSScriptRoot "bazel-bin\spectrum-core\_spectrum_core.pyd"
$devPyd = Join-Path $PSScriptRoot "python\spectrum_core\_spectrum_core.pyd"
if (Test-Path $bazelPyd) {
    Copy-Item $bazelPyd $devPyd -Force
}

Write-Host ""
Write-Host "Release build complete."
Write-Host "  Nuitka dist:  bazel-bin\nuitka\main.dist\"
Write-Host "  Release copy: builds\nuitka-$Version\main.dist\"
Write-Host "  Archive:      7z a builds\nuitka-$Version-windows.7z builds\nuitka-$Version"
