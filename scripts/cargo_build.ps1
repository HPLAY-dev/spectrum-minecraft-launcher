param(
    [switch]$DevCopy
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$CoreDir = Join-Path $Root "src\core\rs\mc-core"
$OutDir = Join-Path $Root "src\core\GUI\py\mc_core"

& (Join-Path $Root "scripts\gen_version.ps1") -BuildId $env:SERENA_BUILD_ID

Push-Location $CoreDir
try {
    $env:PYO3_PYTHON = "python"
    $env:PYO3_USE_ABI3_FORWARD_COMPATIBILITY = "1"
    cargo build --release --features python
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $LibName = if ($IsWindows -or $env:OS -match "Windows") {
        "_mc_core.dll"
    } else {
        "_mc_core.so"
    }

    $Built = Join-Path $CoreDir "target\release\$LibName"
    if (-not (Test-Path $Built)) {
        $Built = Get-ChildItem -Path (Join-Path $CoreDir "target\release") -Filter "_mc_core.*" |
            Where-Object { $_.Extension -in ".dll", ".so", ".pyd" } |
            Select-Object -First 1 -ExpandProperty FullName
    }

    if (-not $Built -or -not (Test-Path $Built)) {
        Write-Error "Rust extension not found after build"
    }

    $DestName = if ($IsWindows -or $env:OS -match "Windows") { "_mc_core.pyd" } else { "_mc_core.so" }
    Copy-Item $Built (Join-Path $OutDir $DestName) -Force
    Write-Host "Copied $Built -> $OutDir\$DestName"
}
finally {
    Pop-Location
}
