# -*- coding: utf-8 -*-
"""
设置模块共用组件
提供设置页面通用的蓝白配色常量、画笔色板、颜色选择器与表单行布局。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLayout, QPushButton, QWidget

# ============ 蓝白配色（与全项目一致） ============
COLOR_PRIMARY = "#2F6BFF"        # 主蓝色
COLOR_PRIMARY_DARK = "#1E50CC"   # 主蓝加深（按下效果）
COLOR_LIGHT_BLUE = "#EAF1FF"     # 浅蓝背景（悬停/选中底）
COLOR_BORDER = "#C9DAFF"         # 浅蓝边框
COLOR_WHITE = "#FFFFFF"          # 白色
COLOR_TEXT_DARK = "#22304A"      # 主文字深色
COLOR_TEXT_GRAY = "#7A8699"      # 次要文字灰色

# ============ 画笔色板（与白板/屏幕批注共用） ============
COLOR_PALETTE = [
    "#1F2937",  # 黑
    "#E53935",  # 红
    "#2F6BFF",  # 蓝
    "#2E7D32",  # 绿
    "#F57C00",  # 橙
    "#8E24AA",  # 紫
    "#EC407A",  # 粉
    "#00ACC1",  # 青
]


def make_form_row(title, widget):
    """
    构建一行设置表单：标题（固定宽度）+ 控件 + 弹性留白。

    参数:
        title: 行标题文本
        widget: 设置控件（QWidget）或控件组合（QLayout），均支持
    """
    row = QHBoxLayout()
    row.setSpacing(10)
    label = QLabel(title)
    label.setStyleSheet(f"color: {COLOR_TEXT_DARK}; font-size: 14px;")
    label.setFixedWidth(96)
    row.addWidget(label)
    if isinstance(widget, QLayout):
        row.addLayout(widget)
    else:
        row.addWidget(widget)
    row.addStretch(1)
    return row


class ColorPicker(QWidget):
    """颜色选择器：一排色块按钮，单选高亮，用于选择画笔默认颜色。"""

    def __init__(self, colors=None, parent=None):
        super().__init__(parent)
        self.colors = list(colors or COLOR_PALETTE)
        self.selected = self.colors[0]
        self._buttons = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for color in self.colors:
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, c=color: self.set_selected(c)
            )
            self._buttons.append(btn)
            layout.addWidget(btn)
        self._refresh()

    def set_selected(self, color):
        """选中指定颜色并刷新高亮；不在色板中的颜色忽略。"""
        if color not in self.colors:
            return
        self.selected = color
        self._refresh()

    def value(self):
        """返回当前选中的颜色。"""
        return self.selected

    def _refresh(self):
        """刷新色块样式：选中色块描边使用自身颜色，其余使用白色。"""
        for btn, color in zip(self._buttons, self.colors):
            border = color if color == self.selected else COLOR_WHITE
            btn.setStyleSheet(
                f"QPushButton {{ background: {color}; border: 2px solid {border};"
                f" border-radius: 12px; }}"
            )
