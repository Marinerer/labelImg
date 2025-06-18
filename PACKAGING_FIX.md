# PyInstaller 打包问题修复说明

## 问题描述
使用 pyinstaller 将 labelImg 打包成 exe 文件后，运行时出现多个错误：

1. 找不到预定义类别文件：
```
Not find:/data/predefined_classes.txt (optional)
```

2. MIME 数据库错误：
```
OMimeDatabase:Error loading internal MIME dataAn error has been encountered at line 1 of <internal MIME data>: Premature end of document.
```

3. 属性错误：
```
AttributeError: MainWindow object has no attribute 'default_label'
```

4. 模块导入错误：
```
ModuleNotFoundError: No module named 'libs.combobox'
```

## 问题原因
1. **数据文件缺失**：PyInstaller 打包时没有正确包含 `data/predefined_classes.txt` 文件
2. **资源文件缺失**：缺少 `libs/resources.py` 文件，该文件包含 Qt 资源数据
3. **属性初始化问题**：当预定义类别文件不存在时，`default_label` 属性没有被正确初始化
4. **模块导入问题**：PyInstaller 打包时无法正确处理 `libs` 目录中的相对导入

## 解决方案

### 1. 修改代码以支持打包环境

在 `labelImg.py` 中添加了 `resource_path` 函数来处理打包后的资源路径：

```python
def resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发环境和打包环境"""
    try:
        # PyInstaller 创建临时文件夹，并将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
```

并修改了默认类别文件的路径获取方式。

### 2. 修复属性初始化问题

在 `labelImg.py` 中确保 `default_label` 属性始终被初始化：

```python
if self.label_hist:
    self.default_label = self.label_hist[0]
else:
    self.default_label = ''  # 确保属性存在
```

### 3. 生成 Qt 资源文件

使用 `pyrcc5` 命令生成 `libs/resources.py` 文件：

```bash
pyrcc5 -o libs/resources.py resources.qrc
```

### 4. 修复模块导入问题

在 `labelImg.py` 中添加路径处理代码，确保 PyInstaller 打包环境中能正确导入 libs 模块：

```python
# 添加当前目录到 Python 路径以支持打包环境
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
```

### 5. 创建 PyInstaller 配置文件

创建了 `labelImg.spec` 文件来正确配置 PyInstaller 打包选项，确保包含：
- `data/predefined_classes.txt`
- `resources` 目录
- 整个 `libs` 目录
- 所有 libs 子模块的隐式导入

### 6. 创建自动化构建脚本

- `build.bat`：Windows 批处理脚本
- `build.sh`：Linux/Mac shell 脚本

这些脚本会自动：
1. 生成 Qt 资源文件
2. 检查依赖
3. 清理旧文件
4. 执行打包

## 使用方法

### Windows
```cmd
build.bat
```

### Linux/Mac
```bash
chmod +x build.sh
./build.sh
```

### 手动构建
```bash
pyinstaller labelImg.spec
```

## 验证修复
构建完成后，运行 `dist/labelImg.exe`，应该不再出现找不到 predefined_classes.txt 的错误。

## 注意事项
1. 确保 `data/predefined_classes.txt` 文件存在
2. 如果需要包含其他资源文件，请在 `labelImg.spec` 的 `datas` 部分添加
3. 构建前请确保安装了所有依赖：`pip install pyqt5 lxml pyinstaller`