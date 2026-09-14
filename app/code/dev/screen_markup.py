# -*- coding: utf-8 -*-
"""
屏幕批注组件
继承通用画布基类 StrokeCanvas，全屏透明覆盖层，
可在任意应用上方直接书写标注。
工具栏为独立置顶窗口，显示在屏幕顶部中央，避免透明层上的子控件在 Windows 下失效。
本文件自包含运行所需的全部常量与工具函数。
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from app.code.whiteboard import BOARD_COLORS, StrokeCanvas
from app.code.settings.settings_manager import SettingsManager

# 蓝白配色
COLOR_PRIMARY = "#2F6BFF"        # 主蓝色
COLOR_LIGHT_BLUE = "#EAF1FF"     # 浅蓝背景（悬停/选中底）
COLOR_BORDER = "#C9DAFF"         # 浅蓝边框
COLOR_WHITE = "#FFFFFF"          # 白色
COLOR_TEXT_DARK = "#22304A"      # 主文字深色
COLOR_TEXT_GRAY = "#7A8699"      # 次要文字灰色


class MarkupToolbar(QFrame):
    """独立置顶的批注工具栏窗口。"""

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner  # 所属的 ScreenMarkup 实例

        # 窗口属性：无边框、置顶、工具窗
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("toolbar")
        self.setStyleSheet(self._style())
        self._build_ui()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        """构建工具栏内容。"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # 标题
        title = QLabel("屏幕批注")
        title.setStyleSheet(
            f"color: {COLOR_PRIMARY}; font-size: 14px; font-weight: bold;"
            f"padding: 0 6px;"
        )

        # 工具切换：画笔 / 橡皮
        self.btn_pen = QPushButton("画笔")
        self.btn_pen.setCheckable(True)
        self.btn_pen.setCursor(Qt.PointingHandCursor)
        self.btn_pen.clicked.connect(lambda: self.owner._set_tool("pen"))

        self.btn_eraser = QPushButton("橡皮")
        self.btn_eraser.setCheckable(True)
        self.btn_eraser.setCursor(Qt.PointingHandCursor)
        self.btn_eraser.clicked.connect(lambda: self.owner._set_tool("eraser"))

        # 颜色选择按钮组
        self.color_buttons = []
        for color in BOARD_COLORS:
            btn = QPushButton()
            btn.setFixedSize(20, 20)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, c=color: self.owner._set_color(c)
            )
            self.color_buttons.append(btn)

        # 粗细调节
        self.width_label = QLabel()
        self.width_label.setStyleSheet(
            f"color: {COLOR_TEXT_GRAY}; font-size: 12px;"
        )
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setRange(2, 30)
        self.width_slider.setValue(self.owner.width)
        self.width_slider.setFixedWidth(100)
        self.width_slider.valueChanged.connect(self.owner._set_width)

        # 清空与退出
        self.btn_clear = QPushButton("清空")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.owner.clear_canvas)

        self.btn_exit = QPushButton("退出")
        self.btn_exit.setObjectName("exit")
        self.btn_exit.setCursor(Qt.PointingHandCursor)
        self.btn_exit.clicked.connect(self.owner.close)

        # 组装
        layout.addWidget(title)
        layout.addWidget(self._divider())
        layout.addWidget(self.btn_pen)
        layout.addWidget(self.btn_eraser)
        layout.addWidget(self._divider())
        for b in self.color_buttons:
            layout.addWidget(b)
        layout.addWidget(self._divider())
        layout.addWidget(self.width_label)
        layout.addWidget(self.width_slider)
        layout.addWidget(self._divider())
        layout.addWidget(self.btn_clear)
        layout.addWidget(self.btn_exit)

        # 同步当前状态
        self.refresh_tool_ui()
        self.refresh_color_ui()
        self.refresh_width_ui()

    def _divider(self):
        """创建竖直分隔线。"""
        line = QFrame()
        line.setObjectName("divider")
        line.setFixedWidth(1)
        return line

    def _style(self):
        """工具栏样式：半透明白底蓝边圆角。"""
        return f"""
        QFrame#toolbar {{
            background: rgba(255, 255, 255, 242);
            border: 1px solid {COLOR_BORDER};
            border-radius: 10px;
        }}
        QFrame#divider {{
            background: {COLOR_BORDER};
            border: none;
            max-width: 1px;
            min-width: 1px;
            margin: 6px 2px;
        }}
        QPushButton {{
            background: transparent;
            border: 1px solid {COLOR_BORDER};
            border-radius: 6px;
            color: {COLOR_TEXT_DARK};
            font-size: 13px;
            padding: 6px 12px;
        }}
        QPushButton:hover {{
            background: {COLOR_LIGHT_BLUE};
            color: {COLOR_PRIMARY};
        }}
        QPushButton:checked {{
            background: {COLOR_PRIMARY};
            color: {COLOR_WHITE};
            border-color: {COLOR_PRIMARY};
        }}
        QPushButton#exit {{
            color: #D64545;
        }}
        QPushButton#exit:hover {{
            background: #FDECEC;
            color: #C0392B;
        }}
        QSlider::groove:horizontal {{
            height: 4px;
            background: {COLOR_BORDER};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 14px;
            height: 14px;
            margin: -5px 0;
            background: {COLOR_PRIMARY};
            border-radius: 7px;
        }}
        """

    # ---------- 状态刷新 ----------

    def refresh_tool_ui(self):
        """刷新工具按钮选中状态。"""
        self.btn_pen.setChecked(self.owner.tool == "pen")
        self.btn_eraser.setChecked(self.owner.tool == "eraser")

    def refresh_color_ui(self):
        """刷新颜色按钮选中状态。"""
        for btn, color in zip(self.color_buttons, BOARD_COLORS):
            border = (
                COLOR_PRIMARY if color == self.owner.color else COLOR_WHITE
            )
            btn.setStyleSheet(
                f"QPushButton {{ background: {color}; border: 2px solid {border};"
                f" border-radius: 10px; }}"
            )

    def refresh_width_ui(self):
        """刷新粗细显示。"""
        self.width_label.setText(f"{self.owner.width}px")
        self.width_slider.setValue(self.owner.width)

    # ---------- 定位 ----------

    def _position(self):
        """定位到屏幕顶部中央。"""
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        x = screen.left() + (screen.width() - self.width()) // 2
        self.move(x, screen.top() + 14)


class ScreenMarkup(StrokeCanvas):
    """全屏透明批注层。"""

    def __init__(self, parent=None):
        # 透明背景的画布（不填充背景色，露出下层界面）
        super().__init__(background=None, parent=parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setCursor(Qt.CrossCursor)
        # 从设置读取批注默认参数（默认红色、较粗笔触）
        markup_settings = SettingsManager().get("markup")
        self.color = str(markup_settings.get("default_color", BOARD_COLORS[1]))
        self.width = int(markup_settings.get("default_width", 6))
        self.setGeometry(QGuiApplication.primaryScreen().geometry())

        # 独立置顶的工具栏窗口
        self.toolbar = MarkupToolbar(self)

    # ---------- 显示与关闭 ----------

    def showEvent(self, event):
        """显示时激活窗口并弹出工具栏。"""
        super().showEvent(event)
        self.raise_()
        self.activateWindow()
        self.toolbar._position()
        self.toolbar.show()
        self.toolbar.raise_()

    def hideEvent(self, event):
        """隐藏时同步关闭工具栏。"""
        self.toolbar.close()
        super().hideEvent(event)

    def closeEvent(self, event):
        """关闭时同步关闭工具栏。"""
        self.toolbar.close()
        super().closeEvent(event)

    # ---------- 工具控制 ----------

    def _set_tool(self, tool):
        """切换画笔/橡皮工具。"""
        self.tool = tool
        self.toolbar.refresh_tool_ui()

    def _set_color(self, color):
        """设置当前画笔颜色。"""
        self.color = color
        self.toolbar.refresh_color_ui()

    def _set_width(self, value):
        """设置笔画粗细。"""
        self.width = value
        self.toolbar.refresh_width_ui()
