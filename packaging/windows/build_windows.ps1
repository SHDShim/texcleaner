param(
    [switch]$Installer
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
Set-Location $RepoRoot

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "conda was not found. Install Miniconda, Anaconda, or Miniforge first."
}

$envs = conda env list
if ($envs -notmatch "^\s*docflow\s") {
    conda env create -f environment-windows.yml
} else {
    conda env update -n docflow -f environment-windows.yml --prune
}

conda run -n docflow python -m pytest
conda run -n docflow python -m PyInstaller packaging\pyinstaller\TeXCleaner-windows.spec --clean --noconfirm

if ($Installer) {
    $iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if (-not $iscc) {
        $defaultIscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
        if (Test-Path $defaultIscc) {
            $iscc = $defaultIscc
        }
    }
    if (-not $iscc) {
        throw "ISCC.exe was not found. Install Inno Setup 6 or build only the PyInstaller app."
    }
    & $iscc packaging\windows\TeXCleaner.iss
}

Write-Host "PyInstaller output: dist\TeXCleaner\"
if ($Installer) {
    Write-Host "Installer output: dist\installer\"
}
