# Executable and installer packaging

The Windows build helper synchronizes the `docflow` environment, runs the
tests, and builds the application with PyInstaller.

On Windows, create or update `docflow` with the repository-level
`environment-windows.yml` file before building. See
[`docs/windows_conda_setup.md`](../docs/windows_conda_setup.md).

## Windows executable

From the repository root on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1
```

This creates an onedir application in `dist/TeXCleaner/` and uses the
multi-resolution icon and Windows version metadata. The entire
`dist/TeXCleaner/` directory is required when distributing the portable app.
Both the executable and installer use the repository icon at
`texcleaner/assets/icons/texcleaner.ico`; the build stops if it is missing.

## macOS application

On macOS, in the `docflow` environment:

```bash
python -m PyInstaller packaging/pyinstaller/TeXCleaner-macos.spec --clean
```

This creates `dist/TeX Cleaner.app` and uses
`texcleaner/assets/icons/texcleaner.icns`.

## Windows installer

Install Inno Setup 6 separately, then build both artifacts with:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_windows.ps1 -Installer
```

The per-user installer is written to `dist/installer/`. It does not require
administrator privileges. The helper finds Conda and Inno Setup in their
standard locations; use `-CondaExe C:\path\to\conda.exe` for a custom install.
Use `-SkipEnvironmentUpdate` or `-SkipTests` only for a deliberate faster
rebuild.

## Release notes

- Build executables on the target operating system; PyInstaller is not a
  cross-compiler. A build contains native binaries for the build machine's
  Windows architecture.
- Keep `LICENSE` and `THIRD_PARTY_NOTICES.md` with every redistributable
  artifact.
- Before distributing an artifact, review the exact dependency versions and
  include their required license/notice texts.
- Do not commit `build/`, `dist/`, or installer output; they are ignored by the
  repository.
