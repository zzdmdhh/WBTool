# -*- coding: utf-8 -*-
"""
悬浮球模块 - 主组件
FloatingBall：应用的核心入口之一，启动时由 main.py 创建。支持：
- 左键拖动移动，松手后靠近屏幕边缘自动吸附
- 单击弹出功能选择条（白板 / 退出）
- 长按进入设置界面（唯一设置入口）
同时负责管理白板、设置界面的创建与显示。
"""

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QApplication, QWidget

from app.code.settings.settings_dialog import SettingsDialog
from app.code.settings.settings_manager import SettingsManager
from app.code.whiteboard import Whiteboard

from .constants import COLOR_PRIMARY, COLOR_WHITE, DRAG_THRESHOLD, LOGO_PATH
from .function_bar import FunctionBar


def available_screen_geometry(widget=None):
    """
    获取当前屏幕的可用区域（排除任务栏）。

    参数:
        widget: 需要定位的控件（多屏场景下用于判断所在屏幕）

    返回:
        QRect 屏幕可用区域
    """
    if widget is not None:
        screen = widget.screen()
        if screen is not None:
            return screen.availableGeometry()
    # 兜底：使用主屏幕
    return QGuiApplication.primaryScreen().availableGeometry()


class FloatingBall(QWidget):
    """可移动、可吸附、支持单击/长按的悬浮球。"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 由悬浮球管理的功能窗口实例
        self.whiteboard = None    # 白板实例

        # 从设置读取系统相关参数（大小、长按时长、吸附阈值）
        system = SettingsManager().get("system")
        self.ball_size = int(system.get("ball_size", 56))
        self.long_press_ms = int(system.get("long_press_ms", 700))
        self.snap_threshold = int(system.get("snap_threshold", 60))

        # 窗口属性：无边框、始终置顶、工具窗（不占用任务栏）
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 支持圆角透明外观
        self.setFixedSize(self.ball_size, self.ball_size)

        self._dragging = False              # 是否正在拖动
        self._drag_offset = QPoint()        # 按下点相对窗口左上角的偏移
        self._pressed_pos = QPoint()        # 按下时的全局坐标
        self._long_press_triggered = False  # 长按是否已触发

        # 长按定时器：按住超过阈值后进入设置界面
        self._press_timer = QTimer(self)
        self._press_timer.setSingleShot(True)
        self._press_timer.setInterval(self.long_press_ms)
        self._press_timer.timeout.connect(self._on_long_press)

        # 功能选择条（懒加载，单击时才创建）
        self.function_bar = None

        self._init_position()

    # ---------- 初始化 ----------

    def _init_position(self):
        """初始位置：屏幕右侧垂直居中，贴右边缘。"""
        screen = available_screen_geometry(self)
        x = screen.right() - self.width()
        y = screen.top() + (screen.height() - self.height()) // 2
        self.move(x, y)

    # ---------- 绘制 ----------

    def paintEvent(self, event):
        """绘制悬浮球：白色圆底 + 蓝色描边 + 居中 Logo（缺失时显示 W）。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(2, 2, -2, -2)

        # 底部投影（浅蓝半透明）
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(47, 107, 255, 50))
        painter.drawEllipse(rect.translated(0, 3))

        # 白色主体 + 蓝色描边
        painter.setPen(QPen(QColor(COLOR_PRIMARY), 3))
        painter.setBrush(QColor(COLOR_WHITE))
        painter.drawEllipse(rect)

        # Logo：assets/logo.png 存在时优先绘制，否则显示 W 文字图标
        logo = QPixmap(LOGO_PATH)
        if not logo.isNull():
            inner = rect.adjusted(6, 6, -6, -6)
            logo = logo.scaled(
                inner.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            path = QPainterPath()
            path.addEllipse(inner)
            painter.save()
            painter.setClipPath(path)
            x = inner.center().x() - logo.width() // 2
            y = inner.center().y() - logo.height() // 2
            painter.drawPixmap(x, y, logo)
            painter.restore()
        else:
            painter.setPen(QColor(COLOR_PRIMARY))
            painter.setFont(QFont("Microsoft YaHei UI", 18, QFont.Bold))
            painter.drawText(rect, Qt.AlignCenter, "W")

    # ---------- 鼠标事件 ----------

    def mousePressEvent(self, event):
        """按下：记录信息并启动长按定时器。"""
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._long_press_triggered = False
            self._pressed_pos = event.globalPosition().toPoint()
            self._drag_offset = self._pressed_pos - self.frameGeometry().topLeft()
            self._press_timer.start()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """移动：超过阈值视为拖动，取消长按并跟随移动。"""
        if event.buttons() & Qt.LeftButton:
            moved = (
                event.globalPosition().toPoint() - self._pressed_pos
            ).manhattanLength()
            if moved > DRAG_THRESHOLD:
                if not self._dragging:
                    self._dragging = True
                    self._press_timer.stop()  # 拖动不算长按
                self._move_within_screen(
                    event.globalPosition().toPoint() - self._drag_offset
                )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """释放：区分长按、拖动、单击三种情况。"""
        if event.button() == Qt.LeftButton:
            self._press_timer.stop()
            if self._long_press_triggered:
                # 长按已触发过（进入设置界面），释放时不再响应单击
                self._long_press_triggered = False
            elif self._dragging:
                # 拖动结束：执行边缘吸附
                self._snap_to_edge()
                self._dragging = False
            else:
                # 单击：切换功能选择条显示状态
                self._toggle_function_bar()
        super().mouseReleaseEvent(event)

    # ---------- 长按与功能条 ----------

    def _on_long_press(self):
        """长按定时器到期：标记长按并打开设置界面。"""
        self._long_press_triggered = True
        self.open_settings()

    def _toggle_function_bar(self):
        """切换功能选择条的显示/隐藏。"""
        if self.function_bar is None:
            self.function_bar = FunctionBar(self)
        if self.function_bar.isVisible():
            self.function_bar.close()
            return
        # 计算位置：优先显示在悬浮球右侧，空间不足时显示在左侧
        screen = available_screen_geometry(self)
        bar_w = self.function_bar.width()
        x = self.x() + self.width() + 8
        if x + bar_w > screen.right():
            x = self.x() - bar_w - 8
        y = self.y() + (self.height() - self.function_bar.height()) // 2
        self.function_bar.move(x, y)
        self.function_bar.show()

    # ---------- 功能窗口管理 ----------

    def open_whiteboard(self):
        """打开白板（已存在则复用）。"""
        if self.whiteboard is None:
            self.whiteboard = Whiteboard()
        if not self.whiteboard.isVisible():
            self.whiteboard.show()

    def open_settings(self):
        """打开设置界面（模态对话框），关闭后应用可能变化的系统设置。"""
        SettingsDialog().exec()
        self._apply_system_settings()

    def _apply_system_settings(self):
        """重新读取系统设置并应用到悬浮球（大小、长按时长、吸附阈值）。"""
        system = SettingsManager().get("system")
        ball_size = int(system.get("ball_size", 56))
        long_press_ms = int(system.get("long_press_ms", 700))
        snap_threshold = int(system.get("snap_threshold", 60))

        if ball_size != self.ball_size:
            self.ball_size = ball_size
            self.setFixedSize(ball_size, ball_size)
            self.update()
            self._init_position()
        if long_press_ms != self.long_press_ms:
            self.long_press_ms = long_press_ms
            self._press_timer.setInterval(long_press_ms)
        if snap_threshold != self.snap_threshold:
            self.snap_threshold = snap_threshold

    def quit(self):
        """退出应用。"""
        QApplication.instance().quit()

    # ---------- 移动与吸附 ----------

    def _move_within_screen(self, target_pos):
        """移动窗口并限制在屏幕范围内。"""
        screen = available_screen_geometry(self)
        x = max(screen.left(), min(target_pos.x(), screen.right() - self.width()))
        y = max(screen.top(), min(target_pos.y(), screen.bottom() - self.height()))
        self.move(x, y)

    def _snap_to_edge(self):
        """检测窗口是否贴近屏幕边缘，若是则吸附到边缘。"""
        screen = available_screen_geometry(self)
        x, y = self.x(), self.y()
        threshold = self.snap_threshold

        if x <= screen.left() + threshold:
            x = screen.left()
        elif x + self.width() >= screen.right() - threshold:
            x = screen.right() - self.width()

        if y <= screen.top() + threshold:
            y = screen.top()
        elif y + self.height() >= screen.bottom() - threshold:
            y = screen.bottom() - self.height()

        self.move(x, y)
