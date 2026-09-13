# -*- coding: utf-8 -*-
"""
信息面板组件
显示在屏幕右上角，通过 JSON 读取工具加载 config/info.json 展示信息条目，
支持 {date} {weekday} {time} 动态占位符。
本文件自包含运行所需的全部常量与工具函数。
"""

import json
import os

from PySide6.QtCore import QDateTime, QTimer, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

# ============ 文件路径 ============
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
INFO_JSON_PATH = os.path.join(PROJECT_ROOT, "config", "info.json")

# ============ 蓝白配色 ============
COLOR_PRIMARY = "#2F6BFF"        # 主蓝色
COLOR_BORDER = "#C9DAFF"         # 浅蓝边框
COLOR_TEXT_DARK = "#22304A"      # 主文字深色
COLOR_TEXT_GRAY = "#7A8699"      # 次要文字灰色

# ============ 信息面板 ============
INFO_WIDTH = 230                 # 信息面板宽度
INFO_REFRESH_MS = 30 * 1000      # 信息面板刷新间隔（毫秒）


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


class InfoPanel(QWidget):
    """右上角信息卡片。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}  # 信息数据（来自 info.json）

        # 窗口属性：无边框、置顶、工具窗
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(INFO_WIDTH)

        self._build_ui()
        self._move_to_corner()

        # 定时刷新：信息内容与动态时间
        self._timer = QTimer(self)
        self._timer.setInterval(INFO_REFRESH_MS)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()
        self._refresh()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        """构建卡片：标题 + 分隔线 + 信息条目。"""
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet(self._style())

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # 标题
        self.title_label = QLabel()
        self.title_label.setObjectName("title")
        layout.addWidget(self.title_label)

        # 分隔线
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {COLOR_BORDER}; border: none;")
        layout.addWidget(line)

        # 信息条目区
        self.items_box = QWidget()
        self.items_layout = QVBoxLayout(self.items_box)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(9)
        layout.addWidget(self.items_box)
        layout.addStretch(1)

        # 外层布局容纳容器
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.container)

    def _style(self):
        """卡片样式：半透明白底蓝边圆角。"""
        return f"""
        QFrame#container {{
            background: rgba(255, 255, 255, 242);
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
        }}
        QLabel#title {{
            color: {COLOR_PRIMARY};
            font-size: 15px;
            font-weight: bold;
        }}
        """

    # ---------- 数据刷新 ----------

    def _refresh(self):
        """重新读取 JSON 并重建信息条目。"""
        self.data = load_json(INFO_JSON_PATH, {})
        self.title_label.setText(self.data.get("title", "信息面板"))

        # 清空条目区
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        now = QDateTime.currentDateTime()
        for item in self.data.get("items", []):
            label = item.get("label", "")
            value = self._resolve_value(item.get("value", ""), now)
            self.items_layout.addWidget(self._make_row(label, value))

        # 按内容调整大小并重新定位
        self.adjustSize()
        self._move_to_corner()

    def _resolve_value(self, value, now):
        """解析动态占位符为实际内容。"""
        value = value.replace("{date}", now.toString("yyyy-MM-dd"))
        value = value.replace("{weekday}", weekday_name(now.date()))
        value = value.replace("{time}", now.toString("HH:mm"))
        return value

    def _make_row(self, label, value):
        """构建一行“label : value”。"""
        row = QFrame()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)

        label_w = QLabel(label)
        label_w.setStyleSheet(
            f"color: {COLOR_TEXT_GRAY}; font-size: 13px;"
        )

        value_w = QLabel(value)
        value_w.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 13px; font-weight: bold;"
        )
        value_w.setWordWrap(True)
        value_w.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        h.addWidget(label_w)
        h.addStretch(1)
        h.addWidget(value_w, 0, Qt.AlignRight)

        return row

    # ---------- 定位 ----------

    def _move_to_corner(self):
        """定位到屏幕右上角。"""
        screen = available_screen_geometry(self)
        self.move(screen.right() - self.width() - 10, screen.top() + 10)
