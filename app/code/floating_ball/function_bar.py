# -*- coding: utf-8 -*-
"""
悬浮球模块 - 功能选择条
FunctionBar：单击悬浮球时弹出的横向功能条（白板 / 退出），点击外部自动关闭。
"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QPushButton

from .constants import (
    BAR_BUTTON_HEIGHT,
    BAR_BUTTON_WIDTH,
    BAR_PADDING,
    COLOR_BORDER,
    COLOR_LIGHT_BLUE,
    COLOR_PRIMARY,
    COLOR_TEXT_DARK,
    COLOR_WHITE,
)


class FunctionBar(QFrame):
    """悬浮球的功能选择条：白板 / 退出，横向排列。"""

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner  # 悬浮球实例

        # 窗口属性：无边框、置顶、工具窗
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setObjectName("bar")

        # 固定完整尺寸：确保首次弹出时读取的宽高准确，定位不偏移
        self.setFixedSize(
            BAR_BUTTON_WIDTH * 2 + BAR_PADDING * 2 + 2,
            BAR_BUTTON_HEIGHT + BAR_PADDING * 2,
        )

        # 不透明白色背景：圆角外的角落也保持白色
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(COLOR_WHITE))
        self.setPalette(palette)
        self.setStyleSheet(self._style())

        # 横向布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            BAR_PADDING, BAR_PADDING,
            BAR_PADDING, BAR_PADDING,
        )
        layout.setSpacing(0)

        self.btn_board = self._create_button("白板")
        self.btn_board.clicked.connect(self.owner.open_whiteboard)

        self.btn_quit = self._create_button("退出", quit_style=True)
        self.btn_quit.clicked.connect(self.owner.quit)

        layout.addWidget(self.btn_board)
        layout.addWidget(self._divider())
        layout.addWidget(self.btn_quit)

    # ---------- UI 构建 ----------

    def _create_button(self, text, quit_style=False):
        """创建功能按钮。"""
        btn = QPushButton(text)
        btn.setFixedSize(BAR_BUTTON_WIDTH, BAR_BUTTON_HEIGHT)
        btn.setCursor(Qt.PointingHandCursor)
        if quit_style:
            btn.setObjectName("quit")
        return btn

    def _divider(self):
        """创建竖直分隔线。"""
        line = QFrame()
        line.setObjectName("divider")
        line.setFixedSize(1, BAR_BUTTON_HEIGHT - 12)
        return line

    def _style(self):
        """功能条样式：白底蓝边圆角卡片。"""
        return f"""
        QFrame#bar {{
            background: {COLOR_WHITE};
            border: 1px solid {COLOR_BORDER};
            border-radius: 10px;
        }}
        QFrame#divider {{
            background: {COLOR_BORDER};
            border: none;
        }}
        QPushButton {{
            background: transparent;
            border: none;
            color: {COLOR_TEXT_DARK};
            font-size: 14px;
            font-family: "Microsoft YaHei UI";
        }}
        QPushButton:hover {{
            background: {COLOR_LIGHT_BLUE};
            color: {COLOR_PRIMARY};
        }}
        QPushButton:pressed {{
            background: #D8E6FF;
        }}
        QPushButton#quit {{
            color: #D64545;
        }}
        QPushButton#quit:hover {{
            background: #FDECEC;
            color: #C0392B;
        }}
        """

    # ---------- 外部点击关闭 ----------

    def showEvent(self, event):
        """显示时安装全局事件过滤器。"""
        QApplication.instance().installEventFilter(self)
        super().showEvent(event)

    def hideEvent(self, event):
        """隐藏时移除全局事件过滤器。"""
        QApplication.instance().removeEventFilter(self)
        super().hideEvent(event)

    def eventFilter(self, obj, event):
        """点击功能条外部区域时自动关闭。"""
        if event.type() == QEvent.MouseButtonPress:
            pos = event.globalPosition().toPoint()
            ball = self.owner
            # 点击悬浮球：不在此关闭，由悬浮球自行切换菜单状态
            if ball.frameGeometry().contains(pos):
                return super().eventFilter(obj, event)
            # 点击功能条内部：交由按钮处理
            if self.frameGeometry().contains(pos):
                return super().eventFilter(obj, event)
            # 点击其他区域：关闭功能条
            self.close()
        return super().eventFilter(obj, event)
