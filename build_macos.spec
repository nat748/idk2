# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for macOS .app build
# Usage: pyinstaller build_macos.spec

import os
import customtkinter

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(os.path.dirname(customtkinter.__file__)), 'customtkinter'),
    ],
    hiddenimports=[
        'customtkinter',
        'plistlib',
        'sqlite3',
        'hashlib',
        'Crypto',
        'Crypto.Cipher',
        'Crypto.Cipher.AES',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='iOS Backup Analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='iOS Backup Analyzer',
)

app = BUNDLE(
    coll,
    name='iOS Backup Analyzer.app',
    icon='assets/icon.icns' if os.path.exists('assets/icon.icns') else None,
    bundle_identifier='com.iosbackupanalyzer.app',
    info_plist={
        'CFBundleName': 'iOS Backup Analyzer',
        'CFBundleDisplayName': 'iOS Backup Analyzer',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
    },
)
