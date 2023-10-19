# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['原神抢码器.py'],
    pathex=[],
    binaries=[
        (r'C:\Users\33323\AppData\Local\Programs\Python\Python310\Lib\site-packages\pyzbar\libzbar-64.dll', 'pyzbar'),
        (r'C:\Users\33323\AppData\Local\Programs\Python\Python310\Lib\site-packages\pyzbar\libiconv.dll', 'pyzbar')
    ],
    datas=[],
    hiddenimports=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    icon='原图_200x200.ico',
    name='原神抢码器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

