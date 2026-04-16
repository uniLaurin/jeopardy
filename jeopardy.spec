# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# Plattform-abhängiges App-Icon — fehlt eins, läuft der Build ohne Icon weiter
_ico = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'assets', 'icon.ico')
_icns = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'assets', 'icon.icns')
win_icon = _ico if os.path.exists(_ico) else None
mac_icon = _icns if os.path.exists(_icns) else None

# pygame braucht seine SDL-Libs im Bundle — collect_* holt Binaries + Daten
try:
    from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs
    pygame_submodules = collect_submodules('pygame')
    pygame_binaries = collect_dynamic_libs('pygame')
except Exception:
    pygame_submodules = []
    pygame_binaries = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=pygame_binaries,
    datas=[
        ('questionsets', 'questionsets'),
        ('audio', 'audio'),
    ],
    hiddenimports=pygame_submodules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Jeopardy',
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
    icon=win_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Jeopardy',
)

# macOS .app bundle (ignored on Windows)
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Jeopardy.app',
        icon=mac_icon,
        bundle_identifier='com.jeopardy.game',
    )
