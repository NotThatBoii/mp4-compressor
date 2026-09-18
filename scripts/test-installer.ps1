param([Parameter(Mandatory=$true)][string]$Installer)
$ErrorActionPreference = 'Stop'
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('Compressly-install-test-' + [guid]::NewGuid())
$installDir = Join-Path $testRoot 'Installed App'
New-Item -ItemType Directory -Path $testRoot | Out-Null
function Run-Checked([string]$File, [string[]]$Arguments, [int]$Timeout = 180000) {
    $process = Start-Process -FilePath $File -ArgumentList $Arguments -PassThru -WindowStyle Hidden
    if (-not $process.WaitForExit($Timeout)) { Stop-Process -Id $process.Id; throw "Timed out: $File" }
    if ($process.ExitCode -ne 0) { throw "Process failed ($($process.ExitCode)): $File" }
}
$installerPath = (Resolve-Path -LiteralPath $Installer).Path
$arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', '/NOICONS',
    ('/DIR="' + $installDir + '"'), ('/LOG="' + (Join-Path $testRoot 'setup.log') + '"'))
Run-Checked $installerPath $arguments
Run-Checked (Join-Path $installDir 'Compressly.exe') @('--smoke-test') 45000
# Test an in-place reinstall/upgrade with the stable application ID.
Run-Checked $installerPath $arguments
Run-Checked (Join-Path $installDir 'Compressly.exe') @('--smoke-test') 45000
# An untracked user's video must survive uninstall, even if saved in the app folder.
$userFile = Join-Path $installDir 'user-video.mp4'
[IO.File]::WriteAllText($userFile, 'user data must survive')
Run-Checked (Join-Path $installDir 'unins000.exe') @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART')
if (Test-Path (Join-Path $installDir 'Compressly.exe')) { throw 'Uninstall left the application executable behind.' }
if ([IO.File]::ReadAllText($userFile) -ne 'user data must survive') { throw 'Uninstall modified user data.' }
Write-Output "Install, startup, reinstall, uninstall and user-data preservation passed. Logs: $testRoot"
