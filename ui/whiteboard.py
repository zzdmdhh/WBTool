# -*- coding: utf-8 -*-
"""
白板组件
继承通用画布基类 StrokeCanvas，全屏白色画布，
右上角时间显示，底部为控制工具栏。
"""

from PySide6.QtCore import QDateTime, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from utils import common
from utils.common import StrokeCanvas


class Whiteboard(StrokeCanvas):
    """全屏白板窗口。"""

    def __init__(self, parent=None):
        # 不透明白色背景的画布
        super().__init__(background=common.COLOR_WHITE, parent=parent)
        self.setCursor(Qt.CrossCursor)
        # 全屏显示（覆盖整个屏幕，包括任务栏区域）
        self.setGeometry(QGuiApplication.primaryScreen().geometry())
        self._build_ui()

    def showEvent(self, event):
        """显示时确保窗口置顶并激活，便于接收鼠标键盘事件。"""
        super().showEvent(event)
        self.raise_()
        self.activateWindow()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        """构建右上角时间显示区与底部工具栏。"""
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)

        # 右上角时间显示
        self.date_label = QLabel()
        self.date_label.setStyleSheet(
            f"color: {common.COLOR_TEXT_GRAY}; font-size: 16px;"
        )
        self.time_label = QLabel()
        self.time_label.setStyleSheet(
            f"color: {common.COLOR_TEXT_DARK}; font-size: 56px; font-weight: bold;"
        )
        time_box = QVBoxLayout()
        time_box.setSpacing(2)
        time_box.addWidget(self.date_label, 0, Qt.AlignRight)
        time_box.addWidget(self.time_label, 0, Qt.AlignRight)

        top_row = QHBoxLayout()
        top_row.addStretch(1)
        top_row.addLayout(time_box)
        root.addLayout(top_row)
        root.addStretch(1)

        # 底部控制工具栏
        self.toolbar = self._build_toolbar()
        root.addWidget(self.toolbar, 0, Qt.AlignHCenter)

        # 时间刷新定时器（每秒）
        self._time_timer = QTimer(self)
        self._time_timer.setInterval(1000)
        self._time_timer.timeout.connect(self._update_time)
        self._time_timer.start()
        self._update_time()

    def _build_toolbar(self):
        """构建底部工具栏：工具切换、颜色、粗细、清空、关闭。"""
        bar = QFrame()
        bar.setObjectName("toolbar")
        bar.setStyleSheet(self._toolbar_style())

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(8)

        # 工具切换：画笔 / 橡皮
        self.btn_pen = QPushButton("画笔")
        self.btn_pen.setCheckable(True)
        self.btn_pen.setCursor(Qt.PointingHandCursor)
        self.btn_pen.clicked.connect(lambda: self._set_tool("pen"))

        self.btn_eraser = QPushButton("橡皮")
        self.btn_eraser.setCheckable(True)
        self.btn_eraser.setCursor(Qt.PointingHandCursor)
        self.btn_eraser.clicked.connect(lambda: self._set_tool("eraser"))

        # 颜色选择按钮组
        self.color_buttons = []
        for color in common.BOARD_COLORS:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, c=color: self._set_color(c)
            )
            self.color_buttons.append(btn)

        # 粗细调节
        self.width_label = QLabel(f"{self.width}px")
        self.width_label.setStyleSheet(
            f"color: {common.COLOR_TEXT_GRAY}; font-size: 12px;"
        )
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setRange(2, 30)
        self.width_slider.setValue(self.width)
        self.width_slider.setFixedWidth(120)
        self.width_slider.valueChanged.connect(self._set_width)

        # 清空与关闭
        self.btn_clear = QPushButton("清空")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_canvas)

        self.btn_close = QPushButton("关闭")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close)

        # 组装
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
        layout.addWidget(self.btn_close)

        self._update_tool_ui()
        self._update_color_ui()
        return bar

    def _divider(self):
        """创建竖直分隔线。"""
        line = QFrame()
        line.setObjectName("divider")
        line.setFixedWidth(1)
        return line

    def _toolbar_style(self):
        """工具栏样式：半透明白底蓝边圆角。"""
        return f"""
        QFrame#toolbar {{
            background: rgba(255, 255, 255, 235);
            border: 1px solid {common.COLOR_BORDER};
            border-radius: 12px;
        }}
        QFrame#divider {{
            background: {common.COLOR_BORDER};
            border: none;
            max-width: 1px;
            min-width: 1px;
            margin: 6px 2px;
        }}
        QPushButton {{
            background: transparent;
            border: 1px solid {common.COLOR_BORDER};
            border-radius: 6px;
            color: {common.COLOR_TEXT_DARK};
            font-size: 13px;
            padding: 6px 14px;
        }}
        QPushButton:hover {{
            background: {common.COLOR_LIGHT_BLUE};
            color: {common.COLOR_PRIMARY};
        }}
        QPushButton:checked {{
            background: {common.COLOR_PRIMARY};
            color: {common.COLOR_WHITE};
            border-color: {common.COLOR_PRIMARY};
        }}
        QSlider::groove:horizontal {{
            height: 4px;
            background: {common.COLOR_BORDER};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 14px;
            height: 14px;
            margin: -5px 0;
            background: {common.COLOR_PRIMARY};
            border-radius: 7px;
        }}
        """

    # ---------- 工具控制 ----------

    def _set_tool(self, tool):
        """切换画笔/橡皮工具。"""
        self.tool = tool
        self._update_tool_ui()

    def _update_tool_ui(self):
        """刷新工具按钮选中状态。"""
        self.btn_pen.setChecked(self.tool == "pen")
        self.btn_eraser.setChecked(self.tool == "eraser")

    def _set_color(self, color):
        """设置当前画笔颜色。"""
        self.color = color
        self._update_color_ui()

    def _update_color_ui(self):
        """刷新颜色按钮选中状态（选中项加蓝色描边）。"""
        for btn, color in zip(self.color_buttons, common.BOARD_COLORS):
            border = (
                common.COLOR_PRIMARY if color == self.color else common.COLOR_WHITE
            )
            btn.setStyleSheet(
                f"QPushButton {{ background: {color}; border: 2px solid {border};"
                f" border-radius: 11px; }}"
            )

    def _set_width(self, value):
        """设置笔画粗细。"""
        self.width = value
        self.width_label.setText(f"{value}px")

    # ---------- 时间显示 ----------

    def _update_time(self):
        """刷新右上角时间显示。"""
        now = QDateTime.currentDateTime()
        self.time_label.setText(now.toString("HH:mm:ss"))
        self.date_label.setText(
            f"{now.toString('yyyy年MM月dd日')} {common.weekday_name(now.date())}"
        )
