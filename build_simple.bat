@echo off
echo Building ArchiveSift executable...
echo.

rem 기존 디렉토리 확인
if not exist "core\mpv" (
    echo ERROR: core\mpv 디렉토리가 존재하지 않습니다.
    echo MPV DLL 파일이 필요합니다. 적절한 위치에 있는지 확인하세요.
    pause
    exit /b 1
)

rem spec 파일을 사용한 빌드
pyinstaller --clean main.spec

echo.
if %errorlevel% equ 0 (
    echo Build completed successfully!
    echo Executable can be found in the dist folder.
    
    rem 실행 파일에 DLL 파일이 포함되었는지 확인
    if exist "dist\ArchiveSift\libmpv-2.dll" (
        echo MPV DLL found in output directory.
    ) else if exist "dist\ArchiveSift\mpv-2.dll" (
        echo MPV DLL found in output directory.
    ) else if exist "dist\ArchiveSift\mpv-1.dll" (
        echo MPV DLL found in output directory.
    ) else (
        echo WARNING: MPV DLL files not found in output directory.
        echo The application may not work properly.
    )
) else (
    echo Build failed with error code %errorlevel%.
)

pause 