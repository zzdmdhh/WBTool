# -*- coding: utf-8 -*-
"""
白板组件
自包含实现全部白板功能，可独立运行（python whiteboard.py），
也可由悬浮球菜单的"白板"按钮打开。

包含：
- BOARD_COLORS：画笔颜色色板（白板与屏幕批注共用）
- StrokeCanvas：可书写/擦除的离屏渲染画布基类（白板与屏幕批注共用）
- ToolPopup：从工具按钮向上弹出的设置面板，点击外部自动关闭
- Whiteboard：全屏白色画布窗口，支持多页书写、翻页、保存与工具设置
"""

import os
import sys

from PySide6.QtCore import (
    QDate,
    QDateTime,
    QEvent,
    QPoint,
    QPointF,
    QRect,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# ============ 画笔色板 ============
# 画笔可选颜色（黑、红、蓝、绿、橙、紫、粉、青），白板与屏幕批注共用
BOARD_COLORS = [
    "#1F2937",  # 黑
    "#E53935",  # 红
    "#2F6BFF",  # 蓝
    "#2E7D32",  # 绿
    "#F57C00",  # 橙
    "#8E24AA",  # 紫
    "#EC407A",  # 粉
    "#00ACC1",  # 青
]

# ============ 蓝白配色 ============
COLOR_PRIMARY = "#2F6BFF"      # 主蓝色（选中/高亮）
COLOR_LIGHT_BLUE = "#EAF1FF"   # 浅蓝（悬停背景）
COLOR_BORDER = "#C9DAFF"       # 浅蓝边框
COLOR_WHITE = "#FFFFFF"        # 白色

# 白板内文字统一使用的纯黑颜色
TEXT_COLOR_BLACK = "#000000"

# ============ 尺寸与限制 ============
PEN_WIDTH = 4          # 画笔默认笔触宽度
ERASER_WIDTH = 20      # 橡皮默认笔触宽度
MAX_PAGES = 99         # 白板最大页数
BTN_SIZE = 44          # 正方形按钮边长
PANEL_MARGIN = 36      # 角落面板与屏幕边缘的间距
TIME_FONT_SIZE = 56    # 左上角日期/时间字号


def weekday_name(date=None):
    """
    返回日期对应的中文星期名（星期一~星期日）。

    参数:
        date: QDate 对象，缺省时使用当天

    返回:
        字符串，如 "星期一"
    """
    if date is None:
        date = QDate.currentDate()
    names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return names[date.dayOfWeek() - 1]


# ============ 画布基类 ============

class StrokeCanvas(QWidget):
    """
    可书写/擦除的离屏渲染画布基类，供白板与屏幕批注复用：
    - 已完成的笔画只渲染一次到离屏缓冲，后续重绘开销与笔画数量无关
    - 当前笔画用二次贝塞尔曲线平滑连接采样点，线条连贯
    - 橡皮擦：透明背景使用 Clear 擦除；不透明背景使用背景色覆盖
    """

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


# ============ 工具设置弹出框 ============

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


class Whiteboard(StrokeCanvas):
    """全屏白色画布窗口：左上角时间显示，底部工具栏与左下/右下角面板。"""

    def __init__(self, parent=None):
        # 以不透明白色为背景创建画布
        super().__init__(background=COLOR_WHITE, parent=parent)
        self.setCursor(Qt.CrossCursor)  # 十字光标，便于精准书写
        # 全屏显示（覆盖整个屏幕，包括任务栏区域）
        self.setGeometry(QGuiApplication.primaryScreen().geometry())

        # 多页数据：pages 保存每一页的离屏画布，canvas 始终指向当前页
        self.pages = [self.canvas]
        self.current_page_index = 0

        # 画笔与橡皮各自的笔触宽度（切换工具时决定实际使用的宽度）
        self.pen_width = PEN_WIDTH
        self.eraser_width = ERASER_WIDTH

        # 白板内部提示卡片（替代系统弹窗），首次使用时创建
        self._notice_overlay = None

        self._build_ui()

    # ---------- 窗口事件 ----------

    def showEvent(self, event):
        """窗口显示时确保置顶并激活，便于接收鼠标键盘事件。"""
        super().showEvent(event)
        self.raise_()
        self.activateWindow()

    def resizeEvent(self, event):
        """窗口尺寸变化时按新尺寸重建全部页面，并保留各页已有内容。"""
        if not self.pages:
            self.pages = [self.canvas]
            self.current_page_index = 0
            return
        new_pages = []
        for page in self.pages:
            new_page = QPixmap(self.size())
            new_page.fill(self.background)
            painter = QPainter(new_page)
            painter.drawPixmap(0, 0, page)
            painter.end()
            new_pages.append(new_page)
        self.pages = new_pages
        # canvas 必须与当前页保持同一对象引用，后续绘制才能写进对应页面
        self.canvas = self.pages[self.current_page_index]
        # 同步左下角操作面板与右下角页导航的位置
        if hasattr(self, "action_panel"):
            self._reposition_action_panel()
        if hasattr(self, "page_nav"):
            self._reposition_page_nav()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        """构建整体布局：左上角时间、底部工具栏、角落面板与工具弹出框。"""
        root = QVBoxLayout(self)
        # 底部留白与两侧角落面板一致，保证中间工具栏与两侧面板水平对齐
        root.setContentsMargins(28, 24, 28, PANEL_MARGIN)

        # 左上角时间显示：日期在上、时间在下，均左对齐，字号一致
        # 默认隐藏，由左下角"时间"按钮控制显示
        self.date_label = QLabel()
        self.date_label.setStyleSheet(self._time_label_style())
        self.time_label = QLabel()
        self.time_label.setStyleSheet(self._time_label_style())
        self.date_label.setVisible(False)
        self.time_label.setVisible(False)
        time_box = QVBoxLayout()
        time_box.setSpacing(2)
        time_box.addWidget(self.date_label, 0, Qt.AlignLeft)
        time_box.addWidget(self.time_label, 0, Qt.AlignLeft)

        top_row = QHBoxLayout()
        top_row.addLayout(time_box)
        top_row.addStretch(1)
        root.addLayout(top_row)
        root.addStretch(1)

        # 底部控制工具栏（书写工具，居中显示）
        self.toolbar = self._build_toolbar()
        root.addWidget(self.toolbar, 0, Qt.AlignHCenter)

        # 左下角操作面板与右下角页导航面板
        self._build_action_panel()
        self._build_page_nav()

        # 工具设置弹出框（画笔：颜色+粗细；橡皮：粗细+滑动清空；关闭：退出/最小化）
        self._build_pen_popup()
        self._build_eraser_popup()
        self._build_close_popup()

        # 时间刷新定时器：每秒更新一次日期与时间文本
        self._time_timer = QTimer(self)
        self._time_timer.setInterval(1000)
        self._time_timer.timeout.connect(self._update_time)
        self._time_timer.start()
        self._update_time()

    def _time_label_style(self):
        """时间标签样式：纯黑、大字号、加粗。"""
        return (
            f"color: {TEXT_COLOR_BLACK}; "
            f"font-size: {TIME_FONT_SIZE}px; font-weight: bold;"
        )

    def _build_toolbar(self):
        """构建底部工具栏：画笔、橡皮、工具（正方形按钮，居中显示）。"""
        bar = QFrame()
        bar.setObjectName("toolbar")
        bar.setStyleSheet(self._toolbar_style())

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(8)

        # 画笔：第一次点击选中画笔，再次点击弹出画笔设置框
        self.btn_pen = QPushButton("画笔")
        self.btn_pen.setCheckable(True)
        self.btn_pen.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_pen.setCursor(Qt.PointingHandCursor)
        self.btn_pen.clicked.connect(self._on_pen_clicked)

        # 橡皮：第一次点击选中橡皮，再次点击弹出橡皮设置框
        self.btn_eraser = QPushButton("橡皮")
        self.btn_eraser.setCheckable(True)
        self.btn_eraser.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_eraser.setCursor(Qt.PointingHandCursor)
        self.btn_eraser.clicked.connect(self._on_eraser_clicked)

        # 工具：预留尺子、圆规等绘图工具的入口，点击提示正在开发中
        self.btn_tool = QPushButton("工具")
        self.btn_tool.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_tool.setCursor(Qt.PointingHandCursor)
        self.btn_tool.clicked.connect(
            lambda: self._show_notice("工具功能正在开发中")
        )

        layout.addWidget(self.btn_pen)
        layout.addWidget(self.btn_eraser)
        layout.addWidget(self.btn_tool)

        # 按当前状态刷新工具按钮选中样式
        self._update_tool_ui()
        return bar

    def _build_action_panel(self):
        """构建左下角操作面板：关闭、保存、时间开关（正方形按钮）。"""
        self.action_panel = QFrame(self)
        self.action_panel.setObjectName("panel")
        self.action_panel.setStyleSheet(self._panel_style())

        layout = QHBoxLayout(self.action_panel)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # 关闭：弹出"退出 / 最小化"两个选项（最左侧）
        self.btn_close = QPushButton("关闭")
        self.btn_close.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self._on_close_clicked)

        # 保存：批量导出全部页面为图片
        self.btn_save = QPushButton("保存")
        self.btn_save.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self._save_all_pages)

        # 时间显示开关：默认不显示时间，点亮后显示，再点一次隐藏
        self.btn_time = QPushButton("时间")
        self.btn_time.setCheckable(True)
        self.btn_time.setChecked(False)
        self.btn_time.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_time.setCursor(Qt.PointingHandCursor)
        self.btn_time.clicked.connect(self._toggle_time)

        layout.addWidget(self.btn_close)
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_time)

        self._reposition_action_panel()

    def _build_page_nav(self):
        """构建右下角页导航面板：上一页 / 页码 / 下一页（正方形按钮）。"""
        self.page_nav = QFrame(self)
        self.page_nav.setObjectName("panel")
        self.page_nav.setStyleSheet(self._panel_style())

        layout = QHBoxLayout(self.page_nav)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # 上一页：切换到上一页（首页时无动作）
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setObjectName("nav")
        self.btn_prev.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.clicked.connect(self._prev_page)

        # 页码：以正方形按钮样式显示当前页/总页数，如 1/3
        self.page_label = QLabel("1/1")
        self.page_label.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.page_label.setAlignment(Qt.AlignCenter)

        # 下一页：切换到下一页；末页时自动新建一页并翻过去
        self.btn_next = QPushButton("▶")
        self.btn_next.setObjectName("nav")
        self.btn_next.setFixedSize(BTN_SIZE, BTN_SIZE)
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.clicked.connect(self._next_page)

        layout.addWidget(self.btn_prev)
        layout.addWidget(self.page_label)
        layout.addWidget(self.btn_next)

        self._reposition_page_nav()

    def _build_pen_popup(self):
        """构建画笔设置弹出框：颜色选择 + 画笔粗细。"""
        self.pen_popup = ToolPopup(self)

        # 颜色选择行：每个颜色一个色块按钮
        color_row = QHBoxLayout()
        color_row.setSpacing(6)
        self.color_buttons = []
        for color in BOARD_COLORS:
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, c=color: self._set_color(c)
            )
            self.color_buttons.append(btn)
            color_row.addWidget(btn)
        color_row.addStretch(1)
        self.pen_popup.body.addLayout(color_row)

        # 画笔粗细行：滑块调节 + 数值显示
        self.pen_width_slider = QSlider(Qt.Horizontal)
        self.pen_width_slider.setRange(2, 30)
        self.pen_width_slider.setValue(self.pen_width)
        self.pen_width_slider.setFixedWidth(140)
        self.pen_width_slider.valueChanged.connect(self._set_pen_width)
        self.pen_width_label = QLabel(f"{self.pen_width}px")
        self.pen_popup.body.addLayout(
            self._build_width_row("粗细", self.pen_width_slider, self.pen_width_label)
        )

        self.pen_popup.anchor = self.btn_pen
        self._update_color_ui()

    def _build_eraser_popup(self):
        """构建橡皮设置弹出框：橡皮粗细 + 滑动清空。"""
        self.eraser_popup = ToolPopup(self)

        # 橡皮粗细行：滑块调节 + 数值显示
        self.eraser_width_slider = QSlider(Qt.Horizontal)
        self.eraser_width_slider.setRange(2, 40)
        self.eraser_width_slider.setValue(self.eraser_width)
        self.eraser_width_slider.setFixedWidth(140)
        self.eraser_width_slider.valueChanged.connect(self._set_eraser_width)
        self.eraser_width_label = QLabel(f"{self.eraser_width}px")
        self.eraser_popup.body.addLayout(
            self._build_width_row(
                "粗细", self.eraser_width_slider, self.eraser_width_label
            )
        )

        # 滑动清空：粗红条滑块，滑到底才清空当前页，防止误触
        self.eraser_clear_slider = QSlider(Qt.Horizontal)
        self.eraser_clear_slider.setObjectName("clearSlider")
        self.eraser_clear_slider.setRange(0, 100)
        self.eraser_clear_slider.setValue(0)
        self.eraser_clear_slider.setFixedSize(220, 32)
        self.eraser_clear_slider.valueChanged.connect(self._on_clear_slider_reached_end)
        # 条中间提示文字：鼠标穿透，不影响滑块拖动
        clear_hint = QLabel("滑动以清空", self.eraser_clear_slider)
        clear_hint.setAlignment(Qt.AlignCenter)
        clear_hint.setAttribute(Qt.WA_TransparentForMouseEvents)
        clear_hint.setStyleSheet(
            "color: #C0392B; font-size: 13px; background: transparent;"
        )
        clear_hint.setGeometry(0, 0, 220, 32)
        self.eraser_popup.body.addWidget(self.eraser_clear_slider)

        self.eraser_popup.anchor = self.btn_eraser

    def _build_close_popup(self):
        """构建关闭选项弹出框：退出 / 最小化。"""
        self.close_popup = ToolPopup(self)

        # 退出：清空全部内容并关闭白板（浅红强调色）
        exit_btn = QPushButton("退出")
        exit_btn.setObjectName("danger")
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.clicked.connect(self.close)
        exit_btn.clicked.connect(self.close_popup.close)
        self.close_popup.body.addWidget(exit_btn)

        # 最小化：隐藏窗口但保留画布内容
        min_btn = QPushButton("最小化")
        min_btn.setCursor(Qt.PointingHandCursor)
        min_btn.clicked.connect(self._minimize_window)
        min_btn.clicked.connect(self.close_popup.close)
        self.close_popup.body.addWidget(min_btn)

        self.close_popup.anchor = self.btn_close

    def _build_width_row(self, title, slider, value_label):
        """构建粗细调节行：标题 + 滑块 + 数值。"""
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(QLabel(title))
        row.addWidget(slider)
        row.addWidget(value_label)
        return row

    def _reposition_action_panel(self):
        """将左下角操作面板固定到白板左下角（与边缘留出间距）。"""
        self.action_panel.adjustSize()
        size = self.size()
        self.action_panel.move(
            PANEL_MARGIN, size.height() - self.action_panel.height() - PANEL_MARGIN
        )

    def _reposition_page_nav(self):
        """将右下角页导航面板固定到白板右下角（与边缘留出间距）。"""
        self.page_nav.adjustSize()
        size = self.size()
        self.page_nav.move(
            size.width() - self.page_nav.width() - PANEL_MARGIN,
            size.height() - self.page_nav.height() - PANEL_MARGIN,
        )

    # ---------- 样式 ----------

    def _toolbar_style(self):
        """工具栏样式：半透明白底蓝边圆角，书写工具按钮。"""
        return f"""
        QFrame#toolbar {{
            background: rgba(255, 255, 255, 235);
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
        }}
        QPushButton {{
            background: transparent;
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            color: {TEXT_COLOR_BLACK};
            font-size: 14px;
            padding: 0;
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
        """

    def _panel_style(self):
        """角落面板样式：半透明白底蓝边圆角，正方形按钮。"""
        return f"""
        QFrame#panel {{
            background: rgba(255, 255, 255, 235);
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
        }}
        QPushButton {{
            background: transparent;
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            color: {TEXT_COLOR_BLACK};
            font-size: 14px;
            padding: 0;
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
        QPushButton#nav {{
            font-size: 18px;
        }}
        QLabel {{
            background: transparent;
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            color: {TEXT_COLOR_BLACK};
            font-size: 14px;
        }}
        """

    # ---------- 工具控制 ----------

    def _set_tool(self, tool):
        """切换当前书写工具，并同步使用对应工具的笔触宽度。"""
        self.tool = tool
        self._update_tool_ui()
        self.width = self.pen_width if tool == "pen" else self.eraser_width

    def _update_tool_ui(self):
        """根据当前工具刷新画笔/橡皮按钮的勾选状态。"""
        self.btn_pen.setChecked(self.tool == "pen")
        self.btn_eraser.setChecked(self.tool == "eraser")

    def _on_pen_clicked(self):
        """画笔按钮：第一次点击选中画笔，再次点击向上弹出画笔设置框。"""
        if self.tool != "pen":
            self._set_tool("pen")
            self._close_popups()
        else:
            self._toggle_popup(self.pen_popup, self.btn_pen)

    def _on_eraser_clicked(self):
        """橡皮按钮：第一次点击选中橡皮，再次点击向上弹出橡皮设置框。"""
        if self.tool != "eraser":
            self._set_tool("eraser")
            self._close_popups()
        else:
            self._toggle_popup(self.eraser_popup, self.btn_eraser)

    def _on_close_clicked(self):
        """关闭按钮：向上弹出"退出 / 最小化"两个选项。"""
        self._toggle_popup(self.close_popup, self.btn_close)

    def _toggle_popup(self, popup, anchor):
        """切换弹出框：已显示则收起，否则弹出到锚点按钮上方。"""
        if popup.isVisible():
            popup.close()
            return
        self._close_popups()
        self._show_popup(popup, anchor)

    def _show_popup(self, popup, anchor):
        """将弹出框显示在锚点按钮的正上方（白板内部坐标）。"""
        popup.adjustSize()
        pos = anchor.mapTo(self, QPoint(0, 0))
        x = pos.x() + (anchor.width() - popup.width()) // 2
        y = pos.y() - popup.height() - 10
        popup.move(x, y)
        popup.show()
        popup.raise_()

    def _close_popups(self):
        """关闭所有工具设置弹出框。"""
        for popup in (self.pen_popup, self.eraser_popup, self.close_popup):
            popup.close()

    def _set_color(self, color):
        """切换当前画笔颜色并刷新色块选中样式。"""
        self.color = color
        self._update_color_ui()

    def _update_color_ui(self):
        """刷新画笔设置框中的色块样式：当前选中的色块描边使用自身颜色。"""
        for btn, color in zip(self.color_buttons, BOARD_COLORS):
            border = color if color == self.color else COLOR_WHITE
            btn.setStyleSheet(
                f"QPushButton {{ background: {color}; border: 2px solid {border};"
                f" border-radius: 13px; }}"
            )

    def _set_pen_width(self, value):
        """设置画笔粗细；若当前正在使用画笔则立即生效。"""
        self.pen_width = value
        if self.tool == "pen":
            self.width = value
        self.pen_width_label.setText(f"{value}px")

    def _set_eraser_width(self, value):
        """设置橡皮粗细；若当前正在使用橡皮则立即生效。"""
        self.eraser_width = value
        if self.tool == "eraser":
            self.width = value
        self.eraser_width_label.setText(f"{value}px")

    def _on_clear_slider_reached_end(self, value):
        """滑动清空：滑块滑到底（100）时清空当前页，随后自动复位。"""
        if value >= 100:
            self.clear_canvas()
            self.eraser_popup.close()
            self.eraser_clear_slider.setValue(0)

    # ---------- 时间显示 ----------

    def _update_time(self):
        """刷新左上角日期与时间文本（日期为 年.月.日 点分隔 + 星期）。"""
        now = QDateTime.currentDateTime()
        self.time_label.setText(now.toString("HH:mm:ss"))
        date = now.date()
        self.date_label.setText(
            f"{date.year()}.{date.month()}.{date.day()} {weekday_name(date)}"
        )

    def _toggle_time(self, checked):
        """按勾选状态显示或隐藏左上角时间，按钮点亮表示时间显示中。"""
        self.date_label.setVisible(checked)
        self.time_label.setVisible(checked)

    # ---------- 页管理 ----------

    def _add_page(self):
        """新建一张空白页并切换到新页（最多 99 页）。"""
        if len(self.pages) >= MAX_PAGES:
            self._show_notice(f"已达最大页数 {MAX_PAGES} 页")
            return
        new_canvas = QPixmap(self.size())
        new_canvas.fill(self.background)
        self.pages.append(new_canvas)
        self._switch_page(len(self.pages) - 1)

    def _switch_page(self, index):
        """切换到指定页并刷新界面。"""
        self.current_page_index = index
        self.canvas = self.pages[index]
        self.current_stroke = None
        self._update_page_label()
        self.update()

    def _prev_page(self):
        """切换到上一页（首页时无动作）。"""
        if self.current_page_index > 0:
            self._switch_page(self.current_page_index - 1)

    def _next_page(self):
        """切换到下一页；已是最后一页时自动新建一页并翻过去。"""
        if self.current_page_index < len(self.pages) - 1:
            self._switch_page(self.current_page_index + 1)
        else:
            self._add_page()

    def _update_page_label(self):
        """刷新页码显示，如 1/3。"""
        self.page_label.setText(f"{self.current_page_index + 1}/{len(self.pages)}")

    # ---------- 画布操作 ----------

    def _minimize_window(self):
        """最小化白板：隐藏窗口但保留全部页面内容，之后重新打开内容不丢失。"""
        self.hide()

    def _save_all_pages(self):
        """保存白板为图片：单页直接保存到所选目录，多页在目录下新建文件夹保存。"""
        directory = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not directory:
            return
        timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
        if len(self.pages) == 1:
            # 只有一页：直接在选定目录下保存一张图片
            save_dir = directory
            names = [f"白板_第1页_{timestamp}.png"]
        else:
            # 多页：在选定目录下新建一个带时间戳的文件夹，统一存放
            save_dir = os.path.join(directory, f"白板_{timestamp}")
            os.makedirs(save_dir, exist_ok=True)
            names = [
                f"白板_第{i}页_{timestamp}.png"
                for i in range(1, len(self.pages) + 1)
            ]
        # 统一路径分隔符，避免提示中出现正反斜杠混用（如 C:/app\白板_x）
        save_dir = os.path.normpath(save_dir)
        saved = 0
        for page, name in zip(self.pages, names):
            if page.toImage().save(os.path.join(save_dir, name)):
                saved += 1
        if saved == len(self.pages):
            self._show_notice(f"已保存全部 {saved} 页到：\n{save_dir}")
        else:
            self._show_notice(f"保存完成但部分失败（{saved}/{len(self.pages)} 页）")

    # ---------- 白板内部提示 ----------

    def _show_notice(self, text):
        """
        在白板内部居中弹出提示卡片（替代系统弹窗）。

        参数:
            text: 要展示的提示文字
        """
        if self._notice_overlay is None:
            # 全屏遮罩：半透明深色，覆盖在白板上聚焦提示
            self._notice_overlay = QWidget(self)
            self._notice_overlay.setStyleSheet("background: rgba(0, 0, 0, 60);")
            self._notice_overlay.mousePressEvent = (
                lambda event: self._notice_overlay.hide()
            )

            # 提示卡片：纯白底黑字，与白板一致的蓝边圆角风格
            card = QFrame(self._notice_overlay)
            card.setObjectName("noticeCard")
            card.setStyleSheet(
                f"""
                QFrame#noticeCard {{
                    background: {COLOR_WHITE};
                    border: 1px solid {COLOR_BORDER};
                    border-radius: 12px;
                }}
                QLabel {{
                    color: {TEXT_COLOR_BLACK};
                    background: transparent;
                    font-size: 18px;
                }}
                QPushButton {{
                    background: {COLOR_PRIMARY};
                    color: {COLOR_WHITE};
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    padding: 8px 30px;
                }}
                """
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(32, 26, 32, 20)
            card_layout.setSpacing(18)
            self._notice_label = QLabel()
            self._notice_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(self._notice_label)
            ok_btn = QPushButton("知道了")
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.clicked.connect(self._notice_overlay.hide)
            card_layout.addWidget(ok_btn, 0, Qt.AlignHCenter)
            self._notice_card = card

        # 设置文本、铺满窗口、居中显示卡片
        self._notice_label.setText(text)
        self._notice_overlay.setGeometry(self.rect())
        self._notice_overlay.show()
        self._notice_overlay.raise_()
        self._notice_card.adjustSize()
        self._notice_card.move(
            (self._notice_overlay.width() - self._notice_card.width()) // 2,
            (self._notice_overlay.height() - self._notice_card.height()) // 2,
        )
        self._notice_card.show()
        self._notice_card.raise_()

    # ---------- 关闭 ----------

    def closeEvent(self, event):
        """关闭白板：清空全部内容并重置为单一空白页，再执行基类关闭逻辑。"""
        # 关闭所有工具设置弹出框
        self._close_popups()
        # 清空首页内容，只保留第一页，下次打开从一页开始
        self.pages[0].fill(self.background)
        self.pages = [self.pages[0]]
        self.current_page_index = 0
        self.canvas = self.pages[0]
        self.current_stroke = None
        self._update_page_label()
        self.update()
        super().closeEvent(event)


if __name__ == "__main__":
    # 独立运行入口：直接打开白板
    app = QApplication(sys.argv)
    board = Whiteboard()
    board.show()
    sys.exit(app.exec())
