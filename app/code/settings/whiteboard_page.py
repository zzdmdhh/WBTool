# -*- coding: utf-8 -*-
"""
白板设置页面
配置白板的默认画笔颜色/粗细、默认橡皮粗细、最大页数与是否默认显示时间。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.code.settings.common import (
    COLOR_PALETTE,
    COLOR_TEXT_DARK,
    COLOR_TEXT_GRAY,
    ColorPicker,
    make_form_row,
)


class WhiteboardPage(QWidget):
    """白板设置页面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ---------- UI 构建 ----------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 20)
        layout.setSpacing(16)

        title = QLabel("白板设置")
        title.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 17px; font-weight: bold;"
        )
        layout.addWidget(title)
        layout.addSpacing(4)

        # 默认画笔颜色
        self.color_picker = ColorPicker(COLOR_PALETTE)
        layout.addLayout(make_form_row("默认画笔颜色", self.color_picker))

        # 默认画笔粗细：滑块 + 数值
        self.pen_width_slider = QSlider(Qt.Horizontal)
        self.pen_width_slider.setRange(2, 30)
        self.pen_width_slider.setFixedWidth(200)
        self.pen_width_label = QLabel()
        self.pen_width_label.setStyleSheet(
            f"color: {COLOR_TEXT_GRAY}; font-size: 13px;"
        )
        self.pen_width_slider.valueChanged.connect(
            lambda v: self.pen_width_label.setText(f"{v}px")
        )
        pen_row = QHBoxLayout()
        pen_row.setSpacing(8)
        pen_row.addWidget(self.pen_width_slider)
        pen_row.addWidget(self.pen_width_label)
        layout.addLayout(make_form_row("默认画笔粗细", pen_row))

        # 默认橡皮粗细：滑块 + 数值
        self.eraser_width_slider = QSlider(Qt.Horizontal)
        self.eraser_width_slider.setRange(2, 40)
        self.eraser_width_slider.setFixedWidth(200)
        self.eraser_width_label = QLabel()
        self.eraser_width_label.setStyleSheet(
            f"color: {COLOR_TEXT_GRAY}; font-size: 13px;"
        )
        self.eraser_width_slider.valueChanged.connect(
            lambda v: self.eraser_width_label.setText(f"{v}px")
        )
        eraser_row = QHBoxLayout()
        eraser_row.setSpacing(8)
        eraser_row.addWidget(self.eraser_width_slider)
        eraser_row.addWidget(self.eraser_width_label)
        layout.addLayout(make_form_row("默认橡皮粗细", eraser_row))

        # 最大页数
        self.max_pages_spin = QSpinBox()
        self.max_pages_spin.setRange(10, 99)
        self.max_pages_spin.setSuffix(" 页")
        self.max_pages_spin.setFixedWidth(140)
        layout.addLayout(make_form_row("最大页数", self.max_pages_spin))

        # 是否默认显示时间
        self.show_time_check = QCheckBox("打开白板时默认显示左上角时间")
        self.show_time_check.setStyleSheet(
            f"color: {COLOR_TEXT_DARK}; font-size: 14px;"
        )
        self.show_time_check.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.show_time_check)

        layout.addSpacing(6)

        # 右上角标语
        self.slogan_edit = QLineEdit()
        self.slogan_edit.setPlaceholderText("例如：欢迎使用智慧大屏，开启高效课堂")
        self.slogan_edit.setClearButtonEnabled(True)
        self.slogan_edit.setFixedWidth(320)
        layout.addLayout(make_form_row("右上角标语", self.slogan_edit))
        slogan_hint = QLabel("显示在白板右上角，留空则不显示；保存后下次打开白板生效")
        slogan_hint.setStyleSheet(f"color: {COLOR_TEXT_GRAY}; font-size: 12px;")
        slogan_hint.setIndent(106)
        layout.addWidget(slogan_hint)

        layout.addStretch(1)

    # ---------- 数据读写 ----------

    def load_values(self, values):
        """将设置值填充到界面控件。"""
        self.color_picker.set_selected(str(values.get("default_color", COLOR_PALETTE[0])))
        self.pen_width_slider.setValue(int(values.get("default_pen_width", 4)))
        self.pen_width_label.setText(f"{self.pen_width_slider.value()}px")
        self.eraser_width_slider.setValue(int(values.get("default_eraser_width", 20)))
        self.eraser_width_label.setText(f"{self.eraser_width_slider.value()}px")
        self.max_pages_spin.setValue(int(values.get("max_pages", 99)))
        self.show_time_check.setChecked(bool(values.get("show_time", False)))
        self.slogan_edit.setText(str(values.get("slogan", "")))

    def values(self):
        """从界面控件收集设置值。"""
        return {
            "default_color": self.color_picker.value(),
            "default_pen_width": self.pen_width_slider.value(),
            "default_eraser_width": self.eraser_width_slider.value(),
            "max_pages": self.max_pages_spin.value(),
            "show_time": self.show_time_check.isChecked(),
            "slogan": self.slogan_edit.text().strip(),
        }
