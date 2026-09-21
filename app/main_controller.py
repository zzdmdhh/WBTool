# -*- coding: utf-8 -*-
"""
主程序模块

功能：
- 启动调度：读取设置模块保存的 JSON 配置，按配置决定是否启动其他模块（需求 WB-002）
- 运行模式：半接管 / 全接管模式管理（需求 WB-003）

说明：本文件为骨架占位，具体实现待对应需求开发时完成。
"""


def load_config() -> dict:
    """读取设置 JSON 配置（占位）"""
    raise NotImplementedError("待 WB-002 开发")


def start_modules(config: dict) -> None:
    """按配置启动对应模块（占位）"""
    raise NotImplementedError("待 WB-002 开发")
