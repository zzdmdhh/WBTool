# -*- coding: utf-8 -*-
"""
WBTool 智慧大屏辅助系统 - 主程序
负责创建并运行三个核心组件：悬浮球、课程表、信息显示。
运行方式：python main.py
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from floating_ball import FloatingBall
from info_panel import InfoPanel
from schedule_widget import ScheduleWidget

# 应用名称与版本号
APP_NAME = "WBTool"
APP_VERSION = "1.0.0.100"


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

    # 运行三个核心组件：悬浮球、课程表、信息显示
    ball = FloatingBall()
    schedule = ScheduleWidget()
    info_panel = InfoPanel()

    ball.show()
    schedule.show()
    info_panel.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
