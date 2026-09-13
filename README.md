# WBTool 多功能智慧大屏管理系统

基于 Python 和 PySide6 开发的多功能智慧大屏管理系统。当前发行版提供悬浮球、白板与关于界面，屏幕批注、课程表与信息显示等功能正在开发中，将在后续版本更新。

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
    │   └── info.json            # 信息显示数据（开发中功能使用）
    └── code/                    # 代码目录
        ├── active/              # 正在使用的代码（当前发行版）
        │   ├── floating_ball.py # 悬浮球（含功能选择条），管理白板/关于
        │   ├── whiteboard.py    # 白板
        │   └── about_dialog.py  # 关于界面（含检查更新）
        └── dev/                 # 开发中的代码（后续版本更新）
            ├── screen_markup.py # 屏幕批注
            ├── schedule_widget.py # 课程表
            └── info_panel.py    # 信息面板
```

## 运行方式

```bash
python main.py
```

仅运行 `app/code/active/` 下的发行版代码（悬浮球、白板、关于界面）；`app/code/dev/` 下的开发中代码不参与运行。

## 当前版本功能说明

- 悬浮球：左键拖动移动，松手后靠近屏幕边缘自动吸附
- 单击悬浮球：弹出横向功能选择条（白板、关闭）
- 长按悬浮球（约 0.7 秒）：进入关于界面
- 白板：全屏白色画布，右上角时间显示，底部工具栏支持画笔/橡皮、颜色、粗细、清空、关闭
- 关于界面：应用信息、版本号与检查更新入口

## 开发中功能（后续版本）

- 屏幕批注：全屏透明层，可在任意应用上方直接标注，顶部工具栏操作，Esc 或"退出"结束
- 课程表：屏幕左上角横条，展示当天课程并高亮当前正在进行的课程
- 信息显示：屏幕右上角卡片，展示 JSON 中的信息条目

## 配置文件格式说明

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
