# -*- coding: utf-8 -*-
"""
设置对话框
设置模块的总入口：左侧分类导航 + 右侧页面堆栈，底部提供保存/恢复默认/关闭。
包含系统设置、白板、屏幕批注、课程表、信息面板、关于 六个设置页面。
无边框、可拖动、模态显示，由悬浮球的长按或功能条“设置”按钮打开。
"""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
)

from app.code.settings.about_page import AboutPage
from app.code.settings.common import (
    COLOR_BORDER,
    COLOR_LIGHT_BLUE,
    COLOR_PRIMARY,
    COLOR_TEXT_DARK,
    COLOR_WHITE,
)
from app.code.settings.info_page import InfoPage
from app.code.settings.markup_page import MarkupPage
from app.code.settings.schedule_page import SchedulePage
from app.code.settings.settings_manager import SettingsManager
from app.code.settings.system_page import SystemPage
from app.code.settings.whiteboard_page import WhiteboardPage

# ============ 尺寸 ============
DIALOG_WIDTH = 780               # 对话框宽度
DIALOG_HEIGHT = 540              # 对话框高度
SIDEBAR_WIDTH = 168              # 左侧导航宽度
NAV_BUTTON_HEIGHT = 44           # 导航按钮高度

# 页面定义：(导航标题, 设置段名, 页面类)；段名为 None 的页面不参与设置读写
PAGE_DEFINITIONS = [
    ("系统设置", "system", SystemPage),
    ("白板", "whiteboard", WhiteboardPage),
    ("屏幕批注", "markup", MarkupPage),
    ("课程表", "schedule", SchedulePage),
    ("信息面板", "info", InfoPage),
    ("关于", None, AboutPage),
]


class SettingsDialog(QDialog):
    """设置对话框：左侧导航 + 右侧页面堆栈。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = SettingsManager()
        self._drag_offset = QPoint()   # 拖动偏移

        # 无边框、置顶对话框
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(DIALOG_WIDTH, DIALOG_HEIGHT)

        self._pages = []        # 与 PAGE_DEFINITIONS 顺序一致的页面实例
        self._nav_buttons = []  # 导航按钮列表

        self._build_ui()
        self._select_page(0)
        self._center()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        """构建卡片外壳：左侧导航 + 右侧页面 + 底部操作条。"""
        card = QFrame(self)
        card.setObjectName("card")
        card.setStyleSheet(self._style())
        card.setGeometry(10, 10, self.width() - 20, self.height() - 20)

        # 卡片投影，提升层次感
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(20, 40, 90, 70))
        card.setGraphicsEffect(shadow)

        root = QVBoxLayout(card)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        content.addWidget(self._build_sidebar())
        content.addWidget(self._build_pages(), 1)
        root.addLayout(content, 1)
        root.addWidget(self._build_footer())

    def _build_sidebar(self):
        """左侧导航栏：标题 + 分类按钮列表。"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 22, 12, 16)
        layout.setSpacing(6)

        title = QLabel("设置")
        title.setStyleSheet(
            f"color: {COLOR_PRIMARY}; font-size: 18px; font-weight: bold;"
        )
        layout.addWidget(title)
        layout.addSpacing(10)

        group = QButtonGroup(self)
        group.setExclusive(True)
        for index, (name, section, page_cls) in enumerate(PAGE_DEFINITIONS):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedHeight(NAV_BUTTON_HEIGHT)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, i=index: self._select_page(i)
            )
            group.addButton(btn)
            layout.addWidget(btn)
            self._nav_buttons.append(btn)
        layout.addStretch(1)
        return sidebar

    def _build_pages(self):
        """右侧页面堆栈：按定义实例化各设置页面并载入当前设置。"""
        self.stack = QStackedWidget()
        for name, section, page_cls in PAGE_DEFINITIONS:
            page = page_cls()
            if section is not None:
                page.load_values(self.manager.get(section))
            self._pages.append(page)
            self.stack.addWidget(page)
        return self.stack

    def _build_footer(self):
        """底部操作条：恢复默认 / 保存设置 / 关闭。"""
        footer = QFrame()
        footer.setObjectName("footer")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(10)

        self.btn_reset = QPushButton("恢复默认")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self._on_reset)

        layout.addStretch(1)
        layout.addWidget(self.btn_reset)

        self.btn_save = QPushButton("保存设置")
        self.btn_save.setObjectName("primary")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self._on_save)
        layout.addWidget(self.btn_save)

        btn_close = QPushButton("关闭")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        return footer

    # ---------- 页面切换 ----------

    def _select_page(self, index):
        """切换到指定页面并高亮对应导航按钮。"""
        self.stack.setCurrentIndex(index)
        self._nav_buttons[index].setChecked(True)

    # ---------- 保存 / 恢复 ----------

    def _on_save(self):
        """收集所有页面的值写入设置文件，并执行需要立即生效的操作。"""
        try:
            for (name, section, page_cls), page in zip(
                PAGE_DEFINITIONS, self._pages
            ):
                if section is not None:
                    self.manager.update_section(section, page.values())
            # 执行页面附加操作（如开机自启动注册表写入）
            for page in self._pages:
                apply_method = getattr(page, "apply", None)
                if callable(apply_method):
                    ok, error = apply_method()
                    if not ok:
                        QMessageBox.warning(
                            self, "保存设置",
                            f"部分设置未能生效：{error}",
                        )
        except OSError as exc:
            QMessageBox.warning(self, "保存设置", f"保存失败：{exc}")
            return
        QMessageBox.information(self, "保存设置", "设置已保存。")

    def _on_reset(self):
        """将当前页面恢复为默认值。"""
        index = self.stack.currentIndex()
        name, section, page_cls = PAGE_DEFINITIONS[index]
        if section is None:
            return
        ret = QMessageBox.question(
            self, "恢复默认", f"确定将「{name}」恢复为默认设置吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if ret != QMessageBox.Yes:
            return
        self.manager.reset_section(section)
        self._pages[index].load_values(self.manager.get(section))

    # ---------- 样式 ----------

    def _style(self):
        """整体样式：白底圆角卡片 + 浅蓝侧边栏。"""
        return f"""
        QFrame#card {{
            background: {COLOR_WHITE};
            border-radius: 16px;
        }}
        QFrame#sidebar {{
            background: {COLOR_LIGHT_BLUE};
            border-top-left-radius: 16px;
            border-bottom-left-radius: 16px;
        }}
        QPushButton {{
            background: transparent;
            border: none;
            border-radius: 8px;
            color: {COLOR_TEXT_DARK};
            font-size: 14px;
            text-align: left;
            padding-left: 14px;
        }}
        QPushButton:hover {{
            background: rgba(47, 107, 255, 0.12);
            color: {COLOR_PRIMARY};
        }}
        QPushButton:checked {{
            background: {COLOR_PRIMARY};
            color: {COLOR_WHITE};
            font-weight: bold;
        }}
        QFrame#footer {{
            background: #F7F9FE;
            border-top: 1px solid {COLOR_BORDER};
            border-bottom-left-radius: 16px;
            border-bottom-right-radius: 16px;
        }}
        QFrame#footer QPushButton {{
            background: {COLOR_WHITE};
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            color: {COLOR_PRIMARY};
            font-size: 14px;
            padding: 8px 22px;
            text-align: center;
        }}
        QFrame#footer QPushButton:hover {{
            background: {COLOR_LIGHT_BLUE};
        }}
        QFrame#footer QPushButton#primary {{
            background: {COLOR_PRIMARY};
            border: none;
            color: {COLOR_WHITE};
            font-weight: bold;
        }}
        QFrame#footer QPushButton#primary:hover {{
            background: #4C8DFF;
        }}
        QFrame#footer QPushButton#primary:pressed {{
            background: #1E50CC;
        }}
        """

    # ---------- 定位与拖动 ----------

    def _center(self):
        """将窗口居中显示。"""
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.center() - self.rect().center())

    def mousePressEvent(self, event):
        """按下：记录拖动偏移。"""
        if event.button() == Qt.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """移动：拖动窗口。"""
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)
