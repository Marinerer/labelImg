# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['labelImg.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/predefined_classes.txt', 'data'),
        ('resources', 'resources'),
        ('libs', 'libs'),
    ],
    hiddenimports=[
        'pyqt5', 'lxml', 'xml', 'xml.etree', 'xml.etree.ElementTree', 'lxml.etree',
        'libs', 'libs.combobox', 'libs.default_label_combobox', 'libs.resources',
        'libs.constants', 'libs.utils', 'libs.settings', 'libs.shape',
        'libs.stringBundle', 'libs.canvas', 'libs.zoomWidget', 'libs.lightWidget',
        'libs.labelDialog', 'libs.colorDialog', 'libs.labelFile', 'libs.toolBar',
        'libs.pascal_voc_io', 'libs.yolo_io', 'libs.create_ml_io', 'libs.ustr',
        'libs.hashableQListWidgetItem'
    ],
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
    name='labelImg',
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