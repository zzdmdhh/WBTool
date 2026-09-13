# -*- coding: utf-8 -*-
"""
白板组件
自包含实现全部白板功能，可独立运行（python whiteboard.py），
也可由悬浮球菜单的"白板"按钮打开。

包含：
- BOARD_COLORS：画笔颜色色板（白板与屏幕批注共用）
- StrokeCanvas：可书写/擦除的离屏渲染画布基类（白板与屏幕批注共用）
- Whiteboard：全屏白色画布窗口，支持多页书写、翻页、批量保存
"""

import os
import sys

from PySide6.QtCore import (
    QDateTime,
    QPointF,
    QPropertyAnimation,
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
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# ============ 画笔色板 ============
# 白板与屏幕批注共用的画笔颜色列表（黑、红、蓝）
BOARD_COLORS = ["#1F2937", "#E53935", "#2F6BFF"]

# 蓝白配色
COLOR_PRIMARY = "#2F6BFF"        # 主蓝色
COLOR_LIGHT_BLUE = "#EAF1FF"     # 浅蓝背景（悬停/选中底）
COLOR_BORDER = "#C9DAFF"         # 浅蓝边框
COLOR_WHITE = "#FFFFFF"          # 白色

# 白板内文字统一使用的纯黑颜色
TEXT_COLOR_BLACK = "#000000"

# 画笔与橡皮的固定笔触宽度：橡皮比画笔更粗
PEN_WIDTH = 4
ERASER_WIDTH = 20


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
        self.current_stroke = None    # 当前正在绘制的笔画数据（工具/颜色/宽度/采样点）
        self.tool = "pen"             # 当前工具：pen（画笔）/ eraser（橡皮）
        self.color = BOARD_COLORS[0]  # 当前画笔颜色
        self.width = 4                # 当前笔画粗细

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
            for p in points[1:]:
                path.lineTo(QPointF(p))
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


class Whiteboard(StrokeCanvas):
    """全屏白色画布窗口：左上角时间显示，底部为控制工具栏，支持多页。"""

    def __init__(self, parent=None):
        # 以不透明白色为背景创建画布
        super().__init__(background=COLOR_WHITE, parent=parent)
        self.setCursor(Qt.CrossCursor)  # 十字光标，便于精准书写
        # 全屏显示（覆盖整个屏幕，包括任务栏区域）
        self.setGeometry(QGuiApplication.primaryScreen().geometry())

        # 多页数据：pages 保存每一页的离屏画布，canvas 始终指向当前页
        self.pages = [self.canvas]
        self.current_page_index = 0

        self._build_ui()

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
        # 同步右下角页导航的位置
        if hasattr(self, "page_nav"):
            self._reposition_page_nav()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        """构建整体布局：左上角时间显示区与底部控制工具栏。"""
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)

        # 左上角时间显示：日期在上、时间在下，均左对齐
        self.date_label = QLabel()
        self.date_label.setStyleSheet(
            f"color: {TEXT_COLOR_BLACK}; font-size: 28px; font-weight: bold;"
        )
        self.time_label = QLabel()
        self.time_label.setStyleSheet(
            f"color: {TEXT_COLOR_BLACK}; font-size: 56px; font-weight: bold;"
        )
        time_box = QVBoxLayout()
        time_box.setSpacing(2)
        time_box.addWidget(self.date_label, 0, Qt.AlignLeft)
        time_box.addWidget(self.time_label, 0, Qt.AlignLeft)

        top_row = QHBoxLayout()
        top_row.addLayout(time_box)
        top_row.addStretch(1)
        root.addLayout(top_row)
        root.addStretch(1)

        # 底部控制工具栏
        self.toolbar = self._build_toolbar()
        root.addWidget(self.toolbar, 0, Qt.AlignHCenter)

        # 右下角独立页导航面板（上一页 / 页码 / 下一页）
        self._build_page_nav()

        # 时间刷新定时器：每秒更新一次日期与时间文本
        self._time_timer = QTimer(self)
        self._time_timer.setInterval(1000)
        self._time_timer.timeout.connect(self._update_time)
        self._time_timer.start()
        self._update_time()

    def _build_toolbar(self):
        """
        构建底部控制工具栏，分两个区域：
        - 左区：保存、清空、最小化、时间开关、关闭
        - 中区：画笔、颜色区、橡皮（书写工具）
        """
        bar = QFrame()
        bar.setObjectName("toolbar")
        bar.setStyleSheet(self._toolbar_style())

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(8)

        # ---------- 左区：系统操作 ----------
        # 保存：批量导出全部页面为图片
        self.btn_save = QPushButton("保存")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self._save_canvas)

        # 清空：浅红色样式，清空当前页的全部内容
        self.btn_clear = QPushButton("清空")
        self.btn_clear.setObjectName("clear")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_canvas)

        # 最小化：隐藏窗口但保留画布内容，之后重新打开内容不丢失
        self.btn_minimize = QPushButton("最小化")
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        self.btn_minimize.clicked.connect(self._minimize)

        # 时间显示开关：勾选时显示时间，取消勾选时隐藏时间
        self.btn_time = QPushButton("隐藏时间")
        self.btn_time.setCheckable(True)
        self.btn_time.setChecked(True)
        self.btn_time.setCursor(Qt.PointingHandCursor)
        self.btn_time.clicked.connect(self._toggle_time)

        # 关闭：清空全部内容并退出白板
        self.btn_close = QPushButton("关闭")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close)

        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_clear)
        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_time)
        layout.addWidget(self.btn_close)
        layout.addWidget(self._divider())

        # ---------- 中区：书写工具 ----------
        # 工具切换：画笔 / 橡皮（互斥，可勾选显示当前工具）
        self.btn_pen = QPushButton("画笔")
        self.btn_pen.setCheckable(True)
        self.btn_pen.setCursor(Qt.PointingHandCursor)
        self.btn_pen.clicked.connect(lambda: self._set_tool("pen"))

        self.btn_eraser = QPushButton("橡皮")
        self.btn_eraser.setCheckable(True)
        self.btn_eraser.setCursor(Qt.PointingHandCursor)
        self.btn_eraser.clicked.connect(lambda: self._set_tool("eraser"))

        # 颜色区：独立容器包裹色块按钮，便于整体做展开动画
        self.color_panel = QWidget()
        color_layout = QHBoxLayout(self.color_panel)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(6)
        self.color_buttons = []
        for color in BOARD_COLORS:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, c=color: self._set_color(c)
            )
            self.color_buttons.append(btn)
            color_layout.addWidget(btn)
        # 颜色区展开动画：容器宽度从 0 平滑展开到内容宽度
        self._color_anim = QPropertyAnimation(self.color_panel, b"maximumWidth", self)
        self._color_anim.setDuration(180)

        layout.addWidget(self.btn_pen)
        layout.addWidget(self.color_panel)
        layout.addWidget(self.btn_eraser)

        # 按当前状态刷新工具按钮选中样式
        self._update_tool_ui()
        return bar

    def _build_page_nav(self):
        """构建右下角独立的页导航面板：上一页 / 页码 / 下一页。"""
        self.page_nav = QFrame(self)
        self.page_nav.setObjectName("pageNav")
        self.page_nav.setStyleSheet(self._page_nav_style())

        nav_layout = QHBoxLayout(self.page_nav)
        nav_layout.setContentsMargins(12, 8, 12, 8)
        nav_layout.setSpacing(8)

        # 上一页：切换到上一页（首页时无动作）
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedSize(44, 44)
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.clicked.connect(self._prev_page)

        # 页码：以正方形按钮样式显示当前页/总页数，如 1/3
        self.page_label = QLabel("1/1")
        self.page_label.setFixedSize(44, 44)
        self.page_label.setAlignment(Qt.AlignCenter)

        # 下一页：切换到下一页；末页时自动新建一页并翻过去
        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedSize(44, 44)
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.clicked.connect(self._next_page)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.page_label)
        nav_layout.addWidget(self.btn_next)

        self._reposition_page_nav()

    def _reposition_page_nav(self):
        """将页导航面板固定到白板右下角（与边缘留出间距）。"""
        self.page_nav.adjustSize()
        size = self.size()
        self.page_nav.move(
            size.width() - self.page_nav.width() - 36,
            size.height() - self.page_nav.height() - 36,
        )

    def _page_nav_style(self):
        """页导航面板样式：半透明白底蓝边圆角，正方形大按钮。"""
        return f"""
        QFrame#pageNav {{
            background: rgba(255, 255, 255, 235);
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
        }}
        QPushButton {{
            background: transparent;
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            color: {TEXT_COLOR_BLACK};
            font-size: 18px;
            padding: 0;
        }}
        QPushButton:hover {{
            background: {COLOR_LIGHT_BLUE};
            color: {COLOR_PRIMARY};
        }}
        QLabel {{
            background: transparent;
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            color: {TEXT_COLOR_BLACK};
            font-size: 14px;
        }}
        """

    def _divider(self):
        """创建工具栏中使用的竖直分隔线。"""
        line = QFrame()
        line.setObjectName("divider")
        line.setFixedWidth(1)
        return line

    def _toolbar_style(self):
        """工具栏样式：半透明白底蓝边圆角，清空按钮使用浅红色。"""
        return f"""
        QFrame#toolbar {{
            background: rgba(255, 255, 255, 235);
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
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
            color: {TEXT_COLOR_BLACK};
            font-size: 13px;
            padding: 6px 14px;
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
        QPushButton#clear {{
            background: #FDECEC;
            border: 1px solid #F0B8B8;
            color: #C0392B;
        }}
        QPushButton#clear:hover {{
            background: #F8D7DA;
            color: #A93226;
        }}
        """

    # ---------- 工具控制 ----------

    def _set_tool(self, tool):
        """
        切换当前书写工具：
        - 画笔：展开颜色区（宽度展开动画），使用细笔触
        - 橡皮：收起颜色区，使用固定粗笔触
        """
        self.tool = tool
        self._update_tool_ui()
        if tool == "pen":
            self._show_color_panel()
        else:
            self._hide_color_panel()
        # 橡皮固定比画笔更粗
        self.width = ERASER_WIDTH if tool == "eraser" else PEN_WIDTH

    def _update_tool_ui(self):
        """根据当前工具刷新画笔/橡皮按钮的勾选状态。"""
        self.btn_pen.setChecked(self.tool == "pen")
        self.btn_eraser.setChecked(self.tool == "eraser")

    def _show_color_panel(self):
        """以宽度展开动画弹出颜色区。"""
        self.color_panel.show()
        self._color_anim.stop()
        self._color_anim.setStartValue(0)
        self._color_anim.setEndValue(self.color_panel.sizeHint().width())
        self._color_anim.start()

    def _hide_color_panel(self):
        """隐藏颜色区。"""
        self._color_anim.stop()
        self.color_panel.hide()

    def _set_color(self, color):
        """切换当前画笔颜色并刷新色块选中样式。"""
        self.color = color
        self._update_color_ui()

    def _update_color_ui(self):
        """刷新颜色按钮样式：当前选中的色块加蓝色描边。"""
        for btn, color in zip(self.color_buttons, BOARD_COLORS):
            border = (
                COLOR_PRIMARY if color == self.color else COLOR_WHITE
            )
            btn.setStyleSheet(
                f"QPushButton {{ background: {color}; border: 2px solid {border};"
                f" border-radius: 11px; }}"
            )

    # ---------- 时间显示 ----------

    def _update_time(self):
        """刷新左上角日期与时间文本。"""
        now = QDateTime.currentDateTime()
        self.time_label.setText(now.toString("HH:mm:ss"))
        self.date_label.setText(
            f"{now.toString('yyyy年MM月dd日')} {weekday_name(now.date())}"
        )

    def _toggle_time(self, checked):
        """按勾选状态显示或隐藏左上角时间，并同步按钮文字。"""
        self.date_label.setVisible(checked)
        self.time_label.setVisible(checked)
        self.btn_time.setText("隐藏时间" if checked else "显示时间")

    # ---------- 页管理 ----------

    def _add_page(self):
        """新建一张空白页并切换到新页。"""
        new_canvas = QPixmap(self.size())
        new_canvas.fill(self.background)
        self.pages.append(new_canvas)
        self.current_page_index = len(self.pages) - 1
        self.canvas = new_canvas
        self.current_stroke = None
        self._update_page_label()
        self.update()

    def _prev_page(self):
        """切换到上一页（首页时无动作）。"""
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self.canvas = self.pages[self.current_page_index]
            self.current_stroke = None
            self._update_page_label()
            self.update()

    def _next_page(self):
        """切换到下一页；已是最后一页时自动添加一张新页并翻过去。"""
        if self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
            self.canvas = self.pages[self.current_page_index]
            self.current_stroke = None
            self._update_page_label()
            self.update()
        else:
            # 已在最后一页：自动新建一页并翻到新页
            self._add_page()

    def _update_page_label(self):
        """刷新页码显示，如 1/3。"""
        self.page_label.setText(f"{self.current_page_index + 1}/{len(self.pages)}")

    # ---------- 画布操作 ----------

    def _minimize(self):
        """最小化白板：隐藏窗口但保留全部页面内容，之后重新打开内容不丢失。"""
        self.hide()

    def _save_canvas(self):
        """批量保存全部页面为图片文件（每页一张 PNG）。"""
        directory = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not directory:
            return
        timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
        saved = 0
        for i, page in enumerate(self.pages, start=1):
            path = os.path.join(directory, f"白板_第{i}页_{timestamp}.png")
            if page.toImage().save(path):
                saved += 1
        if saved == len(self.pages):
            QMessageBox.information(
                self, "保存白板", f"已保存全部 {saved} 页到：\n{directory}"
            )
        else:
            QMessageBox.warning(
                self, "保存白板",
                f"保存完成但部分失败（{saved}/{len(self.pages)} 页）。",
            )

    # ---------- 关闭 ----------

    def closeEvent(self, event):
        """关闭白板：清空全部页面内容后再关闭。"""
        for page in self.pages:
            page.fill(self.background)
        self.current_stroke = None
        self.update()
        super().closeEvent(event)


if __name__ == "__main__":
    # 独立运行入口：直接打开白板
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    board = Whiteboard()
    board.show()
    sys.exit(app.exec())
