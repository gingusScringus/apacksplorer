# build.spec
# shared PyInstaller spec for all platforms (Windows/Linux/macOS)
# run via: pyinstaller build.spec
# (produce.sh still handles per-OS orchestration/naming, this just replaces the CLI flags)

import os
import platform
import sys

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
system = platform.system()
project_root = os.path.abspath(SPECPATH)

# --- shared across all platforms ---
added_data = [
    ("tools", "tools"),
    ("forms", "forms"),
    ("core/android_versions.yaml", "core")
]

a = Analysis(
    ["gui/main_window.py"],
    pathex=[project_root],
    binaries=[],
    datas=added_data,
    hiddenimports=collect_submodules("core"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="APacKsplorer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # --windowed equivalent
    icon="assets/APacKsplorer.icns" if system == "Darwin" else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="APacKsplorer",
)

# --- macOS-only: wrap in a .app bundle with Info.plist file-association keys ---
if system == "Darwin":
    app = BUNDLE(
        coll,
        name="APacKsplorer.app",
        icon="assets/APacKsplorer.icns",
        bundle_identifier="com.gingtec.apacksplorer",
        info_plist={
            "CFBundleShortVersionString": "0.1.0",
            "UTExportedTypeDeclarations": [
                {
                    "UTTypeIdentifier": "com.gingtec.apacksplorer.apk",
                    "UTTypeDescription": "Android Package",
                    "UTTypeConformsTo": ["public.data", "public.archive"],
                    "UTTypeTagSpecification": {
                        "public.filename-extension": ["apk"]
                    },
                }
            ],
            "CFBundleDocumentTypes": [
                {
                    "CFBundleTypeName": "Android Package",
                    "CFBundleTypeRole": "Viewer",
                    "LSItemContentTypes": ["com.gingtec.apacksplorer.apk"],
                    "CFBundleTypeIconFile": "APacKsplorer.icns",
                    "LSHandlerRank": "Alternate",
                }
            ],
        },
    )