"""PyInstaller onedir specification for the Windows desktop application."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_root = Path(SPECPATH).resolve().parents[1]
package_root = project_root / "texcleaner"

customtkinter_datas, customtkinter_binaries, customtkinter_hiddenimports = collect_all("customtkinter")
arxiv_datas, arxiv_binaries, arxiv_hiddenimports = collect_all("arxiv_latex_cleaner")

a = Analysis(
    [str(project_root / "packaging" / "pyinstaller" / "texcleaner_launcher.py")],
    pathex=[str(project_root)],
    binaries=[*customtkinter_binaries, *arxiv_binaries],
    datas=[
        (str(package_root / "assets"), "texcleaner/assets"),
        (str(package_root / "scripts"), "texcleaner/scripts"),
        (str(project_root / "LICENSE"), "."),
        (str(project_root / "THIRD_PARTY_NOTICES.md"), "."),
        *customtkinter_datas,
        *arxiv_datas,
    ],
    hiddenimports=[*customtkinter_hiddenimports, *arxiv_hiddenimports],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TeXCleaner",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(package_root / "assets" / "icons" / "texcleaner.ico"),
    version=str(project_root / "packaging" / "pyinstaller" / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    a.zipfiles,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TeXCleaner",
)
