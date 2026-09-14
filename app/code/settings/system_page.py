# -*- coding: utf-8 -*-
"""
系统设置页面
包含悬浮球大小、长按打开设置的时长、边缘吸附阈值，以及开机自启动。
其中开机自启动通过 Windows 注册表 Run 键读写，不写入 settings.json。
"""

import os
import sys

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.code.settings.common import (
    COLOR_TEXT_DARK,
    COLOR_TEXT_GRAY,
    make_form_row,
)

# 文件位于 app/code/settings/ 下，上溯三级得到 app/ 根目录
APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 主程序入口（用于开机自启动）
MAIN_ENTRY = os.path.join(os.path.dirname(APP_ROOT), "main.py")
APP_TITLE = "WBTool"

# 开机自启动注册表位置（当前用户）
RUN_KEY = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"


def auto_start_enabled():
    """查询开机自启动注册表项是否存在。"""
    try:
        reg = QSettings(RUN_KEY, QSettings.NativeFormat)
        return bool(reg.value(APP_TITLE))
    except Exception:
        return False


def set_auto_start(enabled):
    """
    写入或移除开机自启动注册表项。

    参数:
        enabled: True 写入启动项，False 移除启动项

    返回:
        (成功与否, 错误信息)；成功时错误信息为空字符串
    """
    try:
        reg = QSettings(RUN_KEY, QSettings.NativeFormat)
        if enabled:
            command = f'"{sys.executable}" "{MAIN_ENTRY}"'
            reg.setValue(APP_TITLE, command)
        else:
            reg.remove(APP_TITLE)
        reg.sync()
        return True, ""
    except Exception as exc:
        return False, str(exc)


class SystemPage(QWidget):
    """系统设置页面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 20)
        layout.setSpacing(14)

        title = QLabel("系统设置")
        title.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 17px; font-weight: bold;"
        )
        layout.addWidget(title)
        layout.addSpacing(4)

        # 悬浮球大小：滑块 + 数值
        self.ball_size_slider = QSlider(Qt.Horizontal)
        self.ball_size_slider.setRange(40, 80)
        self.ball_size_slider.setFixedWidth(220)
        self.ball_size_label = QLabel()
        self.ball_size_label.setStyleSheet(
            f"color: {COLOR_TEXT_GRAY}; font-size: 13px;"
        )
        self.ball_size_slider.valueChanged.connect(
            lambda v: self.ball_size_label.setText(f"{v}px")
        )
        ball_row = QHBoxLayout()
        ball_row.setSpacing(8)
        ball_row.addWidget(self.ball_size_slider)
        ball_row.addWidget(self.ball_size_label)
        layout.addLayout(make_form_row("悬浮球大小", ball_row))
        hint = QLabel("悬浮球边长（像素），保存后立即生效")
        hint.setStyleSheet(f"color: {COLOR_TEXT_GRAY}; font-size: 12px;")
        hint.setIndent(106)
        layout.addWidget(hint)
        layout.addSpacing(4)

        # 长按打开设置的判定时长
        self.long_press_spin = QSpinBox()
        self.long_press_spin.setRange(300, 2000)
        self.long_press_spin.setSingleStep(50)
        self.long_press_spin.setSuffix(" 毫秒")
        self.long_press_spin.setFixedWidth(140)
        layout.addLayout(make_form_row("长按打开设置", self.long_press_spin))

        # 边缘吸附阈值
        self.snap_spin = QSpinBox()
        self.snap_spin.setRange(20, 150)
        self.snap_spin.setSuffix(" 像素")
        self.snap_spin.setFixedWidth(140)
        layout.addLayout(make_form_row("边缘吸附阈值", self.snap_spin))

        layout.addSpacing(6)

        # 开机自启动
        self.auto_start_check = QCheckBox("开机时自动启动 WBTool")
        self.auto_start_check.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 14px;"
        )
        self.auto_start_check.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.auto_start_check)
        hint2 = QLabel("通过 Windows 注册表 Run 键实现，取消勾选即可关闭")
        hint2.setStyleSheet(f"color: {COLOR_TEXT_GRAY}; font-size: 12px;")
        hint2.setIndent(106)
        layout.addWidget(hint2)

        layout.addStretch(1)

    # ---------- 数据读写 ----------

    def load_values(self, values):
        """将设置值填充到界面控件。"""
        self.ball_size_slider.setValue(int(values.get("ball_size", 56)))
        self.ball_size_label.setText(f"{self.ball_size_slider.value()}px")
        self.long_press_spin.setValue(int(values.get("long_press_ms", 700)))
        self.snap_spin.setValue(int(values.get("snap_threshold", 60)))
        self.auto_start_check.setChecked(auto_start_enabled())

    def values(self):
        """从界面控件收集设置值。"""
        return {
            "ball_size": self.ball_size_slider.value(),
            "long_press_ms": self.long_press_spin.value(),
            "snap_threshold": self.snap_spin.value(),
        }

    def apply(self):
        """保存后执行开机自启动注册表操作。"""
        return set_auto_start(self.auto_start_check.isChecked())
