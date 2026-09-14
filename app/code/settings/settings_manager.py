# -*- coding: utf-8 -*-
"""
设置管理器
统一负责 app/config/settings.json 的读取、保存与默认值管理。
各模块（悬浮球、白板、屏幕批注、课程表、信息面板）通过本单例读写各自的设置项；
修改后立即写入磁盘，重启后保持生效。
"""

import json
import os

# 文件位于 app/code/settings/ 下，上溯三级得到 app/ 根目录
APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETTINGS_PATH = os.path.join(APP_ROOT, "config", "settings.json")

# ============ 默认设置 ============
DEFAULT_SETTINGS = {
    # 系统相关设置
    "system": {
        "ball_size": 56,          # 悬浮球边长（像素）
        "long_press_ms": 700,     # 长按打开设置界面的判定时间（毫秒）
        "snap_threshold": 60,     # 悬浮球边缘吸附判定阈值（像素）
    },
    # 白板设置
    "whiteboard": {
        "default_color": "#1F2937",    # 默认画笔颜色
        "default_pen_width": 4,        # 默认画笔粗细
        "default_eraser_width": 20,    # 默认橡皮粗细
        "max_pages": 99,               # 最大页数
        "show_time": False,            # 打开白板时是否默认显示时间
        "slogan": "",                  # 白板右上角标语（空表示不显示）
        "slogan_color": "#7A8699",     # 白板右上角标语颜色
    },
    # 屏幕批注设置
    "markup": {
        "default_color": "#E53935",    # 默认画笔颜色
        "default_width": 6,            # 默认笔画粗细
    },
    # 课程表设置
    "schedule": {
        "refresh_seconds": 30,         # 刷新间隔（秒）
    },
    # 信息面板设置
    "info": {
        "refresh_seconds": 30,         # 刷新间隔（秒）
        "panel_width": 230,            # 面板宽度（像素）
    },
}


def _deep_merge(base, override):
    """递归合并字典：override 的值覆盖 base，base 中缺失的键保留默认值。"""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class SettingsManager:
    """设置管理器（进程内单例）。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_data"):
            self._data = self._load()

    # ---------- 读取 ----------

    def _load(self):
        """读取磁盘上的设置并与默认值合并，缺失键自动回落到默认值。"""
        data = {}
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}
        if not isinstance(data, dict):
            data = {}
        return _deep_merge(DEFAULT_SETTINGS, data)

    def get(self, section, key=None, default=None):
        """
        读取设置。

        参数:
            section: 设置段名（system / whiteboard / markup / schedule / info）
            key: 设置键名；为 None 时返回整段设置的拷贝
            default: 键不存在时的返回值

        返回:
            设置值或整段字典
        """
        section_data = self._data.get(section, {})
        if key is None:
            return dict(section_data)
        return section_data.get(key, default)

    def all(self):
        """返回全部设置的拷贝。"""
        return json.loads(json.dumps(self._data))

    # ---------- 写入 ----------

    def update_section(self, section, values):
        """整段更新设置并保存（只接受默认设置中存在的键）。"""
        if section not in DEFAULT_SETTINGS:
            raise KeyError(f"未知设置段：{section}")
        merged = dict(self._data.get(section, {}))
        for key, value in values.items():
            if key in DEFAULT_SETTINGS[section]:
                merged[key] = value
        self._data[section] = merged
        self.save()

    def reset_section(self, section):
        """将某段设置恢复为默认值并保存。"""
        if section not in DEFAULT_SETTINGS:
            raise KeyError(f"未知设置段：{section}")
        self._data[section] = dict(DEFAULT_SETTINGS[section])
        self.save()

    def save(self):
        """将当前设置写入 settings.json。"""
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            raise OSError(f"保存设置失败：{exc}") from exc
