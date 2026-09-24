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
# only bundle the platform tools dir this build actually needs at runtime
# (core/apk.py and core/adb.py only ever look at their own platform's subfolder)
if system == "Windows":
    tools_subdir = "windows"
elif system == "Darwin":
    tools_subdir = "macos"
elif system == "Linux":
    tools_subdir = "linux"
else:
    raise RuntimeError(f"unsupported platform: {system}")

added_data = [
    (f"tools/{tools_subdir}", f"tools/{tools_subdir}"),
    ("forms", "forms"),
    ("core/android_versions.yaml", "core")
]

# PyQt5 submodules APacKsplorer doesn't touch - trims the Qt runtime that
# gets bundled. QtSvg stays IN (planned icon browser will render adaptive
# icon layers, which are vector drawables under the hood).
pyqt5_excludes = [
    'PyQt5.QtWebEngine', 'PyQt5.QtWebEngineCore', 'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets',
    'PyQt5.QtQml', 'PyQt5.QtQuick', 'PyQt5.QtQuickWidgets', 'PyQt5.QtQuick3D',
    'PyQt5.QtSql',
    'PyQt5.QtTest',
    'PyQt5.QtBluetooth', 'PyQt5.QtNfc',
    'PyQt5.QtPositioning', 'PyQt5.QtLocation',
    'PyQt5.QtSensors',
    'PyQt5.QtSerialPort',
    'PyQt5.QtHelp',
    'PyQt5.QtDesigner',
    'PyQt5.QtXmlPatterns',
    'PyQt5.QtPrintSupport',
    'PyQt5.QtNetwork',
]

a = Analysis(
    ["main.py"],
    pathex=[project_root],
    binaries=[],
    datas=added_data,
    hiddenimports=collect_submodules("core"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=pyqt5_excludes,
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
            "LSMultipleInstancesProhibited": True,
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