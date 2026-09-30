# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

# Recopilar todos los archivos de app
datas = [
    ('app', 'app'),
    ('app/ui/screens', 'app/ui/screens'),
    ('app/ui/widgets', 'app/ui/widgets'),
    ('app/ui/themes', 'app/ui/themes'),
    ('app/assets', 'app/assets'),
]

binaries = []
hiddenimports = [
    'app.ui.screens.mesas_screen',
    'app.ui.screens.productos_screen',
    'app.ui.screens.usuarios_screen',
    'app.ui.screens.caja_screen',
    'app.ui.screens.historial_screen',
    'app.ui.screens.inventario_screen',
    'app.ui.screens.reportes_screen',
    'app.ui.screens.configuracion_screen',
    'app.ui.screens.cobro_screen',
    'app.ui.screens.github_config_screen',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name='TECHCRM-POS',
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
    icon=['app/assets/icon.ico'],
)
