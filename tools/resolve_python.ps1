function Resolve-PythonExe {
    if ($env:PYO3_PYTHON -and (Test-Path $env:PYO3_PYTHON)) {
        return (Resolve-Path $env:PYO3_PYTHON).Path
    }

    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $cmd) {
        throw "python not found; install Python 3.12+"
    }

    $exe = $cmd.Source
    if ($exe -notmatch "WindowsApps\\python(\.exe)?$") {
        return $exe
    }

    $candidates = @(
        "$env:LOCALAPPDATA\Python\bin\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "C:\Python314\python.exe",
        "C:\Python312\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }

    throw "Full Python install required (not Windows Store stub). Found: $exe"
}
