# -*- coding: utf-8 -*-
"""
JSON 文件读取工具
负责从磁盘读取 JSON 配置，文件缺失或格式错误时返回默认值，避免程序崩溃。
"""

import json
import os


def load_json(file_path, default=None):
    """
    读取 JSON 文件。

    参数:
        file_path: JSON 文件路径
        default: 读取失败时返回的默认值（默认空字典）

    返回:
        解析后的字典/列表；读取失败或文件不存在时返回 default
    """
    if default is None:
        default = {}
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # 文件内容不是合法 JSON 时返回默认值
        return default
