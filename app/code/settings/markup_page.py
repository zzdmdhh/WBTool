# -*- coding: utf-8 -*-
"""
屏幕批注设置页面
配置批注层的默认画笔颜色与默认笔画粗细。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.code.settings.common import (
    COLOR_PALETTE,
    COLOR_TEXT_DARK,
    COLOR_TEXT_GRAY,
    ColorPicker,
    make_form_row,
)


class MarkupPage(QWidget):
    """屏幕批注设置页面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 20)
        layout.setSpacing(16)

        title = QLabel("屏幕批注设置")
        title.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 17px; font-weight: bold;"
        )
        layout.addWidget(title)
        layout.addSpacing(4)

        # 默认画笔颜色
        self.color_picker = ColorPicker(COLOR_PALETTE)
        layout.addLayout(make_form_row("默认画笔颜色", self.color_picker))

        # 默认笔画粗细：滑块 + 数值
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setRange(2, 30)
        self.width_slider.setFixedWidth(200)
        self.width_label = QLabel()
        self.width_label.setStyleSheet(
            f"color: {COLOR_TEXT_GRAY}; font-size: 13px;"
        )
        self.width_slider.valueChanged.connect(
            lambda v: self.width_label.setText(f"{v}px")
        )
        width_row = QHBoxLayout()
        width_row.setSpacing(8)
        width_row.addWidget(self.width_slider)
        width_row.addWidget(self.width_label)
        layout.addLayout(make_form_row("默认笔画粗细", width_row))

        hint = QLabel("屏幕批注为开发中功能，设置将在功能启用后生效")
        hint.setStyleSheet(f"color: {COLOR_TEXT_GRAY}; font-size: 12px;")
        hint.setIndent(106)
        layout.addWidget(hint)

        layout.addStretch(1)

    # ---------- 数据读写 ----------

    def load_values(self, values):
        """将设置值填充到界面控件。"""
        self.color_picker.set_selected(str(values.get("default_color", COLOR_PALETTE[1])))
        self.width_slider.setValue(int(values.get("default_width", 6)))
        self.width_label.setText(f"{self.width_slider.value()}px")

    def values(self):
        """从界面控件收集设置值。"""
        return {
            "default_color": self.color_picker.value(),
            "default_width": self.width_slider.value(),
        }
