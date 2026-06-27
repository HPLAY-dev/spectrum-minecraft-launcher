# Assemble launcher tree into bazel-bin/launcher
param(
    [Parameter(Mandatory = $true)][string]$OutDir,
    [Parameter(Mandatory = $true)][string]$StampFile,
    [Parameter(Mandatory = $true)][string]$PydPath
)

$ErrorActionPreference = "Stop"
$Root = Get-Location

function Copy-Tree($RelativePath) {
    $src = Join-Path $Root $RelativePath
    if (-not (Test-Path $src)) { return }
    $dst = Join-Path $OutDir $RelativePath
    $parent = Split-Path $dst -Parent
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
    Copy-Item $src $dst -Recurse -Force
}

if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Copy-Tree "python"
Copy-Tree "app"
foreach ($dir in @("assets", "languages", "themes", "qml", "web", "fonts")) {
    Copy-Tree $dir
}

Get-ChildItem $Root -Filter "*.py" -File | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $OutDir $_.Name) -Force
}

$pyCoreDir = Join-Path $OutDir "python\spectrum_core"
if (-not (Test-Path $pyCoreDir)) {
    New-Item -ItemType Directory -Force -Path $pyCoreDir | Out-Null
}

foreach ($junk in @("_spectrum_core_test.pyd", "__pycache__")) {
    Get-ChildItem $pyCoreDir -Recurse -Filter $junk -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Copy-Item $PydPath (Join-Path $pyCoreDir "_spectrum_core.pyd") -Force

$stampDir = Split-Path $StampFile -Parent
if ($stampDir -and -not (Test-Path $stampDir)) {
    New-Item -ItemType Directory -Force -Path $stampDir | Out-Null
}
Set-Content -Path $StampFile -Value (Get-Date -Format o) -Encoding utf8
Write-Host "Assembled launcher -> $OutDir"
