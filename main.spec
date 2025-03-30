# -*- mode: python ; coding: utf-8 -*-
import os

# MPV DLL 파일 경로 찾기
mpv_dll_paths = [
    os.path.join('core', 'mpv', 'libmpv-2.dll'),
    os.path.join('core', 'mpv', 'mpv-2.dll'),
    os.path.join('core', 'mpv', 'mpv-1.dll'),
    'libmpv-2.dll',
    'mpv-2.dll',
    'mpv-1.dll'
]

found_dlls = []
for dll_path in mpv_dll_paths:
    if os.path.exists(dll_path):
        found_dlls.append((dll_path, '.'))  # 루트 디렉토리에 복사
        print(f"Found MPV DLL: {dll_path}")

if not found_dlls:
    print("WARNING: MPV DLL files not found. Executable may not work properly.")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=found_dlls,  # MPV DLL 파일을 binaries에 추가
    datas=[
        ('core/ArchiveSift.ico', '.'),
        ('core/mpv/include', 'core/mpv/include'),
    ],
    hiddenimports=['mpv'],  # mpv 모듈을 명시적으로 가져오기
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
    console=False,  # 콘솔 창 숨기기
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='core/ArchiveSift.ico',
)
