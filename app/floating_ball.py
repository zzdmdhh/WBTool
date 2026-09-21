# -*- coding: utf-8 -*-
"""
悬浮球模块（主程序模块的一部分，需求 WB-001）

功能：
- 半接管模式下程序启动后显示悬浮球，作为主操作入口；
- 悬浮球可拖动至屏幕任意位置，松开后靠近屏幕边缘时自动吸附；
- 单击弹出功能菜单：白板、屏幕批注、退出（3 个按钮）；
- 长按打开设置；
- 点击「退出」后由主控制器退出整个程序（所有模块一并退出）。

说明：
- 本控件为无边框、置顶、不在任务栏显示的小工具窗口（Qt.Tool）；
- 白板 / 屏幕批注 / 设置 对应模块尚未开发，本类只对外发射信号，
  由主控制器（main_controller.py）统一接线与占位提示。
"""

from PySide6.QtCore import (
    Qt,
    QTimer,
    QPoint,
    QPointF,
    QRect,
    Signal,
    QPropertyAnimation,
    QEasingCurve,
)
from PySide6.QtGui import (
    QColor,
    QPainter,
    QRadialGradient,
    QPainterPath,
    QFont,
)
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QPushButton,
    QVBoxLayout,
    QGraphicsDropShadowEffect,
    QApplication,
)

# ---------- 常量配置 ----------
BALL_SIZE = 56            # 悬浮球直径（逻辑像素，高 DPI 由 Qt 自动缩放）
DRAG_THRESHOLD = 6       # 按下后移动超过该距离才视为拖动（避免与单击冲突）
LONG_PRESS_MS = 600      # 长按判定时长（毫秒）
SNAP_THRESHOLD = 90      # 松开时距离边缘小于该像素则吸附
EDGE_MARGIN = 12         # 吸附后距屏幕边缘的留白
SNAP_ANIM_MS = 180       # 吸附动画时长
POPUP_WIDTH = 168        # 弹出菜单宽度

# 蓝白简约配色
COLOR_BALL_LIGHT = QColor("#64B5F6")   # 球体高光（浅蓝）
COLOR_BALL_DARK = QColor("#1565C0")    # 球体主体（深蓝）
COLOR_BALL_TEXT = QColor("#FFFFFF")    # 球内文字（白）
COLOR_MENU_BG = "#FFFFFF"              # 菜单背景（白）
COLOR_MENU_BORDER = "#BBDEFB"          # 菜单描边（浅蓝）
COLOR_BTN_TEXT = "#1565C0"             # 按钮文字（深蓝）
COLOR_BTN_HOVER = "#E3F2FD"            # 按钮悬停（极浅蓝）
COLOR_QUIT_TEXT = "#C62828"            # 退出按钮文字（柔和红，仅作功能区分）

# 菜单按钮统一样式（蓝白简约）
MENU_BTN_QSS = """
    QPushButton {
        background-color: #FFFFFF;
        color: %s;
        border: none;
        padding: 10px 16px;
        font-family: "Microsoft YaHei";
        font-size: 14px;
        text-align: center;
    }
    QPushButton:hover { background-color: %s; }
    QPushButton:pressed { background-color: #BBDEFB; }
""" % (COLOR_BTN_TEXT, COLOR_BTN_HOVER)


class BallPopup(QFrame):
    """悬浮球单击弹出的功能菜单（白板 / 屏幕批注 / 退出）。

    使用 Qt.Popup 标志：点击菜单外任意位置自动关闭，符合触屏操作习惯。
    """

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("ballPopup")
        # 白色圆角面板 + 浅蓝描边
        self.setStyleSheet(
            "#ballPopup { background-color: %s; border: 1px solid %s; border-radius: 12px; }"
            % (COLOR_MENU_BG, COLOR_MENU_BORDER)
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.btn_whiteboard = QPushButton("白板")
        self.btn_annotation = QPushButton("屏幕批注")
        self.btn_quit = QPushButton("退出")

        for btn in (self.btn_whiteboard, self.btn_annotation):
            btn.setStyleSheet(MENU_BTN_QSS)
        # 「退出」按钮文字用柔和红色，便于一眼识别；面板仍为蓝白配色
        self.btn_quit.setStyleSheet(
            MENU_BTN_QSS.replace(COLOR_BTN_TEXT, COLOR_QUIT_TEXT)
        )

        for btn in (self.btn_whiteboard, self.btn_annotation, self.btn_quit):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            layout.addWidget(btn)

        self.setFixedWidth(POPUP_WIDTH)


class FloatingBall(QWidget):
    """悬浮球主控件（需求 WB-001）。

    对外信号：
    - launch_whiteboard_requested：单击菜单「白板」；
    - launch_annotation_requested：单击菜单「屏幕批注」；
    - quit_requested：单击菜单「退出」；
    - open_settings_requested：长按悬浮球。
    """

    launch_whiteboard_requested = Signal()
    launch_annotation_requested = Signal()
    quit_requested = Signal()
    open_settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 无边框 + 置顶 + 不在任务栏显示
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(BALL_SIZE, BALL_SIZE)
        self.setCursor(Qt.PointingHandCursor)
        # 柔和投影，增强悬浮感
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 90))
        self.setGraphicsEffect(shadow)

        # 长按定时器
        self._long_press_timer = QTimer(self)
        self._long_press_timer.setSingleShot(True)
        self._long_press_timer.setInterval(LONG_PRESS_MS)
        self._long_press_timer.timeout.connect(self._on_long_press)

        # 手势状态
        self._press_global_pos = QPoint()   # 按下时的全局坐标
        self._press_window_pos = QPoint()   # 按下时的窗口左上角坐标
        self._dragging = False              # 是否处于拖动中
        self._long_press_fired = False      # 本次按压是否已触发长按
        self._gesture_cancelled = False     # 长按触发后，后续手势取消

        # 吸附动画
        self._snap_anim = QPropertyAnimation(self, b"geometry", self)
        self._snap_anim.setDuration(SNAP_ANIM_MS)
        self._snap_anim.setEasingCurve(QEasingCurve.OutCubic)

        # 弹出菜单（懒加载）
        self._popup = None

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    def move_to_default_position(self):
        """启动时把悬浮球放到屏幕右侧偏下位置（贴近右缘，模拟已吸附状态）。"""
        screen = self.screen() or QApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = geo.right() - self.width() - EDGE_MARGIN
        y = geo.bottom() - self.height() - int(geo.height() * 0.25)
        self.move(x, y)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        """绘制蓝色渐变圆形 + 白色字母「W」。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 四周留出投影空间
        rect = self.rect().adjusted(5, 5, -5, -5)
        path = QPainterPath()
        path.addEllipse(rect)

        gradient = QRadialGradient(
            QPointF(rect.center()), rect.width() / 2
        )
        gradient.setColorAt(0.0, COLOR_BALL_LIGHT)
        gradient.setColorAt(1.0, COLOR_BALL_DARK)
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # 中央白色字母
        painter.setPen(COLOR_BALL_TEXT)
        font = QFont("Microsoft YaHei", 13, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, "W")

    # ------------------------------------------------------------------
    # 鼠标交互：拖动 / 单击 / 长按 识别
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)
        # 记录按下起点
        self._press_global_pos = event.globalPosition().toPoint()
        self._press_window_pos = self.pos()
        self._dragging = False
        self._long_press_fired = False
        self._gesture_cancelled = False
        self._long_press_timer.start()
        event.accept()

    def mouseMoveEvent(self, event):
        if self._press_global_pos.isNull():
            return
        # 超过阈值才进入拖动；一旦拖动就取消长按判定
        if not self._dragging:
            moved = (
                event.globalPosition().toPoint() - self._press_global_pos
            ).manhattanLength()
            if moved > DRAG_THRESHOLD:
                self._dragging = True
                self._long_press_timer.stop()
        if self._dragging and not self._gesture_cancelled:
            delta = event.globalPosition().toPoint() - self._press_global_pos
            self.move(self._press_window_pos + delta)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mouseReleaseEvent(event)
        self._long_press_timer.stop()

        if not self._gesture_cancelled:
            if not self._dragging and not self._long_press_fired:
                # 单击（未拖动、未触发长按）：弹出功能菜单
                self._show_popup()
            elif self._dragging:
                # 拖动结束：靠近边缘则自动吸附
                self._snap_to_edge()

        # 复位状态
        self._press_global_pos = QPoint()
        self._dragging = False
        self._long_press_fired = False
        self._gesture_cancelled = False
        event.accept()

    def _on_long_press(self):
        """长按计时结束：打开设置。"""
        self._long_press_fired = True
        self._gesture_cancelled = True   # 取消后续的单击 / 拖动行为
        self.open_settings_requested.emit()

    # ------------------------------------------------------------------
    # 边缘吸附
    # ------------------------------------------------------------------
    def _snap_to_edge(self):
        """根据松开时的位置，对距离屏幕边缘足够近的一侧做吸附动画。"""
        screen = self.screen() or QApplication.primaryScreen()
        geo = screen.availableGeometry()

        x, y = self.x(), self.y()
        w, h = self.width(), self.height()

        dist_left = x - geo.left()
        dist_right = geo.right() - (x + w)
        dist_top = y - geo.top()
        dist_bottom = geo.bottom() - (y + h)

        new_x, new_y = x, y
        # 横向：吸附到最近的左 / 右边缘
        if min(dist_left, dist_right) <= SNAP_THRESHOLD:
            if dist_left <= dist_right:
                new_x = geo.left() + EDGE_MARGIN
            else:
                new_x = geo.right() - w - EDGE_MARGIN
        # 纵向：若同样贴近上 / 下边缘，则一并吸附
        if min(dist_top, dist_bottom) <= SNAP_THRESHOLD:
            if dist_top <= dist_bottom:
                new_y = geo.top() + EDGE_MARGIN
            else:
                new_y = geo.bottom() - h - EDGE_MARGIN

        if (new_x, new_y) != (x, y):
            self._animate_move(new_x, new_y)
        else:
            # 吸附时保持在屏幕可用区域内（防止越界）
            self._clamp_to_screen()

    def _animate_move(self, x, y):
        """以动画方式移动到目标位置。"""
        self._snap_anim.stop()
        self._snap_anim.setStartValue(self.geometry())
        self._snap_anim.setEndValue(QRect(x, y, self.width(), self.height()))
        self._snap_anim.start()

    def _clamp_to_screen(self):
        """把悬浮球限制在当前屏幕可用区域内。"""
        screen = self.screen() or QApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = max(geo.left(), min(self.x(), geo.right() - self.width()))
        y = max(geo.top(), min(self.y(), geo.bottom() - self.height()))
        if (x, y) != (self.x(), self.y()):
            self.move(x, y)

    # ------------------------------------------------------------------
    # 弹出菜单
    # ------------------------------------------------------------------
    def _show_popup(self):
        """在悬浮球旁弹出功能菜单，并按屏幕边界自动调整位置。"""
        if self._popup is None:
            self._popup = BallPopup()
            self._popup.btn_whiteboard.clicked.connect(
                self.launch_whiteboard_requested.emit
            )
            self._popup.btn_annotation.clicked.connect(
                self.launch_annotation_requested.emit
            )
            self._popup.btn_quit.clicked.connect(self.quit_requested.emit)

        screen = self.screen() or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        ball_geo = self.geometry()

        # 根据悬浮球在屏幕左右半区决定菜单位于球的哪一侧
        if ball_geo.center().x() < screen_geo.center().x():
            x = ball_geo.right() + 8
        else:
            x = ball_geo.left() - self._popup.sizeHint().width() - 8
        y = ball_geo.center().y() - self._popup.sizeHint().height() // 2

        # 防止菜单超出屏幕可用区域
        x = max(screen_geo.left(),
                min(x, screen_geo.right() - self._popup.sizeHint().width()))
        y = max(screen_geo.top(),
                min(y, screen_geo.bottom() - self._popup.sizeHint().height()))

        self._popup.move(x, y)
        self._popup.show()
        self._popup.raise_()
