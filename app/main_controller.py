# -*- coding: utf-8 -*-
"""
主程序模块（主控制器）

职责：
- 半接管模式（需求 WB-003，本期默认模式）：创建并显示悬浮球（需求 WB-001）；
- 接线悬浮球对外信号：
    * 「白板」「屏幕批注」→ 对应业务模块尚未开发，先给出占位提示；
    * 「退出」→ 调用 QApplication.quit()，整个程序（所有模块）一并退出；
    * 长按 → 打开设置（设置界面属需求 WB-005，暂为占位提示）；
- 预留模块注册位，供 WB-002（JSON 配置启动调度）与 WB-003（运行模式）接入。

说明：
- load_config() / start_modules() 为 WB-002 的占位接口，本期不启用；
- 本期不读取配置文件（无 config/ 下的 JSON 也能正常启动）。
"""

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication, QMessageBox

from .floating_ball import FloatingBall


class MainController(QObject):
    """主控制器：负责悬浮球生命周期与全局退出。"""

    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self._app = app
        self._ball = FloatingBall()

        # 接线悬浮球信号
        self._ball.launch_whiteboard_requested.connect(self._open_whiteboard)
        self._ball.launch_annotation_requested.connect(self._open_annotation)
        self._ball.quit_requested.connect(self._quit_all)
        self._ball.open_settings_requested.connect(self._open_settings)

    def start(self) -> None:
        """半接管模式启动：把悬浮球放到默认位置并显示。"""
        self._ball.move_to_default_position()
        self._ball.show()

    # ------------------------------------------------------------------
    # 信号处理（各业务模块尚未开发，先占位提示）
    # ------------------------------------------------------------------
    def _open_whiteboard(self) -> None:
        """菜单「白板」：待白板模块（WB-004）开发后接入。"""
        QMessageBox.information(
            None, "WBTool", "白板模块正在开发中（WB-004），敬请期待。"
        )

    def _open_annotation(self) -> None:
        """菜单「屏幕批注」：待屏幕批注模块开发后接入。"""
        QMessageBox.information(
            None, "WBTool", "屏幕批注模块正在开发中，敬请期待。"
        )

    def _open_settings(self) -> None:
        """长按悬浮球：待设置界面（WB-005）开发后接入。"""
        QMessageBox.information(
            None, "WBTool", "设置界面正在开发中（WB-005），敬请期待。"
        )

    def _quit_all(self) -> None:
        """退出整个程序（所有模块一并退出）。"""
        self._app.quit()


# ----------------------------------------------------------------------
# WB-002 占位接口（本期不启用，待启动调度需求开发时实现）
# ----------------------------------------------------------------------
def load_config() -> dict:
    """读取设置 JSON 配置（占位，待 WB-002 开发）。"""
    raise NotImplementedError("待 WB-002 开发")


def start_modules(config: dict) -> None:
    """按配置启动对应模块（占位，待 WB-002 开发）。"""
    raise NotImplementedError("待 WB-002 开发")
