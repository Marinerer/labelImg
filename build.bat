@echo off
echo Building labelImg with PyInstaller...
echo.

REM 检查是否安装了 pyinstaller
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM 生成资源文件
echo Generating resources.py...
pyrcc5 -o libs/resources.py resources.qrc
if %errorlevel% neq 0 (
    echo Failed to generate resources.py
    pause
    exit /b 1
)

REM 删除之前的构建文件
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM 使用 spec 文件构建
echo Building executable...
pyinstaller labelImg.spec

if %errorlevel% equ 0 (
    echo.
    echo Build completed successfully!
    echo Executable can be found in: dist\labelImg.exe
    echo.
    pause
) else (
    echo.
    echo Build failed!
    pause
)