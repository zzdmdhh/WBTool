# WBTool 多功能智慧大屏管理系统

基于 Python 和 PySide6 开发的多功能智慧大屏管理系统。当前发行版提供悬浮球、白板与设置界面（含系统、各模块设置与关于），屏幕批注、课程表与信息显示等功能正在开发中，将在后续版本更新。

## 项目结构

```
WBTool/
├── main.py                      # 主程序入口：运行悬浮球（python main.py）
├── requirements.txt             # 依赖清单
├── README.md                    # 说明文档
├── .gitignore                   # Git 排除文件
├── LICENSE                      # GPL-3.0 许可证
└── app/                         # 应用主体
    ├── assets/                  # 静态资源（logo.png 放入后自动显示）
    ├── config/                  # 配置文件
    │   ├── schedule.json        # 课程表数据（开发中功能使用）
    │   ├── info.json            # 信息显示数据（开发中功能使用）
    │   └── settings.json        # 设置数据（首次保存设置时生成）
    └── code/                    # 代码目录
        ├── active/              # 正在使用的代码（当前发行版）
        │   ├── floating_ball.py # 悬浮球（含功能选择条），管理白板/设置
        │   └── whiteboard.py    # 白板
        ├── settings/            # 设置模块（由原关于界面升级而来）
        │   ├── settings_dialog.py   # 设置对话框（侧边导航 + 页面堆栈）
        │   ├── settings_manager.py  # 设置读写（settings.json）
        │   ├── common.py            # 共用配色与控件
        │   ├── system_page.py       # 系统设置页面
        │   ├── whiteboard_page.py   # 白板设置页面
        │   ├── markup_page.py       # 屏幕批注设置页面
        │   ├── schedule_page.py     # 课程表设置页面
        │   ├── info_page.py         # 信息面板设置页面
        │   └── about_page.py        # 关于页面
        └── dev/                 # 开发中的代码（后续版本更新）
            ├── screen_markup.py # 屏幕批注
            ├── schedule_widget.py # 课程表
            └── info_panel.py    # 信息面板
```

## 运行方式

```bash
python main.py
```

仅运行 `app/code/active/` 下的发行版代码（悬浮球、白板）；`app/code/dev/` 下的开发中代码不参与运行。

## 当前版本功能说明

- 悬浮球：左键拖动移动，松手后靠近屏幕边缘自动吸附
- 单击悬浮球：弹出横向功能选择条（白板、设置、关闭）
- 长按悬浮球（默认约 0.7 秒，可在设置中调整）：进入设置界面
- 白板：全屏白色画布，右上角时间显示，底部工具栏支持画笔/橡皮、颜色、粗细、清空、关闭
- 设置界面：左侧分类导航，包含系统设置、白板、屏幕批注、课程表、信息面板、关于六个页面
  - 系统设置：悬浮球大小、长按打开设置的时长、边缘吸附阈值、开机自启动
  - 白板设置：默认画笔颜色/粗细、默认橡皮粗细、最大页数、默认显示时间
  - 屏幕批注设置：默认画笔颜色、默认笔画粗细
  - 课程表设置：刷新间隔，快速打开课程表配置文件
  - 信息面板设置：刷新间隔、面板宽度，快速打开信息面板配置文件
  - 关于：应用信息、版本号与检查更新入口

## 配置文件格式说明

### app/config/settings.json

由设置界面自动生成与管理，无需手动编辑；缺失的设置项自动回落到默认值。

- `system`：悬浮球边长 `ball_size`、长按判定时间 `long_press_ms`（毫秒）、吸附阈值 `snap_threshold`（像素）
- `whiteboard`：默认画笔颜色 `default_color`、默认画笔粗细 `default_pen_width`、默认橡皮粗细 `default_eraser_width`、最大页数 `max_pages`、默认显示时间 `show_time`
- `markup`：默认画笔颜色 `default_color`、默认笔画粗细 `default_width`
- `schedule`：刷新间隔 `refresh_seconds`（秒）
- `info`：刷新间隔 `refresh_seconds`（秒）、面板宽度 `panel_width`（像素）

### app/config/schedule.json

- `title`：横条标题
- `courses`：课程数组，字段为 `name`（名称）、`weekday`（星期，周一~周日）、`start`/`end`（起止时间 HH:mm）、`room`（教室）

### app/config/info.json

- `title`：卡片标题
- `items`：信息条目数组，字段为 `label`（标签）和 `value`（内容）
- `value` 支持动态占位符：`{date}` 当前日期、`{weekday}` 当前星期、`{time}` 当前时间

## 写在最后

此项目使用GPL-3.0许可证开源，请遵守许可证条款使用，项目作者zzdmdhh，如果项目对你有帮助就请给个star
特别鸣谢：xvyang zhang
