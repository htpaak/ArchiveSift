# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('core/mpv/libmpv-2.dll', '.'),  # MPV DLL file to main directory
        ('core/mpv/libmpv-2.dll', 'core/mpv/'),  # Keep in original path too
    ],
    datas=[
        ('core/mpv/include', 'core/mpv/include'),  # Header files
        ('core/ArchiveSift.ico', '.'),  # Icon file to root directory
        ('core/ArchiveSift.ico', 'core/'),  # Icon file to core directory
        ('ui/', 'ui/'),  # Include UI components
        ('core/', 'core/'),  # Include core modules
        ('media/', 'media/'),  # Include media handlers
        ('events/', 'events/'),  # Include event handlers
        ('file/', 'file/'),  # Include file browser components
        ('features/', 'features/'),  # Include features
        ('exceptions/', 'exceptions/'),  # Include exceptions
    ],
    hiddenimports=[
        'mpv',
        'cv2',
        'PIL',
        'io',
        'json',
        'shutil',
        're',
        'collections',
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtGui',
        'PyQt5.QtCore',
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
    name='ArchiveSift',
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
    icon='core/ArchiveSift.ico',
    version='file_version_info.txt',  # Optional version info file
) 