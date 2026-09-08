# Windows conda setup

Use this file to create a Windows conda environment equivalent to the
repository's `docflow` development environment.

## Prerequisites

- Windows 10 or Windows 11
- Miniconda, Anaconda, or Miniforge
- Git

Use **Anaconda Prompt**, **Miniforge Prompt**, or **PowerShell after running
`conda init powershell`**.

## Create the environment

From the repository root:

```powershell
conda env create -f environment-windows.yml
conda activate docflow
```

If `docflow` already exists, update it instead:

```powershell
conda env update -n docflow -f environment-windows.yml --prune
conda activate docflow
```

The environment file installs the package in editable mode with development
and packaging dependencies:

```text
-e .[dev,packaging]
```

This uses the runtime dependencies declared in `pyproject.toml`, including
`customtkinter` and `arxiv-latex-cleaner`.

## Verify the installation

Run the test suite:

```powershell
python -m pytest
```

Start the application:

```powershell
python -m texcleaner
```

Check the command-line entry point:

```powershell
texcleaner --version
```

## Build the Windows application

The Windows PyInstaller specification is included in the repository. Build it
from the repository root after activating `docflow`:

```powershell
python -m PyInstaller packaging/pyinstaller/TeXCleaner-windows.spec --clean
```

The output is written to:

```text
dist\TeXCleaner\
```

You can also run the full Windows build helper from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1
```

To build the installer too:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1 -Installer
```

To build the installer, install Inno Setup on the Windows build machine and
open:

```text
packaging\windows\TeXCleaner.iss
```

## Troubleshooting

If `conda activate docflow` fails in PowerShell, initialize conda and restart
PowerShell:

```powershell
conda init powershell
```

If editable installation fails because the repository path contains special
characters, move or clone the repository into a simple path such as:

```text
C:\Users\<username>\Git-Workspace\tex-cleaner
```

If `tkinter` cannot be imported, recreate the environment from
`environment-windows.yml`. The file explicitly includes the conda `tk` package.
