"""PyInstaller onedir specification for a future Windows build."""

from pathlib import Path


project_root = Path(SPECPATH).resolve().parents[1]
package_root = project_root / "texcleaner"

a = Analysis(
    [str(project_root / "packaging" / "pyinstaller" / "texcleaner_launcher.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(package_root / "assets"), "texcleaner/assets"),
        (str(package_root / "scripts"), "texcleaner/scripts"),
        (str(project_root / "LICENSE"), "."),
        (str(project_root / "THIRD_PARTY_NOTICES.md"), "."),
    ],
    hiddenimports=["arxiv_latex_cleaner.__main__"],
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
