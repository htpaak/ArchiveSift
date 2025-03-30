@echo off
echo Building ArchiveSift single-file executable...
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller is not installed. Installing it now...
    pip install pyinstaller
)

REM Create the single-file executable
pyinstaller --clean archivesift_onefile.spec

echo.
if %errorlevel% equ 0 (
    echo Build completed successfully!
    echo Executable can be found in the dist folder.
) else (
    echo Build failed with error code %errorlevel%.
)

pause 