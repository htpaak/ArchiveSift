@echo off
echo Building ArchiveSift single-file executable...
echo.

rem 기존 DLL 확인
if not exist "core\mpv\libmpv-2.dll" (
    if not exist "core\mpv\mpv-2.dll" (
        if not exist "core\mpv\mpv-1.dll" (
            echo WARNING: MPV DLL 파일을 찾을 수 없습니다.
            echo 계속 진행할까요? (Y/N)
            set /p choice=
            if /i NOT "%choice%"=="Y" exit /b 1
        )
    )
)

rem --onefile 옵션을 사용한 원파일 빌드
pyinstaller --clean --onefile --icon=core\ArchiveSift.ico ^
    --add-data "core/ArchiveSift.ico;." ^
    --add-binary "core/mpv/libmpv-2.dll;." ^
    --add-data "mpv_wrapper.py;." ^
    --hidden-import mpv_wrapper ^
    --hidden-import mpv ^
    --noconsole main.py -n ArchiveSift

echo.
if %errorlevel% equ 0 (
    echo Build completed successfully!
    echo.
    echo Executable can be found at: dist\ArchiveSift.exe
    echo.
    echo Note: This is a single-file executable with all dependencies bundled inside.
) else (
    echo Build failed with error code %errorlevel%.
)

pause 