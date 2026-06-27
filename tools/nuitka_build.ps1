# Bazel genrule: Nuitka standalone 发布包 -> bazel-bin/nuitka/main.dist/
param(
    [Parameter(Mandatory = $true)]
    [string]$OutDir,
    [Parameter(Mandatory = $true)]
    [string]$StampFile,
    [Parameter(Mandatory = $true)]
    [string]$PydPath,
    [string]$Version = "1.0.0",
    [string]$Entry = "main.py"
)

if ($env:LAUNCHER_VERSION) { $Version = $env:LAUNCHER_VERSION }

$ErrorActionPreference = "Stop"
$Root = Get-Location
. (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "resolve_python.ps1")
. (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "ensure_build_env.ps1")
Ensure-WindowsBuildEnv

if (-not [System.IO.Path]::IsPathRooted($PydPath)) {
    $PydPath = Join-Path $Root $PydPath
}
$PydPath = [System.IO.Path]::GetFullPath($PydPath)

$pydTarget = Join-Path $Root "python\spectrum_core\_spectrum_core.pyd"
$pydDir = Split-Path $pydTarget -Parent
if (-not (Test-Path $pydDir)) {
    New-Item -ItemType Directory -Force -Path $pydDir | Out-Null
}
Copy-Item $PydPath $pydTarget -Force
Remove-SpectrumCoreBuildJunk -PyCoreDir $pydDir

$python = Resolve-PythonExe
$env:PYTHONPATH = Join-Path $Root "python"
$scratch = Join-Path $env:TEMP ("spectrum_nuitka_" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $scratch | Out-Null

try {
    $pydRel = "python/spectrum_core/_spectrum_core.pyd"
    $pyVer = & $python -c "import sys; print(sys.version_info[:2])" 2>$null
    $pyMajor, $pyMinor = 3, 12
    if ($pyVer -match '\((\d+),\s*(\d+)\)') {
        $pyMajor = [int]$Matches[1]
        $pyMinor = [int]$Matches[2]
    }

    $toolchain = Get-NuitkaToolchainArgs -PyMajor $pyMajor -PyMinor $pyMinor
    $toolchainArgs = $toolchain.Args
    $toolchainName = $toolchain.Name
    Write-Host "[nuitka] Python $pyMajor.$pyMinor -> $toolchainName"

    $nuitkaArgs = $toolchainArgs + @(
        "--standalone",
        "--jobs=16",
        "--enable-plugin=pyside6",
        "--include-package=spectrum_core",
        "--include-package=modrinth_api_wrapper",
        "--include-package=app",
        "--include-data-dir=./assets=assets",
        "--include-data-dir=./languages=languages",
        "--include-data-dir=./qml=qml",
        "--include-data-dir=./themes=themes",
        "--include-data-dir=./web=web",
        "--include-data-files=${pydRel}=${pydRel}",
        "--assume-yes-for-downloads",
        "--output-dir=$scratch",
        "--show-progress",
        "--windows-console-mode=disable",
        "--windows-file-version=$Version",
        "--windows-product-version=$Version",
        "--windows-file-description=Spectrum Minecraft Launcher",
        $Entry
    )

    Write-Host "[nuitka] compiling $Entry (version $Version) ..."
    & $python (Join-Path $Root "make_tools.py") nuitka @nuitkaArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $base = [System.IO.Path]::GetFileNameWithoutExtension($Entry)
    $distSrc = Join-Path $scratch "$base.dist"
    if (-not (Test-Path $distSrc)) {
        throw "Nuitka output not found: $distSrc"
    }

    if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    Copy-Item $distSrc (Join-Path $OutDir "main.dist") -Recurse -Force

    $stampDir = Split-Path $StampFile -Parent
    if ($stampDir -and -not (Test-Path $stampDir)) {
        New-Item -ItemType Directory -Force -Path $stampDir | Out-Null
    }
    Set-Content -Path $StampFile -Value (Get-Date -Format o) -Encoding utf8
    Write-Host "Nuitka standalone -> $(Join-Path $OutDir 'main.dist')"
} finally {
    Remove-Item $scratch -Recurse -Force -ErrorAction SilentlyContinue
}
