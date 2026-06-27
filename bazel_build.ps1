# Bazel packaging only (Rust via Cargo). Use build.ps1 for the full project build.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "[build] Bazel //:build_all ..."
bazel build //:build_all
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Bazel packaging complete."
Write-Host "For Rust extension, run: .\cargo_build.ps1  or  .\build.ps1"
