param([string]$Compiler, [switch]$SkipAppBuild)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
Push-Location $repoRoot
try {
    $version = (Get-Content -LiteralPath VERSION -Raw).Trim()
    if ($version -notmatch '^\d+\.\d+\.\d+$') { throw 'VERSION must contain major.minor.patch.' }
    $python = Join-Path $repoRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'Create the Windows Python virtual environment first; see README.md.' }
    if (-not $SkipAppBuild) {
        & $python -m PyInstaller --clean --noconfirm Compressly.spec
        if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }
    }
    & $python scripts/prepare-distribution.py
    if ($LASTEXITCODE -ne 0) { throw 'Distribution preparation failed.' }
    if (-not $Compiler) {
        $candidates = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe")
        $Compiler = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    }
    if (-not $Compiler -or -not (Test-Path -LiteralPath $Compiler)) { throw 'Install Inno Setup 6, or pass -Compiler with the full path to ISCC.exe.' }
    & $Compiler "/DMyAppVersion=$version" installer/Compressly.iss
    if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed.' }
    $installer = Get-Item "dist/installer/Compressly-$version-Setup-x64.exe"
    $hash = (Get-FileHash -LiteralPath $installer.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $($installer.Name)" | Set-Content -LiteralPath dist/installer/SHA256SUMS.txt -Encoding ascii
    Write-Output "Ready: $($installer.FullName)"
} finally { Pop-Location }
