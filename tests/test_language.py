#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Language功能
"""

import os
import sys
from os.path import dirname, abspath
from PyQt5.QtCore import QFile, QIODevice, QTextStream

# 添加当前目录到搜索路径
sys.path.append(dirname(dirname(abspath(__file__))))

from libs.ustr import ustr

def load_strings_directly(file_path):
    """直接加载字符串文件"""
    strings = {}
    PROP_SEPERATOR = '='
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and PROP_SEPERATOR in line:
                    key_value = line.split(PROP_SEPERATOR, 1)
                    key = key_value[0].strip()
                    value = key_value[1].strip().strip('"')
                    strings[key] = value
    
    return strings

def test_strings():
    """测试字符串加载"""
    print("=== 测试字符串资源加载 ===")
    
    # 测试英文字符串
    en_strings = load_strings_directly('resources/strings/strings.properties')
    print(f"英文字符串总数: {len(en_strings)}")
    
    # 检查新添加的字符串
    new_keys = ['languageSwitch', 'registrationCode', 'registrationSuccess', 'registrationFailed']
    
    for key in new_keys:
        if key in en_strings:
            print(f"✓ {key}: {en_strings[key]}")
        else:
            print(f"✗ 缺少字符串: {key}")
    
    print()
    
    # 测试中文字符串
    cn_strings = load_strings_directly('resources/strings/strings-zh-CN.properties')
    print(f"中文字符串总数: {len(cn_strings)}")
    
    for key in new_keys:
        if key in cn_strings:
            print(f"✓ {key}: {cn_strings[key]}")
        else:
            print(f"✗ 缺少字符串: {key}")
    
    print()
    
    # 测试日文字符串
    ja_strings = load_strings_directly('resources/strings/strings-ja-JP.properties')
    print(f"日文字符串总数: {len(ja_strings)}")
    
    for key in new_keys:
        if key in ja_strings:
            print(f"✓ {key}: {ja_strings[key]}")
        else:
            print(f"✗ 缺少字符串: {key}")

if __name__ == '__main__':
    test_strings()
    print("\n测试完成！")
    print("\n功能说明:")
    print("1. 在帮助菜单中添加了'语言切换'选项")
    print("2. 在帮助菜单中添加了'注册码'选项")
    print("3. 支持英文、中文、日文界面")
    print("4. 支持30天试用期管理")
    print("5. 注册码: mengqing723@qq.com (一年期), mengqing723@gmail.com (永久期)")