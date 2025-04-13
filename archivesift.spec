# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# mpv DLL 파일 경로 지정
mpv_dll_path = os.path.join('core', 'mpv', 'libmpv-2.dll')
if not os.path.exists(mpv_dll_path):
    mpv_dll_path = 'libmpv-2.dll'  # 대체 경로

# 모든 필요한 데이터 파일 수집
datas = []

# 아이콘 파일
icon_path = os.path.join('core', 'ArchiveSift.ico')
if os.path.exists(icon_path):
    datas.append((icon_path, 'core'))

# 에셋 폴더가 있는 경우
if os.path.exists('assets'):
    datas.append(('assets', 'assets'))

# binaries 목록 생성
binaries = []
if os.path.exists(mpv_dll_path):
    binaries.append((mpv_dll_path, 'mpv'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=['PIL', 'PIL._imagingtk', 'PIL._tkinter_finder', 'cv2', 'setup_mpv'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,  # 최적화 수준 향상
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ArchiveSift',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 콘솔 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['core\\ArchiveSift.ico'],
)
