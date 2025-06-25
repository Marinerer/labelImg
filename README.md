<div align="center">
  <a href="https://vitejs.dev/">
    <img width="200" height="200" hspace="10" src="./resources/icons/app.png" alt="vite logo" />
  </a>
  <h1>labelImg</h1>
  <p>
    一个图像标注工具，它是用 `Python` 编写的，并使用 `Qt` 作为其图形界面。
  </p>
</div>

标注数据以 [ImageNet](http://www.image-net.org/) 使用的 `PASCAL VOC` 格式的 `XML` 文件保存。此外，它还支持 `YOLO` 和 `CreateML` 格式。

## Features

- 🌐 中/英/日多语言支持
- ✅ 支持标注对象多选操作
- 📋 支持复制/粘贴标注数据
- 🔖 支持同时创建多标签
- 🗑️ 同步删除图片及标注文件
- 🔄 撤销部分操作

## Usage

### Hotkeys

| Hotkey             | Description                  |
| ------------------ | ---------------------------- |
| `Ctrl + u`         | 从目录中加载所有图像         |
| `Ctrl + r`         | 更改默认标注目标目录         |
| `Ctrl + s`         | 保存                         |
| `Ctrl + d`         | 复制当前标签和矩形框         |
| `Ctrl + e`         | 更新当前矩形的标签           |
| `Ctrl + z`         | 撤销操作（仅限当前图片）     |
| `Ctrl + Shift + d` | 删除当前图像及标注文件       |
| `Delete`           | 删除选定的矩形框             |
| `Shift + c`        | 清空当前图像的所有标注       |
| `Ctrl + v`         | 粘贴上一张数据               |
| `Ctrl + Shift + c` | 复制选中的数据               |
| `Ctrl + Shift + v` | 粘贴复制的数据               |
| `Space`            | 将当前图像标记为已验证       |
| `w`                | 创建一个矩形框               |
| `d`, `]`           | 下一张图片                   |
| `a`, `[`           | 上一张图片                   |
| `Ctrl++`           | 放大                         |
| `Ctrl--`           | 缩小                         |
| `↑→↓←`             | 使用键盘箭头移动选定的矩形框 |
| `Ctrl + click`     | 点选形状                     |
| `Shift + move`     | 框选形状                     |


### 多选操作

支持选中多个形状，并同时支持 移动、删除等操作

- `单选`: 直接点击形状。
- `多选`: 按住 `Ctrl + click` 进行多选。
- `框选`: 按住 `Ctrl + move` 进行框选。
- `取消选择`: 按住 `Ctrl` + 点击已选中的形状。

> [!TIP]
> 支持 按住 `Ctrl` + 点击空白处可拖动多个选中的形状。



## 源码编译

Linux/Ubuntu/Mac 需要 [Python](https://www.python.org/downloads/) 和 [PyQt](https://pypi.org/project/PyQt5/)

### Ubuntu Linux

`Python 3 + Qt5`

```shell
sudo apt-get install pyqt5-dev-tools
sudo pip3 install -r requirements/requirements-linux-python3.txt
make qt5py3
python3 labelImg.py
python3 labelImg.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```



### macOS

`Python 3 + Qt5`

```shell
brew install qt  # Install qt-5.x.x by Homebrew
brew install libxml2

or using pip

pip3 install pyqt5 lxml # Install qt and lxml by pip

make qt5py3
python3 labelImg.py
python3 labelImg.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```



Python 3 Virtualenv (推薦方法)

Virtualenv 可以避免版本和相依性問題

```shell
brew install python3
pip3 install pipenv
pipenv run pip install pyqt5==5.15.2 lxml
pipenv run make qt5py3
pipenv run python3 labelImg.py
[Optional] rm -rf build dist; python setup.py py2app -A;mv "dist/labelImg.app" /Applications
```



### Windows

安裝 [Python](https://www.python.org/downloads/windows/), [PyQt5](https://www.riverbankcomputing.com/software/pyqt/download) 和 [install lxml](http://lxml.de/installation.html).

安裝並到 [labelImg](https://github.com/HumanSignal/labelImg/blob/master/readme/README.zh.rst#labelimg) 目錄

```shell
#pyrcc4
pyrcc4 -o libs/resources.py resources.qrc
#pyrcc5
pyrcc5 -o libs/resources.py resources.qrc

python labelImg.py
python labelImg.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```

打包 `.exe`

```shell
#Install pyinstaller and execute
pip install pyinstaller
pyinstaller --hidden-import=pyqt5 --hidden-import=lxml -F -n "labelImg" -c labelImg.py -p ./libs -p ./
```



### Windows + Anaconda

下載並安裝 [Anaconda](https://www.anaconda.com/download/#download) (Python 3+)

打開 Anaconda Prompt 然後到 [labelImg](https://github.com/HumanSignal/labelImg/blob/master/readme/README.zh.rst#labelimg) 目錄

```shell
conda install pyqt=5
conda install -c anaconda lxml
pyrcc5 -o libs/resources.py resources.qrc
python labelImg.py
python labelImg.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```



### Get from PyPI but only python3.0 or above

```shell
pip3 install labelImg
labelImg
labelImg [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```



## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a [Pull Request](https://github.com/Marinerer/labelImg).