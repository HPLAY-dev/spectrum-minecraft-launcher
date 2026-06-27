# Build PyO3 extension and copy to python/spectrum_core/
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\spectrum-core"

function Resolve-PythonExe {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $cmd) { throw "python not found" }
    $exe = $cmd.Source
    if ($exe -match "WindowsApps\\python(\.exe)?$") {
        $c = "$env:LOCALAPPDATA\Python\bin\python.exe"
        if (Test-Path $c) { return $c }
        throw "PYO3 needs full Python (not Store stub): $exe"
    }
    return $exe
}

$env:PYO3_PYTHON = (Resolve-PythonExe)
cargo build --release --features python
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$out = Join-Path $PWD "target\release"
$dst = Join-Path $PSScriptRoot "python\spectrum_core\_spectrum_core.pyd"
foreach ($name in @("spectrum_core.dll", "_spectrum_core.dll", "_spectrum_core.pyd")) {
    $src = Join-Path $out $name
    if (Test-Path $src) {
        try {
            $tmp = "$dst.new"
            Copy-Item $src $tmp -Force
            if (Test-Path $dst) { Remove-Item $dst -Force }
            Rename-Item $tmp $dst -Force
        } catch {
            if (Test-Path $dst) {
                Write-Warning "Could not replace locked $dst (stop running launcher and rebuild). Using existing .pyd."
                exit 0
            }
            throw
        }
        Write-Host "Copied to python\spectrum_core\_spectrum_core.pyd"
        exit 0
    }
}
Write-Error "Build output not found in $out"
exit 1
