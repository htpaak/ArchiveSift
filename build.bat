@echo off
REM 현재 배치 파일의 디렉토리로 이동
cd /d "%~dp0"

REM 기존 빌드 아티팩트 제거
echo Cleaning up previous build artifacts...
if exist "__pycache__" (
    echo Removing __pycache__ directory...
    rd /s /q "__pycache__"
)
if exist "build" (
    echo Removing build directory...
    rd /s /q "build"
)
if exist "dist" (
    echo Removing dist directory...
    rd /s /q "dist"
)
echo Removing *.spec files...
del /q *.spec
echo.

echo Checking and installing PyInstaller if necessary...
REM PyInstaller 설치 확인 및 자동 설치
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller is not installed. Installing it now...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo Failed to install PyInstaller. Exiting.
        pause
        exit /b %errorlevel%
    )
)

echo Building the application...

REM PyInstaller 실행:
REM --noconsole: 콘솔 창 없이 실행 (GUI 애플리케이션용)
REM --onefile: 모든 파일을 하나의 실행 파일(.exe)로 묶음
REM --clean: 빌드 전 캐시 정리
REM --icon="assets/icon.ico": 실행 파일 아이콘 설정 (아이콘이 assets 폴더에 있다고 가정)
REM --add-data "assets;assets": assets 폴더 및 내용 포함 (필요시 경로 및 대상 수정)
REM --add-binary "core/mpv/libmpv-2.dll;.": MPV DLL 파일을 실행 파일과 같은 경로에 포함
REM --hidden-import=module_name: PyInstaller가 자동으로 찾지 못하는 모듈이 있다면 이 옵션 사용
REM --exclude-module: 특정 모듈 제외 (테스트 등)
REM --name="MediaSorterPAAK": 생성될 실행 파일의 이름 지정
REM main.py: 빌드할 메인 파이썬 스크립트
pyinstaller --noconsole ^
  --onefile ^
  --clean ^
  --icon="assets/icon.ico" ^
  --add-data "assets;assets" ^
  --add-binary "core/mpv/libmpv-2.dll;." ^
  --exclude-module=pytest ^
  --exclude-module=_pytest ^
  --exclude-module=unittest ^
  --name="MediaSorterPAAK" ^
  main.py

echo.
REM 빌드 성공/실패 확인
if %errorlevel% equ 0 (
    echo Build completed successfully!
    echo Executable can be found in the 'dist' folder.
) else (
    echo Build failed with error code %errorlevel%.
    echo Check the build logs above for details. Potential issues: missing icon/data files, hidden imports, or external DLLs like MPV.
)

pause 