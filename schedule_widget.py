# -*- coding: utf-8 -*-
"""
课程表组件
显示在屏幕左上角的横向条，通过 JSON 读取工具加载 config/schedule.json，
展示当天课程并高亮当前正在进行的课程。
本文件自包含运行所需的全部常量与工具函数。
"""

import json
import os

from PySide6.QtCore import QDate, QTime, QTimer, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

# ============ 文件路径 ============
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCHEDULE_JSON_PATH = os.path.join(PROJECT_ROOT, "config", "schedule.json")

# ============ 蓝白配色 ============
COLOR_PRIMARY = "#2F6BFF"        # 主蓝色
COLOR_LIGHT_BLUE = "#EAF1FF"     # 浅蓝背景（悬停/选中底）
COLOR_BORDER = "#C9DAFF"         # 浅蓝边框
COLOR_WHITE = "#FFFFFF"          # 白色
COLOR_TEXT_DARK = "#22304A"      # 主文字深色
COLOR_TEXT_GRAY = "#7A8699"      # 次要文字灰色

# ============ 课程表 ============
SCHEDULE_REFRESH_MS = 30 * 1000  # 课程表刷新间隔（毫秒）


def load_json(file_path, default=None):
    """
    读取 JSON 文件。

    参数:
        file_path: JSON 文件路径
        default: 读取失败时返回的默认值（默认空字典）

    返回:
        解析后的字典/列表；读取失败或文件不存在时返回 default
    """
    if default is None:
        default = {}
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # 文件内容不是合法 JSON 时返回默认值
        return default


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


class ScheduleWidget(QWidget):
    """左上角课程表横条。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}  # 课程表数据（来自 schedule.json）

        # 窗口属性：无边框、置顶、工具窗
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._build_ui()
        self._move_to_corner()

        # 定时刷新：课程内容与当前课程状态
        self._timer = QTimer(self)
        self._timer.setInterval(SCHEDULE_REFRESH_MS)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()
        self._refresh()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        """构建容器：标题 + 课程标签区。"""
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet(self._style())

        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 左侧标题（蓝底胶囊）
        self.title_label = QLabel()
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignCenter)

        # 右侧课程区
        self.courses_box = QWidget()
        self.courses_layout = QHBoxLayout(self.courses_box)
        self.courses_layout.setContentsMargins(14, 0, 14, 0)
        self.courses_layout.setSpacing(10)

        layout.addWidget(self.title_label)
        layout.addWidget(self.courses_box, 1)

        # 外层布局容纳容器
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.container)

    def _style(self):
        """横条样式：白底蓝边圆角，标题蓝底白字。"""
        return f"""
        QFrame#container {{
            background: {COLOR_WHITE};
            border: 1px solid {COLOR_BORDER};
            border-radius: 10px;
        }}
        QLabel#title {{
            background: {COLOR_PRIMARY};
            color: {COLOR_WHITE};
            font-size: 13px;
            font-weight: bold;
            padding: 0 16px;
            border-top-left-radius: 10px;
            border-bottom-left-radius: 10px;
        }}
        QLabel#course {{
            color: {COLOR_TEXT_DARK};
            font-size: 13px;
            padding: 0 2px;
        }}
        QLabel#course_current {{
            background: {COLOR_LIGHT_BLUE};
            color: {COLOR_PRIMARY};
            font-size: 13px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 6px;
        }}
        """

    # ---------- 数据刷新 ----------

    def _refresh(self):
        """重新读取 JSON 并重建课程标签。"""
        self.data = load_json(SCHEDULE_JSON_PATH, {})
        today = weekday_name(QDate.currentDate())
        courses = [
            c for c in self.data.get("courses", [])
            if c.get("weekday") == today
        ]

        # 标题：课程表名称 + 今天星期
        title = self.data.get("title", "课程表")
        self.title_label.setText(f"{title} · {today}")

        # 清空课程区
        while self.courses_layout.count():
            item = self.courses_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not courses:
            # 今天没有课程时显示提示
            empty = QLabel("今天暂无课程")
            empty.setStyleSheet(
                f"color: {COLOR_TEXT_GRAY}; font-size: 13px; padding: 0 4px;"
            )
            self.courses_layout.addWidget(empty)
        else:
            now = QTime.currentTime()
            for course in courses:
                is_current = self._is_current(course, now)
                label = QLabel(self._course_text(course))
                label.setObjectName("course_current" if is_current else "course")
                self.courses_layout.addWidget(label)

        # 按内容调整窗口大小并重新定位
        self.adjustSize()
        self._move_to_corner()

    def _course_text(self, course):
        """拼接单节课的显示文本。"""
        name = course.get("name", "")
        start = course.get("start", "")
        end = course.get("end", "")
        room = course.get("room", "")
        text = f"{name} {start}-{end}"
        if room:
            text += f" {room}"
        return text

    def _is_current(self, course, now):
        """判断某节课是否为当前正在进行的课程。"""
        start = QTime.fromString(course.get("start", ""), "HH:mm")
        end = QTime.fromString(course.get("end", ""), "HH:mm")
        return start.isValid() and end.isValid() and start <= now < end

    # ---------- 定位 ----------

    def _move_to_corner(self):
        """定位到屏幕左上角。"""
        screen = available_screen_geometry(self)
        self.move(screen.left() + 10, screen.top() + 10)
