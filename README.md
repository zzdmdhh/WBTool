# WBTool 多功能智慧大屏管理系统
基于 Python 和 PySide6 开发的多功能智慧大屏管理系统，提供白板、屏幕批注、课程表与信息显示功能。

## 项目结构

```
WBTool/
├── main.py                      # 主程序：创建并运行悬浮球、课程表、信息显示
├── requirements.txt             # 依赖清单
├── README.md                    # 说明文档
├── assets/                      # 静态资源（logo.png 放入后自动显示）
├── ui/                          # 界面组件
│   ├── __init__.py
│   ├── floating_ball.py         # 悬浮球（含功能选择条），管理白板/批注/关于
│   ├── whiteboard.py            # 白板
│   ├── screen_markup.py         # 屏幕批注
│   ├── schedule_widget.py       # 课程表
│   ├── info_panel.py            # 信息面板
│   └── about_dialog.py          # 关于界面（含检查更新）
├── utils/                       # 通用工具
│   ├── __init__.py
│   ├── common.py                # 通用文件：全局配置、屏幕工具、画布基类
│   └── json_loader.py           # JSON 读取工具
└── config/
    ├── schedule.json            # 课程表数据
    └── info.json                # 信息显示数据
```

各模块相互独立，统一引用 `utils/common.py`（配色、尺寸、路径、屏幕工具、画布基类）与 `utils/json_loader.py`（JSON 读取）。

## 使用说明

- 悬浮球：左键拖动移动，松手后靠近屏幕边缘自动吸附
- 单击悬浮球：弹出横向功能选择条（白板、屏幕批注、关闭）
- 长按悬浮球（约 0.7 秒）：进入关于界面
- 白板：全屏白色画布，右上角时间显示，底部工具栏支持画笔/橡皮、颜色、粗细、清空、关闭
- 屏幕批注：全屏透明层，可在任意应用上方直接标注，顶部工具栏操作，Esc 或“退出”结束
- 课程表：屏幕左上角横条，展示当天课程并高亮当前正在进行的课程
- 信息显示：屏幕右上角卡片，展示 JSON 中的信息条目

## 配置文件说明

### config/schedule.json

- `title`：横条标题
- `courses`：课程数组，字段为 `name`（名称）、`weekday`（星期，周一~周日）、`start`/`end`（起止时间 HH:mm）、`room`（教室）

### config/info.json

- `title`：卡片标题
- `items`：信息条目数组，字段为 `label`（标签）和 `value`（内容）
- `value` 支持动态占位符：`{date}` 当前日期、`{weekday}` 当前星期、`{time}` 当前时间

