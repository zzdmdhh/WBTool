# -*- coding: utf-8 -*-
"""
WBTool 程序入口

功能：启动智慧大屏辅助管理操作工具（教学辅助工具）
说明：本文件仅负责创建 QApplication 并交给主程序模块（MainController）接管；
     半接管模式下由悬浮球作为主操作入口（需求 WB-001）。
"""

import sys

from PySide6.QtWidgets import QApplication

from app.main_controller import MainController


def main():
    """程序主入口"""
    app = QApplication(sys.argv)
    app.setApplicationName("WBTool")
    app.setOrganizationName("WBTool")

    # 主控制器接管：半接管模式，显示悬浮球
    controller = MainController(app)
    controller.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
