param(
    [string]$BuildType = "Release"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

& (Join-Path $Root "scripts\gen_version.ps1") -BuildId $env:SERENA_BUILD_ID

Write-Host "==> Building C++ core"
cmake -S $Root -B (Join-Path $Root "build") -DCMAKE_BUILD_TYPE=$BuildType
cmake --build (Join-Path $Root "build") --config $BuildType

Write-Host "==> Building Rust core"
& (Join-Path $Root "scripts\cargo_build.ps1")

Write-Host "Done."
