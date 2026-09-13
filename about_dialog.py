# -*- coding: utf-8 -*-
"""
关于界面
展示应用 Logo、名称、版本、简介与开源信息，支持检查更新，可拖动移动。
本文件自包含运行所需的全部常量与工具函数。
"""

import json
import os

from PySide6.QtCore import QPoint, Qt, QUrl
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

# ============ 文件路径 ============
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
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

# ============ 应用信息 ============
APP_NAME = "WBTool"
APP_STAGE = "Alpha"            # 发布阶段：Alpha / Beta / Release
APP_VERSION = "1.0.0.100"      # 版本号
APP_DESC = "多功能智慧大屏管理系统"
# 开源仓库地址（待补充）：填入后，关于界面自动将其显示为可点击的链接
APP_REPO_URL = ""
# 更新检查接口地址（待配置）：返回 JSON，格式 {"version": "x.y.z", "url": "下载地址", "notes": "更新说明"}
# 留空时，点击“检查更新”会提示尚未配置
UPDATE_URL = ""


def _rounded_pixmap(pixmap, size, radius):
    """将图片等比缩放为 size×size 并裁剪为圆角，返回新 QPixmap。"""
    scaled = pixmap.scaled(
        size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
    rounded = QPixmap(size, size)
    rounded.fill(Qt.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size, size, radius, radius)
    painter.setClipPath(path)
    x = (size - scaled.width()) // 2
    y = (size - scaled.height()) // 2
    painter.drawPixmap(x, y, scaled)
    painter.end()
    return rounded


class AboutDialog(QDialog):
    """关于 WBTool 的对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_offset = QPoint()    # 拖动偏移
        self._manager = None            # 更新请求管理器
        self._reply = None              # 进行中的更新请求
        self._btn_update = None         # “检查更新”按钮

        # 无边框、置顶对话框
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(480, 540)

        self._build_ui()
        self._center()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        """构建关于卡片内容。"""
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

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_banner())
        layout.addWidget(self._build_body(), 1)

    def _build_banner(self):
        """顶部渐变横幅：Logo + 名称 + 简介 + 版本徽标。"""
        banner = QFrame()
        banner.setObjectName("banner")
        banner.setFixedHeight(140)

        h = QHBoxLayout(banner)
        h.setContentsMargins(30, 22, 30, 22)
        h.setSpacing(18)

        # Logo（存在 assets/logo.png 时显示图片，否则显示 W 占位）
        logo = QLabel()
        logo.setFixedSize(72, 72)
        logo.setAlignment(Qt.AlignCenter)
        image = self._load_logo(72)
        if image is not None:
            logo.setPixmap(image)
        else:
            logo.setText("W")
            logo.setStyleSheet(
                "background: rgba(255,255,255,0.95); border-radius: 36px;"
                f"color: {COLOR_PRIMARY}; font-size: 30px; font-weight: bold;"
            )

        # 名称 + 简介
        text_box = QVBoxLayout()
        text_box.setSpacing(5)
        name = QLabel(APP_NAME)
        name.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: bold;")
        desc = QLabel(APP_DESC)
        desc.setStyleSheet("color: rgba(255,255,255,0.92); font-size: 13px;")
        text_box.addWidget(name)
        text_box.addWidget(desc)
        text_box.addStretch(1)

        # 版本徽标
        badge = QLabel(f"{APP_STAGE} {APP_VERSION}")
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            "background: rgba(255,255,255,0.22); color: #FFFFFF;"
            "font-size: 12px; font-weight: bold; border-radius: 13px;"
            "padding: 5px 14px;"
        )

        h.addWidget(logo)
        h.addLayout(text_box)
        h.addStretch(1)
        h.addWidget(badge, 0, Qt.AlignTop)
        return banner

    def _build_body(self):
        """正文：开源说明 + 底部按钮。"""
        body = QFrame()
        body.setObjectName("body")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(30, 26, 30, 24)
        layout.setSpacing(10)

        # 开源说明
        license_title = QLabel("开源协议")
        license_title.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 15px; font-weight: bold;"
        )
        license_text = QLabel(
            "本项目基于 GPL-3.0 许可证开源发布，遵循自由软件精神："
            "可自由使用、复制、修改与分发；"
            "修改后的衍生作品需以相同许可证开源。"
        )
        license_text.setWordWrap(True)
        license_text.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 13px;"
        )

        # 开源仓库链接（地址待补充时显示占位文字）
        if APP_REPO_URL:
            repo = QLabel(
                f'<a href="{APP_REPO_URL}" '
                f'style="color:{COLOR_PRIMARY}; text-decoration:none;">'
                "开源仓库地址 →</a>"
            )
            repo.setOpenExternalLinks(True)
            repo.setCursor(Qt.PointingHandCursor)
        else:
            repo = QLabel("开源仓库地址：待补充")
            repo.setStyleSheet(
                f"color: {COLOR_TEXT_GRAY}; font-size: 13px;"
            )

        layout.addWidget(license_title)
        layout.addWidget(license_text)
        layout.addWidget(repo)
        layout.addStretch(1)

        # 底部按钮：检查更新（主按钮）+ 关闭
        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        self._btn_update = QPushButton("检查更新")
        self._btn_update.setObjectName("primary")
        self._btn_update.setCursor(Qt.PointingHandCursor)
        self._btn_update.clicked.connect(self.check_update)
        btn_close = QPushButton("关闭")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        buttons.addStretch(1)
        buttons.addWidget(self._btn_update)
        buttons.addWidget(btn_close)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        return body

    def _style(self):
        """卡片样式：白底圆角卡片 + 顶部蓝色渐变横幅。"""
        return f"""
        QFrame#card {{
            background: {COLOR_WHITE};
            border-radius: 20px;
        }}
        QFrame#banner {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {COLOR_PRIMARY}, stop:1 #5B93FF);
            border-top-left-radius: 20px;
            border-top-right-radius: 20px;
        }}
        QFrame#body {{
            background: {COLOR_WHITE};
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
        }}
        QPushButton {{
            background: {COLOR_WHITE};
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            color: {COLOR_PRIMARY};
            font-size: 14px;
            padding: 9px 30px;
        }}
        QPushButton:hover {{
            background: {COLOR_LIGHT_BLUE};
        }}
        QPushButton:pressed {{
            background: #D8E6FF;
        }}
        QPushButton#primary {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLOR_PRIMARY}, stop:1 #4C8DFF);
            border: none;
            color: #FFFFFF;
            font-weight: bold;
        }}
        QPushButton#primary:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2F6BFF, stop:1 #6BA5FF);
        }}
        QPushButton#primary:pressed {{
            background: {COLOR_PRIMARY_DARK};
        }}
        """

    # ---------- Logo 加载 ----------

    def _load_logo(self, size):
        """加载 assets/logo.png；文件不存在或读取失败时返回 None。"""
        if not os.path.exists(LOGO_PATH):
            return None
        pixmap = QPixmap(LOGO_PATH)
        if pixmap.isNull():
            return None
        return _rounded_pixmap(pixmap, size, size // 2)

    # ---------- 检查更新 ----------

    def check_update(self):
        """检查更新：请求更新服务器，比对版本号后提示结果。"""
        if not UPDATE_URL:
            QMessageBox.information(
                self, "检查更新",
                "更新服务器地址尚未配置。\n"
                "请在 about_dialog.py 中填写 UPDATE_URL 后重试。",
            )
            return

        self._btn_update.setEnabled(False)
        self._btn_update.setText("检查中…")

        if self._manager is None:
            self._manager = QNetworkAccessManager(self)
        request = QNetworkRequest(QUrl(UPDATE_URL))
        request.setTransferTimeout(8000)
        self._reply = self._manager.get(request)
        self._reply.finished.connect(self._on_update_finished)

    def _on_update_finished(self):
        """更新请求结束：解析结果并弹窗提示。"""
        reply = self._reply
        self._reply = None
        self._btn_update.setEnabled(True)
        self._btn_update.setText("检查更新")

        if reply is None:
            return
        if reply.error() != QNetworkReply.NetworkError.NoError:
            QMessageBox.warning(
                self, "检查更新",
                "检查更新失败：无法连接更新服务器，请检查网络后重试。",
            )
            reply.deleteLater()
            return

        try:
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
        except Exception:
            data = {}
        reply.deleteLater()

        latest = str(data.get("version", "")).strip()
        if not latest:
            QMessageBox.information(
                self, "检查更新",
                "更新服务器返回的数据异常，请稍后重试。",
            )
            return

        if self._compare_version(latest, APP_VERSION) > 0:
            message = f"发现新版本：{APP_STAGE} {latest}"
            notes = str(data.get("notes") or "").strip()
            if notes:
                message += f"\n\n更新说明：\n{notes}"
            ret = QMessageBox.question(
                self, "检查更新", message + "\n\n是否前往下载？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes,
            )
            if ret == QMessageBox.Yes:
                url = str(data.get("url") or "").strip()
                if url:
                    QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.information(
                self, "检查更新",
                f"当前已是最新版本（{APP_STAGE} {APP_VERSION}）。",
            )

    @staticmethod
    def _compare_version(a, b):
        """比较两个版本号，返回 a>b:1、a<b:-1、相等:0。"""
        def parts(v):
            return [int(p) for p in str(v).split(".") if p.isdigit()]
        pa, pb = parts(a), parts(b)
        for x, y in zip(pa, pb):
            if x != y:
                return 1 if x > y else -1
        return 0

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

    def closeEvent(self, event):
        """关闭时中止未完成的更新请求，避免回调访问已销毁控件。"""
        reply = self._reply
        if reply is not None and reply.isRunning():
            try:
                reply.finished.disconnect(self._on_update_finished)
            except RuntimeError:
                pass
            reply.abort()
        super().closeEvent(event)
