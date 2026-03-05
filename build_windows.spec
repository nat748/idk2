# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Windows .exe build
# Usage: pyinstaller build_windows.spec

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
    a.binaries,
    a.datas,
    [],
    name='iOS Backup Analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)
