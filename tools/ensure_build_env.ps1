function Ensure-WindowsBuildEnv {
    if (-not $env:OS) { $env:OS = "Windows_NT" }
    if (-not $env:SystemRoot) { $env:SystemRoot = $env:WINDIR }
    if (-not $env:WINDIR) { $env:WINDIR = $env:SystemRoot }
    if (-not $env:ComSpec) {
        $env:ComSpec = Join-Path $env:SystemRoot "System32\cmd.exe"
    }
    if (-not $env:TEMP) {
        $env:TEMP = [System.IO.Path]::GetTempPath().TrimEnd('\')
    }
    if (-not $env:TMP) { $env:TMP = $env:TEMP }

    if (-not $env:PROCESSOR_ARCHITECTURE) {
        if ([Environment]::Is64BitProcess) {
            $env:PROCESSOR_ARCHITECTURE = "AMD64"
        } else {
            $env:PROCESSOR_ARCHITECTURE = "x86"
        }
    }
    if (-not $env:PROCESSOR_ARCHITEW6432) {
        if ([Environment]::Is64BitOperatingSystem -and -not [Environment]::Is64BitProcess) {
            $env:PROCESSOR_ARCHITEW6432 = "AMD64"
        }
    }
    if (-not $env:NUMBER_OF_PROCESSORS) {
        $env:NUMBER_OF_PROCESSORS = [Environment]::ProcessorCount.ToString()
    }
    if (-not $env:ProgramFiles) {
        $env:ProgramFiles = Join-Path $env:SystemRoot "Program Files"
    }
    if (-not ${env:ProgramFiles(x86)}) {
        ${env:ProgramFiles(x86)} = Join-Path $env:SystemRoot "Program Files (x86)"
    }
}

function Test-MsvcAvailable {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path $vswhere)) { return $false }
    $vsPath = & $vswhere -latest -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath 2>$null
    return [bool]$vsPath
}

function Import-VcVarsIfNeeded {
    if (-not (Test-MsvcAvailable)) {
        return $false
    }

    $vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
    $vsPath = & $vswhere -latest -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath 2>$null
    $vcvars = Join-Path $vsPath "VC\Auxiliary\Build\vcvars64.bat"
    if (-not (Test-Path $vcvars)) {
        return $false
    }

    Write-Host "[nuitka] loading MSVC environment from $vsPath"
    cmd.exe /c "`"$vcvars`" >nul 2>&1 && set" | ForEach-Object {
        if ($_ -match '^(?<key>[^=]+)=(?<val>.*)$') {
            $name = $Matches['key'].Trim()
            $value = $Matches['val']
            if ($name) {
                Set-Item -Path "Env:$name" -Value $value
            }
        }
    }
    return $true
}

function Get-NuitkaToolchainArgs {
    param(
        [int]$PyMajor,
        [int]$PyMinor
    )

    if ($PyMajor -lt 3 -or ($PyMajor -eq 3 -and $PyMinor -lt 13)) {
        return @{ Args = @("--mingw64"); Name = "MinGW64" }
    }

    $forced = $env:NUITKA_TOOLCHAIN
    if ($forced -eq "mingw64") {
        throw "NUITKA_TOOLCHAIN=mingw64 is not supported on Python 3.13+"
    }
    if ($forced -eq "msvc") {
        if (-not (Import-VcVarsIfNeeded)) {
            throw "NUITKA_TOOLCHAIN=msvc set but Visual Studio C++ tools were not found"
        }
        return @{ Args = @("--msvc=latest"); Name = "MSVC" }
    }
    if ($forced -eq "zig") {
        if (-not [Environment]::Is64BitProcess) {
            throw "NUITKA_TOOLCHAIN=zig requires 64-bit Python"
        }
        return @{ Args = @("--zig"); Name = "Zig" }
    }

    if (Import-VcVarsIfNeeded) {
        return @{ Args = @("--msvc=latest"); Name = "MSVC" }
    }

    if (-not [Environment]::Is64BitProcess) {
        throw "Python 3.13+ requires MSVC or Zig; install VS Build Tools or use 64-bit Python"
    }

    return @{
        Args = @("--zig")
        Name = "Zig (MSVC unavailable, Nuitka will download toolchain)"
    }
}

function Remove-SpectrumCoreBuildJunk {
    param([string]$PyCoreDir)

    foreach ($name in @("_spectrum_core_test.pyd", "_spectrum_core.pyd.new")) {
        $path = Join-Path $PyCoreDir $name
        if (Test-Path $path) { Remove-Item $path -Force }
    }
    Get-ChildItem $PyCoreDir -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
