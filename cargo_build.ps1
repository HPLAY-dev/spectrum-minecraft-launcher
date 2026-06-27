# Build PyO3 extension; Bazel 通过 -OutPath 指定产物路径
param(
    [Parameter(Mandatory = $false)]
    [string]$OutPath = "",
    [switch]$DevCopy
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
Set-Location "$RepoRoot\spectrum-core"

if ($OutPath -and -not [System.IO.Path]::IsPathRooted($OutPath)) {
    $OutPath = Join-Path $RepoRoot $OutPath
}
if ($OutPath) {
    $OutPath = [System.IO.Path]::GetFullPath($OutPath)
}

function Resolve-CargoExe {
    if ($env:CARGO -and (Test-Path $env:CARGO)) { return $env:CARGO }
    $cmd = Get-Command cargo -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidates = @(
        "$env:USERPROFILE\.cargo\bin\cargo.exe",
        "$env:LOCALAPPDATA\Programs\Rust stable MSVC\bin\cargo.exe",
        "C:\Program Files\Rust stable MSVC\bin\cargo.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    throw "cargo not found; install Rust or add cargo to PATH"
}

. (Join-Path $PSScriptRoot "tools\resolve_python.ps1")

$env:PYO3_PYTHON = (Resolve-PythonExe)
$cargo = Resolve-CargoExe
$cargoBin = Split-Path $cargo -Parent
$env:PATH = "$cargoBin;$env:PATH"
& $cargo build --release --features python
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$out = Join-Path $PWD "target\release"
$dst = if ($OutPath) { $OutPath } else {
    Join-Path $PSScriptRoot "python\spectrum_core\_spectrum_core.pyd"
}

foreach ($name in @("spectrum_core.dll", "_spectrum_core.dll", "_spectrum_core.pyd")) {
    $src = Join-Path $out $name
    if (-not (Test-Path $src)) { continue }

    $dstDir = Split-Path $dst -Parent
    if ($dstDir -and -not (Test-Path $dstDir)) {
        New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
    }

    try {
        Copy-Item $src $dst -Force
    } catch {
        if ($OutPath) { throw }
        if (Test-Path $dst) {
            Write-Warning "Could not replace locked $dst (stop running launcher and rebuild). Using existing .pyd."
            exit 0
        }
        throw
    }

    Write-Host "Built PyO3 extension -> $dst"

    if ($DevCopy -and $OutPath) {
        $dev = Join-Path $PSScriptRoot "python\spectrum_core\_spectrum_core.pyd"
        if ($dev -ne $OutPath) {
            Copy-Item $dst $dev -Force
            Write-Host "Dev copy -> python\spectrum_core\_spectrum_core.pyd"
        }
    }
    exit 0
}

Write-Error "Build output not found in $out"
exit 1
