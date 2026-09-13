# -*- coding: utf-8 -*-
"""
课程表组件
显示在屏幕左上角的横向条，通过 JSON 读取工具加载 config/schedule.json，
展示当天课程并高亮当前正在进行的课程。
"""

from PySide6.QtCore import QDate, QTime, QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from utils import common
from utils import json_loader


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
        self._timer.setInterval(common.SCHEDULE_REFRESH_MS)
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
            background: {common.COLOR_WHITE};
            border: 1px solid {common.COLOR_BORDER};
            border-radius: 10px;
        }}
        QLabel#title {{
            background: {common.COLOR_PRIMARY};
            color: {common.COLOR_WHITE};
            font-size: 13px;
            font-weight: bold;
            padding: 0 16px;
            border-top-left-radius: 10px;
            border-bottom-left-radius: 10px;
        }}
        QLabel#course {{
            color: {common.COLOR_TEXT_DARK};
            font-size: 13px;
            padding: 0 2px;
        }}
        QLabel#course_current {{
            background: {common.COLOR_LIGHT_BLUE};
            color: {common.COLOR_PRIMARY};
            font-size: 13px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 6px;
        }}
        """

    # ---------- 数据刷新 ----------

    def _refresh(self):
        """重新读取 JSON 并重建课程标签。"""
        self.data = json_loader.load_json(common.SCHEDULE_JSON_PATH, {})
        today = common.weekday_name(QDate.currentDate())
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
                f"color: {common.COLOR_TEXT_GRAY}; font-size: 13px; padding: 0 4px;"
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
        screen = common.available_screen_geometry(self)
        self.move(screen.left() + 10, screen.top() + 10)
