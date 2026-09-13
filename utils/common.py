# -*- coding: utf-8 -*-
"""
通用文件
集中管理全局配置（配色、尺寸、路径）与屏幕工具函数，
供悬浮球、白板、屏幕批注、课程表、信息面板、关于界面等所有模块统一引用。
"""

import os

from PySide6.QtGui import QGuiApplication

# ============ 文件路径 ============
# 本文件位于 utils/common.py，向上两级为项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEDULE_JSON_PATH = os.path.join(PROJECT_ROOT, "config", "schedule.json")
INFO_JSON_PATH = os.path.join(PROJECT_ROOT, "config", "info.json")
# Logo 图片路径：将 logo.png 放入项目根目录的 assets/ 文件夹即可自动显示
LOGO_PATH = os.path.join(PROJECT_ROOT, "assets", "logo.png")

# ============ 蓝白配色 ============
COLOR_PRIMARY = "#2F6BFF"        # 主蓝色
COLOR_PRIMARY_DARK = "#1E50CC"   # 主蓝加深（按下效果）
COLOR_LIGHT_BLUE = "#EAF1FF"     # 浅蓝背景（悬停/选中底）
COLOR_BORDER = "#C9DAFF"         # 浅蓝边框
COLOR_WHITE = "#FFFFFF"          # 白色
COLOR_TEXT_DARK = "#22304A"      # 主文字深色
COLOR_TEXT_GRAY = "#7A8699"      # 次要文字灰色

# ============ 悬浮球 ============
BALL_SIZE = 56                   # 悬浮球边长
SNAP_THRESHOLD = 60              # 边缘吸附判定阈值（像素）
LONG_PRESS_MS = 700              # 长按判定时间（毫秒）
DRAG_THRESHOLD = 8               # 拖动判定阈值（像素）

# ============ 功能选择条 ============
BAR_BUTTON_HEIGHT = 40           # 功能按钮高度
BAR_BUTTON_WIDTH = 100           # 功能按钮宽度
BAR_PADDING = 8                  # 功能条内边距

# ============ 课程表 / 信息面板 ============
SCHEDULE_REFRESH_MS = 30 * 1000  # 课程表刷新间隔（毫秒）
INFO_WIDTH = 230                 # 信息面板宽度
INFO_REFRESH_MS = 30 * 1000      # 信息面板刷新间隔（毫秒）

# ============ 应用信息 ============
APP_NAME = "WBTool"
APP_STAGE = "Alpha"            # 发布阶段：Alpha / Beta / Release
APP_VERSION = "1.0.0.100"      # 版本号
APP_DESC = "多功能智慧大屏管理系统"
APP_LICENSE = "GPL-3.0"        # 开源许可证
# 开源仓库地址（待补充）：填入后，关于界面自动将其显示为可点击的链接
APP_REPO_URL = ""
# 更新检查接口地址（待配置）：返回 JSON，格式 {"version": "x.y.z", "url": "下载地址", "notes": "更新说明"}
# 留空时，点击“检查更新”会提示尚未配置
UPDATE_URL = ""


# ============ 屏幕工具 ============

def available_screen_geometry(widget=None):
    """
    获取当前屏幕的可用区域（排除任务栏）。

    参数:
        widget: 需要定位的控件（多屏场景下用于判断所在屏幕）

    返回:
        QRect 屏幕可用区域
    """
    if widget is not None:
        screen = widget.screen()
        if screen is not None:
            return screen.availableGeometry()
    # 兜底：使用主屏幕
    return QGuiApplication.primaryScreen().availableGeometry()


def weekday_name(date=None):
    """
    返回日期对应的中文星期名（周一~周日）。

    参数:
        date: QDate 对象，缺省时使用当天

    返回:
        字符串，如 "周一"
    """
    from PySide6.QtCore import QDate

    if date is None:
        date = QDate.currentDate()
    names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return names[date.dayOfWeek() - 1]
