"""PyInstaller onedir specification for a future macOS build."""

from pathlib import Path


project_root = Path(SPECPATH).resolve().parents[1]
package_root = project_root / "texcleaner"

a = Analysis(
    [str(package_root / "__main__.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(package_root / "assets"), "texcleaner/assets"),
        (str(package_root / "scripts"), "texcleaner/scripts"),
        (str(project_root / "LICENSE"), "."),
        (str(project_root / "THIRD_PARTY_NOTICES.md"), "."),
    ],
    hiddenimports=[],
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
    name="TeX Cleaner",
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
    icon=str(package_root / "assets" / "icons" / "texcleaner.icns"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    a.zipfiles,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TeX Cleaner",
)
