a = Analysis(
    ['main_view.py'],
    pathex=[],
    binaries=[],
    datas=[('style/styles.qss', 'style'), ('assets/', 'assets/'), ('Tesseract/', 'Tesseract/'), ('poppler/', 'poppler/')],
    hiddenimports=[],
    hookspath=None,
    excludes=None,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    name='PDF Flow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    icon='assets/icons/icon.png',
    upx=True,
    upx_exclude=[],
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='PDF Flow',
)