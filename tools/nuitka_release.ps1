# 复制 Nuitka 产物到 builds/nuitka-VERSION/（build_release.ps1 调用）
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDist,
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [string]$Version = "1.0.0"
)

if ($env:LAUNCHER_VERSION) { $Version = $env:LAUNCHER_VERSION }

$ErrorActionPreference = "Stop"
if (-not (Test-Path $SourceDist)) {
    throw "Nuitka dist not found: $SourceDist"
}

$releaseRoot = Join-Path $RepoRoot ("builds\nuitka-" + $Version)
if (Test-Path $releaseRoot) { Remove-Item $releaseRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $releaseRoot | Out-Null
Copy-Item $SourceDist (Join-Path $releaseRoot "main.dist") -Recurse -Force
Write-Host "Release bundle -> $releaseRoot"
