# -*- coding: utf-8 -*-
"""
悬浮球组件
应用的核心入口之一，启动时由 main.py 创建。支持：
- 左键拖动移动，松手后靠近屏幕边缘自动吸附
- 单击弹出功能选择条（白板 / 关闭）
- 长按进入关于界面
同时负责管理白板、关于界面的创建与显示。
本文件自包含运行所需的全部常量与工具函数。
"""

import os

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from app.code.active.about_dialog import AboutDialog
from app.code.active.whiteboard import Whiteboard

# ============ 文件路径 ============
# 文件位于 app/code/active/ 下，上溯三级得到 app/ 根目录
APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Logo 图片路径：将 logo.png 放入 app/assets/ 文件夹即可自动显示
LOGO_PATH = os.path.join(APP_ROOT, "assets", "logo.png")

# ============ 蓝白配色 ============
COLOR_PRIMARY = "#2F6BFF"        # 主蓝色
COLOR_LIGHT_BLUE = "#EAF1FF"     # 浅蓝背景（悬停/选中底）
COLOR_BORDER = "#C9DAFF"         # 浅蓝边框
COLOR_WHITE = "#FFFFFF"          # 白色
COLOR_TEXT_DARK = "#22304A"      # 主文字深色

# ============ 悬浮球 ============
BALL_SIZE = 56                   # 悬浮球边长
SNAP_THRESHOLD = 60              # 边缘吸附判定阈值（像素）
LONG_PRESS_MS = 700              # 长按判定时间（毫秒）
DRAG_THRESHOLD = 8               # 拖动判定阈值（像素）

# ============ 功能选择条 ============
BAR_BUTTON_HEIGHT = 40           # 功能按钮高度
BAR_BUTTON_WIDTH = 100           # 功能按钮宽度
BAR_PADDING = 8                  # 功能条内边距


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


class FunctionBar(QFrame):
    """悬浮球的功能选择条：白板 / 关闭，横向排列。"""

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

        self.btn_quit = self._create_button("关闭", quit_style=True)
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


class FloatingBall(QWidget):
    """可移动、可吸附、支持单击/长按的悬浮球。"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 由悬浮球管理的功能窗口实例
        self.whiteboard = None    # 白板实例

        # 窗口属性：无边框、始终置顶、工具窗（不占用任务栏）
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 支持圆角透明外观
        self.setFixedSize(BALL_SIZE, BALL_SIZE)

        self._dragging = False              # 是否正在拖动
        self._drag_offset = QPoint()        # 按下点相对窗口左上角的偏移
        self._pressed_pos = QPoint()        # 按下时的全局坐标
        self._long_press_triggered = False  # 长按是否已触发

        # 长按定时器：按住超过阈值后进入关于界面
        self._press_timer = QTimer(self)
        self._press_timer.setSingleShot(True)
        self._press_timer.setInterval(LONG_PRESS_MS)
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
                # 长按已触发过（进入关于界面），释放时不再响应单击
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
        """长按定时器到期：标记长按并打开关于界面。"""
        self._long_press_triggered = True
        self.open_about()

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

    def open_about(self):
        """打开关于界面（模态对话框）。"""
        AboutDialog().exec()

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
        threshold = SNAP_THRESHOLD

        if x <= screen.left() + threshold:
            x = screen.left()
        elif x + self.width() >= screen.right() - threshold:
            x = screen.right() - self.width()

        if y <= screen.top() + threshold:
            y = screen.top()
        elif y + self.height() >= screen.bottom() - threshold:
            y = screen.bottom() - self.height()

        self.move(x, y)
