@echo off
:: Set UTF-8 encoding
chcp 65001 >nul

echo [INFO] Starting optimized build (reducing Windows Defender false positives)...

:: Clean old build files
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "LiXinTools.spec" del "LiXinTools.spec"

:: Build application (with optimization options)
echo [INFO] Building application...
pyinstaller --name "LiXinTools" ^
            --icon "gui/pic/app_icon.ico" ^
            --onefile ^
            --noconsole ^
            --noupx ^
            --clean ^
            --add-data "gui/pic;gui/pic" ^
            --add-data "config/room_data;config/room_data" ^
            main.py

:: Check build result
if %errorlevel% neq 0 (
    echo [ERROR] Build failed! Please check the output.
) else (
    echo [SUCCESS] Application build completed!
    echo [INFO] Executable file is in the "dist" folder: LiXinTools.exe
    echo [TIP] This version uses optimized options to reduce Windows Defender false positives
)

echo.
echo Press any key to exit...
pause > nul 