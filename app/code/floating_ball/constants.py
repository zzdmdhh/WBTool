# -*- coding: utf-8 -*-
"""
悬浮球模块常量
包含文件路径、蓝白配色与功能选择条尺寸等常量。
"""

import os

# ============ 文件路径 ============
# 文件位于 app/code/floating_ball/ 下，上溯三级得到 app/ 根目录
APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Logo 图片路径：将 logo.png 放入 app/assets/ 文件夹即可自动显示
LOGO_PATH = os.path.join(APP_ROOT, "assets", "logo.png")

# ============ 蓝白配色 ============
COLOR_PRIMARY = "#2F6BFF"        # 主蓝色
COLOR_LIGHT_BLUE = "#EAF1FF"     # 浅蓝背景（悬停/选中底）
COLOR_BORDER = "#C9DAFF"         # 浅蓝边框
COLOR_WHITE = "#FFFFFF"          # 白色
COLOR_TEXT_DARK = "#22304A"      # 主文字深色

# ============ 悬浮球 ============
# 悬浮球大小、长按判定时间、吸附阈值从设置读取（见 system 设置段），
# 此处仅保留拖动判定阈值常量。
DRAG_THRESHOLD = 8               # 拖动判定阈值（像素）

# ============ 功能选择条 ============
BAR_BUTTON_HEIGHT = 40           # 功能按钮高度
BAR_BUTTON_WIDTH = 100           # 功能按钮宽度
BAR_PADDING = 8                  # 功能条内边距
