# -*- coding: utf-8 -*-
"""
白板模块 - 画布基类
StrokeCanvas：可书写/擦除的离屏渲染画布基类，供白板与屏幕批注复用：
- 已完成的笔画只渲染一次到离屏缓冲，后续重绘开销与笔画数量无关
- 当前笔画用二次贝塞尔曲线平滑连接采样点，线条连贯
- 橡皮擦：透明背景使用 Clear 擦除；不透明背景使用背景色覆盖
"""

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from .constants import BOARD_COLORS, PEN_WIDTH


class StrokeCanvas(QWidget):
    """可书写/擦除的离屏渲染画布基类。"""

    closed = Signal()  # 窗口关闭信号，供外部监听关闭动作

    def __init__(self, background=None, parent=None):
        """
        初始化画布状态。

        参数:
            background: 画布背景色（QColor 或颜色字符串），None 表示透明背景
        """
        super().__init__(parent)
        self.background = QColor(background) if background else None

        self.canvas = QPixmap(1, 1)   # 离屏缓冲：存放已完成的笔画，减少重绘开销
        self.current_stroke = None    # 当前绘制中的笔画数据（类型/颜色/宽度/采样点）
        self.tool = "pen"             # 当前工具：pen（画笔）/ eraser（橡皮）
        self.color = BOARD_COLORS[0]  # 当前画笔颜色
        self.width = PEN_WIDTH        # 当前笔画粗细

        # 窗口属性：无边框、置顶、工具窗（不占用任务栏）
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )

    # ---------- 绘制 ----------

    def paintEvent(self, event):
        """绘制背景、已完成的笔画与正在绘制的笔画。"""
        painter = QPainter(self)
        if self.background is not None:
            painter.fillRect(self.rect(), self.background)
        painter.drawPixmap(0, 0, self.canvas)
        if self.current_stroke is not None:
            self._render_stroke(painter, self.current_stroke)

    def resizeEvent(self, event):
        """窗口尺寸变化时按新尺寸重建离屏缓冲，并保留原有内容。"""
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
        """将一条笔画按画笔/橡皮两种模式绘制到目标 painter 上。"""
        points = stroke["points"]
        if len(points) < 2:
            return
        if stroke["kind"] == "eraser":
            if self.background is None:
                # 透明背景：将笔画路径擦除为完全透明
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                pen = QPen(
                    QColor(0, 0, 0, 0), stroke["width"],
                    Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin,
                )
            else:
                # 不透明背景：用背景色覆盖笔画路径，等效于擦除
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
            # 采样点太少时直接用直线连接
            for point in points[1:]:
                path.lineTo(QPointF(point))
            return path
        # 以相邻两点的中点为端点、采样点为控制点逐段平滑
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
        """按下鼠标左键：记录起点并开始一条新笔画。"""
        if event.button() == Qt.LeftButton:
            self.current_stroke = {
                "kind": "eraser" if self.tool == "eraser" else "pen",
                "color": self.color,
                "width": self.width,
                "points": [event.position().toPoint()],
            }
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """按住左键移动：向当前笔画追加采样点并触发重绘。"""
        if self.current_stroke is not None and event.buttons() & Qt.LeftButton:
            pos = event.position().toPoint()
            points = self.current_stroke["points"]
            # 过滤过于密集的重复采样点，减少数据量与卡顿
            if not points or (pos - points[-1]).manhattanLength() >= 2:
                points.append(pos)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """松开左键：完成当前笔画并渲染到离屏缓冲。"""
        if event.button() == Qt.LeftButton and self.current_stroke is not None:
            self._commit_stroke(self.current_stroke)
            self.current_stroke = None
        super().mouseReleaseEvent(event)

    def _commit_stroke(self, stroke):
        """将一条已完成的笔画渲染进离屏缓冲，保证后续重绘无需重画。"""
        painter = QPainter(self.canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        self._render_stroke(painter, stroke)
        painter.end()
        self.update()

    # ---------- 画布操作 ----------

    def clear_canvas(self):
        """清空画布全部内容，恢复为空白背景。"""
        if self.background is not None:
            self.canvas.fill(self.background)
        else:
            self.canvas.fill(Qt.transparent)
        self.current_stroke = None
        self.update()

    # ---------- 键盘与关闭 ----------

    def keyPressEvent(self, event):
        """按 Esc 键快速关闭白板。"""
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """窗口关闭时发出关闭信号。"""
        self.closed.emit()
        super().closeEvent(event)
