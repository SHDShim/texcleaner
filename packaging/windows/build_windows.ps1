param(
    [switch]$Installer,
    [switch]$SkipEnvironmentUpdate,
    [switch]$SkipTests,
    [string]$CondaExe
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
Set-Location $RepoRoot

$windowsIcon = Join-Path $RepoRoot "texcleaner\assets\icons\texcleaner.ico"
if (-not (Test-Path -LiteralPath $windowsIcon -PathType Leaf)) {
    throw "Repository Windows icon not found: $windowsIcon"
}

if (-not $CondaExe) {
    $condaCommand = Get-Command conda.exe -ErrorAction SilentlyContinue
    if ($condaCommand) {
        $CondaExe = $condaCommand.Source
    } elseif ($env:CONDA_EXE -and (Test-Path -LiteralPath $env:CONDA_EXE)) {
        $CondaExe = $env:CONDA_EXE
    } else {
        $candidates = @(
            "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
            "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
            "$env:ProgramData\miniconda3\Scripts\conda.exe",
            "$env:ProgramData\anaconda3\Scripts\conda.exe"
        )
        $CondaExe = $candidates | Where-Object {
            Test-Path -LiteralPath $_ -ErrorAction SilentlyContinue
        } | Select-Object -First 1
    }
}

if (-not $CondaExe -or -not (Test-Path -LiteralPath $CondaExe)) {
    throw "conda.exe was not found. Install Miniconda, Anaconda, or Miniforge, or pass -CondaExe."
}

function Invoke-Conda {
    & $CondaExe @args
    if ($LASTEXITCODE -ne 0) {
        throw "Conda command failed with exit code $LASTEXITCODE."
    }
}

if (-not $SkipEnvironmentUpdate) {
    Write-Host "Synchronizing the docflow environment from environment-windows.yml..."
    Invoke-Conda env update -n docflow -f environment-windows.yml --prune
}

if (-not $SkipTests) {
    Write-Host "Running tests..."
    Invoke-Conda run --no-capture-output -n docflow python -m pytest
}

Write-Host "Building the Windows executable..."
Invoke-Conda run --no-capture-output -n docflow python -m PyInstaller `
    packaging\pyinstaller\TeXCleaner-windows.spec --clean --noconfirm

$appExe = Join-Path $RepoRoot "dist\TeXCleaner\TeXCleaner.exe"
if (-not (Test-Path -LiteralPath $appExe)) {
    throw "PyInstaller completed without creating $appExe"
}

$versionOutput = Invoke-Conda run -n docflow python -c `
    "from texcleaner.version import __version__; print(__version__)"
$version = ($versionOutput | Select-Object -Last 1).Trim()

if ($Installer) {
    $iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if (-not $iscc) {
        $isccCandidates = @(
            "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
            "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
        )
        $iscc = $isccCandidates | Where-Object {
            Test-Path -LiteralPath $_ -ErrorAction SilentlyContinue
        } | Select-Object -First 1
    }
    if (-not $iscc) {
        throw "ISCC.exe was not found. Install Inno Setup 6, then rerun with -Installer."
    }
    Write-Host "Building the Windows installer..."
    & $iscc "/DMyAppVersion=$version" packaging\windows\TeXCleaner.iss
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup failed with exit code $LASTEXITCODE."
    }
}

Write-Host "Executable output: dist\TeXCleaner\TeXCleaner.exe"
if ($Installer) {
    Write-Host "Installer output: dist\installer\TeXCleaner-$version-Setup.exe"
}
