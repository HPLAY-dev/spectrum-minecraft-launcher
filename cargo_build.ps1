# Build PyO3 extension and copy to python/spectrum_core/
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\spectrum-core"
$env:PYO3_PYTHON = "python"
cargo build --release --features python
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$out = Join-Path $PWD "target\release"
$dst = Join-Path $PSScriptRoot "python\spectrum_core\_spectrum_core.pyd"
foreach ($name in @("spectrum_core.dll", "_spectrum_core.dll", "_spectrum_core.pyd")) {
    $src = Join-Path $out $name
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "Copied to python\spectrum_core\_spectrum_core.pyd"
        exit 0
    }
}
Write-Error "Build output not found in $out"
exit 1
