#!/bin/bash

echo "Building labelImg with PyInstaller..."
echo

# 检查是否安装了 pyinstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# 生成资源文件
echo "Generating resources.py..."
pyrcc5 -o libs/resources.py resources.qrc
if [ $? -ne 0 ]; then
    echo "Failed to generate resources.py"
    exit 1
fi

# 删除之前的构建文件
if [ -d "dist" ]; then
    rm -rf "dist"
fi
if [ -d "build" ]; then
    rm -rf "build"
fi

# 使用 spec 文件构建
echo "Building executable..."
pyinstaller labelImg.spec

if [ $? -eq 0 ]; then
    echo
    echo "Build completed successfully!"
    echo "Executable can be found in: dist/labelImg"
    echo
else
    echo
    echo "Build failed!"
fi