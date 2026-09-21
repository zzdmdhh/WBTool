# -*- coding: utf-8 -*-
"""
WBTool 程序入口

功能：启动智慧大屏辅助管理操作工具（教学辅助工具）
说明：本文件仅负责创建 QApplication 并进入事件循环，后续由主程序模块接管启动调度。
"""

import sys

from PySide6.QtWidgets import QApplication, QMainWindow


class MainWindow(QMainWindow):
    """主窗口占位骨架，后续由主程序模块（WB-001 / WB-002 / WB-003）完善"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WBTool")
        self.resize(800, 600)


def main():
    """程序主入口"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
