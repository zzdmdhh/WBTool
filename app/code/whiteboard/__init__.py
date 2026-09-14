# -*- coding: utf-8 -*-
"""
白板模块
由多个文件组成：constants（常量与工具）、canvas（画布基类）、
widgets（工具弹出框）、whiteboard（主窗口）。
为兼容旧导入，本包同时对外导出 BOARD_COLORS / StrokeCanvas / Whiteboard。
"""

from .canvas import StrokeCanvas
from .constants import BOARD_COLORS
from .whiteboard import Whiteboard

__all__ = ["BOARD_COLORS", "StrokeCanvas", "Whiteboard"]
