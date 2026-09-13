# -*- coding: utf-8 -*-
"""
通用文件
集中管理全局配置（配色、尺寸、路径）、屏幕工具函数与共用画布基类，
供悬浮球、白板、屏幕批注、课程表、信息面板、关于界面等所有模块统一引用。
"""

import os

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QWidget

# ============ 文件路径 ============
# 本文件位于 utils/common.py，向上两级为项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEDULE_JSON_PATH = os.path.join(PROJECT_ROOT, "config", "schedule.json")
INFO_JSON_PATH = os.path.join(PROJECT_ROOT, "config", "info.json")
# Logo 图片路径：将 logo.png 放入项目根目录的 assets/ 文件夹即可自动显示
LOGO_PATH = os.path.join(PROJECT_ROOT, "assets", "logo.png")

# ============ 蓝白配色 ============
COLOR_PRIMARY = "#2F6BFF"        # 主蓝色
COLOR_PRIMARY_DARK = "#1E50CC"   # 主蓝加深（按下效果）
COLOR_LIGHT_BLUE = "#EAF1FF"     # 浅蓝背景（悬停/选中底）
COLOR_BORDER = "#C9DAFF"         # 浅蓝边框
COLOR_WHITE = "#FFFFFF"          # 白色
COLOR_TEXT_DARK = "#22304A"      # 主文字深色
COLOR_TEXT_GRAY = "#7A8699"      # 次要文字灰色

# ============ 悬浮球 ============
BALL_SIZE = 56                   # 悬浮球边长
SNAP_THRESHOLD = 60              # 边缘吸附判定阈值（像素）
LONG_PRESS_MS = 700              # 长按判定时间（毫秒）
DRAG_THRESHOLD = 8               # 拖动判定阈值（像素）

# ============ 功能选择条 ============
BAR_BUTTON_HEIGHT = 40           # 功能按钮高度
BAR_BUTTON_WIDTH = 100           # 功能按钮宽度
BAR_PADDING = 8                  # 功能条内边距

# ============ 白板 / 批注 ============
BOARD_COLORS = ["#1F2937", "#E53935", "#2F6BFF", "#2E9E5B", "#F59E0B"]  # 画笔颜色列表

# ============ 课程表 / 信息面板 ============
SCHEDULE_REFRESH_MS = 30 * 1000  # 课程表刷新间隔（毫秒）
INFO_WIDTH = 230                 # 信息面板宽度
INFO_REFRESH_MS = 30 * 1000      # 信息面板刷新间隔（毫秒）

# ============ 应用信息 ============
APP_NAME = "WBTool"
APP_STAGE = "Alpha"            # 发布阶段：Alpha / Beta / Release
APP_VERSION = "1.0.0.100"      # 版本号
APP_DESC = "多功能智慧大屏管理系统"
APP_LICENSE = "GPL-3.0"        # 开源许可证
# 开源仓库地址（待补充）：填入后，关于界面自动将其显示为可点击的链接
APP_REPO_URL = ""
# 更新检查接口地址（待配置）：返回 JSON，格式 {"version": "x.y.z", "url": "下载地址", "notes": "更新说明"}
# 留空时，点击“检查更新”会提示尚未配置
UPDATE_URL = ""


# ============ 屏幕工具 ============

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


def weekday_name(date=None):
    """
    返回日期对应的中文星期名（周一~周日）。

    参数:
        date: QDate 对象，缺省时使用当天

    返回:
        字符串，如 "周一"
    """
    from PySide6.QtCore import QDate

    if date is None:
        date = QDate.currentDate()
    names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return names[date.dayOfWeek() - 1]


# ============ 画布基类 ============

class StrokeCanvas(QWidget):
    """
    可书写/擦除的离屏渲染画布基类，供白板与屏幕批注复用：
    - 已完成的笔画只渲染一次到离屏缓冲，之后的重绘开销与笔画数量无关
    - 当前笔画使用二次贝塞尔曲线平滑连接采样点，线条连贯
    - 橡皮擦：透明背景使用 Clear 擦除；不透明背景使用背景色覆盖
    """

    closed = Signal()  # 窗口关闭信号

    def __init__(self, background=None, parent=None):
        """
        参数:
            background: 画布背景色（QColor 或颜色字符串），None 表示透明背景
        """
        super().__init__(parent)
        self.background = QColor(background) if background else None

        self.canvas = QPixmap(1, 1)   # 离屏缓冲（已完成的笔画）
        self.current_stroke = None    # 正在绘制的笔画
        self.tool = "pen"             # 当前工具：pen（画笔）/ eraser（橡皮）
        self.color = BOARD_COLORS[0]  # 当前画笔颜色
        self.width = 4                # 当前笔画粗细

        # 窗口属性：无边框、置顶、工具窗
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )

    # ---------- 绘制 ----------

    def paintEvent(self, event):
        """绘制背景、离屏缓冲与当前笔画。"""
        painter = QPainter(self)
        if self.background is not None:
            painter.fillRect(self.rect(), self.background)
        painter.drawPixmap(0, 0, self.canvas)
        if self.current_stroke is not None:
            self._render_stroke(painter, self.current_stroke)

    def resizeEvent(self, event):
        """窗口大小变化时重建离屏缓冲并保留原内容。"""
        super().resizeEvent(event)
        new_canvas = QPixmap(self.size())
        if self.background is not None:
            new_canvas.fill(self.background)
        else:
            new_canvas.fill(Qt.transparent)
        painter = QPainter(new_canvas)
        painter.drawPixmap(0, 0, self.canvas)
        painter.end()
        self.canvas = new_canvas

    def _render_stroke(self, painter, stroke):
        """将一条笔画绘制到目标 painter 上（画笔/橡皮）。"""
        points = stroke["points"]
        if len(points) < 2:
            return
        if stroke["kind"] == "eraser":
            if self.background is None:
                # 透明背景：擦除为完全透明
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                pen = QPen(
                    QColor(0, 0, 0, 0), stroke["width"],
                    Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin,
                )
            else:
                # 不透明背景：用背景色覆盖，等效于擦除
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                pen = QPen(
                    self.background, stroke["width"],
                    Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin,
                )
        else:
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(
                QColor(stroke["color"]), stroke["width"],
                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin,
            )
        painter.setPen(pen)
        painter.drawPath(self._stroke_path(points))

    def _stroke_path(self, points):
        """
        将采样点构建为平滑路径。
        使用二次贝塞尔曲线：以相邻两点的中点为曲线端点、采样点为控制点，
        避免直线段连接造成的折线感，保证线条连贯。
        """
        path = QPainterPath(QPointF(points[0]))
        if len(points) < 3:
            # 点太少时直接连接
            for p in points[1:]:
                path.lineTo(QPointF(p))
            return path
        # 中点贝塞尔平滑
        for i in range(len(points) - 2):
            mid = QPointF(
                (points[i + 1].x() + points[i + 2].x()) / 2.0,
                (points[i + 1].y() + points[i + 2].y()) / 2.0,
            )
            path.quadTo(QPointF(points[i + 1]), mid)
        path.lineTo(QPointF(points[-1]))
        return path

    # ---------- 鼠标事件 ----------

    def mousePressEvent(self, event):
        """按下：开始一条新笔画。"""
        if event.button() == Qt.LeftButton:
            self.current_stroke = {
                "kind": "eraser" if self.tool == "eraser" else "pen",
                "color": self.color,
                "width": self.width,
                "points": [event.position().toPoint()],
            }
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """移动：向当前笔画追加采样点并重绘。"""
        if self.current_stroke is not None and event.buttons() & Qt.LeftButton:
            pos = event.position().toPoint()
            points = self.current_stroke["points"]
            # 过滤过于密集的重复采样点，减少数据量与卡顿
            if not points or (pos - points[-1]).manhattanLength() >= 2:
                points.append(pos)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """释放：完成笔画并渲染到离屏缓冲。"""
        if event.button() == Qt.LeftButton and self.current_stroke is not None:
            self._commit_stroke(self.current_stroke)
            self.current_stroke = None
        super().mouseReleaseEvent(event)

    def _commit_stroke(self, stroke):
        """将一条完成的笔画渲染到离屏缓冲。"""
        painter = QPainter(self.canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        self._render_stroke(painter, stroke)
        painter.end()
        self.update()

    # ---------- 画布操作 ----------

    def clear_canvas(self):
        """清空画布内容。"""
        if self.background is not None:
            self.canvas.fill(self.background)
        else:
            self.canvas.fill(Qt.transparent)
        self.current_stroke = None
        self.update()

    # ---------- 键盘与关闭 ----------

    def keyPressEvent(self, event):
        """按 Esc 键快速关闭。"""
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """关闭时发出关闭信号。"""
        self.closed.emit()
        super().closeEvent(event)
