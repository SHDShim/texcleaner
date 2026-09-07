# Future executable and installer packaging

Packaging is prepared but intentionally not run during normal development.
The `docflow` environment already contains PyInstaller.

## Windows executable

From the repository root on Windows, in the `docflow` environment:

```powershell
python -m PyInstaller packaging/pyinstaller/TeXCleaner-windows.spec --clean
```

This creates an onedir application in `dist/TeXCleaner/` and uses the
multi-resolution icon at `texcleaner/assets/icons/texcleaner.ico`.

## macOS application

On macOS, in the `docflow` environment:

```bash
python -m PyInstaller packaging/pyinstaller/TeXCleaner-macos.spec --clean
```

This creates `dist/TeX Cleaner.app` and uses
`texcleaner/assets/icons/texcleaner.icns`.

## Windows installer

Install Inno Setup separately on the Windows build machine, then open
`packaging/windows/TeXCleaner.iss` in Inno Setup after building the PyInstaller
directory. The installer script is a template and has not been executed here.

## Release notes

- Build executables on the target operating system; PyInstaller is not a
  cross-compiler.
- Keep `LICENSE` and `THIRD_PARTY_NOTICES.md` with every redistributable
  artifact.
- Before distributing an artifact, review the exact dependency versions and
  include their required license/notice texts.
- Do not commit `build/`, `dist/`, or installer output; they are ignored by the
  repository.
