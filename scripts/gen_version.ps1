param(
    [string]$BuildId = $env:SERENA_BUILD_ID
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$VersionFile = Join-Path $Root "config\version.json"
$HeaderFile = Join-Path $Root "src\common\include\mc\common\version.generated.hpp"

if (-not $BuildId) {
    $BuildId = "0"
}

$commit = "dev"
try {
    $commit = (git -C $Root rev-parse --short HEAD 2>$null).Trim()
    if (-not $commit) { $commit = "dev" }
} catch {
    $commit = "dev"
}

$version = @{
    name     = "SerenaLauncher"
    codename = "Okra"
    major    = 26
    quarter  = "Q2"
    build_id = $BuildId
    commit   = $commit
} | ConvertTo-Json -Depth 3

$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($VersionFile, $version, $utf8)

$full = "26Q2.$BuildId.$commit"
$header = @"
#pragma once

#define SERENA_APP_NAME "SerenaLauncher"
#define SERENA_CODENAME "Okra"
#define SERENA_MAJOR_VERSION 26
#define SERENA_QUARTER "Q2"
#define SERENA_BUILD_ID "$BuildId"
#define SERENA_COMMIT "$commit"
#define SERENA_VERSION_STRING "$full"
"@

[System.IO.File]::WriteAllText($HeaderFile, $header, $utf8)
Write-Host "SerenaLauncher $full (Okra)"
