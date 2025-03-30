# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('core/mpv/libmpv-2.dll', '.'),  # 루트 디렉토리에 복사
        ('core/mpv/libmpv-2.dll', 'mpv'),  # mpv 폴더에 복사
        ('core/mpv/libmpv-2.dll', 'core/mpv'),  # core/mpv 폴더에 복사
    ],
    datas=[
        ('core/ArchiveSift.ico', 'core'),
        ('core/mpv', 'mpv'),
        ('ui', 'ui'),
        ('media', 'media'),
        ('core', 'core'),
        ('events', 'events'),
        ('features', 'features'),
        ('file', 'file'),
        ('exceptions', 'exceptions'),
    ],
    hiddenimports=[
        'PyQt5.QtCore', 
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'cv2',
        'PIL',
        'mpv',
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

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ArchiveSift',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 콘솔 창이 표시되지 않도록 설정
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='core/ArchiveSift.ico',
)
