# -*- coding: utf-8 -*-
"""
WBTool 智慧大屏辅助系统 - 主程序
负责创建并运行悬浮球（悬浮球菜单内含白板、设置界面）。
运行方式：python main.py
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.code.active.floating_ball import FloatingBall

# 应用名称与版本号
APP_NAME = "WBTool"
APP_VERSION = "1.0.0"


def main():
    # 高 DPI 缩放策略：保证高分屏下界面清晰
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    # 关闭所有窗口时不自动退出，由悬浮球菜单的“关闭”按钮显式退出
    app.setQuitOnLastWindowClosed(False)

    # 运行悬浮球：功能选择条可打开白板，长按进入设置界面
    ball = FloatingBall()
    ball.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
