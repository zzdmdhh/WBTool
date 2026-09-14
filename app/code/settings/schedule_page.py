# -*- coding: utf-8 -*-
"""
课程表设置页面
配置课程表的刷新间隔，并提供配置文件（schedule.json）的快速打开入口。
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.code.settings.common import (
    COLOR_PRIMARY,
    COLOR_TEXT_DARK,
    COLOR_TEXT_GRAY,
    make_form_row,
)

# 文件位于 app/code/settings/ 下，上溯三级得到 app/ 根目录
APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEDULE_JSON_PATH = os.path.join(APP_ROOT, "config", "schedule.json")


class SchedulePage(QWidget):
    """课程表设置页面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 20)
        layout.setSpacing(16)

        title = QLabel("课程表设置")
        title.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 17px; font-weight: bold;"
        )
        layout.addWidget(title)
        layout.addSpacing(4)

        # 刷新间隔
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(5, 600)
        self.refresh_spin.setSuffix(" 秒")
        self.refresh_spin.setFixedWidth(140)
        layout.addLayout(make_form_row("刷新间隔", self.refresh_spin))

        # 配置文件
        self.path_label = QLabel(SCHEDULE_JSON_PATH)
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet(
            f"color: {COLOR_TEXT_GRAY}; font-size: 12px;"
        )
        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        path_label_title = QLabel("配置文件")
        path_label_title.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 14px;"
        )
        path_label_title.setFixedWidth(96)
        path_row.addWidget(path_label_title)
        path_row.addWidget(self.path_label, 1)

        self.btn_open = QPushButton("打开配置文件")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.setStyleSheet(
            f"QPushButton {{ background: transparent; border: 1px solid #C9DAFF;"
            f" border-radius: 6px; color: {COLOR_PRIMARY}; font-size: 13px;"
            f" padding: 6px 14px; }}"
            f"QPushButton:hover {{ background: #EAF1FF; }}"
        )
        self.btn_open.clicked.connect(self._open_config)
        path_row.addWidget(self.btn_open, 0, Qt.AlignTop)
        layout.addLayout(path_row)

        hint = QLabel("课程内容（课程名称、时间、教室）在配置文件中编辑，保存后自动生效")
        hint.setStyleSheet(f"color: {COLOR_TEXT_GRAY}; font-size: 12px;")
        hint.setIndent(106)
        layout.addWidget(hint)

        layout.addStretch(1)

    # ---------- 数据读写 ----------

    def load_values(self, values):
        """将设置值填充到界面控件。"""
        self.refresh_spin.setValue(int(values.get("refresh_seconds", 30)))

    def values(self):
        """从界面控件收集设置值。"""
        return {"refresh_seconds": self.refresh_spin.value()}

    # ---------- 打开配置文件 ----------

    def _open_config(self):
        """使用系统默认编辑器打开课程表配置文件。"""
        try:
            os.startfile(SCHEDULE_JSON_PATH)  # Windows 专用
        except OSError:
            self.path_label.setText(
                f"{SCHEDULE_JSON_PATH}\n（打开失败，请手动使用编辑器打开该文件）"
            )
