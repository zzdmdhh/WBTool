# -*- coding: utf-8 -*-
"""
白板模块 - 工具设置弹出框
ToolPopup：从工具按钮向上弹出的设置面板，点击外部自动关闭，
由白板主窗口按工具类型填充内容。
"""

from PySide6.QtCore import QEvent, QPoint, QRect, Qt
from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout

from .constants import (
    COLOR_BORDER,
    COLOR_LIGHT_BLUE,
    COLOR_PRIMARY,
    TEXT_COLOR_BLACK,
)


class ToolPopup(QFrame):
    """从工具按钮向上弹出的设置面板，点击面板外部自动关闭。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.anchor = None  # 触发本弹出框的按钮，用于判断点击是否落在按钮上

        # 作为父窗口的子控件显示，与底部工具栏相同的绘制方式与半透明效果
        self.setObjectName("popup")
        self.setStyleSheet(self._style())

        self.body = QVBoxLayout(self)  # 内容容器：由白板按工具类型填充
        self.body.setContentsMargins(12, 10, 12, 10)
        self.body.setSpacing(8)

        # 创建后立即隐藏，避免父窗口显示时弹出框跟着自动显示在左上角
        self.hide()

    def _style(self):
        """弹出框样式：半透明白底蓝边圆角，含按钮、标签与两种滑块样式。"""
        return f"""
        QFrame#popup {{
            background: rgba(255, 255, 255, 235);
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
        }}
        QPushButton {{
            background: transparent;
            border: 1px solid {COLOR_BORDER};
            border-radius: 6px;
            color: {TEXT_COLOR_BLACK};
            font-size: 13px;
            padding: 6px 14px;
        }}
        QPushButton:hover {{
            background: {COLOR_LIGHT_BLUE};
            color: {COLOR_PRIMARY};
        }}
        QPushButton#danger {{
            background: #FDECEC;
            border: 1px solid #F0B8B8;
            color: #C0392B;
        }}
        QPushButton#danger:hover {{
            background: #F8D7DA;
            color: #A93226;
        }}
        QLabel {{
            color: {TEXT_COLOR_BLACK};
            font-size: 13px;
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
        QSlider#clearSlider::groove:horizontal {{
            height: 22px;
            background: #FDECEC;
            border: 1px solid #F0B8B8;
            border-radius: 11px;
        }}
        QSlider#clearSlider::handle:horizontal {{
            width: 26px;
            height: 26px;
            margin: -2px 0;
            background: #C0392B;
            border-radius: 13px;
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
        """点击弹出框外部区域时自动关闭；点击触发按钮则交由按钮处理。"""
        if event.type() == QEvent.MouseButtonPress:
            pos = event.globalPosition().toPoint()
            # 点击触发本弹出框的按钮：不在此关闭，由按钮切换弹出状态
            if self.anchor is not None:
                anchor_rect = QRect(
                    self.anchor.mapToGlobal(QPoint(0, 0)), self.anchor.size()
                )
                if anchor_rect.contains(pos):
                    return super().eventFilter(obj, event)
            # 点击弹出框内部：交由内部控件处理
            popup_rect = QRect(self.mapToGlobal(QPoint(0, 0)), self.size())
            if popup_rect.contains(pos):
                return super().eventFilter(obj, event)
            # 点击其他区域：关闭弹出框
            self.close()
        return super().eventFilter(obj, event)
