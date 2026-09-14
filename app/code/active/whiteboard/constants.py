# -*- coding: utf-8 -*-
"""
白板模块常量与工具函数
包含画笔色板、蓝白配色、尺寸限制与中文星期工具函数。
白板、屏幕批注等模块共同依赖本文件。
"""

from PySide6.QtCore import QDate

# ============ 画笔色板 ============
# 画笔可选颜色（黑、红、蓝、绿、橙、紫、粉、青），白板与屏幕批注共用
BOARD_COLORS = [
    "#1F2937",  # 黑
    "#E53935",  # 红
    "#2F6BFF",  # 蓝
    "#2E7D32",  # 绿
    "#F57C00",  # 橙
    "#8E24AA",  # 紫
    "#EC407A",  # 粉
    "#00ACC1",  # 青
]

# ============ 蓝白配色 ============
COLOR_PRIMARY = "#2F6BFF"      # 主蓝色（选中/高亮）
COLOR_LIGHT_BLUE = "#EAF1FF"   # 浅蓝（悬停背景）
COLOR_BORDER = "#C9DAFF"       # 浅蓝边框
COLOR_WHITE = "#FFFFFF"        # 白色

# 白板内文字统一使用的纯黑颜色
TEXT_COLOR_BLACK = "#000000"

# 白板右上角标语文字颜色（柔和灰）
COLOR_TEXT_GRAY = "#7A8699"

# ============ 尺寸与限制 ============
PEN_WIDTH = 4          # 画笔默认笔触宽度
ERASER_WIDTH = 20      # 橡皮默认笔触宽度
MAX_PAGES = 99         # 白板最大页数
BTN_SIZE = 44          # 正方形按钮边长
PANEL_MARGIN = 36      # 角落面板与屏幕边缘的间距
TIME_FONT_SIZE = 56    # 左上角日期/时间字号


def weekday_name(date=None):
    """
    返回日期对应的中文星期名（星期一~星期日）。

    参数:
        date: QDate 对象，缺省时使用当天

    返回:
        字符串，如 "星期一"
    """
    if date is None:
        date = QDate.currentDate()
    names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return names[date.dayOfWeek() - 1]
